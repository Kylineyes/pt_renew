"""单连接自建窗口诊断；批准前不导入MCP/原生桌面，记录真实call_tool起止。"""
from pathlib import Path
import asyncio,base64,datetime,hashlib,json,os,re,subprocess,sys,time
from snapshot_pacer import SnapshotPacer
from diagnostic_guard import DiagnosticGuard as Guard
from budget import Budget
R=Path(__file__).resolve().parent
FROZEN_TOOLS=R.parent/'tools'
FROZEN_PACKAGE=R.parent/'isolated'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
def require_approval():
 sys.path.insert(0,str(FROZEN_TOOLS))
 from control_surface_approval import require_client_approval
 return require_client_approval(R,FROZEN_TOOLS,FROZEN_PACKAGE,require_owned_close=True)
class McpTransport:
 def __init__(self,connection,schemas,validate,launch,root):
  self.connection,self.schemas,self.validate,self.launch,self.root=connection,schemas,validate,launch,root
  self.number=0;self.pacer=SnapshotPacer(4.0)
  self.calls=(root/'actual-calls.jsonl').open('x',encoding='utf-8')
 def event(self,**v):self.calls.write(json.dumps(dict(monotonic=time.monotonic(),wall=time.time(),**v),ensure_ascii=False)+'\n');self.calls.flush()
 async def __call__(self,tool,args):
  self.number+=1;stem=f'{self.number:04}-{tool}'
  if tool=='Launch':return await self.launch(args)
  self.validate(args,self.schemas[tool])
  if tool=='Snapshot':await self.pacer.before()
  check_runtime(tool=='Shortcut' and args=={'shortcut':'alt+f4'})
  self.event(event='call_tool-start',call=stem,tool=tool)
  try:result=await asyncio.wait_for(self.connection.call_tool(tool,args),35)
  except BaseException as error:
   self.event(event='call_tool-end',call=stem,tool=tool,exception=type(error).__name__,message=str(error));raise
  else:self.event(event='call_tool-end',call=stem,tool=tool,is_error=result.is_error)
  finally:
   if tool=='Snapshot':self.pacer.after()
  row=dict(tool=tool,arguments=args,is_error=result.is_error,text=[],images=[],structured_content=result.structured_content)
  write(self.root/(stem+'-raw.json'),result.model_dump(mode='json'))
  for part in result.content:
   if part.type=='text':row['text'].append(part.text)
   elif part.type=='image':
    p=self.root/f'{stem}-{len(row["images"]):02}.png';p.write_bytes(base64.b64decode(part.data));row['images'].append(p.name)
  write(self.root/(stem+'.json'),row);return row
def check_runtime(cleanup=False):
 limits=load(R/'runtime-limits.json')
 assert time.monotonic()+35<limits['cleanup_deadline' if cleanup else 'diagnostic_deadline'],'已到用户批准的运行截止，只能报告未完成'
