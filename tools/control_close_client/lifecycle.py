"""仅对本client持有的自建窗口正常生命周期关闭，不发送键鼠。"""
from pathlib import Path
import ctypes,json,time
from ctypes import wintypes
from process_witness import ProcessWitness,handle_birth,kernel_api
TITLE='PT Renew 控制诊断试验'
def normal_close(root,target,birth,expected_hwnd):
 marker=Path(root)/'lifecycle-close-attempt.json'
 with marker.open('x',encoding='utf-8') as f:json.dump(dict(target=target,birth=birth,expected_hwnd=expected_hwnd,monotonic=time.monotonic(),not_input_evidence=True),f,ensure_ascii=False)
 k=kernel_api();w=ProcessWitness(target['pid'],birth)
 assert w.poll() is None,'已退出，禁止重复关闭'
 k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
 image=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(image))
 assert k.QueryFullProcessImageNameW(w.handle,0,image,ctypes.byref(size)) and image.value.casefold()==target['image'].casefold() and handle_birth(k,w.handle)==birth,'窗口所属进程映像或创建时间变化'
 u=ctypes.WinDLL('user32',use_last_error=True)
 u.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
 u.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
 u.GetClassNameW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
 u.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM];u.PostMessageW.restype=wintypes.BOOL
 def identity(hwnd):
  pid=wintypes.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));title=ctypes.create_unicode_buffer(512);cls=ctypes.create_unicode_buffer(128);u.GetWindowTextW(hwnd,title,len(title));u.GetClassNameW(hwnd,cls,len(cls))
  return dict(pid=pid.value,hwnd=hwnd,title=title.value,cls=cls.value)
 if expected_hwnd is None:
  found=[];callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
  def visit(hwnd,param):
   row=identity(hwnd)
   if row['pid']==target['pid'] and row['title']==TITLE and row['cls']=='TkTopLevel':found.append(row)
   return True
  callback=callback_type(visit);u.EnumWindows.argtypes=[callback_type,wintypes.LPARAM];assert u.EnumWindows(callback,0)
  assert len(found)==1,'本自建进程的唯一窗口不可确认';row=found[0]
 else:row=identity(expected_hwnd)
 assert row['pid']==target['pid'] and row['title']==TITLE and row['cls']=='TkTopLevel','自建窗口身份改变'
 assert u.PostMessageW(row['hwnd'],0x10,0,0),'正常关闭消息发送失败'
 result=dict(completed=True,**row,birth=birth,image=image.value,post_message='WM_CLOSE',post_message_count=1,keyboard_mouse_calls=0,termination_calls=0,not_input_evidence=True,monotonic=time.monotonic())
 (Path(root)/'lifecycle-close-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');return result
