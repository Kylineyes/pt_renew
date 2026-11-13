"""Win64读取适配的合成native函数测试，绝不调用真实工厂或Windows API。"""
import copy
import ctypes
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import legacy_source_memory_reader as memory
import legacy_source_call_capture as capture
import audit_legacy_source_observation as audit

EVIDENCE = REPO / '.local-analysis/ex005-memory-reader'


def events(value):
    """给实际capture输出附加纯合成v2身份；不伪造真实覆盖证明。"""
    coverage = {'from': 'before_first_target_instruction', 'until': 'process_exit',
                'domains': ['directory_api', 'parse', 'file_io']}
    bodies = [
        ('run_start', {'coverage': coverage, 'lost_events': 0, 'truncated_events': 0}),
        ('call_enter', {'call_id': 'api-1', 'operation': 'api',
                        'name': 'SHGetSpecialFolderPathA', 'phase': '合成返回', 'path': None}),
        ('api_snapshot', {'call_id': 'api-1', 'capture': value}),
        ('call_return', {'call_id': 'api-1', 'result': value['raw_bool']}),
        ('run_end', {'coverage': copy.deepcopy(coverage), 'lost_events': 0,
                      'truncated_events': 0, 'complete': True, 'event_count': 5}),
    ]
    return [{'schema_version': 2, 'run_id': '合成读取互通', 'seq': index, 'pid': 123,
             'creation_filetime': '134390106270047430', 'tid': 11,
             'image_sha256': 'a' * 64, 'kind': kind, 'data': data,
             'utc_ns': 1794573455000000000 + index,
             'monotonic_ns': 9007199254740993 + index}
            for index, (kind, data) in enumerate(bodies)]


