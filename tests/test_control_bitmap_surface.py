"""用原源码的类/循环与假Win32返回值验证资源实验，不创建窗口、钩子或输入。"""
import ast
from copy import deepcopy
from collections import Counter
from contextlib import contextmanager
import ctypes
import hashlib
import importlib.util
import logging
from pathlib import Path
import sys
import threading
import time
import types
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from control_bitmap_surface import (INDICATOR_THREAD, NativeBitmapApi, NativeCallError,
                                    SUPPORTED_SOURCES, install_bitmap_surface)
from control_bitmap_surface_model import BitmapSurfaceModel
from audit_control_surfaces import audit


def source_nodes(relative, names):
    package=Path(next(iter(importlib.util.find_spec('windows_mcp').submodule_search_locations)))
    path=package/relative
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==SUPPORTED_SOURCES[relative], '原测试源码版本变化'
    parsed=ast.parse(raw.decode('utf-8'))
    selected=[node for node in parsed.body if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names]
    return ast.Module(body=selected,type_ignores=[])


def make_flash():
    names={'_POINT','_SIZE','_BLENDFUNCTION','_BITMAPINFOHEADER','_BITMAPINFO'}
    namespace=dict(ctypes=ctypes)
    exec(compile(source_nodes('desktop/flash_overlay.py',names),'<冻结位图结构>','exec'),namespace)
    return types.SimpleNamespace(**{name:namespace[name] for name in names},
        _BI_RGB=0,_DIB_RGB_COLORS=0,_AC_SRC_OVER=0,_AC_SRC_ALPHA=1,_ULW_ALPHA=2,
        _SW_SHOWNA=8,_HWND_TOPMOST=-1,_SWP_NOSIZE=1,_SWP_NOMOVE=2,_SWP_NOACTIVATE=16,_SWP_SHOWWINDOW=64)


class Function:
    def __init__(self, invoke):self.invoke=invoke
    def __call__(self,*args):return self.invoke(*args)


class NativeSystem:
    def __init__(self):
        self.calls=[]
        self.counts=Counter()
        self.program={}
        self.next_handle=100
        self.screens=set()
        self.memory={}
        self.bitmaps={}
        self.frames=[]
        self.headers=[]
        self.error_code=87
        self.before=None

    def libraries(self):
        def function(name):return Function(lambda *args:self.call(name,*args))
        return (types.SimpleNamespace(**{name:function(name) for name in ('GetDC','ReleaseDC','UpdateLayeredWindow')}),
                types.SimpleNamespace(**{name:function(name) for name in
                    ('CreateCompatibleDC','CreateDIBSection','SelectObject','DeleteObject','DeleteDC')}))

    def handle(self):
        self.next_handle+=1
        return self.next_handle

    def call(self,name,*args):
        self.calls.append((name,args))
        self.counts[name]+=1
        if self.before:self.before(name)
        programmed=self.program.get((name,self.counts[name]),'正常')
        if programmed!='正常' and programmed!='空像素':return programmed
        if name=='GetDC':
            value=self.handle();self.screens.add(value);return value
        if name=='ReleaseDC':self.screens.remove(args[1]);return 1
        if name=='CreateCompatibleDC':
            assert args[0] in self.screens
            value=self.handle();self.memory[value]=7;return value
        if name=='CreateDIBSection':
            header=args[1]._obj.bmiHeader
            self.headers.append((header.biWidth,header.biHeight,header.biPlanes,header.biBitCount,header.biCompression))
            value=self.handle()
            data=ctypes.create_string_buffer(header.biWidth*(-header.biHeight)*4+1)
            self.bitmaps[value]=data
            args[3]._obj.value=None if programmed=='空像素' else ctypes.addressof(data)
            return value
        if name=='SelectObject':
            memory,bitmap=args
            assert bitmap==7 or bitmap in self.bitmaps
            original=self.memory[memory];self.memory[memory]=bitmap;return original
        if name=='DeleteDC':del self.memory[args[0]];return 1
        if name=='DeleteObject':
            assert args[0] not in self.memory.values(), '位图仍被选中'
            del self.bitmaps[args[0]];return 1
        if name=='UpdateLayeredWindow':
            target,screen,pos,size,memory,origin,color,blend,flags=args
            assert screen in self.screens
            data=self.bitmaps[self.memory[memory]].raw
            self.frames.append(dict(target=target,x=pos._obj.x,y=pos._obj.y,width=size._obj.cx,
                                    height=size._obj.cy,source=(origin._obj.x,origin._obj.y),
                                    opacity=blend._obj.SourceConstantAlpha&255,
                                    alpha=blend._obj.AlphaFormat,flags=flags,pixels=data[:-1]))
            return 1
        raise AssertionError(name)

    def balanced(self):return not self.screens and not self.memory and not self.bitmaps


