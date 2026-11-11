"""复用已审单菜单准备器，生成两轮Capture及看图正常宿主X的新候选。"""
import argparse
import ast
import json
from pathlib import Path

from prepare_legacy_click_observation import prepare, replace, sha, REPO


def prepare_capture(**arguments):
    prepare(**arguments)
    root=Path(arguments['destination']).resolve();slot=root/'slot'
    source=Path(arguments['source']).resolve()
    driver=(root/'desktop_session.py').read_text(encoding='utf-8')
    gate=(source/'review_gate.py').read_text(encoding='utf-8')
    gate=replace(gate,"LIFECYCLE = {'Close', 'WaitExit', 'Stop'}", "LIFECYCLE = {'CleanupSnapshot', 'CleanupFocus', 'CloseX', 'WaitExit', 'Stop'}")
    gate=replace(gate,'needs_guest=False, menu_open=False):','needs_guest=False, menu_open=False, rounds_completed=0):')
    gate=replace(gate,"'guest': entries(root, guest or []), 'needs_guest': needs_guest, 'menu_open': menu_open}","'guest': entries(root, guest or []), 'needs_guest': needs_guest, 'menu_open': menu_open, 'rounds_completed': rounds_completed}")
    gate=replace(gate,"    if tool in LIFECYCLE:\n        if tool == 'Close' and request.get('arguments') != {'shortcut': 'alt+f4'}: raise RuntimeError('Close只允许普通Alt+F4')\n        return", """    if tool in LIFECYCLE:
        if tool == 'CloseX':
            if not isinstance(state, dict) or packet.get('previous') != state['step'] or packet.get('nonce') != state['nonce']:
                raise RuntimeError('正常宿主X必须绑定当前原图')
            if load(root/(state['step']+'-observation.json')) != state: raise RuntimeError('正常宿主X当前观测不符')
            review(root, plan, state, 'host')
            args=request.get('arguments', {})
            if set(args) != {'loc'} or not isinstance(args['loc'], list) or len(args['loc']) != 2 or any(type(v) is not int for v in args['loc']):
                raise RuntimeError('正常宿主X只允许看图确认的整数loc默认Click')
        return
    if tool not in ('Launch', 'App', 'Snapshot', 'Click'): raise RuntimeError('两轮捕获禁止其它业务')
    if tool == 'Click' and request.get('purpose') not in ('capture_menu_open', 'guest_capture'):
        raise RuntimeError('只允许Capture打开及已审核截图项')""")
    gate=replace(gate,"    if menu:\n        args", "    if menu:\n        if state.get('rounds_completed', 0) >= 2: raise RuntimeError('两轮已完成，只允许正常收尾')\n        args")
    capture_start=gate.index('def capture_before(')
    gate=gate[:capture_start]+'''def capture_before(root):
    result={}
    for path in sorted((root/'captures').rglob('*')):
        if path.is_symlink() or path.is_junction(): raise RuntimeError('捕获目录不允许联接或符号链接')
        if path.is_file(): result[str(path.resolve())]={'bytes':path.stat().st_size,'sha256':sha(path)}
    return result

def capture_after(root, before):
    after=capture_before(root)
    if any(after.get(path)!=entry for path,entry in before.items()): raise RuntimeError('旧捕获文件被修改或删除')
    new=[Path(path) for path in after if path not in before]
    if len(new)!=1 or new[0].suffix.lower()!='.png': raise RuntimeError('单次捕获必须恰一张新PNG且无其它新文件')
    if entries(root,new)[0]['dimensions'] != [640,480]: raise RuntimeError('新客体图不是640x480')
    return new
'''
    driver=replace(driver,'    active_job = None','    active_job = None\n    completed_rounds = 0')
    start=driver.index('    def lifecycle(')
    end=driver.index('    try:\n        rpc.start(plan)',start)
    driver=driver[:start]+'''    def lifecycle(tool, req, name):
        nonlocal target, identity, root_hwnd, state, last_capture, cleanup_focus_used, cleanup_close_used
        rpc.observation_job = None
        rpc.limit = deadline
        if tool == 'Stop':
            if target is not None: raise RuntimeError('必须先原WaitExit记录目标退出再Stop')
            return True
        if target is None: raise RuntimeError('没有原Popen目标')
        if tool == 'WaitExit':
            rc=target.wait(timeout=min(5, rpc.remaining()))
            save(name+'-exit.json', dict(identity, wait_return=rc, at=stamp()))
            target=None; identity=None
            if rc!=0: raise RuntimeError('原目标非零退出：'+str(rc))
            return False
        if active_job is not None and not active_job.done.is_set(): raise Refused('采样尚在途，拒绝新增收尾桌面请求')
        if target.poll() is not None or process_identity(target)!=identity: raise Refused('原目标已退出或精确身份变化')
        if tool == 'CleanupFocus':
            if cleanup_focus_used or cleanup_close_used: raise Refused('正常收尾聚焦次数已使用')
            rpc.gate(name);rpc.remaining()
            native=inspect_desktop();save(name+'-native-before.json',native)
            own=[w for w in native['visible_windows'] if w['hwnd']==root_hwnd and w['process']['pid']==target.pid]
            if len(own)!=1: raise Refused('正常收尾精确窗口不唯一')
            args={'mode':'switch','name':own[0]['title']}
            guard_window(native,target.pid,root_hwnd,'App',args)
            cleanup_focus_used=True;rpc.tool('App',args,name)
        if tool in ('CleanupSnapshot','CleanupFocus'):
            last_capture=rpc.snapshot(name+'-current',target.pid)
            state=publish(ROOT,plan,last_capture, json.loads((ROOT/(last_capture+'-images.json')).read_text(encoding='utf-8')),
                [Path(item['path']) for item in (state or {}).get('guest',[])], rounds_completed=completed_rounds)
            return False
        if tool!='CloseX': raise RuntimeError('收尾只允许当前图/精确聚焦/正常宿主X/原WaitExit/Stop')
        if cleanup_close_used: raise Refused('正常宿主X已发送，不重发')
        rpc.gate(name);rpc.remaining()
        native=inspect_desktop();save(name+'-native-before.json',native)
        args=req['arguments'];guard_window(native,target.pid,root_hwnd,'Click',args)
        own=next(w for w in native['visible_windows'] if w['hwnd']==root_hwnd)
        left,top,right,bottom=own['rect'];x,y=args['loc']
        if not right-60<=x<right or not top<=y<top+45: raise Refused('当前图坐标不在正常宿主X区域')
        if process_identity(target)!=identity: raise Refused('关闭发送前原身份变化')
        rpc.remaining();cleanup_close_used=True
        rpc.tool('Click',args,name)
        return False
''' + driver[end:]
    driver=replace(driver,'                validate(ROOT, plan, None, packet)','                validate(ROOT, plan, state, packet)')
    driver=replace(driver,"save('menu-attempted.json',", "save(name+'-attempted.json',")
    driver=replace(driver,"ROOT/'menu-observation.jsonl'", "ROOT/(name+'-observation.jsonl')")
    driver=replace(driver,"save('menu-observation-summary.json', require_coverage(job, *interval))", "save(name+'-sampling-summary.json', require_coverage(job, *interval))\n                    rpc.observation_job = None")
    driver=replace(driver,"if is_guest: save(name+'-guest-before.json', guest_before)", "if is_guest: save(name+'-guest-before.json', {'at':stamp(),'perf_counter_ns':time.perf_counter_ns(),'files':guest_before})")
    driver=replace(driver,"                    guest_paths = capture_after(ROOT, guest_before)","                    guest_paths = capture_after(ROOT, guest_before)\n                    save(name+'-guest-after.json',{'at':stamp(),'perf_counter_ns':time.perf_counter_ns(),'files':capture_before(ROOT)})\n                    completed_rounds += 1")
    driver=replace(driver,"menu_open=req.get('purpose') == 'capture_menu_open')","menu_open=req.get('purpose') == 'capture_menu_open', rounds_completed=completed_rounds)")
    for text in (driver,gate): ast.parse(text)
    (root/'desktop_session.py').write_text(driver,encoding='utf-8')
    for folder in (root,slot):(folder/'review_gate.py').write_text(gate,encoding='utf-8')
    # 原submit在CloseX时必须加载当前state，不能把其当作无需审核的生命周期。
    submit=(root/'submit.py').read_text(encoding='utf-8')
    submit=replace(submit,"state = None if request['tool'] in LIFECYCLE else load(ROOT / 'current-state.json')", "state = None if request['tool'] in LIFECYCLE and request['tool'] != 'CloseX' else load(ROOT / 'current-state.json')")
    for folder in (root,slot):(folder/'submit.py').write_text(submit,encoding='utf-8')
    plan=json.loads((slot/'live-plan.json').read_text(encoding='utf-8'))
    plan.update({'driver_sha256':sha(root/'desktop_session.py'),'review_gate_sha256':sha(root/'review_gate.py'),'submit_sha256':sha(root/'submit.py'),
        'capture_rounds':2,'budget_seconds':1500,'executor':'本指定Pi唯一操作者，先父审新GO后两轮Capture，不做其它业务',
        'acceptance':['两轮各自当前菜单真实read->选择截图->全目录恰一新640x480PNG->本模型host/guest真实read','原输入不变和原Popen真实wait0'],
        'failure_cleanup':'首次120秒零新增桌面请求后只接CleanupSnapshot/CleanupFocus/当前图CloseX/原WaitExit/Stop，不重复业务或Alt+F4'})
    for item in plan['frozen_files']:
        item.update({'bytes':Path(item['path']).stat().st_size,'sha256':sha(item['path'])})
    plan['frozen_files'].append({'path':str(REPO/'tools/prepare_legacy_capture.py'),'bytes':Path(__file__).stat().st_size,'sha256':sha(__file__)})
    (slot/'live-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    preparation=json.loads((root/'preparation.json').read_text(encoding='utf-8'))
    preparation.update({'plan_sha256':sha(slot/'live-plan.json'),'files':plan['frozen_files'],'capture_rounds':2})
    (root/'preparation.json').write_text(json.dumps(preparation,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'final_plan_sha256':sha(slot/'live-plan.json'),'driver_sha256':plan['driver_sha256'],'gate_sha256':plan['review_gate_sha256'],'slot':str(slot)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true',help='只复用尚未获GO或启动的自有候选')
    for name in ('source','destination','installation','session','task','dispatch'):parser.add_argument('--'+name,required=True)
    prepare_capture(**vars(parser.parse_args()))
