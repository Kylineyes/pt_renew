"""冻结Python依赖、重定向器拒绝和共享启动截止；不加载控制包或桌面。"""
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.core import Clock, Context, Ledger, SECOND, digest
from async_product_client.product import tree_hashes
from async_product_client.python_environment import PythonEnvironment
from async_product_client.runtime import CreatorRuntime, FrozenProgram
from async_product_client.runtime_worker import run as worker_run
from async_product_client.witness import audit_relay
from test_async_product_probe import ProbeFixture


class EnvironmentTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def environment(self):
        dependencies = self.root / 'dependencies'; dependencies.mkdir()
        (dependencies / 'frozen_test_dependency.py').write_text('VALUE = 42\n', encoding='utf-8')
        return PythonEnvironment(str(dependencies), tree_hashes(dependencies), tuple(sys.version_info[:3]))

    async def test_complete_dependency_tree_rejects_modified_and_extra_files(self):
        profile = self.environment(); self.assertEqual(profile.verify(), ([Path(profile.root)], False))
        path = Path(profile.root) / 'extra.py'; path.write_text('VALUE = 1', encoding='utf-8')
        with self.assertRaises(ValueError): profile.verify()
        path.unlink(); (Path(profile.root) / 'frozen_test_dependency.py').write_text('VALUE = 0', encoding='utf-8')
        with self.assertRaises(ValueError): profile.verify()

    async def test_version_mismatch_and_nonisolated_activation_make_no_path_change(self):
        profile = self.environment(); original = list(sys.path)
        with patch('async_product_client.python_environment.sys.flags', SimpleNamespace(isolated=0, no_site=0)):
            with self.assertRaises(ValueError): profile.activate()
        self.assertEqual(sys.path, original)
        changed = PythonEnvironment(profile.root, profile.files, (0, 0, 0))
        with self.assertRaises(ValueError): changed.verify()

    async def test_pth_executable_and_escaping_paths_are_refused(self):
        profile = self.environment(); root = Path(profile.root)
        for content in ('import os\n', '../\n'):
            (root / 'unsafe.pth').write_text(content, encoding='utf-8')
            frozen = PythonEnvironment(str(root), tree_hashes(root), profile.version)
            with self.subTest(content=content), self.assertRaises(ValueError): frozen.verify()

    async def test_redirector_is_refused_before_creator_popen(self):
        prefix = self.root / 'venv'; (prefix / 'Scripts').mkdir(parents=True)
        interpreter = prefix / 'Scripts/python.exe'; interpreter.write_bytes(b'redirector')
        (prefix / 'pyvenv.cfg').write_text('home = base', encoding='utf-8')
        modules = self.root / 'modules'; (modules / 'async_product_client').mkdir(parents=True)
        (modules / 'async_product_client/runtime_worker.py').write_text('', encoding='utf-8')
        program = FrozenProgram(str(interpreter), digest(interpreter.read_bytes()), str(modules),
                                tuple(tree_hashes(modules).items()), 'async_product_client/runtime_worker.py')
        ledger = Ledger(context=Context('task', 'dispatch', 'run', 'session'),
                        cleanup_deadline_ns=Clock().monotonic_ns() + 900 * SECOND, enabled=True)
        calls = []; runtime = CreatorRuntime(ledger, self.root / 'evidence', enabled=True,
                                             popen=lambda *args, **kwargs: calls.append(args))
        with self.assertRaises(ValueError):
            with ledger.operation('create', 'start'): runtime.spawn('service', role='service', program=program)
        self.assertEqual(calls, []); self.assertEqual(runtime.children, {})

    async def test_probe_redirector_is_refused_before_any_query_creation(self):
        folder = self.root / 'fixture'; folder.mkdir(); f = ProbeFixture(folder)
        prefix = self.root / 'probe-venv'; (prefix / 'Scripts').mkdir(parents=True)
        interpreter = prefix / 'Scripts/python.exe'; interpreter.write_bytes(b'redirector')
        (prefix / 'pyvenv.cfg').write_text('home = base', encoding='utf-8')
        f.probe.interpreter = interpreter; f.probe.interpreter_sha256 = digest(interpreter.read_bytes())
        with self.assertRaises(ValueError): await f.run()
        self.assertEqual(f.calls, [])

    async def test_expired_shared_startup_deadline_stops_worker_before_source_or_driver_load(self):
        plan = self.root / 'launch.json'
        row = dict(schema_version=1, enabled=True, role='service', startup_deadline_ns=1, diagnostic_deadline_ns=2)
        raw = json.dumps(row).encode(); plan.write_bytes(raw)
        with patch('async_product_client.runtime_worker.FrozenProgram.verify') as verify:
            self.assertEqual(await worker_run(plan, digest(raw)), 1)
            verify.assert_not_called()
        failure = json.loads((self.root / 'creator-failure.json').read_text(encoding='utf-8'))
        self.assertIn('启动截止', failure['reason'])

    @unittest.skipUnless(sys.platform == 'win32', '实际原Popen适配只支持Windows')
    async def test_isolated_base_python_imports_only_new_frozen_dependency_and_keeps_original_pid(self):
        profile = self.environment()
        modules = self.root / 'modules'
        shutil.copytree(ROOT / 'tools/async_product_client', modules / 'async_product_client',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        driver = modules / 'driver.py'
        driver.write_text("import frozen_test_dependency as dependency\nasync def run(runtime, configuration):\n    assert dependency.VALUE == 42\n    assert __import__('os').getpid() == runtime.relay.self_identity['pid']\n    assert __import__('sys').flags.isolated == __import__('sys').flags.no_site == 1\n    return 0\n", encoding='utf-8')
        interpreter = Path(sys._base_executable).resolve()
        program = FrozenProgram(str(interpreter), digest(interpreter.read_bytes()), str(modules),
                                tuple(tree_hashes(modules).items()), 'driver.py', asdict(profile))
        context = Context('task', 'dispatch', 'run', 'session')
        ledger = Ledger(context=context, cleanup_deadline_ns=Clock().monotonic_ns() + 900 * SECOND, enabled=True)
        runtime = CreatorRuntime(ledger, self.root / 'evidence', enabled=True)
        with ledger.operation('create', 'start'):
            process = runtime.spawn('service', role='service', program=program)
        await runtime.wait_child('service')
        child = runtime.children['service']
        audited = audit_relay((child['folder'] / 'creator-report.json').read_bytes(), context=asdict(context),
                               expected_identity=child['identity'], expected_role='service')
        self.assertEqual(audited['identities'], 1); self.assertEqual(process.returncode, 0)
        self.assertEqual(tree_hashes(Path(profile.root)), profile.files)


if __name__ == '__main__': unittest.main()
