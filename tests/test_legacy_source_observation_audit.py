"""联合观测审计的内存与本树合成JSONL测试；不采集或启动原软件。"""
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

EVIDENCE = REPO / '.local-analysis/ex005-observation-audit'
COVERAGE = {'from': 'before_first_target_instruction', 'until': 'process_exit',
            'domains': ['directory_api', 'parse', 'file_io']}
CREATED = 134390106270047430


def trace():
    """两个线程交错，线程内嵌套、同路径重复打开及失败打开无句柄。"""
    rows = []
    def add(kind, data, tid=11):
        rows.append({'schema_version': 1, 'run_id': '合成单运行', 'seq': len(rows), 'pid': 123,
                     'creation_filetime': str(CREATED), 'tid': tid, 'image_sha256': 'a' * 64,
                     'kind': kind, 'utc_ns': 1794573455000000000 + len(rows),
                     'monotonic_ns': 9007199254740993 + len(rows), 'data': data})
    def call(call_id, operation, tid=11):
        add('call_enter', {'call_id': call_id, 'operation': operation, 'name': '合成调用',
                          'phase': '最早用户解析', 'path': '虚构配置路径' if operation == 'parse' else None}, tid)
    def opened(open_id, handle, parse='p1', tid=11, success=True):
        add('file_open', {'open_id': open_id, 'parse_call_id': parse, 'path': '重复路径.conf',
                          'success': success, 'handle': handle, 'error': None if success else 2}, tid)
    def read(open_id, parse='p1', tid=11):
        add('file_read', {'open_id': open_id, 'parse_call_id': parse, 'offset': 0, 'requested': 8,
                          'transferred': 8, 'success': True, 'error': None}, tid)
    def close(open_id, tid=11):
        add('file_close', {'open_id': open_id, 'success': True, 'error': None}, tid)
    def returned(call_id, tid=11):
        add('call_return', {'call_id': call_id, 'result': 1}, tid)
    add('run_start', {'coverage': copy.deepcopy(COVERAGE), 'lost_events': 0, 'truncated_events': 0})
    call('p1', 'parse')
    call('a1', 'api')
    call('p2', 'parse', 22)
    opened('o2', 'H2', 'p2', 22)
    opened('o1', 'H1')
    read('o1')
    returned('a1')
    close('o1')
    opened('failed', None, success=False)
    opened('o3', 'H1')
    close('o3')
    returned('p1')
    read('o2', 'p2', 22)
    close('o2', 22)
    returned('p2', 22)
    add('run_end', {'coverage': copy.deepcopy(COVERAGE), 'lost_events': 0, 'truncated_events': 0,
                    'complete': True, 'event_count': len(rows) + 1})
    return rows


def reindex(rows):
    for i, row in enumerate(rows):
        row['seq'] = i
    if rows and rows[-1]['kind'] == 'run_end':
        rows[-1]['data']['event_count'] = len(rows)
    return rows


