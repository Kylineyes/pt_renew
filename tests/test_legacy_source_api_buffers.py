"""目录返回快照的合成边界测试；不调用真实 API 或读取用户配置。"""
from pathlib import Path
import importlib.util
import locale
import os
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('legacy_source_api_buffers',
                                             REPO / 'tools/legacy_source_api_buffers.py')
buffers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(buffers)
EVIDENCE = REPO / '.local-analysis/ex005-api-buffer-decoder'


class ApiBufferTests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def raw(self, value):
        # 合成输入只落本任务忽略目录，读取后由 TemporaryDirectory 清理。
        path = self.root / 'snapshot.bin'
        path.write_bytes(value)
        return path.read_bytes()

    def shell(self, raw=b'C:\\synthetic\0', **changes):
        args = {'raw_bool': 1, 'raw_bytes': self.raw(raw), 'read_limit': 260,
                'read_complete': True, 'encoding': 'cp1252'}
        args.update(changes)
        return buffers.decode_shell_folder(**args)

    def windir(self, raw=b'C:\\synthetic\0', **changes):
        args = {'pointer_is_null': False, 'raw_bytes': self.raw(raw), 'read_limit': 260,
                'read_complete': True, 'encoding': 'cp1252'}
        args.update(changes)
        return buffers.decode_windir(**args)

    def test_success_keeps_raw_bool_and_does_not_normalize_path(self):
        for value in (1, 42, -1, -(1 << 31), (1 << 31) - 1):
            with self.subTest(value=value):
                result = self.shell(b'  X:\\a\\..\\b \\  \0', raw_bool=value)
                self.assertEqual(result['raw_bool'], value)
                self.assertEqual(result['path_text'], '  X:\\a\\..\\b \\  ')
                self.assertEqual(result['status'], 'success_nonempty')
                self.assertFalse(result['fallback_required'])

    def test_failure_nonempty_residue_is_never_path(self):
        raw = b'C:\\old-residue\0\xfftail'
        result = self.shell(raw, raw_bool=0)
        self.assertEqual(result['status'], 'api_failed')
        self.assertFalse(result['api_success'])
        self.assertEqual(result['text'], 'C:\\old-residue')
        self.assertEqual(result['raw_bytes'], raw)
        self.assertEqual(result['tail_bytes'], b'\xfftail')
        self.assertIsNone(result['path_text'])
        self.assertTrue(result['fallback_required'])

    def test_success_empty_is_distinct_from_failure(self):
        success = self.shell(b'\0old')
        failed = self.shell(b'\0old', raw_bool=0)
        self.assertEqual(success['status'], 'success_empty')
        self.assertEqual(failed['status'], 'api_failed')
        self.assertEqual(success['first_nul'], 0)
        self.assertEqual(success['text'], '')
        self.assertIsNone(success['path_text'])
        self.assertTrue(success['fallback_required'])
        self.assertEqual(success['tail_bytes'], b'old')

    def test_last_allowed_byte_can_terminate_260_byte_snapshot(self):
        raw = b'a' * 259 + b'\0'
        result = self.shell(raw)
        self.assertEqual(result['first_nul'], 259)
        self.assertEqual(result['path_text'], 'a' * 259)
        self.assertFalse(result['possible_truncation'])
        self.assertEqual(result['raw_bytes'], raw)

    def test_260_bytes_without_nul_are_unknown(self):
        result = self.shell(b'a' * 260)
        self.assertEqual(result['status'], 'unknown')
        self.assertIsNone(result['first_nul'])
        self.assertIsNone(result['text'])
        self.assertIsNone(result['path_text'])
        self.assertIsNone(result['fallback_required'])
        self.assertEqual(result['issues'], ['missing_nul'])
        self.assertTrue(result['possible_truncation'])

    def test_embedded_nul_stops_text_but_keeps_all_tail_bytes(self):
        raw = b'a\0b\0\xff'
        result = self.shell(raw)
        self.assertEqual(result['first_nul'], 1)
        self.assertEqual(result['text'], 'a')
        self.assertEqual(result['tail_bytes'], b'b\0\xff')
        self.assertEqual(result['raw_bytes'], raw)
        self.assertEqual(result['issues'], [])

    def test_incomplete_read_remains_unknown_even_with_nul(self):
        result = self.shell(b'C:\\partial\0', read_complete=False)
        self.assertEqual(result['text'], 'C:\\partial')
        self.assertEqual(result['status'], 'unknown')
        self.assertIsNone(result['path_text'])
        self.assertIsNone(result['fallback_required'])
        self.assertIn('incomplete_read', result['issues'])

    def test_failed_bool_still_preserves_incomplete_and_decode_errors(self):
        result = self.shell(b'\xff\0', raw_bool=0, encoding='utf-8', read_complete=False)
        self.assertEqual(result['status'], 'api_failed')
        self.assertEqual(result['buffer_status'], 'unknown')
        self.assertTrue(result['fallback_required'])
        self.assertEqual(result['raw_bytes'], b'\xff\0')
        self.assertEqual(result['issues'], ['incomplete_read', 'decode_error'])
        self.assertEqual(result['decode_error']['start'], 0)
        self.assertIsNone(result['text'])

    def test_empty_and_short_unterminated_reads_are_unknown(self):
        for raw in (b'', b'x'):
            with self.subTest(raw=raw):
                result = self.shell(raw, read_limit=1)
                self.assertEqual(result['status'], 'unknown')
                self.assertTrue(result['possible_truncation'])

    def test_strict_decode_error_has_offsets_without_replacement_text(self):
        raw = b'a\xc3\0tail'
        result = self.shell(raw, encoding='utf-8')
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['decode_error']['start'], 1)
        self.assertEqual(result['decode_error']['end'], 2)
        self.assertIsNone(result['text'])
        self.assertIsNone(result['path_text'])
        self.assertEqual(result['raw_bytes'], raw)
        self.assertEqual(result['tail_bytes'], b'tail')

    def test_explicit_ansi_multibyte_and_aliases(self):
        for encoding in ('cp936', 'gbk', 'cp932', 'cp65001', 'utf-8'):
            with self.subTest(encoding=encoding):
                raw = '漢字'.encode(encoding) + b'\0'
                result = self.shell(raw, encoding=encoding)
                self.assertEqual(result['text'], '漢字')
                self.assertEqual(result['encoding'], encoding)
                self.assertEqual(result['raw_bytes'], raw)

    def test_encoding_is_required_and_implicit_or_non_ansi_codecs_rejected(self):
        for encoding in (None, '', 1252, 'not-a-codec', 'mbcs', 'oem',
                         'utf-16', 'utf-8-sig', 'utf-7', 'latin-1', 'hex'):
            with self.subTest(encoding=encoding), self.assertRaises(buffers.SnapshotFormatError):
                self.shell(encoding=encoding)
        with self.assertRaises(TypeError):
            buffers.decode_shell_folder(raw_bool=1, raw_bytes=b'x\0',
                                        read_limit=2, read_complete=True)

    def test_read_limits_are_exact_and_never_silently_slice(self):
        for limit in (0, -1, 261, True, 260.0, '260', None):
            with self.subTest(limit=limit), self.assertRaises(buffers.SnapshotFormatError):
                self.shell(read_limit=limit)
        with self.assertRaises(buffers.SnapshotFormatError):
            self.shell(b'a' * 260 + b'\0')
        with self.assertRaises(buffers.SnapshotFormatError):
            self.shell(b'x\0', read_limit=1)
        self.assertEqual(self.shell(b'\0', read_limit=1)['status'], 'success_empty')

    def test_raw_bool_type_and_32_bit_bounds_rejected(self):
        for value in (True, False, 1.0, '1', None, 1 << 31, -(1 << 31) - 1, 0xffffffff):
            with self.subTest(value=value), self.assertRaises(buffers.SnapshotFormatError):
                self.shell(raw_bool=value)

    def test_raw_buffer_and_read_flag_types_rejected(self):
        for raw in ('x\0', bytearray(b'x\0'), memoryview(b'x\0'), [120, 0], None):
            with self.subTest(raw=repr(raw)), self.assertRaises(buffers.SnapshotFormatError):
                self.shell(raw_bytes=raw)
        for flag in (0, 1, 'true', None):
            with self.subTest(flag=flag), self.assertRaises(buffers.SnapshotFormatError):
                self.shell(read_complete=flag)

    def test_windir_null_has_no_invented_buffer_or_text(self):
        result = self.windir(pointer_is_null=True, raw_bytes=None,
                             read_limit=None, read_complete=None)
        self.assertEqual(result['status'], 'null_pointer')
        self.assertTrue(result['literal_fallback_required'])
        self.assertEqual(result['buffer_status'], 'not_applicable')
        self.assertIsNone(result['raw_bytes'])
        self.assertIsNone(result['text'])
        self.assertIsNone(result['value_text'])

    def test_windir_nonnull_empty_never_selects_literal_fallback(self):
        result = self.windir(b'\0residue')
        self.assertEqual(result['status'], 'nonnull_empty')
        self.assertFalse(result['literal_fallback_required'])
        self.assertEqual(result['value_text'], '')
        self.assertEqual(result['tail_bytes'], b'residue')

    def test_windir_nonnull_text_and_unknowns(self):
        result = self.windir(b'C:\\synthetic\0')
        self.assertEqual(result['status'], 'nonnull_nonempty')
        self.assertEqual(result['value_text'], 'C:\\synthetic')
        for raw, changes in ((b'x', {}), (b'x\0', {'read_complete': False}),
                             (b'\xff\0', {'encoding': 'utf-8'})):
            with self.subTest(raw=raw, changes=changes):
                result = self.windir(raw, **changes)
                self.assertEqual(result['status'], 'unknown')
                self.assertIsNone(result['value_text'])
                self.assertFalse(result['literal_fallback_required'])

    def test_null_pointer_contradictions_and_pointer_types_rejected(self):
        for changes in ({'raw_bytes': b'\0'}, {'read_limit': 260}, {'read_complete': False}):
            args = {'pointer_is_null': True, 'raw_bytes': None,
                    'read_limit': None, 'read_complete': None}
            args.update(changes)
            with self.subTest(changes=changes), self.assertRaises(buffers.SnapshotFormatError):
                self.windir(**args)
        for flag in (0, 1, None, 'null'):
            with self.subTest(flag=flag), self.assertRaises(buffers.SnapshotFormatError):
                self.windir(pointer_is_null=flag)
        with self.assertRaises(buffers.SnapshotFormatError):
            self.windir(raw_bytes=None)

    def test_no_environment_locale_path_resolution_or_api_collection(self):
        forbidden = AssertionError('不应查询本机环境、locale、路径或真实 API')
        with patch.dict(os.environ, {}, clear=True), \
                patch('os.getenv', side_effect=forbidden), \
                patch.object(locale, 'getpreferredencoding', side_effect=forbidden), \
                patch.object(Path, 'resolve', side_effect=forbidden), \
                patch.object(Path, 'exists', side_effect=forbidden):
            args = {'raw_bytes': b'X:\\..\\raw\0', 'read_limit': 260,
                    'read_complete': True, 'encoding': 'cp1252'}
            result = buffers.decode_shell_folder(raw_bool=1, **args)
            self.assertEqual(result['path_text'], 'X:\\..\\raw')
            self.assertEqual(buffers.decode_windir(pointer_is_null=False, **args)['value_text'],
                             'X:\\..\\raw')
        self.assertEqual(set(self.root.iterdir()), set())


if __name__ == '__main__':
    unittest.main(verbosity=2)
