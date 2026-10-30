"""统一产品会话的完整假API联调；不启动产品/桌面/COM或新Pi任务。"""
from dataclasses import replace
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.commands import COMMANDS
from async_product_client.core import digest, SECOND
from async_product_client.file_dialog import FILE_TITLE, NetFileSpec
from async_product_client.session import ProductSession
from async_product_client.lifecycle import ProcessRegistry
from async_product_client.process import OwnedProductProcess
from async_product_client.product import ProductOwner, WindowPolicy, EXPERIMENT_SUFFIX, tree_hashes
from test_async_product_gate import Fixture as GateFixture
from test_async_product_client import Rig, Process


class Fixture:
    def __init__(self, root, kind='net'):
        self.f = GateFixture(root, kind); self.rig = self.f.rig
        self.root = Path(root)
        self.a_path,self.b_path=self.root/'a.net',self.root/'b.net'
        self.a_path.write_bytes(b'NET A'); self.b_path.write_bytes(b'NET B')
        self.a=NetFileSpec(str(self.a_path.resolve()),digest(self.a_path.read_bytes()))
        self.b=NetFileSpec(str(self.b_path.resolve()),digest(self.b_path.read_bytes()))
        for row in self.f.rows:
            for key,value in list(row.items()):
                if value == 'a'*64: row[key] = self.a.sha256
                elif value == 'b'*64: row[key] = self.b.sha256
        self.f.rows[1].update(path=self.a.path,generation='3')
        self.f.rows[2]['thread_id']='22'
        self.f.rows[3]['thread_id']='22'
        self.f.rows[4].update(captured_generation='3',current_generation='3',revision='2')
        if kind=='net': self.f.rows[5]['path']=self.b.path
        self.f.write(5)
        self.f.creator.initial_net=self.a
        self.mode,self.value='main',''
        self.calls=[]; self.native_mutation=lambda row:row
        self.native_windows=[]
        self.error=None
        self.command_boxes={'netlistOpen':[50,50,200,90],'copperAnalyze':[50,100,250,140]}
        rig=self.rig; fixture=self
        original_native=rig.io.native_api
        async def native():
            if fixture.mode=='file':
                main=rig.main_window(); main['enabled']=False
                base=dict(pid=42,enabled=True,offscreen=False,descendant_verified=True)
                controls=dict(filename=dict(base,automation_id='1148',control_type=50004,rect=[200,400,700,450],
                                           value=fixture.value,read_only=False),
                              open=dict(base,automation_id='1',control_type=50000,name='打开(O)',rect=[700,500,800,550]),
                              cancel=dict(base,automation_id='2',control_type=50000,name='取消',rect=[700,560,800,610]))
                dialog=dict(pid=42,birth=100,image=rig.owner.identity.image,hwnd=150,owner=99,title=FILE_TITLE,
                            cls='#32770',enabled=True,modal=True,rect=[100,100,900,700],
                            coordinate_space='physical-desktop-pixels',thread_context_restored=True,file_controls=controls,
                            file_focus=dict(pid=42,automation_id='1148',control_type=50004,descendant_verified=True))
                fixture.native_windows.append(2)
                return fixture.native_mutation(dict(input_desktop='Default',locked=False,foreground_stable=True,
                                                     windows=[main,dialog],foreground=dialog))
            row=await original_native()
            for window in row['windows']:
                if window['hwnd']==99:
                    window['commands']={key:dict(pid=42,automation_id=key,name=name,control_type=50000,
                                            enabled=True,offscreen=False,descendant_verified=True,rect=fixture.command_boxes[key])
                                        for key,name in COMMANDS.items()}
            if row['foreground'].get('hwnd')==99: row['foreground']=copy.deepcopy(row['windows'][0])
            fixture.native_windows.append(len(row['windows']))
            return fixture.native_mutation(row)
        original_transport=rig.io.transport
        class Transport:
            async def file_dialog_type(self,permit):
                args=permit.consume(rig.ledger); fixture.calls.append(('Type',args));fixture.value=args['text']
                if fixture.error: raise fixture.error
                x,y=args['loc']
                return dict(tool='Type',arguments=args,is_error=False,text=[f"Typed {args['text']} at ({x},{y})."])
            async def __call__(self,tool,args):
                fixture.calls.append((tool,copy.deepcopy(args)))
                if fixture.error: raise fixture.error
                if tool=='Click' and args['loc']==[125,70]:fixture.mode='file'
                elif tool=='Click' and args['loc']==[150,120]:fixture.f.write(8)
                elif tool=='Click' and fixture.mode=='file':
                    fixture.mode='main'
                    if args['loc']==[750,525]:fixture.f.write(8)
                result=await original_transport(tool,args)
                if tool=='Shortcut' and args.get('shortcut')=='delete':fixture.f.write(9)
                return result
        rig.io.native_api=native; rig.io.transport=Transport()
        self.session=ProductSession(rig.ledger,rig.io,rig.reviews,self.f.journal,a=self.a,b=self.b,
                                     board_sha256='c'*64,revision=2,diagnostic_deadline_ns=600*SECOND,
                                     enabled=True,event_api=self.f.api,pause=self.f.pause,waiter=rig.waiter)

    async def baseline(self):
        rid=await self.session.prepare('prepare',self.rig.ledger.token)
        await self.session.ack_baseline('baseline-read',self.rig.ledger.token,**self.rig.read(rid))

    async def target(self, *, attach=True):
        rig=self.rig;s=self.session
        await self.baseline()
        rid=await s.capture_command('command',rig.ledger.token)
        await s.ack_command('command-read',rig.ledger.token,**rig.read(rid))
        rig.clock.tick()
        await s.invoke_command('invoke',rig.ledger.token,image_point=[125,70] if self.f.creator.kind=='net' else [150,120])
        if self.f.creator.kind=='net':
            rid=await s.file_step('dialog',rig.ledger.token,action='start')
            await s.file_step('dialog-read',rig.ledger.token,action='ack',**rig.read(rid))
            rid=await s.file_step('path',rig.ledger.token,action='type')
            await s.file_step('path-read',rig.ledger.token,action='ack',**rig.read(rid))
            rig.clock.tick()
            await s.file_step('open',rig.ledger.token,action='choose',choice='open',image_point=[650,425])
        manifest=dict(run_id=self.f.rows[0]['run_id'],request_id='2',kind=self.f.creator.kind,pid='42',creation_filetime='100',
                      release_event=f"Local\\PtRenewAsync-{self.f.rows[0]['run_id']}-2-release",
                      cancel_event=f"Local\\PtRenewAsync-{self.f.rows[0]['run_id']}-2-cancel")
        (self.f.directory/'request-2.json').write_text(json.dumps(manifest),encoding='utf-8')
        if attach: await s.attach_gate('attach',rig.ledger.token)

    async def race(self):
        s,rig=self.session,self.rig
        await self.target()
        rid=await s.race_step('gate',rig.ledger.token,action='gate-image')
        await s.race_step('gate-read',rig.ledger.token,action='ack',review_id=rid,**rig.read(rid))
        rid=await s.race_step('edit',rig.ledger.token,action='edit',image_point=[500,400])
        await s.race_step('edit-read',rig.ledger.token,action='ack',review_id=rid,**rig.read(rid))
        await s.race_step('release',rig.ledger.token,action='release')
        rid=await s.race_step('final',rig.ledger.token,action='final-image')
        await s.race_step('final-read',rig.ledger.token,action='ack',review_id=rid,**rig.read(rid))


class SessionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def fixture(self,kind='net'):
        path=self.root/str(len(list(self.root.iterdir())));path.mkdir();return Fixture(path,kind)

    async def test_net_and_copper_complete_session_preserve_shared_context_trigger_and_dirty_exit(self):
        for kind in ('net','copper'):
            with self.subTest(kind=kind):
                f=self.fixture(kind);await f.race();s,rig=f.session,f.rig
                self.assertEqual(s.stage,'settled');self.assertTrue(s.race.settled)
                trigger=s.trigger_mono_ns
                self.assertEqual(s.race.deadline,trigger+60*SECOND)
                self.assertEqual(s.gate.trigger_mono_ns,trigger)
                self.assertEqual(f.f.signal_calls,['release'])
                self.assertEqual(sum(tool=='Type' for tool,args in f.calls),1 if kind=='net' else 0)
                rid=await s.close_step('close',rig.ledger.token,action='start',dirty=True)
                await s.close_step('modal-read',rig.ledger.token,action='ack',**rig.read(rid))
                await s.close_step('discard',rig.ledger.token,action='choose',choice='放弃更改',image_point=[100,275])
                self.assertEqual(s.stage,'retired');self.assertTrue(rig.owner.retired)
                self.assertIs(rig.waited_process,rig.process)
                from async_product_client.budget import session_budget
                budget=session_budget(kind)
                self.assertEqual(len(f.native_windows),budget['native_observations'])
                self.assertEqual(2*sum(f.native_windows),budget['probe_queries'])
                self.assertTrue(budget['exceeds_frozen_probe_limit'])
                self.assertFalse(budget['ready_for_live'])
                report=s.report();self.assertFalse(report['ready_for_live']);self.assertFalse(report['gui_verified'])
                self.assertIsNone(report['failed_id'])

    async def test_missing_wrong_a_path_digest_generation_acceptance_and_thread_block_baseline(self):
        for index,field,value in [(1,'path','other.net'),(3,'result_sha256','b'*64),(4,'current_generation','99'),
                                  (4,'experiment_aborted',True),(3,'thread_id','11'),(4,'accepted',False)]:
            f=self.fixture();f.f.rows[index][field]=value;f.f.write(5)
            with self.subTest(field=field),self.assertRaises(ValueError):await f.session.prepare('prepare',f.rig.ledger.token)
            self.assertEqual(f.calls,[]);self.assertEqual(f.rig.shots,0)
            self.assertIsNotNone(f.rig.ledger.failed)

    async def test_disabled_busy_old_token_queue_and_original_diagnostic_deadline_do_no_work(self):
        for mode in ('disabled','busy','token','queue','deadline'):
            f=self.fixture();rig=f.rig
            if mode=='disabled':f.session.enabled=False
            if mode=='busy':rig.ledger.busy=True
            if mode=='queue':rig.ledger.pending=True
            if mode=='deadline':rig.clock.tick(600)
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                await f.session.prepare('prepare','old' if mode=='token' else rig.ledger.token)
            self.assertEqual(f.calls,[]);self.assertEqual(rig.shots,0)

    async def test_command_before_baseline_wrong_point_or_changed_button_never_clicks(self):
        f=self.fixture()
        with self.assertRaises(ValueError):await f.session.capture_command('command',f.rig.ledger.token)
        self.assertEqual(f.calls,[])
        for mode in ('wrong-point','changed','disabled','text-focus'):
            f=self.fixture();await f.baseline();s,rig=f.session,f.rig
            rid=await s.capture_command('command',rig.ledger.token)
            await s.ack_command('command-read',rig.ledger.token,**rig.read(rid))
            if mode=='changed':f.command_boxes['netlistOpen']=[70,50,210,90]
            if mode in ('disabled','text-focus'):
                def mutate(row):
                    if mode=='disabled':row['foreground']['commands']['netlistOpen']['enabled']=False
                    else:row['foreground']['focus_kind']='text'
                    return row
                f.native_mutation=mutate
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                await s.invoke_command('invoke',rig.ledger.token,image_point=[500,500] if mode=='wrong-point' else [125,70])
            self.assertEqual(f.calls,[])

    async def test_b_path_or_extra_request_and_original_trigger_expiry_block_attach(self):
        for mode in ('path','count','expired'):
            f=self.fixture();await f.target(attach=False)
            s,rig=f.session,f.rig
            if mode=='path':f.f.rows[5]['path']='other.net';f.f.write(8)
            if mode=='count':
                row=dict(f.f.rows[5],request_id='3',gated=False,sequence='9',monotonic_ns='900000000')
                path=f.f.directory/'events.jsonl';path.write_bytes(path.read_bytes()+json.dumps(row).encode()+b'\n')
            if mode=='expired':rig.clock.tick(60)
            with self.subTest(mode=mode),self.assertRaises(ValueError):await s.attach_gate('attach',rig.ledger.token)
            self.assertEqual(f.f.signal_calls,[])

    async def test_release_unknown_and_later_normal_exit_keep_session_failure(self):
        f=self.fixture();await f.target();s,rig=f.session,f.rig
        rid=await s.race_step('gate',rig.ledger.token,action='gate-image')
        await s.race_step('gate-read',rig.ledger.token,action='ack',review_id=rid,**rig.read(rid))
        rid=await s.race_step('edit',rig.ledger.token,action='edit',image_point=[500,400])
        await s.race_step('edit-read',rig.ledger.token,action='ack',review_id=rid,**rig.read(rid))
        f.f.signal_error=ConnectionError('信号未知')
        with self.assertRaises(ConnectionError):await s.race_step('release',rig.ledger.token,action='release')
        failure=rig.ledger.failed,rig.ledger.token,rig.ledger.not_before_ns
        f.f.rows[9]['event']='aborted';f.f.rows[-1]['experiment_aborted']=True;f.f.write(len(f.f.rows))
        rig.clock.tick(121)
        rid=await s.close_step('close',rig.ledger.token,action='start',dirty=True)
        await s.close_step('modal-read',rig.ledger.token,action='ack',**rig.read(rid))
        await s.close_step('discard',rig.ledger.token,action='choose',choice='放弃更改',image_point=[100,275])
        self.assertTrue(rig.owner.retired)
        self.assertEqual((rig.ledger.failed,rig.ledger.token,rig.ledger.not_before_ns),failure)
        self.assertFalse(s.close.completed)

    async def test_hidden_named_command_or_wrong_experiment_suffix_cannot_reach_any_input(self):
        for mode in ('hidden','wrong-name','suffix'):
            f=self.fixture();await f.baseline()
            def mutate(row):
                main=row['foreground']
                if mode=='hidden':main['commands']['netlistOpen']['offscreen']=True
                if mode=='wrong-name':main['commands']['netlistOpen']['name']='other'
                if mode=='suffix':
                    for window in row['windows']:window['title']=window['title'].replace(EXPERIMENT_SUFFIX,'')
                    main['title']=main['title'].replace(EXPERIMENT_SUFFIX,'')
                return row
            f.native_mutation=mutate
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                await f.session.capture_command('command',f.rig.ledger.token)
            self.assertEqual(f.calls,[])
            self.assertIsNotNone(f.rig.ledger.failed)

    async def test_read_ack_or_unknown_race_action_cannot_skip_shared_session_stages(self):
        for mode in ('command-ack','race','file'):
            f=self.fixture();s,rig=f.session,f.rig
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                if mode=='command-ack':await s.ack_command('ack',rig.ledger.token)
                elif mode=='race':await s.race_step('skip',rig.ledger.token,action='release')
                else:await s.file_step('skip',rig.ledger.token,action='type')
            self.assertEqual(f.calls,[])
        f=self.fixture();await f.target()
        with self.assertRaises(ValueError):
            await f.session.race_step('unknown',f.rig.ledger.token,action='cancel-and-pass')
        self.assertEqual(f.f.signal_calls,[])
        self.assertFalse(f.session.report()['race_protocol_settled'])

    async def test_uia_main_command_subtree_only_exports_exact_readonly_named_buttons(self):
        from async_product_client.native import ReadOnlyUia
        trace=[]
        class Control:
            def __init__(self,aid,name,ctype,hwnd=0,parent=None):
                self.AutomationId,self.Name,self.ControlType=aid,name,ctype
                self.ProcessId,self.NativeWindowHandle=42,hwnd
                self.ClassName='Qt6120QWindowIcon'
                self.IsEnabled,self.IsOffscreen=True,False
                self.BoundingRectangle=SimpleNamespace(left=50,top=50,right=200,bottom=90)
                self.children,self.parent=[],parent
            def GetPattern(self,pattern):trace.append('WindowPattern');return SimpleNamespace(IsModal=False)
            def GetChildren(self):trace.append('GetChildren');return self.children
            def GetParentControl(self):return self.parent
        root=Control('mainWindow',WindowPolicy('board.pcb').title(False),50032,99)
        button=Control('netlistOpen',COMMANDS['netlistOpen'],50000,parent=root)
        root.children=[button,Control('unrelated','其他按钮',50000,parent=root)]
        module=SimpleNamespace(__file__=str(self.root/'package/windows_mcp/uia/__init__.py'),
                               PatternId=SimpleNamespace(WindowPattern=1),ControlFromHandle=lambda hwnd:root,
                               GetFocusedControl=lambda:button)
        row=ReadOnlyUia(module,package_root=self.root/'package').inspect(99,42)
        self.assertEqual([x['automation_id'] for x in row['commands']],['netlistOpen'])
        self.assertTrue(row['commands'][0]['descendant_verified'])
        self.assertTrue(trace)
        button.Name='wrong'
        with self.assertRaises(ValueError):ReadOnlyUia(module,package_root=self.root/'package').inspect(99,42)

    async def test_creator_initial_a_command_line_and_explicit_experiment_titles(self):
        path=self.root/'creator';path.mkdir();rig=Rig(path)
        a_path=path/'a.net';a_path.write_bytes(b'initial')
        a=NetFileSpec(str(a_path.resolve()),digest(a_path.read_bytes()))
        calls=[];process=Process()
        def popen(command,**kwargs):calls.append(command);return process
        api=SimpleNamespace(inspect=lambda value:dict(pid=value.pid,birth=100,handle=555,original_handle=True,
                                    image=str((rig.deployment/'pt-renew.exe').resolve())))
        creator=OwnedProductProcess(rig.ledger,kind='net',experiment_directory=path/'events',board_copy=rig.board,
                                    evidence_root=path/'logs',enabled=True,popen=popen,handle_api=api,initial_net=a)
        try:
            with rig.ledger.operation('launch','start'):
                owner=ProductOwner(rig.ledger)
                owner.launch(deployment=rig.deployment,manifest=tree_hashes(rig.deployment),inputs={**rig.inputs,str(a_path):a.sha256},
                             environment={},factory=creator,inspect_created=creator.inspect_created)
            command=calls[0]
            self.assertEqual(command[command.index('--netlist')+1],a.path)
            self.assertEqual(command[-1],str(rig.board.resolve()))
            self.assertTrue(WindowPolicy('board.pcb').title(False).endswith(EXPERIMENT_SUFFIX))
            self.assertIn(' * 已修改',WindowPolicy('board.pcb').title(True))
        finally:creator.close_streams()


if __name__=='__main__':unittest.main(verbosity=2)
