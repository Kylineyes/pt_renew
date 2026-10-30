"""原阶段剩余时间回归；假时钟/工具/探针，不访问桌面。"""
import asyncio
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.core import Context, Ledger, SECOND
from async_product_client.transport import McpProductTransport
from test_async_product_adapters import Clock, Connection
from test_async_product_client import Rig
from test_async_product_probe import ProbeFixture


class DeadlineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def ledger(self):
        clock = Clock()
        return Ledger(context=Context('task', 'dispatch', 'run', 'session'), clock=clock,
                      cleanup_deadline_ns=910 * SECOND, enabled=True)

    def adapter(self, ledger):
        connection = Connection(ledger.clock)
        connection.row = dict(is_error=False, content=[dict(type='text', text='Single left clicked at (1,2).')])
        adapter = McpProductTransport(ledger, connection, self.root / 'calls', enabled=True,
                                      validate=lambda tool, args: None)
        return adapter, connection

    async def test_slow_schema_precheck_exhausts_t1_before_tool_dispatch(self):
        ledger = self.ledger(); ledger.arm_gate(ledger.clock.now)
        adapter, connection = self.adapter(ledger)
        adapter.validate = lambda *args: ledger.clock.tick(20)
        with self.assertRaises(ValueError):
            with ledger.operation('slow', 'start'):
                await adapter('Click', dict(loc=[1, 2]))
        self.assertEqual(connection.calls, [])
        self.assertEqual(adapter.calls, [])
        self.assertEqual(ledger.failed, 'slow')
        self.assertEqual(ledger.not_before_ns, ledger.clock.now + 120 * SECOND)

    async def test_actual_wait_uses_remaining_after_schema_and_start_persistence(self):
        ledger = self.ledger(); trigger = ledger.clock.now; ledger.arm_gate(trigger)
        adapter, connection = self.adapter(ledger)
        adapter.validate = lambda *args: ledger.clock.tick(3)
        original = adapter.write
        def write(name, row):
            original(name, row)
            if name.endswith('-start.json'): ledger.clock.tick(4)
        adapter.write = write
        observed = []
        original_wait = asyncio.wait_for
        async def wait(awaitable, timeout):
            observed.append(timeout)
            return await original_wait(awaitable, timeout)
        with patch('async_product_client.transport.asyncio.wait_for', wait):
            with ledger.operation('call', 'start'):
                await adapter('Click', dict(loc=[1, 2]))
        self.assertEqual(observed, [13.])
        self.assertEqual(adapter.calls[0]['deadline_ns'], trigger + 20 * SECOND)
        self.assertEqual(len(connection.calls), 1)

    async def test_raw_normalized_and_final_persistence_each_count_toward_t1(self):
        for suffix in ('raw.json', 'normalized.json', 'end.json'):
            with self.subTest(suffix=suffix):
                ledger = self.ledger(); ledger.arm_gate(ledger.clock.now)
                adapter, connection = self.adapter(ledger)
                original = adapter.write
                def write(name, row):
                    original(name, row)
                    if name.endswith(suffix): ledger.clock.tick(20)
                adapter.write = write
                with self.assertRaises(ValueError):
                    with ledger.operation('call', 'start'):
                        await adapter('Click', dict(loc=[1, 2]))
                self.assertEqual(len(connection.calls), 1)
                self.assertEqual(ledger.token, 'start')
                self.assertEqual(ledger.failed, 'call')
                # 独立子例使用独立证据目录。
                adapter.root.rename(self.root / suffix)

    async def test_unknown_tool_is_not_retried_after_late_lifecycle_exit(self):
        ledger = self.ledger(); ledger.arm_gate(ledger.clock.now)
        adapter, connection = self.adapter(ledger)
        connection.error = TimeoutError('传输结果未知')
        with self.assertRaises(TimeoutError):
            with ledger.operation('unknown', 'start'):
                await adapter('Click', dict(loc=[1, 2]))
        saved = ledger.failed, ledger.token, ledger.not_before_ns, ledger.cleanup_deadline_ns
        ledger.clock.tick(121)
        with self.assertRaises(ValueError):
            with ledger.operation('retry', ledger.token):
                await adapter('Click', dict(loc=[1, 2]))
        self.assertEqual(len(connection.calls), 1)
        self.assertEqual(saved, (ledger.failed, ledger.token, ledger.not_before_ns, ledger.cleanup_deadline_ns))

    async def test_operation_request_and_complete_persistence_are_inside_deadline(self):
        for kind in ('request', 'complete'):
            ledger = self.ledger(); ledger.arm_gate(ledger.clock.now)
            ledger.emit = lambda row: ledger.clock.tick(20) if row['kind'] == kind else None
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                with ledger.operation('persist', 'start'): pass
            self.assertEqual(ledger.token, 'start')
            self.assertEqual(ledger.failed, 'persist')
            self.assertFalse(ledger.busy)

    async def test_t1_t2_release_start_and_finish_are_strict_original_absolute_limits(self):
        for stage, seconds in (('gate', 20), ('edit', 50), ('release-start', 55), ('release-finish', 60)):
            ledger = self.ledger(); trigger = ledger.clock.now; ledger.arm_gate(trigger)
            for next_stage in ('edit', 'release-start', 'release-finish'):
                if ledger.gate_phase == stage: break
                ledger.advance_gate(next_stage)
            ledger.clock.tick(seconds)
            with self.subTest(stage=stage), self.assertRaises(ValueError):
                with ledger.operation('expired', 'start'): pass
            self.assertEqual(ledger.failed, 'expired')
            self.assertEqual(ledger.gate_trigger_ns, trigger)
            self.assertEqual(ledger.cleanup_deadline_ns, 910 * SECOND)

    async def test_request_or_ack_cannot_rearm_or_skip_phase(self):
        ledger = self.ledger(); trigger = ledger.clock.now; ledger.arm_gate(trigger)
        ledger.clock.tick(1)
        with self.assertRaises(ValueError): ledger.arm_gate(ledger.clock.now)
        with self.assertRaises(ValueError): ledger.advance_gate('release-start')
        ledger.arm_gate(trigger)
        self.assertEqual(ledger.current_deadline_ns, trigger + 20 * SECOND)

    async def test_cleanup_bypasses_expired_gate_but_not_cooldown_or_total_budget(self):
        ledger = self.ledger(); ledger.arm_gate(ledger.clock.now); ledger.fail('original', '原失败')
        saved = ledger.failed, ledger.token, ledger.not_before_ns
        with self.assertRaises(ValueError):
            with ledger.operation('early', 'start', cleanup=True): pass
        ledger.clock.tick(120)
        with ledger.operation('cleanup', 'start', cleanup=True):
            self.assertEqual(ledger.current_deadline_ns, 910 * SECOND)
            ledger.time_left((35 + 5 + 40) * SECOND)
        self.assertEqual(saved, (ledger.failed, ledger.token, ledger.not_before_ns))
        ledger.clock.now = ledger.cleanup_deadline_ns
        with self.assertRaises(ValueError):
            with ledger.operation('late', 'start', cleanup=True): pass

    async def test_probe_source_hash_cost_is_in_original_five_second_cap(self):
        fixture = ProbeFixture(self.root)
        probe, ledger = fixture.probe, fixture.rig.ledger
        original = probe.sources
        def sources(): original(); ledger.clock.tick(5)
        probe.sources = sources
        with self.assertRaises(ValueError): await fixture.run()
        self.assertEqual(fixture.calls, [])
        self.assertTrue(probe.failed)
        self.assertEqual(ledger.failed, 'probe')

    async def test_probe_uses_stage_deadline_and_late_exit_only_updates_lifecycle(self):
        fixture = ProbeFixture(self.root); fixture.mode = 'hung'
        ledger, probe = fixture.rig.ledger, fixture.probe
        trigger = ledger.clock.now; ledger.arm_gate(trigger); ledger.clock.tick(19)
        with self.assertRaises(ValueError): await fixture.run()
        child = probe.children[0]
        self.assertEqual(child['request']['deadline_ns'], trigger + 20 * SECOND)
        self.assertLessEqual(ledger.clock.now, trigger + 20 * SECOND)
        self.assertEqual(len(fixture.calls), 1)
        saved = ledger.failed, ledger.token, ledger.not_before_ns
        fixture.mode = 'valid'; ledger.clock.tick(1)
        self.assertEqual(probe.reap()[0]['exit_code'], 0)
        self.assertFalse(child['accepted'])
        self.assertEqual(saved, (ledger.failed, ledger.token, ledger.not_before_ns))

    async def test_probe_accepted_event_persistence_cannot_make_late_result_accepted(self):
        fixture = ProbeFixture(self.root); ledger = fixture.rig.ledger
        ledger.emit = lambda row: ledger.clock.tick(5) if row['kind'] == 'uia_probe_accepted' else None
        with self.assertRaises(ValueError): await fixture.run()
        child = fixture.probe.children[0]
        self.assertEqual(child['exit_code'], 0)
        self.assertFalse(child['accepted'])
        self.assertTrue(child['stop_requested'])

    async def test_signal_attempt_persistence_crossing_55_sends_no_event_and_consumes_opportunity(self):
        from test_async_product_gate import Fixture
        fixture = Fixture(self.root); await fixture.prepare(); await fixture.edit()
        ledger, clock = fixture.rig.ledger, fixture.rig.clock
        ledger.emit = lambda row: clock.tick(55) if row['kind'] == 'gate_signal_attempt' else None
        with self.assertRaises(ValueError): await fixture.race.release('release', ledger.token)
        self.assertEqual(fixture.signal_calls, [])
        self.assertTrue(fixture.race.release_attempted)
        self.assertTrue(fixture.releaser.used)
        self.assertEqual(ledger.failed, 'release')
        self.assertEqual(sorted(fixture.close_calls), ['cancel', 'release'])

    async def test_race_ack_postcheck_and_completion_cost_cannot_silently_advance_t1(self):
        rig = Rig(self.root); rig.launch()
        await rig.race.capture_gate('gate', rig.ledger.token)
        evidence = rig.read('gate-image')
        rig.ledger.emit = lambda row: rig.clock.tick(20) if row['kind'] == 'complete' else None
        with self.assertRaises(ValueError):
            await rig.race.ack('ack', rig.ledger.token, review_id='gate-image', **evidence)
        self.assertEqual(rig.ledger.gate_phase, 'gate')
        self.assertEqual(rig.ledger.failed, 'ack')
        self.assertEqual(rig.ledger.token, 'gate')


if __name__ == '__main__': unittest.main()
