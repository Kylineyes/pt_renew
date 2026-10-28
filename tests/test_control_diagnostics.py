"""诊断包装回归：保持真实控制器拒绝与输入账本语义，测试不安装钩子。"""
from pathlib import Path
import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_diagnostics import TraceWriter, install


class DiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from windows_mcp.desktop import control, control_overlay
        # 只包装实际控制器；桌面服务/指针用假实现，绝不调用输入API。
        class Desktop:
            def get_screenshot(self):return types.SimpleNamespace(size=(32,32))
        cls.control=control
        cls.sink=tempfile.TemporaryDirectory(prefix='pt-control-trace-')
        cls.path=Path(cls.sink.name)/'trace.jsonl'
        cls.trace=TraceWriter(cls.path)
        cls.desktop=types.SimpleNamespace(Desktop=Desktop)
        cls.moves=[]
        cls.uia=types.SimpleNamespace(SetCursorPos=lambda *a:cls.moves.append(a))
        cls.owner=install(control,control_overlay,cls.desktop,cls.uia,cls.trace)

    @classmethod
    def tearDownClass(cls):
        cls.trace.close()
        lines=[json.loads(s) for s in cls.path.read_text(encoding='utf-8').splitlines()]
        assert any(e['event']=='capture-pause-enter' for e in lines)
        assert any(e['event']=='begin_call-error' and e.get('code')=='USER_CONTROL' for e in lines)
        assert not any('vkCode' in e or 'text' in e for e in lines)
        cls.sink.cleanup()

    def make(self,state='ready'):
        obj=self.control.ControlCoordinator()
        obj._state=state
        obj._last_physical_event=-100
        obj._last_user=-100
        return obj

    def test_user_refusal_original_code_and_state_preserved(self):
        obj=self.make('user');obj._last_user=1_000_000_000
        with self.assertRaises(self.control.ControlBlocked) as caught:obj.begin_call('Snapshot')
        self.assertEqual(caught.exception.code,'USER_CONTROL')
        self.assertEqual(obj._state,'user')
        self.assertEqual(caught.exception.status['diagnostics']['state'],'user')
        self.assertEqual(obj._active_calls,0)

    def test_capture_pause_still_blocks_new_call(self):
        obj=self.make('ai');obj._lease_until=1_000_000_000
        obj._visual_armed=True
        token=obj.pause_for_capture()
        self.assertTrue(obj._visual_paused)
        self.assertTrue(obj.input_ledger._blocked)
        with self.assertRaises(self.control.ControlBlocked) as caught:obj.begin_call('Click')
        self.assertEqual(caught.exception.code,'CONTROL_UNAVAILABLE')
        self.assertTrue(caught.exception.status['diagnostics']['visual_paused'])
        obj.resume_after_capture(token,restored=True)
        self.assertFalse(obj._visual_paused)

    def test_held_key_remains_blocked_and_not_leaked_in_status(self):
        obj=self.make();obj._pressed.add(192)
        with self.assertRaises(self.control.ControlBlocked) as caught:obj.begin_call('Snapshot')
        self.assertEqual(caught.exception.code,'PHYSICAL_INPUT_HELD')
        self.assertEqual(obj._pressed,{192})
        fields=caught.exception.status['diagnostics']
        self.assertEqual(fields['pressed_count'],1)
        self.assertNotIn('pressed_vks',fields)

    def test_fail_open_never_enables_lease(self):
        obj=self.make('ai');obj._suppress=True
        obj._fail_open()
        self.assertFalse(obj._suppress)
        self.assertTrue(obj._emergency)
        self.assertTrue(obj.input_ledger._blocked)
        with self.assertRaises(self.control.ControlBlocked):obj.begin_call('Click')

    def test_queued_physical_event_still_changes_user_state(self):
        obj=self.make('ai');obj._lease_until=1_000_000_000
        obj._visual_armed=False
        obj._handle(('key',))
        self.assertEqual(obj._state,'user')

    def test_screenshot_wrapper_preserves_result(self):
        value=self.desktop.Desktop().get_screenshot()
        self.assertEqual(value.size,(32,32))
        self.assertEqual(self.moves,[])

    def test_trace_is_bounded_and_reports_loss(self):
        with tempfile.TemporaryDirectory(prefix='pt-bounded-trace-') as tmp:
            trace=TraceWriter(Path(tmp)/'small.jsonl',capacity=2)
            # 工作线程被暂时阻止排空时，写端仍不等待I/O。
            with patch.object(trace,'_drain'):
                for n in range(10):trace.emit('sample',sample=n)
                self.assertLessEqual(len(trace.rows),2)
                self.assertGreater(trace.dropped,0)
            trace.close()


if __name__=='__main__':unittest.main(verbosity=2)
