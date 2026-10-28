"""仅供批准的新隔离进程使用的不可变图层DC/DIB复用；导入本模块不调用Win32。"""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import functools
import threading
import time

from control_bitmap_surface_model import BitmapSurfaceModel

INDICATOR_THREAD = 'windows-mcp-control-indicator'
MAX_SURFACES = 64
MAX_BITMAP_BYTES = 64 * 1024 * 1024
SUPPORTED_SOURCES = {
    'desktop/control_overlay.py': 'e8101f7e5be97e7d902aa7872d09e8beba8225acb661201af9618cef6c53bc36',
    'desktop/flash_overlay.py': 'e9b326c99040fe5b481ae3c0f7dd014a798691143d5b2058ae184c524ab48695',
}


class NativeCallError(OSError):
    def __init__(self, api, code):
        super().__init__(code, '位图资源API失败：' + api)
        self.api = api
        self.native_error = code


class NativeBitmapApi:
    """私有WinDLL函数对象，成功后才记入/移出账本，失败句柄保持所有权。"""

    def __init__(self, flash, record, *, libraries=None, last_error=None, clock=time.perf_counter):
        self.flash, self.record, self.clock = flash, record, clock
        self.owner = threading.get_ident()
        if libraries is None:
            # 不使用ctypes.windll缓存，不改变原模块或进程共享函数的签名。
            libraries = (ctypes.WinDLL('user32', use_last_error=True),
                         ctypes.WinDLL('gdi32', use_last_error=True))
        self.user, self.gdi = libraries
        self.last_error = last_error or ctypes.get_last_error
        self.screens, self.memories, self.bitmaps = set(), {}, {}
        pointer = ctypes.POINTER
        signatures = {
            'GetDC': (self.user, wintypes.HDC, [wintypes.HWND]),
            'ReleaseDC': (self.user, ctypes.c_int, [wintypes.HWND, wintypes.HDC]),
            'CreateCompatibleDC': (self.gdi, wintypes.HDC, [wintypes.HDC]),
            'CreateDIBSection': (self.gdi, wintypes.HBITMAP,
                                 [wintypes.HDC, pointer(flash._BITMAPINFO), wintypes.UINT,
                                  pointer(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]),
            'SelectObject': (self.gdi, wintypes.HGDIOBJ, [wintypes.HDC, wintypes.HGDIOBJ]),
            'DeleteObject': (self.gdi, wintypes.BOOL, [wintypes.HGDIOBJ]),
            'DeleteDC': (self.gdi, wintypes.BOOL, [wintypes.HDC]),
            'UpdateLayeredWindow': (self.user, wintypes.BOOL,
                                    [wintypes.HWND, wintypes.HDC, pointer(flash._POINT), pointer(flash._SIZE),
                                     wintypes.HDC, pointer(flash._POINT), wintypes.COLORREF,
                                     pointer(flash._BLENDFUNCTION), wintypes.DWORD]),
        }
        self.functions = {}
        for name, (library, result, args) in signatures.items():
            function = getattr(library, name)
            function.restype, function.argtypes = result, args
            self.functions[name] = function

    def _invoke(self, name, *args):
        if threading.get_ident() != self.owner:
            raise RuntimeError('原生位图API必须在创建线程调用')
        started = self.clock()
        failed = False
        try:
            if name == 'memmove':
                return ctypes.memmove(*args)
            result = self.functions[name](*args)
            # 在计时、记录或下一次API之前保存原生错误码。
            if not result or (name == 'SelectObject' and result in (-1, ctypes.c_void_p(-1).value)):
                code = self.last_error()
                raise NativeCallError(name, code)
            return result
        except BaseException:
            failed = True
            raise
        finally:
            self.record(name, self.clock()-started, failed)

    def snapshot(self):
        return dict(screen_dc_count=len(self.screens), memory_dc_count=len(self.memories),
                    bitmap_count=len(self.bitmaps),
                    selected_bitmap_count=sum(value in self.bitmaps for value in tuple(self.memories.values())))

    def acquire_screen(self):
        screen = self._invoke('GetDC', None)
        self.screens.add(screen)
        return screen

    def release_screen(self, screen):
        if screen not in self.screens:
            raise RuntimeError('屏幕DC不属于当前图层')
        self._invoke('ReleaseDC', None, screen)
        self.screens.remove(screen)

    def create_memory(self, screen):
        if screen not in self.screens:
            raise RuntimeError('创建内存DC缺少所属屏幕DC')
        memory = self._invoke('CreateCompatibleDC', screen)
        self.memories[memory] = None
        return memory

    def delete_memory(self, memory):
        if memory not in self.memories:
            raise RuntimeError('内存DC不属于当前图层')
        self._invoke('DeleteDC', memory)
        del self.memories[memory]

    def create_bitmap(self, screen, width, height):
        if screen not in self.screens:
            raise RuntimeError('创建DIB缺少所属屏幕DC')
        info = self.flash._BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(self.flash._BITMAPINFOHEADER)
        info.bmiHeader.biWidth, info.bmiHeader.biHeight = width, -height
        info.bmiHeader.biPlanes, info.bmiHeader.biBitCount = 1, 32
        info.bmiHeader.biCompression = self.flash._BI_RGB
        bits = ctypes.c_void_p()
        bitmap = self._invoke('CreateDIBSection', screen, ctypes.byref(info),
                              self.flash._DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
        # 即使bits为空也先移交成功句柄，由寿命核心关闭，不在后端丢弃部分结果。
        self.bitmaps[bitmap] = (bits.value, width*height*4)
        return bitmap, bits.value

    def delete_bitmap(self, bitmap):
        if bitmap not in self.bitmaps or bitmap in self.memories.values():
            raise RuntimeError('不能删除未知或仍被选中的位图')
        self._invoke('DeleteObject', bitmap)
        del self.bitmaps[bitmap]

    def select(self, memory, bitmap):
        if memory not in self.memories:
            raise RuntimeError('选择位图的内存DC不属于当前图层')
        original = self._invoke('SelectObject', memory, bitmap)
        self.memories[memory] = bitmap
        return original

    def copy(self, bits, pixels):
        if bits is None or not any(pointer == bits and size == len(pixels)
                                   for pointer, size in self.bitmaps.values()):
            raise RuntimeError('像素指针或复制长度不属于当前DIB')
        self._invoke('memmove', bits, pixels, len(pixels))

    def update(self, target, screen, memory, width, height, x, y, opacity):
        if screen not in self.screens or self.memories.get(memory) not in self.bitmaps:
            raise RuntimeError('上传缺少当前图层的完整资源')
        pos, size, origin = self.flash._POINT(x, y), self.flash._SIZE(width, height), self.flash._POINT(0, 0)
        blend = self.flash._BLENDFUNCTION(self.flash._AC_SRC_OVER, 0, opacity, self.flash._AC_SRC_ALPHA)
        self._invoke('UpdateLayeredWindow', target, screen, ctypes.byref(pos), ctypes.byref(size), memory,
                     ctypes.byref(origin), 0, ctypes.byref(blend), self.flash._ULW_ALPHA)


class SurfaceManager:
    """强引用全部待退役图层，保守锁存失败；主线程只审计，释放仍由所属线程完成。"""

    def __init__(self, flash, trace, original_close, *, api_factory=NativeBitmapApi,
                 max_surfaces=MAX_SURFACES, max_bytes=MAX_BITMAP_BYTES):
        self.flash, self.trace, self.original_close = flash, trace, original_close
        self.api_factory, self.max_surfaces, self.max_bytes = api_factory, max_surfaces, max_bytes
        self.entries, self.next_id, self.failed = {}, 0, False

    def snapshot(self):
        entries = list(self.entries.values())
        counts = dict(screen_dc_count=0, memory_dc_count=0, bitmap_count=0, selected_bitmap_count=0)
        for entry in entries:
            if entry['api'] is not None:
                for name, value in entry['api'].snapshot().items():
                    counts[name] += value
        return dict(surfaces=len(entries), reserved_bytes=sum(e['size'] for e in entries),
                    failed=self.failed, **counts)

    @contextmanager
    def operation(self, entry, name):
        stages = {}
        entry['stages'] = stages
        started = time.perf_counter()
        error = None
        try:
            yield
        except BaseException as caught:
            self.failed = True
            error = type(caught).__name__
            raise
        finally:
            finished = time.perf_counter()
            entry['stages'] = None
            self.trace.emit('indicator-surface-operation', schema_version=1, surface_id=entry['id'],
                            operation=name, width=entry['width'], height=entry['height'], bgra_bytes=entry['size'],
                            started=started, finished=finished, duration_seconds=finished-started,
                            stages=stages, exception=error, resources=self.snapshot())

    def _entry(self, layer):
        entry = self.entries.get(id(layer))
        if entry is not None and entry['owner'] != threading.get_ident():
            raise RuntimeError('图层资源只能由创建线程使用或退役')
        return entry

    def upload(self, layer, target, x, y, width, height, pixels, opacity):
        entry = self._entry(layer)
        if (getattr(layer, '_pt_surface_retired', False) or type(target) is not int
                or target <= 0 or layer.hwnd != target):
            self.failed = True
            raise RuntimeError('目标图层已关闭或窗口身份无效，禁止重新分配资源')
        if self.failed:
            raise RuntimeError('资源实验已失败，禁止新建或继续上传')
        if entry is None:
            if (type(width) is not int or type(height) is not int or not 0 < width <= 2147483647
                    or not 0 < height <= 2147483647 or type(pixels) is not bytes or len(pixels) != width*height*4):
                self.failed = True
                raise ValueError('图层尺寸或不可变BGRA无效')
            if (len(self.entries) >= self.max_surfaces or
                    self.snapshot()['reserved_bytes']+len(pixels) > self.max_bytes):
                self.failed = True
                raise RuntimeError('图层资源实验超过冻结数量或字节预算')
            self.next_id += 1
            entry = dict(id=self.next_id, layer=layer, owner=threading.get_ident(), target=target,
                         width=width, height=height, pixels=pixels, size=len(pixels),
                         api=None, surface=None, stages=None)
            self.entries[id(layer)] = entry

            def record(name, duration, failed):
                stages = entry['stages']
                if stages is None:
                    raise RuntimeError('原生资源API不在完整操作记录范围内')
                stage = stages.setdefault(name, dict(calls=0, failures=0, duration_seconds=0.0))
                stage['calls'] += 1
                stage['failures'] += int(failed)
                stage['duration_seconds'] += duration

            with self.operation(entry, 'initialize'):
                entry['api'] = self.api_factory(self.flash, record)
                try:
                    entry['surface'] = BitmapSurfaceModel(entry['api'], width, height, pixels, target=target)
                except BaseException as error:
                    entry['surface'] = getattr(error, 'pending_surface', None)
                    raise
        if (entry['target'] != target or entry['width'] != width or entry['height'] != height
                or entry['pixels'] is not pixels):
            self.failed = True
            raise RuntimeError('图层身份、尺寸或像素变化，必须关闭并重建')
        with self.operation(entry, 'upload'):
            entry['surface'].present(x, y, opacity)

    def close_layer(self, layer):
        entry = self._entry(layer)
        if entry is None:
            result = self.original_close(layer)
            if hasattr(layer, '_pt_surface_owner'):
                layer._pt_surface_retired = True
            return result
        with self.operation(entry, 'retire'):
            if entry['surface'] is not None:
                entry['surface'].close()
            if entry['api'] is not None and any(entry['api'].snapshot().values()):
                raise RuntimeError('资源仍未释放，不能销毁所属窗口')
            if layer.hwnd != entry['target']:
                raise RuntimeError('图层窗口身份变化，禁止销毁其他窗口')
            self.original_close(layer)
            layer._pt_surface_retired = True
            del self.entries[id(layer)]

    def retire_owner(self):
        errors = []
        for entry in reversed(list(self.entries.values())):
            if entry['owner'] == threading.get_ident():
                try:
                    self.close_layer(entry['layer'])
                except BaseException as error:
                    errors.append(error)
        return errors

    def audit_shutdown(self):
        resources = self.snapshot()
        balanced = resources['surfaces'] == 0 and all(resources[key] == 0 for key in
                      ('screen_dc_count', 'memory_dc_count', 'bitmap_count', 'selected_bitmap_count', 'reserved_bytes'))
        self.trace.emit('indicator-surface-shutdown', balanced=balanced, resources=resources)
        if not balanced or self.failed:
            raise RuntimeError('图层资源实验失败或退役账本未清空，不能声明通过')
        return resources


def install_bitmap_surface(overlay, trace, *, api_factory=NativeBitmapApi,
                           max_surfaces=MAX_SURFACES, max_bytes=MAX_BITMAP_BYTES):
    """只在尚未启动的新进程安装；启动批准必须先核对原源码及全部模块摘要。"""
    flash = overlay.flash_overlay
    if getattr(overlay, '_pt_bitmap_surface_installed', False):
        raise RuntimeError('图层资源复用不可重复安装')
    if getattr(overlay, '_instance', None) is not None:
        raise RuntimeError('不能在已启动的指示层安装资源实验')
    if getattr(flash, '_pt_bitmap_timing_installed', False):
        raise RuntimeError('资源复用不能与旧位图计时同时安装')
    if type(max_surfaces) is not int or max_surfaces <= 0 or type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError('资源预算必须为正整数')
    layer_type, indicator_type = overlay._Layer, overlay._Indicator
    original_init, original_opacity, original_close = layer_type.__init__, layer_type.set_opacity, layer_type.close
    original_run, original_push = indicator_type._run, flash._push_bitmap
    manager = SurfaceManager(flash, trace, original_close, api_factory=api_factory,
                             max_surfaces=max_surfaces, max_bytes=max_bytes)
    local = threading.local()

    def context(method, *, initializing=False):
        @functools.wraps(method)
        def run(layer, *args, **kwargs):
            managed = hasattr(layer, '_pt_surface_owner')
            if initializing and managed:
                raise RuntimeError('已绑定图层不能重新初始化')
            if initializing and threading.current_thread().name == INDICATOR_THREAD:
                layer._pt_surface_owner = threading.get_ident()
                managed = True
            if not managed:
                return method(layer, *args, **kwargs)
            if layer._pt_surface_owner != threading.get_ident():
                raise RuntimeError('图层只能由创建线程操作')
            previous = getattr(local, 'layer', None)
            if previous is not None:
                raise RuntimeError('资源实验不接受嵌套图层上传')
            local.layer = layer
            try:
                return method(layer, *args, **kwargs)
            finally:
                local.layer = previous
        return run

    @functools.wraps(original_push)
    def push(target, x, y, width, height, pixels, *, opacity=255):
        layer = getattr(local, 'layer', None)
        if layer is None:
            return original_push(target, x, y, width, height, pixels, opacity=opacity)
        return manager.upload(layer, target, x, y, width, height, pixels, opacity)

    @functools.wraps(original_run)
    def owner_run(indicator):
        def latch(error):
            with indicator.condition:
                if indicator.error is None:
                    indicator.error = error
                indicator.condition.notify_all()
        try:
            return original_run(indicator)
        except BaseException as error:
            manager.failed = True
            latch(error)
            raise
        finally:
            errors = manager.retire_owner()
            if errors:
                latch(BaseExceptionGroup('显示线程退出时仍有图层未退役', errors))
            elif manager.failed:
                latch(RuntimeError('图层资源实验曾失败，保持故障状态'))
            trace.emit('indicator-surface-owner-exit', resources=manager.snapshot(),
                       cleanup_errors=len(errors))

    def close(layer):
        if (hasattr(layer, '_pt_surface_owner') and
                layer._pt_surface_owner != threading.get_ident()):
            raise RuntimeError('图层只能由创建线程退役')
        if getattr(layer, '_pt_surface_retired', False):
            return
        return manager.close_layer(layer)

    layer_type.__init__ = context(original_init, initializing=True)
    layer_type.set_opacity = context(original_opacity)
    layer_type.close = close
    indicator_type._run = owner_run
    flash._push_bitmap = push
    overlay._pt_bitmap_surface_installed = True
    overlay._pt_bitmap_surface_manager = manager
    trace.emit('indicator-surface-installed', schema_version=1, max_surfaces=max_surfaces,
               max_bitmap_bytes=max_bytes, scope=INDICATOR_THREAD, runtime_verified=False)
    return manager
