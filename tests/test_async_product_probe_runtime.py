"""COM初始化自动导入/额外计数、私有缓存及探针来源契约；纯假API。"""
from contextlib import contextmanager
from dataclasses import asdict
import copy
import ctypes
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.com_apartment import ApartmentTrace, CtypesProxy, FunctionProxy, ImportLoader, validate_com_report
from async_product_client.probe_environment import GENERATED, freeze_probe_environment, validate_probe_environment
from async_product_client.probe_workspace import ProbeWorkspace
from async_product_client.product import tree_hashes
from async_product_client.python_environment import environment
from test_async_product_probe import ProbeFixture


@contextmanager
def isolated_modules():
    with patch.dict(sys.modules):
        for name in list(sys.modules):
            if name == 'comtypes' or name.startswith('comtypes.') or name == 'windows_mcp' or name.startswith('windows_mcp.'):
                sys.modules.pop(name)
        yield


class ProbeRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def profile(self):
        source = self.root / 'full-dependencies'; source.mkdir()
        for name in GENERATED | {'comtypes/__init__.py', 'comtypes/client/__init__.py', 'unused.py'}:
            path = source / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# 合成冻结依赖\n', encoding='utf-8')
        return dict(root=str(source), files=tree_hashes(source), version=list(sys.version_info[:3]))

    def fake_ole(self):
        self.calls = []
        def initialize(*args): self.calls.append('init'); return 0
        def uninitialize(): self.calls.append('uninit')
        return SimpleNamespace(CoInitializeEx=initialize, CoInitialize=initialize, CoUninitialize=uninitialize)

    async def test_explicit_import_and_original_uia_extra_initializers_all_balance(self):
        ole = self.fake_ole()
        with isolated_modules():
            trace = ApartmentTrace(ole=ole)
            with trace:
                # 模拟comtypes自动CoInitializeEx及原_AutomationClient.CoInitialize。
                proxy = trace.ole(ole); proxy.CoInitializeEx(None, 2); proxy.CoInitialize(None)
                trace.shutdown_callbacks.append((proxy.CoUninitialize, (), {}))
            report = validate_com_report(trace.report())
        self.assertEqual(self.calls, ['init'] * 3 + ['uninit'] * 3)
        self.assertEqual(report['balance'], 0)
        self.assertNotIn(trace, sys.meta_path)

    async def test_module_local_ctypes_proxy_and_shutdown_interception_keep_real_module_unchanged(self):
        ole = self.fake_ole(); source = '''import ctypes
import atexit
_ole = ctypes.OleDLL('ole32')
_ole.CoInitializeEx(None, 2)
def _shutdown(): _ole.CoUninitialize()
atexit.register(_shutdown)
'''
        class Loader:
            def exec_module(self, module): exec(source, module.__dict__)
        with isolated_modules(), patch.object(ctypes, 'OleDLL', return_value=ole, create=True):
            trace = ApartmentTrace(ole=ole)
            with trace:
                module = ModuleType('comtypes'); sys.modules['comtypes'] = module
                ImportLoader(Loader(), trace).exec_module(module)
                self.assertIsNot(module.ctypes, ctypes)
                self.assertIs(sys.modules['ctypes'], ctypes)
                self.assertEqual(len(trace.shutdown_callbacks), 1)
                self.assertIs(module.ctypes.c_void_p, ctypes.c_void_p)
            self.assertTrue(validate_com_report(trace.report())['balanced'])
        self.assertEqual(self.calls, ['init', 'init', 'uninit', 'uninit'])

    async def test_uia_original_retry_sleep_is_refused_by_module_local_proxy(self):
        ole = self.fake_ole(); module = ModuleType('windows_mcp.uia.core')
        class Loader:
            def exec_module(self, module): exec('import time\n', module.__dict__)
        with isolated_modules():
            with ApartmentTrace(ole=ole) as trace:
                ImportLoader(Loader(), trace).exec_module(module)
                with self.assertRaises(ValueError): module.time.sleep(.1)
        self.assertEqual(self.calls, ['init', 'uninit'])

    async def test_stop_prevents_any_com_initialization(self):
        ole = self.fake_ole()
        def stop(): raise ValueError('原停止标记')
        with isolated_modules(), self.assertRaises(ValueError):
            with ApartmentTrace(ole=ole, checkpoint=stop): pass
        self.assertEqual(self.calls, [])

    async def test_exception_still_balances_acquired_initializers_and_preserves_error(self):
        ole = self.fake_ole()
        with isolated_modules():
            trace = ApartmentTrace(ole=ole)
            with self.assertRaisesRegex(RuntimeError, '原观察错误'):
                with trace:
                    trace.ole(ole).CoInitialize(None)
                    raise RuntimeError('原观察错误')
        self.assertTrue(validate_com_report(trace.report())['balanced'])
        self.assertEqual(self.calls, ['init', 'init', 'uninit', 'uninit'])

    async def test_bad_hresult_unknown_api_and_wrong_thread_do_not_produce_success(self):
        ole = self.fake_ole()
        with isolated_modules():
            trace = ApartmentTrace(ole=ole)
            with trace: pass
        valid = trace.report()
        for mode in ('negative', 'extra-uninit', 'thread', 'missing-return', 'balance'):
            row = copy.deepcopy(valid)
            if mode == 'negative': row['calls'][0]['result'] = -1
            if mode == 'extra-uninit': row['calls'].insert(0, dict(api='CoUninitialize', returned=True, thread=row['thread'], balance=-1))
            if mode == 'thread': row['calls'][0]['thread'] += 1
            if mode == 'missing-return': row['calls'][0]['returned'] = False
            if mode == 'balance': row['calls'][0]['balance'] = 9
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate_com_report(row)

    async def test_complete_comtypes_subset_is_byte_identical_and_source_unchanged(self):
        source = self.profile()
        profile = freeze_probe_environment(source, self.root / 'probe-dependencies')
        self.assertEqual(profile['files'], {name: sha for name, sha in source['files'].items() if name.startswith('comtypes/')})
        self.assertNotIn('unused.py', profile['files'])
        self.assertEqual(tree_hashes(source['root']), source['files'])
        self.assertEqual(tree_hashes(profile['root']), profile['files'])
        validate_probe_environment(environment(profile))

    async def test_missing_generated_wrapper_and_extra_noncomtypes_package_are_refused(self):
        source = self.profile()
        profile = freeze_probe_environment(source, self.root / 'probe-dependencies')
        for mode in ('missing', 'extra'):
            row = copy.deepcopy(profile)
            if mode == 'missing': row['files'].pop('comtypes/gen/UIAutomationClient.py')
            else: row['files']['numpy/__init__.py'] = '0' * 64
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate_probe_environment(environment(row))

    async def test_workspace_cache_is_private_and_original_dependency_tree_remains_unchanged(self):
        source = self.profile(); profile = freeze_probe_environment(source, self.root / 'probe-dependencies')
        workspace = ProbeWorkspace(profile, self.root / 'runtime'); private = workspace.prepare()
        self.assertNotEqual(private.root, profile['root'])
        self.assertEqual(private.files, profile['files'])
        with patch('async_product_client.probe_workspace.sys.addaudithook') as hook, \
             patch.object(type(private), 'activate'):
            old_temp = tempfile.tempdir
            with workspace:
                self.assertEqual(tempfile.gettempdir(), str(self.root / 'runtime/temp'))
                hook.assert_called_once()
            self.assertEqual(tempfile.tempdir, old_temp)
        self.assertEqual(tree_hashes(source['root']), source['files'])

    async def test_readonly_audit_blocks_cache_repair_but_allows_private_lock_and_results(self):
        source = self.profile(); profile = freeze_probe_environment(source, self.root / 'probe-dependencies')
        workspace = ProbeWorkspace(profile, self.root / 'runtime'); private = workspace.prepare()
        frozen = str(Path(private.root) / 'comtypes/gen/UIAutomationClient.py')
        for event, args in [('open', (frozen, 'w', os.O_WRONLY)), ('os.remove', (frozen, -1)),
                            ('os.rename', (frozen, str(self.root / 'away.py'), -1, -1))]:
            with self.subTest(event=event), self.assertRaises(ValueError): workspace.audit(event, args)
        workspace.audit('open', (frozen, 'r', 0))
        workspace.audit('open', (str(workspace.root / 'temp/cache.lock'), 'a', os.O_RDWR | os.O_CREAT))
        self.assertEqual(tree_hashes(profile['root']), profile['files'])

    async def test_parent_requires_balanced_com_receipt_and_unchanged_private_runtime(self):
        source = self.profile(); profile = freeze_probe_environment(source, self.root / 'probe-dependencies')
        ole = self.fake_ole()
        with isolated_modules():
            trace = ApartmentTrace(ole=ole)
            with trace: pass
        receipt = trace.report()
        for mode in ('valid', 'unbalanced', 'missing', 'changed-private'):
            folder = self.root / mode; folder.mkdir(); f = ProbeFixture(folder)
            f.probe.python_environment = profile
            def mutate(result):
                result['com_apartment'] = copy.deepcopy(receipt)
                result['private_runtime_unchanged'] = mode != 'changed-private'
                if mode == 'unbalanced': result['com_apartment']['calls'][0]['result'] = -1
                if mode == 'missing': result.pop('com_apartment')
            f.mutate = mutate
            if mode == 'valid':
                await f.run()
                self.assertTrue(f.probe.children[0]['accepted'])
                self.assertEqual(f.calls[0][0][1:3], ['-I', '-S'])
            else:
                with self.subTest(mode=mode), self.assertRaises(ValueError): await f.run()
                self.assertFalse(f.probe.children[0]['accepted'])
                self.assertEqual(f.probe.children[0]['exit_code'], 0)
                self.assertEqual(f.rig.ledger.failed, 'probe')
            self.assertEqual(len(f.calls), 1)

    async def test_private_runtime_modified_after_query_is_rejected_without_altering_template(self):
        source = self.profile(); profile = freeze_probe_environment(source, self.root / 'probe-dependencies')
        workspace = ProbeWorkspace(profile, self.root / 'runtime'); private = workspace.prepare()
        (Path(private.root) / 'comtypes/gen/UIAutomationClient.py').write_text('# 损坏\n', encoding='utf-8')
        with self.assertRaises(ValueError): workspace.verify()
        self.assertEqual(tree_hashes(profile['root']), profile['files'])

    async def test_parent_probe_timing_retains_original_deadline_and_persistence_inside_it(self):
        f = ProbeFixture(self.root)
        await f.run()
        child = f.probe.children[0]; row = child['timing']
        self.assertTrue(row['accepted']); self.assertLess(row['finished_ns'], child['request']['deadline_ns'])
        ordered = ['started_ns', 'precheck_finished_ns', 'request_written_ns', 'popen_created_ns', 'exit_observed_ns',
                   'validation_finished_ns', 'finished_ns']
        self.assertEqual([row[name] for name in ordered], sorted(row[name] for name in ordered))
        saved = json.loads((Path(child['folder']) / 'parent-timing.json').read_text(encoding='utf-8'))
        self.assertFalse(saved['accepted'])
        self.assertEqual(saved['deadline_ns'], child['request']['deadline_ns'])


if __name__ == '__main__': unittest.main()
