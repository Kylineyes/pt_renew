"""实际提取核心输出到审计v2的离线互通测试；内存与身份全部为合成数据。"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import legacy_source_call_capture as capture
import audit_legacy_source_observation as audit

EVIDENCE = REPO / '.local-analysis/ex005-capture-binding-0174'
COVERAGE = {'from': 'before_first_target_instruction', 'until': 'process_exit',
            'domains': ['directory_api', 'parse', 'file_io']}


def produced(raw, *, caller=0xa56bbe, rax=0xffffffff, complete=True, encoding='ascii'):
    """实际调用begin/finish，不手造capture对象或重新实现提取算法。"""
    stack, buffer, returned = 0x1000, 0x4000, 0x140000123
    memory = {stack: {'data': returned.to_bytes(8, 'little'), 'complete': True},
              buffer: {'data': raw, 'complete': complete}}
    reads = []
    def read_memory(address, size):
        reads.append((address, size))
        return memory[address]
    entry = capture.begin_shell_folder_call(
        {'rcx': 0, 'rdx': buffer, 'r8': 0x1c if caller == 0xa56bbe else 0x1a,
         'r9': 0, 'rsp': stack}, module_base=0x140000000, caller_rva=caller,
        encoding=encoding, read_memory=read_memory)
    result = capture.finish_shell_folder_call(
        entry, {'rax': rax, 'rip': returned, 'rsp': stack + 8}, read_memory=read_memory)
    return result, reads


def events(captures):
    """为生产者输出附加独立调用身份；覆盖字段仅为合成声明。"""
    rows = []
    def add(kind, data, tid=11):
        rows.append({'schema_version': 2, 'run_id': '离线互通', 'seq': len(rows),
                     'pid': 123, 'creation_filetime': '134390106270047430', 'tid': tid,
                     'image_sha256': 'a' * 64, 'kind': kind,
                     'utc_ns': 1794573455000000000 + len(rows),
                     'monotonic_ns': 9007199254740993 + len(rows), 'data': data})
    add('run_start', {'coverage': copy.deepcopy(COVERAGE),
                      'lost_events': 0, 'truncated_events': 0})
    # 两个线程的进入交错；每个snapshot直接使用生产者返回的原对象。
    for index in range(len(captures)):
        add('call_enter', {'call_id': f'api-{index}', 'operation': 'api',
                           'name': 'SHGetSpecialFolderPathA', 'phase': '合成返回',
                           'path': None}, tid=11 + index)
    for index, value in enumerate(captures):
        add('api_snapshot', {'call_id': f'api-{index}', 'capture': value}, tid=11 + index)
        add('call_return', {'call_id': f'api-{index}', 'result': value['raw_bool']}, tid=11 + index)
    add('run_end', {'coverage': copy.deepcopy(COVERAGE), 'lost_events': 0,
                    'truncated_events': 0, 'complete': True, 'event_count': len(rows) + 1})
    return rows


class CaptureIntegrationTests(unittest.TestCase):
    def assert_no_execution_claim(self, report):
        self.assertIsNone(report['source_attribution'])
        self.assertIs(report['execution_ready'], False)

    def test_two_produced_sites_keep_signed_bool_tail_and_exact_identity(self):
        raw = b'X:\\synthetic\0\xfftail'
        first, reads = produced(raw)
        second, _ = produced(b'old-residue', caller=0xa56bec, rax=0)
        rows = events([first, second])
        before = copy.deepcopy(rows)
        result = audit.audit_events(rows)
        self.assertTrue(result['integrity_passed'], result)
        self.assertEqual(reads, [(0x1000, 8), (0x4000, 260)])
        self.assertEqual(result['identity']['creation_filetime'], '134390106270047430')
        bound = result['api_snapshots']['api-0']
        self.assertEqual(bound['capture'], first)
        self.assertEqual(bound['decoded']['raw_bool'], -1)
        self.assertEqual(bound['decoded']['raw_bytes'], {'encoding': 'hex', 'hex': raw.hex()})
        self.assertEqual(bound['decoded']['tail_bytes'], {'encoding': 'hex', 'hex': b'\xfftail'.hex()})
        self.assertEqual(bound['decoded']['path_text'], 'X:\\synthetic')
        failed = result['api_snapshots']['api-1']['decoded']
        self.assertEqual(failed['status'], 'api_failed')
        self.assertIsNone(failed['path_text'])
        self.assertEqual(rows, before)
        self.assert_no_execution_claim(result)

    def test_produced_incomplete_read_is_preserved_then_rejected(self):
        value, _ = produced(b'x\0tail', complete=False)
        self.assertFalse(value['read_complete'])
        result = audit.audit_events(events([value]))
        self.assertFalse(result['integrity_passed'])
        self.assertIn('incomplete_snapshot', {x['code'] for x in result['issues']})
        bound = result['api_snapshots']['api-0']
        self.assertFalse(bound['accepted'])
        self.assertEqual(bound['decoded']['raw_bytes']['hex'], b'x\0tail'.hex())
        self.assert_no_execution_claim(result)

    def test_produced_unknown_success_and_failed_bool_have_distinct_audit_results(self):
        for raw in (b'without-nul', b'\xff\0tail'):
            with self.subTest(raw=raw):
                value, _ = produced(raw, encoding='utf-8')
                rejected = audit.audit_events(events([value]))
                self.assertFalse(rejected['integrity_passed'])
                self.assertIn('unknown_snapshot', {x['code'] for x in rejected['issues']})
                failed, _ = produced(raw, rax=0, encoding='utf-8')
                accepted = audit.audit_events(events([failed]))
                self.assertTrue(accepted['integrity_passed'], accepted)
                self.assertIsNone(accepted['api_snapshots']['api-0']['decoded']['path_text'])
                self.assert_no_execution_claim(accepted)

    def test_produced_empty_success_and_260_byte_boundary_are_consumed(self):
        for raw, position in ((b'\0tail', 0), (b'x' * 259 + b'\0', 259)):
            with self.subTest(length=len(raw)):
                value, _ = produced(raw, rax=0x80000000)
                result = audit.audit_events(events([value]))
                self.assertTrue(result['integrity_passed'], result)
                decoded = result['api_snapshots']['api-0']['decoded']
                self.assertEqual(decoded['first_nul'], position)
                self.assertEqual(decoded['raw_bool'], -(1 << 31))
                self.assertEqual(decoded['raw_bytes']['hex'], raw.hex())
                self.assert_no_execution_claim(result)

    def test_produced_capture_still_requires_matching_return_event(self):
        value, _ = produced(b'x\0')
        rows = events([value])
        next(x for x in rows if x['kind'] == 'call_return')['data']['result'] = 1
        result = audit.audit_events(rows)
        self.assertFalse(result['integrity_passed'])
        self.assertIn('snapshot_return_mismatch', {x['code'] for x in result['issues']})
        self.assert_no_execution_claim(result)

    def test_jsonl_digest_covers_full_produced_capture_and_input_is_read_only(self):
        value, _ = produced(b'x\0\xfftail')
        raw = ('\r\n'.join(json.dumps(row, ensure_ascii=False) for row in events([value]))
               + '\r\n').encode('utf-8')
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE) as folder:
            path = Path(folder) / 'synthetic.jsonl'
            path.write_bytes(raw)
            result = audit.audit_jsonl(path)
            self.assertTrue(result['integrity_passed'], result)
            self.assertEqual(result['input']['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(result['input']['bytes_read'], len(raw))
            self.assertEqual(result['input']['sha256_scope'], 'full_input')
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(result['api_snapshots']['api-0']['capture'], value)
            self.assert_no_execution_claim(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