class Fixture:
    def __init__(self):
        self.system=NativeSystem()
        self.flash=make_flash()
        self.rows=[]
        self.events=[]
        self.trace=types.SimpleNamespace(emit=lambda event,**values:self.rows.append(dict(event=event,**values)))
        self.original_uploads=[]
        self.flash._push_bitmap=lambda *args,**kwargs:self.original_uploads.append((args,kwargs))
        self.flash._pump_messages=lambda hwnd:self.events.append(('pump',hwnd))
        self.flash._create_layered_window=self.create_window
        self.api_objects=[]
        self.visible=set()
        user=types.SimpleNamespace(SetWindowDisplayAffinity=lambda *args:1,
                                   ShowWindow=self.show,SetWindowPos=lambda *args:1,
                                   IsWindowVisible=lambda hwnd:hwnd in self.visible,
                                   DestroyWindow=self.destroy,UnregisterClassW=lambda *args:1,
                                   GetCursorPos=lambda point:1)
        namespace=dict(ctypes=ctypes,wintypes=ctypes.wintypes,threading=threading,time=time,
                       logger=logging.getLogger('纯离线资源测试'),flash_overlay=self.flash,_user32=user,
                       _WDA_EXCLUDEFROMCAPTURE=17,_SW_HIDE=0,_REFRESH_SECONDS=.05,
                       _BORDER=2,_NOTICE_GLOW_PAD=1,_CURSOR_SIZE=2,_AMBER=(1,2,3),_BLUE=(4,5,6),
                       _edge_bitmap=lambda w,h,*args:b'a'*(w*h*4),_notice_bitmap=lambda width:None,
                       _cursor_bitmap=lambda color:b'c'*16,_breath_opacity=lambda elapsed:128)
        exec(compile(source_nodes('desktop/control_overlay.py',{'_Layer','_Indicator','_build_layers'}),
                     '<冻结原图层及显示循环>','exec'),namespace)
        self.namespace=namespace
        self.overlay=types.SimpleNamespace(_Layer=namespace['_Layer'],_Indicator=namespace['_Indicator'],
                                           flash_overlay=self.flash,_instance=None)

    def create_window(self,*args):
        handle=self.system.handle()
        self.events.append(('create-window',handle))
        return handle,1

    def show(self,hwnd,mode):
        if mode:self.visible.add(hwnd)
        else:self.visible.discard(hwnd)
        self.events.append(('show' if mode else 'hide',hwnd))

    def destroy(self,hwnd):
        self.events.append(('destroy-window',hwnd))
        self.visible.discard(hwnd)
        return 1

    def factory(self,flash,record):
        api=NativeBitmapApi(flash,record,libraries=self.system.libraries(),last_error=lambda:self.system.error_code)
        self.api_objects.append(api)
        return api

    def install(self,**kwargs):
        self.manager=install_bitmap_surface(self.overlay,self.trace,api_factory=self.factory,**kwargs)
        return self.manager

    def layer(self,pixels=b'12345678'):
        return self.overlay._Layer(1,2,2,1,pixels,'测试')


