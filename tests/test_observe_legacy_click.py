"""EX-001 只读候选的假 API 验证：不加载 DLL、不读取桌面、不创建窗口。"""
import ast
import ctypes
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import observe_legacy_click as candidate


class Function:
    def __init__(self, call):
        self.call = call

    def __call__(self, *args):
        return self.call(*args)


class FakeApi:
    def __init__(self):
        self.calls = []
        self.fail = set()
        self.foregrounds = iter([2**40 + 1, 2**40 + 2])
        for name in candidate.SIGNATURES:
            setattr(self, name, Function(lambda *args, name=name: self.call(name, *args)))

    def call(self, name, *args):
        self.calls.append(name)
        if name in self.fail:
            return -1 if name == 'GetAwarenessFromDpiAwarenessContext' else 0
        if name == 'GetForegroundWindow':
            return next(self.foregrounds)
        if name in ('GetCursorPos', 'GetPhysicalCursorPos'):
            args[0]._obj.x, args[0]._obj.y = (-25, 80) if name == 'GetCursorPos' else (-50, 160)
            return 1
        if name in ('WindowFromPoint', 'WindowFromPhysicalPoint'):
            assert isinstance(args[0], candidate.wintypes.POINT)
            return 2**40 + 3
        if name == 'GetWindowThreadProcessId':
            args[1]._obj.value = 444
            return 555
        if name == 'GetWindowRect':
            rect = args[1]._obj
            rect.left, rect.top, rect.right, rect.bottom = -100, 0, 500, 500
            return 1
        if name == 'GetGUIThreadInfo':
            value = args[1]._obj
            assert value.cbSize == ctypes.sizeof(candidate.GuiThreadInfo)
            value.flags, value.hwndCapture, value.hwndMenuOwner = 4, 7, 8
            return 1
        if name in ('GetThreadDpiAwarenessContext', 'GetWindowDpiAwarenessContext'):
            return 2**40 + 4
        if name == 'GetAwarenessFromDpiAwarenessContext':
            return 2
        if name == 'GetDpiForWindow':
            return 192
        raise AssertionError(name)


def observer(api):
    ticks = iter(range(10000))
    return candidate.Observer(api, clock=lambda: next(ticks), last_error=lambda: 5)


