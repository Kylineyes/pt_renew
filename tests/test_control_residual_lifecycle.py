"""独立残留生命周期的假API/假时钟及来源证据契约测试，不访问真实桌面。"""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from control_residual_lifecycle import ResidualLifecycle,SOURCE_FILES,TITLE,check_plan,sha

TARGET=dict(pid=42,birth=100,image='C:/test/pythonw.exe',hwnd=99,title=TITLE,cls='TkTopLevel')


class Api:
    def __init__(self):
        self.calls=[];self.target=copy.deepcopy(TARGET);self.code=None;self.exit_code=0
        self.windows=[{k:TARGET[k] for k in ('pid','hwnd','title','cls')}]
        self.returned=True;self.error=None;self.identities=0;self.changed_late=False
    def hold(self,pid,birth):self.calls.append('hold');return '原查询句柄',100
    def identity(self,handle,hwnd):
        self.calls.append('identity');self.identities+=1
        row=copy.deepcopy(self.target)
        if self.changed_late and self.identities==2:row['hwnd']=123
        return row
    def poll(self,handle):self.calls.append('poll');return self.code
    def matching_windows(self,title):self.calls.append('windows');return self.windows
    def post_close(self,hwnd):
        self.calls.append('post-close')
        if self.error:raise self.error
        return self.returned
    def wait(self,handle,seconds):self.calls.append('wait');return self.exit_code
    def close(self,handle):self.calls.append('release-handle')


