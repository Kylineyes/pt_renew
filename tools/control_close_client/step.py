"""单步提交器；只写文件，不接触桌面，不自动聚焦/等待冷却/重发输入。"""
from pathlib import Path
import json,re,sys,time
R=Path(__file__).resolve().parent

def submit(ident,kind,values):
    assert re.fullmatch(r'[a-zA-Z0-9_-]+',ident),'步骤ID不合法'
    assert not (R/(ident+'-complete.json')).exists(),'步骤ID已存在，禁止重试同一动作'
    state=json.loads((R/'live-state.json').read_text(encoding='utf-8-sig'))
    assert not state['busy'],'已有请求执行中'
    assert not list((R/'inbox').glob('*.json')),'禁止排队'
    request={'id':ident,'parent':state['token'],'kind':'action','capture':False}
    values=list(values or [])
    if values and values[-1]=='quiet':values.pop();request['capture']=False
    if kind=='key':
        if values[0].casefold()=='alt+f4':raise ValueError('关闭必须使用专用close-owned命令')
        request.update(tool='Shortcut',arguments={'shortcut':values[0]})
    elif kind=='click':request.update(tool='Click',arguments={'loc':[int(values[0]),int(values[1])],'button':values[2] if len(values)>2 else 'left','clicks':1})
    elif kind=='type':raise ValueError('本任务禁止文字输入')
    elif kind=='switch':raise ValueError('只能通过显式受审阅restore-target恢复自建窗口')
    elif kind=='uia-preflight':request.update(kind='uia-preflight',capture=False)
    elif kind=='initial-activate':request.update(kind='initial-activate',capture=False)
    elif kind=='begin-group':request.update(kind='begin-group',capture=False)
    elif kind=='launch':request.update(tool='Launch',arguments={'case':'diagnostic-window'})
    elif kind=='snapshot':request.update(tool='Snapshot',arguments={'use_vision':True,'use_annotation':False,'use_ui_tree':False},capture=False)
    elif kind in ('restore-target','resume'):raise ValueError('本轮失败后只收尾，不恢复或重发诊断组')
    elif kind=='diagnose':request.update(kind='diagnose',capture=False)
    elif kind in ['type','signal','verdict','critical']:raise ValueError('本任务禁止产品/实验/文字输入入口')
    elif kind=='close-owned':
        assert not values,'专用关闭不接受PID或窗口参数'
        request.update(kind='close-owned',capture=False)
    elif kind=='stop':request.update(kind='stop',capture=False)
    elif kind=='lifecycle-close':request.update(kind='lifecycle-close',capture=False)
    elif kind=='retire':request.update(kind='retire',capture=False)
    else:raise ValueError('未知命令，禁止回退为截图')
    if request['kind'] in ('action','close-owned'):
        assert not state['failed'],'链已失败，先独立diagnose及明确resume'
        assert time.monotonic()>=state['not_before_monotonic'],'120秒冷却未满'
    temp=R/'inbox'/(ident+'.tmp');dest=temp.with_suffix('.json')
    with temp.open('x',encoding='utf-8') as f:json.dump(request,f,ensure_ascii=False)
    temp.rename(dest)
    end=time.monotonic()+(45 if kind=='close-owned' else 40)
    while time.monotonic()<end:
        result=R/(ident+'-complete.json')
        if result.exists():
            row=json.loads(result.read_text(encoding='utf-8-sig'))
            if not row.get('completed'):raise RuntimeError(json.dumps(row,ensure_ascii=False))
            return row
        if (R/'client-fatal.json').exists():raise RuntimeError('长驻客户端已停，禁止自动重连')
        time.sleep(.15)
    raise TimeoutError('当前请求结果未知，禁止发下一步或重发当前动作')

def main():
    ident,kind,*values=sys.argv[1:]
    lock=R/'submission.lock'
    with lock.open('x',encoding='utf-8') as f:f.write(ident)
    try:
        row=submit(ident,kind,values)
        (R/(ident+'-driver-result.json')).write_text(json.dumps(row,ensure_ascii=False),encoding='utf-8')
        if sys.stdout:print(json.dumps(row,ensure_ascii=False))
    finally:lock.unlink()
if __name__=='__main__':main()