class NativeSurfaceTests(unittest.TestCase):
    @contextmanager
    def indicator_thread(self):
        thread=threading.current_thread()
        previous=thread.name
        thread.name=INDICATOR_THREAD
        try:
            yield
        finally:
            thread.name=previous

    def test_native_structures_pixels_alpha_and_resource_balance(self):
        case=Fixture();manager=case.install()
        with self.indicator_thread():
            layer=case.layer()
            layer.set_opacity(80)
            layer.move(10,20)
            layer.set_opacity(0)
            layer.set_opacity(0)
            self.assertEqual(len(case.system.frames),3)
            self.assertEqual(case.system.headers,[(2,-1,1,32,0)])
            for frame in case.system.frames:
                self.assertEqual(frame['pixels'],b'12345678')
                self.assertEqual((frame['source'],frame['alpha'],frame['flags']),((0,0),1,2))
            self.assertEqual(case.system.frames[-1]['opacity'],0)
            self.assertEqual((case.system.frames[-1]['x'],case.system.frames[-1]['y']),(10,20))
            self.assertFalse(case.original_uploads)
            layer.close()
            manager.audit_shutdown()
        self.assertTrue(case.system.balanced())
        self.assertEqual(case.system.counts,Counter(GetDC=4,ReleaseDC=4,CreateCompatibleDC=1,
                         CreateDIBSection=1,SelectObject=2,UpdateLayeredWindow=3,DeleteObject=1,DeleteDC=1))
        operations=[row for row in case.rows if row['event']=='indicator-surface-operation']
        self.assertEqual(sum(row['stages'].get('memmove',{}).get('calls',0) for row in operations),1)
        self.assertTrue(all('hwnd' not in row and 'pixels' not in row for row in case.rows))
        self.assertTrue(all(row['finished']>=row['started'] for row in operations))

    def test_zero_null_and_hgdi_error_returns_never_clear_ownership(self):
        for name,value in [('GetDC',None),('GetDC',0),('CreateCompatibleDC',0),('CreateDIBSection',0),
                           ('SelectObject',0),('SelectObject',-1),('SelectObject',ctypes.c_void_p(-1).value),
                           ('UpdateLayeredWindow',0),('ReleaseDC',0)]:
            case=Fixture();manager=case.install();case.system.program[(name,1)]=value
            with self.subTest(name=name,value=value),self.indicator_thread():
                with self.assertRaises(NativeCallError) as caught:case.layer()
                self.assertEqual(caught.exception.api,name)
                self.assertEqual(caught.exception.native_error,87)
                self.assertTrue(case.system.balanced())
                self.assertTrue(manager.failed)
                self.assertEqual(manager.snapshot()['surfaces'],0)
                with self.assertRaises(RuntimeError):manager.audit_shutdown()

    def test_successful_bitmap_with_null_bits_is_retired_without_copy(self):
        case=Fixture();manager=case.install()
        case.system.program[('CreateDIBSection',1)]='空像素'
        with self.indicator_thread(),self.assertRaisesRegex(OSError,'空像素'):case.layer()
        self.assertTrue(case.system.balanced())
        self.assertEqual(case.system.counts['SelectObject'],0)
        self.assertEqual(case.system.counts['DeleteObject'],1)
        self.assertFalse(case.system.frames)
        self.assertEqual(manager.snapshot()['surfaces'],0)

    def test_constructor_pending_resources_retained_until_owner_cleanup(self):
        case=Fixture();manager=case.install()
        case.system.program.update({('CreateDIBSection',1):'空像素',('DeleteObject',1):0,('DeleteObject',2):0})
        with self.indicator_thread():
            with self.assertRaises(BaseExceptionGroup):case.layer()
            self.assertEqual(manager.snapshot()['bitmap_count'],1)
            self.assertEqual(manager.snapshot()['surfaces'],1)
            self.assertFalse(any(name=='destroy-window' for name,hwnd in case.events))
            with self.assertRaises(RuntimeError):manager.audit_shutdown()
            self.assertEqual(manager.retire_owner(),[])
        self.assertTrue(case.system.balanced())
        self.assertEqual(manager.snapshot()['surfaces'],0)
        self.assertTrue(manager.failed)

    def test_restore_and_delete_failures_cannot_delete_selected_bitmap_or_destroy_window(self):
        case=Fixture();manager=case.install()
        with self.indicator_thread():
            layer=case.layer()
            case.system.program.update({('SelectObject',2):0,('DeleteDC',1):0})
            with self.assertRaises(BaseExceptionGroup):layer.close()
            self.assertEqual(case.system.counts['DeleteObject'],0)
            self.assertEqual(manager.snapshot()['selected_bitmap_count'],1)
            self.assertFalse(any(name=='destroy-window' for name,hwnd in case.events))
            with self.assertRaises(RuntimeError):layer.set_opacity(20)
            layer.close()
        self.assertTrue(case.system.balanced())
        self.assertTrue(manager.failed)

    def test_independent_native_cleanup_failures_report_and_keep_exact_ledger(self):
        for name in ('DeleteDC','DeleteObject'):
            case=Fixture();manager=case.install()
            with self.subTest(name=name),self.indicator_thread():
                layer=case.layer()
                case.system.program[(name,1)]=0
                with self.assertRaises(BaseExceptionGroup):layer.close()
                self.assertEqual(manager.snapshot()['memory_dc_count'],int(name=='DeleteDC'))
                self.assertEqual(manager.snapshot()['bitmap_count'],int(name=='DeleteObject'))
                layer.close()
                self.assertTrue(case.system.balanced())
        # 上传失败且释放屏幕DC也失败，随后由正常退役回收，但不重发上传。
        case=Fixture();manager=case.install()
        with self.indicator_thread():
            layer=case.layer()
            case.system.program.update({('UpdateLayeredWindow',2):0,('ReleaseDC',3):0})
            with self.assertRaises(BaseExceptionGroup):layer.set_opacity(30)
            self.assertEqual(manager.snapshot()['screen_dc_count'],1)
            self.assertEqual(layer.opacity,None)
            layer.close()
            self.assertTrue(case.system.balanced())
            self.assertEqual(case.system.counts['UpdateLayeredWindow'],2)

    def test_other_threads_and_unrelated_flash_keep_original_upload(self):
        case=Fixture();manager=case.install()
        case.layer()
        self.assertEqual(len(case.original_uploads),1)
        with self.indicator_thread():case.flash._push_bitmap(123,0,0,1,1,b'abcd')
        self.assertEqual(len(case.original_uploads),2)
        self.assertFalse(case.system.calls)
        manager.audit_shutdown()

    def test_managed_layer_foreign_thread_rejected_before_backend(self):
        case=Fixture();case.install()
        with self.indicator_thread():layer=case.layer()
        calls=len(case.system.calls);errors=[]
        def worker():
            for action in (lambda:layer.set_opacity(10),layer.close):
                try:action()
                except RuntimeError as error:errors.append(str(error))
        thread=threading.Thread(target=worker);thread.start();thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors),2)
        self.assertEqual(len(case.system.calls),calls)
        with self.indicator_thread():layer.close()
        self.assertTrue(case.system.balanced())

    def test_mutated_pixels_or_geometry_rejected_without_fallback(self):
        for change in ('pixels','geometry','target'):
            case=Fixture();manager=case.install()
            with self.subTest(change=change),self.indicator_thread():
                layer=case.layer();count=len(case.system.frames);target=layer.hwnd
                if change=='pixels':layer.bgra=b'abcdefgh'
                elif change=='geometry':layer.width=1
                else:layer.hwnd+=1000
                with self.assertRaisesRegex(RuntimeError,'重建'):layer.set_opacity(10)
                self.assertEqual(len(case.system.frames),count)
                self.assertTrue(manager.failed)
                if change=='target':
                    with self.assertRaisesRegex(RuntimeError,'禁止销毁其他窗口'):layer.close()
                    self.assertFalse(any(name=='destroy-window' for name,hwnd in case.events))
                    # 只在假对象中恢复测试夹具以结束资源测试，运行时禁止修补身份。
                    layer.hwnd=target
                layer.close()
                self.assertTrue(case.system.balanced())

    def test_closed_layer_cannot_reallocate_or_reinitialize_even_if_hwnd_reused(self):
        case=Fixture();manager=case.install()
        with self.indicator_thread():
            layer=case.layer();target=layer.hwnd;layer.close()
            count=len(case.system.calls);events=len(case.events)
            layer.hwnd=target
            layer.close()
            self.assertEqual(len(case.events),events)
            with self.assertRaisesRegex(RuntimeError,'重新初始化'):
                layer.__init__(0,0,2,1,b'12345678','重复')
            with self.assertRaisesRegex(RuntimeError,'已关闭'):layer.set_opacity(20)
            self.assertEqual(len(case.system.calls),count)
            self.assertEqual(manager.snapshot()['surfaces'],0)
            self.assertTrue(manager.failed)
        self.assertTrue(case.system.balanced())

    def test_fixed_resource_budgets_refuse_before_second_native_allocation(self):
        for limits in (dict(max_surfaces=1),dict(max_bytes=8)):
            case=Fixture();manager=case.install(**limits)
            with self.subTest(limits=limits),self.indicator_thread():
                first=case.layer();count=case.system.counts['CreateDIBSection']
                with self.assertRaisesRegex(RuntimeError,'预算'):case.layer()
                self.assertEqual(case.system.counts['CreateDIBSection'],count)
                self.assertEqual(manager.snapshot()['reserved_bytes'],8)
                first.close()
                self.assertTrue(case.system.balanced())

    def test_install_refuses_live_duplicate_or_old_timing_before_mutation(self):
        for kind in ('live','timing','duplicate'):
            case=Fixture()
            if kind=='live':case.overlay._instance=object()
            elif kind=='timing':case.flash._pt_bitmap_timing_installed=True
            else:case.install()
            original=case.flash._push_bitmap
            with self.subTest(kind=kind),self.assertRaises(RuntimeError):case.install()
            self.assertIs(case.flash._push_bitmap,original)
            self.assertFalse(case.system.calls)

    def test_private_dll_signatures_do_not_modify_original_function_objects(self):
        case=Fixture()
        original=Function(lambda *args:1);original.argtypes=['原签名']
        case.flash._user32=types.SimpleNamespace(GetDC=original)
        case.install()
        with self.indicator_thread():layer=case.layer();layer.close()
        self.assertEqual(original.argtypes,['原签名'])
        self.assertIs(case.flash._user32.GetDC,original)
        self.assertIsNot(case.api_objects[0].functions['GetDC'],original)

    def run_owner(self,case,steps):
        manager=case.install()
        indicator=case.overlay._Indicator()
        case.indicator=indicator
        class Condition:
            def __init__(self):self.index=0
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def wait(self,timeout):
                step=steps[self.index];self.index+=1
                for name,value in step.items():setattr(indicator,name,value)
            def notify_all(self):pass
        indicator.condition=Condition()
        case.namespace['_monitor_rects']=lambda:indicator.rects
        indicator._run()
        return indicator,manager

    def test_original_owner_loop_rebuilds_on_display_and_mode_changes_and_retires_on_stop(self):
        case=Fixture()
        steps=[dict(active=True,pending=False,rects=((0,0,12,12),)),
               dict(pending=True),dict(rects=((0,0,14,14),)),dict(stopping=True)]
        with self.indicator_thread():indicator,manager=self.run_owner(case,steps)
        self.assertIsNone(indicator.error)
        self.assertTrue(case.system.balanced())
        self.assertEqual(case.system.counts['CreateDIBSection'],15)
        self.assertEqual(case.system.counts['DeleteObject'],15)
        self.assertEqual(manager.snapshot()['reserved_bytes'],0)
        self.assertTrue(any(name=='pump' for name,hwnd in case.events))
        self.assertTrue(any(name=='hide' for name,hwnd in case.events))
        self.assertGreater(indicator.heartbeat,0)
        manager.audit_shutdown()

    def test_independent_normal_resource_audit_rejects_missing_or_corrupt_lifetimes(self):
        case=Fixture()
        steps=[dict(active=True,pending=False,rects=((0,0,12,12),)),dict(stopping=True)]
        with self.indicator_thread():indicator,manager=self.run_owner(case,steps)
        manager.audit_shutdown()
        rows=case.rows+[dict(event='trace-closed',dropped=0)]
        result=audit(rows)
        self.assertEqual(result['surfaces'],5)
        self.assertEqual(result['uploads'],10)
        self.assertEqual(result['api_calls']['memmove'],5)
        for corruption in ('counts','ledger','reuse','missing-upload','missing-exit','exception','timing'):
            bad=deepcopy(rows)
            operation=next(row for row in bad if row['event']=='indicator-surface-operation')
            if corruption=='counts':operation['stages']['memmove']['calls']=2
            elif corruption=='ledger':operation['resources']['bitmap_count']=0
            elif corruption=='reuse':operation['surface_id']=999
            elif corruption=='missing-upload':bad=[row for row in bad if not
                    (row.get('surface_id')==1 and row.get('operation')=='upload')]
            elif corruption=='missing-exit':bad=[row for row in bad if row['event']!='indicator-surface-owner-exit']
            elif corruption=='exception':operation['exception']='OSError'
            else:operation['duration_seconds']=-1
            with self.subTest(corruption=corruption),self.assertRaises(ValueError):audit(bad)

    def test_heartbeat_and_acknowledgement_wait_for_all_uploads_and_faults_stay_unacknowledged(self):
        for fails in (False,True):
            case=Fixture();seen=[]
            def observe(name):
                if name=='UpdateLayeredWindow':seen.append((case.indicator.heartbeat,case.indicator.applied))
            case.system.before=observe
            if fails:case.system.program[('UpdateLayeredWindow',1)]=0
            steps=[dict(active=True,pending=False,version=9,rects=((0,0,12,12),)),dict(stopping=True)]
            with self.subTest(fails=fails),self.indicator_thread():
                indicator,manager=self.run_owner(case,steps)
            self.assertTrue(seen)
            self.assertTrue(all(value==seen[0] for value in seen))
            self.assertEqual(seen[0][1],0)
            if fails:
                self.assertIsNotNone(indicator.error)
                self.assertEqual((indicator.heartbeat,indicator.applied),seen[0])
                self.assertEqual(case.system.counts['UpdateLayeredWindow'],1)
            else:
                self.assertIsNone(indicator.error)
                self.assertGreater(indicator.heartbeat,seen[0][0])
                self.assertEqual(indicator.applied,9)
            self.assertTrue(case.system.balanced())

    def test_owner_cleanup_continues_after_one_layer_failure_and_keeps_error_sticky(self):
        case=Fixture()
        case.system.program[('DeleteObject',1)]=0
        steps=[dict(active=True,pending=False,rects=((0,0,12,12),)),dict(stopping=True)]
        with self.indicator_thread(),self.assertRaises(BaseExceptionGroup):
            self.run_owner(case,steps)
        self.assertTrue(case.system.balanced())
        self.assertIsNotNone(case.indicator.error)
        self.assertTrue(case.manager.failed)
        self.assertEqual(case.manager.snapshot()['surfaces'],0)
        self.assertEqual(case.system.counts['UpdateLayeredWindow'],10)
        with self.assertRaises(RuntimeError):case.manager.audit_shutdown()


if __name__=='__main__':
    unittest.main(verbosity=2)
