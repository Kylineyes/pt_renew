"""独立实验进程持有者及单请求事件控制器；不发送任何鼠标键盘输入。"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.platform != "win32":
    raise SystemExit("该实验控制器只支持Windows。")

kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
kernel.OpenEventW.restype = wintypes.HANDLE
kernel.SetEvent.argtypes = [wintypes.HANDLE]
kernel.SetEvent.restype = wintypes.BOOL
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.CloseHandle.restype = wintypes.BOOL
kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel.WaitForSingleObject.restype = wintypes.DWORD
kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
kernel.GetProcessTimes.restype = wintypes.BOOL


def creation_time(handle):
    created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
    if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str((created.dwHighDateTime << 32) | created.dwLowDateTime)


def launch(args):
    candidate = args.candidate.resolve(strict=True)
    directory = args.directory.resolve()
    if directory.exists():
        raise RuntimeError("启动必须使用全新的证据目录，禁止覆盖或清空旧目录。")
    # 启动记录与应用事件分目录；应用独占创建events目录。
    directory.mkdir(parents=True)
    events = directory / "events"
    environment = os.environ.copy()
    for key in list(environment):
        if key.upper().startswith(("QT_", "QML_")) or key.upper() in ("QTDIR", "CMAKE_PREFIX_PATH"):
            environment.pop(key)
    environment["PATH"] = os.pathsep.join([str(Path(os.environ["SystemRoot"]) / "System32"), os.environ["SystemRoot"]])
    command = [str(candidate), "--async-experiment-dir", str(events), "--async-experiment-kind", args.kind,
               "--async-experiment-owner", str(os.getpid()), "--async-experiment-skip", str(args.skip)] + args.application_args
    with (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, cwd=candidate.parent, env=environment, stdout=stdout, stderr=stderr)
        identity = {"owner_pid": os.getpid(), "candidate_pid": process.pid, "command": command,
                    "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                    "candidate_type": "独立实验构建，结果不代表固定候选或稳定产品通过",
                    "events_directory": str(events), "desktop_input_requests": 0}
        (directory / "launch.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(identity, ensure_ascii=False), flush=True)
        # 只持有子进程；候选由操作者正常关闭。意外失去持有者时工作线程自行中止门闩。
        code = process.wait()
        (directory / "exit.json").write_text(json.dumps({"pid": process.pid, "exit_code": code}), encoding="utf-8")
        return code


def signal(args):
    path = args.directory.resolve(strict=True) / f"request-{args.request}.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if str(manifest["request_id"]) != args.request:
        raise RuntimeError("请求ID与清单不符。")
    expected = f"Local\\PtRenewAsync-{manifest['run_id']}-{args.request}-"
    key = "release_event" if args.command == "release" else "cancel_event"
    name = manifest[key]
    if name != expected + ("release" if args.command == "release" else "cancel"):
        raise RuntimeError("事件名称不属于该运行和请求。")
    process = kernel.OpenProcess(0x100000 | 0x1000, False, int(manifest["pid"]))
    if not process:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if creation_time(process) != manifest["creation_filetime"] or kernel.WaitForSingleObject(process, 0) != 258:
            raise RuntimeError("目标进程身份变化或已退出，禁止向旧请求发送控制。")
        handle = kernel.OpenEventW(0x0002, False, name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not kernel.SetEvent(handle):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            kernel.CloseHandle(handle)
    finally:
        kernel.CloseHandle(process)
    print(json.dumps({"signaled": True, "command": args.command, "request_id": args.request,
                      "note": "只证明事件已置位；实际释放或中止以应用events.jsonl为准。"}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("launch", help="持有一个新实验候选进程，直到该进程退出")
    start.add_argument("--candidate", required=True, type=Path)
    start.add_argument("--directory", required=True, type=Path)
    start.add_argument("--kind", required=True, choices=["net", "copper"])
    start.add_argument("--skip", type=int, default=0)
    start.add_argument("application_args", nargs=argparse.REMAINDER)
    for name in ("release", "cancel"):
        sub = commands.add_parser(name, help="只控制清单对应的一个命名事件")
        sub.add_argument("--directory", required=True, type=Path)
        sub.add_argument("--request", required=True)
    args = parser.parse_args()
    if args.command == "launch":
        if args.skip < 0:
            parser.error("跳过数不得为负数。")
        if args.application_args[:1] == ["--"]:
            args.application_args.pop(0)
        if any(value.startswith("--async-experiment-") for value in args.application_args):
            parser.error("应用参数不得覆盖实验身份或门闩配置。")
        return launch(args)
    if not args.request.isascii() or not args.request.isdecimal():
        parser.error("请求ID必须是ASCII十进制整数。")
    return signal(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, KeyError, ValueError) as error:
        raise SystemExit(f"实验控制失败：{error}")
