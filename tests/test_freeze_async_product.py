"""冻结工具只用临时合成文件，不复制历史现场、不创建任务或进程。"""
from pathlib import Path
import json
import sys
import tempfile
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import freeze_async_product
from async_product_client.core import digest
from async_product_client.product import tree_hashes


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.refs = {}
        for label, count in [('experiment', 22), ('fixed', 23), ('stable', 22), ('control_package', 77)]:
            folder = self.root / label
            folder.mkdir()
            for index in range(count):
                (folder / ('pt-renew.exe' if index == 0 else f'file{index}.bin')).write_bytes(str(index).encode())
            self.refs[label] = dict(root=str(folder), files=tree_hashes(folder))
        self.inputs = {}
        for name in ('board.pcb', 'a.net', 'b.net'):
            path = self.root / name
            path.write_bytes(name.encode())
            self.inputs[str(path)] = digest(path.read_bytes())
        self.mock_sha = patch.object(freeze_async_product, 'FROZEN_EXPERIMENT_SHA', self.refs['experiment']['files']['pt-renew.exe'])
        self.mock_sha.start()
        self.addCleanup(self.mock_sha.stop)

    def test_freezes_new_candidate_dependencies_and_never_emits_live_permission(self):
        destination = self.root / 'frozen'
        result = freeze_async_product.freeze(destination, references=self.refs, inputs=self.inputs)
        plan = result['plan']
        self.assertFalse(plan['ready_for_live'])
        self.assertFalse(plan['permission_confirmed'])
        self.assertFalse(plan['budget_armed'])
        self.assertFalse(plan['live_adapter_frozen'])
        self.assertEqual(plan['max_product_launches'], 0)
        self.assertEqual((plan['task_id'], plan['dispatch_id'], plan['run_id'], plan['session_id']), (None,) * 4)
        self.assertEqual((plan['watchdog_ms'], plan['t1_read_ack_ms'], plan['t2_edit_read_ack_ms'],
                          plan['t3_release_start_before_ms']), (60000, 20000, 50000, 55000))
        self.assertEqual(result['files'], tree_hashes(destination / 'candidate'))
        self.assertEqual(result['desktop_requests'], 0)
        self.assertTrue((destination / 'candidate/tools/async_product_client/close.py').is_file())
        self.assertTrue((destination / 'candidate/tools/control_witness_launch.py').is_file())
        self.assertEqual(len([name for name in result['files'] if name.startswith('runtime/windows_mcp/')]), 77)
        self.assertTrue((destination / 'candidate/runtime/package-manifest.json').is_file())
        self.assertTrue(plan['phase_remaining_deadline_offline_tested'])
        self.assertFalse(plan['production_bootstrap_runtime_verified'])
        self.assertTrue((destination / 'candidate/tools/async_product_client/service_driver.py').is_file())
        self.assertEqual(json.loads((destination / 'frozen-manifest.json').read_text(encoding='utf-8'))['plan'], plan)
        with self.assertRaises(FileExistsError):
            freeze_async_product.freeze(destination, references=self.refs, inputs=self.inputs)
        for ref in self.refs.values():
            self.assertEqual(tree_hashes(ref['root']), ref['files'])

    def test_preexisting_bytecode_is_excluded_using_historical_manifest_scope(self):
        package = Path(self.refs['control_package']['root'])
        cache = package / '__pycache__'
        cache.mkdir()
        (cache / 'module.pyc').write_bytes('旧缓存原样保留'.encode())
        self.assertEqual(len(tree_hashes(package)), 78)
        self.assertEqual(tree_hashes(package, ignore_bytecode=True), self.refs['control_package']['files'])
        result = freeze_async_product.freeze(self.root / 'cache-candidate', references=self.refs, inputs=self.inputs)
        self.assertEqual(len([name for name in result['files'] if name.startswith('runtime/windows_mcp/')]), 77)
        self.assertTrue((cache / 'module.pyc').is_file())

    def test_freezes_complete_python_dependency_copy_without_enabling_live(self):
        dependencies = self.root / 'python-dependencies'; dependencies.mkdir()
        (dependencies / 'fake.py').write_text('# 假依赖\n', encoding='utf-8')
        environment = dict(root=str(dependencies), files=tree_hashes(dependencies), version=list(sys.version_info[:3]))
        result = freeze_async_product.freeze(self.root / 'with-python', references=self.refs, inputs=self.inputs,
                                             python_environment=environment)
        self.assertTrue(result['plan']['python_dependency_environment_frozen'])
        self.assertFalse(result['plan']['ready_for_live'])
        self.assertEqual(result['python_environment']['files'], environment['files'])
        target = Path(result['python_environment']['root'])
        self.assertEqual(tree_hashes(target), environment['files'])
        self.assertEqual(tree_hashes(dependencies), environment['files'])

    def test_changed_reference_input_and_unpinned_exe_cannot_publish_manifest(self):
        for mode in ('reference', 'input', 'unpinned'):
            with self.subTest(mode=mode):
                if mode == 'reference':
                    path = Path(self.refs['stable']['root']) / 'file1.bin'
                else:
                    path = self.root / 'a.net'
                original = path.read_bytes()
                if mode != 'unpinned': path.write_bytes(b'changed')
                try:
                    with patch.object(freeze_async_product, 'FROZEN_EXPERIMENT_SHA',
                                      '0' * 64 if mode == 'unpinned' else self.refs['experiment']['files']['pt-renew.exe']):
                        destination = self.root / mode
                        with self.assertRaises(ValueError):
                            freeze_async_product.freeze(destination, references=self.refs, inputs=self.inputs)
                        self.assertFalse((destination / 'frozen-manifest.json').exists())
                finally:
                    path.write_bytes(original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
