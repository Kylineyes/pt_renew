"""自建诊断窗口归属检查；继承原120秒Guard，只显式恢复已知目标。"""
import json
from guard import Guard,Halt
TITLE='PT Renew 控制诊断试验'
class BoundaryBeforeTool(Halt):
 pass
class DiagnosticGuard(Guard):
 async def perform(self,request):
  self.boundary_not_sent=False
  row=await super().perform(request)
  if self.boundary_not_sent:
   row=dict(row,executed=False,tool_call_sent=False)
   self.event('pre_tool_rejection_corrected',id=request['id'],result=row)
  return row
 def bind(self,pid,image):
  birth=self.birth_getter(pid)
  if birth is None:raise Halt('诊断窗口创建时间不可确认')
  super().bind(pid,image);self.expected_birth=birth;self.expected_hwnd=None
 def require_arguments(self,tool,args):
  if tool=='App':
   if args!={'mode':'switch','name':TITLE}:raise Halt('只能显式切换本轮自建窗口')
   if not self.target:raise Halt('没有绑定自建窗口')
   return
  if tool not in ['Launch','Snapshot','Click','Shortcut']:raise Halt('本任务只允许Snapshot/Click/Shortcut及自建窗口启动')
  super().require_arguments(tool,args)
 async def raw(self,tool,args):
  if tool=='Click':
   x,y=args['loc'];rect=getattr(self,'last_rect',None)
   if not rect or getattr(self,'coordinate_space',None)!='physical-desktop-pixels' or not (rect[0]<x<rect[2] and rect[1]<y<rect[3]):
    self.boundary_not_sent=True
    raise BoundaryBeforeTool('Click必须位于已核验物理桌面坐标窗口矩形内，工具未调用')
  return await super().raw(tool,args)
 async def observe_native(self):
  n=await super().observe_native()
  if self.target:
   f=n['foreground'];m=[w for w in n['windows'] if w.get('title')==TITLE]
   if len(m)!=1 or m[0].get('pid')!=self.target['pid'] or m[0].get('birth')!=self.expected_birth or f.get('birth')!=self.expected_birth:self.retreat('诊断窗口标题/PID/创建时间不符')
   if m[0].get('image','').casefold()!=self.target['image'].casefold() or f.get('hwnd')!=m[0].get('hwnd'):self.retreat('诊断窗口映像/HWND不符')
   if self.expected_hwnd is None:self.expected_hwnd=m[0]['hwnd']
   if m[0]['hwnd']!=self.expected_hwnd:self.retreat('诊断窗口主HWND改变')
   self.logical_rect=m[0].get('rect')
   physical=self.geometry_getter(self.expected_hwnd,self.target,self.expected_birth)
   if physical.get('coordinate_space')!='physical-desktop-pixels' or physical.get('thread_context_restored') is not True:self.retreat('物理矩形坐标或线程恢复不可确认')
   rect=physical.get('rect')
   if not isinstance(rect,list) or len(rect)!=4 or rect[0]>=rect[2] or rect[1]>=rect[3]:self.retreat('物理矩形未知或无效')
   self.last_rect=rect;self.coordinate_space=physical['coordinate_space']
   self.event('physical_target_rect',hwnd=self.expected_hwnd,birth=self.expected_birth,logical_rect=self.logical_rect,**physical)
  return n
 async def restore_target(self,ident,failed_id):
  if ident in self.seen or self.busy or not self.failed or failed_id!=self.failed or not self.target:return dict(completed=False,reason='恢复须引用当前失败和新ID')
  self.seen.add(ident);self.busy=True;attempted=False;executed=False
  try:
   self.cool_check();row=await self.raw('ControlStatus',{});s=row.get('structured_content') or json.loads('\n'.join(row['text']))
   if s.get('state') not in ['ready','ai']:self.retreat('目标恢复前工具门禁未允许')
   self.cool_check();self.event('native_request',purpose='explicit_restore_preflight');n=await self.native();self.event('native_result',purpose='explicit_restore_preflight',result=n)
   if n.get('input_desktop')!='Default' or n.get('locked') is not False or not n.get('foreground_stable'):self.retreat('目标恢复前桌面不安全或不稳定')
   m=[w for w in n.get('windows',[]) if w.get('title')==TITLE]
   if len(m)!=1 or m[0].get('pid')!=self.target['pid'] or m[0].get('birth')!=self.expected_birth or m[0].get('image','').casefold()!=self.target['image'].casefold():self.retreat('目标恢复前唯一标题/PID/映像/创建时间不符')
   if self.expected_hwnd is not None and m[0]['hwnd']!=self.expected_hwnd:self.retreat('目标恢复前HWND已变')
   self.expected_hwnd=m[0]['hwnd'];attempted=True
   await self.raw('App',{'mode':'switch','name':TITLE});executed=True;await self.observe_native()
   self.serial+=1;self.diagnosis=f'restore:{ident}:{self.serial}'
   return dict(completed=True,executed=True,diagnosis=self.diagnosis,failed_id=self.failed,explicit_resume_required=True)
  except Exception as error:
   self.diagnosis=None;return dict(completed=False,reason=str(error),executed=True if executed else ('unknown' if attempted else False),failed_id=self.failed,not_before_monotonic=self.not_before)
  finally:self.busy=False
