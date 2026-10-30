"""唯一原门闩release：SetEvent只是信号，原gate-released日志才是有效回执。"""
from __future__ import annotations

import asyncio
import os

from .core import SECOND, positive, require


class ExistingEventApi:
    """仅打开原应用已创建的具名事件；不创建、重置或设置cancel。"""

    def __init__(self):
        self.kernel = None

    def load(self):
        if self.kernel is None:
            import ctypes
            from ctypes import wintypes
            require(os.name == 'nt', '原门闩事件仅支持Windows')
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
            kernel.OpenEventW.restype = wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.WaitForSingleObject.restype = wintypes.DWORD
            kernel.SetEvent.argtypes = [wintypes.HANDLE]
            kernel.SetEvent.restype = wintypes.BOOL
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel.CloseHandle.restype = wintypes.BOOL
            self.kernel = kernel
        return self.kernel

    def open_existing(self, name, *, writable):
        import ctypes
        kernel = self.load()
        handle = kernel.OpenEventW(0x100000 | (0x0002 if writable else 0), False, name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def unsignaled(self, handle):
        return self.load().WaitForSingleObject(handle, 0) == 258

    def signal(self, handle):
        require(bool(self.load().SetEvent(handle)), '原SetEvent失败，释放结果未知')

    def close(self, handle):
        require(bool(self.load().CloseHandle(handle)), '原事件句柄释放失败')


async def local_pause(seconds):
    await asyncio.sleep(seconds)


class GateRelease:
    def __init__(self, gate, reviews, *, enabled=False, event_api=None, pause=local_pause,
                 margin_ns=5 * SECOND):
        require(positive(margin_ns) and margin_ns < 60 * SECOND, '原release时限余量无效')
        self.gate, self.reviews = gate, reviews
        self.ledger = gate.ledger
        require(reviews.ledger is self.ledger, 'release读图关口属于其他客户端')
        self.enabled = enabled is True
        self.api, self.pause = event_api or ExistingEventApi(), pause
        self.margin_ns = margin_ns
        self.used = False
        self.attempted = False
        self.returned = False
        self.confirmed = False
        self.signal_returned = False
        self.handles = []

    def require_reviews(self):
        matching = {}
        for ident in self.reviews.consumed:
            request = self.reviews.requests[ident]
            if (request.gate_request_id == self.gate.request_id
                    and request.application_run_id == self.ledger.application_run_id
                    and request.context == self.ledger.context
                    and request.stage in ('gate', 'edit')):
                require(request.stage not in matching, '同一阶段混入多个已消费读图关口')
                require(ident in self.reviews.acks
                        and self.reviews.acks[ident]['ack_mono_ns'] < request.deadline_mono_ns,
                        'release前read/ack原本已超时或缺失')
                matching[request.stage] = request
        require(set(matching) == {'gate', 'edit'}, '唯一release须已有门闩图及编辑图实际read/ack消费证明')
        expected = dict(matching['edit'].expected)
        return expected

    def waiting(self, expected, *, margin_ns):
        self.ledger.desktop_allowed()
        require(not self.ledger.cleanup_active, '失败正常收尾不能发送竞争release')
        state = self.gate.observe()
        require(state.phase == 'waiting' and not state.aborted and not state.released_ns and not state.returned_ns
                and state.published_ns > state.ready_ns and state.dirty is True and state.tracks == 0
                and state.net_sha256 == self.gate.a_sha256
                and dict(revision=state.revision, dirty=state.dirty, tracks=state.tracks, net_sha256=state.net_sha256) == expected
                and self.ledger.clock.monotonic_ns() + margin_ns < self.gate.deadline_ns
                and state.sampled_app_ns + margin_ns < state.deadline_ns,
                '原门闩已经终止、编辑后变化或原时限不足')
        return state

    async def __call__(self, request_id):
        self.ledger.desktop_allowed()
        require(self.enabled and not self.used and request_id == self.gate.request_id, 'release默认禁用、机会已消费或ID错误')
        require(self.ledger.events and self.ledger.events[-1].get('kind') == 'release_attempt'
                and self.ledger.events[-1].get('request_id') == request_id, '必须由竞争状态机唯一release尝试调用')
        expected = self.require_reviews()
        state = self.waiting(expected, margin_ns=self.margin_ns)
        self.used = True
        try:
            manifest = self.gate.manifest
            release = self.api.open_existing(manifest['release_event'], writable=True)
            self.handles.append(release)
            cancel = self.api.open_existing(manifest['cancel_event'], writable=False)
            self.handles.append(cancel)
            require(self.api.unsignaled(cancel) and self.api.unsignaled(release), '原cancel/release事件已置位或状态未知')
            self.waiting(expected, margin_ns=self.margin_ns)
            require(self.api.unsignaled(cancel) and self.api.unsignaled(release), '信号发送前原门闩事件已变化')
            self.attempted = True
            self.ledger.event('gate_signal_attempt', application_run_id=self.ledger.application_run_id,
                              request_id=request_id, event_name=manifest['release_event'])
            self.waiting(expected, margin_ns=self.margin_ns)
            self.api.signal(release)
            self.signal_returned = True
            self.ledger.event('gate_signal_returned', request_id=request_id,
                              meaning='仅SetEvent返回，尚无原gate-released证明')
            while True:
                self.ledger.desktop_allowed()
                require(self.ledger.clock.monotonic_ns() < self.gate.deadline_ns, '原release等待截止已到')
                current = self.gate.observe()
                require(not current.aborted and current.phase != 'accepted', '原应用中止或意外接受，不能记有效释放')
                if current.released_ns:
                    require(state.published_ns < current.released_ns < current.deadline_ns,
                            '原gate-released时间不在有效门闩内')
                    self.confirmed = True
                    self.returned = True
                    return dict(run_id=current.run_id, pid=current.pid, request_id=request_id, released=True,
                                aborted=False, app_ns=current.released_ns, original_app_event=True,
                                trace_sha256=self.gate.last_observation['trace_sha256'])
                require(not current.returned_ns, '工作返回却缺少原gate-released事件')
                remaining = (self.gate.deadline_ns - self.ledger.clock.monotonic_ns()) / SECOND
                require(remaining > .001, '原release剩余不足1毫秒，不再新建等待块')
                seconds = min(.5, remaining / 2)
                require(seconds > 0, '原release等待时限耗尽')
                await asyncio.wait_for(self.pause(seconds), timeout=min(1., remaining))
        finally:
            errors = []
            for handle in reversed(self.handles):
                try: self.api.close(handle)
                except BaseException as error: errors.append(error)
            self.handles.clear()
            if errors:
                self.confirmed = False
                self.returned = False
                raise RuntimeError('原门闩句柄清理失败，不能返回成功') from errors[0]
