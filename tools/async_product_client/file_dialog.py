"""原生NET文件框独立状态机；路径固定为冻结副本，实际读图后唯一输入与明确打开。"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

from .core import digest, positive, require, valid_hash

FILE_TITLE = '只读载入 Protel 网表'
FILE_CLASS = '#32770'


@dataclass(frozen=True)
class NetFileSpec:
    path: str
    sha256: str

    def __post_init__(self):
        value = Path(self.path)
        require(value.is_absolute() and not value.as_posix().startswith('//')
                and value.name in ('a.net', 'b.net') and valid_hash(self.sha256)
                and not any(c in self.path for c in ('\r', '\n', '\0', '"')), '只允许本轮冻结A/B网表绝对路径')

    def verify(self):
        path = Path(self.path)
        require(path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == self.sha256,
                '冻结网表副本缺失或摘要改变')


class FileTypePermit:
    """仅当前文件框操作生成并消费一次；外部请求不得直接反序列化该对象。"""

    def __init__(self, ledger, arguments, spec):
        require(type(spec) is NetFileSpec and arguments.get('text') == spec.path,
                '文件框Type凭据只能绑定冻结A/B网表副本')
        spec.verify()
        self.spec = spec
        self.ledger, self.parent = ledger, ledger.token
        self._arguments, self.used = copy.deepcopy(arguments), False

    @property
    def arguments(self):
        return copy.deepcopy(self._arguments)

    def consume(self, ledger):
        ledger.desktop_allowed()
        require(ledger is self.ledger and ledger.token == self.parent and not self.used
                and not ledger.cleanup_active, '文件框Type凭据已消费、跨客户端/token或属于收尾')
        require(self._arguments.get('text') == self.spec.path, '文件框Type路径与冻结副本不符')
        self.spec.verify()
        self.used = True
        return dict(self.arguments)


class FileDialogPolicy:
    @staticmethod
    def check(native, identity, *, main_title):
        require(native.get('input_desktop') == 'Default' and native.get('locked') is False
                and native.get('foreground_stable') is True, '文件框输入桌面/前景未知')
        windows = native.get('windows', [])
        main = [w for w in windows if w.get('hwnd') == identity.hwnd]
        require(len(main) == 1 and identity.matches(main[0]) and main[0].get('owner') == 0
                and main[0].get('cls') == 'Qt6120QWindowIcon' and main[0].get('title') == main_title
                and main[0].get('enabled') is False, '文件框对应主窗身份/标题/禁用状态不符')
        owned = [w for w in windows if w.get('pid') == identity.pid and w.get('owner') == identity.hwnd]
        require(len(windows) == 2 and len(owned) == 1, '文件框归属不唯一或出现额外窗口')
        target = owned[0]
        require(positive(target.get('hwnd')) and target['hwnd'] != identity.hwnd
                and all(target.get(k) == getattr(identity, k) for k in ('pid', 'birth'))
                and str(target.get('image', '')).casefold() == identity.image.casefold()
                and target.get('cls') == FILE_CLASS and target.get('title') == FILE_TITLE
                and target.get('enabled') is True and target.get('modal') is True
                and native.get('foreground') == target, '原生文件框精确身份/owner/前景不符')
        rect = target.get('rect', [])
        require(target.get('coordinate_space') == 'physical-desktop-pixels'
                and target.get('thread_context_restored') is True and len(rect) == 4
                and all(type(v) is int for v in rect) and rect[0] < rect[2] and rect[1] < rect[3], '文件框物理矩形未知')
        controls = target.get('file_controls', {})
        require(set(controls) == {'filename', 'open', 'cancel'}, '文件框缺少唯一文件名/打开/取消控件')
        for name, row in controls.items():
            box = row.get('rect', [])
            require(row.get('pid') == identity.pid and row.get('descendant_verified') is True
                    and row.get('enabled') is True and row.get('offscreen') is False
                    and len(box) == 4 and all(type(v) is int for v in box)
                    and rect[0] <= box[0] < box[2] <= rect[2] and rect[1] <= box[1] < box[3] <= rect[3],
                    '文件框控件归属/启用/物理rect无效')
        edit = controls['filename']
        require(edit.get('automation_id') == '1148' and edit.get('control_type') == 50004
                and isinstance(edit.get('value'), str) and edit.get('read_only') is False, '文件名Edit身份/只读值不符')
        require(controls['open'].get('automation_id') == '1' and controls['open'].get('control_type') == 50000
                and controls['open'].get('name') == '打开(O)'
                and controls['cancel'].get('automation_id') == '2' and controls['cancel'].get('control_type') == 50000
                and controls['cancel'].get('name') == '取消', '原生打开/取消按钮协议未冻结或不符')
        return target


class NetFileDialog:
    def __init__(self, ledger, io, reviews, spec, *, request_id, main_title, deadline_ns, enabled=False):
        require(positive(request_id) and positive(deadline_ns) and deadline_ns <= ledger.cleanup_deadline_ns,
                '文件框关联请求/原截止无效')
        require(io.ledger is ledger and reviews.ledger is ledger and reviews.identity == io.owner.identity,
                '文件框组件不属于同一客户端/主窗')
        self.ledger, self.io, self.reviews, self.spec = ledger, io, reviews, spec
        self.request_id, self.main_title, self.deadline_ns = request_id, main_title, deadline_ns
        self.enabled = enabled is True
        self.stage = 'new'
        self.bound_hwnd = None
        self.dialog_review = self.path_review = None
        self.type_used = self.choice_used = False
        self.trigger_mono_ns = None
        self.review_windows = {}

    def check(self):
        self.ledger.desktop_allowed()
        require(self.enabled and not self.ledger.cleanup_active
                and self.ledger.clock.monotonic_ns() < self.deadline_ns, '文件框禁用/原截止已到/错误收尾阶段')
        self.spec.verify()
        self.io.owner.alive()

    async def observe(self):
        self.check()
        native = await self.io.native_api()
        self.check()
        target = FileDialogPolicy.check(native, self.io.owner.identity, main_title=self.main_title)
        require(self.bound_hwnd is None or target['hwnd'] == self.bound_hwnd, '文件框HWND改变')
        self.ledger.event('file_dialog_observed', result=native)
        return target

    async def capture(self, ident, stage):
        before = await self.observe()
        shot = await self.io.snapshot_api(before)
        after = await self.observe()
        require(before == after and shot.hwnd == before['hwnd'] and shot.physical_rect == tuple(before['rect']),
                '文件框截图期间身份/控件/物理rect改变')
        self.review_windows[ident] = copy.deepcopy(before)
        self.reviews.request(ident, stage=stage, snapshot=shot, gate_request_id=self.request_id,
                             deadline_mono_ns=self.deadline_ns, app_deadline_ns=None,
                             expected=dict(title=FILE_TITLE, owner=self.io.owner.identity.hwnd,
                                           path=before['file_controls']['filename']['value'],
                                           sha256=self.spec.sha256))

    async def start(self, ident, parent):
        with self.ledger.operation(ident, parent):
            self.check()
            require(self.stage == 'new', '文件框阶段已开始，禁止重置')
            target = await self.observe()
            self.bound_hwnd = target['hwnd']
            self.dialog_review = ident + '-image'
            await self.capture(self.dialog_review, 'file-dialog')
            self.stage = 'dialog-requested'
        return self.dialog_review

    async def ack(self, ident, parent, *, call_id, result_id, judgment, summary):
        with self.ledger.operation(ident, parent):
            self.check()
            require(self.stage in ('dialog-requested', 'path-requested'), '文件框ack乱序')
            review = self.dialog_review if self.stage == 'dialog-requested' else self.path_review
            before = await self.observe()
            require(before == self.review_windows[review], '发布图像后文件框控件/路径/焦点已经变化')
            self.reviews.ack(review, call_id=call_id, result_id=result_id, judgment=judgment, summary=summary)
            after = await self.observe()
            require(before == after, '文件框实际read期间控件/路径变化')
            if self.stage == 'path-requested':
                require(after['file_controls']['filename']['value'] == self.spec.path, '实际read确认路径并非冻结副本')
            self.stage = 'dialog-read' if self.stage == 'dialog-requested' else 'path-read'

    async def type_path(self, ident, parent):
        with self.ledger.operation(ident, parent):
            self.check()
            require(self.stage == 'dialog-read' and not self.type_used, '文件框必须实际read后才唯一输入路径')
            target = await self.observe()
            require(target == self.review_windows[self.dialog_review], '实际read后文件框控件/焦点改变')
            row = self.reviews.consume(self.dialog_review, stage='file-dialog')
            require(row.snapshot.hwnd == target['hwnd'] and row.snapshot.physical_rect == tuple(target['rect']), '读图后文件框改变')
            edit = target['file_controls']['filename']
            box = edit['rect']; point = [(box[0] + box[2]) // 2, (box[1] + box[3]) // 2]
            arguments = dict(text=self.spec.path, loc=point, clear=True, press_enter=False, caret_position='idle')
            permit = FileTypePermit(self.ledger, arguments, self.spec)
            self.type_used = True
            self.stage = 'type-attempted'
            receipt = await self.io.transport.file_dialog_type(permit)
            require(receipt.get('tool') == 'Type' and receipt.get('arguments') == arguments
                    and receipt.get('is_error') is False
                    and receipt.get('text') == [f'Typed {self.spec.path} at ({point[0]},{point[1]}).'], '文件框Type回执错误或结果未知')
            after = await self.observe()
            focus = after.get('file_focus', {})
            require(after['file_controls']['filename']['value'] == self.spec.path
                    and focus.get('automation_id') == '1148' and focus.get('control_type') == 50004
                    and focus.get('pid') == self.io.owner.identity.pid and focus.get('descendant_verified') is True,
                    'Type后冻结路径值/文件名焦点后验不符')
            self.path_review = ident + '-image'
            await self.capture(self.path_review, 'file-path')
            self.stage = 'path-requested'
        return self.path_review

    async def choose(self, ident, parent, *, choice, image_point):
        with self.ledger.operation(ident, parent):
            self.check()
            require(choice in ('open', 'cancel') and not self.choice_used
                    and (self.stage == 'path-read' if choice == 'open' else self.stage in ('dialog-read', 'path-read')),
                    '文件框选择乱序；打开前必须实际read确认冻结路径')
            target = await self.observe()
            review = self.path_review if self.stage == 'path-read' else self.dialog_review
            stage = 'file-path' if self.stage == 'path-read' else 'file-dialog'
            require(target == self.review_windows[review], '实际read后文件框控件/路径/焦点改变')
            row = self.reviews.consume(review, stage=stage)
            shot = row.snapshot
            require(shot.hwnd == target['hwnd'] and shot.physical_rect == tuple(target['rect'])
                    and len(image_point) == 2 and all(type(v) is int for v in image_point)
                    and 0 <= image_point[0] < shot.width and 0 <= image_point[1] < shot.height, '文件框图像坐标/HWND不符')
            if choice == 'open': require(target['file_controls']['filename']['value'] == self.spec.path, '打开前冻结路径已变')
            point = [round(shot.physical_rect[i] + image_point[i] * shot.scale[i]) for i in (0, 1)]
            box = target['file_controls'][choice]['rect']
            require(box[0] < point[0] < box[2] and box[1] < point[1] < box[3], '实际read坐标不在明确按钮内')
            self.check()
            self.choice_used = True
            self.stage = choice + '-attempted'
            # 目标异步请求由明确打开按钮触发；起点必须早于该原输入调用。
            if choice == 'open': self.trigger_mono_ns = self.ledger.clock.monotonic_ns()
            await self.io._send('Click', dict(loc=point), f'Single left clicked at ({point[0]},{point[1]}).')
            await self.io.observe(dirty=False)
            self.check()
            self.stage = 'submitted' if choice == 'open' else 'cancelled'
        return dict(stage=self.stage, trigger_mono_ns=self.trigger_mono_ns, load_verified=False)
