"""有界COM探针和主窗发现契约；只用假子进程/时钟/API，不加载真实COM或桌面。"""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.core import SECOND, digest
from async_product_client.probe import BoundedUiaProbe
from async_product_client.discovery import ProductMainDiscovery
from async_product_client.product import tree_hashes
from test_async_product_client import Rig
from test_async_product_native import Fixture as NativeFixture


class ProbeFixture:
    def __init__(self, root):
        self.root = Path(root)
        self.rig = Rig(root); self.rig.launch()
        self.creator = SimpleNamespace(process=self.rig.process, inspect_created=self.rig.inspect)
        self.interpreter = self.root / 'python.exe'; self.interpreter.write_bytes(b'fake interpreter')
        self.package = self.root / 'package'; (self.package / 'windows_mcp').mkdir(parents=True)
        for index in range(77): (self.package / 'windows_mcp' / f'module{index}.py').write_bytes(str(index).encode())
        self.modules = self.root / 'tools'; (self.modules / 'async_product_client').mkdir(parents=True)
        for name in ('probe_worker.py', 'native.py', 'core.py', 'product.py', 'events.py', 'race.py', '__init__.py'):
            (self.modules / 'async_product_client' / name).write_bytes(name.encode())
        self.calls, self.processes = [], []
        self.mode = 'valid'
        self.mutate = lambda result: None
        self.delay = .1
        self.child_handle_error = False
        self.pause_calls = []
        fixture = self
        class Process:
            def __init__(self, request_path):
                self.pid = 1000 + len(fixture.processes)
                self.returncode = None
                self.path = Path(request_path)
                self.start = fixture.rig.clock.now
            def poll(self):
                if fixture.mode == 'hung' or fixture.rig.clock.now - self.start < round(fixture.delay * SECOND): return None
                if self.returncode is None:
                    request = json.loads(self.path.read_text(encoding='utf-8'))
                    row = dict(schema_version=1, context=request['context'], nonce=request['nonce'], target=request['target'],
                               child_pid=self.pid, request_sha256=digest(self.path.read_bytes()), started_ns=self.start,
                               finished_ns=fixture.rig.clock.now, completed=True, readonly=True, input_calls=0,
                               com_uninitialized=True, dpi_restored=True,
                               uia=dict(readonly=True, root=dict(pid=42, hwnd=request['target']['hwnd']), focus=None, buttons=[], modal=False))
                    fixture.mutate(row)
                    (self.path.parent / 'result.json').write_text(json.dumps(row), encoding='utf-8')
                    self.returncode = 1 if fixture.mode == 'nonzero' else 0
                return self.returncode
        def popen(command, **kwargs):
            fixture.calls.append((command, kwargs))
            if fixture.mode == 'create-error': raise ValueError('原创建失败/未知')
            process = Process(command[-1]); fixture.processes.append(process); return process
        class Handles:
            def inspect(self, process):
                if fixture.child_handle_error: raise ValueError('探针句柄身份未知')
                return dict(pid=process.pid, birth=5000, image=str(fixture.interpreter), handle=6000, original_handle=True)
        async def sleep(seconds):
            fixture.pause_calls.append(seconds)
            fixture.rig.clock.tick(seconds)
        self.probe = BoundedUiaProbe(self.rig.ledger, self.rig.owner, self.creator,
                                    interpreter=self.interpreter, interpreter_sha256=digest(self.interpreter.read_bytes()),
                                    package_root=self.package, package_files=tree_hashes(self.package / 'windows_mcp'),
                                    module_root=self.modules, module_files=tree_hashes(self.modules),
                                    evidence_root=self.root / 'queries', deadline_ns=self.rig.clock.now + 20 * SECOND,
                                    enabled=True, popen=popen, handle_api=Handles(), sleeper=sleep)
        self.added = False

    async def run(self, ident='probe'):
        with self.rig.ledger.operation(ident, self.rig.ledger.token):
            return await self.probe.inspect(99, 42)


class ProbeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixtures = []
        self.addCleanup(self.cleanup_streams)

    def cleanup_streams(self):
        for fixture in self.fixtures:
            for child in fixture.probe.children:
                fixture.probe.close_streams(child)

    def fixture(self):
        folder = self.root / str(len(list(self.root.iterdir()))); folder.mkdir()
        fixture = ProbeFixture(folder); self.fixtures.append(fixture); return fixture

    async def test_original_child_exit_zero_nonce_context_and_restore_proof_required(self):
        f = self.fixture()
        row = await f.run()
        self.assertEqual(row['root'], dict(pid=42, hwnd=99))
        self.assertEqual(len(f.calls), 1)
        command, kwargs = f.calls[0]
        self.assertEqual(command[1:4], ['-B', '-X', 'utf8'])
        self.assertFalse(kwargs['shell'])
        child = f.probe.children[0]
        self.assertIs(child['process'], f.processes[0])
        self.assertEqual(child['exit_code'], 0)
        self.assertTrue(child['accepted'])
        self.assertTrue(all(s.closed for s in child['streams']))
        self.assertTrue(max(f.pause_calls) <= .1)
        self.assertEqual(f.rig.calls, [])
        self.assertIsNone(f.rig.ledger.failed)

    async def test_disabled_cooldown_wrong_target_source_and_total_deadline_create_nothing(self):
        for mode in ('disabled', 'cooldown', 'pid', 'package', 'module', 'interpreter', 'deadline'):
            f = self.fixture()
            if mode == 'disabled': f.probe.enabled = False
            if mode == 'cooldown': f.rig.ledger.not_before_ns = f.rig.clock.now + 120 * SECOND
            if mode == 'pid': f.rig.process.pid = 43
            if mode == 'package': (f.package / 'windows_mcp/module0.py').write_bytes(b'changed')
            if mode == 'module': (f.modules / 'async_product_client/core.py').write_bytes(b'changed')
            if mode == 'interpreter': f.interpreter.write_bytes(b'changed')
            if mode == 'deadline': f.rig.clock.tick(21)
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.calls, [])
            self.assertFalse((f.root / 'queries').exists())

    async def test_hung_probe_preserves_popen_deadline_and_failure_without_kill_or_retry(self):
        f = self.fixture(); f.mode = 'hung'
        deadline = f.probe.deadline_ns
        with self.assertRaises(ValueError): await f.run()
        self.assertTrue(f.probe.failed)
        self.assertIs(f.probe.children[0]['process'], f.processes[0])
        self.assertIsNone(f.probe.children[0]['exit_code'])
        self.assertTrue((Path(f.probe.children[0]['folder']) / 'stop-requested').is_file())
        self.assertFalse(f.probe.children[0]['accepted'])
        self.assertEqual(f.probe.deadline_ns, deadline)
        self.assertTrue(max(f.pause_calls) <= 1)
        saved = f.rig.ledger.failed, f.rig.ledger.not_before_ns, f.rig.ledger.token
        self.assertEqual(f.probe.reap()[0]['outcome'], 'unknown')
        f.mode = 'valid'
        self.assertEqual(f.probe.reap()[0]['exit_code'], 0)
        self.assertFalse(f.probe.children[0]['accepted'])
        self.assertEqual((f.rig.ledger.failed, f.rig.ledger.not_before_ns, f.rig.ledger.token), saved)
        f.rig.clock.tick(121)
        with self.assertRaises(ValueError): await f.run('retry')
        self.assertEqual(len(f.calls), 1)

    async def test_child_identity_error_keeps_original_popen_and_creator_failure_closes_logs(self):
        for mode in ('identity', 'create'):
            f = self.fixture()
            if mode == 'identity': f.child_handle_error = True
            else: f.mode = 'create-error'
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.run()
            child = f.probe.children[0]
            self.assertTrue(f.probe.failed)
            self.assertEqual(len(f.calls), 1)
            if mode == 'identity': self.assertIs(child['process'], f.processes[0])
            else:
                self.assertIsNone(child['process'])
                self.assertTrue(all(s.closed for s in child['streams']))

    async def test_malformed_wrong_nonce_context_pid_target_restore_or_nonzero_never_accepted(self):
        cases = [('nonce', 'old'), ('context', {}), ('child_pid', 500), ('target', {}),
                 ('request_sha256', '0' * 64), ('completed', False), ('readonly', False),
                 ('input_calls', True), ('com_uninitialized', False), ('dpi_restored', False),
                 ('finished_ns', 10**30)]
        for key, value in cases:
            f = self.fixture(); f.mutate = lambda row: row.update({key: value})
            with self.subTest(key=key), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.probe.children[0]['exit_code'], 0)
            self.assertFalse(f.probe.children[0]['accepted'])
            self.assertEqual(len(f.calls), 1)
        f = self.fixture(); f.mode = 'nonzero'
        with self.assertRaises(ValueError): await f.run()
        self.assertEqual(f.probe.children[0]['exit_code'], 1)
        self.assertFalse(f.probe.children[0]['accepted'])

    async def test_total_deadline_and_max_queries_do_not_reset_between_successes(self):
        f = self.fixture(); f.probe.max_queries = 1
        await f.run()
        with self.assertRaises(ValueError): await f.run('second')
        self.assertEqual(len(f.calls), 1)
        f = self.fixture(); deadline = f.probe.deadline_ns
        await f.run(); f.rig.clock.tick(21)
        with self.assertRaises(ValueError): await f.run('second')
        self.assertEqual(f.probe.deadline_ns, deadline)
        self.assertEqual(len(f.calls), 1)

    async def test_async_uia_is_accepted_by_native_collector_without_parent_com_calls(self):
        folder = self.root / 'native'; folder.mkdir()
        f = NativeFixture(folder)
        original = f.uia.inspect
        calls = []
        async def inspect(hwnd, pid): calls.append(hwnd); return original(hwnd, pid)
        f.uia.inspect = inspect
        row = await f.run()
        self.assertEqual(row['foreground']['focus_kind'], 'canvas')
        self.assertEqual(calls, [99, 99])
        self.assertEqual(f.rig.calls, [])


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, loaded=True):
        folder = self.root / str(len(list(self.root.iterdir()))); folder.mkdir()
        f = NativeFixture(folder)
        f.rig.owner.identity = None
        title = f.rig.policy.title(False) if loaded else 'PT Renew · 内存编辑 · 不支持保存'
        f.rows[99]['title'] = title
        f.uia_rows[99]['root'].update(name=title, automation_id='mainWindow', control_type=50032)
        f.uia_rows[99]['modal'] = False
        f.discovery = ProductMainDiscovery(f.rig.ledger, f.rig.owner, f.creator, f.rig.policy,
                                           uia=f.uia, api=f.api, enabled=True)
        return f

    async def run_discovery(self, f, loaded=True):
        with f.rig.ledger.operation('discover', f.rig.ledger.token):
            return await f.discovery.run(loaded=loaded)

    async def test_initial_empty_and_loaded_title_bind_only_once_without_activation(self):
        for loaded in (False, True):
            f = self.fixture(loaded)
            row = await self.run_discovery(f, loaded)
            self.assertEqual((row.pid, row.birth, row.hwnd), (42, 100, 99))
            self.assertEqual(f.rig.calls, [])
            self.assertIs(f.rig.owner.identity, row)
            with self.assertRaises(ValueError): await f.discovery.run(loaded=loaded)

    async def test_wrong_pid_owner_title_class_foreground_disabled_modal_and_uia_identity_do_not_bind(self):
        for mode in ('pid', 'owner', 'title', 'class', 'foreground', 'disabled', 'modal', 'uia-id', 'uia-type'):
            f = self.fixture()
            if mode == 'pid': f.rows[99]['pid'] = 43
            if mode == 'owner': f.rows[99]['owner'] = 1
            if mode == 'title': f.rows[99]['title'] += 'extra'
            if mode == 'class': f.rows[99]['cls'] = 'Tk'
            if mode == 'foreground': f.foreground = 100
            if mode == 'disabled': f.rows[99]['enabled'] = False
            if mode == 'modal': f.uia_rows[99]['modal'] = True
            if mode == 'uia-id': f.uia_rows[99]['root']['automation_id'] = 'other'
            if mode == 'uia-type': f.uia_rows[99]['root']['control_type'] = 50033
            with self.subTest(mode=mode), self.assertRaises(ValueError): await self.run_discovery(f)
            self.assertIsNone(f.rig.owner.identity)
            self.assertEqual(f.rig.calls, [])

    async def test_same_class_dialog_or_second_main_cannot_be_counted_as_unique_product(self):
        for owner in (0, 99):
            f = self.fixture()
            f.rows[101] = dict(f.rows[99], hwnd=101, owner=owner)
            f.rects[101] = list(f.rects[99])
            with self.assertRaises(ValueError): await self.run_discovery(f)
            self.assertIsNone(f.rig.owner.identity)

    async def test_window_or_popen_changed_during_async_query_preserves_unbound_state(self):
        for mode in ('title', 'rect', 'pid', 'deadline'):
            f = self.fixture()
            original = f.uia.inspect
            async def inspect(hwnd, pid):
                row = original(hwnd, pid)
                if mode == 'title': f.rows[99]['title'] = 'changed'
                if mode == 'rect': f.rects[99][0] += 10
                if mode == 'pid': f.rig.process.pid = 43
                if mode == 'deadline': f.rig.clock.tick(1000)
                return row
            f.uia.inspect = inspect
            with self.subTest(mode=mode), self.assertRaises(ValueError): await self.run_discovery(f)
            self.assertIsNone(f.rig.owner.identity)
            self.assertEqual(f.rig.calls, [])

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def request(self, folder):
        from async_product_client.probe_worker import TOOLS
        from async_product_client.core import Context
        package = folder / 'package'; (package / 'windows_mcp').mkdir(parents=True)
        for index in range(77): (package / 'windows_mcp' / f'module{index}.py').write_bytes(str(index).encode())
        row = dict(schema_version=1, context=asdict(Context('task', 'dispatch', 'run', 'session')),
                   nonce='00000000-0000-4000-8000-000000000001', target=dict(pid=42, birth=100, hwnd=99),
                   readonly=True, input_calls=0, created_mono_ns=10, deadline_ns=100,
                   interpreter=str(Path(sys.executable).resolve()), interpreter_sha256=digest(Path(sys.executable).read_bytes()),
                   module_root=str(TOOLS), module_files={'async_product_client/probe_worker.py': digest((TOOLS / 'async_product_client/probe_worker.py').read_bytes())},
                   package_root=str(package), package_files=tree_hashes(package / 'windows_mcp'))
        path = folder / 'request.json'; path.write_text(json.dumps(row), encoding='utf-8')
        return path, row

    def test_worker_success_is_only_after_cleanup_and_original_request_validation(self):
        from async_product_client.probe_worker import execute
        path, request = self.request(self.root)
        calls = []
        def query(target, package):
            calls.append((target, package))
            return dict(com_uninitialized=True, dpi_restored=True, uia=dict(readonly=True, root=dict(pid=42, hwnd=99)))
        self.assertEqual(execute(path, query=query, clock=lambda: 20), 0)
        result = json.loads((self.root / 'result.json').read_text(encoding='utf-8'))
        self.assertTrue(result['completed'])
        self.assertEqual(result['request_sha256'], digest(path.read_bytes()))
        self.assertEqual(result['context'], request['context'])
        self.assertEqual(len(calls), 1)
        with self.assertRaises(ValueError): execute(path, query=query, clock=lambda: 20)
        self.assertEqual(len(calls), 1)

    def test_worker_rejects_preexisting_stop_expired_changed_source_and_restore_failure(self):
        from async_product_client.probe_worker import execute
        for mode in ('stop', 'expired', 'module', 'package', 'com', 'dpi', 'query-error', 'request-changed'):
            folder = self.root / mode; folder.mkdir()
            path, request = self.request(folder)
            calls = []
            if mode == 'stop': (folder / 'stop-requested').write_bytes(b'parent failed')
            if mode == 'module': request['module_files']['async_product_client/probe_worker.py'] = '0' * 64
            if mode == 'package': (folder / 'package/windows_mcp/module0.py').write_bytes(b'changed')
            path.write_text(json.dumps(request), encoding='utf-8')
            def query(target, package):
                calls.append('query')
                if mode == 'query-error': raise ValueError('COM查询失败')
                if mode == 'request-changed': path.write_bytes(path.read_bytes() + b' ')
                return dict(com_uninitialized=mode != 'com', dpi_restored=mode != 'dpi', uia=dict(readonly=True))
            code = execute(path, query=query, clock=lambda: 101 if mode == 'expired' else 20)
            self.assertEqual(code, 1)
            result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
            self.assertFalse(result['completed'])
            self.assertEqual(len(calls), 0 if mode in ('stop', 'expired', 'module', 'package') else 1)

    def test_uia_checkpoint_stops_between_queries_without_an_input_or_close_method(self):
        from async_product_client.native import ReadOnlyUia
        calls = []
        class Control:
            ProcessId = 42
            NativeWindowHandle = 99
            Name = 'board'
            ClassName = 'Qt6120QWindowIcon'
            AutomationId = 'mainWindow'
            ControlType = 50032
            IsEnabled = True
            IsOffscreen = False
            def GetPattern(self, pattern): calls.append('pattern'); return None
        count = 0
        def check():
            nonlocal count
            count += 1
            if count > 4: raise ValueError('父已请求停止')
        module = SimpleNamespace(__file__=str(self.root / 'package/windows_mcp/uia/__init__.py'),
                                  ControlFromHandle=lambda hwnd: Control(), PatternId=SimpleNamespace(WindowPattern=1))
        bridge = ReadOnlyUia(module, package_root=self.root / 'package', checkpoint=check)
        with self.assertRaises(ValueError): bridge.inspect(99, 42)
        self.assertEqual(calls, [])


if __name__ == '__main__': unittest.main(verbosity=2)
