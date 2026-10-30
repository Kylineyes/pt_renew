"""监督器创建前的完整兼容性材料、会话及唯一机会核验；全部假产品。"""
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.client_driver import authorize
from async_product_client.core import SECOND, digest
from async_product_client.launch import CompatibilityLaunch
from async_product_client.product import tree_hashes
from async_product_client.runtime import FrozenProgram
from test_async_product_probe import ProbeFixture


class MaterialTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        root = self.root / str(len(list(self.root.iterdir()))); root.mkdir()
        f = ProbeFixture(root); ledger = f.rig.ledger; ledger.diagnostic_deadline_ns = 600 * SECOND
        for name in ('client_driver.py', 'service_driver.py', 'supervisor_driver.py', 'runtime_worker.py'):
            (f.modules / 'async_product_client' / name).write_text('# 假入口\n', encoding='utf-8')
        for name in ('run_control_diagnostics.py', 'control_diagnostics.py'):
            (f.modules / name).write_text('# 假启动器\n', encoding='utf-8')
        dependencies = root / 'dependencies'; dependencies.mkdir()
        (dependencies / 'fake.py').write_text('# 假依赖\n', encoding='utf-8')
        environment = dict(root=str(dependencies), files=tree_hashes(dependencies), version=list(sys.version_info[:3]))
        interpreter = Path(sys._base_executable).resolve(); files = tree_hashes(f.modules)
        program = FrozenProgram(str(interpreter), digest(interpreter.read_bytes()), str(f.modules), tuple(files.items()),
                                'async_product_client/client_driver.py', environment)
        client_root = root / 'execution/supervisor/client'
        f.runtime = SimpleNamespace(enabled=True, relay=SimpleNamespace(role='client'), ledger=ledger, root=client_root)
        a, b = root / 'a.net', root / 'b.net'; a.write_bytes(b'new A'); b.write_bytes(b'new B')
        common = dict(permission='本轮必要控制授权', message_id='new-message', permission_confirmed=True)
        approval = dict(common, context=asdict(ledger.context), scope='product-compatibility', evidence_root=str(client_root),
                        max_product_launches=1, max_connections=1, max_probe_queries=32,
                        diagnostic_deadline_ns=ledger.diagnostic_deadline_ns, cleanup_deadline_ns=ledger.cleanup_deadline_ns)
        server = dict(common, task_id=ledger.context.task_id, dispatch_id=ledger.context.dispatch_id,
                      client_run_id=ledger.context.run_id, session_id=ledger.context.session_id, mode='diagnostics-only',
                      diagnostic_seconds=600, total_seconds=900,
                      launcher_files={name: files[name] for name in ('run_control_diagnostics.py', 'control_diagnostics.py')})
        approval_path, server_path = root / 'approval.json', root / 'server-approval.json'
        approval_path.write_text(json.dumps(approval, ensure_ascii=False), encoding='utf-8')
        server_path.write_text(json.dumps(server, ensure_ascii=False), encoding='utf-8')
        product = dict(kind='net', deployment=str(f.rig.deployment), manifest=f.rig.manifest,
                       board=str(f.rig.board), board_sha256=digest(f.rig.board.read_bytes()),
                       a=dict(path=str(a), sha256=digest(a.read_bytes())), b=dict(path=str(b), sha256=digest(b.read_bytes())),
                       environment={'PATH': 'unused'}, interpreter=str(interpreter), interpreter_sha256=program.interpreter_sha256,
                       package_root=str(f.package), package_files=tree_hashes(f.package / 'windows_mcp'),
                       module_root=str(f.modules), module_files=files, diagnostic_deadline_ns=ledger.diagnostic_deadline_ns,
                       revision=2, python_environment=environment)
        f.configuration = dict(approval=str(approval_path), approval_sha256=digest(approval_path.read_bytes()),
                               service_program=asdict(replace(program, entry='async_product_client/service_driver.py')),
                               service_configuration=dict(package_root=str(f.package), trace=str(root / 'trace.jsonl'),
                                                          approval=str(server_path), approval_sha256=digest(server_path.read_bytes())),
                               product=product, session_file=str(f.rig.journal),
                               schemas={name: {'type': 'object'} for name in ('Snapshot', 'Click', 'Shortcut', 'Type')})
        f.program, f.approval, f.server = program, approval, server
        f.pi_env = dict(PI_PROVIDER=ledger.context.provider, PI_MODEL=ledger.context.model,
                        PI_REASONING_LEVEL=ledger.context.thinking, PI_SESSION_ID=ledger.context.session_id)
        f.pin = patch('async_product_client.client_driver.EXPERIMENT_SHA', f.rig.manifest['pt-renew.exe'])
        return f

    async def test_complete_new_materials_validate_without_creating_process_or_reading_images(self):
        f = self.fixture()
        with f.pin, patch.dict(os.environ, f.pi_env): row = authorize(f.runtime, f.configuration)
        self.assertEqual(row['context'], asdict(f.rig.ledger.context))
        self.assertEqual(f.calls, []); self.assertEqual(f.rig.native_calls, 0)
        self.assertEqual(f.rig.shots, 0)

    async def test_wrong_pi_context_changed_inputs_environment_schema_and_server_source_are_refused(self):
        for mode in ('pi', 'context', 'input', 'environment', 'schema', 'server-source', 'deadline'):
            f = self.fixture(); env = dict(f.pi_env)
            if mode == 'pi': env['PI_SESSION_ID'] = 'old-session'
            if mode == 'context':
                f.approval['context']['task_id'] = 'old-task'
                path = Path(f.configuration['approval']); path.write_text(json.dumps(f.approval), encoding='utf-8')
                f.configuration['approval_sha256'] = digest(path.read_bytes())
            if mode == 'input': Path(f.configuration['product']['b']['path']).write_bytes(b'changed')
            if mode == 'environment': f.configuration['product']['environment']['QT_PLUGIN_PATH'] = 'old'
            if mode == 'schema': del f.configuration['schemas']['Click']
            if mode == 'server-source': f.server['launcher_files']['control_diagnostics.py'] = '0' * 64
            if mode == 'deadline': f.configuration['product']['diagnostic_deadline_ns'] += SECOND
            if mode == 'server-source':
                path = Path(f.configuration['service_configuration']['approval']); path.write_text(json.dumps(f.server), encoding='utf-8')
                f.configuration['service_configuration']['approval_sha256'] = digest(path.read_bytes())
            with self.subTest(mode=mode), f.pin, patch.dict(os.environ, env), self.assertRaises(ValueError):
                authorize(f.runtime, f.configuration)
            self.assertEqual(f.calls, [])

    async def test_missing_specific_materials_stop_before_root_supervisor_popen(self):
        f = self.fixture(); calls = []
        launch = CompatibilityLaunch(f.rig.ledger, f.root / 'execution', enabled=True)
        launch.runtime.popen = lambda *args, **kwargs: calls.append(args)
        configuration = dict(client_program=asdict(f.program), client_configuration=f.configuration)
        supervisor = replace(f.program, entry='async_product_client/supervisor_driver.py')
        Path(f.configuration['approval']).write_text('{}', encoding='utf-8')
        with f.pin, patch.dict(os.environ, f.pi_env), self.assertRaises(ValueError):
            launch.start('launch-root', f.rig.ledger.token, supervisor_program=supervisor, configuration=configuration)
        self.assertEqual(calls, []); self.assertFalse(launch.used)
        self.assertEqual(launch.runtime.children, {})

    async def test_slow_root_material_check_is_inside_shared_original_35_second_startup(self):
        f = self.fixture(); calls = []
        launch = CompatibilityLaunch(f.rig.ledger, f.root / 'execution', enabled=True)
        launch.runtime.popen = lambda *args, **kwargs: calls.append(args)
        configuration = dict(client_program=asdict(f.program), client_configuration=f.configuration)
        supervisor = replace(f.program, entry='async_product_client/supervisor_driver.py')
        def slow(*args): f.rig.clock.tick(35); return f.program
        with patch('async_product_client.launch.authorize_child', slow), self.assertRaises(ValueError):
            launch.start('launch-root', f.rig.ledger.token, supervisor_program=supervisor, configuration=configuration)
        self.assertEqual(calls, []); self.assertEqual(f.rig.ledger.failed, 'launch-root')
        self.assertEqual(f.rig.ledger.cleanup_deadline_ns, 1000 * SECOND)


if __name__ == '__main__': unittest.main()
