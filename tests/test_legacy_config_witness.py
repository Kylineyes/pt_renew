"""冻结配置文字见证器的合成边界测试；不读取用户配置或运行目标程序。"""
from pathlib import Path
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import inspect_legacy_config_witness as witness

EVIDENCE = REPO / '.local-analysis/ex005-config-witness'


class ConfigWitnessTests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.left = self.root / 'left.conf'
        self.right = self.root / 'right.conf'
        self.left.write_text('[sdl]\nfulldouble=false\n', encoding='utf-8')
        self.right.write_bytes(self.left.read_bytes())

    def inspect(self, *pairs, **kwargs):
        return witness.inspect_witness(self.left, self.right,
                                       pairs or [('sdl', 'fulldouble')], **kwargs)

    def cli(self, *extra):
        return subprocess.run([sys.executable, '-I', '-B',
                               str(REPO / 'tools/inspect_legacy_config_witness.py'),
                               str(self.left), str(self.right), '--candidate', 'sdl/fulldouble',
                               *map(str, extra)], capture_output=True, timeout=10)

    def test_present_absent_and_exact_input_digest(self):
        self.right.write_text('[dosbox]\nmemsize=16\n[sdl]\nwaitonerror=true\n', encoding='utf-8')
        result = self.inspect(('sdl', 'fulldouble'), ('sdl', 'waitonerror'), ('dosbox', 'memsize'))
        self.assertEqual([x['explicit_override'] for x in result['inputs'][0]['candidates']],
                         ['present', 'absent', 'absent'])
        self.assertEqual([x['explicit_override'] for x in result['inputs'][1]['candidates']],
                         ['absent', 'present', 'present'])
        for path, item in zip((self.left, self.right), result['inputs']):
            self.assertEqual(item['bytes'], len(path.read_bytes()))
            self.assertEqual(item['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertIsNone(result['comparisons'][0]['text_distinguishable'])

    def test_equal_values_and_identical_copies_cannot_attribute_source(self):
        result = self.inspect()
        self.assertTrue(result['input_bytes_equal'])
        self.assertTrue(result['comparisons'][0]['single_value_text_equal'])
        self.assertFalse(result['comparisons'][0]['text_distinguishable'])
        self.assertIsNone(result['comparisons'][0]['source_attribution'])
        self.assertTrue(all(value is None for value in result['unknown'].values()))
        for item in result['inputs']:
            self.assertTrue(all(value is None for value in item['candidates'][0]['unknown'].values()))

    def test_case_spaces_comments_and_raw_values_preserved(self):
        self.left.write_bytes(b';fulldouble=ignored\r\n [ SDL ] \r\n FullDouble \t= false \t\r\n')
        result = self.inspect(('SDL', 'FULLDOUBLE'))
        occurrence = result['inputs'][0]['candidates'][0]['occurrences'][0]
        self.assertEqual(occurrence, {'line': 3, 'section_line': 2,
            'raw_line': ' FullDouble \t= false \t', 'raw_key': ' FullDouble \t',
            'raw_value': ' false \t', 'value_text': 'false'})
        self.assertFalse(result['comparisons'][0]['raw_value_sequences_equal'])
        self.assertTrue(result['comparisons'][0]['single_value_text_equal'])

    def test_different_text_is_only_text_evidence(self):
        self.right.write_text('[sdl]\nfulldouble=true\n', encoding='utf-8')
        result = self.inspect()['comparisons'][0]
        self.assertTrue(result['text_distinguishable'])
        self.assertIsNone(result['source_attribution'])

    def test_duplicate_keys_keep_every_value_without_last_wins(self):
        self.left.write_text('[sdl]\nfulldouble=false\nfulldouble=true\n', encoding='utf-8')
        result = self.inspect()
        item = result['inputs'][0]['candidates'][0]
        self.assertEqual([x['line'] for x in item['occurrences']], [2, 3])
        self.assertEqual([x['raw_value'] for x in item['occurrences']], ['false', 'true'])
        self.assertIn('duplicate_key', item['ambiguity_reasons'])
        self.assertIsNone(result['comparisons'][0]['single_value_text_equal'])
        self.assertIsNone(item['unknown']['effective_value'])

    def test_duplicate_sections_ambiguous_even_without_duplicate_key(self):
        self.left.write_text('[sdl]\nfulldouble=false\n[SDL]\nwaitonerror=true\n', encoding='utf-8')
        item = self.inspect()['inputs'][0]['candidates'][0]
        self.assertEqual(item['section_lines'], [1, 3])
        self.assertEqual(item['ambiguity_reasons'], ['duplicate_section'])
        self.assertEqual(item['explicit_override'], 'present')

    def test_absence_in_duplicate_section_is_unknown(self):
        self.left.write_text('[sdl]\n[SDL]\n', encoding='utf-8')
        item = self.inspect()['inputs'][0]['candidates'][0]
        self.assertEqual(item['explicit_override'], 'unknown')

    def test_autoexec_equals_and_malformed_looking_commands_are_not_properties(self):
        self.left.write_text('[autoexec]\nfulldouble=true\nset X=Y\n[not a header\n'
                             '[sdl]\nfulldouble=false\n', encoding='utf-8')
        result = self.inspect(('sdl', 'fulldouble'), ('autoexec', 'fulldouble'))
        ordinary, command = result['inputs'][0]['candidates']
        self.assertEqual(ordinary['occurrences'][0]['line'], 6)
        self.assertFalse(result['inputs'][0]['issues'])
        self.assertEqual(command['occurrences'], [])
        self.assertEqual(command['explicit_override'], 'unknown')
        self.assertIn('autoexec_is_command_text', command['ambiguity_reasons'])

    def test_malformed_lines_invalidate_absence_without_guessing_section(self):
        for text, code in (('[sdl] # suffix\nfulldouble=true\n', 'malformed_section'),
                           ('[sdl]\nfulldouble true\n', 'non_property_line'),
                           ('[sdl]\n=value\n', 'malformed_key'),
                           ('fulldouble=true\n', 'outside_section'),
                           ('[]\nfulldouble=true\n', 'malformed_section'),
                           ('[bad$]\nfulldouble=true\n', 'malformed_section')):
            with self.subTest(code=code):
                self.left.write_text(text, encoding='utf-8')
                report = self.inspect()['inputs'][0]
                self.assertEqual(report['issues'][0]['code'], code)
                self.assertEqual(report['candidates'][0]['explicit_override'], 'unknown')
                self.assertEqual(report['candidates'][0]['occurrences'], [])

    def test_malformed_elsewhere_does_not_hide_match_but_blocks_unique_comparison(self):
        self.left.write_text('[sdl]\nfulldouble=false\n[other]\nbroken\n', encoding='utf-8')
        result = self.inspect()
        self.assertEqual(result['inputs'][0]['candidates'][0]['explicit_override'], 'present')
        self.assertTrue(result['inputs'][0]['candidates'][0]['ambiguous'])
        self.assertIsNone(result['comparisons'][0]['single_value_text_equal'])
        self.assertTrue(result['comparisons'][0]['raw_value_sequences_equal'])

    def test_empty_quoted_inline_comment_and_equals_values_remain_literal(self):
        for value in ('', '"false"', 'false # note', 'false;note', 'x=y'):
            with self.subTest(value=value):
                self.left.write_text('[sdl]\nfulldouble=' + value + '\n', encoding='utf-8')
                item = self.inspect()['inputs'][0]['candidates'][0]
                self.assertEqual(item['occurrences'][0]['raw_value'], value)
                self.assertFalse(item['ambiguous'])
                self.assertIsNone(item['unknown']['legal_values'])

    def test_strict_decode_failure_retains_hash_without_replacement(self):
        self.left.write_bytes(b'[sdl]\nfulldouble=\xff\n')
        result = self.inspect()
        item = result['inputs'][0]
        self.assertFalse(item['scan_complete'])
        self.assertEqual(item['issues'][0]['code'], 'decode_error')
        self.assertEqual(item['candidates'][0]['explicit_override'], 'unknown')
        self.assertEqual(item['sha256'], hashlib.sha256(self.left.read_bytes()).hexdigest())
        self.assertIsNone(result['comparisons'][0]['raw_value_sequences_equal'])

    def test_bom_and_explicit_encoding_without_autodetection(self):
        self.left.write_bytes('[sdl]\nfulldouble=false\n'.encode('utf-8-sig'))
        self.assertFalse(self.inspect()['inputs'][0]['issues'])
        self.left.write_bytes('[sdl]\nfulldouble=false\n'.encode('utf-16'))
        self.assertTrue(self.inspect()['inputs'][0]['issues'])
        self.assertTrue(self.inspect(left_encoding='utf-16')['comparisons'][0]['single_value_text_equal'])
        self.left.write_bytes('; café\n[sdl]\nfulldouble=false\n'.encode('cp1252'))
        self.assertTrue(self.inspect(left_encoding='cp1252')['comparisons'][0]['single_value_text_equal'])

    def test_nul_and_unicode_separators_are_not_silently_split_or_discarded(self):
        for char in ('\0', '\x1a', '\u0085', '\u2028', '\u2029', '\ufeff'):
            with self.subTest(char=repr(char)):
                self.left.write_text('[sdl]\nfulldouble=false' + char + 'fulldouble=true\n', encoding='utf-8')
                item = self.inspect()['inputs'][0]
                self.assertEqual(item['issues'][0]['line'], 2)
                self.assertEqual(item['issues'][0]['code'], 'unsupported_control')
                self.assertEqual(item['candidates'][0]['occurrences'], [])

    def test_candidate_bounds_and_duplicate_names_rejected(self):
        for pairs in ([], [('sdl', 'x')] * 4, [('SDL', 'X'), ('sdl', 'x')],
                      [('sdl', '')], [('sdl', 'x/y')]):
            with self.subTest(pairs=pairs), self.assertRaises(ValueError):
                witness.inspect_witness(self.left, self.right, pairs)

    def test_cli_stdout_only_reads_two_explicit_files_and_preserves_inputs(self):
        before = {p: p.read_bytes() for p in (self.left, self.right)}
        reads = []
        original = Path.read_bytes
        def read(path):
            reads.append(path)
            return original(path)
        output = io.StringIO()
        with patch.object(Path, 'read_bytes', read), contextlib.redirect_stdout(output):
            self.assertEqual(witness.main([str(self.left), str(self.right),
                                          '--candidate', 'sdl/fulldouble']), 0)
        self.assertEqual(reads, [self.left, self.right])
        self.assertEqual(json.loads(output.getvalue())['schema_version'], 1)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(set(self.root.iterdir()), {self.left, self.right})
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['input_bytes_equal'])

    def test_cli_output_exclusive_and_cannot_overwrite_inputs_or_evidence(self):
        output = self.root / 'report.json'
        first = self.cli('--output', output)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, b'')
        before = {p: p.read_bytes() for p in (self.left, self.right, output)}
        for path in before:
            with self.subTest(path=path):
                result = self.cli('--output', path)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(path.read_bytes(), before[path])

    def test_output_hardlink_to_input_is_not_overwritten(self):
        alias = self.root / 'alias.json'
        os.link(self.left, alias)
        before = self.left.read_bytes()
        self.assertEqual(self.cli('--output', alias).returncode, 2)
        self.assertEqual(self.left.read_bytes(), before)

    def test_cli_rejects_invalid_candidates_and_missing_input_without_output(self):
        output = self.root / 'not-created.json'
        for extra in (('--candidate', 'sdl/fulldouble'),
                      ('--candidate', 'sdl/one', '--candidate', 'sdl/two', '--candidate', 'sdl/three'),
                      ('--candidate', 'invalid')):
            result = self.cli(*extra, '--output', output)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())
        self.right.unlink()
        self.assertEqual(self.cli('--output', output).returncode, 2)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