class ObserverTests(unittest.TestCase):
    def test_transition_negative_points_large_handles_and_menu(self):
        api = FakeApi()
        row = observer(api).sample([12], [-50, 160])
        self.assertNotEqual(row['foreground_before']['value'], row['foreground_after']['value'])
        self.assertEqual(row['logical_cursor']['point'], [-25, 80])
        self.assertEqual(row['physical_cursor']['point'], [-50, 160])
        self.assertEqual(row['foreground_gui']['state']['menu_owner'], 8)
        self.assertEqual(row['windows'][0]['pid'], 444)
        self.assertFalse(row['runtime_verified'])
        for value in [row['foreground_before'], row['foreground_after'], row['logical_cursor']]:
            self.assertLess(value['start_ns'], value['end_ns'])
        self.assertEqual(row['hit_predictions'][0]['source'], 'request_assumed_physical')

    def test_failed_cursor_not_zero_filled_or_used_for_hit(self):
        api = FakeApi()
        api.fail.update(['GetCursorPos', 'GetPhysicalCursorPos', 'GetWindowRect', 'GetGUIThreadInfo'])
        row = observer(api).sample([12], [1, 2])
        self.assertIsNone(row['logical_cursor']['point'])
        self.assertEqual(row['logical_cursor']['win32_error'], 5)
        self.assertEqual(len(row['hit_predictions']), 1)
        self.assertIsNone(row['windows'][0]['rect']['rect_observer_context'])
        self.assertIsNone(row['foreground_gui']['state'])

    def test_null_foreground_and_hits_not_converted_to_known_recipient(self):
        api = FakeApi()
        api.fail.update(['GetForegroundWindow', 'WindowFromPoint', 'WindowFromPhysicalPoint'])
        row = observer(api).sample([12], [1, 2])
        self.assertIsNone(row['foreground_gui'])
        self.assertEqual(len(row['windows']), 1)
        self.assertEqual(row['hit_predictions'][0]['query']['value'], 0)
        self.assertIsNone(row['hit_predictions'][0]['query']['win32_error'])

    def test_unknown_dpi_identity_and_gui_are_retained(self):
        api = FakeApi()
        api.fail.update(['GetThreadDpiAwarenessContext', 'GetWindowDpiAwarenessContext',
                         'GetDpiForWindow', 'GetWindowThreadProcessId'])
        row = observer(api).sample([12], [1, 2])
        self.assertIsNone(row['observer_awareness'])
        self.assertIsNone(row['windows'][0]['pid'])
        self.assertIsNone(row['windows'][0]['awareness'])
        self.assertTrue(row['windows'][0]['dpi']['failed'])
        self.assertIsNone(row['foreground_gui'])

    def test_signatures_preserve_pointer_width_and_point_by_value(self):
        api = candidate.bind(FakeApi())
        self.assertIs(api.GetForegroundWindow.restype, candidate.wintypes.HWND)
        self.assertIs(api.GetThreadDpiAwarenessContext.restype, ctypes.c_void_p)
        self.assertEqual(api.WindowFromPhysicalPoint.argtypes, [candidate.wintypes.POINT])
        self.assertEqual(api.calls, [])
        if sys.platform == 'win32':
            self.assertEqual(ctypes.sizeof(candidate.wintypes.POINT), 8)
            self.assertEqual(ctypes.sizeof(candidate.GuiThreadInfo), 72 if ctypes.sizeof(ctypes.c_void_p) == 8 else 48)

    def test_bounded_loop_no_catchup(self):
        now = [0]
        rows = []
        class Slow:
            def sample(self, *args):
                now[0] += 20_000_000
                return {'start_ns': now[0] - 20_000_000, 'end_ns': now[0]}
        result = candidate.sample_for(Slow(), [12], [1, 2], .05, .01, rows.append,
                                     clock=lambda: now[0], sleep=lambda value: now.__setitem__(0, now[0] + int(value * 1e9)))
        self.assertEqual(result['samples'], 2)
        self.assertEqual([row['sequence'] for row in rows], [0, 1])
        self.assertGreaterEqual(result['end_ns'], result['deadline_ns'])

    def test_invalid_budget_or_identity_rejected_before_any_api(self):
        for windows, point, duration, interval in [([], [1, 2], 2, .01), ([True], [1, 2], 2, .01),
                ([12], [2**31, 1], 2, .01), ([12], [1, 2], 4, .01),
                ([12], [1, 2], 2, .001), ([12], [1, 2], float('nan'), .01)]:
            with self.subTest(windows=windows, point=point, duration=duration, interval=interval):
                with self.assertRaises(ValueError):
                    candidate.sample_for(None, windows, point, duration, interval, lambda row: None)

    def test_no_dll_loaded_on_import_or_default_cli_and_no_output_overwrite(self):
        script = Path(candidate.__file__)
        result = subprocess.run([sys.executable, str(script), '--window', '12', '--point', '1', '2',
                                 '--output', 'unused.jsonl'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        with tempfile.TemporaryDirectory(prefix='pt-renew-ex001-') as directory:
            output = Path(directory) / 'existing.jsonl'
            output.write_text('原件', encoding='utf-8')
            with patch.object(sys, 'argv', [str(script), '--observe-readonly', '--window', '12',
                              '--point', '1', '2', '--output', str(output)]), patch.object(candidate, 'Observer') as native:
                with self.assertRaises(FileExistsError):
                    candidate.main()
                native.assert_not_called()
            self.assertEqual(output.read_text(encoding='utf-8'), '原件')

    def test_api_failure_signal_prevents_next_native_query(self):
        api = FakeApi()
        api.fail.add('GetCursorPos')
        failed = []
        value = candidate.Observer(api, last_error=lambda: 5,
            cancelled=lambda: bool(failed), on_failure=failed.append)
        result = value.point('GetCursorPos')
        self.assertTrue(result['failed'])
        self.assertEqual(failed[0]['win32_error'], 5)
        with self.assertRaises(InterruptedError): value.point('GetPhysicalCursorPos')
        self.assertEqual(api.calls, ['GetCursorPos'])

    def test_cancel_before_next_api_does_not_query_or_read_error(self):
        api = FakeApi()
        value = candidate.Observer(api, cancelled=lambda: True,
                                   last_error=lambda: self.fail('不能读取错误码'))
        with self.assertRaises(InterruptedError):
            value.call('GetForegroundWindow')
        self.assertEqual(api.calls, [])

    def test_unknown_api_rejected_before_call(self):
        api = FakeApi()
        with self.assertRaisesRegex(ValueError, '拒绝'):
            observer(api).call('SetCursorPos', 1, 2)
        self.assertEqual(api.calls, [])

    def test_api_allowlist_has_no_mutators_hooks_or_desktop_import(self):
        tree = ast.parse(Path(candidate.__file__).read_text(encoding='utf-8'))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertNotIn('windows_mcp', imports)
        self.assertFalse(any(name.startswith(('Set', 'Send', 'Post', 'Create', 'Attach'))
                             for name in candidate.SIGNATURES))
        # 实际用户库调用只有签名表中的只读函数；动态调用按同一表审查。
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
                      and isinstance(node.value, ast.Attribute) and node.value.attr == 'user'}
        self.assertEqual(attributes, set())


if __name__ == '__main__':
    unittest.main(verbosity=2)
