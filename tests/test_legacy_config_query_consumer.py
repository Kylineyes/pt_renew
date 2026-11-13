"""无目标、无 GUI 的查询消费契约测试；仅使用本树合成 JSON 夹具。"""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import legacy_config_query_consumer as consumer

EVIDENCE = REPO / '.local-analysis/ex005-query-consumer'
FULLDOUBLE = 'CONFIG -get sdl fulldouble'
WAITONERROR = 'CONFIG -get sdl waitonerror'


class QueryConsumerTests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='fixture-', dir=EVIDENCE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def cli(self, *args):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            try:
                code = consumer.main(list(map(str, args)))
            except SystemExit as result:
                code = result.code
        return code, output.getvalue(), error.getvalue()

    def input_file(self, value):
        path = self.root / 'synthetic-commands.json'
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def test_explicit_keys_generate_one_or_two_independent_ascii_commands_in_order(self):
        cases = [(['fulldouble'], [FULLDOUBLE]), (['waitonerror'], [WAITONERROR]),
                 (['fulldouble', 'waitonerror'], [FULLDOUBLE, WAITONERROR]),
                 (['waitonerror', 'fulldouble'], [WAITONERROR, FULLDOUBLE])]
        for keys, expected in cases:
            with self.subTest(keys=keys):
                self.assertEqual(consumer.generate_commands(keys), expected)
                report = consumer.contract_from_keys(keys)
                self.assertEqual(report['commands'], expected)
                self.assertEqual(report['keys'], [{'section': 'sdl', 'key': key} for key in keys])
                self.assertTrue(all(command.isascii() for command in report['commands']))

    def test_external_commands_use_same_consumer_and_keep_reverse_order(self):
        report = consumer.consume_commands([WAITONERROR, FULLDOUBLE])
        self.assertEqual(report['commands'], [WAITONERROR, FULLDOUBLE])
        self.assertEqual([key['key'] for key in report['keys']], ['waitonerror', 'fulldouble'])
        self.assertEqual(report, consumer.contract_from_keys(['waitonerror', 'fulldouble']))

    def test_readiness_and_known_setenv_effects_are_not_execution_proof(self):
        report = consumer.consume_commands([FULLDOUBLE, WAITONERROR])
        self.assertIs(report['execution_ready'], False)
        effect = report['known_effects']['shell_environment']
        self.assertEqual(effect['variable'], 'CONFIG')
        self.assertTrue(effect['attempts_update'])
        self.assertFalse(effect['caller_checks_result'])
        self.assertTrue(effect['failure_may_remove_old_entry'])
        self.assertTrue(effect['shared_between_queries'])
        self.assertFalse(report['known_effects']['output']['delivery_verified'])
        self.assertEqual({item['kind'] for item in report['missing_evidence']},
                         {'isolation', 'observation', 'actual_query', 'creator_exit'})

    def test_plain_string_empty_overlong_duplicate_and_non_string_lists_rejected(self):
        for value in (None, True, 'fulldouble', [], ['fulldouble'] * 2,
                      ['fulldouble', 'waitonerror', 'fulldouble'], [None], [1], [[]],
                      {'fulldouble': True}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                consumer.contract_from_keys(value)
        for value in (None, True, FULLDOUBLE, [], [FULLDOUBLE, FULLDOUBLE],
                      [FULLDOUBLE, WAITONERROR, FULLDOUBLE], [None], [1], [[]],
                      {'commands': [FULLDOUBLE]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                consumer.consume_commands(value)

    def test_key_names_are_exact_and_do_not_accept_shell_or_qualified_syntax(self):
        for key in ('SDL/fulldouble', 'sdl fulldouble', 'sdl/fulldouble', 'FULLDOUBLE',
                    ' fulldouble', 'fulldouble ', 'fulldouble\n', 'fulldouble\x00',
                    'waitonerror;exit', 'memsize', 'output', 'exit', 'mount', 'pt', ''):
            with self.subTest(key=key), self.assertRaises(ValueError):
                consumer.contract_from_keys([key])

    def test_real_consumer_rejects_shell_injection_and_extra_parameters(self):
        rejected = [
            FULLDOUBLE + ';exit', FULLDOUBLE + ' & exit', FULLDOUBLE + ' && exit',
            FULLDOUBLE + ' | echo x', FULLDOUBLE + ' > OUT.TXT', FULLDOUBLE + ' < IN.TXT',
            FULLDOUBLE + ' >> OUT.TXT', FULLDOUBLE + '\n' + WAITONERROR,
            FULLDOUBLE + '\r\nexit', FULLDOUBLE + '\x00',
            'CONFIG -get "sdl fulldouble"', 'CONFIG -get sdl "fulldouble"',
            "CONFIG -get sdl 'fulldouble'", 'CONFIG -get sdl fulldouble extra',
            'CONFIG -get sdl,fulldouble', 'CONFIG -get sdl=fulldouble',
            'CONFIG -set sdl fulldouble=true', 'mount c x', 'PT SYN1.PCB', 'exit',
            '@echo off', 'set CONFIG=true', 'call ' + FULLDOUBLE,
        ]
        for command in rejected:
            with self.subTest(command=repr(command)), self.assertRaises(ValueError):
                consumer.consume_commands([command])
        # 合法前项不能掩盖后续附加 shell 语句。
        with self.assertRaises(ValueError):
            consumer.consume_commands([FULLDOUBLE, 'exit'])

    def test_real_consumer_rejects_whitespace_case_unicode_and_prefix_near_misses(self):
        rejected = [' ' + FULLDOUBLE, FULLDOUBLE + ' ', FULLDOUBLE + '\n',
                    FULLDOUBLE + '\r', FULLDOUBLE.replace(' ', '\t'),
                    FULLDOUBLE.replace(' ', '  ', 1), FULLDOUBLE.replace(' ', '\u00a0', 1),
                    FULLDOUBLE.lower(), FULLDOUBLE.replace('-get', '-GET'),
                    FULLDOUBLE.replace('sdl', 'SDL'), FULLDOUBLE + 'x',
                    FULLDOUBLE.replace('CONFIG', 'ＣＯＮＦＩＧ'), 'CONFIG -get sdl fulldoubl',
                    FULLDOUBLE + '\u2028']
        for command in rejected:
            with self.subTest(command=repr(command)), self.assertRaises(ValueError):
                consumer.consume_commands([command])

    def test_input_and_returned_data_do_not_share_mutable_lists_or_defaults(self):
        commands = [FULLDOUBLE]
        report = consumer.consume_commands(commands)
        commands.append('exit')
        self.assertEqual(report['commands'], [FULLDOUBLE])
        report['commands'].append('exit')
        report['keys'][0]['key'] = 'changed'
        report['known_effects']['shell_environment']['attempts_update'] = False
        fresh = consumer.contract_from_keys(('fulldouble',))
        self.assertEqual(fresh['commands'], [FULLDOUBLE])
        self.assertEqual(fresh['keys'][0]['key'], 'fulldouble')
        self.assertTrue(fresh['known_effects']['shell_environment']['attempts_update'])

    def test_cli_keys_stdout_does_not_read_files_or_create_outputs(self):
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('参数模式不应读文件')):
            code, output, error = self.cli('--key', 'waitonerror', '--key', 'fulldouble')
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)['commands'], [WAITONERROR, FULLDOUBLE])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_cli_json_reads_only_explicit_input_and_preserves_its_bytes(self):
        path = self.input_file([WAITONERROR, FULLDOUBLE])
        before = path.read_bytes()
        reads = []
        original = Path.read_bytes
        def read(item):
            reads.append(item)
            return original(item)
        with patch.object(Path, 'read_bytes', read):
            code, output, error = self.cli('--commands-json', path)
        self.assertEqual(code, 0, error)
        self.assertEqual(reads, [path])
        self.assertEqual(json.loads(output)['commands'], [WAITONERROR, FULLDOUBLE])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_cli_output_is_exclusive_and_input_or_existing_evidence_survives(self):
        path = self.input_file([FULLDOUBLE])
        output = self.root / 'contract.json'
        code, stdout, error = self.cli('--commands-json', path, '--output', output)
        self.assertEqual(code, 0, error)
        self.assertEqual(stdout, '')
        self.assertFalse(json.loads(output.read_text(encoding='utf-8'))['execution_ready'])
        for existing in (path, output):
            before = existing.read_bytes()
            code, stdout, error = self.cli('--commands-json', path, '--output', existing)
            self.assertEqual(code, 2)
            self.assertEqual(stdout, '')
            self.assertEqual(existing.read_bytes(), before)

    def test_output_alias_cannot_overwrite_input_content(self):
        path = self.input_file([FULLDOUBLE])
        alias = self.root / 'alias.json'
        os.link(path, alias)
        before = path.read_bytes()
        code, _, _ = self.cli('--commands-json', path, '--output', alias)
        self.assertEqual(code, 2)
        self.assertEqual(path.read_bytes(), before)

    def test_json_bad_types_encoding_and_injected_commands_fail_before_output_creation(self):
        path = self.root / 'invalid.json'
        output = self.root / 'not-created.json'
        for raw in (b'{', b'\xff', b'null', b'{}', b'[]', b'[1]',
                    json.dumps([FULLDOUBLE + '\nexit']).encode('utf-8'),
                    json.dumps({'commands': [FULLDOUBLE], 'execution_ready': True}).encode('utf-8')):
            with self.subTest(raw=raw):
                path.write_bytes(raw)
                code, stdout, _ = self.cli('--commands-json', path, '--output', output)
                self.assertEqual(code, 2)
                self.assertEqual(stdout, '')
                self.assertFalse(output.exists())
        path.write_bytes(json.dumps([FULLDOUBLE]).encode('utf-8-sig'))
        code, stdout, error = self.cli('--commands-json', path)
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(stdout)['commands'], [FULLDOUBLE])

    def test_cli_has_no_default_key_execution_or_abbreviated_options(self):
        path = self.input_file([FULLDOUBLE])
        output = self.root / 'not-created.json'
        for args in ((), ('--key', 'fulldouble', '--commands-json', path),
                     ('--key', 'fulldouble', '--execute'),
                     ('--key', 'fulldouble', '--exit'),
                     ('--key', 'fulldouble', '--out', output),
                     ('--key', 'fulldouble', '--key', 'fulldouble'),
                     ('--key', 'fulldouble', '--key', 'waitonerror', '--key', 'output')):
            with self.subTest(args=args):
                code, stdout, _ = self.cli(*args)
                self.assertEqual(code, 2)
                self.assertEqual(stdout, '')
                self.assertFalse(output.exists())
        code, _, _ = self.cli('--commands-json', self.root / 'missing.json', '--output', output)
        self.assertEqual(code, 2)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
