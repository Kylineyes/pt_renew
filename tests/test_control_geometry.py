"""线程DPI物理矩形回归，注入假Win32接口，不接触实际窗口。"""
from pathlib import Path
import ctypes,sys,unittest
from ctypes import wintypes
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_geometry import physical_window_rect

class User32:
 def __init__(self):self.contexts=[];self.fail_enter=False;self.fail_read=False;self.fail_restore=False;self.box=[1500,825,2874,1634]
 def SetThreadDpiAwarenessContext(self,context):
  self.contexts.append(context)
  if len(self.contexts)==1:return None if self.fail_enter else 123
  return None if self.fail_restore else 456
 def GetWindowRect(self,hwnd,pointer):
  if self.fail_read:return False
  rect=ctypes.cast(pointer,ctypes.POINTER(wintypes.RECT)).contents
  rect.left,rect.top,rect.right,rect.bottom=self.box;return True
class GeometryTests(unittest.TestCase):
 def test_physical_pixels_not_logical_bounds(self):
  api=User32();row=physical_window_rect(7,api)
  self.assertEqual(row['rect'],[1500,825,2874,1634]);self.assertEqual(row['coordinate_space'],'physical-desktop-pixels')
  self.assertEqual(ctypes.c_ssize_t(api.contexts[0].value).value,-4);self.assertEqual(api.contexts[-1],123)
  self.assertTrue(row['rect'][0]<2186<row['rect'][2] and row['rect'][1]<1256<row['rect'][3])
 def test_restore_on_read_failure(self):
  api=User32();api.fail_read=True
  with self.assertRaisesRegex(RuntimeError,'读取失败'):physical_window_rect(7,api)
  self.assertEqual(api.contexts[-1],123)
 def test_unknown_dpi_never_returns_assumed_bounds(self):
  api=User32();api.fail_enter=True
  with self.assertRaisesRegex(RuntimeError,'未知'):physical_window_rect(7,api)
  self.assertEqual(len(api.contexts),1)
 def test_restore_failure_rejects_result(self):
  api=User32();api.fail_restore=True
  with self.assertRaisesRegex(RuntimeError,'恢复'):physical_window_rect(7,api)
 def test_invalid_rectangle_rejected_after_restore(self):
  api=User32();api.box=[0,0,0,0]
  with self.assertRaisesRegex(RuntimeError,'无效'):physical_window_rect(7,api)
  self.assertEqual(api.contexts[-1],123)
 def test_invalid_handle_never_calls_api(self):
  api=User32()
  for value in [0,-1,True,None]:
   with self.assertRaises(ValueError):physical_window_rect(value,api)
  self.assertEqual(api.contexts,[])
if __name__=='__main__':unittest.main(verbosity=2)
