"""专用关闭与普通输入边界测试；只使用假时钟/Popen/API。"""
import asyncio
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import json
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
sys.path.insert(0, str(ROOT/'tools/control_close_client'))
from control_owned_close import OwnedDiagnosticClose, TITLE
from diagnostic_guard import DiagnosticGuard
from budget import Budget
import step
from freeze_control_close import freeze


class Clock:
    now = 10.0
    def monotonic(self): return self.now
    def wall(self): return 1000 + self.now


class Process:
    pid = 42
    returncode = None
    polls = 0
    def poll(self):
        self.polls += 1
        return self.returncode


class Rig:
    def __init__(self, *, enabled=True):
        self.clock = Clock()
        self.process = Process()
        self.events = []
        self.calls = []
        self.native_calls = 0
        self.error = None
        self.wait_error = None
        self.code = 0
        self.disappear = False
        self.window = dict(pid=42, birth=100, image='C:/test/pythonw.exe', hwnd=99,
                           title=TITLE, cls='TkTopLevel', rect=[0, 0, 100, 100])
        async def native():
            self.native_calls += 1
            w = copy.deepcopy(self.window)
            return dict(input_desktop='Default', locked=False, foreground_stable=True,
                        windows=[] if self.disappear else [w],
                        foreground=dict(pid=1, hwnd=2) if self.disappear else w)
        async def transport(tool, args):
            self.calls.append((tool, args))
            self.disappear = True
            if isinstance(self.error, BaseException): raise self.error
            return self.error or dict(text=['已执行'], is_error=False)
        async def waiter(process, seconds):
            self.assert_process = process
            self.clock.now += seconds
            if self.wait_error: raise self.wait_error
            process.returncode = self.code
            return self.code
        self.guard = DiagnosticGuard(transport, native, self.events.append, self.clock)
        self.guard.birth_getter = lambda pid: 100
        self.guard.geometry_getter = lambda *args: dict(rect=[0,0,100,100],
            coordinate_space='physical-desktop-pixels', thread_context_restored=True)
        self.guard.bind(42, self.window['image'])
        self.guard.expected_hwnd = 99
        self.close = OwnedDiagnosticClose(enabled=enabled, cleanup_deadline=1000., waiter=waiter)
        self.close.bind_created(self.process, birth=100, image=self.window['image'])
    async def run(self, ident='close', **kwargs):
        return await self.close.run(self.guard, ident, self.guard.token,
                                    stage_ready=kwargs.get('stage_ready', True), pending=kwargs.get('pending', False))


