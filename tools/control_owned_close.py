"""精确自建诊断窗的一次正常关闭；默认禁用，导入不访问桌面。"""
from __future__ import annotations

import asyncio
import re

TITLE = 'PT Renew 控制诊断试验'


async def wait_owned_process(process, seconds):
    # Windows Popen.wait使用创建时持有的原进程句柄，不按PID重新查找。
    return await asyncio.to_thread(process.wait, timeout=seconds)


class OwnedDiagnosticClose:
    """只能由创建窗口的客户端登记原Popen，不能从请求中接收PID或窗口身份。"""

    def __init__(self, *, enabled=False, cleanup_deadline, waiter=wait_owned_process):
        self.enabled = enabled is True
        self.cleanup_deadline = cleanup_deadline
        self.waiter = waiter
        self.process = None
        self.identity = None
        self.used = False
        self.attempted = False
        self.returned = False
        self.confirmed = False
        self.wait_seconds = 5.0
        self.tool_margin_seconds = 35.0
        self.stop_margin_seconds = 40.0

    def bind_created(self, process, *, birth, image):
        if self.process is not None or self.used or process.poll() is not None:
            raise ValueError('只能登记本轮客户端刚创建且仍存活的唯一原Popen')
        if type(process.pid) is not int or process.pid <= 0 or type(birth) is not int or birth <= 0 or not image:
            raise ValueError('自建Popen身份不完整')
        self.process = process
        self.identity = dict(pid=process.pid, birth=birth, image=image)

    async def run(self, guard, ident, parent, *, stage_ready=False, pending=False):
        rejected = dict(completed=False, executed=False, tool_call_sent=False)
        queued = pending if callable(pending) else lambda: pending
        if (not self.enabled or self.used or queued() or not stage_ready
                or guard.busy or guard.failed or not isinstance(ident, str)
                or re.fullmatch(r'[a-zA-Z0-9_-]+', ident) is None or ident in guard.seen
                or parent != guard.token or self.process is None or not guard.target
                or not getattr(guard, 'expected_hwnd', None)):
            return dict(rejected, reason='关闭未启用、机会已消费或当前ID/token/阶段/所有权不允许')
        # 过期请求不访问Popen、原生桌面或工具，也不改变原截止。
        now = guard.clock.monotonic()
        required = self.tool_margin_seconds + self.wait_seconds + self.stop_margin_seconds
        if now < guard.not_before or now + required >= self.cleanup_deadline:
            return dict(rejected, reason='冷却未满或收尾不足35秒工具余量、5秒退出等待及40秒停止余量')
        self.used = True
        guard.seen.add(ident)
        guard.busy = True
        phase = 'preflight'
        exit_code = None
        guard.event('owned_close_request', id=ident, parent=parent, identity=self.identity,
                    cleanup_deadline=self.cleanup_deadline)
        try:
            owned = self.identity
            if (self.process.pid != owned['pid'] or self.process.poll() is not None
                    or guard.target != dict(pid=owned['pid'], image=owned['image'])
                    or guard.expected_birth != owned['birth']):
                raise ValueError('原Popen已退出或绑定PID/创建时间/映像改变')
            guard.require_arguments('Shortcut', dict(shortcut='alt+f4'))
            native = await guard.gate()
            matches = [w for w in native.get('windows', []) if w.get('title') == TITLE]
            expected = dict(owned, hwnd=guard.expected_hwnd, title=TITLE, cls='TkTopLevel')
            for window in matches + [native.get('foreground', {})]:
                if any(window.get(k) != v for k, v in expected.items() if k != 'image') or window.get('image', '').casefold() != owned['image'].casefold():
                    raise ValueError('关闭前PID/创建时间/映像/HWND/标题/类或前景不符')
            if len(matches) != 1 or self.process.poll() is not None:
                raise ValueError('关闭前目标不唯一或原Popen已经退出')
            guard.cool_check()
            if guard.clock.monotonic() + required >= self.cleanup_deadline or queued():
                raise ValueError('前置核验后剩余收尾时间不足或出现排队请求')
            phase = 'tool'
            self.attempted = True
            guard.event('owned_close_tool_start', id=ident, tool='Shortcut', arguments=dict(shortcut='alt+f4'))
            try:
                receipt = await guard.raw('Shortcut', dict(shortcut='alt+f4'))
                self.returned = True
                if (not isinstance(receipt, dict) or receipt.get('tool') != 'Shortcut'
                        or receipt.get('arguments') != dict(shortcut='alt+f4')
                        or receipt.get('is_error') is not False
                        or receipt.get('text') != ['Pressed alt+f4.']):
                    raise ValueError('原Shortcut回执缺失、错误或与冻结协议不符，执行结果未知')
                self.confirmed = True
            finally:
                guard.event('owned_close_tool_end', id=ident, returned=self.returned)
            phase = 'wait_exit'
            exit_code = await self.waiter(self.process, self.wait_seconds)
            guard.event('owned_close_exit', id=ident, pid=owned['pid'], birth=owned['birth'],
                        exit_code=exit_code, original_popen=True)
            if (type(exit_code) is not int or exit_code != 0 or self.process.returncode != exit_code
                    or self.process.pid != owned['pid']):
                raise ValueError('原Popen退出码非0或退出证据不一致')
            # 成功关闭后只读原Popen，不再要求已消失窗口保持前景。
            # retire为同步操作；在此释放busy以沿用原Guard的退役约束。
            phase = 'retire'
            guard.busy = False
            guard.retire(owned['pid'], exit_code)
            guard.token = ident
            result = dict(completed=True, executed=True, tool_call_sent=True, retired=True,
                          pid=owned['pid'], birth=owned['birth'], exit_code=exit_code, token=ident)
        except (Exception, asyncio.CancelledError) as error:
            guard.failed = ident
            guard.diagnosis = None
            if guard.not_before <= guard.clock.monotonic():
                try:
                    guard.retreat('专用关闭失败：' + type(error).__name__ + ': ' + str(error))
                except Exception:
                    pass
            result = dict(completed=False, executed=True if self.confirmed else 'unknown' if self.attempted else False,
                          tool_call_sent=self.attempted, returned=self.returned, retired=False,
                          reason=type(error).__name__ + ': ' + str(error), phase=phase,
                          failed_id=ident, not_before_monotonic=guard.not_before, exit_code=exit_code)
        finally:
            guard.busy = False
        guard.event('owned_close_complete', id=ident, result=result)
        return result
