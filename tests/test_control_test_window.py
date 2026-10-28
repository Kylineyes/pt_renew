"""测试窗新增日志路径的离线测试，不建立GUI或发送输入。"""
from pathlib import Path
import io
import json
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from control_test_window import CallbackCounter, WindowLog, launch_window, report_callback_error


class WindowLoggingTests(unittest.TestCase):
    def test_two_callbacks_have_distinct_kinds_and_monotonic_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            log = WindowLog(path)
            labels = []
            counter = CallbackCounter(log, labels.append)
            counter.on_input('click')
            counter.on_input('shortcut')
            log.record('normal-close', counts=dict(counter.counts))
            log.close()
            rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
            self.assertEqual([row['kind'] for row in rows[:2]], ['click', 'shortcut'])
            self.assertEqual([row['counts'] for row in rows],
                             [{'click': 1, 'shortcut': 0}, {'click': 1, 'shortcut': 1}, {'click': 1, 'shortcut': 1}])
            self.assertLessEqual(rows[0]['monotonic'], rows[1]['monotonic'])
            self.assertEqual(labels[-1], '按钮回调：1；快捷键回调：1')

    def test_callback_exception_is_recorded_with_original_stderr_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            log = WindowLog(path)
            stderr = io.StringIO()
            try:
                raise RuntimeError('定向异常证据')
            except RuntimeError:
                report_callback_error(log, *sys.exc_info(), stderr=stderr)
            log.close()
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['event'], 'callback-error')
            self.assertIn('Traceback', stderr.getvalue())
            self.assertIn('RuntimeError: 定向异常证据', stderr.getvalue())

    def test_explicit_child_stdout_stderr_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / 'exception_child.py'
            script.write_text("import sys\nprint('定向标准输出', flush=True)\nraise RuntimeError('子进程异常证据')\n", encoding='utf-8')
            child = launch_window(sys.executable, script, root)
            self.assertNotEqual(child.wait(timeout=10), 0)
            self.assertIn('定向标准输出', (root / 'window-stdout.log').read_text(encoding='utf-8'))
            self.assertIn('RuntimeError: 子进程异常证据', (root / 'window-stderr.log').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
