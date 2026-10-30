"""产品专用一次正常关闭；dirty模态真实读图后明确点击，原Popen等待后退役。"""
from __future__ import annotations

from .core import SECOND, require
from .product import MODAL_TITLE, original_wait


class ProductClose:
    def __init__(self, ledger, io, reviews, *, cleanup_ready, request_id, waiter=original_wait,
                 wait_ns=5 * SECOND, tool_margin_ns=35 * SECOND, stop_margin_ns=40 * SECOND):
        require(all(type(x) is int and x > 0 for x in (wait_ns, tool_margin_ns, stop_margin_ns)),
                '冻结正常退出余量无效')
        self.ledger, self.io, self.reviews = ledger, io, reviews
        self.cleanup_ready, self.request_id = cleanup_ready, request_id
        self.waiter = waiter
        self.wait_ns, self.tool_margin_ns, self.stop_margin_ns = wait_ns, tool_margin_ns, stop_margin_ns
        self.used = False
        self.choice_used = False
        self.stage = 'new'
        self.modal_review = None
        self.completed = False

    def budget(self):
        self.ledger.time_left(self.tool_margin_ns + self.wait_ns + self.stop_margin_ns)

    async def finish(self):
        self.stage = 'wait-exit'
        await self.io.owner.wait_exit(self.waiter, self.wait_ns)
        self.stage = 'retired'
        self.ledger.event('normal_close_finished', completed=self.ledger.failed is None,
                          lifecycle_only=self.ledger.failed is not None)

    async def start(self, ident, parent, *, dirty):
        with self.ledger.operation(ident, parent, cleanup=True):
            require(not self.used and self.stage == 'new' and type(dirty) is bool,
                    '正常关闭机会已消费或dirty状态未知')
            self.budget()
            require(await self.cleanup_ready(), '产品实验尚未结算或仍有门闩工作')
            self.used = True
            await self.io.observe(dirty=dirty)
            self.budget()
            self.stage = 'close-attempted'
            await self.io._send('Shortcut', dict(shortcut='alt+f4'), 'Pressed alt+f4.')
            if not dirty:
                # 正常退出后不再做已消失窗口的前景检查；普通输入仍在ProductIO中保持后验。
                await self.finish()
            else:
                self.stage = 'modal-observe'
                shot = await self.io.capture(stage='dirty-modal', dirty=True)
                self.modal_review = ident + '-image'
                self.reviews.request(self.modal_review, stage='dirty-modal', snapshot=shot,
                                     gate_request_id=self.request_id,
                                     deadline_mono_ns=self.ledger.cleanup_deadline_ns -
                                     (self.tool_margin_ns + self.wait_ns + self.stop_margin_ns),
                                     app_deadline_ns=None,
                                     expected=dict(title=MODAL_TITLE, default_button='取消',
                                                   discard_button='放弃更改', owner=self.io.owner.identity.hwnd))
                self.stage = 'modal-requested'
        self.completed = self.stage == 'retired' and self.ledger.failed is None
        return self.modal_review

    def ack_modal(self, ident, parent, *, call_id, result_id, judgment, summary):
        with self.ledger.operation(ident, parent, cleanup=True):
            require(self.stage == 'modal-requested', '未请求当前dirty模态图')
            self.budget()
            self.reviews.ack(self.modal_review, call_id=call_id, result_id=result_id,
                             judgment=judgment, summary=summary)
            self.stage = 'modal-read'

    async def choose(self, ident, parent, *, choice, image_point):
        with self.ledger.operation(ident, parent, cleanup=True):
            require(self.stage == 'modal-read' and not self.choice_used and choice in ('放弃更改', '取消'),
                    '必须先实际read当前模态，再唯一明确选择按钮')
            self.budget()
            row = self.reviews.consume(self.modal_review, stage='dirty-modal')
            target = await self.io.observe(stage='dirty-modal', dirty=True)
            require(target['hwnd'] == row.snapshot.hwnd and tuple(target['rect']) == row.snapshot.physical_rect,
                    '实际read之后模态HWND或物理矩形改变')
            shot = row.snapshot
            require(len(image_point) == 2 and all(type(x) is int for x in image_point)
                    and 0 <= image_point[0] < shot.width and 0 <= image_point[1] < shot.height,
                    '模态选择点不在实际图像内')
            point = [round(shot.physical_rect[i] + image_point[i] * shot.scale[i]) for i in (0, 1)]
            self.io.point(target, point)
            buttons = target.get('buttons', {})
            rect = buttons.get(choice, [])
            require(len(rect) == 4 and rect[0] < point[0] < rect[2] and rect[1] < point[1] < rect[3],
                    '读图坐标不在明确命名的目标按钮内')
            self.budget()
            self.choice_used = True
            self.stage = 'choice-attempted'
            await self.io._send('Click', dict(loc=point), f'Single left clicked at ({point[0]},{point[1]}).')
            if choice == '放弃更改':
                await self.finish()
            else:
                await self.io.observe(dirty=True)
                self.stage = 'cancelled'
                self.ledger.event('normal_close_cancelled', close_opportunity_consumed=True)
        self.completed = self.stage == 'retired' and self.ledger.failed is None

    async def reap_after_failure(self):
        """只等待原Popen；零桌面请求，不能把先前输入错误改写成成功。"""
        require(self.ledger.failed is not None and not self.ledger.busy, '仅用于失败后的原Popen见证')
        await self.io.owner.wait_exit(self.waiter, self.wait_ns)
        self.ledger.event('failed_product_reaped', failed_id=self.ledger.failed, completed=False)
