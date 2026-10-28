"""健康诊断开关必须在加载桌面控制包之前核验，不创建钩子或窗口。"""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from run_control_diagnostics import digest, serve


class LauncherHealthTests(unittest.TestCase):
    def refuse(self, options, reason):
        with tempfile.TemporaryDirectory(prefix='pt-health-approval-') as directory:
            root = Path(directory)
            (root / 'windows_mcp').mkdir()
            manifest = root / 'package-manifest.json'
            manifest.write_text(json.dumps(dict(files=digest(root / 'windows_mcp'))), encoding='utf-8')
            approval = dict(mode='diagnostics-only', task_id='离线任务', dispatch_id='离线派发',
                            package_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                            launcher_files={}, **options)
            approval_path = root / 'approval.json'
            approval_path.write_text(json.dumps(approval), encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, reason):
                serve(root, root / 'trace.jsonl', approval_path)
            self.assertFalse((root / 'trace.jsonl').exists())

    def test_fix_requires_sampling(self):
        self.refuse(dict(indicator_health_fix=True), '必须同时启用实际判定采样')

    def test_sampling_requires_frozen_module(self):
        self.refuse(dict(indicator_health_sampling=True), '未列入批准摘要')

    def test_bitmap_timing_requires_sampling_and_frozen_module(self):
        self.refuse(dict(indicator_bitmap_timing=True), '必须同时批准健康采样')
        # 选项拒绝在控制包导入前完成。
        self.refuse(dict(indicator_bitmap_timing='true'), '必须是布尔值')

    def test_string_false_is_not_a_boolean_option(self):
        for name in ('indicator_health_sampling', 'indicator_health_fix'):
            with self.subTest(name=name):
                self.refuse({name: 'false'}, '必须是布尔值')


if __name__ == '__main__':
    unittest.main(verbosity=2)
