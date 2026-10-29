"""已结算诊断窗的独立生命周期收尾；默认只检查，不复用原控制链。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import time

TITLE = 'PT Renew 控制诊断试验'
SOURCE_FILES = frozenset(('window-launch.json','uia-preflight.json','window.py',
    'hard-deadline-exit.json','live-state.json','controller-trace.jsonl',
    'v3-s09-close-complete.json'))


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_plan(plan, *, now, tool_sha256):
    if (plan.get('mode') != 'residual-diagnostic-lifecycle'
            or not re.fullmatch(r'lifecycle_[0-9a-f]{12}',str(plan.get('operation_id')))
            or plan.get('tool_sha256') != tool_sha256
            or type(plan.get('deadline')) not in (int,float) or now >= plan['deadline']):
        raise ValueError('必须是本工具摘要绑定、未过期的独立生命周期方案')
    source = Path(plan['source_root']).resolve(strict=True)
    files = plan.get('source_files_sha256',{})
    if set(files) != SOURCE_FILES:
        raise ValueError('来源证据集合不完整或包含未约定文件')
    for name, expected in files.items():
        if sha(source/name) != expected:
            raise ValueError('来源原件发生变化：'+name)
    # 拒绝任意自制脚本或产品窗口冒用同名诊断身份。
    if sha(source/'window.py') != sha(Path(__file__).with_name('control_test_window.py')):
        raise ValueError('来源窗口不是本工具库的诊断测试窗')
    launch=load(source/'window-launch.json');uia=load(source/'uia-preflight.json')
    hard=load(source/'hard-deadline-exit.json');state=load(source/'live-state.json')
    close=load(source/'v3-s09-close-complete.json')
    if (launch.get('product_candidate') is not False or uia.get('completed') is not True
            or uia.get('identity_verified') is not True or uia.get('Name') != TITLE
            or uia.get('ClassName') != 'TkTopLevel'
            or hard.get('outstanding_window') is not True or hard.get('window_exit') is not None
            or hard.get('window_pid') != launch.get('pid')
            or close.get('tool_call_sent') is not False or close.get('executed') is not False
            or close.get('completed') is not False or close.get('phase') != 'preflight'
            or not state.get('failed') or now < state['not_before_monotonic']):
        raise ValueError('来源不是已结束且关闭未发送、完整冷却已满的精确自建诊断窗')
    target=dict(pid=launch['pid'],birth=launch['birth'],image=launch['image'],
                hwnd=uia['expected_hwnd'],title=TITLE,cls='TkTopLevel')
    if (any(type(target[k]) is not int or target[k]<=0 for k in ('pid','birth','hwnd'))
            or any(uia.get(k)!=launch[k] for k in ('pid','birth','image'))
            or state.get('target') != dict(pid=target['pid'],image=target['image'])
            or plan.get('target') != target):
        raise ValueError('方案、来源UIA、原启动和目标绑定身份不一致')
    trace=(source/'controller-trace.jsonl').read_text(encoding='utf-8').splitlines()
    if not trace or json.loads(trace[-1]).get('event')!='trace-closed' or json.loads(trace[-1]).get('dropped')!=0:
        raise ValueError('来源控制服务缺少正常日志关闭证明')
    return target


class ResidualLifecycle:
    """新查询句柄只证明本次独立生命周期，不冒充原Popen或原验收通过。"""

    def __init__(self, api, record, reserve, *, clock=time.monotonic):
        self.api,self.record,self.reserve,self.clock=api,record,reserve,clock

    def run(self, target, *, execute=False, deadline, authorized=False):
        handle=None;attempted=False;sent=False
        try:
            if self.clock()+10>=deadline:
                raise ValueError('生命周期方案不足10秒退出等待余量')
            if execute and not authorized:
                raise ValueError('没有显式独立生命周期许可，禁止发关闭消息')
            handle,birth=self.api.hold(target['pid'],target['birth'])
            if birth!=target['birth']:
                raise ValueError('当前查询句柄创建时间变化')
            current=self.api.identity(handle,target['hwnd'])
            if current != target or self.api.poll(handle) is not None:
                raise ValueError('当前PID/创建时间/映像/HWND/标题/类改变或已经退出')
            if self.api.matching_windows(TITLE) != [dict(pid=target['pid'],hwnd=target['hwnd'],title=TITLE,cls='TkTopLevel')]:
                raise ValueError('当前同名诊断窗不唯一或窗口身份不符')
            self.record('identity_verified',identity=current,original_popen=False,late_query_handle=True)
            if not execute:
                return dict(completed=True,inspected=True,post_message_count=0,original_popen=False)
            # reserve必须是独占创建并持久化的一次机会。未知结果绝不重发。
            self.reserve(target)
            if self.api.identity(handle,target['hwnd']) != target or self.api.poll(handle) is not None:
                raise ValueError('关闭前最后身份核验失败，机会保持已消费')
            if self.clock()+10>=deadline:
                raise ValueError('关闭前已不足退出等待余量')
            attempted=True
            self.record('post_message_start',identity=target,message='WM_CLOSE')
            sent=self.api.post_close(target['hwnd'])
            self.record('post_message_return',returned=sent)
            if sent is not True:
                raise RuntimeError('正常关闭消息返回失败，禁止重发')
            code=self.api.wait(handle,min(10,deadline-self.clock()))
            self.record('late_handle_exit',pid=target['pid'],birth=target['birth'],exit_code=code,original_popen=False)
            if type(code) is not int or code!=0:
                raise RuntimeError('退出超时或非0，不能记生命周期通过')
            return dict(completed=True,post_message_count=1,exit_code=code,
                        original_popen=False,late_query_handle=True,gui_acceptance=False)
        except (Exception,KeyboardInterrupt) as error:
            return dict(completed=False,reason=type(error).__name__+': '+str(error),
                        post_message_attempted=attempted,post_message_returned=sent,
                        original_popen=False,gui_acceptance=False,no_retry=True)
        finally:
            if handle is not None:self.api.close(handle)


class WindowsApi:
    def __init__(self):
        import ctypes
        from ctypes import wintypes
        from control_process_supervisor import ProcessApi
        self.ctypes,self.types=ctypes,wintypes
        self.process=ProcessApi();self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.process.kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
        self.process.kernel.QueryFullProcessImageNameW.restype=wintypes.BOOL
        signatures={
            'GetWindowThreadProcessId':(wintypes.DWORD,[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]),
            'GetWindowTextW':(ctypes.c_int,[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]),
            'GetClassNameW':(ctypes.c_int,[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]),
            'PostMessageW':(wintypes.BOOL,[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]),
        }
        for name,(result,args) in signatures.items():
            fn=getattr(self.user,name);fn.argtypes=args;fn.restype=result

    def hold(self,pid,birth):return self.process.hold(pid,birth)
    def poll(self,handle):return self.process.poll(handle)
    def close(self,handle):return self.process.close(handle)

    def window(self,hwnd):
        c,t=self.ctypes,self.types;pid=t.DWORD()
        if not self.user.GetWindowThreadProcessId(hwnd,c.byref(pid)):raise c.WinError(c.get_last_error())
        title=c.create_unicode_buffer(512);cls=c.create_unicode_buffer(128)
        self.user.GetWindowTextW(hwnd,title,len(title))
        if not self.user.GetClassNameW(hwnd,cls,len(cls)):raise c.WinError(c.get_last_error())
        return dict(pid=pid.value,hwnd=hwnd,title=title.value,cls=cls.value)

    def identity(self,handle,hwnd):
        c,t=self.ctypes,self.types;row=self.window(hwnd)
        image=c.create_unicode_buffer(32768);size=t.DWORD(len(image))
        if not self.process.kernel.QueryFullProcessImageNameW(handle,0,image,c.byref(size)):raise c.WinError(c.get_last_error())
        return dict(row,birth=self.process.birth(handle),image=image.value)

    def matching_windows(self,title):
        c,t=self.ctypes,self.types;found=[];errors=[]
        callback_type=c.WINFUNCTYPE(t.BOOL,t.HWND,t.LPARAM)
        def visit(hwnd,param):
            try:
                row=self.window(hwnd)
                if row['title']==title:found.append(row)
            except Exception as error:errors.append(str(error));return False
            return True
        callback=callback_type(visit)
        self.user.EnumWindows.argtypes=[callback_type,t.LPARAM];self.user.EnumWindows.restype=t.BOOL
        if not self.user.EnumWindows(callback,0) or errors:raise RuntimeError('窗口唯一性枚举失败：'+str(errors))
        return found

    def post_close(self,hwnd):return bool(self.user.PostMessageW(hwnd,0x10,0,0))
    def wait(self,handle,seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            code=self.poll(handle)
            if code is not None:return code
            time.sleep(.05)
        return self.poll(handle)


def main():
    parser=argparse.ArgumentParser(description='精确已结算诊断窗的独立生命周期；默认只读')
    parser.add_argument('--plan',required=True,type=Path)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();plan=load(args.plan)
    target=check_plan(plan,now=time.monotonic(),tool_sha256=sha(Path(__file__)))
    root=Path(plan['evidence_root']).resolve(strict=True)
    log=root/('execute-events.jsonl' if args.execute else 'inspect-events.jsonl')
    # 再次执行或检查不会覆盖既有原件。
    with log.open('x',encoding='utf-8') as out:
        def record(kind,**fields):
            out.write(json.dumps(dict(kind=kind,monotonic=time.monotonic(),**fields),ensure_ascii=False)+'\n');out.flush()
        def reserve(identity):
            with (root/'close-attempt.json').open('x',encoding='utf-8') as marker:
                json.dump(dict(identity=identity,plan_sha256=sha(args.plan),monotonic=time.monotonic()),marker,ensure_ascii=False)
        result=ResidualLifecycle(WindowsApi(),record,reserve).run(target,execute=args.execute,
            authorized=plan.get('permission_confirmed') is True and bool(plan.get('permission')),
            deadline=plan['deadline'])
        record('operation_complete',operation_id=plan['operation_id'],result=result)
    with (root/('execute-result.json' if args.execute else 'inspect-result.json')).open('x',encoding='utf-8') as out:
        json.dump(result,out,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['completed'] else 1


if __name__=='__main__':raise SystemExit(main())
