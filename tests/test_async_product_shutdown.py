"""初始化、未绑定、文件框和未知探针的正常收尾回归；全部假GUI。"""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.core import SECOND
from async_product_client.product import ProductOwner
from async_product_client.shutdown import ShutdownCoordinator
from test_async_product_client import Rig
from test_async_product_session import Fixture as SessionFixture
from test_async_product_probe import ProbeFixture


class ShutdownTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    async def test_initialization_failure_before_product_creation_has_no_desktop_work(self):
        rig = Rig(self.root)
        shutdown = ShutdownCoordinator(rig.ledger, rig.owner)
        shutdown.fail('initialize', ValueError('初始化失败'))
        self.assertEqual(shutdown.poll()['next_action'], 'wait-original-cooldown')
        rig.clock.tick(120)
        report = shutdown.poll()
        self.assertEqual(report['next_action'], 'publish-local-report')
        self.assertTrue(report['lifecycle_complete'])
        self.assertFalse(report['action_succeeded'])
        self.assertEqual(report['failed_id'], 'initialize')
        self.assertEqual(rig.native_calls, 0); self.assertEqual(rig.calls, [])

    async def test_unbound_original_product_is_preserved_and_never_closed_by_pid(self):
        rig = Rig(self.root); rig.launch(); rig.owner.identity = None
        shutdown = ShutdownCoordinator(rig.ledger, rig.owner)
        shutdown.fail('discover', ValueError('主窗未知')); rig.clock.tick(120)
        report = shutdown.poll()
        self.assertEqual(report['next_action'], 'preserve-unbound-product')
        self.assertFalse(report['lifecycle_complete'])
        self.assertEqual(rig.calls, []); self.assertEqual(rig.native_calls, 0)

    async def test_identity_unknown_late_exit_zero_only_updates_lifecycle_observation(self):
        rig = Rig(self.root); rig.launch(); rig.owner.process_identity = None
        shutdown = ShutdownCoordinator(rig.ledger, rig.owner)
        shutdown.fail('identity', ValueError('创建身份未知')); rig.process.returncode = 0; rig.clock.tick(120)
        report = shutdown.poll()
        self.assertEqual(report['original_product_exit'], 0)
        self.assertFalse(report['lifecycle_complete'])
        self.assertFalse(report['action_succeeded'])
        self.assertEqual(report['failed_id'], 'identity')

    async def test_failure_before_gate_attachment_can_normally_close_clean_product_after_cooldown(self):
        fixture = SessionFixture(self.root); rig, session = fixture.rig, fixture.session
        await fixture.baseline()
        shutdown = ShutdownCoordinator(rig.ledger, rig.owner, session=session)
        shutdown.fail('pre-gate', ValueError('门闩前失败'))
        saved = rig.ledger.failed, rig.ledger.token, rig.ledger.not_before_ns
        with self.assertRaises(ValueError):
            await session.close_step('early-close', rig.ledger.token, action='start', dirty=False)
        self.assertEqual(fixture.calls, [])
        rig.clock.tick(120)
        await session.close_step('close', rig.ledger.token, action='start', dirty=False)
        self.assertEqual(session.stage, 'retired')
        self.assertEqual(fixture.calls, [('Shortcut', dict(shortcut='alt+f4'))])
        self.assertEqual(rig.process.returncode, 0)
        self.assertEqual(saved, (rig.ledger.failed, rig.ledger.token, rig.ledger.not_before_ns))

    async def open_dialog(self, fixture):
        session, rig = fixture.session, fixture.rig
        await fixture.baseline()
        review = await session.capture_command('command', rig.ledger.token)
        await session.ack_command('command-read', rig.ledger.token, **rig.read(review))
        await session.invoke_command('invoke', rig.ledger.token, image_point=[125, 70])

    async def test_file_failure_requires_new_actual_read_then_one_cancel_and_normal_close(self):
        fixture = SessionFixture(self.root); session, rig = fixture.session, fixture.rig
        await self.open_dialog(fixture)
        shutdown = ShutdownCoordinator(rig.ledger, rig.owner, session=session)
        shutdown.fail('file-stage', ValueError('文件框阶段失败'))
        saved = rig.ledger.failed, rig.ledger.token, rig.ledger.not_before_ns
        rig.clock.tick(120)
        self.assertEqual(shutdown.poll()['next_action'], 'read-and-cancel-file-dialog')
        review = await session.cancel_file_step('cancel-image', rig.ledger.token, action='start')
        self.assertEqual(len(fixture.calls), 1)
        await session.cancel_file_step('cancel-read', rig.ledger.token, action='ack', **rig.read(review))
        await session.cancel_file_step('cancel', rig.ledger.token, action='choose', choice='cancel', image_point=[650, 485])
        self.assertEqual(session.stage, 'cancelled')
        self.assertFalse(any(tool == 'Type' for tool, args in fixture.calls))
        await session.close_step('close', rig.ledger.token, action='start', dirty=False)
        self.assertEqual(session.stage, 'retired')
        self.assertEqual(len(fixture.calls), 3)
        self.assertEqual(saved, (rig.ledger.failed, rig.ledger.token, rig.ledger.not_before_ns))
        self.assertIsNone(rig.ledger.gate_trigger_ns)

    async def test_open_click_postcheck_failure_retains_cancel_path_before_dialog_object_exists(self):
        fixture = SessionFixture(self.root); session, rig = fixture.session, fixture.rig
        await fixture.baseline()
        review = await session.capture_command('command', rig.ledger.token)
        await session.ack_command('command-read', rig.ledger.token, **rig.read(review))
        def mutation(row):
            if fixture.mode == 'file': raise ValueError('点击后观察未知')
            return row
        fixture.native_mutation = mutation
        with self.assertRaises(ValueError):
            await session.invoke_command('invoke', rig.ledger.token, image_point=[125, 70])
        self.assertIsNone(session.dialog)
        self.assertTrue(session.command.used)
        self.assertEqual(len(fixture.calls), 1)
        fixture.native_mutation = lambda row: row
        rig.clock.tick(120)
        shutdown = ShutdownCoordinator(rig.ledger, rig.owner, session=session)
        self.assertEqual(shutdown.poll()['next_action'], 'read-and-cancel-file-dialog')
        review = await session.cancel_file_step('cancel-image', rig.ledger.token, action='start')
        await session.cancel_file_step('cancel-read', rig.ledger.token, action='ack', **rig.read(review))
        await session.cancel_file_step('cancel', rig.ledger.token, action='choose', choice='cancel', image_point=[650, 485])
        await session.close_step('close', rig.ledger.token, action='start', dirty=False)
        self.assertEqual(session.stage, 'retired')
        self.assertEqual(rig.ledger.failed, 'invoke')
        self.assertEqual(len(fixture.calls), 3)

    async def test_active_original_worker_blocks_close_without_sending_alt_f4(self):
        fixture = SessionFixture(self.root); rig, session = fixture.rig, fixture.session
        await fixture.target(attach=False)
        rig.ledger.fail('attach', '尚未绑定门闩'); rig.clock.tick(120)
        before = list(fixture.calls)
        with self.assertRaises(ValueError):
            await session.close_step('close', rig.ledger.token, action='start', dirty=False)
        self.assertEqual(fixture.calls, before)
        self.assertFalse(session.close.used)

    async def test_unknown_probe_writes_stop_and_prevents_more_native_even_after_late_zero(self):
        fixture = ProbeFixture(self.root); rig = fixture.rig; fixture.mode = 'hung'
        with self.assertRaises(ValueError): await fixture.run()
        shutdown = ShutdownCoordinator(rig.ledger, rig.owner, probe=fixture.probe)
        shutdown.stop_probes(); rig.clock.tick(120)
        saved = rig.ledger.failed, rig.ledger.token, rig.ledger.not_before_ns
        self.assertEqual(shutdown.poll()['next_action'], 'preserve-unknown-probe')
        fixture.mode = 'valid'
        report = shutdown.poll()
        self.assertEqual(report['probes'][0]['exit_code'], 0)
        self.assertEqual(report['next_action'], 'preserve-unknown-probe')
        self.assertEqual(len(fixture.calls), 1)
        self.assertEqual(saved, (rig.ledger.failed, rig.ledger.token, rig.ledger.not_before_ns))

    async def test_service_cannot_stop_before_product_exit_or_during_cooldown(self):
        rig = Rig(self.root); rig.launch(); calls = []
        async def close(): calls.append('EOF'); return '原报告'.encode('utf-8')
        connection = SimpleNamespace(close=close)
        shutdown = ShutdownCoordinator(rig.ledger, rig.owner, connection=connection)
        shutdown.fail('failed', ValueError('失败'))
        with self.assertRaises(ValueError): await shutdown.stop_service()
        rig.clock.tick(120)
        with self.assertRaises(ValueError): await shutdown.stop_service()
        rig.process.returncode = 0
        self.assertEqual(await shutdown.stop_service(), '原报告'.encode('utf-8'))
        with self.assertRaises(ValueError): await shutdown.stop_service()
        self.assertEqual(calls, ['EOF'])
        self.assertEqual(rig.calls, [])


if __name__ == '__main__': unittest.main()
