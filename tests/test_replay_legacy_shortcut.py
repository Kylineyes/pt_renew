"""Shortcut原AST的假API回归；不导入windows_mcp、不调用真实键盘或桌面。"""
import ast
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import replay_legacy_shortcut as candidate


def events(result, api): return [row for row in result['calls'] if row['api']==api]


class ExtractionBoundaryTests(unittest.TestCase):
    def test_refuses_import_dynamic_execution_and_reflection(self):
        for code in ('import os', 'def f():\n return open("x")',
                     'def f():\n return __import__("os")', 'def f():\n return value.__class__',
                     'def f():\n return __builtins__["__import__"]("os")'):
            with self.subTest(code=code), self.assertRaises(ValueError):
                candidate.compile_selected(ast.parse(code).body, {})

    def test_default_cli_refuses_output_overwrite_before_source_execution(self):
        with tempfile.TemporaryDirectory(prefix='pt-renew-ex003-') as directory:
            path=Path(directory)/'result.json';path.write_text('原件',encoding='utf-8')
            with patch.object(sys,'argv',['tool','--source','不存在路径','--output',str(path)]), patch.object(candidate,'ShortcutReplay') as replay:
                with self.assertRaises(FileExistsError):candidate.main()
                replay.assert_not_called()
            self.assertEqual(path.read_text(encoding='utf-8'),'原件')


@unittest.skipUnless(all((candidate.DEFAULT_SOURCE/p).is_file() for p in candidate.SOURCE_FILES), '需要只读的本机安装源码；不下载或导入包')
class OriginalShortcutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.replay=candidate.ShortcutReplay()
    @classmethod
    def tearDownClass(cls):
        if not cls.replay.unchanged():raise AssertionError('原安装源码变化')

    def successful(self, value, **kwargs):
        result=self.replay.trace(value,**kwargs)
        self.assertIsNone(result['error'])
        self.assertEqual(result['result'],'Pressed '+value+'.')
        self.assertEqual([r['event'] for r in result['control']],['checkpoint','record_step'])
        return result

    def test_shift_i_exact_vk_order_flags_scans_and_nominal_waits(self):
        row=self.successful('shift+i')
        self.assertEqual(row['sendkeys'],[{'text':'{shift}i','kwargs':{'interval':.01}}])
        self.assertEqual([(r['vk'],r['scan'],r['flags'],r['extra'],r['at_ns']) for r in events(row,'keybd_event')],
            [(16,42,1,0,0),(73,23,1,0,10_000_000),(73,23,3,0,20_000_000),(16,42,3,0,30_000_000)])
        self.assertEqual(events(row,'SendInput'),[])
        self.assertEqual(row['nominal_sleep_ns'],540_000_000)

    def test_letter_case_and_whitespace_keep_same_vk_path_under_shift(self):
        expected=[(16,1),(73,1),(73,3),(16,3)]
        for key in ('Shift+I',' shift + i '):
            with self.subTest(key=key):
                row=self.successful(key)
                self.assertEqual([(r['vk'],r['flags']) for r in events(row,'keybd_event')],expected)

    def test_named_enter_return_esc_escape(self):
        for text,vk in [('enter',13),('return',13),('esc',27),('escape',27),('down',40),('up',38)]:
            with self.subTest(text=text):
                row=self.successful(text)
                self.assertEqual([(r['vk'],r['flags']) for r in events(row,'keybd_event')],[(vk,1),(vk,3)])
                self.assertEqual(events(row,'SendInput'),[])
                self.assertEqual(row['nominal_sleep_ns'],520_000_000)

    def test_shift_s_uses_vk_s(self):
        row=self.successful('shift+s')
        self.assertEqual([(r['vk'],r['flags']) for r in events(row,'keybd_event')],[(16,1),(83,1),(83,3),(16,3)])

    def test_plain_lower_and_upper_letters_are_unicode_not_shift(self):
        for text,unit in [('i',105),('I',73),('s',115)]:
            with self.subTest(text=text):
                row=self.successful(text)
                self.assertEqual([(r['vk'],r['scan'],r['flags'],r['count']) for r in events(row,'SendInput')],[(0,unit,4,1),(0,unit,6,1)])
                self.assertEqual(events(row,'keybd_event'),[])
                self.assertEqual(events(row,'MapVirtualKeyA'),[])
                self.assertEqual(row['nominal_sleep_ns'],510_000_000)

    def test_f11_is_released_before_unicode_p(self):
        row=self.successful('f11+p')
        self.assertEqual([(r['vk'],r['flags']) for r in events(row,'keybd_event')],[(122,1),(122,3)])
        ordered=[r for r in row['calls'] if r['api'] in ('keybd_event','SendInput')]
        self.assertEqual([r['api'] for r in ordered],['keybd_event','keybd_event','SendInput','SendInput'])
        self.assertEqual(ordered[2]['scan'],ord('p'))

    def test_left_shift_uses_original_fixed_scan_table(self):
        row=self.successful('lshift+i')
        self.assertEqual(events(row,'keybd_event')[0]['vk'],160)
        self.assertEqual(events(row,'keybd_event')[0]['scan'],42)
        self.assertFalse(any(r['vk']==160 for r in events(row,'MapVirtualKeyA')))

    def test_nonmapped_character_is_unicode_after_shift_release(self):
        row=self.successful('shift+中')
        ordered=[r for r in row['calls'] if r['api'] in ('keybd_event','SendInput')]
        self.assertEqual([r['flags'] for r in ordered],[1,3,4,6])
        self.assertEqual(ordered[2]['scan'],ord('中'))

    def test_supplementary_unicode_is_two_utf16_event_pairs(self):
        row=self.successful('😀')
        self.assertEqual([(r['scan'],r['flags']) for r in events(row,'SendInput')],[(0xD83D,4),(0xD83D,6),(0xDE00,4),(0xDE00,6)])

    def test_zero_sendinput_results_do_not_prevent_success_text(self):
        for returns in ((0,1),(1,0),(0,0)):
            with self.subTest(returns=returns):
                row=self.successful('i',send_input_returns=returns)
                self.assertEqual([r['result'] for r in events(row,'SendInput')],list(returns))

    def test_mapping_zero_keeps_vk_injection_without_delivery_confirmation(self):
        row=self.successful('shift+i',scan_map={})
        self.assertEqual([r['scan'] for r in events(row,'keybd_event')],[0,0,0,0])
        self.assertEqual([r['flags'] for r in events(row,'keybd_event')],[1,1,3,3])

    def test_checkpoint_rejection_sends_zero_events_and_no_success(self):
        row=self.replay.trace('shift+i',fail_checkpoint=True)
        self.assertEqual(row['calls'],[])
        self.assertEqual(row['sendkeys'],[])
        self.assertIsNone(row['result'])
        self.assertEqual([r['event'] for r in row['control']],['checkpoint'])

    def test_mid_sequence_exception_is_not_a_transaction_or_success(self):
        row=self.replay.trace('shift+i',keybd_raises_at=2)
        self.assertEqual(row['error']['type'],'RuntimeError')
        self.assertIsNone(row['result'])
        self.assertEqual([(r['vk'],r['flags']) for r in events(row,'keybd_event')],[(16,1),(73,1)])
        self.assertFalse(any(r['event']=='record_step' for r in row['control']))

    def test_invalid_plus_is_rejected_before_native_api(self):
        row=self.replay.trace('+')
        self.assertEqual(row['error']['type'],'TypeError')
        self.assertIn('ord() expected a character',row['error']['message'])
        self.assertEqual(row['calls'],[])
        self.assertIsNone(row['result'])


if __name__=='__main__': unittest.main(verbosity=2)
