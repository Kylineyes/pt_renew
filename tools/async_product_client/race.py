"""单次NET/铜竞争编排；同应用时钟顺序与外部保守截止分别核验。"""
from __future__ import annotations

from dataclasses import dataclass

from .core import SECOND, positive, require, valid_hash


@dataclass(frozen=True)
class GateState:
    run_id: str
    pid: int
    request_id: int
    kind: str
    sequence: int
    entered_ns: int
    ready_ns: int
    deadline_ns: int
    sampled_app_ns: int
    phase: str
    revision: int
    dirty: bool
    tracks: int
    net_sha256: str
    published_ns: int = 0
    released_ns: int = 0
    returned_ns: int = 0
    discarded_ns: int = 0
    aborted: bool = False
    original_discard_decision: bool = False


class RaceClient:
    def __init__(self, ledger, io, reviews, *, gate_api, release_api, kind, request_id,
                 trigger_mono_ns, a_sha256, revision, watchdog_ns=60 * SECOND,
                 release_margin_ns=5 * SECOND):
        require(kind in ('net', 'copper') and positive(request_id) and positive(revision)
                and valid_hash(a_sha256), '实验类型/请求/原修订/A来源不完整')
        require(positive(watchdog_ns) and watchdog_ns <= 60 * SECOND
                and positive(release_margin_ns) and release_margin_ns < watchdog_ns, '冻结时限或释放余量无效')
        require(type(trigger_mono_ns) is int and 0 <= trigger_mono_ns <= ledger.clock.monotonic_ns(),
                '必须保存目标请求触发前的本地单调时钟')
        self.ledger, self.io, self.reviews = ledger, io, reviews
        self.gate_api, self.release_api = gate_api, release_api
        self.kind, self.request_id = kind, request_id
        self.a_sha256, self.original_revision = a_sha256, revision
        self.watchdog_ns, self.release_margin_ns = watchdog_ns, release_margin_ns
        self.deadline = min(trigger_mono_ns + watchdog_ns, ledger.cleanup_deadline_ns)
        self.gate_read_deadline = min(trigger_mono_ns + watchdog_ns // 3, self.deadline)
        self.edit_read_deadline = min(trigger_mono_ns + watchdog_ns * 5 // 6, self.deadline)
        self.stage = 'new'
        self.first = None
        self.previous = None
        self.gate_review = self.edit_review = self.final_review = None
        self.release_attempted = False
        self.release_returned = False
        self.release_app_ns = None
        self.settled = False

    async def state(self, *, waiting=True, margin=0):
        self.ledger.time_left()
        require(not waiting or self.ledger.clock.monotonic_ns() + margin < self.deadline,
                '原门闩保守截止已到或剩余时间不足')
        # gate_api仅能读本地应用状态，不得做桌面预检/续心跳/重置门闩。
        state = await self.gate_api()
        require(isinstance(state, GateState), '应用门闩观察未知')
        require((state.run_id, state.pid, state.request_id, state.kind) ==
                (self.ledger.application_run_id, self.io.owner.identity.pid, self.request_id, self.kind),
                '门闩运行/PID/请求/类型不匹配')
        require(all(positive(x) for x in (state.sequence, state.entered_ns, state.ready_ns,
                                        state.deadline_ns, state.sampled_app_ns))
                and state.entered_ns < state.ready_ns <= state.sampled_app_ns
                and state.deadline_ns - state.ready_ns == self.watchdog_ns, '应用原时钟或60秒截止不符')
        require(type(state.revision) is int and state.revision > 0 and type(state.tracks) is int
                and state.tracks >= 0 and type(state.dirty) is bool and type(state.aborted) is bool
                and valid_hash(state.net_sha256), '应用文档观察字段无效')
        if self.first is None:
            self.first = state
        else:
            require((state.entered_ns, state.ready_ns, state.deadline_ns) ==
                    (self.first.entered_ns, self.first.ready_ns, self.first.deadline_ns), '原应用门闩时钟改变')
        if self.previous is not None:
            require(state.sequence >= self.previous.sequence
                    and state.sampled_app_ns >= self.previous.sampled_app_ns, '应用观察时钟或序号倒退')
            require(state.sequence != self.previous.sequence or state == self.previous,
                    '同序号应用状态被改写')
        self.previous = state
        if waiting:
            require(state.phase == 'waiting' and not state.aborted and not state.returned_ns
                    and not state.released_ns and state.sampled_app_ns + margin < state.deadline_ns
                    and self.ledger.clock.monotonic_ns() + margin < self.deadline,
                    '门闩已取消/返回/释放/超时或缺少余量')
        return state

    def expected(self, state):
        return dict(revision=state.revision, dirty=state.dirty, tracks=state.tracks,
                    net_sha256=state.net_sha256)

    def edited(self, state):
        require(state.revision > self.original_revision and state.dirty is True and state.tracks == 0
                and state.net_sha256 == self.a_sha256 and state.ready_ns < state.published_ns < state.deadline_ns,
                '缺少门闩内document-published/新修订/dirty/零走线/A来源')

    async def capture_gate(self, ident, parent):
        with self.ledger.operation(ident, parent):
            require(self.stage == 'new', '门闩图阶段乱序')
            state = await self.state(waiting=True)
            require(state.revision == self.original_revision and state.dirty is False and state.tracks == 1
                    and state.net_sha256 == self.a_sha256 and not state.published_ns, '初始A来源或单走线文档不符')
            shot = await self.io.capture()
            await self.state(waiting=True)
            self.gate_review = ident + '-image'
            self.reviews.request(self.gate_review, stage='gate', snapshot=shot,
                                 gate_request_id=self.request_id, deadline_mono_ns=self.gate_read_deadline,
                                 app_deadline_ns=state.deadline_ns, expected=self.expected(state))
            self.stage = 'gate-requested'
        return self.gate_review

    async def ack(self, ident, parent, *, review_id, call_id, result_id, judgment, summary):
        with self.ledger.operation(ident, parent):
            stages = {'gate-requested': self.gate_review, 'edit-requested': self.edit_review,
                      'final-requested': self.final_review}
            require(review_id == stages.get(self.stage) and review_id is not None, '图像ack阶段乱序')
            if self.stage != 'final-requested':
                await self.state(waiting=True)
            self.reviews.ack(review_id, call_id=call_id, result_id=result_id, judgment=judgment, summary=summary)
            if self.stage != 'final-requested':
                current = await self.state(waiting=True)
            else:
                current = await self.state(waiting=False)
                self.final_state(current)
            require(self.expected(current) == dict(self.reviews.requests[review_id].expected),
                    '实际read期间应用文档发生变化')
            self.stage = {'gate-requested': 'gate-read', 'edit-requested': 'edit-read',
                          'final-requested': 'settled'}[self.stage]
            if self.stage == 'settled':
                self.reviews.consume(review_id, stage='final')
        if self.stage == 'settled':
            self.settled = self.ledger.failed is None

    async def edit(self, ident, parent, *, image_point):
        with self.ledger.operation(ident, parent):
            require(self.stage == 'gate-read', '必须先实际read门闩图')
            await self.state(waiting=True, margin=self.release_margin_ns)
            request = self.reviews.consume(self.gate_review, stage='gate')
            shot = request.snapshot
            require(len(image_point) == 2 and all(type(x) is int for x in image_point)
                    and 0 <= image_point[0] < shot.width and 0 <= image_point[1] < shot.height,
                    '选择点不在实际门闩图内')
            point = [round(shot.physical_rect[i] + image_point[i] * shot.scale[i]) for i in (0, 1)]
            await self.io.click(point)
            await self.state(waiting=True, margin=self.release_margin_ns)
            await self.io.delete()
            state = await self.state(waiting=True, margin=self.release_margin_ns)
            self.edited(state)
            shot = await self.io.capture(dirty=True)
            await self.state(waiting=True, margin=self.release_margin_ns)
            self.edit_review = ident + '-image'
            self.reviews.request(self.edit_review, stage='edit', snapshot=shot,
                                 gate_request_id=self.request_id, deadline_mono_ns=self.edit_read_deadline,
                                 app_deadline_ns=state.deadline_ns, expected=self.expected(state))
            self.stage = 'edit-requested'
        return self.edit_review

    async def release(self, ident, parent):
        with self.ledger.operation(ident, parent):
            require(self.stage == 'edit-read' and not self.release_attempted, '释放乱序或机会已消费')
            state = await self.state(waiting=True, margin=self.release_margin_ns)
            self.edited(state)
            require(dict(self.reviews.requests[self.edit_review].expected) == self.expected(state),
                    '实际read后文档又发生变化')
            self.reviews.consume(self.edit_review, stage='edit')
            self.release_attempted = True
            self.ledger.event('release_attempt', request_id=self.request_id)
            # 消费机会后传输未知仍不重试，不把cancel作为release。
            receipt = await self.release_api(self.request_id)
            self.release_returned = True
            self.ledger.event('release_receipt', receipt=receipt, returned=True)
            require(isinstance(receipt, dict) and receipt.get('request_id') == self.request_id
                    and receipt.get('pid') == self.io.owner.identity.pid
                    and receipt.get('run_id') == self.ledger.application_run_id
                    and receipt.get('released') is True and receipt.get('aborted') is False
                    and type(receipt.get('app_ns')) is int
                    and state.published_ns < receipt['app_ns'] < state.deadline_ns
                    and self.ledger.clock.monotonic_ns() < self.deadline,
                    'release回执未知、越过原截止或已中止')
            self.release_app_ns = receipt['app_ns']
            self.stage = 'released'
            self.ledger.event('release_returned', receipt=receipt)

    def final_state(self, state):
        self.edited(state)
        require(state.phase == 'discarded' and not state.aborted and state.original_discard_decision is True
                and state.published_ns < state.released_ns < state.returned_ns < state.discarded_ns
                <= state.sampled_app_ns and state.released_ns < state.deadline_ns
                and state.released_ns == self.release_app_ns,
                '缺少有效release/返回/原淘汰决定')

    async def capture_final(self, ident, parent):
        with self.ledger.operation(ident, parent):
            require(self.stage == 'released', '不能用事后图补门闩内read')
            state = await self.state(waiting=False)
            self.final_state(state)
            shot = await self.io.capture(dirty=True)
            after = await self.state(waiting=False)
            self.final_state(after)
            require(self.expected(after) == self.expected(state), '终图期间文档发生变化')
            self.final_review = ident + '-image'
            self.reviews.request(self.final_review, stage='final', snapshot=shot,
                                 gate_request_id=self.request_id, deadline_mono_ns=self.ledger.cleanup_deadline_ns,
                                 app_deadline_ns=state.deadline_ns, expected=self.expected(state))
            self.stage = 'final-requested'
        return self.final_review

    async def cleanup_ready(self):
        if self.settled:
            return True
        state = await self.state(waiting=False)
        # 失败组只能按aborted收尾；本地终态不授予竞争通过。
        return (state.aborted is True and state.phase in ('discarded', 'returned')
                and state.ready_ns < state.returned_ns <= state.sampled_app_ns)
