"""后端注入的不可变图层资源寿命核心；模块本身不加载Win32或安装运行时包装。"""
from __future__ import annotations

import threading


class BitmapSurfaceModel:
    """后端失败须抛异常；保留部分结果，统一所有权、上传及退役顺序。"""

    def __init__(self, api, width, height, pixels, *, target, owner_id=threading.get_ident):
        if (type(width) is not int or type(height) is not int or width <= 0 or height <= 0
                or width > 2147483647 or height > 2147483647
                or type(pixels) is not bytes or len(pixels) != width*height*4):
            raise ValueError('不可变图层的尺寸或BGRA字节数无效')
        self.api = api
        self.target = target
        self.width, self.height = width, height
        self._owner_id = owner_id
        self.owner = owner_id()
        self.memory = self.bitmap = self.screen = self.original = None
        self.selected = False
        self.state = 'initializing'
        try:
            self.screen = api.acquire_screen()
            self.memory = api.create_memory(self.screen)
            self.bitmap, bits = api.create_bitmap(self.screen, width, height)
            if bits is None:
                # DIB句柄成功但像素指针为空时，句柄已归本实例，仍需正常退役。
                raise OSError('CreateDIBSection返回空像素指针')
            self.original = api.select(self.memory, self.bitmap)
            self.selected = True
            api.copy(bits, pixels)
            api.release_screen(self.screen)
            self.screen = None
            self.state = 'ready'
        except BaseException as error:
            self._retire_after_failure(error)

    def _check_owner(self):
        if self._owner_id() != self.owner:
            raise RuntimeError('位图资源必须由创建线程使用和释放')

    def _retire_after_failure(self, original):
        self.state = 'failed'
        try:
            self.close()
        except BaseException as cleanup:
            failure = BaseExceptionGroup('位图实验失败，退役仍有异常', [original, cleanup])
            # 构造尚未返回时也必须让调用者取回资源，不能只把句柄留在局部对象。
            failure.pending_surface = self
            raise failure from None
        raise original

    def present(self, x, y, opacity):
        """保留每次GetDC/ReleaseDC及完整上传；不写心跳或显示确认。"""
        self._check_owner()
        if self.state != 'ready':
            raise RuntimeError('已失败或退役的位图资源不可继续上传')
        if type(opacity) is not int or not 0 <= opacity <= 255:
            raise ValueError('透明度必须为0至255的整数')
        try:
            self.screen = self.api.acquire_screen()
            self.api.update(self.target, self.screen, self.memory, self.width, self.height, x, y, opacity)
            self.api.release_screen(self.screen)
            self.screen = None
        except BaseException as error:
            self._retire_after_failure(error)

    def close(self):
        """尽量释放全部可独立释放的资源；失败保留句柄，允许所属线程重试退役。"""
        self._check_owner()
        if self.state == 'closed':
            return
        self.state = 'failed'
        errors = []

        def attempt(action):
            try:
                action()
                return True
            except BaseException as error:
                errors.append(error)
                return False

        if self.selected:
            if attempt(lambda: self.api.select(self.memory, self.original)):
                self.selected = False
        # 恢复选择失败时先删除DC解除选择，不能直接删除仍被选中的位图。
        if self.memory is not None and attempt(lambda: self.api.delete_memory(self.memory)):
            self.memory = None
            self.selected = False
        if self.bitmap is not None and not self.selected:
            if attempt(lambda: self.api.delete_bitmap(self.bitmap)):
                self.bitmap = None
        if self.screen is not None and attempt(lambda: self.api.release_screen(self.screen)):
            self.screen = None
        if errors:
            failure = BaseExceptionGroup('位图资源退役失败，剩余句柄保留', errors)
            failure.pending_surface = self
            raise failure
        self.state = 'closed'
