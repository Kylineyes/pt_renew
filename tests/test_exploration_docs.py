"""探索文档检查器的证据路径边界回归。"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('check_exploration_docs', ROOT / 'tools/check_exploration_docs.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class EvidenceLinkTests(unittest.TestCase):
    def test_local_evidence_is_not_portable_document(self):
        for target in ('../.local-analysis/missing.json', '../../other-tree/.local-analysis/a.md#旧锚点',
                       '../%2Elocal-analysis/missing.png', r'..\.local-analysis\missing.json'):
            with self.subTest(target=target):
                self.assertIsNone(CHECK.resolve(ROOT / 'docs/example.md', target))

    def test_external_and_absolute_links_remain_excluded(self):
        for target in ('https://example.invalid/a.md', 'C:/missing/evidence.json', '/missing/evidence.json'):
            with self.subTest(target=target):
                self.assertIsNone(CHECK.resolve(ROOT / 'docs/example.md', target))

    def test_repository_file_and_anchor_are_still_checked(self):
        source = ROOT / 'docs/example.md'
        self.assertEqual(CHECK.resolve(source, 'missing.md#段落'), (ROOT / 'docs/missing.md', '段落'))
        self.assertEqual(CHECK.resolve(source, '../src/missing.h'), (ROOT / 'src/missing.h', ''))
        self.assertEqual(CHECK.resolve(source, '#当前'), (source, '当前'))

    def test_similar_name_does_not_hide_document_links(self):
        source = ROOT / 'docs/example.md'
        self.assertIsNotNone(CHECK.resolve(source, '.local-analysis-not-evidence/missing.md'))
        self.assertIsNotNone(CHECK.resolve(source, 'local-analysis/missing.md'))


if __name__ == '__main__':
    unittest.main()
