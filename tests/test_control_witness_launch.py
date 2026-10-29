"""以无GUI的标准库子进程验证venv见证器身份、放行和精确退出码。"""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_witness_launch import WitnessLaunch,base_python


class WitnessLaunchTests(unittest.TestCase):
    def test_base_interpreter_is_real_file_without_pid_redirect(self):
        interpreter=base_python()
        self.assertTrue(interpreter.is_file())
        self.assertEqual(interpreter,Path(sys._base_executable).resolve())

    def test_payload_waits_for_exact_pid_handshake_and_wait_preserves_exit_code(self):
        with tempfile.TemporaryDirectory(prefix='pt-witness-') as directory:
            root=Path(directory);script=root/'witness.py';marker=root/'executed.json'
            script.write_text("import os,json\nfrom pathlib import Path\nPath('executed.json').write_text(json.dumps(dict(pid=os.getpid())))\n",encoding='utf-8')
            launch=WitnessLaunch(script,root/'evidence')
            self.assertEqual(launch.identity['pid'],launch.process.pid)
            self.assertFalse(marker.exists())
            launch.release()
            result=launch.wait(10)
            self.assertEqual(result['exit_code'],0)
            self.assertEqual(json.loads(marker.read_text())['pid'],result['pid'])
            self.assertEqual(result['pid'],result['actual_pid'])
            with self.assertRaises(RuntimeError):launch.release()
            self.assertEqual(result['termination_calls'],0)

    def test_payload_nonzero_exit_is_recorded_without_retry_or_kill(self):
        with tempfile.TemporaryDirectory(prefix='pt-witness-error-') as directory:
            root=Path(directory);script=root/'witness.py'
            script.write_text('raise SystemExit(7)',encoding='utf-8')
            launch=WitnessLaunch(script,root/'evidence');launch.release()
            result=launch.wait(10)
            self.assertEqual(result['exit_code'],7)
            self.assertTrue((launch.directory/'popen-exit.json').exists())
            self.assertEqual(len(list((root/'evidence').iterdir())),1)

    def test_identity_read_permission_retry_keeps_original_deadline_and_process(self):
        launch=WitnessLaunch.__new__(WitnessLaunch)
        payload=dict(pid=123,executable='基础Python',script_sha256='冻结摘要',release_deadline=20)
        launch.ready_path=SimpleNamespace(read_text=Mock(side_effect=[FileNotFoundError('未发布'),PermissionError('暂不可读'),json.dumps(payload)]))
        launch.process=SimpleNamespace(poll=Mock(return_value=None))
        now=[10.]
        def advance(seconds):now[0]+=seconds
        with patch('control_witness_launch.time.monotonic',side_effect=lambda:now[0]),patch('control_witness_launch.time.sleep',side_effect=advance):
            self.assertEqual(launch._wait_identity(10.05),payload)
        self.assertEqual(launch.ready_path.read_text.call_count,3)
        self.assertEqual(launch.process.poll.call_count,2)
        self.assertLess(now[0],10.05)
        self.assertEqual(payload['release_deadline'],20)

    def test_permanently_unreadable_identity_expires_without_release_or_new_process(self):
        launch=WitnessLaunch.__new__(WitnessLaunch)
        launch.ready_path=SimpleNamespace(read_text=Mock(side_effect=PermissionError('持续不可读')))
        launch.process=SimpleNamespace(poll=Mock(return_value=None))
        now=[10.]
        def advance(seconds):now[0]+=seconds
        with patch('control_witness_launch.time.monotonic',side_effect=lambda:now[0]),patch('control_witness_launch.time.sleep',side_effect=advance):
            with self.assertRaisesRegex(RuntimeError,'原握手截止.*PermissionError') as caught:
                launch._wait_identity(10.025)
        self.assertIs(caught.exception.pending_launch,launch)
        self.assertLessEqual(now[0],10.035)
        self.assertEqual(launch.ready_path.read_text.call_count,3)

    def test_initialization_read_or_parse_exception_retains_original_popen_for_wait(self):
        for error in (PermissionError('身份文件不可读'),ValueError('身份JSON损坏')):
            with self.subTest(error=error),tempfile.TemporaryDirectory(prefix='pt-witness-constructor-') as directory:
                root=Path(directory);script=root/'target.py';script.write_text('raise SystemExit(0)')
                process=SimpleNamespace(pid=123,poll=Mock(return_value=None),wait=Mock(return_value=7))
                with patch('control_witness_launch.base_python',return_value=Path(sys._base_executable)),patch('control_witness_launch.subprocess.Popen',return_value=process) as create,patch.object(WitnessLaunch,'_wait_identity',side_effect=error):
                    with self.assertRaises(type(error)) as caught:WitnessLaunch(script,root/'evidence')
                launch=caught.exception.pending_launch
                self.assertIs(launch.process,process)
                self.assertFalse(launch.released)
                self.assertFalse(launch.release_path.exists())
                self.assertEqual(create.call_count,1)
                result=launch.wait(10)
                self.assertEqual(result['exit_code'],7)
                self.assertIsNone(result['actual_pid'])
                self.assertFalse(result['released'])
                self.assertTrue(launch.stdout.closed and launch.stderr.closed)
                self.assertFalse(list(root.glob('executed*')))

    def test_changed_script_is_not_released_and_pending_popen_is_retained(self):
        with tempfile.TemporaryDirectory(prefix='pt-witness-changed-') as directory:
            root=Path(directory);script=root/'witness.py';script.write_text("print('原脚本')",encoding='utf-8')
            launch=WitnessLaunch(script,root/'evidence')
            script.write_text("from pathlib import Path;Path('不应执行').touch()",encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'握手后变化') as caught:launch.release()
            self.assertIs(caught.exception.pending_launch,launch)
            self.assertFalse(launch.release_path.exists())
            # 不放行目标；写错误身份使假测试子进程自行拒绝并正常结束。
            launch.release_path.write_text(json.dumps(dict(pid=-1,script_sha256='错误摘要')),encoding='utf-8')
            result=launch.wait(10)
            self.assertNotEqual(result['exit_code'],0)
            self.assertFalse((root/'不应执行').exists())
            self.assertFalse(result['released'])


if __name__=='__main__':unittest.main(verbosity=2)
