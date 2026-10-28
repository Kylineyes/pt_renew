"""首次激活的离线契约测试；只用假窗口、假工具及假时钟，不访问桌面。"""
from pathlib import Path
import copy
import sys
import types
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from control_target_activation import InitialTargetActivation, TITLE


class FakeGuard:
    def __init__(self):
        self.busy=False;self.failed=None;self.diagnosis=None;self.token='uia';self.seen=set()
        self.target=dict(pid=42,image='C:/test/pythonw.exe')
        self.expected_birth=100;self.expected_hwnd=99;self.not_before=0.;self.now=10.
        self.clock=types.SimpleNamespace(monotonic=lambda:self.now)
        self.calls=[];self.events=[];self.post=False;self.blocked=False;self.crash=False
        self.window=dict(pid=42,birth=100,hwnd=99,image='c:/TEST/PYTHONW.EXE',title=TITLE,cls='TkTopLevel')
        self.native_row=dict(input_desktop='Default',locked=False,foreground_stable=True,
                             foreground=dict(pid=1,hwnd=2),windows=[self.window])
        self.held={192}
    def event(self,kind,**data):self.events.append((kind,data))
    def cool_check(self):
        if self.now<self.not_before:raise RuntimeError('120秒未满')
    def require_arguments(self,tool,args):
        if (tool,args)!=('App',dict(mode='switch',name=TITLE)):raise ValueError('入口不允许')
    async def native(self):self.calls.append('native');return copy.deepcopy(self.native_row)
    async def raw(self,tool,args):
        self.calls.append((tool,args))
        if self.blocked:
            self.retreat('原工具拒绝')
        if self.crash:raise ConnectionError('传输未知')
        if self.post:self.native_row['foreground']=copy.deepcopy(self.window)
        return dict(is_error=False)
    async def observe_native(self):
        self.calls.append('post-native')
        if self.native_row['foreground'].get('hwnd')!=self.expected_hwnd:
            self.retreat('目标不是前景')
    def retreat(self,reason):self.not_before=self.now+120;raise RuntimeError(reason)


class ActivationTests(unittest.IsolatedAsyncioTestCase):
    async def activate(self,guard,activation=None,**kwargs):
        activation=activation or InitialTargetActivation()
        return await activation.run(guard,'activate','uia',uia_ready=kwargs.get('uia_ready',True),
                                    groups_started=kwargs.get('groups_started',0))

    async def test_non_target_foreground_uses_one_original_app_then_postcheck(self):
        guard=FakeGuard();guard.post=True
        result=await self.activate(guard)
        self.assertTrue(result['completed'])
        self.assertEqual(guard.calls,['native',('App',dict(mode='switch',name=TITLE)),'post-native'])
        self.assertEqual(guard.token,'activate');self.assertIsNone(guard.failed)
        self.assertEqual(guard.held,{192})
        self.assertFalse(guard.busy)

    async def test_success_text_without_target_foreground_still_fails(self):
        guard=FakeGuard();activation=InitialTargetActivation()
        result=await self.activate(guard,activation)
        self.assertFalse(result['completed']);self.assertTrue(result['executed'])
        self.assertEqual(guard.failed,'activate');self.assertEqual(guard.not_before,130.)
        before=list(guard.calls)
        retry=await activation.run(guard,'second','uia',uia_ready=True,groups_started=0)
        self.assertFalse(retry['completed']);self.assertEqual(guard.calls,before)
        self.assertEqual(guard.held,{192})

    async def test_mismatched_identity_or_duplicate_title_never_sends_app(self):
        changes=[('pid',43),('birth',101),('hwnd',98),('image','different'),('cls','Other')]
        for key,value in changes:
            with self.subTest(key=key):
                guard=FakeGuard();guard.window[key]=value
                result=await self.activate(guard)
                self.assertFalse(result['completed']);self.assertFalse(result['tool_call_sent'])
                self.assertEqual(guard.calls,['native']);self.assertEqual(guard.failed,'activate')
        guard=FakeGuard();guard.native_row['windows'].append(copy.deepcopy(guard.window))
        result=await self.activate(guard)
        self.assertFalse(result['completed']);self.assertEqual(guard.calls,['native'])

    async def test_locked_unstable_or_unknown_desktop_never_activates(self):
        for key,value in [('locked',True),('foreground_stable',False),('input_desktop',None)]:
            guard=FakeGuard();guard.native_row[key]=value
            result=await self.activate(guard)
            self.assertFalse(result['tool_call_sent']);self.assertEqual(guard.calls,['native'])

    async def test_original_tool_refusal_and_transport_unknown_preserved(self):
        for attribute in ('blocked','crash'):
            guard=FakeGuard();setattr(guard,attribute,True)
            result=await self.activate(guard)
            self.assertFalse(result['completed']);self.assertEqual(result['executed'],'unknown')
            self.assertEqual(guard.not_before,130.);self.assertEqual(guard.failed,'activate')
            self.assertNotIn('post-native',guard.calls)
            self.assertEqual(guard.held,{192})

    async def test_failed_busy_old_token_unready_or_existing_group_rejected_without_calls(self):
        cases=[dict(failed='old'),dict(busy=True),dict(token='stale'),dict(expected_hwnd=None),dict(expected_birth=None)]
        for changes in cases:
            guard=FakeGuard()
            for name,value in changes.items():setattr(guard,name,value)
            result=await self.activate(guard)
            self.assertFalse(result['completed']);self.assertEqual(guard.calls,[])
            self.assertEqual(guard.failed,changes.get('failed'))
        for kwargs in (dict(uia_ready=False),dict(groups_started=1)):
            guard=FakeGuard();result=await self.activate(guard,**kwargs)
            self.assertFalse(result['completed']);self.assertEqual(guard.calls,[])

    async def test_cooldown_never_calls_native_or_tool_and_is_not_reset(self):
        guard=FakeGuard();guard.not_before=100.
        result=await self.activate(guard)
        self.assertFalse(result['completed']);self.assertEqual(guard.calls,[])
        self.assertEqual(guard.not_before,100.);self.assertFalse(guard.busy)

    async def test_duplicate_id_never_replays(self):
        guard=FakeGuard();guard.seen.add('activate')
        result=await self.activate(guard)
        self.assertFalse(result['completed']);self.assertEqual(guard.calls,[])


if __name__=='__main__':unittest.main(verbosity=2)
