"""一次菜单动作的短时只读采样候选；导入不加载 Win32，不发送输入或截图。"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import datetime
import json
import sys
import time


class GuiThreadInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
                *[(name, wintypes.HWND) for name in
                  ("hwndActive", "hwndFocus", "hwndCapture", "hwndMenuOwner",
                   "hwndMoveSize", "hwndCaret")], ("rcCaret", wintypes.RECT)]


# 仅列只读 API；句柄／DPI 上下文必须按指针宽度绑定，POINT 按值传入。
SIGNATURES = {
    "GetForegroundWindow": ([], wintypes.HWND),
    "GetCursorPos": ([ctypes.POINTER(wintypes.POINT)], wintypes.BOOL),
    "GetPhysicalCursorPos": ([ctypes.POINTER(wintypes.POINT)], wintypes.BOOL),
    "WindowFromPoint": ([wintypes.POINT], wintypes.HWND),
    "WindowFromPhysicalPoint": ([wintypes.POINT], wintypes.HWND),
    "GetWindowThreadProcessId": ([wintypes.HWND, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD),
    "GetWindowRect": ([wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL),
    "GetGUIThreadInfo": ([wintypes.DWORD, ctypes.POINTER(GuiThreadInfo)], wintypes.BOOL),
    "GetThreadDpiAwarenessContext": ([], ctypes.c_void_p),
    "GetWindowDpiAwarenessContext": ([wintypes.HWND], ctypes.c_void_p),
    "GetAwarenessFromDpiAwarenessContext": ([ctypes.c_void_p], ctypes.c_int),
    "GetDpiForWindow": ([wintypes.HWND], wintypes.UINT),
}


def bind(user):
    for name, (args, result) in SIGNATURES.items():
        function = getattr(user, name)
        function.argtypes, function.restype = args, result
    return user


class Observer:
    def __init__(self, user=None, *, clock=time.perf_counter_ns, last_error=None,
                 cancelled=lambda: False):
        if user is None:
            if sys.platform != "win32":
                raise RuntimeError("只读原生采样仅支持 Windows")
            user = bind(ctypes.WinDLL("user32", use_last_error=True))
        self.user = user
        self.clock = clock
        self.last_error = last_error or ctypes.get_last_error
        self.cancelled = cancelled

    def call(self, name, *args, convert=lambda value: value, failed=lambda value: False,
             error_defined=False):
        if name not in SIGNATURES:
            raise ValueError("拒绝非只读采样 API")
        if self.cancelled():
            raise InterruptedError("已取消采样，不再启动新 Win32 查询")
        start = self.clock()
        raw = getattr(self.user, name)(*args)
        # 只有文档定义失败返回值和 GetLastError 的调用才读取错误码。
        error = self.last_error() if failed(raw) and error_defined else None
        return {"api": name, "start_ns": start, "end_ns": self.clock(),
                "value": convert(raw), "failed": bool(failed(raw)), "win32_error": error}

    def point(self, name):
        point = wintypes.POINT()
        row = self.call(name, ctypes.byref(point), failed=lambda value: not value,
                        error_defined=True, convert=bool)
        row["point"] = [point.x, point.y] if not row["failed"] else None
        return row

    def window(self, hwnd):
        pid = wintypes.DWORD()
        identity = self.call("GetWindowThreadProcessId", hwnd, ctypes.byref(pid),
                             failed=lambda value: not value, error_defined=True)
        rect = wintypes.RECT()
        bounds = self.call("GetWindowRect", hwnd, ctypes.byref(rect), convert=bool,
                           failed=lambda value: not value, error_defined=True)
        bounds["rect_observer_context"] = (None if bounds["failed"] else
                                          [rect.left, rect.top, rect.right, rect.bottom])
        context = self.call("GetWindowDpiAwarenessContext", hwnd,
                            failed=lambda value: not value)
        awareness = (None if context["failed"] else self.call(
            "GetAwarenessFromDpiAwarenessContext", context["value"],
            failed=lambda value: value == -1))
        dpi = self.call("GetDpiForWindow", hwnd, failed=lambda value: not value)
        return {"hwnd": hwnd, "identity": identity,
                "pid": None if identity["failed"] else pid.value,
                "rect": bounds, "dpi_context": context, "awareness": awareness, "dpi": dpi}

    def sample(self, windows, request_point):
        start = self.clock()
        context = self.call("GetThreadDpiAwarenessContext", failed=lambda value: not value)
        awareness = (None if context["failed"] else self.call(
            "GetAwarenessFromDpiAwarenessContext", context["value"],
            failed=lambda value: value == -1))
        foreground = self.call("GetForegroundWindow")
        logical = self.point("GetCursorPos")
        physical = self.point("GetPhysicalCursorPos")
        hits = []
        # 请求点只能假设为物理屏幕点，不能冒称服务线程已采用相同坐标空间。
        points = [("request_assumed_physical", "WindowFromPhysicalPoint", request_point),
                  ("cursor_physical", "WindowFromPhysicalPoint", physical["point"]),
                  ("cursor_observer_logical", "WindowFromPoint", logical["point"])]
        for source, api, point in points:
            if point is not None:
                hit = self.call(api, wintypes.POINT(*point))
                hits.append({"source": source, "point": list(point), "query": hit})
        handles = dict.fromkeys([*windows, foreground["value"],
                                 *(hit["query"]["value"] for hit in hits)])
        info = [self.window(hwnd) for hwnd in handles if hwnd]
        fg_info = next((row for row in info if row["hwnd"] == foreground["value"]), None)
        gui = None
        if fg_info and not fg_info["identity"]["failed"]:
            value = GuiThreadInfo(cbSize=ctypes.sizeof(GuiThreadInfo))
            gui = self.call("GetGUIThreadInfo", fg_info["identity"]["value"], ctypes.byref(value),
                            convert=bool, failed=lambda result: not result, error_defined=True)
            gui["state"] = None if gui["failed"] else {
                "flags": value.flags, "active": value.hwndActive, "focus": value.hwndFocus,
                "capture": value.hwndCapture, "menu_owner": value.hwndMenuOwner}
        after = self.call("GetForegroundWindow")
        return {"start_ns": start, "end_ns": self.clock(), "observer_dpi_context": context,
                "observer_awareness": awareness, "foreground_before": foreground,
                "foreground_after": after, "logical_cursor": logical, "physical_cursor": physical,
                "hit_predictions": hits, "windows": info, "foreground_gui": gui,
                "runtime_verified": False}


def validate(windows, request_point, duration, interval):
    if not 0 < duration <= 3 or not 0.005 <= interval <= 1:
        raise ValueError("采样预算须为 0–3 秒，间隔须为 0.005–1 秒")
    if not 1 <= len(windows) <= 3 or any(type(hwnd) is not int or hwnd <= 0 for hwnd in windows):
        raise ValueError("只接受 1–3 个已核验的正窗口句柄")
    if len(request_point) != 2 or any(type(v) is not int or not -(2**31) <= v < 2**31 for v in request_point):
        raise ValueError("请求点须为两个有符号 32 位整数")


def sample_for(observer, windows, request_point, duration, interval, emit, *,
               clock=time.perf_counter_ns, sleep=time.sleep, stop=lambda: False):
    """串行查询不是原子快照；记录每次调用时间，不补造错过的采样。"""
    validate(windows, request_point, duration, interval)
    start = clock()
    deadline = start + int(duration * 1e9)
    count = 0
    while not stop() and clock() < deadline:
        sample = observer.sample(windows, request_point)
        sample["sequence"] = count
        emit(sample)
        count += 1
        # 不追赶积压，也不承诺阻塞中的 Win32 调用可被此截止打断。
        remaining = deadline - clock()
        if remaining > 0:
            sleep(min(interval, remaining / 1e9))
    return {"samples": count, "start_ns": start, "end_ns": clock(),
            "deadline_ns": deadline, "runtime_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observe-readonly", action="store_true", help="明确启用真实只读查询；不是现场授权")
    parser.add_argument("--window", type=lambda value: int(value, 0), action="append", required=True)
    parser.add_argument("--point", nargs=2, type=int, required=True, help="仅假设为物理屏幕请求点")
    parser.add_argument("--duration", type=float, default=2)
    parser.add_argument("--interval", type=float, default=0.01)
    parser.add_argument("--output", required=True, help="新建 JSONL；拒绝覆盖")
    args = parser.parse_args()
    if not args.observe_readonly:
        parser.error("默认不查询桌面；真实使用须显式 --observe-readonly 并另行满足现场约束")
    # 先验证参数和输出排他性，再加载 Win32；与真实采样共用校验。
    validate(args.window, args.point, args.duration, args.interval)
    with open(args.output, "x", encoding="utf-8") as output:
        def emit(row):
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
        anchor_before = time.perf_counter_ns()
        utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        anchor_after = time.perf_counter_ns()
        emit({"kind": "header", "utc": utc, "utc_anchor_ns": [anchor_before, anchor_after],
              "clock": "perf_counter_ns", "windows": args.window, "request_point": args.point,
              "duration": args.duration, "interval": args.interval,
              "note": "候选未实机验证；命中预测不是接收者，未观测服务 API 返回或输入线程"})
        observer = Observer()
        result = sample_for(observer, args.window, args.point, args.duration, args.interval, emit)
        emit({"kind": "end", **result})


if __name__ == "__main__":
    main()
