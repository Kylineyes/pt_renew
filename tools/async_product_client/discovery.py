"""首次主HWND发现并绑定；明确标题、owner及只读UIA交叉核验，不尝试聚焦或输入。"""
from __future__ import annotations

from .core import require
from .native import ReadOnlyWin32, query_uia
from .product import QT_CLASS, EXPERIMENT_SUFFIX


class ProductMainDiscovery:
    def __init__(self, ledger, owner, creator, policy, *, uia, api=None, enabled=False):
        self.ledger, self.owner, self.creator, self.policy = ledger, owner, creator, policy
        self.uia, self.api, self.enabled = uia, api or ReadOnlyWin32(), enabled is True
        self.used = False

    def identity(self):
        require(self.owner.process is self.creator.process and self.owner.process is not None
                and self.owner.process_identity is not None and self.owner.process.poll() is None,
                '主窗发现必须属于本轮创建的存活原Popen')
        row = self.creator.inspect_created(self.owner.process)
        require(row == self.owner.process_identity, '主窗发现前后原Popen/句柄身份改变')
        return row

    async def run(self, *, loaded):
        self.ledger.desktop_allowed()
        require(self.enabled and not self.used and self.owner.identity is None and type(loaded) is bool
                and self.uia is not None, '主窗发现禁用、重复、已绑定或载图阶段未知')
        self.used = True
        info = self.identity()
        require(self.api.desktop() == 'Default', '主窗发现输入桌面未知')
        foreground = self.api.foreground()
        handles = self.api.enumerate(info['pid'])
        require(handles and len(handles) == len(set(handles)), '产品可见窗口集合为空或重复')
        title = self.policy.title(False) if loaded else 'PT Renew · 内存编辑 · 不支持保存' + EXPERIMENT_SUFFIX
        raw = {hwnd: self.api.window(hwnd) for hwnd in handles}
        require(all(row['pid'] == info['pid'] and row['visible'] is True for row in raw.values()),
                '可见窗口枚举过程中PID/可见性改变')
        matches = [row for row in raw.values() if row['owner'] == 0 and row['cls'] == QT_CLASS and row['title'] == title]
        require(len(matches) == 1, '主窗必须为唯一精确标题/Qt类/无owner窗口')
        main = matches[0]
        require(main['hwnd'] == foreground and main['enabled'] is True and len(handles) == 1,
                '初始前景不是唯一产品主窗，或已出现文件框/owned窗口')
        geometry = self.api.geometry(main['hwnd'])
        rect = geometry.get('rect', [])
        require(geometry.get('coordinate_space') == 'physical-desktop-pixels'
                and geometry.get('thread_context_restored') is True and len(rect) == 4
                and all(type(x) is int for x in rect) and rect[0] < rect[2] and rect[1] < rect[3],
                '初始主窗物理矩形或DPI恢复未知')
        uia = await query_uia(self.uia, main['hwnd'], info['pid'])
        self.ledger.desktop_allowed()
        root = uia.get('root', {})
        require(uia.get('readonly') is True and root.get('pid') == info['pid'] and root.get('hwnd') == main['hwnd']
                and root.get('name') == title and root.get('cls') == QT_CLASS
                and root.get('automation_id') == 'mainWindow' and root.get('enabled') is True
                and root.get('control_type') == 50032 and uia.get('modal') is False,
                '首次主窗UIA身份/objectName/类型/模态状态不符')
        require(self.api.desktop() == 'Default' and self.api.foreground() == foreground
                and self.api.enumerate(info['pid']) == handles
                and all(self.api.window(hwnd) == raw[hwnd] for hwnd in handles)
                and self.api.geometry(main['hwnd']) == geometry, '首次主窗发现过程中前景/窗口/物理rect改变')
        self.identity()
        self.ledger.desktop_allowed()
        identity = self.owner.bind_main(main['hwnd'])
        self.ledger.event('main_window_discovered', identity=info, hwnd=identity.hwnd, loaded=loaded,
                          native=main, geometry=geometry, uia=uia, input_calls=0)
        return identity