class MemoryReaderTests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.calls = []
        self.order = []
        self.payload = self.fixture('native.bin', b'AB\0tail')
        self.transferred = len(self.payload)
        self.raw_bool = 1
        self.error = 299
        self.reader = memory.make_memory_reader(0x1234, read_process_memory=self.native,
                                                get_last_error=self.last_error)

    def fixture(self, name, raw):
        path = self.root / name
        path.write_bytes(raw)
        return path.read_bytes()

    def native(self, handle, address, destination, requested, transferred):
        self.order.append('rpm')
        self.calls.append((handle.value, address.value, requested.value))
        self.assertIs(type(handle), memory.HANDLE)
        self.assertIs(type(address), memory.ADDRESS)
        self.assertIs(type(destination), memory.ADDRESS)
        self.assertIs(type(requested), memory.SIZE_T)
        self.assertIs(type(transferred), ctypes.POINTER(memory.SIZE_T))
        # 污染本地缓冲尾部，证明结果不会发布计数外字节或靠初始零补齐。
        ctypes.memset(destination, 0xa5, requested.value)
        ctypes.memmove(destination, self.payload, min(len(self.payload), requested.value))
        if self.transferred is not None:
            transferred.contents.value = self.transferred
        if isinstance(self.raw_bool, Exception):
            raise self.raw_bool
        return self.raw_bool

    def last_error(self):
        self.order.append('error')
        if isinstance(self.error, Exception):
            raise self.error
        return self.error

    def test_exact_win64_types_complete_and_independent_receipt(self):
        self.assertEqual(ctypes.sizeof(memory.BOOL), 4)
        self.assertEqual(ctypes.sizeof(memory.SIZE_T), 8)
        self.assertEqual(ctypes.sizeof(memory.HANDLE), 8)
        self.assertEqual(ctypes.sizeof(memory.ADDRESS), 8)
        result = self.reader(0x4000, 7)
        self.assertEqual(result, {'data': self.payload, 'complete': True})
        self.assertEqual(set(result), {'data', 'complete'})
        self.assertEqual(self.reader.last_receipt,
                         {'requested': 7, 'transferred': 7, 'raw_bool': 1, 'error': None})
        receipt = self.reader.last_receipt
        receipt['raw_bool'] = 0
        self.assertEqual(self.reader.last_receipt['raw_bool'], 1)
        self.assertEqual(self.calls, [(0x1234, 0x4000, 7)])
        self.assertEqual(self.order, ['rpm'])

    def test_bool_minus_one_int_min_and_positive_nonone_are_preserved(self):
        for value in (-1, -(1 << 31), 42, (1 << 31) - 1):
            with self.subTest(value=value):
                self.raw_bool = value
                self.assertTrue(self.reader(0x4000, 7)['complete'])
                self.assertEqual(self.reader.last_receipt['raw_bool'], value)
        self.assertNotIn('error', self.order)

    def test_success_short_read_is_incomplete_and_never_pads_output(self):
        self.transferred = 3
        result = self.reader(0x4000, 12)
        self.assertEqual(result, {'data': b'AB\0', 'complete': False})
        self.assertEqual(self.reader.last_receipt['error'], None)
        self.assertEqual(self.order, ['rpm'])

    def test_failed_partial_and_zero_reads_keep_exact_count(self):
        self.raw_bool = 0
        for count in (3, 0, 7):
            self.transferred = count
            self.order.clear()
            result = self.reader(0x4000, 7)
            self.assertEqual(result, {'data': self.payload[:count], 'complete': False})
            self.assertEqual(self.reader.last_receipt,
                             {'requested': 7, 'transferred': count, 'raw_bool': 0, 'error': 299})
            self.assertEqual(self.order, ['rpm', 'error'])

    def test_success_zero_count_does_not_invent_a_nul(self):
        self.transferred = 0
        self.assertEqual(self.reader(0x4000, 7), {'data': b'', 'complete': False})

    def test_failure_samples_error_immediately_and_success_never_samples_stale_error(self):
        self.raw_bool = 0
        self.reader(0x4000, 7)
        self.assertEqual(self.order, ['rpm', 'error'])
        self.raw_bool = -1
        self.error = AssertionError('成功不得取旧错误码')
        result = self.reader(0x4000, 7)
        self.assertTrue(result['complete'])
        self.assertIsNone(self.reader.last_receipt['error'])
        self.assertEqual(self.order, ['rpm', 'error', 'rpm'])

    def test_oversized_or_unwritten_counts_rejected_without_buffer_result(self):
        for value in (8, memory.UINT64_MAX, None, -1):
            with self.subTest(value=value):
                self.transferred = value
                with self.assertRaises(memory.MemoryReaderError):
                    self.reader(0x4000, 7)
                self.assertGreater(self.reader.last_receipt['transferred'], 7)
        self.assertEqual(len(self.calls), 4)

    def test_failed_overcount_still_samples_error_before_rejection(self):
        self.raw_bool = 0
        self.transferred = 8
        with self.assertRaises(memory.MemoryReaderError):
            self.reader(0x4000, 7)
        self.assertEqual(self.order, ['rpm', 'error'])
        self.assertEqual(self.reader.last_receipt['error'], 299)

    def test_invalid_native_bool_is_not_coerced_or_allowed_to_reuse_old_receipt(self):
        self.reader(0x4000, 7)
        for value in (True, False, 1.0, '1', None, 0xffffffff,
                      -(1 << 31) - 1, 1 << 31, ctypes.c_int32(-1)):
            with self.subTest(value=repr(value)):
                self.raw_bool = value
                with self.assertRaises(memory.MemoryReaderError):
                    self.reader(0x4000, 7)
                self.assertIsNone(self.reader.last_receipt)
        self.assertNotIn('error', self.order)

    def test_invalid_error_code_does_not_reuse_previous_success(self):
        self.reader(0x4000, 7)
        self.raw_bool = 0
        for value in (True, -1, 1 << 32, '299', 299.0, None):
            with self.subTest(value=value):
                self.error = value
                with self.assertRaises(memory.MemoryReaderError):
                    self.reader(0x4000, 7)
                self.assertIsNone(self.reader.last_receipt)

    def test_exception_from_native_or_error_callback_propagates_without_retry(self):
        self.reader(0x4000, 7)
        error = RuntimeError('合成native异常')
        self.raw_bool = error
        with self.assertRaises(RuntimeError) as caught:
            self.reader(0x4000, 7)
        self.assertIs(caught.exception, error)
        self.assertIsNone(self.reader.last_receipt)
        self.assertEqual(len(self.calls), 2)
        self.raw_bool = 0
        self.error = error
        with self.assertRaises(RuntimeError) as caught:
            self.reader(0x4000, 7)
        self.assertIs(caught.exception, error)
        self.assertIsNone(self.reader.last_receipt)
        self.assertEqual(self.order[-2:], ['rpm', 'error'])

    def test_invalid_handle_types_zero_and_known_pseudo_handles_rejected(self):
        values = [0, -1, -2, True, 1.0, '4660', None, 1 << 64,
                  ctypes.c_void_p(0x1234), *memory._PSEUDO_HANDLES]
        for value in values:
            with self.subTest(value=repr(value)), self.assertRaises(memory.MemoryReaderError):
                memory.make_memory_reader(value, read_process_memory=self.native,
                                          get_last_error=self.last_error)
        self.assertEqual(self.calls, [])
        with self.assertRaises(TypeError):
            memory.make_memory_reader(pid=123, read_process_memory=self.native,
                                      get_last_error=self.last_error)

    def test_bad_callback_arguments_rejected_without_reads(self):
        for native, error in ((None, self.last_error), (self.native, None), (1, 2)):
            with self.assertRaises(memory.MemoryReaderError):
                memory.make_memory_reader(0x1234, read_process_memory=native, get_last_error=error)
        self.assertEqual(self.calls, [])

    def test_address_size_type_bounds_and_overflow_rejected_before_native(self):
        self.reader(0x4000, 7)
        calls = len(self.calls)
        for address in (0, -1, True, 1.0, '4096', None, 1 << 64):
            with self.subTest(address=address), self.assertRaises(memory.MemoryReaderError):
                self.reader(address, 1)
            self.assertIsNone(self.reader.last_receipt)
        for size in (0, -1, 261, True, 1.0, '8', None):
            with self.subTest(size=size), self.assertRaises(memory.MemoryReaderError):
                self.reader(0x4000, size)
        with self.assertRaises(memory.MemoryReaderError):
            self.reader(memory.UINT64_MAX, 1)
        self.assertEqual(len(self.calls), calls)

    def test_260_and_maximum_nonoverflow_address_are_exact(self):
        self.payload = self.fixture('boundary.bin', b'a' * 259 + b'\0')
        self.transferred = 260
        result = self.reader(memory.UINT64_MAX - 260, 260)
        self.assertTrue(result['complete'])
        self.assertEqual(result['data'], self.payload)
        self.assertEqual(self.calls[-1], (0x1234, memory.UINT64_MAX - 260, 260))
        self.payload = b'\0'
        self.transferred = 1
        self.assertEqual(self.reader(0x4000, 1), {'data': b'\0', 'complete': True})

    def test_import_and_injected_constructor_do_not_load_dll_or_call_native(self):
        spec = importlib.util.spec_from_file_location('synthetic_memory_reader',
                                                     REPO / 'tools/legacy_source_memory_reader.py')
        module = importlib.util.module_from_spec(spec)
        with patch.object(ctypes, 'WinDLL', create=True, side_effect=AssertionError('禁止DLL加载')):
            spec.loader.exec_module(module)
            reader = module.make_memory_reader(0x1234, read_process_memory=self.native,
                                                get_last_error=self.last_error)
        self.assertIsNone(reader.last_receipt)
        self.assertEqual(self.calls, [])
        # 本测试明确不调用make_windows_memory_reader，即使工厂可被模拟。

    def test_non_64_bit_injected_abi_rejected_without_dll_or_reads(self):
        original = ctypes.sizeof
        with patch.object(ctypes, 'sizeof', side_effect=lambda value: 4 if value is memory.HANDLE else original(value)):
            with self.assertRaises(memory.MemoryReaderError):
                memory.make_memory_reader(0x1234, read_process_memory=self.native,
                                          get_last_error=self.last_error)
        self.assertEqual(self.calls, [])

    def produce(self, *, partial=False):
        stack, address, returned = 0x1000, 0x4000, 0x140000123
        raw = self.fixture('source-buffer.bin', b'X:\\synthetic\0\xfftail')
        # 完整RPM读计划要求全量260；首NUL后的全部原缓冲也必须保留。
        padded = raw + b'Z' * (260 - len(raw))
        memory_map = {stack: returned.to_bytes(8, 'little'), address: padded}
        def native(handle, pointer, destination, requested, transferred):
            self.calls.append((handle.value, pointer.value, requested.value))
            data = memory_map[pointer.value]
            count = len(raw) if partial and pointer.value == address else requested.value
            ctypes.memmove(destination, data, count)
            transferred.contents.value = count
            return 0 if partial and pointer.value == address else 1
        reader = memory.make_memory_reader(0x1234, read_process_memory=native,
                                           get_last_error=self.last_error)
        entry = capture.begin_shell_folder_call(
            {'rcx': 0, 'rdx': address, 'r8': 0x1c, 'r9': 0, 'rsp': stack},
            module_base=0x140000000, caller_rva=0xa56bbe, encoding='ascii', read_memory=reader)
        value = capture.finish_shell_folder_call(
            entry, {'rax': 0xffffffff, 'rip': returned, 'rsp': stack + 8}, read_memory=reader)
        return value, reader, raw, padded

    def test_reader_to_actual_begin_finish_and_v2_preserves_stack_buffer_and_tail(self):
        value, reader, raw, padded = self.produce()
        self.assertEqual(self.calls, [(0x1234, 0x1000, 8), (0x1234, 0x4000, 260)])
        self.assertTrue(value['read_complete'])
        self.assertEqual(value['raw_bool'], -1)
        self.assertEqual(reader.last_receipt['raw_bool'], 1)
        self.assertEqual(bytes.fromhex(value['raw_hex']), padded)
        report = audit.audit_events(events(value))
        self.assertTrue(report['integrity_passed'], report)
        decoded = report['api_snapshots']['api-1']['decoded']
        self.assertEqual(decoded['raw_bytes']['hex'], padded.hex())
        self.assertEqual(decoded['tail_bytes']['hex'], padded[len(b'X:\\synthetic\0'):].hex())
        self.assertNotIn('last_receipt', value)
        self.assertEqual(reader.last_receipt['requested'], 260)
        self.assertIsNone(report['source_attribution'])
        self.assertFalse(report['execution_ready'])

    def test_partial_reader_output_reaches_actual_capture_then_v2_rejects(self):
        value, reader, raw, _ = self.produce(partial=True)
        self.assertFalse(value['read_complete'])
        self.assertEqual(value['raw_bool'], -1)
        self.assertEqual(reader.last_receipt['raw_bool'], 0)
        self.assertEqual(bytes.fromhex(value['raw_hex']), raw)
        self.assertEqual(reader.last_receipt['error'], 299)
        report = audit.audit_events(events(value))
        self.assertFalse(report['integrity_passed'])
        self.assertIn('incomplete_snapshot', {item['code'] for item in report['issues']})
        self.assertFalse(report['api_snapshots']['api-1']['accepted'])
        self.assertEqual(self.calls, [(0x1234, 0x1000, 8), (0x1234, 0x4000, 260)])

    def test_partial_stack_rpm_is_rejected_by_actual_begin(self):
        self.payload = (0x140000123).to_bytes(8, 'little')
        self.transferred = 7
        with self.assertRaises(capture.CallCaptureError):
            capture.begin_shell_folder_call(
                {'rcx': 0, 'rdx': 0x4000, 'r8': 0x1c, 'r9': 0, 'rsp': 0x1000},
                module_base=0x140000000, caller_rva=0xa56bbe, encoding='ascii', read_memory=self.reader)
        self.assertEqual(self.calls, [(0x1234, 0x1000, 8)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
