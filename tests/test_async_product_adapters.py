"""MCP/PNG/原Popen适配契约；只用合成数据和假API，不连接服务或启动产品。"""
import base64
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from async_product_client.core import Context, Ledger, SECOND
from async_product_client.transport import McpProductTransport, normalize_result, png_dimensions
from async_product_client.process import OwnedProductProcess, OriginalHandleApi
from async_product_client.product import ProductOwner, tree_hashes


def png(width=4, height=3):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + b'\x44\x55\x66' * width) * height)) + chunk(b'IEND', b''))


class Clock:
    def __init__(self): self.now, self.wall = 10 * SECOND, 1_800_000_000 * SECOND
    def monotonic_ns(self): return self.now
    def wall_ns(self): return self.wall
    def tick(self, seconds=.1):
        self.now += round(seconds * SECOND); self.wall += round(seconds * SECOND)


class Result:
    def __init__(self, value): self.value = value
    def model_dump(self, *, mode):
        assert mode == 'json'
        return copy.deepcopy(self.value)


class Connection:
    def __init__(self, clock):
        self.clock, self.calls, self.error = clock, [], None
        self.image = png()
        self.row = dict(is_error=False, content=[dict(type='text', text='Screenshot Region: (-10,20,30,50)\nCoordinate Space: Virtual desktop coordinates'),
                                                dict(type='image', mime_type='image/png', data=base64.b64encode(self.image).decode())])
    async def call_tool(self, tool, arguments):
        self.calls.append((tool, copy.deepcopy(arguments)))
        self.clock.tick()
        if self.error: raise self.error
        return Result(self.row)


