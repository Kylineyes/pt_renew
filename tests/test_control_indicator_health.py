"""指示层并发心跳顺序复现与保守边界，不创建真实窗口。"""
from pathlib import Path
import sys,types,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_indicator_health import indicator_healthy, indicator_health_sample, install_indicator_health
import threading

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
 def test_sample_exposes_the_values_that_caused_original_race(self):
  obj=self.make()
  def clock():obj.heartbeat=10.0001;return 10.
  sample=indicator_health_sample(obj,clock)
  self.assertFalse(sample['healthy'])
  self.assertEqual(sample['now'],10.)
  self.assertEqual(sample['heartbeat'],10.0001)
  self.assertLess(sample['heartbeat_age_seconds'],0)
  obj.heartbeat=10.
  fixed=indicator_health_sample(obj,clock,heartbeat_first=True)
  self.assertTrue(fixed['healthy'])
  self.assertEqual(fixed['heartbeat'],10.)
 def test_original_short_circuit_does_not_read_clock_after_fault(self):
  for attr,value in [('stopping',True),('error',RuntimeError('失败'))]:
   obj=self.make();setattr(obj,attr,value)
   def clock():raise AssertionError('原短路路径不得取时间')
   sample=indicator_health_sample(obj,clock)
   self.assertFalse(sample['healthy'])
   self.assertIsNone(sample['heartbeat'])
 def make_overlay(self):
  obj=self.make();obj.thread.ident=threading.get_ident()
  def operation(*args):return '原结果'
  layer=type('Layer',(),{n:staticmethod(operation) for n in ('set_opacity','show','hide','move','close')})
  indicator=type('Indicator',(),{'change':staticmethod(operation)})
  return types.SimpleNamespace(_lock=threading.Lock(),_instance=obj,
   _monitor_rects=operation,_build_layers=operation,_Layer=layer,_Indicator=indicator,
   flash_overlay=types.SimpleNamespace(_pump_messages=operation))
 def test_installed_baseline_and_fix_use_actual_sample(self):
  for fixed,expected in [(False,False),(True,True)]:
   overlay=self.make_overlay();rows=[]
   trace=types.SimpleNamespace(emit=lambda event,**fields:rows.append(dict(event=event,**fields)))
   def clock():overlay._instance.heartbeat=10.0001;return 10.
   install_indicator_health(overlay,trace,heartbeat_first=fixed,clock=clock)
   self.assertEqual(overlay.is_healthy(),expected)
   row=rows[-1]
   self.assertEqual(row['healthy'],expected)
   self.assertEqual(row['heartbeat'],10. if fixed else 10.0001)
   with self.assertRaises(RuntimeError):install_indicator_health(overlay)
 def test_phase_wrapper_preserves_result_exception_and_restores_phase(self):
  overlay=self.make_overlay();rows=[]
  def failure():raise ValueError('原异常')
  overlay._build_layers=failure
  trace=types.SimpleNamespace(emit=lambda event,**fields:rows.append(dict(event=event,**fields)))
  install_indicator_health(overlay,trace,heartbeat_first=False,phases=True)
  self.assertEqual(overlay._monitor_rects(),'原结果')
  with self.assertRaisesRegex(ValueError,'原异常'):overlay._build_layers()
  self.assertEqual(rows[-1]['exception'],'ValueError')
  overlay.is_healthy()
  self.assertIsNone(rows[-1]['phase'])
 def test_inflight_phase_is_visible_to_health_sample(self):
  overlay=self.make_overlay();rows=[]
  overlay._monitor_rects=lambda:overlay.is_healthy()
  trace=types.SimpleNamespace(emit=lambda event,**fields:rows.append(dict(event=event,**fields)))
  install_indicator_health(overlay,trace,phases=True)
  overlay._monitor_rects()
  sample=next(r for r in rows if r['event']=='indicator-health-sample')
  self.assertEqual(sample['phase']['name'],'_monitor_rects')
  self.assertGreaterEqual(sample['phase_age_seconds'],0)
if __name__=='__main__':unittest.main(verbosity=2)
