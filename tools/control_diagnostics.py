"""为独立控制工具副本附加只读诊断；不改控制判定、输入或心跳阈值。"""
from __future__ import annotations

import collections
import functools
import inspect
import json
import os
from pathlib import Path
import threading
import time


class TraceWriter:
    """钩子线程只向有界队列追加；磁盘写入由独立线程处理。"""

    def __init__(self, path: Path, capacity: int = 4096):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open('x', encoding='utf-8')
        self.rows = collections.deque(maxlen=capacity)
        self.capacity = capacity
        self.dropped = 0
        self.error = None
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, name='pt-control-trace', daemon=True)
        self.thread.start()

    def emit(self, event: str, **fields):
        if len(self.rows) == self.capacity:
            self.dropped += 1
        self.rows.append(dict(event=event, monotonic=time.monotonic(), wall=time.time(),
                              thread=threading.current_thread().name, **fields))

    def _drain(self):
        while True:
            try:
                row = self.rows.popleft()
            except IndexError:
                break
            self.stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        self.stream.flush()

    def _run(self):
        try:
            while not self.stop.wait(.05):
                self._drain()
            self._drain()
        except Exception as error:
            self.error = type(error).__name__ + ': ' + str(error)

    def close(self):
        self.stop.set()
        self.thread.join(2)
        if self.thread.is_alive():
            raise RuntimeError('诊断记录线程未退出')
        if not self.error:
            self.stream.write(json.dumps(dict(event='trace-closed', dropped=self.dropped,
                                              monotonic=time.monotonic()), ensure_ascii=False) + '\n')
        self.stream.close()
        if self.error:
            raise RuntimeError('诊断日志写入失败：' + self.error)


def controller_fields(owner, overlay=None):
    """非原子允许字段快照，不调用status、不校准集合、不读取键入内容。"""
    now = time.monotonic()
    names = ['_state', '_generation', '_active_calls', '_suppress', '_visual_armed',
             '_visual_paused', '_rotating', '_fast_pending', '_fast_takeover', '_emergency']
    result = {name.lstrip('_'): getattr(owner, name, None) for name in names}
    for name in ['_thread_beat', '_last_physical_event', '_last_user']:
        value = getattr(owner, name, 0.)
        result[name.lstrip('_') + '_age_seconds'] = now - value if value else None
    for name in ['_pressed', '_mouse_down', '_delivered_keys', '_delivered_mouse']:
        result[name.lstrip('_') + '_count'] = len(getattr(owner, name, ()))
    result.update({
        'monitor_alive': bool(getattr(owner, '_thread', None) and owner._thread.is_alive()),
        'monitor_stopping': bool(getattr(owner, '_stop', None) and owner._stop.is_set()),
    })
    indicator = getattr(overlay, '_instance', None)
    if indicator is not None:
        result['indicator'] = dict(heartbeat_age_seconds=now-indicator.heartbeat,
                                  alive=indicator.thread.is_alive(), active=indicator.active,
                                  pending=indicator.pending, suspended=indicator.suspended,
                                  version=indicator.version, applied=indicator.applied,
                                  stopping=indicator.stopping,
                                  error=type(indicator.error).__name__ if indicator.error else None)
    return result


