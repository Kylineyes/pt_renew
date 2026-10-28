"""为批准的新隔离进程细分指示层位图上传耗时；安装本身不调用桌面。"""
from __future__ import annotations

import functools
import threading
import time


class _ApiView:
    """仅替换目标模块持有的引用，不改共享ctypes/WinDLL对象。"""

    def __init__(self, original, replacements):
        self.original = original
        self.replacements = replacements

    def __getattr__(self, name):
        if name in self.replacements:
            return self.replacements[name]
        return getattr(self.original, name)


def install_bitmap_timing(flash, trace, *, clock=time.perf_counter):
    """只记录指示层线程的一次完整上传；其他线程继续调用原函数。"""
    if getattr(flash, '_pt_bitmap_timing_installed', False):
        raise RuntimeError('位图上传计时不可重复安装')
    local = threading.local()
    groups = {
        '_user32': ('GetDC', 'UpdateLayeredWindow', 'ReleaseDC'),
        '_gdi32': ('CreateCompatibleDC', 'CreateDIBSection', 'SelectObject', 'DeleteObject', 'DeleteDC'),
        'ctypes': ('memmove',),
    }
    views = {}

    def measure(original, name):
        @functools.wraps(original)
        def call(*args, **kwargs):
            active = getattr(local, 'active', None)
            if active is None:
                return original(*args, **kwargs)
            started = clock()
            try:
                return original(*args, **kwargs)
            finally:
                duration = clock()-started
                item = active.setdefault(name, dict(calls=0, duration_seconds=0.0))
                item['calls'] += 1
                item['duration_seconds'] += duration
        return call

    # 先核对所有入口，缺失则安装前失败，避免一半引用已替换。
    for attribute, names in groups.items():
        original = getattr(flash, attribute)
        replacements = {name:measure(getattr(original, name), name) for name in names}
        views[attribute] = _ApiView(original, replacements)
    original_push = flash._push_bitmap

    @functools.wraps(original_push)
    def push(hwnd, x, y, w, h, bgra, *, opacity=255):
        if threading.current_thread().name != 'windows-mcp-control-indicator':
            return original_push(hwnd, x, y, w, h, bgra, opacity=opacity)
        # 不记录HWND、坐标、像素内容或输入值，只记录尺寸与成本。
        previous = getattr(local, 'active', None)
        stages = {}
        local.active = stages
        started = clock()
        exception = None
        try:
            return original_push(hwnd, x, y, w, h, bgra, opacity=opacity)
        except BaseException as error:
            exception = type(error).__name__
            raise
        finally:
            duration = clock()-started
            local.active = previous
            measured = sum(row['duration_seconds'] for row in stages.values())
            trace.emit('indicator-bitmap-upload', width=w, height=h, bgra_bytes=len(bgra),
                       duration_seconds=duration, measured_api_seconds=measured,
                       outside_api_seconds=duration-measured, stages=stages, exception=exception)

    for attribute, view in views.items():
        setattr(flash, attribute, view)
    flash._push_bitmap = push
    flash._pt_bitmap_timing_installed = True
    trace.emit('indicator-bitmap-timing-installed', schema_version=1,
               scope='windows-mcp-control-indicator', pixel_contents_recorded=False)