class ObservationAuditTests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'events.jsonl'

    def write(self, rows=None):
        rows = trace() if rows is None else rows
        self.path.write_bytes(('\n'.join(json.dumps(row, ensure_ascii=False) for row in rows) + '\n').encode('utf-8'))
        return self.path

    def codes(self, rows):
        result = audit.audit_events(rows)
        self.assertFalse(result['integrity_passed'])
        self.assertIsNone(result['source_attribution'])
        self.assertIs(result['execution_ready'], False)
        return {x['code'] for x in result['issues']}

    def cli(self, *args):
        return subprocess.run([sys.executable, '-I', '-B', str(REPO / 'tools/audit_legacy_source_observation.py'),
                               str(self.path), *map(str, args)], capture_output=True, timeout=10)

    def test_interleaved_nested_calls_and_duplicate_paths_pass_without_attribution(self):
        result = audit.audit_events(trace())
        self.assertTrue(result['integrity_passed'], result)
        self.assertIsNone(result['source_attribution'])
        self.assertIs(result['execution_ready'], False)
        self.assertEqual(result['identity']['creation_filetime'], str(CREATED))
        self.assertEqual(result['summary']['counts']['file_open'], 4)
        self.assertEqual(result['summary']['open_ids'], [])
        self.assertEqual(result['summary']['pending_calls'], [])

    def test_large_integer_filetime_and_clocks_remain_exact(self):
        rows = trace()
        rows[3]['creation_filetime'] = CREATED
        result = audit.audit_events(rows)
        self.assertTrue(result['integrity_passed'], result)
        self.write(rows)
        from_file = audit.audit_jsonl(self.path)
        self.assertTrue(from_file['integrity_passed'])
        self.assertEqual(from_file['identity']['creation_filetime'], '134390106270047430')
        self.assertEqual(json.loads(self.path.read_bytes().splitlines()[3])['utc_ns'], rows[3]['utc_ns'])

    def test_identity_cannot_change_mid_run_even_with_same_pid(self):
        for key, value in (('creation_filetime', str(CREATED + 1)), ('pid', 124),
                           ('run_id', '另一运行'), ('image_sha256', 'b' * 64)):
            with self.subTest(key=key):
                rows = trace()
                rows[5][key] = value
                self.assertIn('identity_changed', self.codes(rows))

    def test_noninteger_and_bool_cannot_impersonate_integer_fields(self):
        for key in ('schema_version', 'seq', 'pid', 'tid', 'utc_ns', 'monotonic_ns', 'creation_filetime'):
            for value in (True, False, 1.0, -1, None):
                with self.subTest(key=key, value=value):
                    rows = trace()
                    rows[0][key] = value
                    self.assertFalse(audit.audit_events(rows)['integrity_passed'])

    def test_filetime_noncanonical_strings_and_overflow_rejected(self):
        for value in ('0', '01', '+123', '1e17', '1.0', ' 123', '１２３', str(1 << 64), 1 << 64):
            with self.subTest(value=value):
                rows = trace()
                rows[0]['creation_filetime'] = value
                self.assertFalse(audit.audit_events(rows)['integrity_passed'])

    def test_sequence_gap_duplicate_and_reordering_rejected(self):
        for mode in ('gap', 'duplicate', 'reorder'):
            rows = trace()
            if mode == 'gap':
                rows[5]['seq'] += 1
            elif mode == 'duplicate':
                rows[5]['seq'] -= 1
            else:
                rows[4], rows[5] = rows[5], rows[4]
            with self.subTest(mode=mode):
                self.assertIn('sequence_gap', self.codes(rows))

    def test_monotonic_equal_allowed_utc_adjustment_does_not_fake_monotonic(self):
        rows = trace()
        rows[5]['monotonic_ns'] = rows[4]['monotonic_ns']
        rows[5]['utc_ns'] = 1
        self.assertTrue(audit.audit_events(rows)['integrity_passed'])
        rows[5]['monotonic_ns'] -= 1
        self.assertIn('clock_reversed', self.codes(rows))

    def test_missing_start_end_and_empty_stream(self):
        self.assertIn('missing_start', self.codes(reindex(trace()[1:])))
        self.assertIn('missing_end', self.codes(trace()[:-1]))
        self.assertIn('empty_input', self.codes([]))

    def test_end_does_not_allow_following_events_or_second_start(self):
        rows = trace()
        rows.append(copy.deepcopy(rows[-1]))
        self.assertIn('after_end', self.codes(rows))
        rows = trace()
        rows.insert(1, copy.deepcopy(rows[0]))
        self.assertIn('duplicate_start', self.codes(reindex(rows)))

    def test_loss_and_truncation_at_start_or_end_reject(self):
        for index in (0, -1):
            for key in ('lost_events', 'truncated_events'):
                rows = trace()
                rows[index]['data'][key] = 1
                with self.subTest(index=index, key=key):
                    self.assertIn('collection_loss', self.codes(rows))
                rows[index]['data'][key] = True
                self.assertIn('invalid_integer', self.codes(rows))

    def test_coverage_incomplete_duplicate_unknown_and_changed_rejected(self):
        for data in ({'from': 'after_first_read'}, {'until': 'before_exit'},
                     {'domains': ['parse']}, {'domains': ['parse', 'parse', 'file_io']},
                     {'domains': ['directory_api', 'parse', 'file_io', 'other']}):
            rows = trace()
            rows[0]['data']['coverage'].update(data)
            with self.subTest(data=data):
                self.assertIn('insufficient_coverage', self.codes(rows))
        rows = trace()
        rows[-1]['data']['coverage']['domains'].reverse()
        self.assertIn('coverage_changed', self.codes(rows))

    def test_end_incomplete_or_wrong_event_count(self):
        rows = trace()
        rows[-1]['data']['complete'] = 1
        self.assertIn('incomplete_end', self.codes(rows))
        rows[-1]['data']['complete'] = True
        rows[-1]['data']['event_count'] -= 1
        self.assertIn('count_mismatch', self.codes(rows))

    def test_cross_thread_or_non_lifo_return_rejected(self):
        rows = trace()
        rows[7]['tid'] = 22
        self.assertIn('return_mismatch', self.codes(rows))
        rows = trace()
        rows[7]['data']['call_id'] = 'p1'
        self.assertIn('return_mismatch', self.codes(rows))

    def test_duplicate_call_id_after_return_is_still_rejected(self):
        rows = trace()
        extra = copy.deepcopy(rows[2])
        extra['monotonic_ns'] = rows[7]['monotonic_ns']
        extra['utc_ns'] = rows[7]['utc_ns']
        rows.insert(8, extra)
        self.assertIn('duplicate_call', self.codes(reindex(rows)))

    def test_orphan_duplicate_and_unreturned_calls(self):
        rows = trace()
        rows[7]['data']['call_id'] = '不存在'
        self.assertIn('orphan_return', self.codes(rows))
        rows = trace()
        rows.insert(8, copy.deepcopy(rows[7]))
        self.assertIn('duplicate_return', self.codes(reindex(rows)))
        rows = trace()
        del rows[7]
        self.assertIn('unreturned_call', self.codes(reindex(rows)))

    def test_parse_result_and_return_before_close_are_not_accepted(self):
        rows = trace()
        rows[12]['data']['result'] = 2
        self.assertIn('invalid_parse_result', self.codes(rows))
        rows = trace()
        rows[8], rows[12] = rows[12], rows[8]
        self.assertIn('parse_has_open_file', self.codes(reindex(rows)))

    def test_failed_open_without_handle_is_valid_but_never_creates_resource(self):
        rows = trace()
        self.assertTrue(audit.audit_events(rows)['integrity_passed'])
        rows[10]['data']['open_id'] = 'failed'
        self.assertIn('duplicate_open', self.codes(rows))
        rows = trace()
        rows[6]['data']['open_id'] = 'failed'
        self.assertIn('unknown_open', self.codes(rows))

    def test_failure_handle_success_without_handle_and_active_handle_alias_rejected(self):
        for index, value, code in ((9, 'Hbad', 'failed_open_handle'),
                                   (5, None, 'invalid_text'), (5, 'H2', 'handle_already_open')):
            rows = trace()
            rows[index]['data']['handle'] = value
            with self.subTest(index=index, value=value):
                self.assertIn(code, self.codes(rows))

    def test_parse_link_must_exist_and_remain_on_same_thread(self):
        for index, key, value in ((5, 'parse_call_id', 'a1'), (5, 'parse_call_id', 'p2'),
                                   (6, 'parse_call_id', 'p2')):
            rows = trace()
            rows[index]['data'][key] = value
            with self.subTest(index=index, value=value):
                self.assertIn('invalid_parse_link', self.codes(rows))
        rows = trace()
        rows[6]['tid'] = 22
        self.assertIn('invalid_parse_link', self.codes(rows))

    def test_failed_close_retains_handle_and_can_be_retried(self):
        rows = trace()
        rows[8]['data'].update(success=False, error=5)
        self.assertIn('handle_already_open', self.codes(rows))
        retry = copy.deepcopy(rows[8])
        retry['data'].update(success=True, error=None)
        rows.insert(9, retry)
        self.assertTrue(audit.audit_events(reindex(rows))['integrity_passed'])

    def test_unclosed_file_in_end_summary_is_not_lost(self):
        rows = trace()
        del rows[14:16]
        result = audit.audit_events(reindex(rows))
        self.assertIn('unclosed_file', {x['code'] for x in result['issues']})
        self.assertEqual(result['summary']['open_ids'], ['o2'])

    def test_read_size_offset_and_error_semantics(self):
        for key, value in (('requested', True), ('offset', -1), ('transferred', 9),
                           ('offset', (1 << 64) - 1), ('error', 0)):
            rows = trace()
            rows[6]['data'][key] = value
            with self.subTest(key=key, value=value):
                self.assertFalse(audit.audit_events(rows)['integrity_passed'])
        rows = trace()
        rows[6]['data'].update(success=False, error=5, transferred=2)
        self.assertTrue(audit.audit_events(rows)['integrity_passed'])
        rows[6]['data'].update(success=True, error=None, transferred=0)
        self.assertTrue(audit.audit_events(rows)['integrity_passed'])

    def test_unknown_kind_extra_missing_fields_and_wrong_data_types(self):
        for mode in ('kind', 'extra', 'missing', 'data', 'schema'):
            rows = trace()
            if mode == 'kind':
                rows[0]['kind'] = 'property'
            elif mode == 'extra':
                rows[0]['source_attribution'] = '伪造结论'
            elif mode == 'missing':
                del rows[0]['tid']
            elif mode == 'data':
                rows[0]['data'] = []
            else:
                rows[0]['schema_version'] = 2
            with self.subTest(mode=mode):
                self.assertFalse(audit.audit_events(rows)['integrity_passed'])

    def test_malformed_json_utf8_blank_bom_and_nonobject_are_auditable(self):
        for raw in (b'{broken', b'\xff', b'\n', b'{}\n\n', b'\xef\xbb\xbf{}', b'[]', b'null'):
            self.path.write_bytes(raw)
            with self.subTest(raw=raw):
                result = audit.audit_jsonl(self.path)
                self.assertFalse(result['integrity_passed'])
                self.assertEqual(result['input']['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(result['input']['sha256_scope'], 'full_input')

    def test_duplicate_json_keys_nested_or_common_are_rejected(self):
        for raw in (b'{"seq":0,"seq":1}', b'{"data":{"call_id":"a","call_id":"b"}}'):
            self.path.write_bytes(raw)
            result = audit.audit_jsonl(self.path)
            self.assertEqual(result['issues'][0]['code'], 'invalid_json')
            self.assertIn('重复JSON键', result['issues'][0]['detail'])

    def test_floats_exponents_and_nonfinite_json_numbers_rejected_without_rounding(self):
        for token in ('134390106270047430.0', '1e0', 'NaN', 'Infinity', '-Infinity'):
            raw = json.dumps(trace()[0]).replace('"' + str(CREATED) + '"', token).encode('utf-8')
            self.path.write_bytes(raw)
            with self.subTest(token=token):
                self.assertEqual(audit.audit_jsonl(self.path)['issues'][0]['code'], 'invalid_json')

    def test_crlf_and_no_final_newline_are_allowed_and_digest_is_raw(self):
        self.write()
        for raw in (self.path.read_bytes().replace(b'\n', b'\r\n'), self.path.read_bytes().rstrip(b'\n')):
            self.path.write_bytes(raw)
            result = audit.audit_jsonl(self.path)
            self.assertTrue(result['integrity_passed'], result)
            self.assertEqual(result['input']['sha256'], hashlib.sha256(raw).hexdigest())

    def test_byte_line_event_limits_are_explicit(self):
        self.path.write_bytes(b'x' * 21)
        with patch.object(audit, 'MAX_BYTES', 20):
            result = audit.audit_jsonl(self.path)
        self.assertEqual(result['issues'][0]['code'], 'input_too_large')
        self.assertEqual(result['input']['sha256_scope'], 'read_prefix')
        self.path.write_bytes(b'{}' * 10)
        with patch.object(audit, 'MAX_LINE_BYTES', 10):
            self.assertEqual(audit.audit_jsonl(self.path)['issues'][0]['code'], 'line_too_large')
        self.write()
        with patch.object(audit, 'MAX_EVENTS', 2):
            self.assertEqual(audit.audit_jsonl(self.path)['issues'][0]['code'], 'too_many_events')
            with self.assertRaises(audit.AuditError):
                audit.audit_events(trace())

    def test_cli_exit_codes_and_explicit_input_remain_unchanged(self):
        self.write()
        before = self.path.read_bytes()
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['integrity_passed'])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(set(self.root.iterdir()), {self.path})
        self.path.write_bytes(b'{invalid')
        result = self.cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['issues'][0]['code'], 'invalid_json')
        self.path.unlink()
        self.assertEqual(self.cli().returncode, 2)

    def test_memory_api_rejects_non_json_values_without_mutating_events(self):
        rows = trace()
        before = copy.deepcopy(rows)
        self.assertTrue(audit.audit_events(rows)['integrity_passed'])
        self.assertEqual(rows, before)
        for value in ({}, [set()], [float('nan')]):
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                audit.audit_events(value)

    def test_unreturned_api_call_is_reported_even_with_a_valid_end(self):
        rows = trace()
        rows = reindex([rows[0], rows[2], rows[-1]])
        result = audit.audit_events(rows)
        self.assertEqual({x['code'] for x in result['issues']}, {'unreturned_call'})
        self.assertEqual(result['summary']['pending_calls'], ['a1'])

    def test_strings_cannot_carry_escaped_surrogates_or_controls(self):
        for value in ('\ud800', '\x00', ' ', 'x' * 1025):
            rows = trace()
            rows[0]['run_id'] = value
            with self.subTest(value=repr(value)):
                if value == '\ud800':
                    # JSON可写转义代理项，但它不是合法UTF-8文本标识符。
                    raw = ('\n'.join(json.dumps(row) for row in rows)).encode('ascii')
                    self.path.write_bytes(raw)
                    self.assertEqual(audit.audit_jsonl(self.path)['issues'][0]['code'], 'invalid_text')
                else:
                    self.assertIn('invalid_text', self.codes(rows))

    def test_nested_parse_lifecycle_keeps_parent_and_child_separate(self):
        rows = trace()
        child = copy.deepcopy(rows[1])
        child['data']['call_id'] = 'child'
        child['monotonic_ns'] = rows[7]['monotonic_ns']
        child['utc_ns'] = rows[7]['utc_ns']
        returned = copy.deepcopy(rows[7])
        returned['data']['call_id'] = 'child'
        rows[8:8] = [child, returned]
        self.assertTrue(audit.audit_events(reindex(rows))['integrity_passed'])
        rows[9]['data']['call_id'] = 'p1'
        self.assertIn('return_mismatch', self.codes(rows))

    def test_raw_jsonl_only_reads_the_explicit_input(self):
        self.write()
        sibling = self.root / 'ignored.jsonl'
        sibling.write_bytes('不应读取'.encode('utf-8'))
        import io
        import contextlib
        output = io.StringIO()
        reads = []
        original = Path.open
        def opened(path, *args, **kwargs):
            reads.append(path)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', opened), contextlib.redirect_stdout(output):
            self.assertEqual(audit.main([str(self.path)]), 0)
        self.assertEqual(reads, [self.path])
        self.assertTrue(json.loads(output.getvalue())['integrity_passed'])

    def test_exclusive_output_refuses_existing_input_symlink_and_hardlink(self):
        self.write()
        output = self.root / 'report.json'
        first = self.cli('--output', output)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = {p: p.read_bytes() for p in (self.path, output)}
        for path in (output, self.path):
            with self.subTest(path=path):
                self.assertEqual(self.cli('--output', path).returncode, 2)
        hardlink = self.root / 'alias.json'
        hardlink.hardlink_to(self.path)
        self.assertEqual(self.cli('--output', hardlink).returncode, 2)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        link = self.root / 'link.json'
        try:
            link.symlink_to(output)
        except OSError:
            # Windows可能未授予符号链接权限；排他写的已存在普通文件和硬链接仍实际验过。
            return
        self.assertEqual(self.cli('--output', link).returncode, 2)
        self.assertEqual(output.read_bytes(), before[output])


if __name__ == '__main__':
    unittest.main()
