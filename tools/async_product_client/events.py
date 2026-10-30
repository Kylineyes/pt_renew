"""原应用JSONL与request清单绑定；只读本地证据，不把事件当作GUI证明。"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re

from .core import ApplicationRun, SECOND, digest, positive, require, valid_hash
from .race import GateState


def integer(value, field):
    require(type(value) is int or isinstance(value, str) and re.fullmatch('[0-9]+', value),
            field + '必须为无损非负整数')
    number = int(value)
    require(number >= 0, field + '不能为负数')
    return number


def unique_object(pairs):
    row = {}
    for key, value in pairs:
        require(key not in row, 'JSON含重复字段：' + key)
        row[key] = value
    return row


def decode_object(raw):
    row = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object)
    require(isinstance(row, dict), 'JSON必须为单一对象')
    return row


class ApplicationJournal:
    """绑定本客户端创建的原Popen及唯一随机UUID；每次读取核对既有完整前缀。"""

    def __init__(self, ledger, owner, creator, *, kind, current_identity, reader=None):
        require(kind in ('net', 'copper') and kind == creator.kind, '应用事件类型不匹配')
        self.ledger, self.owner, self.creator = ledger, owner, creator
        self.kind, self.current_identity = kind, current_identity
        self.directory = creator.experiment_directory
        self.reader = reader or (lambda path: Path(path).read_bytes())
        self.prefix = b''
        self.rows = []
        self.startup = None
        self.original_identity = None
        self.current_owner = None

    def process_identity(self):
        require(self.owner.process is not None and self.owner.process is self.creator.process
                and self.owner.process_identity is not None, '原Popen创建所有者不一致')
        require(self.owner.process.poll() is None, '产品原Popen已经退出')
        current = self.creator.inspect_created(self.owner.process)
        original = self.original_identity or self.owner.process_identity
        require(current == original, '原Popen句柄/PID/birth/image在事件核对期间改变')
        owner = self.current_identity()
        require(owner.get('original_handle') is True and positive(owner.get('pid'))
                and positive(owner.get('birth')) and owner['pid'] == self.creator.owner_pid,
                '当前持续客户端owner身份未知')
        if self.current_owner is not None:
            require(owner == self.current_owner, '持续客户端owner身份改变')
        return current, owner

    def read(self):
        # 这是本地文件/原Popen核对，不调用native桌面或MCP，不续门闩心跳。
        self.process_identity()
        require(self.directory.is_dir() and not self.directory.is_symlink()
                and not self.directory.is_junction(), '应用原事件目录不存在或被替换为链接')
        path = self.directory / 'events.jsonl'
        require(not path.is_symlink(), '应用原事件记录不能是链接')
        raw = self.reader(path)
        require(isinstance(raw, bytes) and raw and raw.endswith(b'\n') and raw.startswith(self.prefix),
                '应用事件缺失/末行不完整/原前缀被改写或截断')
        rows = [decode_object(line) for line in raw.splitlines()]
        require(rows and rows[0].get('event') == 'run-started', '缺少原应用启动记录')
        run, pid = rows[0].get('run_id'), integer(rows[0].get('pid'), '应用PID')
        require(pid == self.owner.process.pid, '应用事件不属于原Popen')
        previous = -1
        known = {'run-started', 'request-created', 'worker-entered', 'gate-ready', 'gate-released',
                 'aborted', 'worker-returned', 'callback-accepted', 'callback-discarded',
                 'document-published', 'run-stopped'}
        for number, row in enumerate(rows, 1):
            require(row.get('event') in known and row.get('run_id') == run
                    and integer(row.get('pid'), '应用PID') == pid, '应用事件混入未知类型/run/PID')
            require(integer(row.get('sequence'), '序号') == number, '应用事件序号不连续')
            stamp = integer(row.get('monotonic_ns'), '应用纳秒')
            require(stamp > previous and positive(integer(row.get('thread_id'), '应用线程')),
                    '应用纳秒不递增或线程缺失')
            integer(row.get('wall_ms'), '应用墙钟')
            previous = stamp
        require(sum(r['event'] == 'run-started' for r in rows) == 1
                and sum(r['event'] == 'run-stopped' for r in rows) <= 1
                and not any(r['event'] == 'run-stopped' for r in rows[:-1]), '多次运行或停止后又追加应用事件')
        if self.startup is not None:
            require(rows[0] == self.startup and self.ledger.application is not None
                    and self.ledger.application.run_id == run, '原应用启动记录/绑定改变')
        self.prefix, self.rows = raw, rows
        return rows

    def bind(self):
        self.ledger.desktop_allowed()
        require(self.startup is None and self.ledger.application is None, '禁止重新绑定应用运行')
        info, current_owner = self.process_identity()
        rows = self.read()
        start = rows[0]
        require(start.get('request_id') == '' and start.get('kind') == ''
                and start.get('kind_configured') == self.kind
                and integer(start.get('owner_pid'), '原owner PID') == current_owner['pid']
                and integer(start.get('owner_creation_filetime'), '原owner birth') == current_owner['birth']
                and type(start.get('skip')) is int and start['skip'] == (1 if self.kind == 'net' else 0)
                and type(start.get('watchdog_ms')) is int and start['watchdog_ms'] == 60000,
                '原应用owner/type/skip/60秒看门狗配置不符')
        require(not any(r['event'] in ('gate-ready', 'gate-released', 'aborted', 'run-stopped') for r in rows),
                '必须在目标门闩启动前绑定本轮应用')
        binding = ApplicationRun(self.ledger.context, start['run_id'], info['pid'], info['birth'], info['image'],
                                 current_owner['pid'], current_owner['birth'], str(self.directory),
                                 digest(self.prefix.splitlines(keepends=True)[0]))
        self.original_identity, self.current_owner, self.startup = dict(info), dict(current_owner), dict(start)
        self.ledger.bind_application(binding)
        return binding


class GateJournal:
    """将同一原应用事件映射成GateState；初始文档来自门闩前实际read/ack基线。"""

    def __init__(self, journal, reviews, *, baseline_review_id, request_id, trigger_mono_ns,
                 a_sha256, b_sha256, board_sha256):
        ledger = journal.ledger
        ledger.desktop_allowed()
        require(ledger.application is not None and journal.startup is not None, '尚未绑定原应用随机UUID')
        require(positive(request_id) and type(trigger_mono_ns) is int
                and 0 <= trigger_mono_ns <= ledger.clock.monotonic_ns(), '缺少触发前原始时钟/目标请求')
        require(all(valid_hash(x) for x in (a_sha256, b_sha256, board_sha256))
                and a_sha256 != b_sha256, '输入摘要无效')
        require(reviews.identity == journal.owner.identity and reviews.ledger is ledger,
                '基线审阅关口不属于原产品')
        baseline = reviews.consume(baseline_review_id, stage='baseline')
        require(baseline.context == ledger.context and baseline.application_run_id == ledger.application.run_id
                and baseline.identity == journal.owner.identity
                and baseline.created_mono_ns < trigger_mono_ns
                and reviews.acks[baseline_review_id]['ack_mono_ns'] < trigger_mono_ns
                and reviews.acks[baseline_review_id]['proof']['end_wall_ns']
                    <= baseline.created_wall_ns + (trigger_mono_ns - baseline.created_mono_ns),
                '基线未在目标请求触发前完成实际read或绑定不同应用')
        expected = dict(baseline.expected)
        require(set(expected) == {'revision', 'dirty', 'tracks', 'net_sha256'}
                and positive(expected['revision']) and expected['dirty'] is False
                and type(expected['tracks']) is int and expected['tracks'] == 1
                and expected['net_sha256'] == a_sha256, '基线必须明确clean/单走线/修订/A来源')
        self.journal, self.ledger = journal, ledger
        self.baseline, self.initial = baseline, expected
        self.request_id, self.trigger_mono_ns = request_id, trigger_mono_ns
        self.a_sha256, self.b_sha256, self.board_sha256 = a_sha256, b_sha256, board_sha256
        self.deadline_ns = min(trigger_mono_ns + 60 * SECOND, ledger.cleanup_deadline_ns)
        self.manifest_raw = None
        self.manifest = None
        self.last_state = None
        self.last_observation = None

    def manifest_check(self):
        path = self.journal.directory / f'request-{self.request_id}.json'
        require(not path.is_symlink(), '门闩request清单不能是链接')
        raw = self.journal.reader(path)
        require(self.manifest_raw is None or raw == self.manifest_raw, '原request清单被改写')
        row = decode_object(raw)
        binding = self.ledger.application
        prefix = f'Local\\PtRenewAsync-{binding.run_id}-{self.request_id}-'
        require(set(row) == {'run_id', 'request_id', 'kind', 'pid', 'creation_filetime', 'release_event', 'cancel_event'}
                and row['run_id'] == binding.run_id and integer(row['request_id'], 'request ID') == self.request_id
                and row['kind'] == self.journal.kind and integer(row['pid'], 'request PID') == binding.pid
                and integer(row['creation_filetime'], 'request birth') == binding.birth
                and row['release_event'] == prefix + 'release' and row['cancel_event'] == prefix + 'cancel',
                '原request的UUID/ID/PID/birth/事件名称不符')
        self.manifest_raw, self.manifest = raw, row
        return row

    def observe(self):
        rows = self.journal.read()
        self.manifest_check()
        ns = lambda row: integer(row['monotonic_ns'], '应用纳秒')
        target = [r for r in rows if r.get('request_id') not in ('', None)
                  and integer(r['request_id'], 'request ID') == self.request_id]
        require(target and all(r['kind'] == self.journal.kind for r in target), '目标请求类型未知或混淆')
        def one(event, required=True):
            found = [r for r in target if r['event'] == event]
            require(len(found) == 1 if required else len(found) <= 1, '原事件缺失或重复：' + event)
            return found[0] if found else None
        request, entered, ready = one('request-created'), one('worker-entered'), one('gate-ready')
        require(request.get('gated') is True
                and sum(r['event'] == 'request-created' and r.get('gated') is True for r in rows) == 1,
                '必须恰有一个门闩目标')
        require(integer(request.get('revision'), '原修订') == self.initial['revision']
                and positive(integer(request.get('generation'), '原代次'))
                and ns(request) < ns(entered) < ns(ready), '原请求/进入/ready/修订顺序不符')
        require(entered.get('stage') == ('net-file-open-before-read' if self.journal.kind == 'net' else 'copper-entry-before-budget')
                and entered['thread_id'] == ready['thread_id'] != request['thread_id'], '工作线程或门闩入口不符')
        if self.journal.kind == 'net':
            require(request.get('previous_net_sha256') == self.a_sha256, 'NET门闩前A来源不符')
        else:
            require(request.get('board_sha256') == self.board_sha256 and request.get('net_sha256') == self.a_sha256,
                    '铜门闩输入摘要不符')
        initial = [r for r in rows if r['event'] == 'worker-returned' and r.get('kind') == 'net'
                   and r.get('request_id') != request['request_id'] and ns(r) < ns(request)
                   and r.get('success') is True and r.get('result_sha256') == self.a_sha256]
        require(len(initial) == 1, '缺少唯一门闩前A读取成功')
        accepted = [r for r in rows if r['event'] == 'callback-accepted'
                    and r.get('request_id') == initial[0]['request_id'] and ns(r) < ns(request)]
        require(len(accepted) == 1 and accepted[0].get('accepted') is True
                and accepted[0].get('experiment_aborted') is False and ns(initial[0]) < ns(accepted[0]),
                '门闩前A未正常接受')
        publications = [r for r in rows if r['event'] == 'document-published']
        require(len(publications) <= 1, '出现额外文档发布，不能拼接竞争')
        document = dict(self.initial)
        published = publications[0] if publications else None
        if published:
            require(ns(ready) < ns(published) < ns(ready) + 60 * SECOND
                    and published['thread_id'] == request['thread_id'], '文档发布不在原门闩内或非GUI线程')
            revision, tracks = integer(published.get('revision'), '新修订'), integer(published.get('tracks'), '新走线数')
            require(revision > self.initial['revision'] and published.get('dirty') is True
                    and tracks == 0 and published.get('net_sha256') == self.a_sha256,
                    '原document-published缺少新修订/dirty/零线/A来源')
            document.update(revision=revision, dirty=True, tracks=tracks)
        released, aborted, returned = (one(name, False) for name in ('gate-released', 'aborted', 'worker-returned'))
        callbacks = [r for r in target if r['event'] in ('callback-accepted', 'callback-discarded')]
        require(len(callbacks) <= 1 and not (released and aborted), '完成回调重复或同时出现release/abort')
        for terminal in (released, aborted):
            if terminal:
                require(ns(ready) < ns(terminal), '终止事件早于原ready')
        if released:
            require(ns(released) < ns(ready) + 60 * SECOND and released['thread_id'] == entered['thread_id'],
                    '原release超时或不属于原worker')
            if published: require(ns(published) < ns(released), '先release后编辑不能当有效竞争')
        if returned:
            require((released or aborted) and ns(released or aborted) < ns(returned)
                    and returned['thread_id'] == entered['thread_id'], '原工作返回缺少有效终止前序')
            if self.journal.kind == 'net':
                require(returned.get('success') is True and returned.get('result_sha256') == self.b_sha256,
                        '原NET结果不是冻结B或读取失败')
            else:
                require(returned.get('net_sha256') == self.a_sha256 and returned.get('limit_reached') is False
                        and integer(returned.get('revision'), '铜原修订') == self.initial['revision'],
                        '原铜结果输入/修订/算法预算不符')
        callback = callbacks[0] if callbacks else None
        discard = False
        if callback:
            require(returned and ns(returned) < ns(callback) and callback['thread_id'] == request['thread_id']
                    and type(callback.get('accepted')) is bool
                    and callback['accepted'] == (callback['event'] == 'callback-accepted')
                    and callback.get('experiment_aborted') is bool(aborted), '原回调顺序/线程/接受或中止决定不符')
            if published:
                require(callback['event'] == 'callback-discarded', '旧结果没有被原回调丢弃')
                if self.journal.kind == 'net':
                    require(integer(callback.get('captured_generation'), '捕获代次') == integer(request['generation'], '原代次')
                            and integer(callback.get('current_generation'), '当前代次') != integer(request['generation'], '原代次')
                            and integer(callback.get('revision'), '回调修订') == document['revision'], '原NET代次淘汰不符')
                else:
                    require(callback.get('generation_matches') is False and callback.get('board_matches') is False
                            and callback.get('net_matches') is True
                            and integer(callback.get('captured_revision'), '铜捕获修订') == self.initial['revision']
                            and integer(callback.get('current_revision'), '铜当前修订') == document['revision'], '原铜身份淘汰不符')
                discard = not bool(aborted)
        phase = ('discarded' if callback and callback['event'] == 'callback-discarded' else 'accepted' if callback
                 else 'returned' if returned else 'aborted' if aborted else 'released' if released else 'waiting')
        state = GateState(self.ledger.application.run_id, self.owner_pid, self.request_id, self.journal.kind,
                          integer(rows[-1]['sequence'], '末序号'), ns(entered), ns(ready), ns(ready) + 60 * SECOND,
                          ns(rows[-1]), phase, document['revision'], document['dirty'], document['tracks'], self.a_sha256,
                          ns(published) if published else 0, ns(released) if released else 0,
                          ns(returned) if returned else 0, ns(callback) if callback and callback['event'] == 'callback-discarded' else 0,
                          bool(aborted), discard)
        self.last_state = state
        self.last_observation = dict(context=asdict(self.ledger.context), application_run_id=state.run_id,
                                     trace_sha256=digest(self.journal.prefix), trace_bytes=len(self.journal.prefix),
                                     manifest_sha256=digest(self.manifest_raw), state=asdict(state),
                                     sampled_app_ns_source='原记录最后事件；不是应用当前时刻',
                                     observed_mono_ns=self.ledger.clock.monotonic_ns(), gui_verified=False)
        return state

    @property
    def owner_pid(self):
        return self.ledger.application.pid

    async def __call__(self):
        return self.observe()