class CloseTests(unittest.IsolatedAsyncioTestCase):
    async def test_original_tool_once_then_original_popen_exit_retire_and_no_post_native(self):
        rig = Rig()
        row = await rig.run()
        self.assertTrue(row['completed'])
        self.assertEqual(rig.calls, [('Shortcut', dict(shortcut='alt+f4'))])
        self.assertEqual(rig.native_calls, 1)
        self.assertIs(rig.assert_process, rig.process)
        self.assertIsNone(rig.guard.target)
        self.assertEqual(rig.guard.token, 'close')
        self.assertIsNone(rig.guard.failed)
        self.assertEqual(rig.guard.not_before, 0)
        kinds = [e['kind'] for e in rig.events]
        expected = ['owned_close_request','owned_close_tool_start','tool_request','tool_result',
                    'owned_close_tool_end','owned_close_exit','target_retired','owned_close_complete']
        self.assertEqual([k for k in kinds if k in expected], expected)
        before = (len(rig.calls), rig.native_calls)
        self.assertFalse((await rig.run('again'))['completed'])
        self.assertEqual(before, (len(rig.calls), rig.native_calls))

    async def test_disabled_busy_failed_bad_token_id_stage_and_queue_do_no_work(self):
        for change in ('disabled','busy','failed','token','duplicate','hwnd','stage','queue'):
            with self.subTest(change=change):
                rig = Rig(enabled=change!='disabled')
                if change=='busy': rig.guard.busy=True
                if change=='failed': rig.guard.failed='old'
                if change=='duplicate': rig.guard.seen.add('close')
                if change=='hwnd': rig.guard.expected_hwnd=None
                parent = 'wrong' if change=='token' else rig.guard.token
                polls = rig.process.polls
                row = await rig.close.run(rig.guard,'close',parent,
                    stage_ready=change!='stage', pending=change=='queue')
                self.assertFalse(row['completed'])
                self.assertFalse(row['tool_call_sent'])
                self.assertEqual((rig.native_calls,len(rig.calls),rig.process.polls),(0,0,polls))
                self.assertEqual(rig.guard.token,'start')
                self.assertEqual(rig.guard.failed,'old' if change=='failed' else None)
                self.assertFalse(rig.close.used)

    async def test_cooldown_and_original_cleanup_deadline_never_reset(self):
        for state in ('cooldown','deadline'):
            rig=Rig()
            if state=='cooldown': rig.guard.not_before=100
            else: rig.clock.now=920
            polls=rig.process.polls
            row=await rig.run()
            self.assertFalse(row['completed'])
            self.assertEqual((rig.native_calls,len(rig.calls),rig.process.polls),(0,0,polls))
            self.assertEqual(rig.close.cleanup_deadline,1000)
            self.assertEqual(rig.guard.not_before,100 if state=='cooldown' else 0)

    async def test_identity_errors_prevent_tool_and_preserve_failure(self):
        for key,value in [('pid',43),('birth',101),('image','other'),('hwnd',98),
                          ('title','其他窗口'),('cls','Other')]:
            with self.subTest(key=key):
                rig=Rig();rig.window[key]=value
                row=await rig.run()
                self.assertFalse(row['tool_call_sent'])
                self.assertFalse(row['completed'])
                self.assertEqual(rig.calls,[])
                self.assertEqual(rig.guard.failed,'close')
                self.assertEqual(rig.guard.token,'start')
                self.assertEqual(rig.guard.not_before,130)
                self.assertTrue(rig.close.used)

    async def test_owned_popen_cannot_be_rebound_or_replaced_with_exited_identity(self):
        rig=Rig()
        with self.assertRaises(ValueError): rig.close.bind_created(Process(),birth=100,image='other')
        for change in ('pid','birth','image','exited'):
            rig=Rig()
            if change=='pid': rig.process.pid=43
            if change=='birth': rig.guard.expected_birth=101
            if change=='image': rig.guard.target['image']='other'
            if change=='exited': rig.process.returncode=0
            row=await rig.run()
            self.assertFalse(row['completed']);self.assertEqual(rig.native_calls,0)
            self.assertEqual(rig.calls,[])

    async def test_errors_unknown_timeout_cancel_never_get_rewritten_by_later_exit(self):
        errors=[dict(is_error=True,text=['工具错误']),dict(text=['Error: 原工具拒绝']),
                ConnectionError('传输未知'),asyncio.CancelledError()]
        for error in errors:
            with self.subTest(error=str(error)):
                rig=Rig();rig.error=error
                row=await rig.run()
                self.assertFalse(row['completed']);self.assertEqual(row['executed'],'unknown')
                self.assertEqual(rig.guard.token,'start');self.assertEqual(rig.guard.failed,'close')
                self.assertEqual(rig.guard.not_before,130)
                rig.process.returncode=0
                rig.guard.retire(rig.process.pid,rig.process.poll())
                self.assertEqual(rig.guard.failed,'close');self.assertEqual(rig.guard.not_before,130)
                self.assertEqual(rig.guard.token,'start')
                self.assertFalse((await rig.run('retry'))['completed'])
                self.assertEqual(len(rig.calls),1)
                self.assertEqual(rig.native_calls,1)

    async def test_wait_timeout_cancellation_or_nonzero_exit_keeps_target_and_failed_token(self):
        for value in (subprocess.TimeoutExpired('假进程',5),asyncio.CancelledError(),1,None):
            rig=Rig()
            if isinstance(value,BaseException): rig.wait_error=value
            else: rig.code=value
            row=await rig.run()
            self.assertFalse(row['completed']);self.assertTrue(row['executed'])
            self.assertIsNotNone(rig.guard.target)
            self.assertEqual(rig.guard.failed,'close');self.assertEqual(rig.guard.token,'start')
            self.assertEqual(rig.guard.not_before,135)
            self.assertEqual(len(rig.calls),1);self.assertEqual(rig.native_calls,1)

    async def test_preflight_elapsed_budget_is_rechecked_before_sending(self):
        rig=Rig()
        original=rig.guard.gate
        async def slow_gate():
            row=await original();rig.clock.now=920;return row
        rig.guard.gate=slow_gate
        row=await rig.run()
        self.assertFalse(row['tool_call_sent']);self.assertEqual(rig.calls,[])
        self.assertEqual(rig.close.cleanup_deadline,1000)

    async def test_ordinary_click_and_shortcut_still_require_target_postcheck(self):
        for tool,args in [('Click',dict(loc=[50,50])),('Shortcut',dict(shortcut='ctrl+shift+f8'))]:
            rig=Rig()
            row=await rig.guard.perform(dict(id='normal',parent='start',tool=tool,arguments=args))
            self.assertFalse(row['completed']);self.assertTrue(row['executed'])
            self.assertEqual(row['phase'],'post_native')
            self.assertEqual(rig.native_calls,2)
            self.assertEqual(rig.guard.failed,'normal');self.assertEqual(rig.guard.token,'start')
            self.assertEqual(rig.guard.not_before,130)

    async def test_queue_appearing_during_preflight_cannot_reach_tool(self):
        rig=Rig()
        row=await rig.close.run(rig.guard,'close','start',stage_ready=True,
            pending=lambda:rig.native_calls>0)
        self.assertFalse(row['tool_call_sent']);self.assertEqual(rig.calls,[])
        self.assertEqual(rig.guard.failed,'close')

    def test_step_close_uses_current_token_and_rejects_arbitrary_target_or_old_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'inbox').mkdir()
            (root/'live-state.json').write_text(json.dumps(dict(token='after',failed=None,busy=False,not_before_monotonic=0)))
            def finish(_):
                request=json.loads((root/'inbox/close.json').read_text())
                self.assertEqual(request,dict(id='close',parent='after',kind='close-owned',capture=False))
                (root/'close-complete.json').write_text(json.dumps(dict(completed=True)))
            with patch.object(step,'R',root),patch.object(step.time,'sleep',finish):
                self.assertTrue(step.submit('close','close-owned',[])['completed'])
                (root/'inbox/close.json').unlink()
                with self.assertRaises(AssertionError):step.submit('target','close-owned',['42'])
                with self.assertRaises(ValueError):step.submit('key','key',['ALT+F4'])

    def test_freeze_is_new_directory_only_and_contains_no_live_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);package=root/'windows_mcp';(package/'desktop').mkdir(parents=True)
            (package/'desktop/control.py').write_text('# 假包，只验证离线冻结')
            dest=root/'frozen'
            result=freeze(dest,package)
            self.assertEqual(result['desktop_requests'],0)
            self.assertFalse(result['permission_confirmed'])
            self.assertIsNone(result['task_id'])
            self.assertTrue((dest/'candidate/tools/control_owned_close.py').is_file())
            self.assertFalse((dest/'candidate/client/phase-two-approval.json').exists())
            with self.assertRaises(FileExistsError):freeze(dest,package)

    def test_budget_requires_finished_group_and_blocks_plain_alt_f4(self):
        budget=Budget()
        with self.assertRaises(AssertionError):budget.check(dict(kind='close-owned'))
        budget.groups=1;budget.stage=None;budget.snapshots=2
        self.assertTrue(budget.close_ready())
        budget.check(dict(kind='close-owned'))
        with self.assertRaises(AssertionError):budget.check(dict(kind='close-owned'))
        with self.assertRaises(ValueError):budget.check(dict(kind='action',tool='Shortcut',arguments=dict(shortcut='alt+f4')))
        budget.result(dict(kind='close-owned'),dict(completed=False,executed='unknown'))
        self.assertEqual(budget.close_outcome,'unknown');self.assertTrue(budget.refused)


if __name__=='__main__':unittest.main(verbosity=2)
