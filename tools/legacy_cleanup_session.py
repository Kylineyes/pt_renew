"""EX-001 独立正常退出接续：只取当前图、至多一次精确聚焦和一次宿主X。"""
import ast
import base64
import ctypes
from ctypes import wintypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time

ROOT = Path(sys.argv[1]).resolve() if __name__ == '__main__' else None


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name, value):
    with (ROOT/name).open('x',encoding='utf-8') as stream: json.dump(value,stream,ensure_ascii=False,indent=2)


def exact_target(expected):
    """仅查询目标生命身份；句柄是临时查询句柄，不冒充原owner/Popen。"""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]*5
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    handle=kernel.OpenProcess(0x1000,False,expected['pid'])
    if not handle: raise ctypes.WinError(ctypes.get_last_error())
    try:
        times=[ctypes.c_ulonglong() for _ in range(4)]
        if not kernel.GetProcessTimes(handle,*[ctypes.byref(x) for x in times]): raise ctypes.WinError(ctypes.get_last_error())
        size=wintypes.DWORD(32768); buf=ctypes.create_unicode_buffer(size.value)
        if not kernel.QueryFullProcessImageNameW(handle,0,buf,ctypes.byref(size)): raise ctypes.WinError(ctypes.get_last_error())
        if times[0].value!=expected['creation_filetime'] or Path(buf.value).resolve()!=Path(expected['actual_image']).resolve():
            raise RuntimeError('原目标创建时间或映像变化')
    finally: kernel.CloseHandle(handle)


