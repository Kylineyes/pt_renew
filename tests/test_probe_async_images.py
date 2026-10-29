"""归档读图计时器的假会话测试；不读取产品截图或启动Pi/Qt。"""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from async_product_client.core import Context, SECOND
from probe_async_images import initialize, request, acknowledge, load, preflight


class Clock:
    def __init__(self):
        self.now = 10 * SECOND
        self.wall = 1_800_000_000 * SECOND

    def monotonic_ns(self): return self.now
    def wall_ns(self): return self.wall
    def tick(self, seconds=.01):
        self.now += round(seconds * SECOND)
        self.wall += round(seconds * SECOND)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = self.root / 'evidence'
        self.session = self.root / 'new-session.jsonl'
        self.rows = [dict(type='session', id='new-session')]
        self.flush()
        self.images = []
        for number in (1, 2):
            path = self.root / f'input-{number}.png'
            path.write_bytes(b'\x89PNG\r\n\x1a\n' + bytes([number]))
            self.images.append(str(path))
        self.context = Context('task-new', 'dispatch-new', 'run-new', 'new-session')
        self.clock = Clock()
        initialize(self.evidence, context=self.context, session_file=self.session, images=self.images)

    def flush(self):
        self.session.write_text('\n'.join(json.dumps(x) for x in self.rows) + '\n', encoding='utf-8')

    def read(self, index, mutation=None):
        row = load(self.evidence / f'request-{index}.json')
        self.clock.tick()
        stamp = lambda: datetime.fromtimestamp(self.clock.wall / SECOND, timezone.utc).isoformat()
        assistant = dict(type='message', id=f'assistant-{index}', timestamp=stamp(), message=dict(
            role='assistant', provider='deng', model='gpt-6.1-sol', thinkingLevel='high', content=[dict(
                type='toolCall', id=f'read-{index}', name='read', arguments=dict(path=row['snapshot']['path']))]))
        self.clock.tick()
        result = dict(type='message', id=f'result-{index}', timestamp=stamp(), message=dict(
            role='toolResult', toolCallId=f'read-{index}', toolName='read', isError=False, content=[dict(
                type='image', mimeType='image/png', data=base64.b64encode(Path(row['snapshot']['path']).read_bytes()).decode())]))
        if mutation: mutation(assistant, result)
        self.rows.extend([assistant, result]); self.flush()

    def test_two_strictly_sequential_reads_produce_observation_and_never_live_readiness(self):
        request(self.evidence, 1, clock=self.clock)
        self.read(1)
        self.clock.tick(21)
        first = acknowledge(self.evidence, 1, judgment='合成图A，仅契约测试', clock=self.clock)
        self.assertGreater(first['request_to_ack_seconds'], 20)
        request(self.evidence, 2, clock=self.clock)
        self.read(2)
        acknowledge(self.evidence, 2, judgment='合成图B，仅契约测试', clock=self.clock)
        result = load(self.evidence / 'timing-result.json')
        self.assertFalse(result['observed_t1_under_20'])
        self.assertTrue(result['observed_t2_under_50'])
        self.assertFalse(result['ready_for_live'])
        self.assertFalse(result['gui_verified'])
        self.assertGreaterEqual(result['request_1_to_ack_2_seconds'], first['request_to_ack_seconds'])

    def test_order_duplicate_directory_request_ack_and_input_change_fail_closed(self):
        with self.assertRaises(FileExistsError):
            initialize(self.evidence, context=self.context, session_file=self.session, images=self.images)
        with self.assertRaises(ValueError): request(self.evidence, 2, clock=self.clock)
        row = request(self.evidence, 1, clock=self.clock)
        with self.assertRaises(FileExistsError): request(self.evidence, 1, clock=self.clock)
        self.read(1)
        acknowledge(self.evidence, 1, judgment='合成图A', clock=self.clock)
        with self.assertRaises(ValueError): acknowledge(self.evidence, 1, judgment='重复', clock=self.clock)
        Path(load(self.evidence / 'manifest.json')['images'][1]['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError): request(self.evidence, 2, clock=self.clock)
        self.assertTrue(Path(row['snapshot']['path']).is_file())

    def test_actual_read_missing_image_wrong_model_and_prewritten_receipts_are_not_accepted(self):
        mutations = [lambda a, r: r['message'].update(content=[dict(type='text', text='observed=true')]),
                     lambda a, r: a['message'].update(model='other'),
                     lambda a, r: a.update(timestamp='2000-01-01T00:00:00+00:00')]
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                folder = self.root / f'case-{index}'
                initialize(folder, context=self.context, session_file=self.session, images=self.images)
                request(folder, 1, clock=self.clock)
                saved = self.evidence; self.evidence = folder
                self.rows = self.rows[:1]; self.read(1, mutation)
                with self.assertRaises(ValueError): acknowledge(folder, 1, judgment='不能伪造read', clock=self.clock)
                self.assertFalse((folder / 'ack-1.json').exists())
                self.evidence = saved

    def test_context_image_change_and_wall_jump_never_publish_ack(self):
        request(self.evidence, 1, clock=self.clock); self.read(1)
        self.clock.wall += 2 * SECOND
        with self.assertRaises(ValueError): acknowledge(self.evidence, 1, judgment='时钟变化', clock=self.clock)
        self.clock.wall -= 2 * SECOND
        row = load(self.evidence / 'request-1.json')
        Path(row['snapshot']['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError): acknowledge(self.evidence, 1, judgment='图变了', clock=self.clock)
        self.assertFalse((self.evidence / 'ack-1.json').exists())
        other = self.root / 'other'
        with self.assertRaises(ValueError):
            initialize(other, context=Context('task', 'dispatch', 'run', 'old-session'),
                       session_file=self.session, images=self.images)
        self.assertFalse(other.exists())

    def test_preflight_uses_explicit_utf8_and_nonempty_frozen_manifest(self):
        bundle = self.root / '带中文的新目录'
        frozen = bundle / 'frozen'; frozen.mkdir(parents=True)
        (frozen / '中文.txt').write_text('冻结说明', encoding='utf-8')
        from async_product_client.core import digest
        manifest = dict(files={'中文.txt': digest((frozen / '中文.txt').read_bytes())}, session_file=str(self.session))
        (bundle / 'bundle-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        self.rows.append(dict(type='message', id='actual-assistant', message=dict(role='assistant', provider='deng',
                                                                               model='gpt-6.1-sol', thinkingLevel='high')))
        self.flush()
        result = preflight(bundle, context=self.context, session_file=self.session)
        self.assertEqual((result['frozen_files'], result['assistant_records']), (1, 1))
        self.assertFalse(result['ready_for_live'])
        self.assertTrue(result['all_matched'])
        with self.assertRaises(FileExistsError): preflight(bundle, context=self.context, session_file=self.session)

    def test_preflight_empty_manifest_changed_file_or_wrong_identity_cannot_publish_success(self):
        from async_product_client.core import digest
        for mode in ('empty', 'changed', 'no-assistant', 'wrong-model'):
            bundle = self.root / mode; frozen = bundle / 'frozen'; frozen.mkdir(parents=True)
            path = frozen / 'file.txt'; path.write_bytes(b'original')
            manifest = dict(files={} if mode == 'empty' else {'file.txt': digest(path.read_bytes())}, session_file=str(self.session))
            (bundle / 'bundle-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            if mode == 'changed': path.write_bytes(b'changed')
            self.rows = [self.rows[0]]
            if mode != 'no-assistant':
                self.rows.append(dict(type='message', id='actual', message=dict(role='assistant', provider='deng',
                                    model='other' if mode == 'wrong-model' else 'gpt-6.1-sol', thinkingLevel='high')))
            self.flush()
            with self.assertRaises(ValueError): preflight(bundle, context=self.context, session_file=self.session)
            self.assertFalse((bundle / 'preflight.json').exists())


if __name__ == '__main__': unittest.main(verbosity=2)
