"""图像request/read/ack关口；只消费原会话的成功read image，不自动判断图像内容。"""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from .core import SECOND, digest, positive, require


def wall_ns(stamp):
    value = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    require(value.tzinfo is not None, '会话时间缺少时区')
    delta = value.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * SECOND + delta.microseconds * 1000


@dataclass(frozen=True)
class Snapshot:
    path: str
    sha256: str
    call_id: str
    start_wall_ns: int
    end_wall_ns: int
    width: int
    height: int
    physical_rect: tuple
    scale: tuple
    hwnd: int
    receipt: dict

    def validate(self, image_loader):
        require(positive(self.start_wall_ns) and self.start_wall_ns <= self.end_wall_ns,
                '截图原工具起止不完整')
        require(isinstance(self.call_id, str) and bool(self.call_id), '缺少截图原调用ID')
        require(positive(self.width) and positive(self.height) and positive(self.hwnd), '图像尺寸/HWND无效')
        rect = self.physical_rect
        require(len(rect) == 4 and all(type(x) is int for x in rect)
                and rect[0] < rect[2] and rect[1] < rect[3], '物理矩形无效')
        require(len(self.scale) == 2 and all(type(x) in (int, float) and math.isfinite(x) and x > 0
                                           for x in self.scale), '图像倍率无效')
        require(abs(self.width * self.scale[0] - (rect[2] - rect[0])) < .01
                and abs(self.height * self.scale[1] - (rect[3] - rect[1])) < .01, '物理矩形与图像倍率不匹配')
        require(digest(image_loader(self.path)) == self.sha256, '截图文件缺失或摘要改变')
        require(isinstance(self.receipt, dict) and self.receipt.get('tool') == 'Snapshot'
                and self.receipt.get('is_error') is False, 'Snapshot原工具回执失败或未知')
        images = self.receipt.get('images', [])
        require(len(images) == 1 and images[0].get('mimeType', '').startswith('image/')
                and digest(base64.b64decode(images[0]['data'], validate=True)) == self.sha256,
                'Snapshot原工具没有唯一匹配image')


@dataclass(frozen=True)
class ReviewRequest:
    id: str
    context: object
    identity: object
    gate_request_id: int
    stage: str
    snapshot: Snapshot
    created_wall_ns: int
    created_mono_ns: int
    deadline_mono_ns: int
    app_deadline_ns: int | None
    expected: tuple
    application_run_id: str | None = None


class PiReadVerifier:
    """只读已绑定会话原JSONL；ack不能指定其他会话文件或自行声明image成功。"""

    def __init__(self, journal_path, *, image_loader=None, journal_loader=None):
        self.journal_path = Path(journal_path)
        self.image_loader = image_loader or (lambda path: Path(path).read_bytes())
        self.journal_loader = journal_loader or self.journal_path.read_bytes

    def verify(self, request, call_id, result_id):
        raw = self.journal_loader()
        rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
        sessions = [x for x in rows if x.get('type') == 'session']
        require(len(sessions) == 1 and sessions[0].get('id') == request.context.session_id,
                '原会话ID不匹配或拼接会话')
        ids = [x.get('id') for x in rows if x.get('id')]
        require(len(ids) == len(set(ids)), '原会话记录ID重复')
        calls = []
        results = []
        for index, row in enumerate(rows):
            msg = row.get('message', {})
            if msg.get('role') == 'assistant':
                for part in msg.get('content', []):
                    if part.get('type') == 'toolCall' and part.get('id') == call_id:
                        calls.append((index, row, msg, part))
            if msg.get('role') == 'toolResult' and msg.get('toolCallId') == call_id:
                results.append((index, row, msg))
        require(len(calls) == len(results) == 1, '实际read调用或成功回执缺失/重复')
        ci, cr, assistant, call = calls[0]
        ri, rr, result = results[0]
        ctx = request.context
        require((assistant.get('provider'), assistant.get('model'), assistant.get('thinkingLevel'))
                == (ctx.provider, ctx.model, ctx.thinking), '实际模型或推理强度不匹配')
        require(call.get('name') == 'read' and call.get('arguments', {}).get('path') == request.snapshot.path,
                '实际read工具或图路径不匹配')
        require(ri > ci and rr.get('id') == result_id and result.get('toolName') == 'read'
                and result.get('isError') is False, '实际read顺序或成功回执不匹配')
        start, end = wall_ns(cr['timestamp']), wall_ns(rr['timestamp'])
        require(request.created_wall_ns <= start <= end, 'ack使用了request之前的read或跨日志时钟矛盾')
        snapshot_end = getattr(request.snapshot, 'end_wall_ns', None)
        if snapshot_end is not None:
            require(positive(snapshot_end) and snapshot_end <= request.created_wall_ns,
                    '产品Snapshot结束时间晚于request')
        images = [x for x in result.get('content', []) if x.get('type') == 'image']
        require(len(images) == 1 and images[0].get('mimeType', '').startswith('image/'),
                'read回执缺少唯一成功image')
        # 变换/缩放后的回执也不静默接受；将来适配必须单独冻结可审计的变换链。
        image = base64.b64decode(images[0]['data'], validate=True)
        require(digest(image) == request.snapshot.sha256, 'read回执图像摘要不符')
        require(digest(self.image_loader(request.snapshot.path)) == request.snapshot.sha256,
                'read后的图文件已改变')
        return dict(call_id=call_id, result_id=result_id, start_wall_ns=start, end_wall_ns=end,
                    journal_sha256=digest(raw), image_sha256=digest(image), session_id=ctx.session_id)