class LifecycleTests(unittest.TestCase):
    def rig(self,api=None):
        api=api or Api();records=[];markers=[]
        def reserve(identity):
            if markers:raise FileExistsError('机会已消费')
            markers.append(identity)
        tool=ResidualLifecycle(api,lambda kind,**v:records.append(dict(kind=kind,**v)),reserve,clock=lambda:10)
        return tool,api,records,markers

    def test_inspection_never_consumes_or_posts(self):
        tool,api,records,markers=self.rig()
        row=tool.run(TARGET,deadline=100)
        self.assertTrue(row['completed']);self.assertEqual(row['post_message_count'],0)
        self.assertEqual(markers,[]);self.assertNotIn('post-close',api.calls)
        self.assertFalse(row['original_popen']);self.assertEqual(api.calls[-1],'release-handle')

    def test_close_once_then_waits_same_late_handle_and_never_claims_gui(self):
        tool,api,records,markers=self.rig()
        row=tool.run(TARGET,execute=True,authorized=True,deadline=100)
        self.assertTrue(row['completed']);self.assertEqual(row['exit_code'],0)
        self.assertEqual(api.calls.count('post-close'),1);self.assertEqual(len(markers),1)
        self.assertFalse(row['gui_acceptance']);self.assertFalse(row['original_popen'])
        self.assertEqual([x['kind'] for x in records],['identity_verified','post_message_start','post_message_return','late_handle_exit'])
        again=tool.run(TARGET,execute=True,authorized=True,deadline=100)
        self.assertFalse(again['completed']);self.assertEqual(api.calls.count('post-close'),1)

    def test_missing_permission_or_expired_plan_rejects_before_api(self):
        for kwargs in (dict(execute=True,deadline=100),dict(execute=True,authorized=True,deadline=20)):
            tool,api,_,markers=self.rig();row=tool.run(TARGET,**kwargs)
            self.assertFalse(row['completed']);self.assertEqual(api.calls,[]);self.assertEqual(markers,[])

    def test_changed_identity_duplicate_title_or_exited_process_never_posts(self):
        for field,value in [('pid',43),('birth',101),('image','other'),('hwnd',98),('title','other'),('cls','other')]:
            with self.subTest(field=field):
                tool,api,_,markers=self.rig();api.target[field]=value
                row=tool.run(TARGET,execute=True,authorized=True,deadline=100)
                self.assertFalse(row['completed']);self.assertEqual(markers,[])
                self.assertNotIn('post-close',api.calls);self.assertEqual(api.calls[-1],'release-handle')
        for mode in ('duplicate','exited','late-change'):
            tool,api,_,markers=self.rig()
            if mode=='duplicate':api.windows*=2
            elif mode=='exited':api.code=0
            else:api.changed_late=True
            row=tool.run(TARGET,execute=True,authorized=True,deadline=100)
            self.assertFalse(row['completed']);self.assertNotIn('post-close',api.calls)
            self.assertEqual(bool(markers),mode=='late-change')

    def test_false_return_unknown_exception_timeout_nonzero_and_cancel_are_never_retried(self):
        for mode in ('false','unknown','timeout','nonzero','cancel'):
            with self.subTest(mode=mode):
                tool,api,_,markers=self.rig()
                if mode=='false':api.returned=False
                elif mode=='unknown':api.error=OSError('结果未知')
                elif mode=='cancel':api.error=KeyboardInterrupt()
                elif mode=='timeout':api.exit_code=None
                else:api.exit_code=7
                row=tool.run(TARGET,execute=True,authorized=True,deadline=100)
                self.assertFalse(row['completed']);self.assertTrue(row['no_retry'])
                self.assertEqual(api.calls.count('post-close'),1)
                self.assertEqual(api.calls[-1],'release-handle')
                self.assertFalse(tool.run(TARGET,execute=True,authorized=True,deadline=100)['completed'])
                self.assertEqual(api.calls.count('post-close'),1)

    def source(self,root):
        launch=dict(pid=42,birth=100,image=TARGET['image'],product_candidate=False)
        uia=dict(pid=42,birth=100,image=TARGET['image'],completed=True,identity_verified=True,
                 Name=TITLE,ClassName='TkTopLevel',expected_hwnd=99)
        state=dict(failed='close',not_before_monotonic=5,target=dict(pid=42,image=TARGET['image']))
        values={'window-launch.json':launch,'uia-preflight.json':uia,'live-state.json':state,
                'hard-deadline-exit.json':dict(outstanding_window=True,window_exit=None,window_pid=42),
                'v3-s09-close-complete.json':dict(tool_call_sent=False,executed=False,completed=False,phase='preflight')}
        for name,value in values.items():(root/name).write_text(json.dumps(value),encoding='utf-8')
        (root/'window.py').write_bytes((ROOT/'tools/control_test_window.py').read_bytes())
        (root/'controller-trace.jsonl').write_text(json.dumps(dict(event='trace-closed',dropped=0))+'\n',encoding='utf-8')
        return dict(mode='residual-diagnostic-lifecycle',operation_id='lifecycle_123456789abc',tool_sha256='模块摘要',
                    source_root=str(root),source_files_sha256={n:sha(root/n) for n in SOURCE_FILES},deadline=100,target=TARGET)

    def test_source_contract_binds_only_diagnostic_window_and_never_mutates_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);plan=self.source(root);before={p.name:p.read_bytes() for p in root.iterdir()}
            self.assertEqual(check_plan(plan,now=10,tool_sha256='模块摘要'),TARGET)
            self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir()})
            for key,value in [('mode','other'),('operation_id','old'),('tool_sha256','other'),('deadline',10),('target',dict(TARGET,pid=99))]:
                with self.subTest(key=key),self.assertRaises(ValueError):check_plan(dict(plan,**{key:value}),now=10,tool_sha256='模块摘要')
            (root/'window-launch.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'发生变化'):check_plan(plan,now=10,tool_sha256='模块摘要')

    def test_product_already_sent_close_unfinished_service_or_cooldown_are_refused(self):
        cases=[('window-launch.json','product_candidate',True),('v3-s09-close-complete.json','tool_call_sent',True),
               ('live-state.json','not_before_monotonic',90),('uia-preflight.json','ClassName','Other'),
               ('hard-deadline-exit.json','window_exit',0)]
        for name,key,value in cases:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);plan=self.source(root)
                row=json.loads((root/name).read_text());row[key]=value
                (root/name).write_text(json.dumps(row));plan['source_files_sha256'][name]=sha(root/name)
                with self.assertRaises(ValueError):check_plan(plan,now=10,tool_sha256='模块摘要')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);plan=self.source(root)
            (root/'controller-trace.jsonl').write_text(json.dumps(dict(event='trace-open')))
            plan['source_files_sha256']['controller-trace.jsonl']=sha(root/'controller-trace.jsonl')
            with self.assertRaisesRegex(ValueError,'服务'):check_plan(plan,now=10,tool_sha256='模块摘要')


if __name__=='__main__':unittest.main(verbosity=2)
