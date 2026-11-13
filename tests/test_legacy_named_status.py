"""新命名Status方案仅合成文件/原gate与submit/假driver，不启动桌面。"""
import ast
import base64
import contextlib
import datetime
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import patch
import test_legacy_runtime_config as fixtures

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')


class NamedStatusTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.RuntimeIsolationTests();self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.session=self.fixture.root/'synthetic-session.jsonl'
        self.session.write_text(json.dumps({'type':'session','id':'fake-session'})+'\n',encoding='utf-8')
        self.package,self.plan=self.fixture.generated(lambda **args:fixtures.state.prepare_state(
            named_status=True,budget_seconds=3600,file_submitter_session=str(self.session),**args))
        self.root=self.package/'slot';(self.root/'inbox').mkdir()
        spec=importlib.util.spec_from_file_location('status_gate_fixture',self.package/'review_gate.py')
        self.gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.gate)
        self.png=self.root/'synthetic.png';self.png.write_bytes(PNG)
        self.count=0
        self.binding={k:self.plan[k] for k in ('task','dispatch','session')}

    def observed(self,*,needs_guest=False,rounds=0,menu=False,guest=True):
        self.count+=1
        s=self.gate.publish(self.root,self.plan,'synthetic-'+str(self.count),[{'path':str(self.png)}],
            [self.png] if guest else [],needs_guest,menu,rounds)
        for kind in ('host','guest'):
            if s[kind]:fixtures.dump(self.root/(s['step']+'-'+kind+'-read-review.json'),{
                **self.binding,'step':s['step'],'nonce':s['nonce'],'model':'deng/gpt-6.1-sol','thinking':'high',
                'images':s[kind],'observation':'合成协议验证，不是实际菜单或计数'})
        return s

    def packet(self,purpose,key,name=None):
        s=self.observed()
        return s,{**self.binding,'previous':s['step'],'nonce':s['nonce'],
            'request':{'name':name or purpose.replace('_','-'),'tool':'Shortcut','purpose':purpose,'arguments':{'shortcut':key}}}

    def actual_submit(self,packet):
        path=self.root/'synthetic-packet.json';fixtures.dump(path,packet)
        prior=sys.modules.get('review_gate');sys.modules['review_gate']=self.gate
        try:
            with patch.object(sys,'argv',['submit',str(self.root),str(path)]),contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(self.package/'submit.py'),run_name='__main__')
        finally:
            if prior is None:sys.modules.pop('review_gate',None)
            else:sys.modules['review_gate']=prior
        out=self.root/'inbox'/('request-'+packet['request']['name']+'.json')
        self.assertEqual(json.loads(out.read_text(encoding='utf-8')),packet)
        out.rename(out.with_suffix('.consumed'))

    def use(self,purpose,key,name=None):
        s,p=self.packet(purpose,key,name);self.gate.validate(self.root,self.plan,s,p);self.actual_submit(p)
        # 原driver实际Shortcut分支消费marker，工具/窗口检查及后续Snapshot为假对象。
        self.run_driver_branch(p)
        return p

    def reach_info(self):
        self.use('startup_enter','enter');self.use('main_menu_enter','enter')
        for n in range(7):self.use('navigate_down','down','down-'+str(n))
        self.use('information_confirm','enter')

    def test_complete_named_status_sequence_uses_original_gate_and_submit(self):
        self.reach_info()
        self.use('status_position','up');self.use('status_confirm','enter');self.use('status_return','esc')
        self.use('menu_return','esc')
        self.assertEqual(len(list((self.root/'inbox').glob('*.consumed'))),14)
        self.assertEqual(self.plan['capture_rounds'],16)
        self.assertEqual(self.plan['budget_seconds'],3600)
        self.assertTrue(self.plan['file_submitter']['queue'].endswith('submit-queue'))
        policy=fixtures.isolation.validate_runtime_plan(self.plan)
        self.assertEqual(len(policy['probe_writes']),7)
        self.assertTrue(all(Path(p).parent==self.root/'runtime' for p in policy['probe_writes']))
        # 合成目标EXE与base Python是同一路径，冻结去重，比真实候选少1项。
        self.assertEqual(len(self.plan['frozen_files']),27)

    def test_explicit_file_step_adapter_freezes_both_sources_without_control_change(self):
        package,plan=self.fixture.generated(lambda **args:fixtures.state.prepare_state(
            named_status=True,file_step_adapter=True,budget_seconds=3600,
            file_submitter_session=str(self.session),**args))
        expected=[fixtures.REPO/'tools/legacy_file_step.js',fixtures.REPO/'tools/Wait-LegacyFileStep.ps1']
        before={item['path'] for item in self.plan['frozen_files']}
        for path in expected:
            matches=[item for item in plan['frozen_files'] if Path(item['path'])==path]
            self.assertEqual(len(matches),1)
            self.assertEqual(matches[0]['sha256'],fixtures.digest(path))
            self.assertEqual(matches[0]['bytes'],path.stat().st_size)
            self.assertNotIn(str(path),before)
        self.assertEqual(len(plan['frozen_files']),len(self.plan['frozen_files'])+2)
        for name in ('desktop_session.py','review_gate.py','submit.py'):
            self.assertEqual((package/name).read_bytes(),(self.package/name).read_bytes())
        fixtures.isolation.validate_runtime_plan(plan,runtime_root=package/'slot')
        preparation=json.loads((package/'preparation.json').read_text(encoding='utf-8'))
        self.assertTrue(preparation['file_step_adapter'])
        self.assertFalse(json.loads((self.package/'preparation.json').read_text(encoding='utf-8'))['file_step_adapter'])

    def test_file_step_adapter_requires_explicit_named_status_before_generation(self):
        with patch.object(fixtures.state,'prepare_capture') as prepare:
            with self.assertRaisesRegex(ValueError,'显式新命名Status'):
                fixtures.state.prepare_state(file_step_adapter=True)
            prepare.assert_not_called()

    def test_context_budgets_shift_end_home_and_status_enter_rejected(self):
        for purpose,key in [('status_position','up'),('status_confirm','enter'),('status_return','esc'),
                            ('information','shift+i'),('status','shift+s'),('navigate_up','up'),
                            ('status_position','end'),('status_position','home')]:
            s,p=self.packet(purpose,key)
            with self.subTest(purpose=purpose,key=key),self.assertRaises(RuntimeError):self.gate.validate(self.root,self.plan,s,p)
        self.reach_info()
        for purpose,key in [('navigate_down','down'),('main_menu_enter','enter'),('information_confirm','enter')]:
            s,p=self.packet(purpose,key,'replay-'+purpose)
            with self.assertRaises(RuntimeError):self.gate.validate(self.root,self.plan,s,p)
        self.use('status_position','up')
        s,p=self.packet('status_position','up','up-twice')
        with self.assertRaises(RuntimeError):self.gate.validate(self.root,self.plan,s,p)
        self.use('status_confirm','enter')
        s,p=self.packet('status_confirm','enter','status-page-enter')
        with self.assertRaises(RuntimeError):self.gate.validate(self.root,self.plan,s,p)

    def test_seventh_down_and_each_new_guest_required(self):
        self.use('startup_enter','enter');self.use('main_menu_enter','enter')
        for n in range(6):self.use('navigate_down','down','down-'+str(n))
        s,p=self.packet('information_confirm','enter')
        with self.assertRaisesRegex(RuntimeError,'七次Down'):self.gate.validate(self.root,self.plan,s,p)
        self.use('navigate_down','down','down-6')
        s,p=self.packet('navigate_down','down','eighth-down')
        with self.assertRaises(RuntimeError):self.gate.validate(self.root,self.plan,s,p)
        s,p=self.packet('information_confirm','enter')
        s=self.observed(needs_guest=True,guest=False);p.update(previous=s['step'],nonce=s['nonce'])
        with self.assertRaisesRegex(RuntimeError,'新客体图'):self.gate.validate(self.root,self.plan,s,p)
        s=self.observed();p.update(previous=s['step'],nonce=s['nonce'])
        (self.root/(s['step']+'-guest-read-review.json')).unlink()
        with self.assertRaises(FileNotFoundError):self.gate.validate(self.root,self.plan,s,p)

    def test_capture_limit_and_extra_probe_or_stale_paths_rejected(self):
        s=self.observed(rounds=16)
        p={**self.binding,'previous':s['step'],'nonce':s['nonce'],'request':{'name':'overflow','tool':'Click',
            'purpose':'capture_menu_open','arguments':{'loc':[100,100]}}}
        with self.assertRaisesRegex(RuntimeError,'十六次'):self.gate.validate(self.root,self.plan,s,p)
        path=self.root/'SYN1.conf';original=path.read_text(encoding='utf-8')
        for text in (original+'echo unexpected\n',original.replace('> C:\\OUTPUT.TXT','> D:\\OUTPUT.TXT'),
                     original.replace(str(self.root/'captures'),str(self.fixture.root/'outside'))):
            path.write_text(text,encoding='utf-8')
            with self.assertRaises(ValueError):fixtures.isolation.validate_runtime_plan(self.plan,check_bytes=False)
        path.write_text(original,encoding='utf-8')

    def test_invalid_budget_or_missing_owner_source_zero_base_generation(self):
        with patch.object(fixtures.state,'prepare_navigation') as prepare:
            with self.assertRaises(ValueError):fixtures.state.prepare_state(named_status=True)
            prepare.assert_not_called()
        with patch.object(fixtures.navigation,'prepare_capture') as base:
            with self.assertRaises(ValueError):fixtures.state.prepare_state(named_status=True,
                budget_seconds=3601,file_submitter_session=str(self.session))
            base.assert_not_called()

    def test_public_up_original_ast_uses_named_virtual_key(self):
        from replay_legacy_shortcut import ShortcutReplay
        replay=ShortcutReplay();row=replay.trace('up')
        keys=[c for c in row['calls'] if c['api']=='keybd_event']
        self.assertEqual([(x['vk'],x['scan'],x['flags']) for x in keys],[(0x26,0x48,1),(0x26,0x48,3)])
        self.assertEqual(row['sendkeys'],[{'text':'{up}','kwargs':{'interval':.01}}])
        self.assertIsNone(row['error']);self.assertTrue(replay.unchanged())

    def test_new_named_final_gate_rejects_corruption_after_navigation(self):
        original=fixtures.state.prepare_navigation
        def corrupted(**args):
            original(**args)
            path=Path(args['destination'])/'slot/SYN1.conf'
            path.write_text(path.read_text(encoding='utf-8').replace('logfile=','unexpected-log='),encoding='utf-8')
        with patch.object(fixtures.state,'prepare_navigation',side_effect=corrupted):
            with self.assertRaises(ValueError):self.fixture.generated(lambda **args:fixtures.state.prepare_state(
                named_status=True,budget_seconds=3600,file_submitter_session=str(self.session),**args))

    def run_driver_branch(self,packet):
        scope,tree=self.fixture.driver_definitions(self.package)
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="tool in ('App', 'Shortcut', 'Click', 'Type')")
        calls=[];identity={'pid':-1};target=types.SimpleNamespace(pid=-1,poll=lambda:None)
        def save(name,value):
            fixtures.dump(self.root/name,value)
            calls.append(('save',name))
        rpc=types.SimpleNamespace(gate=lambda name:None,remaining=lambda:100,observation_guard=lambda **kwargs:None,
            snapshot=lambda *args:'synthetic-post',last_interval=(10,20),tool=lambda *args:calls.append(('tool',args[0])))
        scope.update(plan=self.plan,target=target,identity=identity,root_hwnd=-2,process_identity=lambda p:identity,
            tool='Shortcut',req=packet['request'],name=packet['request']['name'],
            rpc=rpc,inspect_desktop=lambda:{},guard_window=lambda *args:-2,save=save,
            time=types.SimpleNamespace(perf_counter_ns=lambda:10),stamp=lambda:'synthetic')
        exec(compile(ast.Module(body=node.body,type_ignores=[]),'<真实driver命名Up分支>','exec'),scope)
        marker=packet['request']['name']+'-'+packet['request']['purpose']+'-used.json'
        self.assertLess(calls.index(('save',marker)),calls.index(('tool','Shortcut')))
        self.assertEqual(scope['last_capture'],'synthetic-post')

    def test_real_driver_shortcut_branch_records_new_purpose_before_fake_tool(self):
        _,packet=self.packet('status_position','up','status-up')
        self.run_driver_branch(packet)


if __name__=='__main__':unittest.main()