class ReviewGate:
    def __init__(self, ledger, identity, verifier, *, publish, publish_ack):
        self.ledger, self.identity, self.verifier = ledger, identity, verifier
        self.publish, self.publish_ack = publish, publish_ack
        self.requests = {}
        self.published_wall_ns = {}
        self.used_images = set()
        self.used_reads = set()
        self.acks = {}
        self.consumed = set()

    def request(self, ident, *, stage, snapshot, gate_request_id, deadline_mono_ns,
                app_deadline_ns, expected):
        ledger = self.ledger
        ledger.desktop_allowed()
        require(ident not in self.requests and stage in ('baseline', 'gate', 'edit', 'final', 'dirty-modal'),
                '图像request ID重复或阶段未知')
        require(positive(gate_request_id) and positive(deadline_mono_ns)
                and (app_deadline_ns is None if stage in ('baseline', 'dirty-modal') else positive(app_deadline_ns)),
                '缺少原应用请求/截止或混用模态与应用时钟')
        require(ledger.clock.monotonic_ns() < deadline_mono_ns <= ledger.cleanup_deadline_ns,
                '图像request已过原截止')
        snapshot.validate(self.verifier.image_loader)
        require(stage == 'dirty-modal' or snapshot.hwnd == self.identity.hwnd, '图像不属于精确产品主HWND')
        require(snapshot.sha256 not in self.used_images, '旧图hash禁止复用')
        require(snapshot.end_wall_ns <= ledger.clock.wall_ns(), '截图墙钟在未来')
        require(expected and all(isinstance(k, str) for k in expected), '必须冻结图像内容判据')
        row = ReviewRequest(ident, ledger.context, self.identity, gate_request_id, stage, snapshot,
                            ledger.clock.wall_ns(), ledger.clock.monotonic_ns(), deadline_mono_ns,
                            app_deadline_ns, tuple(sorted(expected.items())),
                            ledger.application.run_id if ledger.application else None)
        # 先独占ID和hash再持久化；写入未知时不允许重建同图request。
        self.requests[ident] = row
        self.used_images.add(snapshot.sha256)
        self.publish(row)
        self.published_wall_ns[ident] = ledger.clock.wall_ns()
        ledger.event('review_request', request=asdict(row), published_wall_ns=self.published_wall_ns[ident])
        return row

    def ack(self, ident, *, call_id, result_id, judgment, summary):
        ledger = self.ledger
        ledger.desktop_allowed()
        require(ident in self.requests and ident not in self.acks and ident not in self.consumed,
                '未知、重复或已消费ack')
        row = self.requests[ident]
        require(abs((ledger.clock.wall_ns() - row.created_wall_ns)
                    - (ledger.clock.monotonic_ns() - row.created_mono_ns)) <= SECOND,
                'request到ack间墙钟跳变，不能关联实际read时序')
        require(ledger.clock.monotonic_ns() < row.deadline_mono_ns, '实际read/ack已过原截止')
        key = (ledger.context.session_id, call_id)
        require(key not in self.used_reads, '实际read回执已消费')
        proof = self.verifier.verify(row, call_id, result_id)
        require(proof['start_wall_ns'] >= self.published_wall_ns[ident], '实际read早于request持久化完成')
        require(proof['end_wall_ns'] <= ledger.clock.wall_ns(), 'read回执尚未实际返回')
        require(judgment == dict(row.expected) and isinstance(summary, str) and bool(summary.strip()),
                '实际读图内容判断缺失或与冻结判据不符')
        # 辅助observed=true字段从不参与授权；图像内容由指定会话明确判断。
        require(ledger.clock.monotonic_ns() < row.deadline_mono_ns, '实际read证据核对完成时已过原截止')
        self.used_reads.add(key)
        ack = dict(proof=proof, judgment=dict(judgment), summary=summary,
                   ack_mono_ns=ledger.clock.monotonic_ns(), ack_wall_ns=ledger.clock.wall_ns())
        self.publish_ack(ident, ack)
        require(ledger.clock.monotonic_ns() < row.deadline_mono_ns, 'ack持久化完成时已过原截止')
        self.acks[ident] = ack
        ledger.event('review_ack', request_id=ident, **ack)
        return self.acks[ident]

    def consume(self, ident, *, stage):
        require(ident in self.acks and ident not in self.consumed
                and self.requests[ident].stage == stage, '缺少同阶段read/ack或ack已消费')
        row = self.requests[ident]
        require(self.ledger.clock.monotonic_ns() < row.deadline_mono_ns, 'ack消费超过原截止')
        self.consumed.add(ident)
        self.ledger.event('review_consumed', request_id=ident, stage=stage)
        return row
