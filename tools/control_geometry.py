"""在临时线程DPI上下文读取物理窗口矩形，不激活或修改窗口。"""
from __future__ import annotations
import ctypes
from ctypes import wintypes


def physical_window_rect(hwnd: int, user32=None):
    """GetWindowRect不受当前进程DPI虚拟化影响；任何未知状态拒绝返回。"""
    if not isinstance(hwnd,int) or isinstance(hwnd,bool) or hwnd<=0:
        raise ValueError('只接受已核验的正窗口句柄')
    native=user32 is None
    user32=user32 or ctypes.WinDLL('user32',use_last_error=True)
    if native:
        user32.SetThreadDpiAwarenessContext.argtypes=[ctypes.c_void_p]
        user32.SetThreadDpiAwarenessContext.restype=ctypes.c_void_p
        user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
        user32.GetWindowRect.restype=wintypes.BOOL
    previous=user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
    if not previous:
        raise RuntimeError('无法进入PER_MONITOR_AWARE_V2，物理矩形未知')
    try:
        rect=wintypes.RECT()
        if not user32.GetWindowRect(hwnd,ctypes.byref(rect)):
            raise RuntimeError('物理窗口矩形读取失败')
        result=[rect.left,rect.top,rect.right,rect.bottom]
        if result[2]<=result[0] or result[3]<=result[1]:
            raise RuntimeError('物理窗口矩形无效')
    finally:
        if not user32.SetThreadDpiAwarenessContext(previous):
            raise RuntimeError('无法恢复原线程DPI上下文')
    return dict(rect=result,coordinate_space='physical-desktop-pixels',
                dpi_context='PER_MONITOR_AWARE_V2',thread_context_restored=True)
