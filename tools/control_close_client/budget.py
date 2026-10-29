"""诊断预算只限制请求，不调用桌面，不把拒绝改成成功。"""
class Budget:
 def __init__(self):self.groups=0;self.snapshots=0;self.observations=0;self.diagnoses=0;self.refused=False;self.stage=None;self.launched=False;self.cleanup=False;self.close_outcome=None
 def begin(self):
  assert not self.refused and self.groups<1 and self.stage is None,'组预算耗尽/拒绝/前组未结束'
  self.groups+=1;self.stage=0
 def restored(self,row):
  # 恢复路径失败也终止探测，但保留一次只读诊断用于收尾。
  if not row.get('completed'):self.refused=True
 def close_ready(self):
  return self.groups==1 and self.stage is None and not self.refused and self.snapshots==2
 def check(self,request):
  kind=request['kind']
  if kind=='close-owned':
   assert self.close_ready() and not self.cleanup,'仅完整诊断组后允许一次专用关闭'
   self.cleanup=True;return
  if kind=='diagnose':
   assert self.refused and self.diagnoses<1,'拒绝后最多一次同连接诊断';self.diagnoses+=1;return
  if kind!='action':return
  tool=request['tool'];args=request.get('arguments',{})
  if tool=='Launch':assert not self.launched,'仅允许一个自建窗口';self.launched=True;return
  if args=={'shortcut':'alt+f4'}:
   raise ValueError('关闭只能使用close-owned，普通Shortcut入口禁止Alt+F4')
  if self.refused:
   assert tool=='Snapshot' and self.observations<1,'拒绝后仅唯一观察及正常关闭';self.observations+=1;return
  assert self.stage is not None,'必须显式开始一组，先读首图再输入'
  expected=['Snapshot','Click','Shortcut','Snapshot'][self.stage]
  assert tool==expected,'诊断顺序须Snapshot→Click→Shortcut→Snapshot'
  if tool=='Snapshot':assert self.snapshots<4,'截图预算耗尽';self.snapshots+=1
  if tool=='Shortcut':assert args=={'shortcut':'ctrl+shift+f8'},'只允许约定无副作用快捷键'
 def result(self,request,row):
  if row.get('completed') and request.get('kind')=='action' and request.get('arguments')!={'shortcut':'alt+f4'} and request.get('tool')!='Launch' and not self.refused:
   self.stage+=1
   if self.stage==4:self.stage=None
  if request.get('kind')=='close-owned':self.close_outcome=row.get('executed','unknown')
  # 启动后首次非目标前景可专用恢复；真实工具拒绝或无图立即终止探测。
  if not row.get('completed') and (row.get('phase')!='preflight' or request.get('tool')=='Snapshot' and '非目标前景' not in row.get('reason','')):self.refused=True
