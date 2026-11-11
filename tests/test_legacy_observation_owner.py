"""Windows PowerShell 5.1 真实 -File 离线加载；在任何现场进程创建前退出。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest


@unittest.skipUnless(sys.platform == 'win32' and shutil.which('powershell.exe'), '需要现有 Windows PowerShell')
class OwnerFileLoadingTests(unittest.TestCase):
    def test_file_loading_at_both_detach_boundaries_exits_before_resolve_or_create(self):
        script = Path(__file__).resolve().parents[1] / 'tools/Start-LegacyObservationOwner.ps1'
        data = script.read_bytes()
        self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'\n', data.replace(b'\r\n', b''))
        for detach in (False, True):
            with self.subTest(detach=detach):
                # 不存在路径可证明离线检查早于 Resolve-Path、读取计划、Start-Process 和 .Start。
                argv = ['powershell.exe', '-NoProfile', '-File', str(script),
                        '-Slot', str(script.parent / 'offline-check-no-such-slot'), '-OfflineCheck']
                if detach:
                    argv.append('-Detach')
                result = subprocess.run(argv, capture_output=True, timeout=15,
                                        env=dict(os.environ, PYTHONUTF8='1'))
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
                value = json.loads(result.stdout.decode('utf-8-sig'))
                self.assertTrue(value['offline_check'])
                self.assertTrue(value['before_any_process_creation'])
                self.assertEqual(value['detach_boundary'], detach)
                self.assertTrue(value['utf8_bom'])
                self.assertTrue(value['version'].startswith('5.1.'))
                self.assertEqual(Path(value['script']), script)


if __name__ == '__main__': unittest.main(verbosity=2)
