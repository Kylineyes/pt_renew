"""标准库进程监督器：显式启动冻结客户端并精确见证子孙；不访问桌面或终止进程。"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


class ProcessApi:
    """独立kernel32查询函数；持柄后复核创建时间，不由PID消失推断退出。"""

    def __init__(self):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'OpenProcess': (wintypes.HANDLE, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]),
            'CloseHandle': (wintypes.BOOL, [wintypes.HANDLE]),
            'WaitForSingleObject': (wintypes.DWORD, [wintypes.HANDLE, wintypes.DWORD]),
            'GetExitCodeProcess': (wintypes.BOOL, [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]),
            'GetProcessTimes': (wintypes.BOOL, [wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4),
            'CreateToolhelp32Snapshot': (wintypes.HANDLE, [wintypes.DWORD, wintypes.DWORD]),
        }
        for name, (result, arguments) in signatures.items():
            function = getattr(self.kernel, name)
            function.restype, function.argtypes = result, arguments

    def birth(self, handle):
        times = [wintypes.FILETIME() for _ in range(4)]
        if not self.kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime

    def hold(self, pid, expected_birth=None):
        handle = self.kernel.OpenProcess(0x100000 | 0x1000, False, pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            birth = self.birth(handle)
            if expected_birth is not None and birth != expected_birth:
                raise RuntimeError('原进程创建时间变化，拒绝替代身份')
            return handle, birth
        except BaseException:
            self.close(handle)
            raise

    def poll(self, handle):
        status = self.kernel.WaitForSingleObject(handle, 0)
        if status == 258:
            return None
        if status != 0:
            raise RuntimeError('精确进程句柄退出状态不可确认')
        code = wintypes.DWORD()
        if not self.kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value

    def close(self, handle):
        if not self.kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())

    def processes(self):
        class Entry(ctypes.Structure):
            _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR*260)]
        for name in ('Process32FirstW', 'Process32NextW'):
            function = getattr(self.kernel, name)
            function.restype = wintypes.BOOL
            function.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
        handle = self.kernel.CreateToolhelp32Snapshot(2, 0)
        if handle in (None, ctypes.c_void_p(-1).value):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = Entry()
            entry.dwSize = ctypes.sizeof(entry)
            present = self.kernel.Process32FirstW(handle, ctypes.byref(entry))
            rows = []
            while present:
                rows.append(dict(pid=int(entry.th32ProcessID), parent=int(entry.th32ParentProcessID)))
                present = self.kernel.Process32NextW(handle, ctypes.byref(entry))
            # ERROR_NO_MORE_FILES是完整枚举的唯一正常结尾。
            if ctypes.get_last_error() != 18:
                raise ctypes.WinError(ctypes.get_last_error())
            return rows
        finally:
            self.close(handle)


class ChainWitness:
    """进程身份与退出账本；任何已发现但未成功持柄的缺口均阻止完整通过。"""

    def __init__(self, api):
        self.api, self.entries, self.capture_errors = api, {}, []

    def hold(self, pid, *, parent=None, expected_birth=None):
        handle, birth = self.api.hold(pid, expected_birth)
        ident = (pid, birth)
        if ident in self.entries:
            self.api.close(handle)
            return self.entries[ident]
        if parent is not None and birth < parent['birth']:
            self.api.close(handle)
            raise RuntimeError('子进程早于所属父进程，拒绝PID复用关联')
        entry = dict(pid=pid, birth=birth, parent=parent, handle=handle,
                     held_monotonic=time.monotonic(), exit_code=None)
        self.entries[ident] = entry
        return entry

    def scan(self):
        rows = self.api.processes()
        changed = True
        while changed:
            changed = False
            for row in rows:
                if any(e['pid'] == row['pid'] and self.api.poll(e['handle']) is None for e in self.entries.values()):
                    continue
                parents = [e for e in self.entries.values() if e['pid'] == row['parent']
                           and self.api.poll(e['handle']) is None]
                if not parents:
                    continue
                parent = parents[0]
                try:
                    old_count = len(self.entries)
                    self.hold(row['pid'], parent=dict(pid=parent['pid'], birth=parent['birth']))
                    changed |= len(self.entries) != old_count
                except (OSError, RuntimeError) as error:
                    self.capture_errors.append(dict(pid=row['pid'], parent=parent['pid'],
                                                    error=str(error), observed=time.monotonic()))
        for entry in self.entries.values():
            entry['exit_code'] = self.api.poll(entry['handle'])

    def report(self):
        entries = [{key:value for key,value in entry.items() if key != 'handle'}
                   for entry in self.entries.values()]
        all_exited = bool(entries) and all(entry['exit_code'] is not None for entry in entries)
        return dict(processes=entries, capture_errors=list(self.capture_errors), all_exited=all_exited,
                    all_exit0=all_exited and all(entry['exit_code'] == 0 for entry in entries),
                    verified=all_exited and all(entry['exit_code'] == 0 for entry in entries) and not self.capture_errors,
                    termination_calls=0,
                    limitation='轮询不能排除整个生命短于采样间隔的未知子进程；受控短命探针仍须原Popen独立回执。')

    def close(self):
        for entry in self.entries.values():
            self.api.close(entry['handle'])


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def validate_plan(plan, root):
    if plan.get('schema_version') != 1 or plan.get('purpose') != 'control-client-witness':
        raise RuntimeError('缺少明确的监督器冻结方案')
    if (plan.get('diagnostic_seconds') != 600 or plan.get('total_seconds') != 900
            or plan.get('scan_interval_seconds') != .05):
        raise RuntimeError('监督器预算或采样间隔不符')
    interpreter = Path(plan['client_interpreter']).resolve(strict=True)
    if interpreter == Path(sys.executable).resolve():
        raise RuntimeError('必须显式选择独立MCP环境，不能用监督器基础Python替代')
    for collection in ('client_files', 'supervisor_files'):
        files = plan.get(collection)
        if not isinstance(files, dict) or not files:
            raise RuntimeError('监督器方案缺少冻结文件集合：'+collection)
        for name, expected in files.items():
            path = (root/name).resolve()
            if (not path.is_relative_to(root) or not path.is_file()
                    or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
                raise RuntimeError('监督器冻结文件不符：'+name)
    if not {'control_process_supervisor.py', 'control_witness_launch.py'} <= plan['supervisor_files'].keys():
        raise RuntimeError('监督器方案没有绑定直启器及监督器源码')
    if 'client.py' not in plan['client_files']:
        raise RuntimeError('监督器方案未绑定客户端入口')
    for name in ('runtime-limits.json', 'live-state.json', 'supervisor-identity.json', 'supervisor-chain-exit.json'):
        if (root/name).exists():
            raise RuntimeError('已有运行或截止原件，禁止重启客户端')
    approvals = [load(root/name) for name in ('server-approval.json', 'phase-two-approval.json')]
    for approval in approvals:
        if (type(approval.get('diagnostic_seconds')) is not int or approval['diagnostic_seconds'] != 600
                or type(approval.get('total_seconds')) is not int or approval['total_seconds'] != 900):
            raise RuntimeError('批准的600/900秒截止与监督器方案不符')
        if (approval.get('permission_confirmed') is not True or not approval.get('permission')
                or not approval.get('message_id') or approval.get('task_id') != plan.get('task_id')
                or approval.get('dispatch_id') != plan.get('dispatch_id')
                or not plan.get('task_id') or not plan.get('dispatch_id')):
            raise RuntimeError('监督器缺少本轮绑定任务与明确许可')
        if approval.get('supervisor_plan_sha256') != plan['_source_sha256']:
            raise RuntimeError('本轮批准没有冻结监督器方案摘要')
    return interpreter


def main(plan_path=None):
    plan_path = Path(plan_path or Path(__file__).with_name('supervisor-plan.json')).resolve()
    root = plan_path.parent
    plan = load(plan_path)
    plan['_source_sha256'] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    interpreter = validate_plan(plan, root)
    api = ProcessApi()
    chain = ChainWitness(api)
    # 实际监督器就是WitnessLaunch的Popen进程；自身只记录身份，退出码由上层Popen取得。
    own_handle, own_birth = api.hold(os.getpid())
    api.close(own_handle)
    save(root/'supervisor-identity.json', dict(pid=os.getpid(), birth=own_birth,
         interpreter=str(Path(sys.executable).resolve()), client_interpreter=str(interpreter),
         plan_sha256=plan['_source_sha256'], desktop_requests=0))
    deadline_reported = False
    with (root/'client-stdout.log').open('xb') as out, (root/'client-stderr.log').open('xb') as err:
        child = subprocess.Popen([str(interpreter), '-X', 'utf8', str(root/'client.py')], cwd=root,
                                 stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            chain.hold(child.pid)
            while True:
                chain.scan()
                report = chain.report()
                save(root/'supervisor-chain-held.json', report)
                if child.poll() is not None and report['all_exited']:
                    break
                limits = root/'runtime-limits.json'
                if limits.exists() and not deadline_reported:
                    budget = load(limits)
                    if time.monotonic() >= budget['cleanup_deadline']:
                        save(root/'supervisor-deadline.json', dict(original_limits=budget,
                             note='预算已尽，只保留只读退出查询，不结束进程或追加桌面请求'))
                        deadline_reported = True
                time.sleep(plan['scan_interval_seconds'])
            report.update(client_popen_exit_code=child.returncode, supervisor_pid=os.getpid(),
                          supervisor_birth=own_birth, finished=time.monotonic(),
                          supervisor_exit_proof='上层WitnessLaunch原Popen等待，须与本实际PID/birth对应')
            save(root/'supervisor-chain-exit.json', report)
            return 0 if report['verified'] and child.returncode == 0 else 1
        except BaseException as error:
            save(root/'supervisor-fatal.json', dict(error=type(error).__name__+': '+str(error),
                 client_pid=child.pid, client_popen_exit_code=child.poll(), chain=chain.report(),
                 note='不强杀、不重启；保留未结算进程，必须如实报告'))
            raise
        finally:
            chain.close()


if __name__ == '__main__':
    raise SystemExit(main())
