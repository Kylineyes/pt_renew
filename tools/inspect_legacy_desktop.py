"""只读记录 Windows 前景窗口、可见顶层窗口及进程归属，不发送输入或改变焦点。"""

import argparse
import ctypes
from ctypes import wintypes
import datetime
import json
import os
import sys


def inspect_desktop():
    if sys.platform != "win32":
        raise RuntimeError("此工具只支持 Windows")
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    user.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user.IsWindowVisible.argtypes = [wintypes.HWND]
    user.IsIconic.argtypes = [wintypes.HWND]
    user.GetThreadDesktop.argtypes = [wintypes.DWORD]
    user.GetThreadDesktop.restype = wintypes.HANDLE
    user.GetProcessWindowStation.restype = wintypes.HANDLE
    user.GetUserObjectInformationW.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]

    def object_name(handle):
        buf = ctypes.create_unicode_buffer(512)
        needed = wintypes.DWORD()
        if user.GetUserObjectInformationW(handle, 2, buf, ctypes.sizeof(buf), ctypes.byref(needed)):
            return buf.value
        return {"error": ctypes.get_last_error()}

    def process_info(pid):
        session = wintypes.DWORD()
        info = {"pid": pid}
        if kernel.ProcessIdToSessionId(pid, ctypes.byref(session)):
            info["session_id"] = session.value
        else:
            info["session_error"] = ctypes.get_last_error()
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            info["image_error"] = ctypes.get_last_error()
            return info
        try:
            buf = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buf))
            if kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                info["image"] = buf.value
            else:
                info["image_error"] = ctypes.get_last_error()
        finally:
            kernel.CloseHandle(handle)
        return info

    def window_info(hwnd):
        pid = wintypes.DWORD()
        thread = user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        title = ctypes.create_unicode_buffer(user.GetWindowTextLengthW(hwnd) + 1)
        user.GetWindowTextW(hwnd, title, len(title))
        cls = ctypes.create_unicode_buffer(256)
        user.GetClassNameW(hwnd, cls, len(cls))
        rect = wintypes.RECT()
        valid_rect = user.GetWindowRect(hwnd, ctypes.byref(rect))
        return {
            "hwnd": int(hwnd), "title": title.value, "class": cls.value,
            "thread_id": thread, "process": process_info(pid.value),
            "visible": bool(user.IsWindowVisible(hwnd)), "minimized": bool(user.IsIconic(hwnd)),
            "rect": [rect.left, rect.top, rect.right, rect.bottom] if valid_rect else None,
        }

    windows = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def collect(hwnd, _):
        if user.IsWindowVisible(hwnd):
            windows.append(window_info(hwnd))
        return True

    user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    foreground_before = user.GetForegroundWindow()
    enum_ok = bool(user.EnumWindows(collect, 0))
    foreground_after = user.GetForegroundWindow()
    return {
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "observer": process_info(os.getpid()),
        "window_station": object_name(user.GetProcessWindowStation()),
        "thread_desktop": object_name(user.GetThreadDesktop(kernel.GetCurrentThreadId())),
        "foreground_before": window_info(foreground_before) if foreground_before else None,
        "foreground_after": window_info(foreground_after) if foreground_after else None,
        "foreground_stable_during_enumeration": foreground_before == foreground_after,
        "enum_windows_succeeded": enum_ok, "visible_windows": windows,
        "coordinate_note": "窗口矩形受调用进程 DPI 上下文影响；不得直接当作截图物理像素坐标发送输入。",
        "runtime_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="新建 JSON 文件的路径，拒绝覆盖已有文件")
    args = parser.parse_args()
    result = json.dumps(inspect_desktop(), ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "x", encoding="utf-8") as output:
            output.write(result + "\n")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(result)


if __name__ == "__main__":
    main()
