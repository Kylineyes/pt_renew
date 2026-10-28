"""指示层并发心跳顺序复现与保守边界，不创建真实窗口。"""
from pathlib import Path
import sys,types,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_indicator_health import indicator_healthy

class HealthTests(unittest.TestCase):
 def make(self,heartbeat=10.):
  return types.SimpleNamespace(heartbeat=heartbeat,thread=types.SimpleNamespace(is_alive=lambda:True),stopping=False,error=None)
 def test_old_read_order_false_negative_reproduced(self):
  obj=self.make(10.)
  def racing_clock():obj.heartbeat=10.0001;return 10.
  # 原is_healthy表达式的求值顺序，可把更新后的heartbeat与更早now相减。
  old=0<=racing_clock()-obj.heartbeat<=1.
  self.assertFalse(old)
  obj.heartbeat=10.
  self.assertTrue(indicator_healthy(obj,racing_clock))
 def test_stale_remains_unhealthy(self):
  self.assertFalse(indicator_healthy(self.make(8.),lambda:10.))
 def test_future_remains_unhealthy(self):
  self.assertFalse(indicator_healthy(self.make(11.),lambda:10.))
 def test_boundary_keeps_original_one_second(self):
  self.assertTrue(indicator_healthy(self.make(9.),lambda:10.))
  self.assertFalse(indicator_healthy(self.make(8.999),lambda:10.))
 def test_dead_stopping_and_faulted_remain_unhealthy(self):
  for attr,value in [('stopping',True),('error',RuntimeError('失败'))]:
   obj=self.make();setattr(obj,attr,value);self.assertFalse(indicator_healthy(obj,lambda:10.))
  obj=self.make();obj.thread.is_alive=lambda:False;self.assertFalse(indicator_healthy(obj,lambda:10.))
  self.assertFalse(indicator_healthy(None,lambda:10.))
if __name__=='__main__':unittest.main(verbosity=2)