class Process:
    pid = 42
    returncode = None
    def poll(self): return self.returncode


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = Clock()
        self.ledger = Ledger(context=Context('task', 'dispatch', 'run', 'session'), clock=self.clock,
                             cleanup_deadline_ns=1000 * SECOND, enabled=True)
        self.connection = Connection(self.clock)
        self.validations = []

    def adapter(self, **kwargs):
        folder = self.root / str(len(list(self.root.iterdir())))
        return McpProductTransport(self.ledger, self.connection, folder,
                                   validate=lambda tool, args: self.validations.append((tool, args)), **kwargs)

    async def test_original_serialization_snapshot_region_and_png_dimensions_are_bound(self):
        adapter = self.adapter(enabled=True)
        with self.ledger.operation('shot', 'start'):
            shot = await adapter.snapshot(dict(hwnd=99, rect=[-10, 20, 30, 50],
                                               coordinate_space='physical-desktop-pixels', thread_context_restored=True))
        self.assertEqual((shot.width, shot.height, shot.scale), (4, 3, (10., 10.)))
        self.assertEqual(shot.physical_rect, (-10, 20, 30, 50))
        self.assertEqual(Path(shot.path).read_bytes(), self.connection.image)
        self.assertEqual(self.connection.calls, [('Snapshot', dict(use_vision=True, use_annotation=False,
                                                                  use_ui_tree=False, region=[-10, 20, 30, 50]))])
        self.assertEqual(len(self.validations), 1)
        raw = json.loads((adapter.root / '0001-Snapshot-raw.json').read_text(encoding='utf-8'))
        self.assertIn('mime_type', raw['content'][1])
        self.assertIn('mimeType', shot.receipt['images'][0])
        self.assertTrue(adapter.calls[0]['returned'])
        self.assertEqual(self.ledger.not_before_ns, 0)

    async def test_disabled_cooldown_schema_and_expired_budget_send_zero_calls(self):
        for mode in ('disabled', 'cooldown', 'schema', 'deadline', 'unsupported'):
            with self.subTest(mode=mode):
                adapter = self.adapter(enabled=mode != 'disabled')
                if mode == 'cooldown': self.ledger.not_before_ns = 100 * SECOND
                if mode == 'schema':
                    def reject(tool, args): raise ValueError('冻结schema拒绝')
                    adapter.validate = reject
                if mode == 'deadline': self.clock.now = 990 * SECOND
                with self.assertRaises(ValueError):
                    with self.ledger.operation('case-' + mode, self.ledger.token):
                        await adapter('ControlStatus' if mode == 'unsupported' else 'Click', dict(loc=[1, 2]))
                self.assertEqual(self.connection.calls, [])
                # 各子例使用独立账本，避免后续入口继承前一个预期失败。
                self.clock = Clock()
                self.ledger = Ledger(context=Context('task', 'dispatch', 'run', 'session'), clock=self.clock,
                                     cleanup_deadline_ns=1000 * SECOND, enabled=True)
                self.connection = Connection(self.clock)

    async def test_malformed_error_missing_image_wrong_mime_or_text_never_returns_snapshot(self):
        for mode in ('error', 'no-image', 'wrong-mime', 'camel-case', 'text-error', 'png-error', 'two-images'):
            with self.subTest(mode=mode):
                row = {k: v for k, v in self.connection.row.items() if k == 'is_error'}
                row['content'] = [dict(type='text', text='Pressed alt+f4.')]
                if mode == 'error': row['is_error'] = True
                else: row = copy.deepcopy(self.connection.row)
                if mode == 'no-image': row['content'] = row['content'][:1]
                if mode == 'wrong-mime': row['content'][1]['mime_type'] = 'image/jpeg'
                if mode == 'camel-case': row['isError'] = False
                if mode == 'text-error': row['content'][0]['text'] = 'Error capturing desktop state: failed'
                if mode == 'png-error': row['content'][1]['data'] = base64.b64encode(b'fake').decode()
                if mode == 'two-images': row['content'].append(row['content'][1])
                with self.assertRaises(ValueError): normalize_result(row, tool='Snapshot', arguments={})

    async def test_region_mismatch_full_desktop_and_stale_coordinate_space_fail_after_one_snapshot(self):
        for mode in ('region', 'full-desktop', 'space'):
            adapter = self.adapter(enabled=True)
            old = self.connection.row['content'][0]['text']
            self.connection.row['content'][0]['text'] = {
                'region': 'Screenshot Region: (0,0,100,100)\nCoordinate Space: Virtual desktop coordinates',
                'full-desktop': 'Screenshot Size: (1920,1080)',
                'space': 'Screenshot Region: (-10,20,30,50)\nCoordinate Space: logical'}[mode]
            with self.assertRaises(ValueError):
                with self.ledger.operation('shot-' + mode, self.ledger.token):
                    await adapter.snapshot(dict(hwnd=99, rect=[-10, 20, 30, 50], coordinate_space='physical-desktop-pixels',
                                                thread_context_restored=True))
            self.assertEqual(len(adapter.calls), 1)
            self.assertTrue(adapter.calls[0]['returned'])
            self.connection.row['content'][0]['text'] = old
            self.ledger.failed = None  # 仅测试夹具重建，不为生产模块提供恢复接口。
            self.ledger.not_before_ns = 0

    async def test_narrow_transport_blocks_unreviewed_shortcuts_and_nonregion_snapshots(self):
        for tool, args in [('Shortcut', dict(shortcut='enter')), ('Shortcut', dict(shortcut='alt+f4')),
                           ('Click', dict(loc=[1, 2], clicks=2)), ('Snapshot', dict(use_vision=True))]:
            clock = Clock()
            ledger = Ledger(context=Context('task', 'dispatch', 'run', 'session'), clock=clock,
                            cleanup_deadline_ns=1000 * SECOND, enabled=True)
            connection = Connection(clock)
            adapter = McpProductTransport(ledger, connection, self.root / ('narrow-' + str(len(list(self.root.iterdir())))),
                                          enabled=True, validate=lambda *args: None)
            with self.assertRaises(ValueError):
                with ledger.operation('blocked', 'start'):
                    await adapter(tool, args)
            self.assertEqual(connection.calls, [])

    async def test_transport_unknown_preserves_attempt_and_never_retries(self):
        adapter = self.adapter(enabled=True); self.connection.error = ConnectionError('未知')
        with self.assertRaises(ConnectionError):
            with self.ledger.operation('input', 'start'):
                await adapter('Click', dict(loc=[1, 2]))
        self.assertEqual(len(self.connection.calls), 1)
        self.assertFalse(adapter.calls[0]['returned'])
        self.assertEqual(adapter.calls[0]['error'], 'ConnectionError')
        self.assertTrue((adapter.root / '0001-Click-end.json').is_file())
        saved = self.ledger.not_before_ns
        with self.assertRaises(ValueError):
            with self.ledger.operation('retry', 'start'):
                await adapter('Click', dict(loc=[1, 2]))
        self.assertEqual((len(self.connection.calls), self.ledger.not_before_ns), (1, saved))

    async def test_png_crc_dimensions_and_truncated_or_trailing_bytes_are_rejected(self):
        self.assertEqual(png_dimensions(png(2, 3)), (2, 3))
        values = [png()[:-1], png() + b'extra', b'not png', png()[:20] + b'X' + png()[21:]]
        for value in values:
            with self.assertRaises(ValueError): png_dimensions(value)

    def process_rig(self, *, enabled=True, identity_error=False):
        folder = self.root / ('process-' + str(len(list(self.root.iterdir())))); folder.mkdir()
        deploy = folder / 'deployment'; deploy.mkdir()
        for name in ['pt-renew.exe'] + [f'lib{i}' for i in range(21)]: (deploy / name).write_bytes(name.encode())
        board = folder / 'board.pcb'; board.write_bytes(b'new isolated input')
        calls = []
        process = Process()
        def factory(argv, **kwargs): calls.append((argv, kwargs)); return process
        class HandleApi:
            def inspect(self, value):
                if identity_error: raise ValueError('原句柄身份失败')
                return dict(pid=value.pid, birth=100, handle=555, original_handle=True,
                            image=str((deploy / 'pt-renew.exe').resolve()))
        created = OwnedProductProcess(self.ledger, kind='net', experiment_directory=folder / 'app-events', board_copy=board,
                                      evidence_root=folder / 'logs', enabled=enabled, popen=factory, handle_api=HandleApi())
        self.addCleanup(created.close_streams)
        return folder, deploy, board, calls, process, created

    async def test_owned_factory_uses_current_client_owner_and_original_popen_handle(self):
        folder, deploy, board, calls, process, created = self.process_rig()
        owner = ProductOwner(self.ledger)
        import hashlib
        with self.ledger.operation('launch', 'start'):
            owner.launch(deployment=deploy, manifest=tree_hashes(deploy), inputs={str(board): hashlib.sha256(board.read_bytes()).hexdigest()},
                         environment={}, factory=created, inspect_created=created.inspect_created)
            owner.bind_main(99)
        self.assertIs(owner.process, process)
        self.assertIs(created.process, process)
        command, kwargs = calls[0]
        self.assertEqual(command[command.index('--async-experiment-owner') + 1], str(os.getpid()))
        self.assertEqual(command[command.index('--async-experiment-skip') + 1], '1')
        self.assertEqual(command[-1], str(board.resolve()))
        self.assertFalse(kwargs['shell'])
        self.assertTrue(kwargs['close_fds'])
        self.assertEqual(list((folder / 'app-events').iterdir()), [])
        with self.assertRaises(ValueError): created.inspect_created(Process())
        with self.assertRaises(ValueError): created.observe_exit()
        process.returncode = 0
        self.assertEqual(created.observe_exit(), 0)
        self.assertTrue(all(stream.closed for stream in created.streams))

    async def test_identity_failure_keeps_both_original_owners_and_never_relaunches(self):
        folder, deploy, board, calls, process, created = self.process_rig(identity_error=True)
        owner = ProductOwner(self.ledger)
        import hashlib
        with self.assertRaises(ValueError):
            with self.ledger.operation('launch', 'start'):
                owner.launch(deployment=deploy, manifest=tree_hashes(deploy), inputs={str(board): hashlib.sha256(board.read_bytes()).hexdigest()},
                             environment={}, factory=created, inspect_created=created.inspect_created)
        self.assertIs(owner.process, process)
        self.assertIs(created.process, process)
        self.assertTrue(created.used)
        self.assertEqual(len(calls), 1)
        self.assertFalse(all(stream.closed for stream in created.streams))
        process.returncode = 1
        self.assertEqual(created.observe_exit(), 1)
        self.assertEqual(self.ledger.failed, 'launch')

    async def test_disabled_wrong_owner_existing_directory_and_popen_failure_have_no_retry(self):
        for mode in ('disabled', 'owner', 'directory', 'factory-error'):
            folder, deploy, board, calls, process, created = self.process_rig(enabled=mode != 'disabled')
            if mode == 'owner': created.owner_pid = os.getpid() + 1
            if mode == 'directory': created.experiment_directory.mkdir()
            if mode == 'factory-error':
                def fail(*args, **kwargs): raise ValueError('创建失败或未知')
                created.popen = fail
            with self.assertRaises(ValueError):
                with self.ledger.operation('launch-' + mode, self.ledger.token):
                    created([str(deploy / 'pt-renew.exe')], cwd=str(deploy), env={})
            self.assertEqual(calls, [])
            if mode == 'factory-error':
                self.assertTrue(created.used)
                self.assertTrue(all(stream.closed for stream in created.streams))
            self.clock = Clock()
            self.ledger = Ledger(context=Context('task', 'dispatch', 'run', 'session'), clock=self.clock,
                                 cleanup_deadline_ns=1000 * SECOND, enabled=True)

    async def test_normalized_input_reaches_core_strict_receipt_and_keeps_ordinary_postcheck(self):
        from async_product_client.product import ProductIO, WindowPolicy
        from async_product_client.core import Identity
        class Owner:
            identity = Identity(42, 100, 'C:/frozen/pt-renew.exe', 99)
            def alive(self): return None
        owner = Owner()
        adapter = self.adapter(enabled=True)
        policy = WindowPolicy('board.pcb')
        calls = []
        async def native():
            calls.append('native')
            target = dict(pid=42, birth=100, image=owner.identity.image, hwnd=99, owner=0,
                          title=policy.title(False), cls='Qt6120QWindowIcon', rect=[0, 0, 100, 100],
                          coordinate_space='physical-desktop-pixels', thread_context_restored=True)
            return dict(input_desktop='Default', locked=False, foreground_stable=True,
                        windows=[target], foreground=copy.deepcopy(target))
        self.connection.row = dict(is_error=False, content=[dict(type='text', text='Single left clicked at (50,50).')])
        io = ProductIO(self.ledger, owner, policy, native=native, transport=adapter, snapshot=adapter.snapshot)
        with self.ledger.operation('click', 'start'):
            await io.click([50, 50])
        self.assertEqual(calls, ['native', 'native'])
        self.assertEqual(self.connection.calls, [('Click', dict(loc=[50, 50]))])
        self.assertTrue(io.attempts[0]['confirmed'])
        self.assertEqual(self.ledger.token, 'click')

    async def test_tool_deadline_and_wall_jump_reject_returned_receipts_without_retry(self):
        for mode in ('deadline', 'wall'):
            clock = Clock()
            ledger = Ledger(context=Context('task', 'dispatch', 'run', 'session'), clock=clock,
                            cleanup_deadline_ns=1000 * SECOND, enabled=True)
            connection = Connection(clock)
            connection.row = dict(is_error=False, content=[dict(type='text', text='Pressed delete.')])
            original = connection.call_tool
            async def slow(tool, args):
                row = await original(tool, args)
                if mode == 'deadline': clock.tick(35)
                else: clock.wall += 2 * SECOND
                return row
            connection.call_tool = slow
            adapter = McpProductTransport(ledger, connection, self.root / ('time-' + mode), enabled=True,
                                          validate=lambda *args: None)
            with self.assertRaises(ValueError):
                with ledger.operation('input', 'start'):
                    await adapter('Shortcut', dict(shortcut='delete'))
            self.assertEqual(len(connection.calls), 1)
            self.assertTrue(adapter.calls[0]['returned'])
            self.assertTrue((adapter.root / '0001-Shortcut-raw.json').is_file())
            self.assertFalse((adapter.root / '0001-Shortcut-normalized.json').exists())

    async def test_original_handle_queries_the_creation_handle_and_never_opens_a_pid(self):
        import ctypes
        class OriginalProcess(Process):
            _handle = 555
        for mode in ('valid', 'wrong-pid', 'exited', 'image-error'):
            class Kernel:
                def __init__(self): self.handles = []
                def WaitForSingleObject(self, handle, timeout):
                    self.handles.append(handle)
                    return 0 if mode == 'exited' else 258
                def GetProcessId(self, handle):
                    self.handles.append(handle)
                    return 43 if mode == 'wrong-pid' else 42
                def GetProcessTimes(self, handle, a, b, c, d):
                    self.handles.append(handle)
                    a._obj.dwHighDateTime, a._obj.dwLowDateTime = 1, 5
                    return True
                def QueryFullProcessImageNameW(self, handle, flags, buffer, size):
                    self.handles.append(handle)
                    if mode == 'image-error': raise ValueError('映像未知')
                    buffer.value = 'C:/frozen/pt-renew.exe'
                    return True
            kernel = Kernel(); api = OriginalHandleApi(); api.kernel = kernel
            with patch('async_product_client.process.subprocess.Popen', OriginalProcess):
                process = OriginalProcess()
                if mode == 'valid':
                    row = api.inspect(process)
                    self.assertEqual((row['pid'], row['birth'], row['handle']), (42, (1 << 32) | 5, 555))
                    self.assertTrue(row['original_handle'])
                else:
                    with self.assertRaises(ValueError): api.inspect(process)
            self.assertTrue(kernel.handles)
            self.assertEqual(set(kernel.handles), {555})
            self.assertFalse(hasattr(kernel, 'OpenProcess'))

    async def test_import_and_rejected_fake_popen_never_load_kernel_or_access_desktop(self):
        api = OriginalHandleApi()
        self.assertIsNone(api.kernel)
        with self.assertRaises(ValueError): api.inspect(Process())
        self.assertIsNone(api.kernel)


if __name__ == '__main__': unittest.main(verbosity=2)
