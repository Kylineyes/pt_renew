"""Shell32提取核心的合成寄存器与内存回调测试，不连接真实进程。"""
from pathlib import Path
from dataclasses import FrozenInstanceError, replace
import copy
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools import legacy_source_call_capture as capture
from tools import legacy_source_api_buffers as buffers

EVIDENCE = REPO / '.local-analysis/ex005-call-capture'
BASE = 0x140000000
RSP = 0x1000
BUFFER = 0x4000
RETURN = BASE + 0xa56bc4
CAPTURE_FIELDS = {'api', 'module_base', 'caller_rva', 'entry_rsp', 'return_address',
                  'hwnd', 'buffer_address', 'csidl', 'f_create', 'raw_bool',
                  'raw_hex', 'read_limit', 'read_complete', 'encoding'}


class CallCaptureTests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.calls = []
        self.enter = {'rcx': 0, 'rdx': BUFFER, 'r8': 0x1c, 'r9': 0, 'rsp': RSP}
        self.leave = {'rax': 1, 'rip': RETURN, 'rsp': RSP + 8}
        self.responses = {
            RSP: {'data': self.fixture('stack.bin', RETURN.to_bytes(8, 'little')), 'complete': True},
            BUFFER: {'data': self.fixture('buffer.bin', b'X:\\synthetic\0tail'), 'complete': True},
        }

    def fixture(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path.read_bytes()

    def read(self, address, size):
        self.calls.append((address, size))
        result = self.responses[address]
        if isinstance(result, Exception):
            raise result
        return result

    def begin(self, registers=None, **changes):
        args = {'module_base': BASE, 'caller_rva': 0xa56bbe, 'encoding': 'cp1252',
                'read_memory': self.read}
        args.update(changes)
        return capture.begin_shell_folder_call(self.enter if registers is None else registers,
                                               **args)

    def finish(self, entry, registers=None, **changes):
        args = {'read_memory': self.read}
        args.update(changes)
        return capture.finish_shell_folder_call(entry, self.leave if registers is None else registers,
                                                **args)

    def test_exact_capture_fields_and_only_stack_then_saved_buffer_reads(self):
        entry = self.begin()
        self.assertEqual(self.calls, [(RSP, 8)])
        result = self.finish(entry)
        self.assertEqual(self.calls, [(RSP, 8), (BUFFER, 260)])
        self.assertEqual(set(result), CAPTURE_FIELDS)
        self.assertEqual(result, {
            'api': 'SHGetSpecialFolderPathA', 'module_base': BASE,
            'caller_rva': 0xa56bbe, 'entry_rsp': RSP, 'return_address': RETURN,
            'hwnd': 0, 'buffer_address': BUFFER, 'csidl': 0x1c, 'f_create': 0,
            'raw_bool': 1, 'raw_hex': b'X:\\synthetic\0tail'.hex(),
            'read_limit': 260, 'read_complete': True, 'encoding': 'cp1252',
        })

    def test_low_r8d_r9d_and_signed_bool_keep_original_width(self):
        self.enter.update(r8=(0xfedcba98 << 32) | 0x1c, r9=0xffffffff00000000)
        entry = self.begin()
        for rax, expected in ((0xffffffff, -1), (0xdeadbeefffffffff, -1),
                              (0x9876543280000000, -(1 << 31)),
                              (0xffffffffffffffff, -1), (0xabc000000000, 0),
                              (0x123400007fffffff, (1 << 31) - 1)):
            with self.subTest(rax=hex(rax)):
                result = self.finish(entry, {**self.leave, 'rax': rax})
                self.assertEqual(result['raw_bool'], expected)
                self.assertEqual(result['csidl'], 0x1c)
                self.assertEqual(result['f_create'], 0)

    def test_second_caller_requires_its_own_csidl(self):
        self.enter['r8'] = 0x1a
        result = self.finish(self.begin(caller_rva=0xa56bec))
        self.assertEqual((result['caller_rva'], result['csidl']), (0xa56bec, 0x1a))
        self.calls.clear()
        with self.assertRaises(capture.CallCaptureError):
            self.begin(caller_rva=0xa56bbe)
        self.assertEqual(self.calls, [])

    def test_entry_owns_immutable_values_even_if_caller_changes_input_during_read(self):
        def mutate(address, size):
            result = self.read(address, size)
            self.enter.update(rdx=0x9999, rsp=0x7777, r8=0x1a)
            return result
        entry = self.begin(read_memory=mutate)
        self.enter.clear()
        with self.assertRaises(FrozenInstanceError):
            entry.buffer_address = 0x9999
        result = self.finish(entry)
        self.assertEqual(result['buffer_address'], BUFFER)
        self.assertEqual(result['entry_rsp'], RSP)
        self.assertEqual(result['csidl'], 0x1c)
        self.assertEqual(self.calls[-1], (BUFFER, 260))

    def test_input_registers_and_callback_results_remain_unchanged(self):
        before = copy.deepcopy((self.enter, self.leave, self.responses))
        entry = self.begin()
        self.finish(entry)
        self.assertEqual((self.enter, self.leave, self.responses), before)

    def test_wrong_return_rip_or_rsp_rejected_before_buffer_access(self):
        entry = self.begin()
        for registers in ({**self.leave, 'rip': RETURN + 1},
                          {**self.leave, 'rsp': RSP},
                          {**self.leave, 'rsp': RSP + 16}):
            with self.subTest(registers=registers):
                self.calls.clear()
                with self.assertRaises(capture.CallCaptureError):
                    self.finish(entry, registers)
                self.assertEqual(self.calls, [])

    def test_return_registers_must_not_include_volatile_rdx_or_missing_fields(self):
        entry = self.begin()
        for registers in ({**self.leave, 'rdx': 0x9999},
                          {'rax': 1, 'rsp': RSP + 8}, None, []):
            self.calls.clear()
            with self.subTest(registers=registers), self.assertRaises(capture.CallCaptureError):
                capture.finish_shell_folder_call(entry, registers, read_memory=self.read)
            self.assertEqual(self.calls, [])

    def test_address_zero_range_and_addition_overflows_rejected_without_reads(self):
        maximum = capture.UINT64_MAX
        cases = [({'rsp': 0}, {}), ({'rsp': maximum - 7}, {}),
                 ({'rdx': 0}, {}), ({'rdx': maximum - 259}, {}),
                 ({}, {'module_base': 0}),
                 ({}, {'module_base': maximum - 0xa56bbe + 1}),
                 ({}, {'module_base': maximum + 1})]
        for changes, options in cases:
            self.calls.clear()
            with self.subTest(changes=changes, options=options), \
                    self.assertRaises(capture.CallCaptureError):
                self.begin({**self.enter, **changes}, **options)
            self.assertEqual(self.calls, [])

    def test_maximum_nonoverflow_address_ranges_are_not_wrapped(self):
        maximum = capture.UINT64_MAX
        entry_rsp, address = maximum - 8, maximum - 260
        self.responses[entry_rsp] = self.responses[RSP]
        self.responses[address] = self.responses[BUFFER]
        entry = self.begin({**self.enter, 'rsp': entry_rsp, 'rdx': address},
                           module_base=maximum - 0xa56bbe)
        result = self.finish(entry, {**self.leave, 'rsp': maximum})
        self.assertEqual(result['module_base'] + result['caller_rva'], maximum)
        self.assertEqual(result['buffer_address'], address)
        self.assertEqual(self.calls, [(entry_rsp, 8), (address, 260)])

    def test_register_values_are_u64_exact_integers(self):
        for name in self.enter:
            for value in (-1, 1 << 64, True, 0.0, '0', None):
                self.calls.clear()
                with self.subTest(name=name, value=value), \
                        self.assertRaises(capture.CallCaptureError):
                    self.begin({**self.enter, name: value})
                self.assertEqual(self.calls, [])
        entry = self.begin()
        for name in self.leave:
            for value in (-1, 1 << 64, False, 1.0, '1', None):
                self.calls.clear()
                with self.subTest(name=name, value=value), \
                        self.assertRaises(capture.CallCaptureError):
                    self.finish(entry, {**self.leave, name: value})
                self.assertEqual(self.calls, [])

    def test_entry_register_field_sets_and_parameter_gates(self):
        for registers in ({**self.enter, 'rax': 0}, {k: v for k, v in self.enter.items() if k != 'r9'},
                          {}, [], None):
            with self.subTest(registers=registers), self.assertRaises(capture.CallCaptureError):
                capture.begin_shell_folder_call(registers, module_base=BASE, caller_rva=0xa56bbe,
                    encoding='cp1252', read_memory=self.read)
        for changes in ({'rcx': 1}, {'r8': 0x1a}, {'r9': 1}):
            with self.subTest(changes=changes), self.assertRaises(capture.CallCaptureError):
                self.begin({**self.enter, **changes})
        self.assertEqual(self.calls, [])

    def test_invalid_metadata_limits_encoding_or_callback_do_not_read_memory(self):
        cases = ({'caller_rva': True}, {'caller_rva': 0xa56bbf}, {'module_base': True},
                 {'read_limit': 0}, {'read_limit': 261}, {'read_limit': True},
                 {'read_limit': 1.0}, {'encoding': None}, {'encoding': ''},
                 {'encoding': 'mbcs'}, {'encoding': 'utf-16'}, {'read_memory': None})
        for options in cases:
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.begin(**options)
        self.assertEqual(self.calls, [])

    def test_stack_short_incomplete_overlong_or_zero_return_rejected(self):
        cases = [({'data': b'\x01' * n, 'complete': complete})
                 for n, complete in ((0, True), (7, True), (8, False), (9, True))]
        cases.append({'data': b'\0' * 8, 'complete': True})
        for result in cases:
            self.calls.clear()
            self.responses[RSP] = result
            with self.subTest(result=result), self.assertRaises(capture.CallCaptureError):
                self.begin()
            self.assertEqual(self.calls, [(RSP, 8)])

    def test_callback_result_schema_types_are_strict_at_both_reads(self):
        cases = (None, b'x', {}, {'data': b'x'}, {'data': b'x', 'complete': True, 'extra': 0},
                 {'data': bytearray(b'x'), 'complete': True},
                 {'data': b'x', 'complete': 1})
        for result in cases:
            for address in (RSP, BUFFER):
                self.responses[RSP] = {'data': RETURN.to_bytes(8, 'little'), 'complete': True}
                self.responses[BUFFER] = {'data': b'\0', 'complete': True}
                entry = self.begin() if address == BUFFER else None
                self.responses[address] = result
                with self.subTest(result=result, address=address), \
                        self.assertRaises(capture.CallCaptureError):
                    self.finish(entry) if address == BUFFER else self.begin()

    def test_buffer_short_reads_keep_explicit_complete_flag_without_inference(self):
        entry = self.begin()
        for raw, complete in ((b'', False), (b'x', False), (b'x\0', False),
                              (b'\0', True), (b'x', True)):
            self.responses[BUFFER] = {'data': raw, 'complete': complete}
            with self.subTest(raw=raw, complete=complete):
                result = self.finish(entry)
                self.assertEqual(result['raw_hex'], raw.hex())
                self.assertIs(result['read_complete'], complete)
                self.assertEqual(set(result), CAPTURE_FIELDS)

    def test_buffer_260_boundary_tail_and_overlong_response(self):
        entry = self.begin()
        for raw in (b'a' * 259 + b'\0', b'a' * 260, b'a\0b\0\xfftail'):
            self.responses[BUFFER] = {'data': self.fixture('boundary.bin', raw), 'complete': True}
            result = self.finish(entry)
            self.assertEqual(result['raw_hex'], raw.hex())
            self.assertEqual(bytes.fromhex(result['raw_hex']), raw)
        self.responses[BUFFER] = {'data': b'a' * 261, 'complete': False}
        with self.assertRaises(capture.CallCaptureError):
            self.finish(entry)

    def test_one_byte_limit_and_explicit_encoding_name_preserved(self):
        entry = self.begin(read_limit=1, encoding='windows-1252')
        self.responses[BUFFER] = {'data': b'\0', 'complete': True}
        result = self.finish(entry)
        self.assertEqual(result['encoding'], 'windows-1252')
        self.assertEqual(result['read_limit'], 1)
        self.assertEqual(self.calls, [(RSP, 8), (BUFFER, 1)])

    def test_public_decoder_is_reused_for_validation_and_actual_buffer(self):
        with patch.object(capture, 'decode_shell_folder', wraps=buffers.decode_shell_folder) as decoder:
            entry = self.begin(encoding='utf-8')
            self.responses[BUFFER] = {'data': b'\xff\0tail', 'complete': True}
            result = self.finish(entry, {**self.leave, 'rax': 0})
            self.assertEqual(decoder.call_args.kwargs, {
                'raw_bool': 0, 'raw_bytes': b'\xff\0tail', 'read_limit': 260,
                'read_complete': True, 'encoding': 'utf-8'})
            self.assertEqual(result['raw_bool'], 0)
            self.assertNotIn('path_text', result)
            self.assertNotIn('decode_error', result)

    def test_callback_exceptions_propagate_without_retry_or_fabricated_result(self):
        error = RuntimeError('合成内存读取失败')
        self.responses[RSP] = error
        with self.assertRaises(RuntimeError) as caught:
            self.begin()
        self.assertIs(caught.exception, error)
        self.assertEqual(self.calls, [(RSP, 8)])
        self.responses[RSP] = {'data': RETURN.to_bytes(8, 'little'), 'complete': True}
        entry = self.begin()
        self.calls.clear()
        self.responses[BUFFER] = error
        with self.assertRaises(RuntimeError) as caught:
            self.finish(entry)
        self.assertIs(caught.exception, error)
        self.assertEqual(self.calls, [(BUFFER, 260)])

    def test_forged_entry_types_and_replaced_invalid_state_rejected_before_reads(self):
        entry = self.begin()
        for invalid in (None, {}, (), replace(entry, read_limit=261),
                        replace(entry, entry_rsp=0), replace(entry, return_address=0)):
            self.calls.clear()
            with self.subTest(invalid=invalid), self.assertRaises(capture.CallCaptureError):
                self.finish(invalid)
            self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
