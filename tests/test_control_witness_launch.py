"""以无GUI的标准库子进程验证venv见证器身份、放行和精确退出码。"""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest

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
