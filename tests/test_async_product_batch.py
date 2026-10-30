"""批量整窗观察回归；假子进程完成同一完整收集器，不加载桌面或COM。"""
import asyncio
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools')); sys.path.insert(0,str(ROOT/'tests'))
from async_product_client.batch import BatchProductNative, TargetQueryHandle, validate_observation
from async_product_client.native import collect_native
from async_product_client.core import SECOND, digest, Identity
from test_async_product_native import Fixture as NativeFixture
from test_async_product_probe import ProbeFixture
from test_async_product_session import Fixture as SessionFixture


class BatchTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.probes=[]
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for f in self.probes:
            for child in f.probe.children: f.probe.close_streams(child)

    def folder(self):
        path=self.root/str(len(list(self.root.iterdir())));path.mkdir();return path

    async def test_one_child_returns_same_main_modal_file_payload_with_original_double_uia_checks(self):
        for dirty in (False,True):
            f=NativeFixture(self.folder(),dirty=dirty)
            with f.rig.ledger.operation('collect',f.rig.ledger.token):
                expected=await f.collector()
            expected_calls=list(f.calls);f.calls.clear()
            with f.rig.ledger.operation('batch',f.rig.ledger.token):
                row=await collect_native(f.rig.owner.identity,f.api,f.uia,
                                          checkpoint=f.rig.ledger.desktop_allowed,verify_identity=f.collector.identity)
            self.assertEqual(row,expected)
            self.assertEqual(f.calls,expected_calls)
            uia=[entry for entry in f.calls if isinstance(entry,tuple) and entry[0]=='uia']
            self.assertEqual(len(uia),4 if dirty else 2)
            validate_observation(row,f.rig.owner.identity)

    async def test_batch_probe_uses_one_original_popen_zero_exit_and_preserves_nonce_restore_checks(self):
        f=ProbeFixture(self.folder());self.probes.append(f)
        native=NativeFixture(self.folder(),dirty=True)
        # 两份假夹具的进程image不同；结果必须绑定父指定的同一精确原身份。
        with native.rig.ledger.operation('native',native.rig.ledger.token): result=await native.collector()
        for window in result['windows']:window['image']=f.rig.owner.identity.image
        result['foreground']=copy.deepcopy(result['windows'][1])
        def mutate(row):
            request=json.loads(f.processes[0].path.read_text(encoding='utf-8'))
            self.assertEqual(request['query_kind'],'native-observation')
            row.pop('uia');row.update(native=copy.deepcopy(result),query_kind='native-observation')
        f.mutate=mutate
        batch=BatchProductNative(f.rig.ledger,f.rig.owner,f.creator,f.probe,enabled=True)
        with f.rig.ledger.operation('observe',f.rig.ledger.token): row=await batch()
        self.assertEqual(row,result)
        self.assertEqual(len(f.calls),1)
        self.assertIs(f.probe.children[0]['process'],f.processes[0])
        self.assertTrue(f.probe.children[0]['accepted'])
        self.assertEqual(f.probe.children[0]['exit_code'],0)
        self.assertEqual(f.rig.calls,[])

    async def test_unknown_mode_wrong_window_birth_image_owner_rect_and_foreground_are_rejected(self):
        for mode in ('mode','birth','image','owner','rect','foreground','extra','missing-main'):
            f=ProbeFixture(self.folder());self.probes.append(f)
            window=dict(pid=42,birth=100,image=f.rig.owner.identity.image,hwnd=99,owner=0,
                        cls='Qt6120QWindowIcon',title='fake',enabled=True,visible=True,rect=[0,0,100,100],
                        coordinate_space='physical-desktop-pixels',thread_context_restored=True,focus_kind='canvas')
            result=dict(input_desktop='Default',locked=False,foreground_stable=True,windows=[window],foreground=window)
            def mutate(row):
                native=copy.deepcopy(result)
                if mode=='birth':native['windows'][0]['birth']=101
                if mode=='image':native['windows'][0]['image']='other'
                if mode=='owner':native['windows'][0]['owner']=1
                if mode=='rect':native['windows'][0]['rect']=[0,0,0,1]
                if mode=='foreground':native['foreground']={}
                if mode=='extra':native['windows']*=3
                if mode=='missing-main':native['windows'][0]['hwnd']=100
                row.pop('uia');row.update(native=native,query_kind='single-uia' if mode=='mode' else 'native-observation')
            f.mutate=mutate
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                with f.rig.ledger.operation('native',f.rig.ledger.token): await f.probe.observe()
            self.assertEqual(len(f.calls),1)
            self.assertFalse(f.probe.children[0]['accepted'])
            self.assertTrue(f.probe.failed)

    async def test_batch_failure_or_changed_cross_window_state_has_no_second_child_or_inputs(self):
        f=NativeFixture(self.folder(),dirty=True)
        original=f.uia.inspect
        def changed(hwnd,pid):
            row=original(hwnd,pid)
            if hwnd==101:f.rows[99]['title']='changed'
            return row
        f.uia.inspect=changed
        with self.assertRaises(ValueError):
            with f.rig.ledger.operation('batch',f.rig.ledger.token):
                await collect_native(f.rig.owner.identity,f.api,f.uia,
                                     checkpoint=f.rig.ledger.desktop_allowed,verify_identity=f.collector.identity)
        self.assertEqual(f.rig.calls,[])
        f=ProbeFixture(self.folder());self.probes.append(f);f.mode='hung'
        batch=BatchProductNative(f.rig.ledger,f.rig.owner,f.creator,f.probe,enabled=True)
        with self.assertRaises(ValueError):
            with f.rig.ledger.operation('batch',f.rig.ledger.token): await batch()
        saved=f.rig.ledger.failed,f.rig.ledger.token,f.rig.ledger.not_before_ns
        f.mode='valid';f.probe.reap()
        self.assertEqual((f.rig.ledger.failed,f.rig.ledger.token,f.rig.ledger.not_before_ns),saved)
        self.assertEqual(len(f.calls),1)
        self.assertFalse(f.probe.children[0]['accepted'])

    async def test_original_query_limit_and_total_deadline_are_shared_by_batch_and_single_modes(self):
        f=ProbeFixture(self.folder());self.probes.append(f)
        f.probe.max_queries=1
        await f.run()
        with self.assertRaises(ValueError):
            with f.rig.ledger.operation('batch',f.rig.ledger.token): await f.probe.observe()
        self.assertEqual(len(f.calls),1)
        self.assertEqual(f.probe.max_queries,1)

    async def test_session_counts_each_native_observation_once_and_keeps_input_postchecks(self):
        from async_product_client.budget import session_budget
        for kind in ('net','copper'):
            f=SessionFixture(self.folder(),kind)
            original=f.rig.io.native_api
            starts=[]
            async def batch():
                starts.append(f.rig.clock.now)
                return await original()
            f.rig.io.native_api=batch
            await f.race()
            s,rig=f.session,f.rig
            rid=await s.close_step('close',rig.ledger.token,action='start',dirty=True)
            await s.close_step('modal',rig.ledger.token,action='ack',**rig.read(rid))
            await s.close_step('discard',rig.ledger.token,action='choose',choice='放弃更改',image_point=[100,275])
            budget=session_budget(kind)
            self.assertEqual(len(starts),budget['native_observations'])
            self.assertEqual(len(starts),budget['batch_probe_queries'])
            self.assertEqual(f.f.signal_calls,['release'])
            self.assertTrue(rig.owner.retired)
            self.assertEqual(budget['batch_with_main_discovery_queries'],31 if kind=='net' else 22)
            self.assertFalse(budget['batch_exceeds_frozen_probe_limit'])
            self.assertFalse(budget['ready_for_live'])

    async def test_full_sessions_drive_original_fake_popen_for_every_batch_observation(self):
        for kind in ('net','copper'):
            f=SessionFixture(self.folder(),kind)
            p=ProbeFixture(self.folder());self.probes.append(p)
            p.rig=f.rig
            p.probe.ledger,p.probe.owner,p.probe.creator=f.rig.ledger,f.rig.owner,f.f.creator
            p.probe._deadline_ns=f.rig.ledger.cleanup_deadline_ns
            original=f.rig.io.native_api
            observation=None
            def mutate(row):
                row.pop('uia');row.update(query_kind='native-observation',native=copy.deepcopy(observation))
            p.mutate=mutate
            batch=BatchProductNative(f.rig.ledger,f.rig.owner,f.f.creator,p.probe,enabled=True)
            async def native():
                nonlocal observation
                observation=await original()
                for window in observation['windows']:
                    window.setdefault('enabled',True);window.setdefault('visible',True)
                    window.setdefault('focus_kind','unknown')
                if len(observation['windows'])==2:observation['windows'][0]['enabled']=False
                hwnd=observation['foreground']['hwnd']
                observation['foreground']=copy.deepcopy(next(w for w in observation['windows'] if w['hwnd']==hwnd))
                return await batch()
            f.rig.io.native_api=native
            await f.race()
            s,rig=f.session,f.rig
            rid=await s.close_step('close',rig.ledger.token,action='start',dirty=True)
            await s.close_step('modal',rig.ledger.token,action='ack',**rig.read(rid))
            await s.close_step('discard',rig.ledger.token,action='choose',choice='放弃更改',image_point=[100,275])
            from async_product_client.budget import session_budget
            expected=session_budget(kind)['batch_probe_queries']
            self.assertEqual(len(p.calls),expected)
            self.assertEqual(len(p.processes),expected)
            self.assertTrue(all(child['accepted'] and child['exit_code']==0 for child in p.probe.children))
            self.assertTrue(rig.owner.retired)
            self.assertIsNone(rig.ledger.failed)
            self.assertEqual(p.probe.max_queries,32)

    async def test_batch_parent_disabled_cooldown_or_wrong_original_object_create_no_child(self):
        for mode in ('disabled','cooldown','popen'):
            f=ProbeFixture(self.folder());self.probes.append(f)
            batch=BatchProductNative(f.rig.ledger,f.rig.owner,f.creator,f.probe,enabled=mode!='disabled')
            if mode=='cooldown':f.rig.ledger.not_before_ns=f.rig.clock.now+120*SECOND
            if mode=='popen':f.creator.process=object()
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                with f.rig.ledger.operation('batch',f.rig.ledger.token): await batch()
            self.assertEqual(f.calls,[])

    async def test_worker_batch_restores_com_dpi_and_keeps_two_round_checks_in_one_process(self):
        from async_product_client import probe_worker
        from unittest.mock import patch
        from types import SimpleNamespace
        import types
        import sys
        import builtins
        import ctypes
        f=NativeFixture(self.folder(),dirty=True)
        contexts=[];com=[];verifies=[]
        def context(value):contexts.append(value);return 123
        f.api.load=lambda:SimpleNamespace(SetThreadDpiAwarenessContext=context)
        def initialize(*args):com.append('init');return 0
        def uninitialize():com.append('uninit')
        ole=SimpleNamespace(CoInitializeEx=initialize,CoUninitialize=uninitialize)
        class Handle:
            def __init__(self,target):self.target=target
            def __enter__(self):verifies.append('enter');return self
            def verify(self):verifies.append('verify');f.collector.identity()
            def __exit__(self,*args):verifies.append('close')
        module=types.ModuleType('windows_mcp');module.uia=types.ModuleType('windows_mcp.uia')
        module.uia.__file__=str(self.root/'package/windows_mcp/uia/__init__.py')
        original_import=builtins.__import__
        def importing(name,*args,**kwargs):
            return module if name=='windows_mcp.uia' else original_import(name,*args,**kwargs)
        from contextlib import contextmanager
        @contextmanager
        def isolated_modules():
            with patch.dict(sys.modules):
                for name in list(sys.modules):
                    if (name == 'windows_mcp' or name.startswith('windows_mcp.')
                            or name == 'comtypes' or name.startswith('comtypes.')): sys.modules.pop(name)
                yield
        saved_path=list(sys.path)
        try:
            with isolated_modules(), patch('async_product_client.native.ReadOnlyWin32',return_value=f.api),\
                 patch('async_product_client.native.ReadOnlyUia',return_value=f.uia),\
                 patch('async_product_client.batch.TargetQueryHandle',Handle),\
                 patch.object(ctypes,'OleDLL',return_value=ole,create=True),\
                 patch.object(builtins,'__import__',side_effect=importing):
                # worker是同步子入口，放在离线测试线程运行，线程中只有假API。
                result=await asyncio.to_thread(probe_worker.run_uia,
                    dict(pid=42,birth=100,image=f.rig.owner.identity.image,hwnd=99),self.root/'package',
                    checkpoint=lambda:None,kind='native-observation')
        finally:sys.path[:]=saved_path
        self.assertTrue(result['dpi_restored'] and result['com_uninitialized'])
        self.assertEqual(com,['init','uninit'])
        self.assertEqual(contexts[-1],123)
        self.assertEqual(verifies[0],'enter');self.assertEqual(verifies[-1],'close')
        self.assertEqual(len([row for row in f.calls if isinstance(row,tuple) and row[0]=='uia']),4)
        self.assertEqual(result['native']['foreground']['hwnd'],101)

    async def test_worker_stop_checkpoint_prevents_further_native_queries_and_releases_contexts(self):
        from async_product_client import probe_worker
        from unittest.mock import patch
        from types import SimpleNamespace
        import ctypes
        f=NativeFixture(self.folder())
        contexts=[];com=[]
        def context(value):contexts.append(value);return 123
        f.api.load=lambda:SimpleNamespace(SetThreadDpiAwarenessContext=context)
        def initialize(*args):com.append('init');return 0
        def uninitialize():com.append('uninit')
        ole=SimpleNamespace(CoInitializeEx=initialize,CoUninitialize=uninitialize)
        def stop():raise ValueError('原deadline或父停止标记')
        with patch('async_product_client.native.ReadOnlyWin32',return_value=f.api),\
             patch.object(ctypes,'OleDLL',return_value=ole,create=True):
            with self.assertRaises(ValueError):
                probe_worker.run_uia(dict(pid=42,hwnd=99),self.root/'package',checkpoint=stop,kind='native-observation')
        self.assertEqual(f.calls,[])
        self.assertEqual(com,[])
        self.assertEqual(contexts,[])

    def test_query_handle_verifies_birth_image_liveness_and_closes_without_exit_claim(self):
        import ctypes
        from ctypes import wintypes
        for mode in ('valid','birth','image','exited','pid'):
            calls=[]
            class Kernel:
                def WaitForSingleObject(self,handle,timeout):calls.append(('wait',handle));return 0 if mode=='exited' else 258
                def GetProcessId(self,handle):return 43 if mode=='pid' else 42
                def GetProcessTimes(self,handle,a,b,c,d):
                    a._obj.dwHighDateTime=0;a._obj.dwLowDateTime=101 if mode=='birth' else 100;return True
                def QueryFullProcessImageNameW(self,handle,flags,buffer,size):
                    buffer.value='C:/other.exe' if mode=='image' else 'C:/target.exe';return True
                def CloseHandle(self,handle):calls.append(('close',handle));return True
            target=TargetQueryHandle(dict(pid=42,birth=100,image='C:/target.exe'))
            target.kernel=Kernel();target.handle=555
            try:
                if mode=='valid':target.verify()
                else:
                    with self.assertRaises(ValueError):target.verify()
            finally:target.__exit__(None,None,None)
            self.assertEqual(calls[-1],('close',555))
            self.assertIsNone(target.handle)

    async def test_local_ack_and_stable_snapshot_still_reject_changes_before_next_input(self):
        for mode in ('file-value','command-focus','snapshot'):
            f=SessionFixture(self.folder(),'net')
            await f.baseline()
            rid=await f.session.capture_command('command',f.rig.ledger.token)
            if mode=='snapshot':
                original=f.rig.io.snapshot_api
                async def shot(target):
                    result=await original(target)
                    f.native_mutation=lambda row:dict(row,foreground=dict(row['foreground'],focus_kind='text'))
                    return result
                f.rig.io.snapshot_api=shot
                with self.assertRaises(ValueError):
                    with f.rig.ledger.operation('stable',f.rig.ledger.token):await f.rig.io.capture(stable=True)
            else:
                await f.session.ack_command('command-read',f.rig.ledger.token,**f.rig.read(rid))
                if mode=='command-focus':
                    f.native_mutation=lambda row:dict(row,foreground=dict(row['foreground'],focus_kind='text'))
                    with self.assertRaises(ValueError):
                        await f.session.invoke_command('invoke',f.rig.ledger.token,image_point=[125,70])
                else:
                    await f.session.invoke_command('invoke',f.rig.ledger.token,image_point=[125,70])
                    rid=await f.session.file_step('file',f.rig.ledger.token,action='start')
                    f.value='changed.net'
                    with self.assertRaises(ValueError):
                        await f.session.file_step('file-read',f.rig.ledger.token,action='ack',**f.rig.read(rid))
                    self.assertFalse(f.session.dialog.type_used)
            self.assertIsNotNone(f.rig.ledger.failed)
            self.assertFalse(any(tool=='Type' for tool,args in f.calls))

    def test_supporting_target_query_handle_is_not_an_original_popen_witness(self):
        target=TargetQueryHandle(dict(pid=42,birth=100,image='C:/target.exe'))
        self.assertIsNone(target.kernel);self.assertIsNone(target.handle)
        self.assertFalse(hasattr(target,'terminate'))
        self.assertFalse(hasattr(target,'wait_exit'))


if __name__=='__main__':unittest.main(verbosity=2)
