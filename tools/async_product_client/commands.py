"""原产品可见NET按钮的读图后单次点击；不发快捷键或内部编辑命令。"""
from __future__ import annotations

import copy

from .core import require
from .file_dialog import FileDialogPolicy

COMMANDS = {'netlistOpen': '打开 NET…', 'copperAnalyze': '受限铜层几何分析（非 DRC）'}


class ProductCommand:
    def __init__(self, ledger, io, reviews, *, command, request_id, deadline_ns, enabled=False):
        require(command in COMMANDS and deadline_ns <= ledger.cleanup_deadline_ns, '命令或原截止未冻结')
        require(io.ledger is ledger and reviews.ledger is ledger and reviews.identity == io.owner.identity,
                '可见命令接口属于其他客户端/主窗')
        self.ledger, self.io, self.reviews = ledger, io, reviews
        self.command, self.request_id, self.deadline_ns = command, request_id, deadline_ns
        self.enabled = enabled is True
        self.stage, self.review, self.target, self.used = 'new', None, None, False
        self.trigger_mono_ns = None

    def check(self):
        self.ledger.desktop_allowed()
        require(self.enabled and not self.ledger.cleanup_active
                and self.ledger.clock.monotonic_ns() < self.deadline_ns, '可见命令禁用/阶段或原时限不符')

    def button(self, target):
        button = target.get('commands', {}).get(self.command, {})
        box, rect = button.get('rect', []), target['rect']
        require(button.get('automation_id') == self.command and button.get('name') == COMMANDS[self.command]
                and button.get('pid') == self.io.owner.identity.pid and button.get('control_type') == 50000
                and button.get('enabled') is True and button.get('offscreen') is False
                and button.get('descendant_verified') is True and len(box) == 4
                and all(type(v) is int for v in box)
                and rect[0] <= box[0] < box[2] <= rect[2] and rect[1] <= box[1] < box[3] <= rect[3],
                '可见命令按钮身份/名称/归属/物理rect不符')
        return button

    async def capture(self, ident, parent):
        with self.ledger.operation(ident, parent, deadline_ns=self.deadline_ns):
            self.check(); require(self.stage == 'new', '可见命令图不可重复发布')
            shot = await self.io.capture(dirty=False, stable=True)
            after = self.io.capture_targets[shot.call_id]
            self.button(after)
            self.check()
            self.target = copy.deepcopy(after)
            self.review = ident + '-image'
            self.reviews.request(self.review, stage='command', snapshot=shot, gate_request_id=self.request_id,
                                 deadline_mono_ns=self.deadline_ns, app_deadline_ns=None,
                                 expected=dict(command=self.command, name=COMMANDS[self.command], title=after['title']))
            self.stage = 'requested'
        return self.review

    async def ack(self, ident, parent, **evidence):
        with self.ledger.operation(ident, parent, deadline_ns=self.deadline_ns):
            self.check(); require(self.stage == 'requested', '可见命令ack乱序')
            self.reviews.ack(self.review, **evidence)
            require(await self.io.observe(dirty=False) == self.target, '读图或ack核对期间按钮/焦点改变')
            self.check(); self.stage = 'read'

    async def click(self, ident, parent, *, image_point):
        with self.ledger.operation(ident, parent, deadline_ns=self.deadline_ns):
            self.check(); require(self.stage == 'read' and not self.used, '须先实际read命令图，且点击机会未消费')
            target = await self.io.observe(dirty=False)
            require(target == self.target, '实际read后命令按钮/焦点变化')
            button = self.button(target)
            row = self.reviews.consume(self.review, stage='command'); shot = row.snapshot
            require(shot.hwnd == target['hwnd'] and shot.physical_rect == tuple(target['rect'])
                    and len(image_point) == 2 and all(type(v) is int for v in image_point)
                    and 0 <= image_point[0] < shot.width and 0 <= image_point[1] < shot.height, '命令图坐标/窗口不符')
            point = [round(shot.physical_rect[i] + image_point[i] * shot.scale[i]) for i in (0, 1)]
            box = button['rect']
            require(box[0] < point[0] < box[2] and box[1] < point[1] < box[3], '命令点击坐标不在明确按钮内')
            self.check(); self.used = True; self.stage = 'attempted'
            self.trigger_mono_ns = self.ledger.clock.monotonic_ns()
            if self.command == 'copperAnalyze':
                self.ledger.arm_gate(self.trigger_mono_ns)
            await self.io._send('Click', dict(loc=point), f'Single left clicked at ({point[0]},{point[1]}).')
            if self.command == 'netlistOpen':
                # 文件框出现是预期阶段变化；仍保留精确产品前景后验，不把模态当主窗输入。
                native = await self.io.native_api()
                self.check(); self.io.owner.alive()
                FileDialogPolicy.check(native, self.io.owner.identity, main_title=target['title'])
            else:
                await self.io.observe(dirty=False)
            self.check(); self.stage = 'completed'
        return self.trigger_mono_ns
