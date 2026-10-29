"""产品客户端实质契约测试；假Popen/API/时钟，无Qt、输入钩子或现场进程。"""
import asyncio
import base64
import copy
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from async_product_client.core import Context, Identity, Ledger, SECOND, digest, bounded_local_wait
from async_product_client.review import PiReadVerifier, ReviewGate, Snapshot
from async_product_client.product import ProductOwner, ProductIO, WindowPolicy, QT_CLASS, MODAL_TITLE, tree_hashes
from async_product_client.race import GateState, RaceClient
from async_product_client.close import ProductClose
from async_product_client.store import ReviewStore


class Clock:
    def __init__(self):
        self.now = 10 * SECOND
        self.wall = 1_800_000_000 * SECOND

    def monotonic_ns(self):
        return self.now

    def wall_ns(self):
        return self.wall

    def tick(self, seconds=.01):
        self.now += round(seconds * SECOND)
        self.wall += round(seconds * SECOND)


class Process:
    def __init__(self):
        self.pid = 42
        self.returncode = None

    def poll(self):
        return self.returncode


def stamp(ns):
    return datetime.fromtimestamp(ns / SECOND, timezone.utc).isoformat(timespec='microseconds')


class Rig:
    def __init__(self, root, *, enabled=True, kind='net'):
        self.root = Path(root)
        self.clock = Clock()
        self.ledger = Ledger(context=Context('new-task', 'new-dispatch', 'new-run', 'new-session'),
                             cleanup_deadline_ns=1000 * SECOND, clock=self.clock, enabled=enabled)
        self.process = Process()
        self.owner = ProductOwner(self.ledger)
        self.deployment = self.root / 'deployment'
        self.deployment.mkdir()
        for name in ['pt-renew.exe'] + [f'lib{i}.dll' for i in range(21)]:
            (self.deployment / name).write_bytes(name.encode())
        self.manifest = tree_hashes(self.deployment)
        self.board = self.root / 'board.pcb'
        self.board.write_bytes(b'new-copy')
        self.inputs = {str(self.board): digest(self.board.read_bytes())}
        self.create_calls = []
        self.inspect_error = None
        self.wait_error = None
        self.wait_code = 0
        self.waited_process = None
        self.native_calls = 0
        self.calls = []
        self.shots = 0
        self.dirty = False
        self.modal = False
        self.disappear = False
        self.native_mutation = lambda row: row
        self.transport_error = None
        self.transport_result = None
        self.release_error = None
        self.release_calls = 0
        self.focus = 'canvas'
        self.policy = WindowPolicy('board.pcb')
        self.state = GateState('new-run', 42, 7, kind, 1, 1 * SECOND, 2 * SECOND,
                               62 * SECOND, 3 * SECOND, 'waiting', 2, False, 1, 'a' * 64)
        self.journal = self.root / 'session.jsonl'
        self.rows = [dict(type='session', id='new-session')]
        self.flush()
        self.verifier = PiReadVerifier(self.journal)
        self.io = ProductIO(self.ledger, self.owner, self.policy, native=self.native,
                            transport=self.transport, snapshot=self.snapshot)
        self.reviews = None
        self.race = None
        self.close = None

    def factory(self, argv, **kwargs):
        self.create_calls.append((argv, kwargs))
        return self.process

    def inspect(self, process):
        if self.inspect_error:
            raise self.inspect_error
        return dict(pid=process.pid, birth=100, handle=555, original_handle=True,
                    image=str((self.deployment / 'pt-renew.exe').resolve()))

    def launch(self):
        with self.ledger.operation('launch', self.ledger.token):
            self.owner.launch(deployment=self.deployment, manifest=self.manifest, inputs=self.inputs,
                              environment={'PATH': 'frozen-path'}, factory=self.factory,
                              inspect_created=self.inspect)
            self.owner.bind_main(99)
        self.store = ReviewStore(self.root / 'evidence')
        self.reviews = ReviewGate(self.ledger, self.owner.identity, self.verifier,
                                  publish=self.store.request, publish_ack=self.store.ack)
        self.race = RaceClient(self.ledger, self.io, self.reviews, gate_api=self.gate,
                               release_api=self.release, kind=self.state.kind, request_id=7,
                               trigger_mono_ns=self.clock.now, a_sha256='a' * 64, revision=2)
        self.close = ProductClose(self.ledger, self.io, self.reviews, cleanup_ready=self.race.cleanup_ready,
                                  request_id=7, waiter=self.waiter)

    def main_window(self):
        return dict(pid=42, birth=100, image=self.owner.identity.image, hwnd=99, owner=0,
                    cls=QT_CLASS, title=self.policy.title(self.dirty), rect=[0, 0, 1000, 800],
                    coordinate_space='physical-desktop-pixels', thread_context_restored=True,
                    focus_kind=self.focus)

    def modal_window(self):
        row = self.main_window()
        row.update(hwnd=101, owner=99, modal=True, title=MODAL_TITLE, default_button='取消',
                   rect=[200, 200, 800, 600], buttons={'放弃更改': [250, 450, 400, 500], '取消': [600, 450, 750, 500]})
        return row

    async def native(self):
        self.native_calls += 1
        if self.disappear:
            row = dict(windows=[], foreground={}, input_desktop='Default', locked=False, foreground_stable=True)
        else:
            windows = [self.main_window()]
            if self.modal:
                windows.append(self.modal_window())
            row = dict(windows=windows, foreground=copy.deepcopy(windows[-1]), input_desktop='Default',
                       locked=False, foreground_stable=True)
        return self.native_mutation(row)

    async def transport(self, tool, arguments):
        self.calls.append((tool, copy.deepcopy(arguments)))
        if tool == 'Shortcut' and arguments['shortcut'] == 'delete':
            self.dirty = True
            self.state = replace(self.state, revision=3, dirty=True, tracks=0, published_ns=4 * SECOND,
                                 sampled_app_ns=5 * SECOND, sequence=2)
        if tool == 'Shortcut' and arguments['shortcut'] == 'alt+f4':
            self.modal = self.dirty
            self.disappear = not self.dirty
        if tool == 'Click' and self.modal:
            if arguments['loc'][0] < 500:
                self.disappear = True
            else:
                self.modal = False
        if self.transport_error:
            raise self.transport_error
        if self.transport_result is not None:
            return self.transport_result
        text = ('Pressed ' + arguments['shortcut'] + '.' if tool == 'Shortcut' else
                f"Single left clicked at ({arguments['loc'][0]},{arguments['loc'][1]}).")
        return dict(tool=tool, arguments=arguments, is_error=False, text=[text])

    async def snapshot(self, target):
        self.shots += 1
        image = self.root / f'image-{self.shots}.png'
        image.write_bytes(f'本测试图像{self.shots}'.encode())
        start = self.clock.wall_ns()
        self.clock.tick()
        rect = target['rect']
        return Snapshot(str(image), digest(image.read_bytes()), f'snapshot-{self.shots}', start,
                        self.clock.wall_ns(), rect[2] - rect[0], rect[3] - rect[1], tuple(rect), (1., 1.), target['hwnd'],
                        dict(tool='Snapshot', is_error=False,
                             images=[dict(mimeType='image/png', data=base64.b64encode(image.read_bytes()).decode())]))

    async def gate(self):
        return self.state

    async def release(self, request_id):
        self.release_calls += 1
        if self.release_error:
            raise self.release_error
        self.state = replace(self.state, phase='discarded', released_ns=6 * SECOND, returned_ns=7 * SECOND,
                             discarded_ns=8 * SECOND, sampled_app_ns=9 * SECOND, sequence=3,
                             original_discard_decision=True)
        return dict(request_id=request_id, pid=42, run_id='new-run', released=True, aborted=False, app_ns=6 * SECOND)

    async def waiter(self, process, seconds):
        self.waited_process = process
        self.clock.tick(seconds)
        if self.wait_error:
            raise self.wait_error
        process.returncode = self.wait_code
        return self.wait_code

    def flush(self):
        self.journal.write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in self.rows) + '\n', encoding='utf-8')

    def read(self, request_id, *, change=None):
        request = self.reviews.requests[request_id]
        number = len(self.rows)
        call_id, result_id = f'read-{number}', f'result-{number}'
        self.clock.tick()
        assistant = dict(id=f'assistant-{number}', type='message', timestamp=stamp(self.clock.wall_ns()),
                         message=dict(role='assistant', provider='deng', model='gpt-6.1-sol', thinkingLevel='high',
                                      content=[dict(type='toolCall', name='read', id=call_id,
                                                    arguments=dict(path=request.snapshot.path))]))
        self.clock.tick()
        result = dict(id=result_id, type='message', timestamp=stamp(self.clock.wall_ns()),
                      message=dict(role='toolResult', toolName='read', toolCallId=call_id, isError=False,
                                   content=[dict(type='image', mimeType='image/png',
                                                 data=base64.b64encode(Path(request.snapshot.path).read_bytes()).decode())]))
        if change:
            change(assistant, result)
        self.rows.extend([assistant, result])
        self.flush()
        return dict(call_id=call_id, result_id=result_id, judgment=dict(request.expected), summary='已实际读图并逐项核对冻结判据')

    async def gate_read(self):
        rid = await self.race.capture_gate('gate-image', self.ledger.token)
        await self.race.ack('gate-ack', self.ledger.token, review_id=rid, **self.read(rid))

    async def edit_read(self):
        await self.gate_read()
        rid = await self.race.edit('edit', self.ledger.token, image_point=[500, 400])
        await self.race.ack('edit-ack', self.ledger.token, review_id=rid, **self.read(rid))

    async def settled(self):
        await self.edit_read()
        await self.race.release('release', self.ledger.token)
        rid = await self.race.capture_final('final', self.ledger.token)
        await self.race.ack('final-ack', self.ledger.token, review_id=rid, **self.read(rid))


class ProductTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def rig(self, **kwargs):
        root = Path(self.temp.name) / str(len(list(Path(self.temp.name).iterdir())))
        root.mkdir()
        return Rig(root, **kwargs)

    async def assert_halted(self, rig, action, *, inputs=None, release=None):
        token = rig.ledger.token
        with self.assertRaises((ValueError, ConnectionError, subprocess.TimeoutExpired, asyncio.CancelledError)):
            await action()
        self.assertIsNotNone(rig.ledger.failed)
        self.assertEqual(rig.ledger.token, token)
        self.assertGreaterEqual(rig.ledger.not_before_ns, rig.clock.now + 120 * SECOND)
        if inputs is not None:
            self.assertEqual(len(rig.calls), inputs)
        if release is not None:
            self.assertEqual(rig.release_calls, release)

    async def test_net_and_copper_entire_chain_requires_each_read_then_dirty_close(self):
        for kind in ('net', 'copper'):
            with self.subTest(kind=kind):
                rig = self.rig(kind=kind)
                rig.launch()
                await rig.settled()
                self.assertTrue(rig.race.settled)
                self.assertEqual(rig.release_calls, 1)
                self.assertEqual(len(rig.calls), 2)
                rid = await rig.close.start('close', rig.ledger.token, dirty=True)
                args = rig.read(rid)
                rig.close.ack_modal('modal-ack', rig.ledger.token, **args)
                before = rig.native_calls
                await rig.close.choose('discard', rig.ledger.token, choice='放弃更改', image_point=[100, 275])
                self.assertEqual(rig.native_calls - before, 1)
                self.assertIs(rig.waited_process, rig.process)
                self.assertTrue(rig.owner.retired)
                self.assertTrue(rig.close.completed)
                self.assertEqual([x[0] for x in rig.calls], ['Click', 'Shortcut', 'Shortcut', 'Click'])
                self.assertEqual(len(rig.reviews.consumed), 4)
                self.assertIsNone(rig.ledger.failed)
                self.assertEqual(rig.ledger.not_before_ns, 0)

    async def test_disabled_busy_queued_old_token_duplicate_and_cooldown_do_no_desktop_work(self):
        for mode in ('disabled', 'busy', 'queue', 'token', 'duplicate', 'cooldown', 'expired'):
            with self.subTest(mode=mode):
                rig = self.rig()
                rig.launch()
                if mode == 'disabled': rig.ledger.enabled = False
                if mode == 'busy': rig.ledger.busy = True
                if mode == 'queue': rig.ledger.pending = True
                if mode == 'duplicate': rig.ledger.seen.add('gate')
                if mode == 'cooldown': rig.ledger.not_before_ns = 50 * SECOND
                if mode == 'expired': rig.clock.now = 1001 * SECOND
                deadline = rig.ledger.cleanup_deadline_ns
                with self.assertRaises(ValueError):
                    await rig.race.capture_gate('gate', 'old' if mode == 'token' else rig.ledger.token)
                self.assertEqual((rig.native_calls, rig.calls, rig.release_calls), (0, [], 0))
                self.assertEqual(rig.ledger.cleanup_deadline_ns, deadline)
                self.assertIsNone(rig.ledger.failed)

    async def test_snapshot_must_have_current_hash_size_scale_and_bound_hwnd(self):
        for mode in ('hash', 'width', 'scale', 'hwnd', 'rect', 'future'):
            rig = self.rig(); rig.launch()
            original = rig.io.snapshot_api
            async def bad(target):
                shot = await original(target)
                changes = {'hash': dict(sha256='b' * 64), 'width': dict(width=10),
                           'scale': dict(scale=(float('nan'), 1)), 'hwnd': dict(hwnd=100),
                           'rect': dict(physical_rect=(1, 0, 1000, 800)),
                           'future': dict(end_wall_ns=rig.clock.wall_ns() + SECOND)}
                return replace(shot, **changes[mode])
            rig.io.snapshot_api = bad
            await self.assert_halted(rig, lambda: rig.race.capture_gate('gate', rig.ledger.token), inputs=0, release=0)

    async def test_ack_rejects_model_session_path_hash_missing_image_and_reordered_read(self):
        mutations = {
            'model': lambda a, r: a['message'].update(model='other'),
            'thinking': lambda a, r: a['message'].update(thinkingLevel='low'),
            'provider': lambda a, r: a['message'].update(provider='other'),
            'path': lambda a, r: a['message']['content'][0]['arguments'].update(path='old.png'),
            'tool': lambda a, r: a['message']['content'][0].update(name='Snapshot'),
            'error': lambda a, r: r['message'].update(isError=True),
            'missing-image': lambda a, r: r['message'].update(content=[dict(type='text', text='observed=true')]),
            'wrong-image': lambda a, r: r['message']['content'][0].update(data=base64.b64encode(b'old').decode()),
            'prewritten': lambda a, r: a.update(timestamp=stamp(1_700_000_000 * SECOND)),
            'future': lambda a, r: r.update(timestamp=stamp(1_900_000_000 * SECOND)),
        }
        for mode, mutate in mutations.items():
            with self.subTest(mode=mode):
                rig = self.rig(); rig.launch()
                rid = await rig.race.capture_gate('gate', rig.ledger.token)
                args = rig.read(rid, change=mutate)
                await self.assert_halted(rig, lambda: rig.race.ack('ack', rig.ledger.token, review_id=rid, **args),
                                         inputs=0, release=0)
                self.assertNotIn(rid, rig.reviews.acks)
        rig = self.rig(); rig.launch()
        rid = await rig.race.capture_gate('gate', rig.ledger.token)
        args = rig.read(rid)
        rig.rows[0]['id'] = 'old-session'; rig.flush()
        await self.assert_halted(rig, lambda: rig.race.ack('ack', rig.ledger.token, review_id=rid, **args), inputs=0)

    async def test_ack_content_and_changed_image_cannot_be_replaced_by_observed_boolean(self):
        for mode in ('observed', 'summary', 'file-changed', 'duplicate-record'):
            rig = self.rig(); rig.launch()
            rid = await rig.race.capture_gate('gate', rig.ledger.token)
            args = rig.read(rid)
            if mode == 'observed': args['judgment'] = dict(observed=True)
            if mode == 'summary': args['summary'] = ''
            if mode == 'file-changed': Path(rig.reviews.requests[rid].snapshot.path).write_bytes(b'changed')
            if mode == 'duplicate-record': rig.rows.append(rig.rows[-1]); rig.flush()
            await self.assert_halted(rig, lambda: rig.race.ack('ack', rig.ledger.token, review_id=rid, **args), inputs=0)

    async def test_gate_aborted_returned_wrong_run_request_or_clock_prevents_ack_and_release(self):
        mutations = [dict(aborted=True), dict(phase='returned', returned_ns=4 * SECOND),
                     dict(run_id='old-run'), dict(pid=43), dict(request_id=8), dict(kind='copper'),
                     dict(deadline_ns=63 * SECOND), dict(sampled_app_ns=63 * SECOND),
                     dict(sequence=0), dict(ready_ns=0)]
        for changes in mutations:
            with self.subTest(changes=changes):
                rig = self.rig(); rig.launch()
                rid = await rig.race.capture_gate('gate', rig.ledger.token)
                args = rig.read(rid)
                rig.state = replace(rig.state, **changes)
                await self.assert_halted(rig, lambda: rig.race.ack('ack', rig.ledger.token, review_id=rid, **args),
                                         inputs=0, release=0)

    async def test_request_clock_never_restarts_sixty_seconds_and_release_reserves_five_seconds(self):
        for mode in ('late-request', 'late-ack', 'release-margin'):
            rig = self.rig(); rig.launch()
            original_deadline = rig.race.deadline
            if mode == 'late-request':
                rig.clock.tick(60)
                await self.assert_halted(rig, lambda: rig.race.capture_gate('gate', rig.ledger.token), inputs=0)
            elif mode == 'late-ack':
                rid = await rig.race.capture_gate('gate', rig.ledger.token)
                args = rig.read(rid); rig.clock.tick(60)
                await self.assert_halted(rig, lambda: rig.race.ack('ack', rig.ledger.token, review_id=rid, **args), inputs=0)
            else:
                await rig.edit_read()
                rig.clock.tick(56)
                await self.assert_halted(rig, lambda: rig.race.release('release', rig.ledger.token), release=0)
            self.assertEqual(rig.race.deadline, original_deadline)

    async def test_edit_before_read_release_before_edit_and_duplicate_read_never_send_inputs(self):
        for mode in ('edit', 'release', 'double-ack'):
            rig = self.rig(); rig.launch()
            rid = await rig.race.capture_gate('gate', rig.ledger.token)
            if mode == 'edit':
                action = lambda: rig.race.edit('edit', rig.ledger.token, image_point=[500, 400])
            elif mode == 'release':
                action = lambda: rig.race.release('release', rig.ledger.token)
            else:
                args = rig.read(rid)
                await rig.race.ack('ack', rig.ledger.token, review_id=rid, **args)
                action = lambda: rig.race.ack('ack-again', rig.ledger.token, review_id=rid, **args)
            await self.assert_halted(rig, action, inputs=0, release=0)

    async def test_ordinary_selection_and_delete_require_post_native_and_canvas_focus(self):
        for mode in ('text', 'lost-post', 'queue-after-native'):
            rig = self.rig(); rig.launch(); await rig.gate_read()
            before = rig.native_calls
            if mode == 'text': rig.focus = 'text'
            if mode == 'lost-post':
                def mutate(row):
                    if rig.native_calls > before + 1: row['foreground'] = {}
                    return row
                rig.native_mutation = mutate
            if mode == 'queue-after-native':
                def mutate(row):
                    rig.ledger.pending = True
                    return row
                rig.native_mutation = mutate
            await self.assert_halted(rig, lambda: rig.race.edit('edit', rig.ledger.token, image_point=[500, 400]),
                                     inputs=0 if mode == 'queue-after-native' else 1, release=0)
            self.assertNotIn(('Shortcut', dict(shortcut='delete')), rig.calls)

    async def test_wrong_identity_owner_title_class_and_same_class_modal_cannot_reach_input(self):
        changes = [('pid', 43), ('birth', 101), ('image', 'other.exe'), ('hwnd', 98),
                   ('owner', 50), ('title', 'board.pcb extra · 工作副本 · 不支持保存 · PT Renew'), ('cls', 'TkTopLevel')]
        for key, value in changes:
            rig = self.rig(); rig.launch()
            def mutate(row):
                row['windows'][0][key] = value
                row['foreground'] = copy.deepcopy(row['windows'][0])
                return row
            rig.native_mutation = mutate
            await self.assert_halted(rig, lambda: rig.race.capture_gate('gate', rig.ledger.token), inputs=0)
        rig = self.rig(); rig.launch(); rig.modal = True
        await self.assert_halted(rig, lambda: rig.race.capture_gate('gate', rig.ledger.token), inputs=0)

    async def test_edited_document_mutations_and_application_rollback_prevent_release(self):
        changes = [dict(revision=2), dict(dirty=False), dict(tracks=1), dict(net_sha256='b' * 64),
                   dict(published_ns=1), dict(sequence=1), dict(sampled_app_ns=2 * SECOND)]
        for change in changes:
            rig = self.rig(); rig.launch(); await rig.edit_read()
            rig.state = replace(rig.state, sequence=3, **{k: v for k, v in change.items() if k != 'sequence'}) if 'sequence' not in change else replace(rig.state, **change)
            await self.assert_halted(rig, lambda: rig.race.release('release', rig.ledger.token), inputs=2, release=0)

    async def test_release_unknown_is_consumed_and_late_success_cannot_clear_failure(self):
        for error in (ConnectionError('传输未知'), asyncio.CancelledError()):
            rig = self.rig(); rig.launch(); await rig.edit_read()
            rig.release_error = error
            await self.assert_halted(rig, lambda: rig.race.release('release', rig.ledger.token), inputs=2, release=1)
            self.assertTrue(rig.race.release_attempted)
            self.assertFalse(rig.race.release_returned)
            deadline = rig.ledger.not_before_ns
            rig.clock.tick(121)
            with self.assertRaises(ValueError): await rig.race.release('again', rig.ledger.token)
            self.assertEqual((rig.release_calls, rig.ledger.not_before_ns), (1, deadline))

    async def test_cancelled_discard_wrong_original_decision_and_event_order_cannot_settle(self):
        for change in (dict(aborted=True), dict(original_discard_decision=False), dict(released_ns=0),
                       dict(returned_ns=5 * SECOND), dict(discarded_ns=6 * SECOND)):
            rig = self.rig(); rig.launch(); await rig.edit_read()
            await rig.race.release('release', rig.ledger.token)
            rig.state = replace(rig.state, sequence=4, **change)
            await self.assert_halted(rig, lambda: rig.race.capture_final('final', rig.ledger.token), inputs=2)
            self.assertFalse(rig.race.settled)

    async def test_original_popen_deployment_inputs_environment_and_constructor_ownership(self):
        for mode in ('deployment', 'extra-file', 'input', 'environment', 'inspect-failure'):
            rig = self.rig()
            if mode == 'deployment': (rig.deployment / 'lib0.dll').write_bytes(b'changed')
            if mode == 'extra-file': (rig.deployment / 'extra').write_bytes(b'changed')
            if mode == 'input': rig.board.write_bytes(b'changed')
            if mode == 'inspect-failure': rig.inspect_error = ValueError('原句柄身份失败')
            with self.assertRaises(ValueError):
                with rig.ledger.operation('launch', 'start'):
                    rig.owner.launch(deployment=rig.deployment, manifest=rig.manifest, inputs=rig.inputs,
                                     environment={'QT_PLUGIN_PATH': 'old'} if mode == 'environment' else {},
                                     factory=rig.factory, inspect_created=rig.inspect)
            self.assertEqual(len(rig.create_calls), 1 if mode == 'inspect-failure' else 0)
            if mode == 'inspect-failure':
                self.assertIs(rig.owner.process, rig.process)
                self.assertTrue(rig.owner.launch_used)
            self.assertEqual(rig.calls, [])

    async def test_clean_close_waits_original_popen_and_never_checks_disappeared_foreground(self):
        rig = self.rig(); rig.launch(); rig.race.settled = True
        await rig.close.start('close', rig.ledger.token, dirty=False)
        self.assertEqual(rig.native_calls, 1)
        self.assertEqual(rig.calls, [('Shortcut', dict(shortcut='alt+f4'))])
        self.assertIs(rig.waited_process, rig.process)
        self.assertTrue(rig.close.completed)
        self.assertTrue(rig.owner.retired)
        with self.assertRaises(ValueError): await rig.close.start('again', rig.ledger.token, dirty=False)
        self.assertEqual(len(rig.calls), 1)

    async def test_dirty_discard_requires_real_read_and_precise_modal_owner_identity(self):
        for mode in ('no-read', 'pid', 'birth', 'image', 'owner', 'title', 'default', 'second-modal'):
            with self.subTest(mode=mode):
                rig = self.rig(); rig.launch(); rig.race.settled = True; rig.dirty = True
                if mode != 'no-read':
                    def mutate(row):
                        if rig.modal:
                            key = {'default': 'default_button'}.get(mode, mode)
                            if mode == 'second-modal': row['windows'].append(dict(row['windows'][-1], hwnd=102))
                            else: row['windows'][-1][key] = {'pid': 43, 'birth': 101, 'owner': 1}.get(mode, 'other')
                            row['foreground'] = copy.deepcopy(row['windows'][-1])
                        return row
                    rig.native_mutation = mutate
                    await self.assert_halted(rig, lambda: rig.close.start('close', rig.ledger.token, dirty=True), inputs=1)
                else:
                    await rig.close.start('close', rig.ledger.token, dirty=True)
                    await self.assert_halted(rig, lambda: rig.close.choose('discard', rig.ledger.token,
                                                                         choice='放弃更改', image_point=[100, 275]), inputs=1)

    async def test_dirty_cancel_is_explicit_input_postchecked_and_not_product_exit(self):
        rig = self.rig(); rig.launch(); rig.race.settled = True; rig.dirty = True
        rid = await rig.close.start('close', rig.ledger.token, dirty=True)
        rig.close.ack_modal('modal-ack', rig.ledger.token, **rig.read(rid))
        before = rig.native_calls
        await rig.close.choose('cancel', rig.ledger.token, choice='取消', image_point=[475, 275])
        self.assertEqual(rig.native_calls - before, 2)
        self.assertEqual(rig.close.stage, 'cancelled')
        self.assertFalse(rig.close.completed)
        self.assertFalse(rig.owner.retired)
        self.assertIsNone(rig.waited_process)
        with self.assertRaises(ValueError): await rig.close.start('again', rig.ledger.token, dirty=True)
        self.assertEqual(len(rig.calls), 2)

    async def test_modal_moved_or_wrong_named_button_prevents_discard(self):
        for mode in ('moved', 'wrong-button'):
            rig = self.rig(); rig.launch(); rig.race.settled = True; rig.dirty = True
            rid = await rig.close.start('close', rig.ledger.token, dirty=True)
            rig.close.ack_modal('modal-ack', rig.ledger.token, **rig.read(rid))
            if mode == 'moved':
                def mutate(row):
                    row['windows'][-1]['rect'][0] += 10
                    row['foreground'] = copy.deepcopy(row['windows'][-1])
                    return row
                rig.native_mutation = mutate
            await self.assert_halted(rig, lambda: rig.close.choose('discard', rig.ledger.token, choice='放弃更改',
                                                                 image_point=[475, 275] if mode == 'wrong-button' else [100, 275]), inputs=1)

    async def test_close_tool_error_timeout_nonzero_and_later_exit_never_rewrite_success(self):
        for mode in ('tool-error', 'unknown', 'cancelled', 'timeout', 'nonzero'):
            rig = self.rig(); rig.launch(); rig.race.settled = True
            if mode == 'tool-error': rig.transport_result = dict(is_error=True, text=['工具拒绝'])
            if mode == 'unknown': rig.transport_error = ConnectionError('传输未知')
            if mode == 'cancelled': rig.transport_error = asyncio.CancelledError()
            if mode == 'timeout': rig.wait_error = subprocess.TimeoutExpired('假进程', 5)
            if mode == 'nonzero': rig.wait_code = 1
            await self.assert_halted(rig, lambda: rig.close.start('close', rig.ledger.token, dirty=False), inputs=1)
            self.assertFalse(rig.close.completed)
            failure = rig.ledger.failed, rig.ledger.not_before_ns, rig.ledger.token
            if mode != 'nonzero':
                rig.wait_error = None
                await rig.close.reap_after_failure()
                self.assertTrue(rig.owner.retired)
            self.assertEqual((rig.ledger.failed, rig.ledger.not_before_ns, rig.ledger.token), failure)
            before = rig.native_calls
            with self.assertRaises(ValueError): await rig.close.start('retry', rig.ledger.token, dirty=False)
            self.assertEqual((rig.native_calls, len(rig.calls)), (before, 1))

    async def test_aborted_worker_must_return_before_normal_cleanup(self):
        rig = self.rig(); rig.launch()
        rig.state = replace(rig.state, aborted=True, phase='aborted', sequence=2)
        self.assertFalse(await rig.race.cleanup_ready())
        await self.assert_halted(rig, lambda: rig.close.start('close', rig.ledger.token, dirty=False), inputs=0)

    async def test_failed_aborted_cleanup_waits_original_120_seconds_and_keeps_failure_token(self):
        rig = self.rig(); rig.launch()
        await self.assert_halted(rig, lambda: rig.race.release('bad-release', rig.ledger.token), inputs=0)
        rig.state = replace(rig.state, aborted=True, phase='returned', returned_ns=4 * SECOND,
                            sampled_app_ns=5 * SECOND, sequence=2)
        saved = rig.ledger.failed, rig.ledger.not_before_ns, rig.ledger.token, rig.ledger.cleanup_deadline_ns
        with self.assertRaises(ValueError): await rig.close.start('close-too-soon', rig.ledger.token, dirty=False)
        self.assertEqual(rig.native_calls, 0)
        rig.clock.tick(120)
        await rig.close.start('close', rig.ledger.token, dirty=False)
        self.assertFalse(rig.close.completed)
        self.assertTrue(rig.owner.retired)
        self.assertEqual((rig.ledger.failed, rig.ledger.not_before_ns, rig.ledger.token, rig.ledger.cleanup_deadline_ns), saved)

    async def test_t1_t2_thresholds_clock_jump_and_malformed_snapshot_receipts(self):
        for mode in ('t1', 't2', 'wall-jump', 'snapshot-error', 'snapshot-no-image'):
            with self.subTest(mode=mode):
                rig = self.rig(); rig.launch()
                if mode.startswith('snapshot'):
                    original = rig.io.snapshot_api
                    async def snapshot(target):
                        row = await original(target)
                        return replace(row, receipt=dict(tool='Snapshot', is_error=mode == 'snapshot-error', images=[]))
                    rig.io.snapshot_api = snapshot
                    action = lambda: rig.race.capture_gate('gate', rig.ledger.token)
                else:
                    if mode == 't2':
                        await rig.gate_read()
                        rid = await rig.race.edit('edit', rig.ledger.token, image_point=[500, 400])
                    else:
                        rid = await rig.race.capture_gate('gate', rig.ledger.token)
                    args = rig.read(rid)
                    if mode == 'wall-jump': rig.clock.wall += 2 * SECOND
                    else: rig.clock.tick(51 if mode == 't2' else 21)
                    action = lambda: rig.race.ack('ack-late', rig.ledger.token, review_id=rid, **args)
                await self.assert_halted(rig, action, release=0)

    async def test_duplicate_hash_reused_read_wrong_stage_and_store_overwrite_are_rejected(self):
        for mode in ('hash', 'read', 'stage', 'request-write', 'ack-write'):
            with self.subTest(mode=mode):
                rig = self.rig(); rig.launch(); await rig.gate_read()
                first = rig.reviews.requests[rig.race.gate_review]
                if mode == 'hash':
                    original = rig.io.snapshot_api
                    async def shot(target):
                        row = await original(target)
                        return replace(row, path=first.snapshot.path, sha256=first.snapshot.sha256,
                                       receipt=first.snapshot.receipt)
                    rig.io.snapshot_api = shot
                    await self.assert_halted(rig, lambda: rig.race.edit('edit', rig.ledger.token, image_point=[500, 400]), release=0)
                elif mode == 'request-write':
                    with self.assertRaises(FileExistsError): rig.store.request(first)
                    self.assertEqual(json.loads((rig.store.root / 'requests' / (first.id + '.json')).read_text(encoding='utf-8'))['id'], first.id)
                elif mode == 'ack-write':
                    with self.assertRaises(FileExistsError): rig.store.ack(first.id, dict(fake=True))
                else:
                    rid = await rig.race.edit('edit', rig.ledger.token, image_point=[500, 400])
                    args = rig.read(rid)
                    if mode == 'read':
                        args['call_id'] = next(iter(rig.reviews.used_reads))[1]
                    await self.assert_halted(rig, lambda: rig.race.ack('bad-ack', rig.ledger.token,
                                                                     review_id=first.id if mode == 'stage' else rid,
                                                                     **args), release=0)

    async def test_release_malformed_late_and_aborted_receipts_consume_only_one_attempt(self):
        for mode in ('malformed', 'late', 'aborted'):
            rig = self.rig(); rig.launch(); await rig.edit_read()
            async def release(rid):
                rig.release_calls += 1
                if mode == 'late': rig.clock.tick(60)
                return dict(run_id='new-run', pid=42, request_id=rid, released=True,
                            aborted=mode == 'aborted', app_ns=6 * SECOND) if mode != 'malformed' else {}
            rig.race.release_api = release
            await self.assert_halted(rig, lambda: rig.race.release('release', rig.ledger.token), release=1)
            self.assertTrue(rig.race.release_attempted)
            self.assertTrue(rig.race.release_returned)

    async def test_busy_concurrent_request_is_never_queued_or_replayed(self):
        rig = self.rig(); rig.launch()
        entered, release = asyncio.Event(), asyncio.Event()
        original = rig.io.native_api
        async def native():
            entered.set()
            await release.wait()
            return await original()
        rig.io.native_api = native
        first = asyncio.create_task(rig.race.capture_gate('gate', rig.ledger.token))
        await entered.wait()
        try:
            with self.assertRaises(ValueError):
                await rig.race.capture_gate('queued', rig.ledger.token)
        finally:
            release.set()
        await first
        self.assertNotIn('queued', rig.ledger.seen)
        self.assertEqual(rig.shots, 1)
        self.assertEqual(rig.ledger.token, 'gate')

    async def test_local_wait_uses_at_most_one_second_chunks_and_original_deadline(self):
        clock = Clock()
        deadline = clock.now + 3 * SECOND
        chunks = []
        async def waiting(seconds):
            chunks.append(seconds)
            clock.tick(seconds)
            return len(chunks) == 2
        self.assertTrue(await bounded_local_wait(waiting, clock=clock, deadline_ns=deadline, accept=bool))
        self.assertEqual(chunks, [1., 1.])
        with self.assertRaises(ValueError):
            await bounded_local_wait(waiting, clock=clock, deadline_ns=deadline, accept=lambda x: False)
        self.assertEqual(chunks, [1., 1., 1.])
        self.assertEqual(deadline, 13 * SECOND)

    async def test_close_identity_popen_substitution_budget_and_pending_after_wait(self):
        for mode in ('pid', 'exit', 'rebind', 'budget', 'pending-after-wait', 'tool-time'):
            rig = self.rig(); rig.launch(); rig.race.settled = True
            if mode == 'pid': rig.process.pid = 43
            if mode == 'exit': rig.process.returncode = 0
            if mode == 'rebind':
                with self.assertRaises(ValueError): rig.owner.bind_main(100)
                continue
            if mode == 'budget': rig.clock.tick(915)
            if mode == 'pending-after-wait':
                original = rig.close.waiter
                async def waiter(process, seconds):
                    code = await original(process, seconds)
                    rig.ledger.pending = True
                    return code
                rig.close.waiter = waiter
            if mode == 'tool-time':
                original = rig.io.native_api
                async def native():
                    row = await original()
                    rig.clock.tick(915)
                    return row
                rig.io.native_api = native
            await self.assert_halted(rig, lambda: rig.close.start('close', rig.ledger.token, dirty=False),
                                     inputs=1 if mode == 'pending-after-wait' else 0)
            self.assertFalse(rig.close.completed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
