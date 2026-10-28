"""验证实验批准、默认关闭、加载顺序和退出审计；服务/窗口全部使用假对象。"""
import builtins
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import run_control_diagnostics as launcher
import control_bitmap_surface as surface
from test_control_bitmap_surface import Fixture, INDICATOR_THREAD

TOOLS=Path(launcher.__file__).parent
REQUIRED=('run_control_diagnostics.py','control_diagnostics.py','control_indicator_health.py',
          'control_bitmap_surface.py','control_bitmap_surface_model.py')


class LauncherSurfaceTests(unittest.TestCase):
    @contextmanager
    def package(self, *, supported=True):
        with tempfile.TemporaryDirectory(prefix='pt-surface-approval-') as directory:
            root=Path(directory)
            package=root/'windows_mcp'
            (package/'desktop').mkdir(parents=True)
            original=Path(next(iter(importlib.util.find_spec('windows_mcp').submodule_search_locations)))
            for name in surface.SUPPORTED_SOURCES:
                (package/name).write_bytes((original/name).read_bytes() if supported else '不支持的源码'.encode('utf-8'))
            manifest=root/'package-manifest.json'
            manifest.write_text(json.dumps(dict(files=launcher.digest(package))),encoding='utf-8')
            approval=dict(mode='diagnostics-only',task_id='纯离线假任务',dispatch_id='纯离线假派发',
                          package_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                          launcher_files={name:hashlib.sha256((TOOLS/name).read_bytes()).hexdigest() for name in REQUIRED},
                          indicator_bitmap_surface=True,indicator_health_sampling=True,indicator_health_fix=True,
                          permission_confirmed=True,permission='纯离线测试许可字段',message_id='msg_假批准',
                          diagnostic_seconds=600,total_seconds=900)
            yield root,approval

    def write_approval(self,root,approval):
        path=root/'approval.json'
        path.write_text(json.dumps(approval),encoding='utf-8')
        return path

    def refuse(self,root,approval,reason):
        with patch.object(launcher,'TraceWriter',side_effect=AssertionError('拒绝应在创建trace前完成')):
            with self.assertRaisesRegex(RuntimeError,reason):
                launcher.serve(root,root/'trace.jsonl',self.write_approval(root,approval))

    def test_option_requires_boolean_and_frozen_sampling_fix_and_all_modules(self):
        for value in ('false',1,None):
            with self.subTest(value=value),self.package() as (root,approval):
                approval['indicator_bitmap_surface']=value
                self.refuse(root,approval,'必须是布尔值')
        for field in ('indicator_health_sampling','indicator_health_fix'):
            with self.subTest(field=field),self.package() as (root,approval):
                approval[field]=False
                self.refuse(root,approval,'必须同时')
        for name in REQUIRED:
            with self.subTest(name=name),self.package() as (root,approval):
                del approval['launcher_files'][name]
                self.refuse(root,approval,'批准|冻结')
        for field,value in (('permission_confirmed',False),('message_id',None),('permission',''),('total_seconds',1800)):
            with self.subTest(field=field),self.package() as (root,approval):
                approval[field]=value
                self.refuse(root,approval,'本轮明确桌面许可')

    def test_old_bitmap_timing_conflicts_with_surface_experiment(self):
        with self.package() as (root,approval):
            approval['indicator_bitmap_timing']=True
            approval['launcher_files']['control_bitmap_timing.py']=hashlib.sha256((TOOLS/'control_bitmap_timing.py').read_bytes()).hexdigest()
            self.refuse(root,approval,'不能同时启用旧位图计时')

    def test_unsupported_package_or_tampered_core_refused_before_import(self):
        with self.package(supported=False) as (root,approval):
            self.refuse(root,approval,'不支持当前控制包源码')
        with self.package() as (root,approval):
            approval['launcher_files']['control_bitmap_surface_model.py']='0'*64
            self.refuse(root,approval,'审阅后变化')

    @contextmanager
    def fake_runtime(self,root,case,main):
        calls=[]
        modules={name:types.ModuleType(name) for name in
                 ('windows_mcp','windows_mcp.desktop','windows_mcp.uia','windows_mcp.uia.core','windows_mcp.__main__')}
        package=root/'windows_mcp'
        control=types.SimpleNamespace(__file__=str(package/'desktop/control.py'))
        case.overlay.__file__=str(package/'desktop/control_overlay.py')
        case.flash.__file__=str(package/'desktop/flash_overlay.py')
        desktop=modules['windows_mcp.desktop']
        desktop.control,desktop.control_overlay,desktop.service=control,case.overlay,types.SimpleNamespace()
        modules['windows_mcp'].desktop=desktop
        modules['windows_mcp'].uia=modules['windows_mcp.uia']
        modules['windows_mcp.uia'].core=modules['windows_mcp.uia.core']
        modules['windows_mcp.__main__'].main=lambda *args,**kwargs:(calls.append('main'),main())[-1]
        case.trace.close=lambda:calls.append('trace-close')
        original_install=surface.install_bitmap_surface
        def install(overlay,trace):
            calls.append('surface')
            case.manager=original_install(overlay,trace,api_factory=case.factory)
            return case.manager
        def health(overlay,*args,**kwargs):
            calls.append('health')
            self.assertTrue(overlay._pt_bitmap_surface_installed)
            self.assertTrue(kwargs['heartbeat_first'])
        with patch.dict(sys.modules,modules),patch.object(launcher,'TraceWriter',return_value=case.trace),\
             patch.object(launcher,'install',side_effect=lambda *args:calls.append('diagnostics')),\
             patch.object(surface,'install_bitmap_surface',side_effect=install),\
             patch('control_indicator_health.install_indicator_health',side_effect=health):
            yield calls

    def test_default_off_does_not_import_or_install_surface(self):
        case=Fixture()
        with self.package() as (root,approval):
            for name in ('indicator_bitmap_surface','indicator_health_sampling','indicator_health_fix'):
                del approval[name]
            approval['launcher_files']={}
            original_import=builtins.__import__;imports=[]
            def observe(name,*args,**kwargs):
                imports.append(name)
                return original_import(name,*args,**kwargs)
            with self.fake_runtime(root,case,lambda:None) as calls,patch('builtins.__import__',side_effect=observe):
                launcher.serve(root,root/'trace.jsonl',self.write_approval(root,approval))
            self.assertEqual(calls,['diagnostics','main','trace-close'])
            self.assertNotIn('control_bitmap_surface',imports)
            self.assertFalse(case.system.calls)
            self.assertFalse(hasattr(case.overlay,'_pt_bitmap_surface_installed'))

    def test_approved_install_precedes_health_and_shutdown_verifies_zero_ledger(self):
        case=Fixture()
        def main():
            thread=threading.current_thread();previous=thread.name;thread.name=INDICATOR_THREAD
            try:
                layer=case.layer();layer.set_opacity(80);layer.close()
            finally:thread.name=previous
        with self.package() as (root,approval),self.fake_runtime(root,case,main) as calls:
            launcher.serve(root,root/'trace.jsonl',self.write_approval(root,approval))
        self.assertEqual(calls,['diagnostics','surface','health','main','trace-close'])
        self.assertTrue(case.system.balanced())
        row=next(row for row in case.rows if row['event']=='indicator-surface-shutdown')
        self.assertTrue(row['balanced'])
        self.assertFalse(row['resources']['failed'])

    def test_unretired_resources_make_serve_fail_but_trace_still_closes_without_native_cleanup(self):
        case=Fixture()
        def main():
            thread=threading.current_thread();previous=thread.name;thread.name=INDICATOR_THREAD
            try:case.layer()
            finally:thread.name=previous
        with self.package() as (root,approval),self.fake_runtime(root,case,main) as calls:
            with self.assertRaisesRegex(RuntimeError,'账本未清空'):
                launcher.serve(root,root/'trace.jsonl',self.write_approval(root,approval))
        self.assertEqual(calls[-1],'trace-close')
        self.assertEqual(case.system.counts['DeleteObject'],0)
        self.assertEqual(case.manager.snapshot()['bitmap_count'],1)
        self.assertEqual(case.manager.retire_owner(),[])
        self.assertTrue(case.system.balanced())


if __name__=='__main__':
    unittest.main(verbosity=2)
