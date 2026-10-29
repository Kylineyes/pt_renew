"""只读自建窗口UIA前置；独立进程单线程保持COM，不激活或输入。"""
from pathlib import Path
import ctypes,json,sys,threading,time
from ctypes import wintypes
from process_witness import ProcessWitness,handle_birth,kernel_api
TITLE='PT Renew 控制诊断试验'
def compatible(row):
 return bool(row.get('identity_verified') and row.get('CanMinimize') is True and row.get('CanMaximize') is True and row.get('Name')==TITLE and row.get('ClassName')=='TkTopLevel' and row.get('NativeWindowHandle')==row.get('expected_hwnd') and row.get('uia_pid')==row.get('pid') and row.get('enumerated') is True)
def run(root):
 root=Path(root);launch=json.loads((root/'window-launch.json').read_text(encoding='utf-8'));result={}
 def query():
  ole=ctypes.OleDLL('ole32');ole.CoInitializeEx.argtypes=[ctypes.c_void_p,wintypes.DWORD];ole.CoInitializeEx.restype=ctypes.c_long
  hr=ole.CoInitializeEx(None,2)
  try:
   if hr<0:raise RuntimeError('UIA线程COM初始化失败')
   package=Path(json.loads((root/'phase-two-approval.json').read_text(encoding='utf-8-sig'))['package_root']);sys.path.insert(0,str(package))
   import windows_mcp.uia as uia
   from windows_mcp.desktop.service import Desktop
   assert Path(sys.modules['windows_mcp.desktop.service'].__file__).resolve().is_relative_to(package)
   w=ProcessWitness(launch['pid'],launch['birth']);assert w.poll() is None
   k=kernel_api();k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
   buf=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(buf));assert k.QueryFullProcessImageNameW(w.handle,0,buf,ctypes.byref(size)) and buf.value.casefold()==launch['image'].casefold() and handle_birth(k,w.handle)==launch['birth']
   user=ctypes.WinDLL('user32',use_last_error=True);user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)];user.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
   cbtype=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM);found=[]
   def visit(hwnd,param):
    pid=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));name=ctypes.create_unicode_buffer(512);user.GetWindowTextW(hwnd,name,len(name))
    if pid.value==launch['pid'] and name.value==TITLE:found.append(hwnd)
    return True
   cb=cbtype(visit);user.EnumWindows.argtypes=[cbtype,wintypes.LPARAM];assert user.EnumWindows(cb,0) and len(found)==1
   hwnd=found[0];control=uia.ControlFromHandle(hwnd);pattern=control.GetPattern(uia.PatternId.WindowPattern)
   result.update(pid=launch['pid'],birth=launch['birth'],image=buf.value,expected_hwnd=hwnd,identity_verified=True,Name=control.Name,ClassName=control.ClassName,ControlType=int(control.ControlType),ControlTypeName=control.ControlTypeName,NativeWindowHandle=int(control.NativeWindowHandle),uia_pid=int(control.ProcessId),CanMinimize=bool(pattern.CanMinimize) if pattern else None,CanMaximize=bool(pattern.CanMaximize) if pattern else None)
   desktop=Desktop();windows,handles=desktop.get_windows()
   result.update(enumerated=hwnd in handles,enumerated_target=[dict(name=a.name,hwnd=a.handle,pid=a.process_id) for a in windows if a.handle==hwnd],desktop_source=str(Path(sys.modules['windows_mcp.desktop.service'].__file__).resolve()))
   assert w.poll() is None and handle_birth(k,w.handle)==launch['birth']
   result.update(completed=compatible(result),readonly=True,activation_calls=0,input_calls=0,monotonic=time.monotonic())
  except BaseException as error:result.update(completed=False,error=type(error).__name__+': '+str(error),readonly=True,activation_calls=0,input_calls=0)
  finally:
   if hr>=0:ole.CoUninitialize()
 thread=threading.Thread(target=query,name='pt-uia-readonly');thread.start();thread.join()
 (root/'uia-preflight.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result
if __name__=='__main__':run(sys.argv[1])
