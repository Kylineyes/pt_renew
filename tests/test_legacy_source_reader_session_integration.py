"""实际读取适配→提取→session→v2审计的离线验收，仅使用模拟native及本地缓冲。"""
import copy
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from legacy_source_memory_reader import make_memory_reader
from legacy_source_observation_session import ObservationSession, ObservationSessionError

IDENTITY = {'run_id': '读取与组装离线互通', 'pid': 123,
            'creation_filetime': 134390106270047430, 'image_sha256': 'a' * 64}
COVERAGE = {'from': 'before_first_target_instruction', 'until': 'process_exit',
            'domains': ['directory_api', 'parse', 'file_io']}
RETURN = 0x140000123


class ReaderSessionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tick = 0
        self.reads = []
        self.errors = []
        self.modes = {}
        self.memory = {}
        for stack, buffer in ((0x1000, 0x4000), (0x2000, 0x5000), (0x3000, 0x6000)):
            self.memory[stack] = RETURN.to_bytes(8, 'little')
            raw = b'X:\\synthetic\0\xfftail'
            self.memory[buffer] = raw + b'Z' * (260 - len(raw))
        self.reader = make_memory_reader(0x1234, read_process_memory=self.native,
                                         get_last_error=self.last_error)
        self.session = ObservationSession(copy.deepcopy(IDENTITY), start_at=self.at(),
            coverage=copy.deepcopy(COVERAGE), lost_events=0, truncated_events=0,
            read_memory=self.reader)

    def native(self, handle, address, destination, requested, transferred):
        self.reads.append((handle.value, address.value, requested.value))
        mode = self.modes.get(address.value, {})
        if 'raise' in mode:
            raise mode['raise']
        count = mode.get('count', requested.value)
        ctypes.memset(destination, 0xa5, requested.value)
        ctypes.memmove(destination, self.memory[address.value], count)
        transferred.contents.value = count
        return mode.get('bool', 1)

    def last_error(self):
        self.errors.append(299)
        return 299

    def at(self, tid=11):
        self.tick += 1
        return {'tid': tid, 'utc_ns': 1794573455000000000 + self.tick,
                'monotonic_ns': 9007199254740993 + self.tick}

    def begin(self, *, stack=0x1000, buffer=0x4000, tid=11, site=0xa56bbe):
        return self.session.begin_api(
            {'rcx': 0, 'rdx': buffer, 'r8': 0x1c if site == 0xa56bbe else 0x1a,
             'r9': 0, 'rsp': stack}, module_base=0x140000000, caller_rva=site,
            encoding='ascii', read_limit=260, phase='合成读取', at=self.at(tid))

    def returned(self, call_id, *, stack=0x1000, tid=11, rax=0xffffffff, rip=RETURN):
        return self.session.return_api(call_id, {'rax': rax, 'rip': rip, 'rsp': stack + 8},
            snapshot_at=self.at(tid), return_at=self.at(tid))

    def end(self, **changes):
        fields = {'at': self.at(), 'coverage': copy.deepcopy(COVERAGE),
                  'lost_events': 0, 'truncated_events': 0, 'complete': True}
        fields.update(changes)
        return self.session.end(**fields)

    def assert_failed(self):
        result = self.session.report()
        self.assertEqual(result['state'], 'failed')
        self.assertFalse(result['integrity_passed'])
        self.assertIsNone(result['source_attribution'])
        self.assertIs(result['execution_ready'], False)
        return result

    def test_full_reader_output_two_threads_nested_same_return_and_digest(self):
        outer = self.begin()
        other = self.begin(stack=0x2000, buffer=0x5000, tid=22, site=0xa56bec)
        inner = self.begin(stack=0x3000, buffer=0x6000)
        self.returned(other, stack=0x2000, tid=22, rax=0x80000000)
        self.returned(inner, stack=0x3000)
        self.returned(outer)
        result = self.end()
        self.assertTrue(result['integrity_passed'], result)
        snapshots = result['audit']['api_snapshots']
        for call_id, address in ((outer, 0x4000), (other, 0x5000), (inner, 0x6000)):
            self.assertEqual(snapshots[call_id]['capture']['raw_hex'], self.memory[address].hex())
            self.assertEqual(snapshots[call_id]['capture']['return_address'], RETURN)
            self.assertEqual(snapshots[call_id]['decoded']['tail_bytes']['hex'],
                             self.memory[address].split(b'\0', 1)[1].hex())
        self.assertEqual(snapshots[other]['capture']['raw_bool'], -(1 << 31))
        self.assertEqual(self.reader.last_receipt['raw_bool'], 1)
        self.assertEqual([x[1:] for x in self.reads], [(0x1000, 8), (0x2000, 8),
            (0x3000, 8), (0x5000, 260), (0x6000, 260), (0x4000, 260)])
        raw = ('\n'.join(json.dumps(row, ensure_ascii=False, sort_keys=True,
            separators=(',', ':'), allow_nan=False) for row in result['events']) + '\n').encode('utf-8')
        self.assertEqual(result['audit']['input']['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['audit']['input']['sha256_scope'], 'canonical_jsonl')
        self.assertEqual(result['events'][0]['creation_filetime'], IDENTITY['creation_filetime'])
        self.assertEqual(self.errors, [])
        self.assertFalse(result['execution_ready'])
        self.assertIsNone(result['source_attribution'])

    def test_failed_partial_and_success_short_read_seal_without_fake_return(self):
        for native_bool in (0, 1):
            with self.subTest(native_bool=native_bool):
                self.setUp()
                self.modes[0x4000] = {'bool': native_bool, 'count': 13}
                call_id = self.begin()
                with self.assertRaises(ObservationSessionError):
                    self.returned(call_id)
                result = self.assert_failed()
                bound = result['audit']['api_snapshots'][call_id]
                self.assertEqual(bytes.fromhex(bound['capture']['raw_hex']), self.memory[0x4000][:13])
                self.assertEqual(bound['capture']['raw_bool'], -1)
                self.assertFalse(bound['capture']['read_complete'])
                self.assertEqual(self.reader.last_receipt['raw_bool'], native_bool)
                self.assertEqual(self.reader.last_receipt['error'], 299 if native_bool == 0 else None)
                self.assertEqual([row['kind'] for row in result['events']],
                                 ['run_start', 'call_enter', 'api_snapshot'])
                before = list(self.reads)
                with self.assertRaises(ObservationSessionError):
                    self.end()
                self.assertEqual(self.reads, before)

    def test_stack_partial_keeps_unready_enter_and_does_not_read_buffer(self):
        self.modes[0x1000] = {'bool': 0, 'count': 7}
        with self.assertRaises(ObservationSessionError):
            self.begin()
        result = self.assert_failed()
        self.assertFalse(result['pending_calls'][0]['entry_ready'])
        self.assertEqual([row['kind'] for row in result['events']], ['run_start', 'call_enter'])
        self.assertEqual(self.reads, [(0x1234, 0x1000, 8)])
        self.assertEqual(self.reader.last_receipt['error'], 299)

    def test_native_exception_clears_previous_receipt_and_seals_actual_prefix(self):
        call_id = self.begin()
        self.assertTrue(self.reader.last_receipt['raw_bool'])
        self.modes[0x4000] = {'raise': OSError('合成RPM异常')}
        with self.assertRaises(ObservationSessionError):
            self.returned(call_id)
        result = self.assert_failed()
        self.assertIsNone(self.reader.last_receipt)
        self.assertEqual(result['diagnostics'][0]['exception_type'], 'OSError')
        self.assertEqual(result['pending_calls'][0]['call_id'], call_id)
        self.assertEqual([row['kind'] for row in result['events']], ['run_start', 'call_enter'])
        before = list(self.reads)
        with self.assertRaises(ObservationSessionError):
            self.returned(call_id)
        self.assertEqual(self.reads, before)

    def test_wrong_thread_stack_or_rip_rejected_before_native_buffer_access(self):
        for mode in ('thread', 'stack', 'rip'):
            with self.subTest(mode=mode):
                self.setUp()
                call_id = self.begin()
                if mode == 'stack':
                    self.begin(stack=0x2000, buffer=0x5000)
                before = list(self.reads)
                with self.assertRaises(ObservationSessionError):
                    self.returned(call_id, tid=22 if mode == 'thread' else 11,
                                  rip=RETURN + 1 if mode == 'rip' else RETURN)
                self.assertEqual(self.reads, before)
                self.assert_failed()

    def test_shell_failure_residue_is_distinct_from_successful_native_read(self):
        self.memory[0x4000] = b'\xff' * 260
        call_id = self.begin()
        self.returned(call_id, rax=0)
        result = self.end()
        self.assertTrue(result['integrity_passed'], result)
        bound = result['audit']['api_snapshots'][call_id]
        self.assertEqual(bound['decoded']['status'], 'api_failed')
        self.assertIsNone(bound['decoded']['path_text'])
        self.assertEqual(bound['capture']['raw_hex'], self.memory[0x4000].hex())
        self.assertEqual(self.reader.last_receipt['raw_bool'], 1)
        self.assertEqual(bound['capture']['raw_bool'], 0)

    def test_parse_and_repeated_file_lifecycle_with_reader_then_loss_rejected(self):
        self.session.append('call_enter', {'call_id': 'parse', 'operation': 'parse',
            'name': 'Parse', 'phase': '合成解析', 'path': 'synthetic.conf'}, at=self.at())
        call_id = self.begin()
        self.returned(call_id)
        for index in range(2):
            self.session.append('file_open', {'open_id': str(index), 'parse_call_id': 'parse',
                'path': 'synthetic.conf', 'success': True, 'handle': 'H', 'error': None}, at=self.at())
            self.session.append('file_read', {'open_id': str(index), 'parse_call_id': 'parse',
                'offset': 0, 'requested': 1, 'transferred': 1, 'success': True, 'error': None}, at=self.at())
            self.session.append('file_close', {'open_id': str(index), 'success': True,
                'error': None}, at=self.at())
        self.session.append('call_return', {'call_id': 'parse', 'result': 1}, at=self.at())
        result = self.end(lost_events=1)
        self.assertFalse(result['integrity_passed'])
        self.assertEqual(result['state'], 'failed')
        self.assertEqual(result['events'][-1]['data']['lost_events'], 1)
        self.assertEqual(sum(row['kind'] == 'file_open' for row in result['events']), 2)
        self.assertEqual(len(result['audit']['api_snapshots']), 1)


if __name__ == '__main__':
    unittest.main()