def main():
    plan=load(ROOT/'live-plan.json'); go=load(ROOT/'go-start.json')
    if go['approved_plan_sha256']!=sha(ROOT/'live-plan.json'): raise RuntimeError('新GO摘要不符')
    if any(go.get(k)!=plan[k] for k in ('session','task','dispatch')): raise RuntimeError('新GO身份不符')
    end=datetime.datetime.fromisoformat(go['deadline_utc']).timestamp()
    start=datetime.datetime.fromisoformat(go['start_utc']).timestamp()
    if not start<=time.time()<end-120: raise RuntimeError('新收尾时段无效')
    for item in plan['frozen_files']:
        if Path(item['path']).stat().st_size!=item['bytes'] or sha(item['path'])!=item['sha256']: raise RuntimeError('收尾冻结项变化')
    original=Path(plan['original_slot'])
    expected=load(original/'step-002-launch-owned-binding.json')
    if expected!=plan['original_target']: raise RuntimeError('原目标创建证据变化')
    if not (original/'cleanup-only-ready.json').exists(): raise RuntimeError('原完整静默尚未结束')
    if not load(original/'observer-failure-state.json')['done']: raise RuntimeError('原采样尚未结束')
    if list((original/'inbox').glob('request-*.json')): raise RuntimeError('原服务仍有待投请求')
    if any(not p.with_name(p.name.replace('-request.json','-response.json')).exists() for p in original.glob('*-request.json')):
        raise RuntimeError('原服务存在未配对请求')
    # 复用经父审查的Rpc完整定义；不执行其顶层DPI设置或main。
    driver=Path(plan['source_driver'])
    tree=ast.parse(driver.read_text(encoding='utf-8'))
    names=('process_identity','select_region','guard_window','Refused','Rpc')
    exec(compile(ast.Module(body=[n for n in tree.body if getattr(n,'name',None) in names],type_ignores=[]),'<已冻结Rpc纯定义>','exec'),globals())
    from inspect_legacy_desktop import inspect_desktop as inspect
    globals()['inspect_desktop']=inspect
    from review_gate import publish, review
    dpi=bool(ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)))
    save('helper-started.json',{'pid':os.getpid(),'dpi_init_result':dpi,'at':stamp(),'target_owner':'原driver持续持原Popen，本helper仅临时查询身份'})
    rpc=Rpc();rpc.limit=time.monotonic()+end-time.time()
    sequence=0; focused=False; clicked=False; stopped=False; state=None
    def snapshot(name):
        nonlocal state
        exact_target(expected)
        rpc.snapshot(name,expected['pid'])
        images=load(ROOT/(name+'-images.json'))
        state=publish(ROOT,plan,name,images)
        save(name+'-complete.json',{'at':stamp(),'completed':True})
    try:
        rpc.start(plan)
        (ROOT/'inbox').mkdir()
        snapshot('cleanup-000-current')
        while time.monotonic()<rpc.limit:
            paths=list((ROOT/'inbox').glob('request-*.json'))
            if not paths: time.sleep(.1);continue
            if len(paths)!=1: raise RuntimeError('收尾只允许一个请求')
            packet=load(paths[0]);request=packet['request'];tool=request['tool']
            if any(packet.get(k)!=plan[k] for k in ('session','task','dispatch')): raise RuntimeError('收尾请求身份不符')
            if tool not in ('Focus','CloseClick','Stop'): raise RuntimeError('收尾禁止其它动作')
            sequence+=1;name=f'cleanup-{sequence:03}-{tool.lower()}'
            if tool=='Stop':
                result=load(original/'driver-exit.json')
                if result['wait_return']!=0 or load(original/'control-exit.json')['wait_return']!=0:
                    raise RuntimeError('原driver或服务尚未证明正常退出')
                paths[0].rename(paths[0].with_suffix('.consumed'));stopped=True;break
            if packet.get('previous')!=state['step'] or packet.get('nonce')!=state['nonce']: raise RuntimeError('收尾请求不是当前图')
            review(ROOT,plan,state,'host')
            exact_target(expected)
            rpc.gate(name);rpc.remaining()
            native=inspect();save(name+'-native-before.json',native)
            own=[w for w in native['visible_windows'] if w['hwnd']==expected['hwnd'] and w['process']['pid']==expected['pid']]
            if len(own)!=1: raise RuntimeError('原精确窗口不唯一')
            if tool=='Focus':
                if focused or clicked: raise RuntimeError('收尾聚焦次数已使用')
                args={'mode':'switch','name':own[0]['title']}
                if request['arguments']!=args: raise RuntimeError('只能聚焦当前唯一精确标题')
                guard_window(native,expected['pid'],expected['hwnd'],'App',args)
                paths[0].rename(paths[0].with_suffix('.consumed'));focused=True
                rpc.tool('App',args,name);snapshot(name+'-post')
            else:
                if clicked: raise RuntimeError('正常宿主X仅允许一次，不重发')
                args=request['arguments']
                if set(args)!= {'loc'} or len(args['loc'])!=2 or any(type(v)is not int for v in args['loc']): raise RuntimeError('只允许当前图确认的默认Click')
                guard_window(native,expected['pid'],expected['hwnd'],'Click',args)
                # 固定只允许原目标标题栏的正常关闭按钮范围，坐标仍须由当前原图确认。
                left,top,right,bottom=own[0]['rect'];x,y=args['loc']
                if not right-60<=x<right or not top<=y<top+45: raise RuntimeError('坐标不是当前宿主标题栏X范围')
                exact_target(expected);rpc.remaining()
                paths[0].rename(paths[0].with_suffix('.consumed'));clicked=True
                rpc.tool('Click',args,name)
                save(name+'-complete.json',{'at':stamp(),'completed':True,'note':'仅输入回执，退出仍由原driver真实wait证明'})
    except BaseException as error:
        save('cleanup-error.json',{'at':stamp(),'type':type(error).__name__,'error':str(error),'quiet_seconds':120})
        quiet=time.monotonic()+120
        while time.monotonic()<quiet:time.sleep(min(1,quiet-time.monotonic()))
        save('cleanup-quiet-ended.json',{'at':stamp(),'note':'不再接受桌面请求，不重连或换接口'})
        raise
    finally:
        rpc.close()
        save('helper-finished.json',{'at':stamp(),'normal_stop':stopped,'focus_count':int(focused),'close_click_count':int(clicked)})


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    # review_gate仅在新收尾目录，原冻结门保持只读。
    sys.path.insert(0,str(ROOT.parent))
    main()
