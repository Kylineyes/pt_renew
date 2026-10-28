"""以假API验证位图细分计时，不导入Win32包，不创建窗口或截图。"""
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_bitmap_timing import install_bitmap_timing


class BitmapTimingTests(unittest.TestCase):
    def make(self):
        self.elapsed=0.
        self.calls=[]
        self.rows=[]
        flash=types.SimpleNamespace()
        def api(name):
            def invoke(*args):
                self.calls.append((name,args));self.elapsed+=.01
                if name==getattr(self,'fail',None):raise OSError('原始错误')
                return 7
            return invoke
        for group,names in {
            '_user32':('GetDC','UpdateLayeredWindow','ReleaseDC'),
            '_gdi32':('CreateCompatibleDC','CreateDIBSection','SelectObject','DeleteObject','DeleteDC'),
            'ctypes':('memmove',),
        }.items():
            setattr(flash,group,types.SimpleNamespace(**{name:api(name) for name in names},untouched='原字段'))
        def push(hwnd,x,y,w,h,bgra,*,opacity=255):
            dc=flash._user32.GetDC(None)
            memory=flash._gdi32.CreateCompatibleDC(dc)
            bitmap=flash._gdi32.CreateDIBSection(dc)
            try:
                flash.ctypes.memmove(1,bgra,len(bgra))
                old=flash._gdi32.SelectObject(memory,bitmap)
                try:return flash._user32.UpdateLayeredWindow(hwnd,opacity)
                finally:flash._gdi32.SelectObject(memory,old)
            finally:
                flash._gdi32.DeleteObject(bitmap)
                flash._gdi32.DeleteDC(memory)
                flash._user32.ReleaseDC(None,dc)
        flash._push_bitmap=push
        trace=types.SimpleNamespace(emit=lambda event,**fields:self.rows.append(dict(event=event,**fields)))
        return flash,trace

    def run_indicator(self,action):
        with patch('control_bitmap_timing.threading.current_thread',return_value=types.SimpleNamespace(name='windows-mcp-control-indicator')):
            return action()

    def test_api_results_arguments_counts_and_shared_objects_preserved(self):
        flash,trace=self.make();original=flash._user32;original_api=original.GetDC
        install_bitmap_timing(flash,trace,clock=lambda:self.elapsed)
        self.assertEqual(self.run_indicator(lambda:flash._push_bitmap(99,1,2,2,2,b'abcd'*4,opacity=80)),7)
        row=self.rows[-1]
        self.assertEqual(row['stages']['SelectObject']['calls'],2)
        self.assertEqual(row['bgra_bytes'],16)
        self.assertAlmostEqual(row['duration_seconds'],.10)
        self.assertAlmostEqual(row['measured_api_seconds'],.10)
        self.assertEqual(self.calls[5],('UpdateLayeredWindow',(99,80)))
        self.assertIs(original.GetDC,original_api)
        self.assertEqual(flash._user32.untouched,'原字段')
        self.assertNotIn('hwnd',row)
        self.assertNotIn('bgra',row)
        self.assertEqual(len(self.rows),2)

    def test_original_error_and_cleanup_propagate_and_next_call_resets(self):
        flash,trace=self.make();install_bitmap_timing(flash,trace,clock=lambda:self.elapsed)
        self.fail='UpdateLayeredWindow'
        with self.assertRaisesRegex(OSError,'原始错误'):
            self.run_indicator(lambda:flash._push_bitmap(1,0,0,1,1,b'1234'))
        row=self.rows[-1]
        self.assertEqual(row['exception'],'OSError')
        for name in ('DeleteObject','DeleteDC','ReleaseDC'):self.assertEqual(row['stages'][name]['calls'],1)
        self.fail=None
        self.run_indicator(lambda:flash._push_bitmap(1,0,0,1,1,b'1234'))
        self.assertIsNone(self.rows[-1]['exception'])
        self.assertEqual(self.rows[-1]['stages']['GetDC']['calls'],1)

    def test_other_thread_and_api_outside_upload_never_recorded(self):
        flash,trace=self.make();install_bitmap_timing(flash,trace,clock=lambda:self.elapsed)
        flash._push_bitmap(1,0,0,1,1,b'1234')
        self.run_indicator(lambda:flash._user32.GetDC(None))
        self.assertEqual(len(self.rows),1)
        self.assertEqual(len(self.calls),11)

    def test_missing_api_fails_before_replacing_any_reference(self):
        flash,trace=self.make();original=flash._user32
        del flash._gdi32.CreateDIBSection
        with self.assertRaises(AttributeError):install_bitmap_timing(flash,trace)
        self.assertIs(flash._user32,original)
        self.assertFalse(getattr(flash,'_pt_bitmap_timing_installed',False))

    def test_double_install_refused(self):
        flash,trace=self.make();install_bitmap_timing(flash,trace)
        with self.assertRaisesRegex(RuntimeError,'不可重复'):install_bitmap_timing(flash,trace)


if __name__=='__main__':unittest.main(verbosity=2)
