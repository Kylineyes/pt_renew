"""App缓存修复的真实Desktop方法回归；所有窗口/激活API均为假实现。"""
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_app_refresh import install_app_refresh
from windows_mcp.desktop import service


class AppRefreshTests(unittest.TestCase):
    def make(self, current='PT Renew 控制诊断试验'):
        class IsolatedDesktop(service.Desktop):
            pass
        obj=IsolatedDesktop.__new__(IsolatedDesktop)
        obj.desktop_state=types.SimpleNamespace(active_window=types.SimpleNamespace(name='旧窗口',handle=1),windows=[])
        self.refreshed=0;self.activated=[]
        self.window=types.SimpleNamespace(name=current,handle=2,status=service.Status.NORMAL)
        def refresh():
            self.refreshed+=1
            obj.desktop_state=types.SimpleNamespace(active_window=self.window,windows=[self.window])
        obj.get_state=refresh
        obj.bring_window_to_top=lambda h:self.activated.append(h)
        return obj,IsolatedDesktop

    def test_original_stale_cache_reproduced_then_fixed(self):
        obj,cls=self.make()
        # 非空旧缓存触发现场相同not found，尚未激活任何窗口。
        obj.desktop_state.windows=[obj.desktop_state.active_window]
        before,code=obj.switch_app(self.window.name)
        self.assertEqual(code,1);self.assertEqual(self.refreshed,0);self.assertEqual(self.activated,[])
        install_app_refresh(cls)
        with patch.object(service.uia,'IsIconic',return_value=False),patch.object(service.win32gui,'GetForegroundWindow',return_value=2):
            after,code=obj.switch_app(self.window.name)
        self.assertEqual(code,0);self.assertEqual(self.refreshed,1);self.assertEqual(self.activated,[2])

    def test_missing_target_remains_failure(self):
        obj,cls=self.make('完全无关窗口');install_app_refresh(cls)
        text,code=obj.switch_app('PT Renew 控制诊断试验')
        self.assertEqual(code,1);self.assertEqual(self.activated,[])

    def test_refresh_error_prevents_activation(self):
        obj,cls=self.make();install_app_refresh(cls)
        def broken():raise RuntimeError('模拟窗口枚举失败')
        obj.get_state=broken
        with self.assertRaisesRegex(RuntimeError,'枚举失败'):obj.switch_app(self.window.name)
        self.assertEqual(self.activated,[])

    def test_activation_denied_still_fails_postcheck(self):
        obj,cls=self.make();install_app_refresh(cls)
        with patch.object(service.uia,'IsIconic',return_value=False),patch.object(service.win32gui,'GetForegroundWindow',return_value=1),patch.object(service,'perf_counter',side_effect=[0,2]):
            text,code=obj.switch_app(self.window.name)
        self.assertEqual(code,1);self.assertIn('Failed to bring',text)

    def test_second_install_refused(self):
        obj,cls=self.make();install_app_refresh(cls)
        with self.assertRaises(RuntimeError):install_app_refresh(cls)


if __name__=='__main__':unittest.main(verbosity=2)
