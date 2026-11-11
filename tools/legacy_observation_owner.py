"""持有本轮驱动原 Popen/HANDLE 并取得真实 wait；目标与服务由驱动持有。"""
import argparse
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def identity(process):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = [ctypes.c_void_p] * 5
    values = [ctypes.c_ulonglong() for _ in range(4)]
    if not kernel.GetProcessTimes(int(process._handle), *[ctypes.byref(v) for v in values]):
        raise ctypes.WinError(ctypes.get_last_error())
    kernel.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
    buf = ctypes.create_unicode_buffer(32768)
    size = ctypes.c_ulong(len(buf))
    if not kernel.QueryFullProcessImageNameW(int(process._handle), 0, buf, ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {'pid': process.pid, 'popen_identity': id(process), 'original_handle': int(process._handle),
            'creation_filetime': values[0].value, 'actual_image': buf.value}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slot', type=Path)
    args = parser.parse_args()
    root = args.slot.resolve()
    def save(name, value):
        with (root / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
    plan = json.loads((root / 'live-plan.json').read_text(encoding='utf-8'))
    go = json.loads((root / 'go-start.json').read_text(encoding='utf-8'))
    if root != Path(plan['slot']).resolve(): raise RuntimeError('槽路径不符')
    if hashlib.sha256((root/'live-plan.json').read_bytes()).hexdigest() != go['approved_plan_sha256']:
        raise RuntimeError('GO不批准当前plan')
    if any(go.get(k) != plan[k] for k in ('session', 'task', 'dispatch')): raise RuntimeError('GO身份不符')
    start, deadline = (datetime.datetime.fromisoformat(go[k]).timestamp() for k in ('start_utc', 'deadline_utc'))
    if not 420 < deadline-start <= 3600 or not start <= time.time() < deadline-420: raise RuntimeError('GO时段无效')
    for item in plan['frozen_files']:
        path = Path(item['path'])
        if path.stat().st_size != item['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError('冻结文件变化：' + str(path))
    with (root/'driver-stdout.bin').open('xb') as stdout, (root/'driver-stderr.bin').open('xb') as stderr:
        process = subprocess.Popen(plan['launch_argv'], cwd=root, stdout=stdout, stderr=stderr,
            env=dict(os.environ, PYTHONUTF8='1'), creationflags=subprocess.CREATE_NO_WINDOW)
        held = None
        try:
            held = identity(process)
            save('driver-created.json', held)
        finally:
            # 即使创建证据失败，仍由原创建者等待；不遗弃已创建的进程。
            rc = process.wait()
            save('driver-exit.json', {'identity': held, 'wait_return': rc, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return rc


if __name__ == '__main__': raise SystemExit(main())
