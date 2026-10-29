"""不可变运行身份、共享请求账本和时限；导入不访问桌面或创建进程。"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import re
import time

SECOND = 1_000_000_000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def positive(value):
    return type(value) is int and value > 0


def digest(data):
    return hashlib.sha256(data).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


class Clock:
    def monotonic_ns(self):
        return time.monotonic_ns()

    def wall_ns(self):
        return time.time_ns()


@dataclass(frozen=True)
class Context:
    task_id: str
    dispatch_id: str
    run_id: str
    session_id: str
    provider: str = 'deng'
    model: str = 'gpt-6.1-sol'
    thinking: str = 'high'

    def __post_init__(self):
        require(all(isinstance(x, str) and x.strip() for x in
                    (self.task_id, self.dispatch_id, self.run_id, self.session_id)), '本轮上下文不完整')
        require((self.provider, self.model, self.thinking) == ('deng', 'gpt-6.1-sol', 'high'),
                '截图审阅必须使用指定模型和推理强度')


@dataclass(frozen=True)
class Identity:
    pid: int
    birth: int
    image: str
    hwnd: int

    def __post_init__(self):
        require(all(positive(x) for x in (self.pid, self.birth, self.hwnd))
                and isinstance(self.image, str) and bool(self.image), '产品精确身份不完整')

    def matches(self, window):
        return (all(window.get(k) == getattr(self, k) for k in ('pid', 'birth', 'hwnd'))
                and str(window.get('image', '')).casefold() == self.image.casefold())


async def bounded_local_wait(wait_api, *, clock, deadline_ns, accept):
    """仅供本地应用事件等待；每块至多1秒，未知异常直接上抛，原截止不变。"""
    while True:
        remaining = deadline_ns - clock.monotonic_ns()
        require(remaining > 0, '本地门闩等待超过原截止')
        seconds = min(1., remaining / SECOND)
        row = await asyncio.wait_for(wait_api(seconds), timeout=seconds)
        require(clock.monotonic_ns() < deadline_ns, '本地门闩等待返回时已过原截止')
        if accept(row):
            return row


class Ledger:
    """整个产品客户端共用；不提供恢复、重置时限或清除失败接口。"""

    def __init__(self, *, context, cleanup_deadline_ns, clock=None, enabled=False, emit=None):
        require(positive(cleanup_deadline_ns), '原始收尾截止无效')
        self.context = context
        self.clock = clock or Clock()
        self.cleanup_deadline_ns = cleanup_deadline_ns
        self.enabled = enabled is True
        self.emit = emit or (lambda row: None)
        self.token = 'start'
        self.failed = None
        self.not_before_ns = 0
        self.busy = False
        self.cleanup_active = False
        self.pending = False
        self.seen = set()
        self.events = []

    def event(self, kind, **data):
        row = dict(kind=kind, monotonic_ns=self.clock.monotonic_ns(),
                   wall_ns=self.clock.wall_ns(), **data)
        # 内存记录先于外部写入；外部审计失败不能消除已经发生的尝试。
        self.events.append(row)
        self.emit(row)

    def time_left(self, margin_ns=0):
        now = self.clock.monotonic_ns()
        require(now >= self.not_before_ns, '原120秒零桌面请求截止尚未到达')
        require(now + margin_ns < self.cleanup_deadline_ns, '原始收尾时限不足')

    def fail(self, ident, reason):
        if self.failed is None:
            self.failed = ident
            self.not_before_ns = max(self.not_before_ns, self.clock.monotonic_ns() + 120 * SECOND)
            self.event('failed', id=ident, reason=reason, not_before_ns=self.not_before_ns)

    @contextmanager
    def operation(self, ident, parent, *, cleanup=False):
        # 入口拒绝零桌面请求；不能消费已有忙请求的状态或改变其token。
        require(self.enabled and not self.busy and not self.pending
                and (self.failed is None or cleanup),
                '客户端禁用、忙、排队或已有失败锁存')
        require(isinstance(ident, str) and re.fullmatch('[A-Za-z0-9_-]+', ident)
                and ident not in self.seen and parent == self.token, 'ID重复、无效或旧token')
        self.time_left()
        self.seen.add(ident)
        self.busy = True
        self.cleanup_active = cleanup
        try:
            self.event('request', id=ident, parent=parent)
            yield
            self.time_left()
            require(not self.pending, '执行期间出现排队请求')
            self.event('complete', id=ident)
            if self.failed is None:
                self.token = ident
        except BaseException as error:
            self.fail(ident, type(error).__name__ + ': ' + str(error))
            raise
        finally:
            self.busy = False
            self.cleanup_active = False

    def desktop_allowed(self):
        require(self.busy and self.enabled and (self.failed is None or self.cleanup_active) and not self.pending,
                '桌面调用必须属于唯一未失败请求')
        self.time_left()
