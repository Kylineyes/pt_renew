"""单次产品会话编排；共享原Ledger和读图关口，不提供自动读图/现场启动入口。"""
from __future__ import annotations

from pathlib import Path

from .commands import ProductCommand
from .core import SECOND, positive, require, valid_hash
from .events import GateJournal, integer
from .file_dialog import NetFileDialog, NetFileSpec
from .race import RaceClient
from .release import GateRelease
from .close import ProductClose


class ProductSession:
    """从已创建/发现的产品接续；每步显式调用，失败后不恢复旧队列。"""

    def __init__(self, ledger, io, reviews, journal, *, a, b, board_sha256, revision,
                 diagnostic_deadline_ns, enabled=False, event_api=None, pause=None, waiter=None):
        require(type(a) is NetFileSpec and type(b) is NetFileSpec
                and Path(a.path).name == 'a.net' and Path(b.path).name == 'b.net' and a.sha256 != b.sha256
                and valid_hash(board_sha256) and positive(revision), '会话输入/原修订无效')
        require(io.ledger is ledger and reviews.ledger is ledger and journal.ledger is ledger
                and reviews.identity == io.owner.identity and io.owner is journal.owner
                and getattr(journal.creator, 'initial_net', None) == a, '会话组件不共享原身份或创建参数未绑定A副本')
        require(positive(diagnostic_deadline_ns) and diagnostic_deadline_ns <= ledger.cleanup_deadline_ns,
                '会话诊断截止不得超过原收尾截止')
        self.ledger, self.io, self.reviews, self.journal = ledger, io, reviews, journal
        self.a, self.b, self.board_sha256, self.revision = a, b, board_sha256, revision
        self.diagnostic_deadline_ns = diagnostic_deadline_ns
        self.enabled = enabled is True
        self.event_api, self.pause, self.waiter = event_api, pause, waiter
        self.stage = 'created'
        self.baseline_review = None
        self.command = self.dialog = self.gate = self.race = self.close = None
        self.a_request_id = self.target_request_id = None
        self.trigger_mono_ns = None

    def check(self, *stages):
        self.ledger.desktop_allowed()
        require(self.enabled and self.stage in stages and not self.ledger.cleanup_active
                and self.ledger.clock.monotonic_ns() < self.diagnostic_deadline_ns,
                '产品会话禁用、阶段乱序或原诊断截止已到')
        self.a.verify(); self.b.verify()

    def route(self, ident, parent, stages):
        # 各子模块自己管理operation；路由只在拒绝时新建一次失败记录，避免嵌套锁。
        with self.ledger.operation(ident + '-route', parent):
            self.check(*stages)
        return self.ledger.token

    def initial_a(self, rows):
        requests = [r for r in rows if r['event'] == 'request-created']
        require(len(requests) == 1 and requests[0].get('kind') == 'net' and requests[0].get('gated') is False
                and requests[0].get('path') == self.a.path
                and integer(requests[0].get('revision'), '初始A修订') == self.revision,
                '初始A请求并非创建参数中的冻结副本/修订，或已出现额外请求')
        request = requests[0]; rid = request['request_id']
        returned = [r for r in rows if r['event'] == 'worker-returned' and r.get('request_id') == rid]
        accepted = [r for r in rows if r['event'] == 'callback-accepted' and r.get('request_id') == rid]
        require(len(returned) == len(accepted) == 1 and returned[0].get('success') is True
                and returned[0].get('result_sha256') == self.a.sha256 and accepted[0].get('accepted') is True
                and accepted[0].get('experiment_aborted') is False
                and integer(accepted[0].get('captured_generation'), 'A捕获代次') == integer(request.get('generation'), 'A原代次')
                == integer(accepted[0].get('current_generation'), 'A当前代次')
                and integer(accepted[0].get('revision'), 'A回调修订') == self.revision,
                '原初始A没有正常读取/同代次接受')
        require(integer(request['monotonic_ns'], '请求时间') < integer(returned[0]['monotonic_ns'], '返回时间')
                < integer(accepted[0]['monotonic_ns'], '接受时间')
                and request['thread_id'] == accepted[0]['thread_id'] != returned[0]['thread_id']
                and not any(r['event'] in ('aborted', 'document-published', 'callback-discarded', 'gate-ready', 'run-stopped') for r in rows),
                '初始A事件时序/线程或文档状态异常')
        return integer(rid, '初始A请求ID')

    async def prepare(self, ident, parent):
        with self.ledger.operation(ident, parent):
            self.check('created')
            self.journal.bind()
            self.a_request_id = self.initial_a(self.journal.read())
            shot = await self.io.capture(dirty=False)
            require(self.initial_a(self.journal.read()) == self.a_request_id, '基线截图期间A事件改变')
            self.check('created')
            self.baseline_review = ident + '-image'
            self.reviews.request(self.baseline_review, stage='baseline', snapshot=shot,
                                 gate_request_id=self.a_request_id, deadline_mono_ns=self.diagnostic_deadline_ns,
                                 app_deadline_ns=None, expected=dict(revision=self.revision, dirty=False, tracks=1,
                                                                    net_sha256=self.a.sha256))
            self.stage = 'baseline-requested'
        return self.baseline_review

    async def ack_baseline(self, ident, parent, **evidence):
        with self.ledger.operation(ident, parent):
            self.check('baseline-requested')
            self.initial_a(self.journal.read())
            self.reviews.ack(self.baseline_review, **evidence)
            self.initial_a(self.journal.read())
            self.check('baseline-requested'); self.stage = 'baseline-read'

    async def capture_command(self, ident, parent):
        parent = self.route(ident, parent, ('baseline-read',))
        command = 'netlistOpen' if self.journal.kind == 'net' else 'copperAnalyze'
        self.command = ProductCommand(self.ledger, self.io, self.reviews, command=command,
                                      request_id=self.a_request_id + 1, deadline_ns=self.diagnostic_deadline_ns,
                                      enabled=self.enabled)
        result = await self.command.capture(ident, parent)
        self.stage = 'command-requested'
        return result

    async def ack_command(self, ident, parent, **evidence):
        parent = self.route(ident, parent, ('command-requested',))
        await self.command.ack(ident, parent, **evidence)
        self.stage = 'command-read'

    async def invoke_command(self, ident, parent, *, image_point):
        parent = self.route(ident, parent, ('command-read',))
        trigger = await self.command.click(ident, parent, image_point=image_point)
        if self.journal.kind == 'net':
            self.dialog = NetFileDialog(self.ledger, self.io, self.reviews, self.b,
                                        request_id=self.a_request_id + 1, main_title=self.io.policy.title(False),
                                        deadline_ns=self.diagnostic_deadline_ns, enabled=self.enabled)
            self.stage = 'file-open'
        else:
            self.trigger_mono_ns = trigger
            self.stage = 'target-triggered'
        return dict(stage=self.stage, trigger_mono_ns=self.trigger_mono_ns)

    async def file_step(self, ident, parent, *, action, **arguments):
        parent = self.route(ident, parent, ('file-open', 'file-active'))
        methods = {'start': self.dialog.start, 'ack': self.dialog.ack, 'type': self.dialog.type_path,
                   'choose': self.dialog.choose}
        if action not in methods:
            with self.ledger.operation(ident, parent): require(False, '未知文件框动作')
        result = await methods[action](ident, parent, **arguments)
        self.stage = 'file-active'
        if self.dialog.stage == 'submitted':
            self.trigger_mono_ns = self.dialog.trigger_mono_ns
            self.stage = 'target-triggered'
        elif self.dialog.stage == 'cancelled': self.stage = 'cancelled'
        return result

    async def attach_gate(self, ident, parent):
        with self.ledger.operation(ident, parent):
            self.check('target-triggered')
            require(type(self.trigger_mono_ns) is int and self.trigger_mono_ns <= self.ledger.clock.monotonic_ns()
                    < self.trigger_mono_ns + 60 * SECOND,
                    '丢失目标输入前原触发时钟')
            rows = self.journal.read()
            requests = [r for r in rows if r['event'] == 'request-created' and r.get('gated') is True]
            require(len(requests) == 1 and requests[0].get('kind') == self.journal.kind,
                    '尚无唯一目标原门闩请求')
            request = requests[0]
            rid = integer(request.get('request_id'), '目标原请求ID')
            require(rid == self.a_request_id + 1 and sum(r['event'] == 'request-created' for r in rows) == 2,
                    '目标原请求ID或数量不符')
            if self.journal.kind == 'net': require(request.get('path') == self.b.path, '目标NET不是冻结B副本')
            self.target_request_id = rid
            self.gate = GateJournal(self.journal, self.reviews, baseline_review_id=self.baseline_review,
                                    request_id=rid, trigger_mono_ns=self.trigger_mono_ns,
                                    a_sha256=self.a.sha256, b_sha256=self.b.sha256, board_sha256=self.board_sha256)
            self.gate.observe()
            kwargs = dict(enabled=self.enabled, event_api=self.event_api)
            if self.pause is not None: kwargs['pause'] = self.pause
            release = GateRelease(self.gate, self.reviews, **kwargs)
            self.race = RaceClient(self.ledger, self.io, self.reviews, gate_api=self.gate, release_api=release,
                                   kind=self.journal.kind, request_id=rid, trigger_mono_ns=self.trigger_mono_ns,
                                   a_sha256=self.a.sha256, revision=self.revision)
            kwargs = dict(cleanup_ready=self.race.cleanup_ready, request_id=rid)
            if self.waiter is not None: kwargs['waiter'] = self.waiter
            self.close = ProductClose(self.ledger, self.io, self.reviews, **kwargs)
            self.stage = 'race'

    async def race_step(self, ident, parent, *, action, **arguments):
        parent = self.route(ident, parent, ('race',))
        methods = {'gate-image': self.race.capture_gate, 'ack': self.race.ack, 'edit': self.race.edit,
                   'release': self.race.release, 'final-image': self.race.capture_final}
        if action not in methods:
            with self.ledger.operation(ident, parent): require(False, '未知竞争动作')
        result = await methods[action](ident, parent, **arguments)
        if self.race.settled: self.stage = 'settled'
        return result

    async def close_step(self, ident, parent, *, action, **arguments):
        # 此处不重新route/token：失败后的正常收尾必须保留原token/首次120秒截止。
        require(self.enabled and self.close is not None, '尚无已绑定门闩的产品收尾组件')
        methods = {'start': self.close.start, 'ack': self.close.ack_modal, 'choose': self.close.choose}
        require(action in methods, '未知正常收尾动作')
        if action == 'ack': result = methods[action](ident, parent, **arguments)
        else: result = await methods[action](ident, parent, **arguments)
        if self.close.stage == 'retired': self.stage = 'retired'
        return result

    def report(self):
        from .budget import session_budget
        return dict(stage=self.stage, client_run_id=self.ledger.context.run_id,
                    application_run_id=self.ledger.application.run_id if self.ledger.application else None,
                    a_request_id=self.a_request_id, target_request_id=self.target_request_id,
                    trigger_mono_ns=self.trigger_mono_ns, diagnostic_deadline_ns=self.diagnostic_deadline_ns,
                    cleanup_deadline_ns=self.ledger.cleanup_deadline_ns, failed_id=self.ledger.failed,
                    race_protocol_settled=bool(self.race and self.race.settled),
                    original_product_retired=self.io.owner.retired, budget=session_budget(self.journal.kind),
                    ready_for_live=False, gui_verified=False)