def install(control, overlay, service, uia_core, trace: TraceWriter):
    """所有包装均调用原实现且原样传播异常；只附加阶段/原因字段和日志。"""
    cls = control.ControlCoordinator
    if getattr(cls, '_pt_diagnostics_installed', False):
        raise RuntimeError('同一诊断进程禁止重复安装')
    cls._pt_diagnostics_installed = True
    owner = control.get_controller()

    def record(event, obj=owner, **fields):
        trace.emit(event, control=controller_fields(obj, overlay), **fields)

    def wrap(name, event=None, detail=None):
        original = getattr(cls, name)

        @functools.wraps(original)
        def run(obj, *args, **kwargs):
            label = event or name.lstrip('_')
            extra = detail(args, kwargs) if detail else {}
            record(label+'-enter', obj, **extra)
            try:
                result = original(obj, *args, **kwargs)
            except BaseException as error:
                record(label+'-error', obj, exception=type(error).__name__,
                       code=getattr(error, 'code', None), **extra)
                raise
            record(label+'-return', obj, **extra)
            return result
        setattr(cls, name, run)

    wrap('begin_call', detail=lambda a,k:dict(tool=a[0]))
    wrap('end_call')
    wrap('pause_for_capture', 'capture-pause')
    wrap('resume_after_capture', 'capture-resume',
         lambda a,k:dict(capture_generation=a[0], restored=k.get('restored')))
    wrap('_recover_after_rehook', 'rehook-recovery')
    original_fail = cls._fail_open

    @functools.wraps(original_fail)
    def fail(obj, *args, **kwargs):
        # 保留调用点，不输出栈局部变量或用户文字。
        frame = inspect.currentframe()
        caller = frame.f_back
        try:
            source = dict(file=Path(caller.f_code.co_filename).name,
                          function=caller.f_code.co_name, line=caller.f_lineno)
            # 只保留看门狗已求值的布尔证据，不额外发起健康探测。
            probes = {key:caller.f_locals[key] for key in ('indicator_ok','desktop_ok')
                      if isinstance(caller.f_locals.get(key), bool)}
        finally:
            del caller, frame
        result = original_fail(obj, *args, **kwargs)
        record('fail-open', obj, source=source, probes=probes)
        return result
    cls._fail_open = fail
    original_set = cls._set_locked

    @functools.wraps(original_set)
    def set_state(obj, state):
        before = obj._state
        result = original_set(obj, state)
        if result:
            record('state-change', obj, before=before, after=state)
        return result
    cls._set_locked = set_state
    original_handle = cls._handle

    @functools.wraps(original_handle)
    def handle(obj, event):
        before = (obj._state, obj._generation)
        result = original_handle(obj, event)
        if event[0] != 'tick' or before != (obj._state, obj._generation):
            record('input-processed', obj, input_kind=event[0], before=list(before))
        return result
    cls._handle = handle

    for name, struct_name, injected_mask in [('_physical_mouse','_MouseHookData',1),
                                              ('_physical_key','_KeyHookData',0x10)]:
        original = getattr(cls, name)
        def make_callback(original, name, struct_name, injected_mask):
            @functools.wraps(original)
            def callback(obj, code, message, pointer):
                # 只记录低层来源标记和消息类别，不保存按键值/坐标/字符。
                if code >= 0:
                    import ctypes
                    data = ctypes.cast(pointer, ctypes.POINTER(getattr(control, struct_name))).contents
                    trace.emit('hook-event', kind=name, message=int(message),
                               flags=int(data.flags), injected=bool(data.flags & injected_mask),
                               physical_age_before=time.monotonic()-obj._last_physical_event)
                return original(obj, code, message, pointer)
            return callback
        setattr(cls, name, make_callback(original, name, struct_name, injected_mask))

    original_snapshot = cls._snapshot_locked
    @functools.wraps(original_snapshot)
    def snapshot(obj, now):
        result = original_snapshot(obj, now)
        # 错误回执也携带原因上下文，原state/generation/wait字段保持。
        result['diagnostics'] = controller_fields(obj, overlay)
        return result
    cls._snapshot_locked = snapshot

    original_capture = service.Desktop.get_screenshot
    @functools.wraps(original_capture)
    def capture(obj, *args, **kwargs):
        record('screenshot-enter')
        try:
            image = original_capture(obj, *args, **kwargs)
        except BaseException as error:
            record('screenshot-error', exception=type(error).__name__)
            raise
        record('screenshot-return', image_size=list(image.size))
        return image
    service.Desktop.get_screenshot = capture

    original_cursor = uia_core.SetCursorPos
    @functools.wraps(original_cursor)
    def cursor(*args, **kwargs):
        record('cursor-api-enter')
        try:
            return original_cursor(*args, **kwargs)
        finally:
            record('cursor-api-return')
    # uia包按值导出函数，二者同时包装才能覆盖service调用。
    uia_core.SetCursorPos = cursor
    import windows_mcp.uia as uia
    uia.SetCursorPos = cursor
    record('diagnostics-installed', pid=os.getpid(), control_source=str(Path(control.__file__).resolve()))
    return owner
