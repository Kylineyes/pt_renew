"""应用UUID/原日志/唯一release实质测试；假Popen、事件、时钟和会话，无产品/Win32现场。"""
from dataclasses import asdict
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.core import ApplicationRun, SECOND, digest
from async_product_client.events import ApplicationJournal, GateJournal
from async_product_client.release import GateRelease, ExistingEventApi
from async_product_client.race import RaceClient
from test_async_product_client import Rig
from test_audit_async_race import events

UUID = 'd54f66c5-7d61-4107-bd3b-aa96026eb0ac'


class Fixture:
    def __init__(self, root, kind='net'):
        self.rig = Rig(root, kind=kind); self.rig.launch()
        self.root = Path(root)
        self.rows = events(kind, 'race')[:-1]
        for row in self.rows: row['run_id'] = UUID
        self.rows[0].update(owner_pid='800', owner_creation_filetime='900')
        self.directory = self.root / 'events'; self.directory.mkdir()
        self.write(5)
        rig = self.rig
        class Creator:
            pass
        self.creator = Creator()
        self.creator.kind, self.creator.experiment_directory = kind, self.directory
        self.creator.owner_pid, self.creator.process = 800, rig.process
        self.creator.inspect_created = rig.inspect
        self.current = dict(pid=800, birth=900, original_handle=True)
        self.journal = ApplicationJournal(rig.ledger, rig.owner, self.creator, kind=kind,
                                          current_identity=lambda: dict(self.current))
        self.gate = self.releaser = self.race = None
        self.signal_calls, self.open_calls, self.close_calls = [], [], []
        self.event_state = dict(release=False, cancel=False)
        self.signal_error = None
        self.open_error = None
        self.pause_error = None
        self.signal_action = lambda: self.write(len(self.rows))
        self.pause_calls = []
        fixture = self
        class Api:
            def open_existing(self, name, *, writable):
                fixture.open_calls.append((name, writable))
                if fixture.open_error == len(fixture.open_calls): raise ValueError('打开原事件失败')
                return 'release' if writable else 'cancel'
            def unsignaled(self, handle): return not fixture.event_state[handle]
            def signal(self, handle):
                fixture.signal_calls.append(handle)
                if fixture.signal_error: raise fixture.signal_error
                fixture.signal_action()
            def close(self, handle): fixture.close_calls.append(handle)
        self.api = Api()

    def write(self, count):
        self.count = count
        (self.directory / 'events.jsonl').write_bytes(b''.join(json.dumps(r).encode() + b'\n' for r in self.rows[:count]))

    async def prepare(self):
        rig = self.rig
        with rig.ledger.operation('bind-app', rig.ledger.token):
            self.journal.bind()
        with rig.ledger.operation('baseline-request', rig.ledger.token):
            shot = await rig.io.capture()
            rig.reviews.request('baseline-image', stage='baseline', snapshot=shot, gate_request_id=1,
                                deadline_mono_ns=rig.ledger.cleanup_deadline_ns, app_deadline_ns=None,
                                expected=dict(revision=2, dirty=False, tracks=1, net_sha256='a' * 64))
        with rig.ledger.operation('baseline-ack', rig.ledger.token):
            rig.reviews.ack('baseline-image', **rig.read('baseline-image'))
        rig.clock.tick()
        self.trigger = rig.clock.now
        self.write(8)
        manifest = dict(run_id=UUID, request_id='2', kind=self.creator.kind, pid='42', creation_filetime='100',
                        release_event=f'Local\\PtRenewAsync-{UUID}-2-release',
                        cancel_event=f'Local\\PtRenewAsync-{UUID}-2-cancel')
        (self.directory / 'request-2.json').write_text(json.dumps(manifest), encoding='utf-8')
        with rig.ledger.operation('bind-gate', rig.ledger.token):
            self.gate = GateJournal(self.journal, rig.reviews, baseline_review_id='baseline-image', request_id=2,
                                    trigger_mono_ns=self.trigger, a_sha256='a' * 64, b_sha256='b' * 64, board_sha256='c' * 64)
        self.releaser = GateRelease(self.gate, rig.reviews, enabled=True, event_api=self.api, pause=self.pause)
        self.race = RaceClient(rig.ledger, rig.io, rig.reviews, gate_api=self.gate, release_api=self.releaser,
                               kind=self.creator.kind, request_id=2, trigger_mono_ns=self.trigger,
                               a_sha256='a' * 64, revision=2)
        original = rig.io.transport
        async def transport(tool, args):
            result = await original(tool, args)
            if tool == 'Shortcut' and args.get('shortcut') == 'delete': self.write(9)
            return result
        rig.io.transport = transport

    async def pause(self, seconds):
        self.pause_calls.append(seconds)
        self.rig.clock.tick(seconds)
        if self.pause_error: raise self.pause_error

    async def edit(self):
        rig = self.rig
        first = await self.race.capture_gate('gate-shot', rig.ledger.token)
        await self.race.ack('gate-read', rig.ledger.token, review_id=first, **rig.read(first))
        edit = await self.race.edit('edit', rig.ledger.token, image_point=[500, 400])
        await self.race.ack('edit-read', rig.ledger.token, review_id=edit, **rig.read(edit))


class GateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, kind='net'):
        path = self.root / str(len(list(self.root.iterdir()))); path.mkdir()
        return Fixture(path, kind)

    async def test_both_complete_chains_bind_distinct_client_run_and_actual_random_uuid(self):
        for kind in ('net', 'copper'):
            with self.subTest(kind=kind):
                f = self.fixture(kind); await f.prepare(); rig = f.rig
                self.assertNotEqual(rig.ledger.context.run_id, UUID)
                self.assertEqual(rig.ledger.application.run_id, UUID)
                await f.edit()
                await f.race.release('release', rig.ledger.token)
                final = await f.race.capture_final('final', rig.ledger.token)
                await f.race.ack('final-read', rig.ledger.token, review_id=final, **rig.read(final))
                self.assertTrue(f.race.settled)
                self.assertEqual(f.signal_calls, ['release'])
                self.assertEqual(f.close_calls, ['cancel', 'release'])
                self.assertEqual([x[1] for x in f.open_calls], [True, False])
                self.assertTrue(f.releaser.signal_returned and f.releaser.confirmed)
                self.assertEqual(rig.reviews.requests[final].application_run_id, UUID)
                self.assertEqual(rig.ledger.token, 'final-read')
                self.assertFalse(f.gate.last_observation['gui_verified'])
                self.assertEqual(f.gate.last_state.sampled_app_ns, int(f.rows[-1]['monotonic_ns']))

    async def test_startup_owner_birth_kind_skip_watchdog_and_uuid_mismatch_refuse_binding(self):
        mutations = [dict(owner_pid='801'), dict(owner_creation_filetime='901'), dict(kind_configured='other'),
                     dict(skip=0), dict(watchdog_ms=60001), dict(run_id='client-run'), dict(pid='43')]
        for changes in mutations:
            f = self.fixture(); f.rows[0].update(changes); f.write(5)
            with self.subTest(changes=changes), self.assertRaises((ValueError, AttributeError)):
                with f.rig.ledger.operation('bind', f.rig.ledger.token): f.journal.bind()
            self.assertIsNone(f.rig.ledger.application)
            self.assertEqual(f.open_calls, [])

    async def test_application_binding_is_unique_and_context_identity_immutable(self):
        f = self.fixture(); await f.prepare(); rig = f.rig
        binding = rig.ledger.application
        with self.assertRaises(ValueError):
            with rig.ledger.operation('rebind', rig.ledger.token): rig.ledger.bind_application(binding)
        self.assertIs(rig.ledger.application, binding)
        with self.assertRaises(Exception): binding.run_id = 'changed'
        self.assertEqual(rig.ledger.context.run_id, 'new-run')

    async def test_log_prefix_truncation_rewrite_partial_line_duplicate_field_and_bad_clock_fail_closed(self):
        for mode in ('truncated', 'rewritten', 'partial', 'duplicate-key', 'sequence', 'float-clock', 'bool-clock'):
            f = self.fixture(); await f.prepare(); f.gate.observe()
            path = f.directory / 'events.jsonl'; raw = path.read_bytes()
            if mode == 'truncated': path.write_bytes(raw[:len(raw) // 2])
            elif mode == 'rewritten': path.write_bytes(raw.replace(b'owner_pid', b'other_pid', 1))
            elif mode == 'partial': path.write_bytes(raw + b'{')
            elif mode == 'duplicate-key': path.write_bytes(raw + b'{"event":"x","event":"y"}\n')
            else:
                row = dict(f.rows[-1])
                row['sequence'] = '100' if mode == 'sequence' else '9'
                row['monotonic_ns'] = 1.5 if mode == 'float-clock' else True if mode == 'bool-clock' else '10000'
                path.write_bytes(raw + json.dumps(row).encode() + b'\n')
            with self.subTest(mode=mode), self.assertRaises(ValueError): f.gate.observe()
            self.assertEqual(f.signal_calls, [])

    async def test_manifest_wrong_uuid_request_pid_birth_names_or_mutation_never_opens_event(self):
        for field, value in [('run_id', 'old'), ('request_id', '3'), ('pid', '43'), ('creation_filetime', '101'),
                             ('release_event', 'Local\\other'), ('cancel_event', 'Local\\other'), ('kind', 'copper')]:
            f = self.fixture(); await f.prepare()
            path = f.directory / 'request-2.json'; row = json.loads(path.read_text()); row[field] = value
            path.write_text(json.dumps(row), encoding='utf-8')
            with self.subTest(field=field), self.assertRaises(ValueError): f.gate.observe()
            self.assertEqual(f.open_calls, [])
        f = self.fixture(); await f.prepare(); f.gate.observe()
        path = f.directory / 'request-2.json'; path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaises(ValueError): f.gate.observe()

    async def test_original_process_owner_or_handle_changes_fail_without_rebinding(self):
        for mode in ('pid', 'exited', 'handle', 'owner-birth', 'owner-pid', 'object'):
            f = self.fixture(); await f.prepare()
            if mode == 'pid': f.rig.process.pid = 43
            if mode == 'exited': f.rig.process.returncode = 0
            if mode == 'handle':
                original = f.creator.inspect_created
                f.creator.inspect_created = lambda process: dict(original(process), handle=556)
            if mode == 'owner-birth': f.current['birth'] = 901
            if mode == 'owner-pid': f.current['pid'] = 801
            if mode == 'object': f.creator.process = object()
            with self.subTest(mode=mode), self.assertRaises(ValueError): f.gate.observe()
            self.assertEqual(f.open_calls, [])

    async def test_baseline_must_be_actual_ack_in_same_application_before_trigger(self):
        for mode in ('missing-ack', 'late-ack', 'wrong-app', 'wrong-document'):
            f = self.fixture(); await f.prepare(); rig = f.rig
            # 只在测试夹具构造新的无效候选，不为生产提供恢复接口。
            rig.reviews.consumed.remove('baseline-image')
            baseline = rig.reviews.requests['baseline-image']
            from dataclasses import replace
            if mode == 'missing-ack': rig.reviews.acks.pop('baseline-image')
            if mode == 'late-ack': rig.reviews.acks['baseline-image']['ack_mono_ns'] = f.trigger + 1
            if mode == 'wrong-app': rig.reviews.requests['baseline-image'] = replace(baseline, application_run_id='other')
            if mode == 'wrong-document': rig.reviews.requests['baseline-image'] = replace(baseline, expected=tuple(dict(revision=2, dirty=True, tracks=1, net_sha256='a'*64).items()))
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                with rig.ledger.operation('bad-baseline', rig.ledger.token):
                    GateJournal(f.journal, rig.reviews, baseline_review_id='baseline-image', request_id=2,
                                trigger_mono_ns=f.trigger, a_sha256='a'*64, b_sha256='b'*64, board_sha256='c'*64)
            self.assertEqual(f.signal_calls, [])

    async def test_original_a_acceptance_thread_stage_generation_and_publication_mutations_rejected(self):
        cases = [(4, 'accepted', False), (3, 'result_sha256', 'b'*64), (6, 'thread_id', '11'),
                 (6, 'stage', 'other'), (5, 'generation', True), (5, 'previous_net_sha256', 'b'*64)]
        for index, field, value in cases:
            f = self.fixture()
            # 改写必须在首次绑定/读取之前，避免仅被前缀不变规则提前挡住。
            f.rows[index][field] = value; f.write(5)
            await f.prepare()
            with self.subTest(field=field), self.assertRaises(ValueError): f.gate.observe()
        for field, value in [('dirty', False), ('tracks', '1'), ('revision', '2'), ('net_sha256', 'b'*64)]:
            f = self.fixture(); await f.prepare(); f.rows[8][field] = value; f.write(9)
            with self.subTest(field=field), self.assertRaises(ValueError): f.gate.observe()

    async def test_cancelled_discard_is_aborted_and_never_valid_release(self):
        for kind in ('net', 'copper'):
            f = self.fixture(kind); await f.prepare(); await f.edit()
            f.rows[9]['event'] = 'aborted'
            f.rows[-1]['experiment_aborted'] = True
            f.write(len(f.rows))
            state = f.gate.observe()
            self.assertTrue(state.aborted)
            self.assertFalse(state.original_discard_decision)
            self.assertEqual(state.released_ns, 0)
            self.assertTrue(await f.race.cleanup_ready())
            with self.assertRaises(ValueError): await f.race.release('release', f.rig.ledger.token)
            self.assertEqual(f.signal_calls, [])

    async def test_set_event_return_alone_times_out_in_original_one_second_chunks(self):
        f = self.fixture(); await f.prepare(); await f.edit()
        f.signal_action = lambda: None
        saved = f.gate.deadline_ns
        with self.assertRaises(ValueError): await f.race.release('release', f.rig.ledger.token)
        self.assertEqual(f.signal_calls, ['release'])
        self.assertTrue(f.releaser.signal_returned)
        self.assertFalse(f.releaser.confirmed)
        self.assertFalse(f.race.release_returned)
        self.assertTrue(f.pause_calls and max(f.pause_calls) <= 1)
        self.assertEqual(f.gate.deadline_ns, saved)
        self.assertEqual(f.close_calls, ['cancel', 'release'])
        f.rig.clock.tick(121)
        with self.assertRaises(ValueError): await f.race.release('retry', f.rig.ledger.token)
        self.assertEqual(len(f.signal_calls), 1)

    async def test_signal_unknown_cancelled_or_already_signaled_cannot_retry(self):
        for mode in ('signal-unknown', 'cancel-set', 'release-set', 'open-second', 'aborted-after-signal'):
            f = self.fixture(); await f.prepare(); await f.edit()
            if mode == 'signal-unknown': f.signal_error = ConnectionError('SetEvent结果未知')
            if mode == 'cancel-set': f.event_state['cancel'] = True
            if mode == 'release-set': f.event_state['release'] = True
            if mode == 'open-second': f.open_error = 2
            if mode == 'aborted-after-signal':
                def abort():
                    f.rows[9]['event'] = 'aborted'; f.rows[-1]['experiment_aborted'] = True
                    f.write(len(f.rows))
                f.signal_action = abort
            with self.subTest(mode=mode), self.assertRaises((ValueError, ConnectionError)):
                await f.race.release('release', f.rig.ledger.token)
            self.assertLessEqual(len(f.signal_calls), 1)
            self.assertFalse(f.releaser.confirmed)
            self.assertTrue(f.releaser.used)
            self.assertEqual(f.releaser.handles, [])

    async def test_disabled_missing_review_expired_or_wrong_request_do_not_open_or_signal(self):
        for mode in ('disabled', 'missing-read', 'expired', 'wrong-id', 'no-race-attempt'):
            f = self.fixture(); await f.prepare(); await f.edit(); rig = f.rig
            if mode == 'disabled': f.releaser.enabled = False
            if mode == 'missing-read': rig.reviews.consumed.remove(f.race.gate_review)
            if mode == 'expired': rig.clock.tick(60)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                if mode in ('wrong-id', 'no-race-attempt'):
                    with rig.ledger.operation('direct', rig.ledger.token): await f.releaser(99 if mode == 'wrong-id' else 2)
                else: await f.race.release('release', rig.ledger.token)
            self.assertEqual((f.open_calls, f.signal_calls), ([], []))

    async def test_original_callback_wrong_discard_decision_and_result_digest_do_not_settle(self):
        for kind, field, value in [('net', 'captured_generation', '99'), ('net', 'current_generation', '4'),
                                   ('net', 'revision', '2'), ('copper', 'net_matches', False),
                                   ('copper', 'board_matches', True), ('copper', 'current_revision', '2')]:
            f = self.fixture(kind); await f.prepare(); await f.edit()
            f.rows[-1][field] = value
            with self.subTest(kind=kind, field=field), self.assertRaises(ValueError):
                await f.race.release('release', f.rig.ledger.token)
            self.assertFalse(f.race.settled)
            self.assertEqual(len(f.signal_calls), 1)

    async def test_review_verification_and_persistence_cost_cannot_cross_t1_silently(self):
        for mode in ('verify', 'publish'):
            f = self.fixture(); await f.prepare(); rig = f.rig
            rid = await f.race.capture_gate('gate-shot', rig.ledger.token)
            args = rig.read(rid)
            if mode == 'verify':
                original = rig.verifier.verify
                def verify(*values):
                    proof = original(*values); rig.clock.tick(21); return proof
                rig.verifier.verify = verify
            else:
                original = rig.reviews.publish_ack
                def publish(*values): original(*values); rig.clock.tick(21)
                rig.reviews.publish_ack = publish
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                await f.race.ack('gate-ack', rig.ledger.token, review_id=rid, **args)
            self.assertNotIn(rid, rig.reviews.acks)
            self.assertEqual(f.signal_calls, [])
            self.assertEqual(f.race.stage, 'gate-requested')

    async def test_original_result_digest_and_handle_cleanup_errors_do_not_return_success(self):
        for mode in ('net-result', 'copper-limit', 'close-failure'):
            f = self.fixture('copper' if mode == 'copper-limit' else 'net')
            await f.prepare(); await f.edit()
            if mode == 'net-result': f.rows[-2]['result_sha256'] = 'a' * 64
            if mode == 'copper-limit': f.rows[-2]['limit_reached'] = True
            if mode == 'close-failure':
                original = f.api.close
                def close(handle):
                    original(handle)
                    if handle == 'cancel': raise ValueError('句柄清理未知')
                f.api.close = close
            with self.subTest(mode=mode), self.assertRaises((ValueError, RuntimeError)):
                await f.race.release('release', f.rig.ledger.token)
            self.assertFalse(f.race.release_returned)
            self.assertFalse(f.race.settled)
            self.assertEqual(len(f.signal_calls), 1)
            self.assertEqual(f.releaser.handles, [])
            if mode == 'close-failure':
                self.assertFalse(f.releaser.confirmed)
                self.assertFalse(f.releaser.returned)
                self.assertEqual(f.close_calls, ['cancel', 'release'])

    def test_default_event_api_import_does_not_load_kernel_or_create_events(self):
        api = ExistingEventApi()
        self.assertIsNone(api.kernel)
        self.assertFalse(hasattr(api, 'create_event'))
        self.assertFalse(hasattr(api, 'reset_event'))


if __name__ == '__main__': unittest.main(verbosity=2)