async def main():
 approval=require_approval();assert not (R/'live-state.json').exists(),'已有现场状态，禁止重连重置'
 from mcp import ClientSession,StdioServerParameters
 from mcp.client.stdio import stdio_client
 from jsonschema import validate
 from inspect_legacy_desktop import inspect_desktop
 from process_witness import process_birth
 import ctypes
 from ctypes import wintypes
 sys.path.insert(0,str(FROZEN_TOOLS))
 from control_target_activation import InitialTargetActivation
 from control_owned_close import OwnedDiagnosticClose
 initial_activation=InitialTargetActivation()
 owned_close=OwnedDiagnosticClose(enabled=approval.get('owned_diagnostic_close'),cleanup_deadline=time.monotonic()+900)
 child=None;launch_used=False;uia_attempted=False;uia_ready=False;activation_ready=False;event_no=0;budget=Budget();events=R/'events';events.mkdir()
 def emit(row):
  nonlocal event_no
  event_no+=1;write(events/f'{event_no:05}-{row["kind"]}.json',row)
  if row['kind']=='retreat':write(R/'retreat-current.json',row)
  write(R/'live-state.json',dict(guard.state(),client_pid=os.getpid(),event_no=event_no,budget=vars(budget)))
 async def native():
  check_runtime(True)
  user=ctypes.WinDLL('user32',use_last_error=True)
  user.OpenInputDesktop.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];user.OpenInputDesktop.restype=wintypes.HANDLE
  user.CloseDesktop.argtypes=[wintypes.HANDLE]
  user.GetUserObjectInformationW.argtypes=[wintypes.HANDLE,ctypes.c_int,wintypes.LPVOID,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
  h=user.OpenInputDesktop(0,False,1);name=None
  if h:
   try:
    buf=ctypes.create_unicode_buffer(512);needed=wintypes.DWORD()
    if user.GetUserObjectInformationW(h,2,buf,ctypes.sizeof(buf),ctypes.byref(needed)):name=buf.value
   finally:user.CloseDesktop(h)
  n=inspect_desktop();f=n.get('foreground_after') or {}
  def window(w):
   pid=w.get('process',{}).get('pid')
   return dict(birth=process_birth(pid) if guard.target and pid==guard.target['pid'] else None,pid=pid,hwnd=w.get('hwnd'),image=w.get('process',{}).get('image',''),title=w.get('title'),cls=w.get('class'),rect=w.get('rect'))
  return dict(input_desktop=name,locked=name!='Default',foreground_stable=n['foreground_stable_during_enumeration'],foreground=window(f),windows=[window(w) for w in n['visible_windows']],full_native=n)
 async def launch(args):
  nonlocal child,launch_used
  check_runtime()
  from passive_initial import evaluate,read_rows
  limits=load(R/'runtime-limits.json')
  assert evaluate(read_rows(R/'controller-trace.jsonl'),time.monotonic(),limits['started'])['ready'],'创建窗口前被动日志条件已改变，禁止追逐ready重试'
  assert not launch_used and args=={'case':'diagnostic-window'}
  launch_used=True
  exe=Path(sys._base_executable).with_name('pythonw.exe').resolve();assert exe.is_file()
  from window import launch_window
  child=launch_window(exe,R/'window.py',R)
  birth=process_birth(child.pid);assert birth is not None
  row=dict(pid=child.pid,birth=birth,image=str(exe),command=[str(exe),'-X','utf8',str(R/'window.py'),'--evidence-root',str(R)],stdout=str(R/'window-stdout.log'),stderr=str(R/'window-stderr.log'),product_candidate=False)
  owned_close.bind_created(child,birth=birth,image=str(exe))
  write(R/'window-launch.json',row);return row
 env=dict(os.environ,ANONYMIZED_TELEMETRY='false',DO_NOT_TRACK='1',PYTHONUTF8='1',WINDOWS_MCP_SCREENSHOT_BACKEND='pillow')
 server=StdioServerParameters(command='C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Scripts/python.exe',args=['-X','utf8',str(FROZEN_TOOLS/'run_control_diagnostics.py'),'serve','--package-root',str(FROZEN_PACKAGE),'--trace',str(R/'controller-trace.jsonl'),'--approval',str(R/'server-approval.json')],env=env)
 started=time.monotonic();owned_close.cleanup_deadline=started+900;write(R/'runtime-limits.json',dict(started=started,wall=time.time(),diagnostic_deadline=started+600,cleanup_deadline=started+900,permission=approval['permission']))
 async with stdio_client(server) as (rd,wr):
  async with ClientSession(rd,wr) as connection:
   await asyncio.wait_for(connection.initialize(),35);tools=(await asyncio.wait_for(connection.list_tools(),35)).tools;schemas={t.name:t.input_schema for t in tools};write(R/'live-tools.json',[t.model_dump(mode='json') for t in tools])
   def geometry_getter(hwnd,target,birth):
    from process_witness import ProcessWitness,handle_birth,kernel_api
    sys.path.insert(0,str(FROZEN_TOOLS))
    from control_geometry import physical_window_rect
    user=ctypes.WinDLL('user32',use_last_error=True);user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    witness=ProcessWitness(target['pid'],birth);k=kernel_api()
    k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    def verify():
     pid=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));image=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(image))
     assert witness.poll() is None and pid.value==target['pid'] and handle_birth(k,witness.handle)==birth,'物理矩形前后PID/创建时间变化'
     assert k.QueryFullProcessImageNameW(witness.handle,0,image,ctypes.byref(size)) and image.value.casefold()==target['image'].casefold(),'物理矩形前后映像不符'
    try:verify();row=physical_window_rect(hwnd);verify();return row
    finally:witness.close()
   transport=McpTransport(connection,schemas,validate,launch,R);guard=Guard(transport,native,emit);guard.birth_getter=process_birth;guard.geometry_getter=geometry_getter
   write(R/'client-identity.json',dict(pid=os.getpid(),ppid=os.getppid(),python=sys.executable,server=server.model_dump(mode='json'),approval=approval))
   emit(dict(kind='connected',monotonic=time.monotonic(),wall=time.time()))
   from passive_initial import evaluate,read_rows
   decision=None
   while time.monotonic()<started+60:
    try:decision=evaluate(read_rows(R/'controller-trace.jsonl'),time.monotonic(),started)
    except (ValueError,KeyError,TypeError) as error:
     decision=dict(ready=False,reason='初始日志不可解析',exception=type(error).__name__);break
    if decision['ready'] or decision.get('fatal'):break
    await asyncio.sleep(.5)
   if decision is None:decision=dict(ready=False,reason='初始化已耗尽60秒')
   decision.update(finished=time.monotonic(),started=started,observation_limit_seconds=60)
   write(R/'initial-observation.json',decision)
   if not decision['ready']:
    write(R/'no-window-exit.json',dict(reason=decision['reason'],window_created=False,control_tool_calls=0))
    transport.calls.close();return
   while True:
    if time.monotonic()>=load(R/'runtime-limits.json')['cleanup_deadline']:
     write(R/'hard-deadline-exit.json',dict(completed=False,reason='达到900秒硬截止，不再请求桌面',window_pid=child.pid if child else None,window_exit=child.poll() if child else None,outstanding_window=child is not None,no_automatic_reconnect=True))
     transport.calls.close();return
    pending=sorted((R/'inbox').glob('*.json'))
    if len(pending)>1:
     guard.failed='queue-rejected';guard.diagnosis=None
     for p in pending:
      req=load(p);p.unlink();write(R/(req['id']+'-complete.json'),dict(completed=False,reason='多个排队请求全部拒绝'))
     emit(dict(kind='queue_rejected',monotonic=time.monotonic(),wall=time.time()));continue
    if not pending:await asyncio.sleep(.1);continue
    p=pending[0];req=load(p);p.unlink();ident=req['id'];assert re.fullmatch(r'[a-zA-Z0-9_-]+',ident)
    assert not (R/(ident+'-complete.json')).exists(),'重复ID'
    write(R/(ident+'-request.json'),req);kind=req['kind']
    try:
     if kind!='stop':check_runtime(kind in ('close-owned','retire','lifecycle-close','diagnose'))
     if kind=='stop':
      guard.cool_check()
      assert child is None,'必须先证明自建窗口退出并退役';write(R/(ident+'-complete.json'),dict(completed=True,client_stopped=True));emit(dict(kind='client_stop',monotonic=time.monotonic(),wall=time.time()));transport.calls.close();return
     elif kind=='uia-preflight':
      guard.cool_check()
      assert child is not None and child.poll() is None and guard.target and child.pid==guard.target['pid'] and not guard.busy and not uia_attempted and budget.groups==0,'只允许组前一次自建窗口只读UIA前置'
      uia_attempted=True
      proc=await asyncio.create_subprocess_exec(sys.executable,'-X','utf8',str(R/'uia_probe.py'),str(R),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
      write(R/'uia-probe-process.json',dict(pid=proc.pid,birth=process_birth(proc.pid)))
      out,err=await asyncio.wait_for(proc.communicate(),35);write(R/'uia-probe-exit.json',dict(pid=proc.pid,exit_code=proc.returncode,stdout=out.decode('utf-8',errors='replace'),stderr=err.decode('utf-8',errors='replace')))
      assert proc.returncode==0,'UIA只读探针失败，不进入组'
      row=load(R/'uia-preflight.json');uia_ready=row.get('completed') is True
      if uia_ready:guard.expected_hwnd=row['expected_hwnd']
      else:budget.refused=True
     elif kind=='initial-activate':
      check_runtime()
      row=await initial_activation.run(guard,ident,req['parent'],uia_ready=uia_ready,groups_started=budget.groups)
      activation_ready=row.get('completed') is True
      if not activation_ready:budget.refused=True
     elif kind=='begin-group':
      assert activation_ready,'必须先完成原App初始激活和目标前景后验'
      assert uia_ready,'UIA属性及原工具枚举前置未通过，不允许组'
      budget.begin();row=dict(completed=True,group=budget.groups)
     elif kind=='close-owned':
      budget.check(req)
      row=await owned_close.run(guard,ident,req['parent'],stage_ready=budget.close_ready(),pending=lambda:bool(list((R/'inbox').glob('*.json'))))
      budget.result(req,row)
      if row.get('completed') and row.get('retired'):
       write(R/'window-exit.json',dict(row,original_popen=True));child=None
     elif kind=='retire':
      assert child is not None and child.poll() is not None,'无Popen退出正面证据'
      row=dict(completed=True,pid=child.pid,exit_code=child.returncode);write(R/'window-exit.json',row);guard.retire(child.pid,child.returncode);child=None
     elif kind=='lifecycle-close':
      raise ValueError('本候选禁止WM_CLOSE补发；关闭失败只观察原Popen及按预算收尾')
     elif kind in ('restore-target','resume'):raise ValueError('本轮失败后只收尾，不恢复或重发诊断组')
     else:
      if kind=='action' and req.get('tool')!='Launch' and req.get('arguments')!={'shortcut':'alt+f4'}:assert uia_ready,'UIA前置未通过，禁止截图或诊断输入'
      budget.check(req)
      if kind=='diagnose':row=await guard.diagnose(ident)
      elif kind=='action':row=await guard.perform(req)
      else:raise ValueError('未知请求')
      budget.result(req,row)
    except Exception as error:row=dict(completed=False,reason=type(error).__name__+': '+str(error))
    write(R/(ident+'-complete.json'),row);write(R/'live-state.json',dict(guard.state(),client_pid=os.getpid(),event_no=event_no,budget=vars(budget)))
if __name__=='__main__':
 try:asyncio.run(main())
 except BaseException as error:
  write(R/'client-fatal.json',dict(error=str(error),at=datetime.datetime.now().astimezone().isoformat(),no_automatic_reconnect=True));raise
