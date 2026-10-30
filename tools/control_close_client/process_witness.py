"""仅查询已知PID创建时间与退出状态，不访问桌面，不终止进程。"""
import ctypes
from ctypes import wintypes

def kernel_api():
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.GetProcessTimes.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME)]
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    return k

def handle_birth(k,h):
    a,b,c,d=[wintypes.FILETIME() for _ in range(4)]
    if not k.GetProcessTimes(h,ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)):
        raise ctypes.WinError(ctypes.get_last_error())
    return (a.dwHighDateTime<<32)|a.dwLowDateTime

def process_birth(pid):
    if not isinstance(pid,int) or pid<=0:raise ValueError('只允许已知正PID')
    k=kernel_api();h=k.OpenProcess(0x1000,False,pid)
    if not h:
        error=ctypes.get_last_error()
        if error==87:return None # ERROR_INVALID_PARAMETER：该正PID不存在。
        raise ctypes.WinError(error) # 拒绝访问/未知错误不能冒充退出证据。
    try:return handle_birth(k,h)
    finally:k.CloseHandle(h)

class ProcessWitness:
    def __init__(self,pid,birth):
        self.pid,self.birth,self.returncode=pid,birth,None
        self.kernel=kernel_api();self.handle=self.kernel.OpenProcess(0x100000|0x1000,False,pid)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        try:
            # 核验实际持有句柄的创建时间，避免先查PID再开句柄之间复用。
            if handle_birth(self.kernel,self.handle)!=birth:raise RuntimeError('原目标句柄创建时间已变化')
        except BaseException:
            self.close();raise
    def poll(self):
        status=self.kernel.WaitForSingleObject(self.handle,0)
        if status==258:return None
        if status!=0:raise RuntimeError('进程退出状态不可确认')
        code=wintypes.DWORD()
        if not self.kernel.GetExitCodeProcess(self.handle,ctypes.byref(code)):raise ctypes.WinError(ctypes.get_last_error())
        self.returncode=code.value;return self.returncode
    def close(self):
        if self.handle:self.kernel.CloseHandle(self.handle);self.handle=None
    def __del__(self):
        if getattr(self,'handle',None):self.close()
