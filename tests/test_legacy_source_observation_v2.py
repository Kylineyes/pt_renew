"""schema v2只使用手造寄存器快照事件，不读进程或执行任何目标。"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import audit_legacy_source_observation as audit
import legacy_source_api_buffers as buffers
from test_legacy_source_observation_audit import trace as v1_trace

EVIDENCE = REPO / '.local-analysis/ex005-observation-v2'


def capture(*, caller=0xa56bbe, raw_bool=-1, raw=b'C:\\synthetic\0\xfftail'):
    return {'api': 'SHGetSpecialFolderPathA', 'module_base': 0x140000000,
            'caller_rva': caller, 'entry_rsp': 0x100000, 'return_address': 0x140a56bc4,
            'hwnd': 0, 'buffer_address': 0x200000,
            'csidl': 0x1c if caller == 0xa56bbe else 0x1a, 'f_create': 0,
            'raw_bool': raw_bool, 'raw_hex': raw.hex(), 'read_limit': 260,
            'read_complete': True, 'encoding': 'ascii'}


def reindex(rows):
    for i, row in enumerate(rows):
        row['seq'] = i
        row['monotonic_ns'] = 9007199254740993 + i
        row['utc_ns'] = 1794573455000000000 + i
    if rows[-1]['kind'] == 'run_end':
        rows[-1]['data']['event_count'] = len(rows)
    return rows


def trace():
    """保留v1的parse／文件关联，加入两个线程的两个站点快照。"""
    rows = []
    for index, source in enumerate(v1_trace()):
        row = copy.deepcopy(source)
        row['schema_version'] = 2
        if row['kind'] == 'call_enter' and row['data']['operation'] == 'api':
            row['data']['name'] = 'SHGetSpecialFolderPathA'
        if row['kind'] == 'call_return' and row['data']['call_id'] == 'a1':
            row['data']['result'] = -1
        rows.append(row)
        if index == 2:
            snap = copy.deepcopy(row)
            snap.update(kind='api_snapshot', data={'call_id': 'a1', 'capture': capture()})
            rows.append(snap)
        if index == 3:
            enter = copy.deepcopy(row)
            enter['data'] = {'call_id': 'a2', 'operation': 'api', 'name': 'SHGetSpecialFolderPathA',
                             'phase': '第二站点合成调用', 'path': None}
            snap = copy.deepcopy(enter)
            snap.update(kind='api_snapshot', data={'call_id': 'a2', 'capture': capture(
                caller=0xa56bec, raw_bool=0, raw=b'failure residue without nul')})
            returned = copy.deepcopy(enter)
            returned.update(kind='call_return', data={'call_id': 'a2', 'result': 0})
            rows.extend((enter, snap, returned))
    return reindex(rows)


def snapshot(rows, call_id='a1'):
    return next(row for row in rows if row['kind'] == 'api_snapshot' and row['data']['call_id'] == call_id)


def return_event(rows, call_id='a1'):
    return next(row for row in rows if row['kind'] == 'call_return' and row['data']['call_id'] == call_id)


class ObservationV2Tests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'events.jsonl'

    def rejected(self, rows, code):
        report = audit.audit_events(rows)
        self.assertFalse(report['integrity_passed'], report)
        self.assertIn(code, {x['code'] for x in report['issues']}, report)
        self.assertIsNone(report['source_attribution'])
        self.assertIs(report['execution_ready'], False)
        return report

    def test_two_sites_signed_bool_failure_residue_and_locations(self):
        rows = trace()
        report = audit.audit_events(rows)
        self.assertTrue(report['integrity_passed'], report)
        self.assertEqual(report['schema_version'], 2)
        self.assertEqual(report['summary']['counts']['api_snapshot'], 2)
        self.assertEqual(report['summary']['counts']['file_open'], 4)
        self.assertEqual(set(report['api_snapshots']), {'a1', 'a2'})
        for call_id in ('a1', 'a2'):
            bound = report['api_snapshots'][call_id]
            row = snapshot(rows, call_id)
            self.assertEqual((bound['line'], bound['seq'], bound['tid']),
                             (rows.index(row) + 1, row['seq'], row['tid']))
            self.assertEqual(bound['capture'], row['data']['capture'])
            self.assertTrue(bound['accepted'])
        decoded = report['api_snapshots']['a1']['decoded']
        self.assertEqual(decoded['raw_bool'], -1)
        self.assertEqual(decoded['path_text'], 'C:\\synthetic')
        self.assertEqual(decoded['tail_bytes'], {'encoding': 'hex', 'hex': b'\xfftail'.hex()})
        failed = report['api_snapshots']['a2']['decoded']
        self.assertEqual(failed['status'], 'api_failed')
        self.assertEqual(failed['buffer_status'], 'unknown')
        self.assertIsNone(failed['path_text'])
        self.assertTrue(failed['fallback_required'])
        self.assertIsNone(report['source_attribution'])
        self.assertIs(report['execution_ready'], False)
        json.dumps(report, ensure_ascii=False, allow_nan=False)

    def test_calls_existing_decoder_and_does_not_modify_events(self):
        rows = trace()
        before = copy.deepcopy(rows)
        with patch.object(buffers, 'decode_shell_folder', wraps=buffers.decode_shell_folder) as decoder:
            report = audit.audit_events(rows)
        self.assertTrue(report['integrity_passed'])
        self.assertEqual(decoder.call_count, 2)
        self.assertEqual(decoder.call_args_list[0].kwargs['raw_bytes'],
                         bytes.fromhex(snapshot(rows)['data']['capture']['raw_hex']))
        self.assertEqual(rows, before)

    def test_every_capture_field_required_and_unknown_field_rejected(self):
        original = capture()
        for key in original:
            rows = trace()
            del snapshot(rows)['data']['capture'][key]
            with self.subTest(missing=key):
                self.rejected(rows, 'invalid_fields')
        rows = trace()
        snapshot(rows)['data']['capture']['extra'] = 0
        self.rejected(rows, 'invalid_fields')
        rows = trace()
        snapshot(rows)['data']['extra'] = 0
        self.rejected(rows, 'invalid_fields')

    def test_exact_integer_capture_fields_reject_bool_float_and_strings(self):
        names = ('module_base', 'caller_rva', 'entry_rsp', 'return_address', 'hwnd',
                 'buffer_address', 'csidl', 'f_create', 'raw_bool', 'read_limit')
        for name in names:
            for value in (True, 1.0, '1'):
                rows = trace()
                snapshot(rows)['data']['capture'][name] = value
                with self.subTest(name=name, value=value):
                    report = audit.audit_events(rows)
                    self.assertFalse(report['integrity_passed'])

    def test_invalid_site_csidl_and_api_names(self):
        for field, value, code in (('caller_rva', 0xa56bbb, 'invalid_call_site'),
                                   ('csidl', 0x1a, 'site_csidl_mismatch'),
                                   ('api', 'OtherAPI', 'invalid_capture_api'),
                                   ('hwnd', 1, 'invalid_integer'), ('f_create', 1, 'invalid_integer')):
            rows = trace()
            snapshot(rows)['data']['capture'][field] = value
            with self.subTest(field=field):
                self.rejected(rows, code)
        rows = trace()
        next(row for row in rows if row['kind'] == 'call_enter' and row['data']['call_id'] == 'a1')['data']['name'] = 'OtherAPI'
        self.rejected(rows, 'unsupported_v2_api')

    def test_unsigned_address_zero_overflow_and_exact_upper_edges(self):
        for field in ('module_base', 'entry_rsp', 'return_address', 'buffer_address'):
            for value in (0, -1, 1 << 64):
                rows = trace()
                snapshot(rows)['data']['capture'][field] = value
                with self.subTest(field=field, value=value):
                    self.rejected(rows, 'invalid_integer')
        for field, value in (('module_base', audit.UINT64_MAX), ('entry_rsp', audit.UINT64_MAX - 7),
                             ('buffer_address', audit.UINT64_MAX - 259)):
            rows = trace()
            snapshot(rows)['data']['capture'][field] = value
            with self.subTest(field=field):
                self.rejected(rows, 'address_overflow')
        rows = trace()
        cap = snapshot(rows)['data']['capture']
        cap.update(module_base=audit.UINT64_MAX - cap['caller_rva'], entry_rsp=audit.UINT64_MAX - 8,
                   return_address=audit.UINT64_MAX, buffer_address=audit.UINT64_MAX - cap['read_limit'])
        self.assertTrue(audit.audit_events(rows)['integrity_passed'])

    def test_signed_bool_extremes_and_raw_return_must_match(self):
        for value in (-(1 << 31), -1, 1, (1 << 31) - 1):
            rows = trace()
            snapshot(rows)['data']['capture']['raw_bool'] = value
            return_event(rows)['data']['result'] = value
            with self.subTest(value=value):
                report = audit.audit_events(rows)
                self.assertTrue(report['integrity_passed'], report)
                self.assertEqual(report['api_snapshots']['a1']['decoded']['raw_bool'], value)
        for value in (-(1 << 31) - 1, 1 << 31):
            rows = trace()
            snapshot(rows)['data']['capture']['raw_bool'] = value
            self.rejected(rows, 'invalid_integer')
        rows = trace()
        return_event(rows)['data']['result'] = 1
        self.rejected(rows, 'snapshot_return_mismatch')

    def test_raw_hex_is_explicit_canonical_and_lossless(self):
        for raw_hex in ('A0', '0', '0x00', '00 00', 'gg', '00' * 261, [], None):
            rows = trace()
            snapshot(rows)['data']['capture']['raw_hex'] = raw_hex
            with self.subTest(raw_hex=repr(raw_hex)):
                self.rejected(rows, 'invalid_raw_hex')
        rows = trace()
        snapshot(rows)['data']['capture'].update(raw_hex='0000', read_limit=1)
        self.rejected(rows, 'capture_overread')

    def test_read_limit_bounds_and_260_byte_complete_boundary(self):
        for value in (0, 261, -1):
            rows = trace()
            snapshot(rows)['data']['capture']['read_limit'] = value
            with self.subTest(value=value):
                self.rejected(rows, 'invalid_integer')
        rows = trace()
        snapshot(rows)['data']['capture']['raw_hex'] = (b'x' * 259 + b'\0').hex()
        report = audit.audit_events(rows)
        self.assertTrue(report['integrity_passed'])
        self.assertEqual(report['api_snapshots']['a1']['decoded']['first_nul'], 259)
        snapshot(rows)['data']['capture'].update(read_limit=1, raw_hex='00')
        self.assertTrue(audit.audit_events(rows)['integrity_passed'])

    def test_incomplete_read_rejected_even_with_nul_or_failed_bool(self):
        for call_id in ('a1', 'a2'):
            rows = trace()
            snapshot(rows, call_id)['data']['capture'].update(read_complete=False, raw_hex='00')
            with self.subTest(call_id=call_id):
                report = self.rejected(rows, 'incomplete_snapshot')
                self.assertFalse(report['api_snapshots'][call_id]['accepted'])
                self.assertIn('incomplete_read', report['api_snapshots'][call_id]['decoded']['issues'])
        for value in (0, 1, 'true', None):
            rows = trace()
            snapshot(rows)['data']['capture']['read_complete'] = value
            self.rejected(rows, 'invalid_read_complete')

    def test_nonzero_bool_unknown_decode_rejected_but_failure_residue_preserved(self):
        for raw in (b'no nul', b'\xff\0'):
            rows = trace()
            snapshot(rows)['data']['capture']['raw_hex'] = raw.hex()
            with self.subTest(raw=raw):
                report = self.rejected(rows, 'unknown_snapshot')
                self.assertEqual(report['api_snapshots']['a1']['decoded']['status'], 'unknown')
            snapshot(rows)['data']['capture']['raw_bool'] = 0
            return_event(rows)['data']['result'] = 0
            report = audit.audit_events(rows)
            self.assertTrue(report['integrity_passed'], report)
            self.assertIsNone(report['api_snapshots']['a1']['decoded']['path_text'])

    def test_encoding_must_be_explicit_supported_and_original_name_preserved(self):
        for encoding in ('', 'made-up', 'utf-16', None, 1252):
            rows = trace()
            snapshot(rows)['data']['capture']['encoding'] = encoding
            with self.subTest(encoding=encoding):
                self.rejected(rows, 'invalid_capture_buffer')
        rows = trace()
        snapshot(rows)['data']['capture'].update(encoding='UTF8', raw_hex='00ff')
        report = audit.audit_events(rows)
        self.assertTrue(report['integrity_passed'])
        self.assertEqual(report['api_snapshots']['a1']['decoded']['encoding'], 'UTF8')
        self.assertEqual(report['api_snapshots']['a1']['decoded']['canonical_encoding'], 'utf-8')
        self.assertEqual(report['api_snapshots']['a1']['decoded']['status'], 'success_empty')

    def test_orphan_cross_thread_non_api_and_non_top_snapshots(self):
        rows = trace()
        snapshot(rows)['data']['call_id'] = 'not-entered'
        self.rejected(rows, 'orphan_snapshot')
        rows = trace()
        snapshot(rows)['tid'] = 22
        self.rejected(rows, 'snapshot_mismatch')
        rows = trace()
        snapshot(rows)['data']['call_id'] = 'p1'
        self.rejected(rows, 'snapshot_mismatch')
        rows = trace()
        snap = snapshot(rows)
        nested = copy.deepcopy(rows[2])
        nested['data']['call_id'] = 'inner'
        rows.insert(rows.index(snap), nested)
        self.rejected(reindex(rows), 'snapshot_mismatch')

    def test_duplicate_snapshot_and_snapshot_after_return_rejected(self):
        rows = trace()
        snap = snapshot(rows)
        rows.insert(rows.index(snap) + 1, copy.deepcopy(snap))
        self.rejected(reindex(rows), 'duplicate_snapshot')
        rows = trace()
        snap = rows.pop(rows.index(snapshot(rows)))
        rows.insert(rows.index(return_event(rows)) + 1, snap)
        self.rejected(reindex(rows), 'missing_snapshot')
        rows = trace()
        snap = copy.deepcopy(snapshot(rows))
        rows.insert(rows.index(return_event(rows)) + 1, snap)
        self.rejected(reindex(rows), 'snapshot_mismatch')

    def test_missing_snapshot_and_call_binding_fields_are_not_repaired(self):
        rows = trace()
        rows.remove(snapshot(rows))
        self.rejected(reindex(rows), 'missing_snapshot')
        rows = trace()
        del snapshot(rows)['data']['call_id']
        self.rejected(rows, 'invalid_fields')
        rows = trace()
        snapshot(rows)['data']['capture'] = []
        self.rejected(rows, 'invalid_fields')

    def test_mixed_versions_and_unknown_version_rejected(self):
        for index, version in ((0, 1), (3, 1), (-1, 1)):
            rows = trace()
            rows[index]['schema_version'] = version
            with self.subTest(index=index):
                self.rejected(rows, 'mixed_schema_versions')
        for version in (0, 3, True, '2'):
            rows = trace()
            rows[0]['schema_version'] = version
            self.rejected(rows, 'invalid_integer')

    def test_v1_retains_generic_api_and_rejects_snapshot_without_global_changes(self):
        rows = v1_trace()
        report = audit.audit_events(rows)
        self.assertTrue(report['integrity_passed'])
        self.assertEqual(report['schema_version'], 1)
        self.assertNotIn('api_snapshots', report)
        snap = copy.deepcopy(snapshot(trace()))
        snap['schema_version'] = 1
        rows.insert(3, snap)
        self.rejected(reindex(rows), 'unknown_kind')
        self.assertNotIn('api_snapshot', audit.KINDS)

    def test_full_original_jsonl_digest_includes_snapshot_and_raw_tail(self):
        rows = trace()
        raw = ('\r\n'.join(json.dumps(row, ensure_ascii=False) for row in rows)).encode('utf-8')
        self.path.write_bytes(raw)
        report = audit.audit_jsonl(self.path)
        self.assertTrue(report['integrity_passed'], report)
        self.assertEqual(report['input']['bytes_read'], len(raw))
        self.assertEqual(report['input']['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(report['input']['sha256_scope'], 'full_input')
        filtered = b'\r\n'.join(line for line in raw.split(b'\r\n') if b'api_snapshot' not in line)
        self.assertNotEqual(report['input']['sha256'], hashlib.sha256(filtered).hexdigest())
        snapshot(rows)['data']['capture']['raw_hex'] += '00'
        self.path.write_bytes(('\n'.join(json.dumps(row) for row in rows)).encode('utf-8'))
        changed = audit.audit_jsonl(self.path)
        self.assertTrue(changed['integrity_passed'])
        self.assertNotEqual(changed['input']['sha256'], report['input']['sha256'])
        self.assertEqual(self.path.read_bytes(), ('\n'.join(json.dumps(row) for row in rows)).encode('utf-8'))

    def test_cli_json_has_explicit_bytes_and_preserves_exclusive_output(self):
        raw = ('\n'.join(json.dumps(row) for row in trace()) + '\n').encode('utf-8')
        self.path.write_bytes(raw)
        command = [sys.executable, '-I', '-B', str(REPO / 'tools/audit_legacy_source_observation.py'), str(self.path)]
        result = subprocess.run(command, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['api_snapshots']['a1']['decoded']['raw_bytes'],
                         {'encoding': 'hex', 'hex': snapshot(trace())['data']['capture']['raw_hex']})
        output = self.root / 'report.json'
        created = subprocess.run([*command, '--output', str(output)], capture_output=True, timeout=10)
        self.assertEqual(created.returncode, 0, created.stderr)
        before = output.read_bytes()
        refused = subprocess.run([*command, '--output', str(output)], capture_output=True, timeout=10)
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(output.read_bytes(), before)
        self.assertEqual(self.path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
