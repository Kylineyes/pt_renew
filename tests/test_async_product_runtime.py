"""实际无GUI创建者报告链及失败原对象保留；没有真实产品/服务/桌面操作。"""
import asyncio
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from async_product_client.core import Clock, Context, Ledger, SECOND, digest
from async_product_client.product import tree_hashes
from async_product_client.runtime import CreatorRuntime, FrozenProgram
from async_product_client.witness import audit_relay


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = Ledger(context=Context('new-offline-task', 'new-offline-dispatch', 'new-run', 'new-session'),
                             cleanup_deadline_ns=Clock().monotonic_ns() + 900 * SECOND, enabled=True)
        self.ledger.diagnostic_deadline_ns = self.ledger.clock.monotonic_ns() + 600 * SECOND
        modules = self.root / 'modules'; modules.mkdir()
        shutil.copytree(ROOT / 'tools/async_product_client', modules / 'async_product_client',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copyfile(ROOT / 'tests/fixtures/async_product_runtime_driver.py', modules / 'driver.py')
        interpreter = Path(sys._base_executable).resolve()
        self.program = FrozenProgram(str(interpreter), digest(interpreter.read_bytes()), str(modules),
                                     tuple(tree_hashes(modules).items()), 'driver.py')

    def runtime(self, **kwargs):
        return CreatorRuntime(self.ledger, self.root / 'evidence', **kwargs)

    @unittest.skipUnless(sys.platform == 'win32', '实际原Popen句柄适配只支持Windows')
    async def test_real_supervisor_client_service_and_leaf_original_popen_reports(self):
        runtime = self.runtime(enabled=True)
        with self.ledger.operation('spawn', 'start'):
            process = runtime.spawn('supervisor', role='supervisor', program=self.program,
                                    configuration=dict(program=asdict(self.program)))
        root = runtime.root_witness('supervisor')
        try:
            await runtime.wait_child('supervisor')
        finally:
            if process.poll() is not None: runtime.poll()
        folder = runtime.children['supervisor']['folder']
        raw = (folder / 'creator-report.json').read_bytes()
        result = root.finish(raw)
        self.assertEqual(result['roles'], ['client', 'product', 'service', 'supervisor'])
        self.assertEqual(result['identities'], 4)
        self.assertTrue(result['lifecycle_complete'])
        self.assertEqual(process.returncode, 0)
        self.assertFalse(result['ready_for_live'])
        self.assertFalse(result['gui_verified'])
        self.assertFalse(result['unknown_short_lived_descendants_covered'])
        service = json.loads((folder / 'client/service/creator-report.json').read_text(encoding='utf-8'))
        self.assertEqual(service['local']['entries'], {})

    async def test_disabled_or_changed_frozen_program_creates_no_process(self):
        calls = []
        runtime = self.runtime(popen=lambda *args, **kwargs: calls.append(args))
        with self.assertRaises(ValueError):
            with self.ledger.operation('disabled', 'start'):
                runtime.spawn('client', role='client', program=self.program)
        self.assertEqual(calls, [])
        self.assertEqual(runtime.children, {})

    async def test_identity_failure_preserves_actual_created_object_without_binding_or_retry(self):
        process = SimpleNamespace(pid=42, returncode=None, poll=lambda: None)
        def inspect(process): raise ValueError('原身份未知')
        runtime = self.runtime(enabled=True, popen=lambda *args, **kwargs: process,
                               handle_api=SimpleNamespace(inspect=inspect))
        with self.assertRaises(ValueError):
            with self.ledger.operation('spawn', 'start'):
                runtime.spawn('client', role='client', program=self.program)
        child = runtime.children['client']
        self.assertIs(child['process'], process)
        self.assertIs(runtime.registry.entries['client']['process'], process)
        self.assertIsNone(runtime.registry.entries['client']['identity'])
        self.assertFalse((child['folder'] / 'parent-binding.json').exists())
        self.assertFalse(runtime.registry.report()['lifecycle_complete'])
        runtime.close_streams(child)

    async def test_slow_source_verification_exhausts_stage_before_popen(self):
        from test_async_product_client import Clock as FakeClock
        self.ledger.clock = FakeClock(); self.ledger.arm_gate(self.ledger.clock.now)
        calls = []
        runtime = self.runtime(enabled=True, popen=lambda *args, **kwargs: calls.append(args))
        from unittest.mock import patch
        original = FrozenProgram.verify
        def verify(program):
            value = original(program); self.ledger.clock.tick(20); return value
        with patch.object(FrozenProgram, 'verify', verify), self.assertRaises(ValueError):
            with self.ledger.operation('spawn', 'start'):
                runtime.spawn('client', role='client', program=self.program)
        self.assertEqual(calls, [])
        self.assertIsNone(runtime.children['client']['process'])
        self.assertTrue(all(stream.closed for stream in runtime.children['client']['streams']))

    async def test_late_exit_zero_does_not_fill_missing_creation_identity_or_clear_failure(self):
        process = SimpleNamespace(pid=42, returncode=None)
        process.poll = lambda: process.returncode
        runtime = self.runtime(enabled=True, popen=lambda *args, **kwargs: process,
                               handle_api=SimpleNamespace(inspect=lambda p: (_ for _ in ()).throw(ValueError('未知'))))
        with self.assertRaises(ValueError):
            with self.ledger.operation('spawn', 'start'):
                runtime.spawn('client', role='client', program=self.program)
        saved = self.ledger.failed, self.ledger.token, self.ledger.not_before_ns
        process.returncode = 0
        report = runtime.poll()
        self.assertEqual(report['entries']['client']['exit_code'], 0)
        self.assertFalse(report['lifecycle_complete'])
        self.assertEqual(saved, (self.ledger.failed, self.ledger.token, self.ledger.not_before_ns))

    async def test_failure_keeps_original_service_until_eof_and_never_clears_expired_budget(self):
        import io
        runtime = self.runtime()
        process = SimpleNamespace(pid=42, returncode=None, stdin=io.BytesIO())
        def poll():
            if process.stdin.closed: process.returncode = 0
            return process.returncode
        process.poll = poll
        runtime.root.mkdir()
        runtime.registry.created('service', process, role='service')
        runtime.registry.identified('service', process, dict(pid=42, birth=100, handle=555,
                                                             original_handle=True, image=self.program.interpreter))
        runtime.children['service'] = dict(process=process, streams=[], outcome='unknown')
        self.ledger.fail('original', '原失败')
        self.ledger.cleanup_deadline_ns = self.ledger.clock.monotonic_ns() - 1
        saved = self.ledger.failed, self.ledger.token, self.ledger.not_before_ns, self.ledger.cleanup_deadline_ns
        report = await runtime.drain_after_failure()
        self.assertTrue(process.stdin.closed)
        self.assertIs(runtime.registry.entries['service']['process'], process)
        self.assertEqual(report['entries']['service']['exit_code'], 0)
        self.assertFalse(report['action_succeeded'])
        self.assertTrue((runtime.root / 'creator-pending.json').is_file())
        self.assertTrue((runtime.root / 'creator-deadline-unknown.json').is_file())
        self.assertEqual(saved, (self.ledger.failed, self.ledger.token, self.ledger.not_before_ns, self.ledger.cleanup_deadline_ns))

    async def test_discovered_descendant_without_original_popen_remains_gap(self):
        runtime = self.runtime()
        runtime.discovered('unknown', pid=99, birth=123, parent='service')
        report = runtime.poll()
        self.assertIn('unknown', report['discovered_gaps'])
        self.assertFalse(report['lifecycle_complete'])


if __name__ == '__main__': unittest.main()
