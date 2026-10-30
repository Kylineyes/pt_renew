"""单请求产品兼容性驱动；假API和合成read记录，不启动真实服务或产品。"""
from dataclasses import asdict
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.core import SECOND
from async_product_client.driver import DriverMailbox, ProductDriver, submit
from async_product_client.runtime import write_once
from async_product_client.shutdown import ShutdownCoordinator
from test_async_product_session import Fixture


class DriverTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, kind='net'):
        folder = self.root / str(len(list(self.root.iterdir()))); folder.mkdir()
        f = Fixture(folder, kind); ledger = f.rig.ledger
        async def start(ident, parent):
            with ledger.operation(ident, parent): pass
            return f.session
        async def close(): return b'original-service-report'
        shutdown = ShutdownCoordinator(ledger, f.rig.owner, session=f.session, connection=SimpleNamespace(close=close))
        f.driver = ProductDriver(ledger, start=start, shutdown=shutdown, enabled=True)
        f.counter = 0
        return f

    def row(self, f, command, **arguments):
        f.counter += 1
        return dict(context=asdict(f.rig.ledger.context), id=f'command-{f.counter}', parent=f.rig.ledger.token,
                    action=command, arguments=arguments)

    async def baseline(self, f):
        await f.driver.execute(self.row(f, 'start'))
        review = await f.driver.execute(self.row(f, 'prepare'))
        await f.driver.execute(self.row(f, 'ack-baseline', **f.rig.read(review)))

    async def file_dialog(self, f):
        await self.baseline(f)
        review = await f.driver.execute(self.row(f, 'command-image'))
        await f.driver.execute(self.row(f, 'command-ack', **f.rig.read(review)))
        await f.driver.execute(self.row(f, 'command-click', image_point=[125, 70]))

    async def test_complete_compatibility_actual_read_path_type_cancel_clean_close_and_stop(self):
        f = self.fixture(); await self.file_dialog(f)
        review = await f.driver.execute(self.row(f, 'file', action='start'))
        await f.driver.execute(self.row(f, 'file', action='ack', **f.rig.read(review)))
        review = await f.driver.execute(self.row(f, 'file', action='type'))
        await f.driver.execute(self.row(f, 'file', action='ack', **f.rig.read(review)))
        await f.driver.execute(self.row(f, 'file', action='choose', choice='cancel', image_point=[650, 485]))
        await f.driver.execute(self.row(f, 'close', action='start', dirty=False))
        await f.driver.execute(self.row(f, 'stop'))
        self.assertTrue(f.driver.stopped)
        self.assertIsNone(f.rig.ledger.failed)
        self.assertIsNone(f.rig.ledger.gate_trigger_ns)
        self.assertEqual(f.rig.process.returncode, 0)
        self.assertEqual([kind for kind, args in f.calls], ['Click', 'Type', 'Click', 'Shortcut'])
        self.assertFalse(f.driver.report()['ready_for_live'])

    async def test_target_b_open_is_refused_without_consuming_an_input(self):
        f = self.fixture(); await self.file_dialog(f); before = list(f.calls)
        with self.assertRaises(ValueError):
            await f.driver.execute(self.row(f, 'file', action='choose', choice='open', image_point=[650, 425]))
        self.assertEqual(f.calls, before)
        self.assertIsNone(f.rig.ledger.gate_trigger_ns)
        self.assertIsNotNone(f.rig.ledger.failed)

    async def test_copper_gate_and_race_release_are_not_compatibility_actions(self):
        for action in ('command-click', 'race', 'release'):
            f = self.fixture('copper'); await self.baseline(f)
            with self.subTest(action=action), self.assertRaises(ValueError):
                await f.driver.execute(self.row(f, action, image_point=[150, 120]))
            self.assertEqual(f.calls, [])
            self.assertIsNone(f.rig.ledger.gate_trigger_ns)

    async def test_failed_file_stage_waits_original_120_then_new_read_cancel_close(self):
        f = self.fixture(); await self.file_dialog(f)
        f.driver.shutdown.fail('original-file', ValueError('原文件框失败'))
        saved = f.rig.ledger.failed, f.rig.ledger.token, f.rig.ledger.not_before_ns
        before = list(f.calls)
        with self.assertRaises(ValueError):
            await f.driver.execute(self.row(f, 'cancel-file', action='start'))
        self.assertEqual(before, f.calls)
        f.rig.clock.tick(120)
        review = await f.driver.execute(self.row(f, 'cancel-file', action='start'))
        await f.driver.execute(self.row(f, 'cancel-file', action='ack', **f.rig.read(review)))
        await f.driver.execute(self.row(f, 'cancel-file', action='choose', choice='cancel', image_point=[650, 485]))
        await f.driver.execute(self.row(f, 'close', action='start', dirty=False))
        await f.driver.execute(self.row(f, 'stop'))
        self.assertEqual(saved, (f.rig.ledger.failed, f.rig.ledger.token, f.rig.ledger.not_before_ns))
        self.assertEqual(f.session.stage, 'retired')
        self.assertTrue(f.driver.stopped)

    async def test_mailbox_keeps_request_and_reply_originals_and_rejects_rewrites(self):
        f = self.fixture(); mailbox = DriverMailbox(f.driver, f.root); mailbox.initialize()
        row = self.row(f, 'start'); path = submit(f.root, row)
        self.assertTrue(await mailbox.step())
        reply = json.loads((mailbox.replies / '0001.json').read_text(encoding='utf-8'))
        self.assertTrue(reply['completed']); self.assertTrue(path.is_file())
        self.assertFalse(await mailbox.step())
        path.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError): await mailbox.step()
        self.assertEqual(f.calls, [])

    async def test_mailbox_rejects_queued_commands_before_any_action(self):
        f = self.fixture(); mailbox = DriverMailbox(f.driver, f.root); mailbox.initialize()
        submit(f.root, self.row(f, 'start')); submit(f.root, self.row(f, 'prepare'))
        with self.assertRaises(ValueError): await mailbox.step()
        self.assertFalse(f.driver.started); self.assertEqual(f.calls, [])

    async def test_bad_context_old_token_duplicate_and_unknown_schema_never_run_start(self):
        for mode in ('context', 'token', 'extra', 'duplicate', 'disabled'):
            f = self.fixture(); row = self.row(f, 'start')
            if mode == 'context': row['context']['session_id'] = 'old-session'
            if mode == 'token': row['parent'] = 'old'
            if mode == 'extra': row['hidden_tool'] = 'Click'
            if mode == 'duplicate': f.driver.seen.add(row['id'])
            if mode == 'disabled': f.driver.enabled = False
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.driver.execute(row)
            self.assertFalse(f.driver.started); self.assertEqual(f.calls, [])

    async def test_start_final_persistence_failure_still_uses_retained_session_for_normal_close(self):
        f = self.fixture(); ledger = f.rig.ledger
        async def start(ident, parent):
            raise ValueError('装配完成后的最终落盘失败')
        f.driver.start = start
        with self.assertRaises(ValueError): await f.driver.execute(self.row(f, 'start'))
        self.assertIsNone(f.driver.session)
        saved = ledger.failed, ledger.token, ledger.not_before_ns
        f.rig.clock.tick(120)
        await f.driver.execute(self.row(f, 'close', action='start', dirty=False))
        self.assertEqual(f.session.stage, 'retired')
        self.assertEqual(saved, (ledger.failed, ledger.token, ledger.not_before_ns))
        self.assertEqual(f.calls, [('Shortcut', {'shortcut': 'alt+f4'})])

    async def test_reply_persistence_crossing_deadline_latches_failure_before_another_action(self):
        from unittest.mock import patch
        f = self.fixture(); ledger = f.rig.ledger
        ledger.diagnostic_deadline_ns = f.rig.clock.now + SECOND
        mailbox = DriverMailbox(f.driver, f.root); mailbox.initialize()
        submit(f.root, self.row(f, 'start'))
        original = write_once
        def slow(path, raw):
            original(path, raw)
            if Path(path).name == '0001.json': f.rig.clock.tick(1)
        with patch('async_product_client.driver.write_once', slow): await mailbox.step()
        self.assertEqual(ledger.failed, 'mailbox-persist-1')
        self.assertTrue((mailbox.replies / '0001-rejected.json').is_file())
        submit(f.root, self.row(f, 'prepare')); await mailbox.step()
        self.assertEqual(ledger.failed, 'mailbox-persist-1')
        self.assertEqual(f.rig.shots, 0); self.assertEqual(f.calls, [])

    async def test_malformed_command_is_failed_once_and_retains_raw_and_original_cooldown(self):
        f = self.fixture(); mailbox = DriverMailbox(f.driver, f.root); mailbox.initialize()
        write_once(mailbox.inbox / 'broken.json', b'{broken')
        self.assertTrue(await mailbox.step())
        saved = f.rig.ledger.failed, f.rig.ledger.token, f.rig.ledger.not_before_ns
        self.assertFalse(await mailbox.step())
        self.assertEqual(saved, (f.rig.ledger.failed, f.rig.ledger.token, f.rig.ledger.not_before_ns))
        reply = json.loads((mailbox.replies / '0001.json').read_text(encoding='utf-8'))
        self.assertFalse(reply['completed']); self.assertEqual(f.calls, [])


if __name__ == '__main__': unittest.main()
