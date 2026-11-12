"""持有本轮驱动原 Popen/HANDLE 并取得真实 wait；目标与服务由驱动持有。"""
import argparse
import base64
import ctypes
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import threading
import time
from legacy_runtime_config import confined, lexical, validate_runtime_plan


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


def approval_window(root, plan, *, start_only=False):
    """每次投递重新核原GO；生命周期只可在本段硬截止前。"""
    go = json.loads((root/'go-start.json').read_text(encoding='utf-8-sig'))
    if hashlib.sha256((root/'live-plan.json').read_bytes()).hexdigest() != go['approved_plan_sha256']:
        raise RuntimeError('GO不批准当前plan')
    if any(go.get(k) != plan[k] for k in ('session', 'task', 'dispatch')):
        raise RuntimeError('GO身份不符')
    start, deadline = (datetime.datetime.fromisoformat(go[k]).timestamp() for k in ('start_utc', 'deadline_utc'))
    now = time.time()
    if not 420 < deadline-start <= 3600 or not start <= now < deadline-(420 if start_only else 0):
        raise RuntimeError('GO时段无效')
    return deadline


class FileSubmitter:
    """owner自有文件线程；不创建进程、不导入桌面、不直接写业务inbox。"""
    def __init__(self, root, plan, driver):
        self.root, self.plan, self.driver = root, plan, driver
        self.queue = lexical(plan['file_submitter']['queue'])
        confined(self.queue, root)
        self.queue.mkdir(exist_ok=False)
        self.stop_event = threading.Event()
        self.dispatch_lock = threading.Lock()
        self.started = False
        self.failed = False
        self.thread = threading.Thread(target=self.run, name='legacy-file-submit', daemon=False)
        self.error = None
        self.quiet_until = 0
        self.receipts = set()
        self.session_offset = 0

    def save(self, path, value):
        confined(path, self.root)
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)

    def start(self):
        self.thread.start()
        self.started = True

    def stop(self):
        with self.dispatch_lock:
            self.stop_event.set()
        if not self.started:
            self.save(self.root/'submit-thread-exit.json', {'started': False, 'joined': True,
                'error': '线程启动未完成，未创建额外进程'})
            return
        self.thread.join(timeout=5)
        joined = not self.thread.is_alive()
        if not joined:
            try:
                self.save(self.root/'submit-thread-late-join.json', {'joined_within_five_seconds': False})
            finally:
                # 即使超时证据写入失败也不能跳过真实join。
                self.thread.join()
        self.save(self.root/'submit-thread-exit.json', {'joined': not self.thread.is_alive(),
            'joined_within_five_seconds': joined, 'error': self.error,
            'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})

    def require_images(self, packet):
        if packet['request']['tool'] in ('WaitExit', 'Stop', 'CleanupSnapshot', 'CleanupFocus'):
            return []
        state = json.loads((self.root/'current-state.json').read_text(encoding='utf-8'))
        needed = {item['sha256'] for kind in ('host', 'guest') for item in state[kind]}
        # PI_SESSION_FILE是原Pi追加的只读JSONL，不作为输出或另一个控制接口。
        session = Path(self.plan['file_submitter']['session_file'])
        if session.stat().st_size < self.session_offset:
            raise RuntimeError('原Pi JSONL被截断')
        with session.open('rb') as stream:
            stream.seek(self.session_offset)
            while line := stream.readline():
                if not line.endswith(b'\n'):
                    break  # 原Pi可能正在追加一行，留到下次完整行再解析。
                message = json.loads(line).get('message', {})
                if message.get('role') == 'toolResult':
                    for block in message.get('content', []):
                        if block.get('type') == 'image' and block.get('data'):
                            self.receipts.add(hashlib.sha256(base64.b64decode(block['data'])).hexdigest())
                self.session_offset = stream.tell()
        if not needed <= self.receipts:
            raise RuntimeError('原Pi图片回执SHA缺失')
        return sorted(needed)

    def submit(self, packet_path):
        confined(packet_path, self.queue)
        validate_runtime_plan(self.plan, runtime_root=self.root)
        packet = json.loads(packet_path.read_text(encoding='utf-8'))
        request = packet['request']
        name, tool = request['name'], request['tool']
        if not re.fullmatch(r'[a-z0-9-]+', name) or packet_path.name != 'packet-'+name+'.json':
            raise RuntimeError('投递文件名与动作名不符')
        deadline = approval_window(self.root, self.plan)
        lifecycle = {'CleanupSnapshot', 'CleanupFocus', 'CloseX', 'WaitExit', 'Stop'}
        if tool not in lifecycle and time.time() >= deadline-420:
            raise RuntimeError('最后七分钟只允许生命周期')
        if self.stop_event.is_set() or self.driver.poll() is not None:
            raise RuntimeError('driver已退出或投递线程已停止')
        if (self.failed or (self.root/'stopped-error.json').exists()) and tool not in lifecycle:
            raise RuntimeError('失败后禁止恢复业务')
        if (self.root/'stopped-error.json').exists():
            stopped = json.loads((self.root/'stopped-error.json').read_text(encoding='utf-8'))
            if time.time() < datetime.datetime.fromisoformat(stopped['at']).timestamp()+120:
                raise RuntimeError('driver首次拒绝后静默尚未结束')
        if time.monotonic() < self.quiet_until:
            raise RuntimeError('拒绝后120秒内禁止新增投递')
        images = self.require_images(packet)
        # owner主线程不再解析argv；只在文件线程内临时设置后恢复，不启动shell。
        old_argv, old_path = sys.argv, sys.path[:]
        old_gate = sys.modules.get('review_gate')
        try:
            gate_path = self.root.parent/'review_gate.py'
            spec = importlib.util.spec_from_file_location('review_gate', gate_path)
            gate = importlib.util.module_from_spec(spec)
            sys.modules['review_gate'] = gate
            spec.loader.exec_module(gate)
            sys.path.insert(0, str(self.root.parent))
            sys.argv = [str(self.root.parent/'submit.py'), str(self.root), str(packet_path)]
            # 原submit执行其validate、唯一未消费请求检查、动作名禁重放和x创建。
            approval_window(self.root, self.plan)
            if self.stop_event.is_set() or self.driver.poll() is not None:
                raise RuntimeError('提交前driver已退出或线程已停止')
            if tool not in lifecycle and time.time() >= deadline-420:
                raise RuntimeError('投递预检耗时后已过业务截止')
            runpy.run_path(str(self.root.parent/'submit.py'), run_name='__main__')
        finally:
            sys.argv, sys.path = old_argv, old_path
            if old_gate is None:
                sys.modules.pop('review_gate', None)
            else:
                sys.modules['review_gate'] = old_gate
        return images

    def refuse(self, error):
        self.failed = True
        self.quiet_until = max(self.quiet_until, time.monotonic()+120)
        signal = self.root/'stop-business.json'
        if not signal.exists():
            self.save(signal, {**{k: self.plan[k] for k in ('session', 'task', 'dispatch')},
                'reason': 'owner文件投递拒绝：'+str(error)})

    def run(self):
        try:
            self.save(self.root/'submit-thread-started.json', {'owner_pid': os.getpid(),
                'thread_ident': threading.get_ident(), 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
            while not self.stop_event.wait(.1):
                pending = sorted(self.queue.glob('packet-*.json'))
                if not pending:
                    continue
                for path in pending:
                    result = {'packet': path.name, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
                    try:
                        if len(pending) != 1:
                            raise RuntimeError('禁止预排多个投递请求')
                        with self.dispatch_lock:
                            if self.stop_event.is_set() or self.driver.poll() is not None:
                                return
                            result.update(image_receipt_sha256=self.submit(path), submitted=True)
                    except Exception as error:
                        result.update(submitted=False, error=str(error))
                        self.refuse(error)
                    confined(path, self.queue)
                    path.rename(path.with_suffix('.submitted' if result['submitted'] else '.rejected'))
                    self.save(path.with_suffix('.result'), result)
        except BaseException as error:
            self.error = repr(error)
            self.stop_event.set()
            self.save(self.root/'submit-thread-error.json', {'error': self.error})
            self.refuse(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slot', type=Path)
    args = parser.parse_args()
    root = lexical(args.slot)
    def save(name, value):
        with (root / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
    plan = json.loads((root / 'live-plan.json').read_text(encoding='utf-8'))
    validate_runtime_plan(plan, runtime_root=root)
    approval_window(root, plan, start_only=True)
    for item in plan['frozen_files']:
        path = Path(item['path'])
        if path.stat().st_size != item['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError('冻结文件变化：' + str(path))
    validate_runtime_plan(plan, runtime_root=root)
    approval_window(root, plan, start_only=True)
    with (root/'driver-stdout.bin').open('xb') as stdout, (root/'driver-stderr.bin').open('xb') as stderr:
        validate_runtime_plan(plan, runtime_root=root)
        approval_window(root, plan, start_only=True)
        process = subprocess.Popen(plan['launch_argv'], cwd=root, stdout=stdout, stderr=stderr,
            env=dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1'), creationflags=subprocess.CREATE_NO_WINDOW)
        held = None
        rc = None
        submitter = None
        try:
            held = identity(process)
            save('driver-created.json', held)
            if 'file_submitter' in plan:
                validate_runtime_plan(plan, runtime_root=root)
                approval_window(root, plan, start_only=True)
                submitter = FileSubmitter(root, plan, process)
                submitter.start()
        finally:
            # 即使创建证据失败，仍由原创建者等待；不遗弃已创建的进程。
            try:
                rc = process.wait()
            except BaseException:
                # wait被中断也不遗弃原对象；补得真实退出后仍向上保留原异常。
                rc = process.wait()
                raise
            finally:
                try:
                    if submitter is not None:
                        submitter.stop()
                finally:
                    save('driver-exit.json', {'identity': held, 'wait_return': rc,
                        'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    if submitter is not None and submitter.error is not None:
        raise RuntimeError('owner文件投递线程失败：'+submitter.error)
    return rc


if __name__ == '__main__': raise SystemExit(main())
