"""单次受限子进程完成整窗观察；父原Popen证明与子查询句柄证据明确区分。"""
from __future__ import annotations

import os

from .core import positive, require


def validate_observation(row, identity):
    require(isinstance(row, dict) and row.get('input_desktop') == 'Default' and row.get('locked') is False
            and row.get('foreground_stable') is True, '整窗观察桌面/前景状态未知')
    windows = row.get('windows')
    require(isinstance(windows, list) and 1 <= len(windows) <= 2, '整窗观察必须仅含主窗及至多一个owned窗口')
    handles = []
    for window in windows:
        require(isinstance(window, dict) and positive(window.get('hwnd')) and window['hwnd'] not in handles
                and window.get('pid') == identity.pid and window.get('birth') == identity.birth
                and str(window.get('image', '')).casefold() == identity.image.casefold()
                and type(window.get('enabled')) is bool and window.get('visible') is True,
                '整窗观察窗口身份/启用/可见性无效')
        handles.append(window['hwnd'])
        rect = window.get('rect')
        require(window.get('coordinate_space') == 'physical-desktop-pixels'
                and window.get('thread_context_restored') is True and isinstance(rect, list) and len(rect) == 4
                and all(type(x) is int for x in rect) and rect[0] < rect[2] and rect[1] < rect[3], '整窗观察物理rect/DPI恢复未知')
        require(isinstance(window.get('title'), str) and isinstance(window.get('cls'), str)
                and window['cls'] and window.get('focus_kind') in ('canvas', 'text', 'unknown'), '整窗观察字段无效')
        if window['hwnd'] == identity.hwnd:
            require(window.get('owner') == 0 and window['cls'] == 'Qt6120QWindowIcon', '原主HWND/owner/Qt类改变')
        else:
            require(window.get('owner') == identity.hwnd, '额外窗口不属于原主HWND')
    require(identity.hwnd in handles and row.get('foreground') in windows,
            '整窗观察缺少精确主HWND或前景不属于窗口集合')
    if len(windows) == 2:
        main = next(w for w in windows if w['hwnd'] == identity.hwnd)
        require(main['enabled'] is False and row['foreground']['hwnd'] != identity.hwnd,
                'owned窗口出现时主窗必须禁用且模态为前景')
    return row


class BatchProductNative:
    def __init__(self, ledger, owner, creator, probe, *, enabled=False):
        require(probe.ledger is ledger and probe.owner is owner and probe.creator is creator,
                '批量观察必须共享原客户端/产品/探针')
        self.ledger, self.owner, self.creator, self.probe = ledger, owner, creator, probe
        self.enabled = enabled is True
        self.observations = []

    def identity(self):
        self.owner.alive()
        require(self.owner.process is self.creator.process
                and self.creator.inspect_created(self.owner.process) == self.owner.process_identity,
                '整窗观察前后原Popen/创建句柄身份改变')
        return self.owner.identity

    async def __call__(self):
        self.ledger.desktop_allowed()
        require(self.enabled, '批量整窗观察默认禁用')
        identity = self.identity()
        row = await self.probe.observe()
        self.ledger.desktop_allowed()
        require(self.identity() == identity, '整窗观察期间原产品身份改变')
        validate_observation(row, identity)
        self.observations.append(row)
        self.ledger.event('batch_native_observation', result=row, original_popen_verified=True,
                          child_queries_per_observation=1)
        return row


class TargetQueryHandle:
    """子进程查询句柄仅支持在途birth/image核对；从不替代父保存的原Popen。"""

    def __init__(self, target):
        self.target, self.kernel, self.handle = target, None, None

    def __enter__(self):
        import ctypes
        from ctypes import wintypes
        require(os.name == 'nt', '目标查询仅支持Windows')
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'OpenProcess': (wintypes.HANDLE, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]),
            'GetProcessId': (wintypes.DWORD, [wintypes.HANDLE]),
            'GetProcessTimes': (wintypes.BOOL, [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4),
            'QueryFullProcessImageNameW': (wintypes.BOOL, [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                        ctypes.POINTER(wintypes.DWORD)]),
            'WaitForSingleObject': (wintypes.DWORD, [wintypes.HANDLE, wintypes.DWORD]),
            'CloseHandle': (wintypes.BOOL, [wintypes.HANDLE])}
        for name, (result, args) in signatures.items():
            function = getattr(kernel, name); function.restype, function.argtypes = result, args
        self.kernel = kernel
        self.handle = kernel.OpenProcess(0x100000 | 0x1000, False, self.target['pid'])
        require(bool(self.handle), '子进程无法查询原目标')
        try: self.verify()
        except BaseException:
            self.__exit__(None, None, None); raise
        return self

    def verify(self):
        import ctypes
        from ctypes import wintypes
        require(self.handle and self.kernel.WaitForSingleObject(self.handle, 0) == 258
                and self.kernel.GetProcessId(self.handle) == self.target['pid'], '子观察期间目标已退出或PID不同')
        times = [wintypes.FILETIME() for _ in range(4)]
        require(bool(self.kernel.GetProcessTimes(self.handle, *(ctypes.byref(v) for v in times))), '子查询birth失败')
        birth = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        buf = ctypes.create_unicode_buffer(32768); size = wintypes.DWORD(len(buf))
        require(bool(self.kernel.QueryFullProcessImageNameW(self.handle, 0, buf, ctypes.byref(size)))
                and birth == self.target['birth'] and buf.value.casefold() == self.target['image'].casefold(),
                '子查询birth/image与父冻结目标不同')

    def __exit__(self, *args):
        if self.handle:
            handle, self.handle = self.handle, None
            require(bool(self.kernel.CloseHandle(handle)), '子目标查询句柄清理失败')
