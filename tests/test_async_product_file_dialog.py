"""原生文件框阶段与原Popen账本回归；假API/图片会话，无真实桌面或进程。"""
import copy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.core import digest
from async_product_client.file_dialog import NetFileDialog, NetFileSpec, FILE_TITLE, FileTypePermit
from async_product_client.lifecycle import ProcessRegistry
from async_product_client.transport import McpProductTransport
from test_async_product_client import Rig, Process
from test_async_product_adapters import Connection
from test_async_product_native import Fixture as NativeFixture


class Fixture:
    def __init__(self, root):
        self.rig = Rig(root); self.rig.launch()
        self.root = Path(root)
        self.path = self.root / 'a.net'; self.path.write_bytes(b'new-net-copy')
        self.mode, self.value = 'file', ''
        self.mutate = lambda row: row
        self.type_calls, self.click_calls = [], []
        self.error = None
        self.main_title = self.rig.policy.title(False)
        fixture = self
        original_native = self.rig.native
        async def native():
            if fixture.mode == 'main': return await original_native()
            main = fixture.rig.main_window(); main.update(enabled=False)
            dialog = dict(pid=42, birth=100, image=fixture.rig.owner.identity.image, hwnd=150, owner=99,
                          title=FILE_TITLE, cls='#32770', enabled=True, modal=True, rect=[100,100,900,700],
                          coordinate_space='physical-desktop-pixels', thread_context_restored=True,
                          file_controls=fixture.controls(), file_focus=dict(pid=42, automation_id='1148',
                          control_type=50004, descendant_verified=True))
            return fixture.mutate(dict(input_desktop='Default', locked=False, foreground_stable=True,
                                       windows=[main, dialog], foreground=dialog))
        class Transport:
            async def file_dialog_type(self, permit):
                args = permit.consume(fixture.rig.ledger)
                fixture.type_calls.append(args)
                fixture.value = args['text']
                if fixture.error: raise fixture.error
                x,y = args['loc']
                return dict(tool='Type', arguments=args, is_error=False, text=[f"Typed {args['text']} at ({x},{y})."])
            async def __call__(self, tool, args):
                fixture.click_calls.append((tool,args)); fixture.mode = 'main'
                if fixture.error: raise fixture.error
                x,y = args['loc']
                return dict(tool=tool, arguments=args, is_error=False, text=[f'Single left clicked at ({x},{y}).'])
        self.rig.io.native_api = native
        self.rig.io.transport = Transport()
        self.client = NetFileDialog(self.rig.ledger, self.rig.io, self.rig.reviews,
                                     NetFileSpec(str(self.path.resolve()), digest(self.path.read_bytes())),
                                     request_id=7, main_title=self.main_title,
                                     deadline_ns=self.rig.ledger.cleanup_deadline_ns, enabled=True)

    def controls(self):
        base = dict(pid=42, enabled=True, offscreen=False, descendant_verified=True)
        return dict(filename=dict(base, automation_id='1148', control_type=50004, rect=[200,400,700,450],
                                  value=self.value, read_only=False),
                    open=dict(base, automation_id='1', control_type=50000, name='打开(O)', rect=[700,500,800,550]),
                    cancel=dict(base, automation_id='2', control_type=50000, name='取消', rect=[700,560,800,610]))

    async def read_dialog(self):
        rid = await self.client.start('file', self.rig.ledger.token)
        await self.client.ack('file-ack', self.rig.ledger.token, **self.rig.read(rid))

    async def read_path(self):
        await self.read_dialog()
        rid = await self.client.type_path('path', self.rig.ledger.token)
        await self.client.ack('path-ack', self.rig.ledger.token, **self.rig.read(rid))


class FileTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        folder = self.root / str(len(list(self.root.iterdir()))); folder.mkdir()
        return Fixture(folder)

    async def test_actual_read_type_path_read_then_open_once_retains_trigger_before_input(self):
        f = self.fixture(); await f.read_path()
        before = f.rig.clock.now
        result = await f.client.choose('open', f.rig.ledger.token, choice='open', image_point=[650,425])
        self.assertEqual(result['stage'], 'submitted')
        self.assertEqual(result['trigger_mono_ns'], before)
        self.assertFalse(result['load_verified'])
        self.assertEqual(len(f.type_calls), 1)
        self.assertEqual(f.type_calls[0]['text'], str(f.path.resolve()))
        self.assertIs(f.type_calls[0]['press_enter'], False)
        self.assertEqual(f.click_calls, [('Click', dict(loc=[750,525]))])
        self.assertEqual(len(f.rig.reviews.consumed), 2)
        with self.assertRaises(ValueError):
            await f.client.choose('retry', f.rig.ledger.token, choice='open', image_point=[650,425])
        self.assertEqual(len(f.click_calls), 1)

    async def test_cancel_after_initial_read_does_not_type_path_or_record_load_trigger(self):
        f = self.fixture(); await f.read_dialog()
        row = await f.client.choose('cancel', f.rig.ledger.token, choice='cancel', image_point=[650,485])
        self.assertEqual(row['stage'], 'cancelled')
        self.assertIsNone(row['trigger_mono_ns'])
        self.assertEqual(f.type_calls, [])
        self.assertEqual(len(f.click_calls), 1)

    async def test_no_read_before_type_no_path_read_before_open_and_wrong_button_refuse(self):
        for mode in ('no-dialog-read','no-path-read','wrong-button'):
            f = self.fixture()
            if mode == 'no-dialog-read':
                await f.client.start('file', f.rig.ledger.token)
                action = lambda: f.client.type_path('type', f.rig.ledger.token)
            elif mode == 'no-path-read':
                await f.read_dialog(); await f.client.type_path('type', f.rig.ledger.token)
                action = lambda: f.client.choose('open', f.rig.ledger.token, choice='open', image_point=[650,425])
            else:
                await f.read_path()
                action = lambda: f.client.choose('open', f.rig.ledger.token, choice='open', image_point=[650,485])
            with self.subTest(mode=mode), self.assertRaises(ValueError): await action()
            self.assertEqual(f.click_calls, [])
            self.assertEqual(len(f.type_calls), 0 if mode == 'no-dialog-read' else 1)

    async def test_wrong_pid_birth_image_owner_title_class_enabled_and_controls_never_type(self):
        cases = [('pid',43),('birth',101),('image','other.exe'),('owner',50),('title','打开'),('cls','Qt6120QWindowIcon'),
                 ('enabled',False),('modal',False)]
        for field,value in cases:
            f = self.fixture()
            def mutate(row): row['windows'][1][field] = value; return row
            f.mutate = mutate
            with self.subTest(field=field), self.assertRaises(ValueError): await f.read_dialog()
            self.assertEqual((f.type_calls,f.click_calls),([],[]))
        for mode in ('control-id','readonly','outside','duplicate','main-enabled','wrong-pid'):
            f = self.fixture()
            def mutate(row):
                dialog = row['windows'][1]; edit = dialog['file_controls']['filename']
                if mode == 'control-id': edit['automation_id'] = 'search'
                if mode == 'readonly': edit['read_only'] = True
                if mode == 'outside': edit['rect'] = [0,0,20,20]
                if mode == 'duplicate': row['windows'].append(dict(dialog,hwnd=151))
                if mode == 'main-enabled': row['windows'][0]['enabled'] = True
                if mode == 'wrong-pid': edit['pid'] = 43
                return row
            f.mutate = mutate
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.read_dialog()
            self.assertEqual(f.type_calls,[])

    async def test_changed_input_hash_path_value_hwnd_and_unknown_type_are_not_retried(self):
        for mode in ('hash','value','hwnd','unknown'):
            f = self.fixture(); await f.read_dialog()
            if mode == 'hash': f.path.write_bytes(b'changed')
            if mode == 'hwnd':
                def mutate(row): row['windows'][1]['hwnd'] = 151; return row
                f.mutate = mutate
            if mode == 'value':
                def mutate(row): row['windows'][1]['file_controls']['filename']['value'] = 'wrong.net'; return row
                f.mutate = mutate
            if mode == 'unknown': f.error = ConnectionError('Type结果未知')
            token = f.rig.ledger.token
            with self.subTest(mode=mode), self.assertRaises((ValueError,ConnectionError)):
                await f.client.type_path('type',token)
            self.assertEqual(f.rig.ledger.token,token)
            self.assertIsNotNone(f.rig.ledger.failed)
            self.assertLessEqual(len(f.type_calls),1)
            f.rig.clock.tick(121)
            with self.assertRaises(ValueError): await f.client.type_path('retry',token)
            self.assertEqual(f.click_calls,[])

    async def test_open_postcheck_failure_keeps_single_click_and_cannot_promote_later_state(self):
        f=self.fixture(); await f.read_path()
        original = f.rig.io.transport.__class__.__call__
        async def wrong(transport,tool,args):
            result = await original(transport,tool,args)
            f.mode = 'file'
            return result
        f.rig.io.transport.__class__.__call__ = wrong
        with self.assertRaises(ValueError):
            await f.client.choose('open',f.rig.ledger.token,choice='open',image_point=[650,425])
        self.assertEqual(f.client.stage,'open-attempted')
        self.assertIsNotNone(f.client.trigger_mono_ns)
        self.assertEqual(len(f.click_calls),1)

    async def test_disabled_busy_queue_old_token_and_cooldown_do_not_query_or_type(self):
        for mode in ('disabled','busy','queue','token','cooldown','deadline'):
            f=self.fixture()
            if mode=='disabled': f.client.enabled=False
            if mode=='busy': f.rig.ledger.busy=True
            if mode=='queue': f.rig.ledger.pending=True
            if mode=='cooldown': f.rig.ledger.not_before_ns=f.rig.clock.now+120_000_000_000
            if mode=='deadline': f.rig.clock.tick(1000)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                await f.client.start('file','old' if mode=='token' else f.rig.ledger.token)
            self.assertEqual((f.type_calls,f.click_calls),([],[]))

    async def test_transport_type_needs_one_shot_same_ledger_permit_and_general_type_stays_blocked(self):
        f=self.fixture(); clock=f.rig.clock
        connection=Connection(clock)
        connection.row=dict(is_error=False,content=[dict(type='text',text=f'Typed {f.path.resolve()} at (1,2).')])
        transport=McpProductTransport(f.rig.ledger,connection,self.root/'transport',enabled=True,validate=lambda *args:None)
        args=dict(text=str(f.path.resolve()),loc=[1,2],clear=True,press_enter=False,caret_position='idle')
        with f.rig.ledger.operation('type',f.rig.ledger.token):
            with self.assertRaises(ValueError): await transport('Type',args)
            permit=FileTypePermit(f.rig.ledger,args,f.client.spec)
            await transport.file_dialog_type(permit)
            with self.assertRaises(ValueError): await transport.file_dialog_type(permit)
        self.assertEqual(len(connection.calls),1)

    async def test_changed_button_or_focus_after_read_rejects_and_type_permit_copies_arguments(self):
        for mode in ('button','focus'):
            f=self.fixture(); await f.read_dialog()
            def mutate(row):
                target=row['windows'][1]
                if mode=='button': target['file_controls']['open']['rect']=[650,500,750,550]
                else: target['file_focus']['automation_id']='search'
                return row
            f.mutate=mutate
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                await f.client.type_path('type',f.rig.ledger.token)
            self.assertEqual(f.type_calls,[])
        f=self.fixture()
        args=dict(text=f.client.spec.path,loc=[1,2],clear=True,press_enter=False,caret_position='idle')
        permit=FileTypePermit(f.rig.ledger,args,f.client.spec)
        args['loc'][0]=999;args['text']='other'
        public=permit.arguments;public['loc'][0]=888
        with f.rig.ledger.operation('consume',f.rig.ledger.token):
            result=permit.consume(f.rig.ledger)
        self.assertEqual(result['loc'],[1,2])
        self.assertEqual(result['text'],f.client.spec.path)
        for path in ('relative/a.net','//server/share/a.net',str(f.path.parent/'other.net')):
            with self.assertRaises(ValueError): NetFileSpec(path,'a'*64)

    async def test_original_uia_bridge_reads_filename_value_and_buttons_without_setting_value(self):
        from async_product_client.native import ReadOnlyUia
        trace=[]
        class Control:
            def __init__(self,name,aid,ctype,hwnd=0,parent=None):
                self.Name,self.AutomationId,self.ControlType=name,aid,ctype
                self.ProcessId,self.NativeWindowHandle=42,hwnd
                self.ClassName='#32770' if hwnd else 'Edit'
                self.IsEnabled,self.IsOffscreen=True,False
                self.BoundingRectangle=SimpleNamespace(left=200,top=400,right=700,bottom=450)
                self.parent,self.children=parent,[]
            def GetPattern(self,pattern):
                trace.append(('pattern',pattern))
                return SimpleNamespace(IsModal=True) if pattern==1 else SimpleNamespace(Value='frozen-path',IsReadOnly=False)
            def GetChildren(self): return self.children
            def GetParentControl(self): return self.parent
        root=Control(FILE_TITLE,'dialog',50032,150)
        edit=Control('文件名','1148',50004,parent=root)
        root.children=[edit,Control('打开(O)','1',50000,parent=root),Control('取消','2',50000,parent=root)]
        module=SimpleNamespace(__file__=str(self.root/'package/windows_mcp/uia/__init__.py'),
                               PatternId=SimpleNamespace(WindowPattern=1,ValuePattern=2),
                               ControlFromHandle=lambda hwnd:root,GetFocusedControl=lambda:edit)
        result=ReadOnlyUia(module,package_root=self.root/'package').inspect(150,42)
        self.assertEqual(len(result['file_elements']),3)
        value=next(r for r in result['file_elements'] if r['automation_id']=='1148')
        self.assertEqual(value['value'],'frozen-path')
        self.assertFalse(value['read_only'])
        self.assertTrue(result['focus']['descendant_verified'])
        self.assertTrue(trace)

    async def test_original_creator_and_probe_publish_same_objects_to_registry(self):
        from async_product_client.process import OwnedProductProcess
        from async_product_client.product import ProductOwner,tree_hashes
        import test_async_product_probe as helpers
        f=self.fixture()
        registry=ProcessRegistry(f.rig.ledger,required_roles=('product','probe'))
        registry.created('product',f.rig.process,role='product')
        registry.identified('product',f.rig.process,f.rig.owner.process_identity)
        folder=self.root/'probe'; folder.mkdir()
        p=helpers.ProbeFixture(folder)
        # 用探针自己的产品原Popen作父绑定，避免跨客户端对象混淆。
        registry=ProcessRegistry(p.rig.ledger,required_roles=('product','probe'))
        registry.created('product',p.rig.process,role='product')
        registry.identified('product',p.rig.process,p.rig.owner.process_identity)
        p.probe.registry=registry
        try:
            await p.run()
            entry=registry.entries['uia-probe-1']
            self.assertIs(entry['process'],p.processes[0])
            self.assertEqual(entry['parent'],'product')
            self.assertTrue(entry['accepted_exit'])
            p.rig.process.returncode=0
            self.assertTrue(registry.poll()['lifecycle_complete'])
        finally:
            for child in p.probe.children: p.probe.close_streams(child)
        folder=self.root/'creator'; folder.mkdir()
        rig=Rig(folder)
        registry=ProcessRegistry(rig.ledger,required_roles=('product',))
        process=Process()
        api=SimpleNamespace(inspect=lambda value:dict(pid=value.pid,birth=100,handle=555,
                            image=str((rig.deployment/'pt-renew.exe').resolve()),original_handle=True))
        creator=OwnedProductProcess(rig.ledger,kind='net',experiment_directory=folder/'app-events',
                                    board_copy=rig.board,evidence_root=folder/'logs',enabled=True,
                                    popen=lambda *args,**kwargs:process,handle_api=api,registry=registry)
        try:
            owner=ProductOwner(rig.ledger)
            with rig.ledger.operation('create','start'):
                owner.launch(deployment=rig.deployment,manifest=tree_hashes(rig.deployment),inputs=rig.inputs,
                             environment={},factory=creator,inspect_created=creator.inspect_created)
            self.assertIs(registry.entries['product']['process'],owner.process)
            process.returncode=0;creator.observe_exit()
            self.assertTrue(registry.report()['lifecycle_complete'])
        finally: creator.close_streams()

    async def test_native_collector_preserves_file_controls_for_independent_policy(self):
        path=self.root/'native'; path.mkdir()
        native=NativeFixture(path,dirty=True)
        f=self.fixture()
        native.rows[101].update(title=FILE_TITLE,cls='#32770')
        native.uia_rows[101]['root'].update(name=FILE_TITLE,cls='#32770')
        native.uia_rows[101]['file_elements']=list(f.controls().values())
        for element in native.uia_rows[101]['file_elements']:
            element['rect']=[250,300,400,350]
        row=await native.run()
        self.assertEqual(set(row['foreground']['file_controls']),{'filename','open','cancel'})
        self.assertEqual(row['foreground']['title'],FILE_TITLE)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        from async_product_client.core import Ledger,Context
        self.ledger=Ledger(context=Context('task','dispatch','run','session'),cleanup_deadline_ns=10**30)
        self.registry=ProcessRegistry(self.ledger,required_roles=('product','probe'))

    def identity(self,process):
        return dict(pid=process.pid,birth=100,handle=555,image='C:/frozen/test.exe',original_handle=True)

    def test_original_objects_zero_exit_complete_lifecycle_but_never_gui(self):
        for key,role,parent in [('product','product',None),('probe','probe','product')]:
            process=Process(); process.pid=42 if key=='product' else 43
            self.registry.created(key,process,role=role,parent=parent)
            self.registry.identified(key,process,self.identity(process))
            process.returncode=0
        result=self.registry.seal()
        self.assertTrue(result['lifecycle_complete'])
        self.assertTrue(result['action_succeeded'])
        self.assertFalse(result['gui_verified'])
        self.assertFalse(result['unknown_short_lived_descendants_covered'])
        with self.assertRaises(ValueError): self.registry.created('later',Process(),role='probe')

    def test_later_exit_never_clears_failure_token_or_cooldown_and_missing_roles_stay_visible(self):
        process=Process(); self.registry.created('product',process,role='product')
        self.registry.identified('product',process,self.identity(process))
        self.ledger.failed='input-error'; self.ledger.not_before_ns=777; self.ledger.token='before'
        process.returncode=0
        result=self.registry.poll()
        self.assertFalse(result['lifecycle_complete'])
        self.assertEqual(result['missing_roles'],['probe'])
        self.assertFalse(result['action_succeeded'])
        self.assertEqual((self.ledger.failed,self.ledger.token,self.ledger.not_before_ns),('input-error','before',777))

    def test_identity_unknown_nonzero_or_discovered_child_gap_cannot_be_repaired_with_pid_absence(self):
        for mode in ('identity','nonzero','gap'):
            registry=ProcessRegistry(self.ledger,required_roles=('product',))
            process=Process(); registry.created('product',process,role='product')
            if mode!='identity': registry.identified('product',process,self.identity(process))
            if mode=='gap': registry.discovered('unknown-child',pid=99,birth=101,parent='product')
            process.returncode=1 if mode=='nonzero' else 0
            result=registry.seal()
            self.assertFalse(result['lifecycle_complete'])
            self.assertFalse(result['action_succeeded'])
            self.assertIs(registry.entries['product']['process'],process)

    def test_duplicate_popen_changed_pid_identity_and_conflicting_exit_cannot_rewrite_book(self):
        process=Process(); self.registry.created('product',process,role='product')
        with self.assertRaises(ValueError): self.registry.created('second',process,role='probe')
        with self.assertRaises(ValueError): self.registry.identified('product',Process(),self.identity(process))
        self.registry.identified('product',process,self.identity(process))
        process.returncode=0; self.registry.exited('product',process,0)
        process.returncode=1
        with self.assertRaises(ValueError): self.registry.exited('product',process,1)
        self.assertEqual(self.registry.entries['product']['exit_code'],0)
        process.pid=88
        with self.assertRaises(ValueError): self.registry.exited('product',process,1)


if __name__=='__main__': unittest.main(verbosity=2)
