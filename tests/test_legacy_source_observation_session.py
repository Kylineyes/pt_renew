"""状态组装器真实复用提取／审计组件的合成测试，不连接进程或真实API。"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import legacy_source_observation_session as sessions
import legacy_source_call_capture as capture
import audit_legacy_source_observation as audit

EVIDENCE = REPO / '.local-analysis/ex005-observation-session'
IDENTITY = {'run_id': '合成session', 'pid': 123, 'creation_filetime': '134390106270047430',
            'image_sha256': 'a' * 64}
COVERAGE = {'from': 'before_first_target_instruction', 'until': 'process_exit',
            'domains': ['directory_api', 'parse', 'file_io']}
RETURN = 0x140000123


class ObservationSessionTests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.counter = 0
        self.reads = []
        self.memory = {}
        for rsp, buf in ((0x1000, 0x4000), (0x2000, 0x5000), (0x3000, 0x6000)):
            self.memory[rsp] = {'data': RETURN.to_bytes(8, 'little'), 'complete': True}
            path = self.root / (str(buf) + '.bin')
            path.write_bytes(b'X:\\synthetic\0\xfftail')
            self.memory[buf] = {'data': path.read_bytes(), 'complete': True}

    def at(self, tid=11):
        self.counter += 1
        return {'tid': tid, 'utc_ns': 1794573455000000000 + self.counter,
                'monotonic_ns': 9007199254740993 + self.counter}

    def read(self, address, size):
        self.reads.append((address, size))
        value = self.memory[address]
        if isinstance(value, Exception):
            raise value
        return value

    def new(self, **changes):
        args = {'start_at': self.at(), 'coverage': copy.deepcopy(COVERAGE),
                'lost_events': 0, 'truncated_events': 0, 'read_memory': self.read}
        identity = changes.pop('identity', copy.deepcopy(IDENTITY))
        args.update(changes)
        return sessions.ObservationSession(identity, **args)

    def begin(self, session, tid=11, rsp=0x1000, buf=0x4000, **changes):
        args = {'module_base': 0x140000000, 'caller_rva': 0xa56bbe,
                'encoding': 'ascii', 'read_limit': 260, 'phase': '合成Shell32', 'at': self.at(tid)}
        args.update(changes)
        return session.begin_api({'rcx': 0, 'rdx': buf, 'r8': 0x1c, 'r9': 0, 'rsp': rsp}, **args)

    def returned(self, session, call_id, tid=11, rsp=0x1000, rax=0xffffffff, **changes):
        args = {'snapshot_at': self.at(tid), 'return_at': self.at(tid)}
        args.update(changes)
        return session.return_api(call_id, {'rax': rax, 'rip': RETURN, 'rsp': rsp + 8}, **args)

    def end(self, session, **changes):
        args = {'at': self.at(), 'coverage': copy.deepcopy(COVERAGE), 'lost_events': 0,
                'truncated_events': 0, 'complete': True}
        args.update(changes)
        return session.end(**args)

    def assert_failed(self, session):
        report = session.report()
        self.assertFalse(report['integrity_passed'])
        self.assertEqual(report['state'], 'failed')
        self.assertIsNone(report['source_attribution'])
        self.assertIs(report['execution_ready'], False)
        self.assertTrue(report['diagnostics'])
        return report

    def test_two_threads_produced_capture_and_distinct_explicit_times(self):
        session = self.new()
        first = self.begin(session)
        second = self.begin(session, tid=22, rsp=0x2000, buf=0x5000)
        self.returned(session, first)
        self.returned(session, second, tid=22, rsp=0x2000, rax=0xdeadbeef80000000)
        result = self.end(session)
        self.assertTrue(result['integrity_passed'], result)
        self.assertEqual(result['audit']['identity']['creation_filetime'], IDENTITY['creation_filetime'])
        self.assertEqual(result['audit']['api_snapshots'][second]['decoded']['raw_bool'], -(1 << 31))
        self.assertEqual(self.reads, [(0x1000, 8), (0x2000, 8), (0x4000, 260), (0x5000, 260)])
        kinds = [row['kind'] for row in result['events']]
        self.assertEqual(kinds, ['run_start', 'call_enter', 'call_enter', 'api_snapshot',
                                 'call_return', 'api_snapshot', 'call_return', 'run_end'])
        snapshot, returned = result['events'][3:5]
        self.assertLess(snapshot['monotonic_ns'], returned['monotonic_ns'])
        self.assertIs(type(snapshot['utc_ns']), int)
        self.assertIsNone(result['source_attribution'])
        self.assertIs(result['execution_ready'], False)

    def test_nested_same_thread_same_return_address_has_separate_ids(self):
        session = self.new()
        outer = self.begin(session)
        inner = self.begin(session, rsp=0x2000, buf=0x5000)
        self.assertNotEqual(outer, inner)
        self.returned(session, inner, rsp=0x2000)
        self.returned(session, outer)
        result = self.end(session)
        self.assertTrue(result['integrity_passed'], result)
        snapshots = result['audit']['api_snapshots']
        self.assertEqual(snapshots[outer]['capture']['return_address'], snapshots[inner]['capture']['return_address'])

    def test_begin_finish_and_final_audit_are_real_component_calls(self):
        with patch.object(capture, 'begin_shell_folder_call', wraps=capture.begin_shell_folder_call) as begin:
            with patch.object(capture, 'finish_shell_folder_call', wraps=capture.finish_shell_folder_call) as finish:
                with patch.object(audit, 'audit_events', wraps=audit.audit_events) as checked:
                    session = self.new()
                    call_id = self.begin(session)
                    self.returned(session, call_id)
                    result = self.end(session)
        self.assertTrue(result['integrity_passed'])
        self.assertEqual(begin.call_count, 1)
        self.assertEqual(finish.call_count, 1)
        self.assertGreaterEqual(checked.call_count, 5)
        self.assertEqual(checked.call_args.args[0], result['events'])

    def test_bool_width_and_tail_are_kept_without_handmade_capture(self):
        session = self.new()
        call_id = self.begin(session)
        produced = self.returned(session, call_id, rax=0xdeadbeefffffffff)
        report = self.end(session)
        self.assertEqual(produced['raw_bool'], -1)
        self.assertEqual(bytes.fromhex(produced['raw_hex']), self.memory[0x4000]['data'])
        self.assertEqual(report['audit']['api_snapshots'][call_id]['decoded']['tail_bytes'],
                         {'encoding': 'hex', 'hex': b'\xfftail'.hex()})

    def test_second_site_uses_actual_low_register_fields(self):
        session = self.new()
        call_id = session.begin_api({'rcx': 0, 'rdx': 0x4000, 'r8': (123 << 32) | 0x1a,
                                     'r9': 456 << 32, 'rsp': 0x1000}, module_base=0x140000000,
                                    caller_rva=0xa56bec, encoding='ascii', read_limit=260,
                                    phase='第二站点', at=self.at())
        self.returned(session, call_id, rax=0)
        result = self.end(session)
        self.assertTrue(result['integrity_passed'])
        cap = result['audit']['api_snapshots'][call_id]['capture']
        self.assertEqual((cap['csidl'], cap['f_create'], cap['raw_bool']), (0x1a, 0, 0))

    def test_non_top_cross_thread_or_orphan_return_before_memory_read(self):
        for mode in ('outer', 'other_thread', 'orphan'):
            session = self.new()
            outer = self.begin(session)
            self.begin(session, rsp=0x2000, buf=0x5000)
            before = list(self.reads)
            with self.subTest(mode=mode), self.assertRaises(sessions.ObservationSessionError):
                self.returned(session, 'missing' if mode == 'orphan' else outer,
                              tid=22 if mode == 'other_thread' else 11)
            self.assertEqual(self.reads, before)
            self.assert_failed(session)

    def test_bad_rip_rsp_and_extra_registers_stop_before_buffer_read(self):
        for changes in ({'rip': RETURN + 1}, {'rsp': 0x1009}, {'rdx': 0x4000}, {'rax': True}):
            session = self.new()
            call_id = self.begin(session)
            regs = {'rax': 1, 'rip': RETURN, 'rsp': 0x1008, **changes}
            before = list(self.reads)
            with self.subTest(changes=changes), self.assertRaises(sessions.ObservationSessionError):
                session.return_api(call_id, regs, snapshot_at=self.at(), return_at=self.at())
            self.assertEqual(self.reads, before)
            report = self.assert_failed(session)
            self.assertEqual([row['kind'] for row in report['events']], ['run_start', 'call_enter'])
            self.assertEqual(report['pending_calls'][0]['call_id'], call_id)
            self.assertEqual(report['diagnostics'][0]['attempt']['call_id'], call_id)

    def test_stack_short_read_keeps_enter_and_failed_begin_pending(self):
        self.memory[0x1000] = {'data': b'1234567', 'complete': True}
        session = self.new()
        with self.assertRaises(sessions.ObservationSessionError):
            self.begin(session)
        report = self.assert_failed(session)
        self.assertEqual(len(report['events']), 2)
        self.assertFalse(report['pending_calls'][0]['entry_ready'])
        self.assertEqual(report['diagnostics'][0]['exception_type'], 'CallCaptureError')
        self.assertEqual(self.reads, [(0x1000, 8)])

    def test_buffer_incomplete_preserves_snapshot_and_no_fake_return(self):
        self.memory[0x4000] = {'data': b'x\0tail', 'complete': False}
        session = self.new()
        call_id = self.begin(session)
        with self.assertRaises(sessions.ObservationSessionError):
            self.returned(session, call_id)
        report = self.assert_failed(session)
        self.assertEqual([row['kind'] for row in report['events']], ['run_start', 'call_enter', 'api_snapshot'])
        bound = report['audit']['api_snapshots'][call_id]
        self.assertFalse(bound['capture']['read_complete'])
        self.assertFalse(bound['accepted'])
        self.assertTrue(report['pending_calls'])

    def test_short_complete_buffer_can_pass_but_unknown_success_cannot(self):
        session = self.new()
        self.memory[0x4000] = {'data': b'\0', 'complete': True}
        call_id = self.begin(session)
        self.returned(session, call_id)
        self.assertTrue(self.end(session)['integrity_passed'])
        session = self.new()
        self.memory[0x4000] = {'data': b'no nul', 'complete': True}
        call_id = self.begin(session)
        with self.assertRaises(sessions.ObservationSessionError):
            self.returned(session, call_id)
        self.assertIn('unknown_snapshot', self.assert_failed(session)['diagnostics'][0]['detail'])

    def test_callback_exceptions_keep_prefix_and_cannot_be_retried(self):
        for address in (0x1000, 0x4000):
            self.memory[0x1000] = {'data': RETURN.to_bytes(8, 'little'), 'complete': True}
            self.memory[0x4000] = {'data': b'x\0', 'complete': True}
            session = self.new()
            if address == 0x4000:
                call_id = self.begin(session)
            self.memory[address] = OSError('合成读取故障')
            with self.subTest(address=address), self.assertRaises(sessions.ObservationSessionError):
                if address == 0x1000:
                    self.begin(session)
                else:
                    self.returned(session, call_id)
            report = self.assert_failed(session)
            self.assertEqual(report['diagnostics'][0]['exception_type'], 'OSError')
            before = list(self.reads)
            self.memory[address] = {'data': b'x\0', 'complete': True}
            with self.assertRaises(sessions.ObservationSessionError):
                self.begin(session)
            with self.assertRaises(sessions.ObservationSessionError):
                self.end(session)
            self.assertEqual(self.reads, before)
            self.assertEqual(report['events'], session.report()['events'])

    def test_callback_interrupt_is_propagated_and_session_is_sealed(self):
        def interrupted(address, size):
            raise KeyboardInterrupt('合成中断')
        session = self.new(read_memory=interrupted)
        with self.assertRaises(KeyboardInterrupt):
            self.begin(session)
        report = self.assert_failed(session)
        self.assertEqual(report['diagnostics'][0]['exception_type'], 'KeyboardInterrupt')
        self.assertEqual(len(report['events']), 2)
        with self.assertRaises(sessions.ObservationSessionError):
            self.begin(session)

    def test_duplicate_return_and_second_end_never_restore_success(self):
        session = self.new()
        call_id = self.begin(session)
        self.returned(session, call_id)
        before = list(self.reads)
        with self.assertRaises(sessions.ObservationSessionError):
            self.returned(session, call_id)
        self.assertEqual(self.reads, before)
        self.assert_failed(session)
        session = self.new()
        original = self.end(session)
        self.assertTrue(original['integrity_passed'])
        with self.assertRaises(sessions.ObservationSessionError):
            self.end(session)
        self.assert_failed(session)
        self.assertTrue(original['integrity_passed'])

    def test_end_after_pending_call_retains_failed_end_without_fabrication(self):
        session = self.new()
        call_id = self.begin(session)
        result = self.end(session)
        self.assertFalse(result['integrity_passed'])
        self.assertEqual(result['state'], 'failed')
        self.assertEqual(result['pending_calls'][0]['call_id'], call_id)
        self.assertEqual([row['kind'] for row in result['events']], ['run_start', 'call_enter', 'run_end'])
        self.assertIn('unreturned_call', {x['code'] for x in result['audit']['issues']})

    def test_lost_truncated_incomplete_and_coverage_are_caller_declarations(self):
        for changes in ({'lost_events': 1}, {'truncated_events': 2}, {'complete': False},
                        {'lost_events': True}, {'complete': 1},
                        {'coverage': {**COVERAGE, 'until': 'before_exit'}}):
            session = self.new()
            with self.subTest(changes=changes):
                result = self.end(session, **changes)
                self.assertFalse(result['integrity_passed'])
                self.assertEqual(result['state'], 'failed')
        for changes in ({'lost_events': 1}, {'truncated_events': True}):
            with self.subTest(start=changes), self.assertRaises(sessions.ObservationSessionError):
                self.new(**changes)

    def test_invalid_identity_stamps_and_extra_fields_are_rejected(self):
        for identity in ({**IDENTITY, 'pid': True}, {**IDENTITY, 'extra': 1},
                         {**IDENTITY, 'creation_filetime': float(134390106270047430)}):
            with self.subTest(identity=identity), self.assertRaises(sessions.ObservationSessionError):
                self.new(identity=identity)
        for at in ({**self.at(), 'pid': 456}, {**self.at(), 'tid': True},
                   {**self.at(), 'monotonic_ns': 1.0}):
            session = self.new()
            with self.subTest(at=at), self.assertRaises(sessions.ObservationSessionError):
                self.begin(session, at=at)
            self.assert_failed(session)

    def test_return_time_mismatch_is_rejected_before_read(self):
        for mode in ('tid', 'reversed'):
            session = self.new()
            call_id = self.begin(session)
            before = list(self.reads)
            a, b = self.at(), self.at(22 if mode == 'tid' else 11)
            if mode == 'reversed':
                b['monotonic_ns'] = a['monotonic_ns'] - 1
            with self.subTest(mode=mode), self.assertRaises(sessions.ObservationSessionError):
                session.return_api(call_id, {'rax': 1, 'rip': RETURN, 'rsp': 0x1008},
                                   snapshot_at=a, return_at=b)
            self.assertEqual(self.reads, before)

    def test_append_only_parse_file_and_same_path_separate_opens(self):
        session = self.new()
        session.append('call_enter', {'call_id': 'parse1', 'operation': 'parse', 'name': 'Parse',
                                     'phase': '合成解析', 'path': 'same.conf'}, at=self.at())
        call_id = self.begin(session)
        self.returned(session, call_id)
        for i in range(2):
            session.append('file_open', {'open_id': str(i), 'parse_call_id': 'parse1',
                                        'path': 'same.conf', 'success': True, 'handle': 'H', 'error': None}, at=self.at())
            session.append('file_read', {'open_id': str(i), 'parse_call_id': 'parse1', 'offset': 0,
                                        'requested': 1, 'transferred': 1, 'success': True, 'error': None}, at=self.at())
            session.append('file_close', {'open_id': str(i), 'success': True, 'error': None}, at=self.at())
        session.append('call_return', {'call_id': 'parse1', 'result': 1}, at=self.at())
        result = self.end(session)
        self.assertTrue(result['integrity_passed'], result)
        self.assertEqual(result['audit']['summary']['counts']['file_open'], 2)

    def test_append_cannot_forge_api_snapshot_start_end_or_identity(self):
        for kind, data in (('api_snapshot', {}), ('run_start', {}), ('run_end', {}),
                           ('call_enter', {'operation': 'api'}),
                           ('file_open', {'pid': 456})):
            session = self.new()
            with self.subTest(kind=kind), self.assertRaises(sessions.ObservationSessionError):
                session.append(kind, data, at=self.at())
            report = self.assert_failed(session)
            self.assertTrue(all(row['pid'] == IDENTITY['pid'] for row in report['events']))
        session = self.new()
        call_id = self.begin(session)
        before = list(self.reads)
        with self.assertRaises(sessions.ObservationSessionError):
            session.append('call_return', {'call_id': call_id, 'result': 1}, at=self.at())
        self.assertEqual(self.reads, before)

    def test_parse_duplicate_id_and_open_lifecycle_still_rejected_by_audit(self):
        for mode in ('duplicate', 'open'):
            session = self.new()
            data = {'call_id': 'p', 'operation': 'parse', 'name': 'Parse', 'phase': '阶段', 'path': 'same'}
            session.append('call_enter', data, at=self.at())
            if mode == 'open':
                session.append('file_open', {'open_id': 'o', 'parse_call_id': 'p', 'path': 'same',
                                            'success': True, 'handle': 'H', 'error': None}, at=self.at())
            with self.subTest(mode=mode), self.assertRaises(sessions.ObservationSessionError):
                session.append('call_enter' if mode == 'duplicate' else 'call_return',
                               data if mode == 'duplicate' else {'call_id': 'p', 'result': 1}, at=self.at())
            report = self.assert_failed(session)
            self.assertIn('audit_rejected', {x['code'] for x in report['diagnostics']})

    def test_events_after_end_and_callback_reentry_are_rejected(self):
        session = self.new()
        self.end(session)
        with self.assertRaises(sessions.ObservationSessionError):
            self.begin(session)
        self.assert_failed(session)
        session = None
        def read(address, size):
            try:
                self.end(session)
            except sessions.ObservationSessionError:
                pass
            return self.read(address, size)
        session = self.new(read_memory=read)
        with self.assertRaises(sessions.ObservationSessionError):
            self.begin(session)
        self.assert_failed(session)
        self.assertEqual(self.reads, [(0x1000, 8)])

    def test_input_objects_report_and_return_values_are_independently_owned(self):
        identity, coverage, start = copy.deepcopy(IDENTITY), copy.deepcopy(COVERAGE), self.at()
        before = copy.deepcopy((identity, coverage, start, self.memory))
        session = self.new(identity=identity, coverage=coverage, start_at=start)
        regs = {'rcx': 0, 'rdx': 0x4000, 'r8': 0x1c, 'r9': 0, 'rsp': 0x1000}
        entered = copy.deepcopy(regs)
        call_id = session.begin_api(regs, module_base=0x140000000, caller_rva=0xa56bbe,
                                    encoding='ascii', read_limit=260, phase='阶段', at=self.at())
        self.assertEqual(regs, entered)
        regs.clear()
        produced = self.returned(session, call_id)
        self.assertEqual((identity, coverage, start, self.memory), before)
        identity['pid'] = 999
        coverage['domains'].clear()
        start['tid'] = 99
        produced['raw_hex'] = ''
        report = self.end(session)
        self.assertTrue(report['integrity_passed'])
        report['events'].clear()
        report['audit']['api_snapshots'].clear()
        self.assertTrue(session.report()['events'])
        self.assertTrue(session.report()['audit']['api_snapshots'])

    def test_integer_filetime_and_original_parse_input_are_owned(self):
        identity = {**IDENTITY, 'creation_filetime': 134390106270047430}
        session = self.new(identity=identity)
        data = {'call_id': 'p', 'operation': 'parse', 'name': 'Parse', 'phase': '阶段', 'path': 'original.conf'}
        session.append('call_enter', data, at=self.at())
        data['path'] = 'changed.conf'
        session.append('call_return', {'call_id': 'p', 'result': 0}, at=self.at())
        report = self.end(session)
        self.assertTrue(report['integrity_passed'])
        self.assertIs(type(report['events'][0]['creation_filetime']), int)
        self.assertEqual(report['events'][0]['creation_filetime'], 134390106270047430)
        self.assertEqual(report['events'][1]['data']['path'], 'original.conf')

    def test_digest_is_of_assembled_events_and_no_local_clock_needed(self):
        with patch('time.time_ns', side_effect=AssertionError('不读时钟')):
            with patch('time.monotonic_ns', side_effect=AssertionError('不读时钟')):
                session = self.new()
                call_id = self.begin(session)
                self.returned(session, call_id)
                result = self.end(session)
        raw = ('\n'.join(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                                  allow_nan=False) for x in result['events']) + '\n').encode('utf-8')
        self.assertEqual(result['audit']['input']['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['audit']['input']['sha256_scope'], 'canonical_jsonl')
        self.assertIn('不是外部原始采集文件', result['digest_scope'])
        json.dumps(result, ensure_ascii=False, allow_nan=False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
