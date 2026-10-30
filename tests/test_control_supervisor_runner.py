"""本机连续启动器的无GUI进程链、原生持柄与失败保真测试。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_process_supervisor import ProcessApi

TOOLS=Path(__file__).resolve().parents[1]/'tools'


class RunnerTests(unittest.TestCase):
    def prepare(self,root, *, client_code=None):
        names=('control_process_supervisor.py','control_witness_launch.py','control_supervisor_runner.py')
        for name in names:shutil.copyfile(TOOLS/name,root/name)
        if client_code is None:
            client_code="""import subprocess,sys,time
p=subprocess.Popen([sys.executable,'-I','-S','-c','import time;time.sleep(.3)'])
p.wait();time.sleep(.2)
"""
        (root/'client.py').write_text(client_code,encoding='utf-8')
        plan=dict(schema_version=1,purpose='control-client-witness',task_id='task_离线runner',dispatch_id='ctx_离线runner',
            diagnostic_seconds=600,total_seconds=900,scan_interval_seconds=.05,
            client_interpreter=str(Path(sys.executable).resolve()),
            client_files={'client.py':hashlib.sha256((root/'client.py').read_bytes()).hexdigest()},
            supervisor_files={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names})
        plan_path=root/'supervisor-plan.json';plan_path.write_text(json.dumps(plan),encoding='utf-8')
        approval=dict(task_id=plan['task_id'],dispatch_id=plan['dispatch_id'],permission_confirmed=True,
            permission='仅无GUI命令行测试',message_id='假批准',diagnostic_seconds=600,total_seconds=900,
            supervisor_plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest())
        for name in ('server-approval.json','phase-two-approval.json'):
            (root/name).write_text(json.dumps(approval),encoding='utf-8')
        spec=importlib.util.spec_from_file_location('frozen_local_runner',root/'control_supervisor_runner.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_real_supervisor_handshake_hold_release_and_exit_are_continuous(self):
        with tempfile.TemporaryDirectory(prefix='pt-local-runner-') as directory:
            root=Path(directory);module=self.prepare(root)
            result=module.run(root)
            self.assertTrue(result['verified'])
            held=json.loads((root/'runner-held.json').read_text())
            own=json.loads((root/'supervisor-identity.json').read_text())
            self.assertEqual(held['pid'],own['pid'])
            self.assertEqual(held['birth'],own['birth'])
            self.assertEqual(result['supervisor_exit_code'],0)
            self.assertGreaterEqual(len(result['processes']),2)
            self.assertTrue(all(p['exit_code']==0 for p in result['processes']))
            witness=Path(held['witness_directory'])
            released=json.loads((witness/'release.json').read_text())
            self.assertEqual(released['pid'],held['pid'])
            self.assertLess(held['held'],held['identity']['release_deadline'])
            self.assertFalse((root/'outer-driver-release.json').exists())
            self.assertFalse((root/'runner-error.json').exists())
            with self.assertRaisesRegex(RuntimeError,'已有启动器原件'):module.run(root)
            self.assertEqual(len(list(root.glob('witness-*'))),1)

    def test_missing_or_changed_approval_rejects_before_any_supervisor_is_created(self):
        for kind in ('unconfirmed','changed-script','wrong-task','missing-runner'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory(prefix='pt-runner-refuse-') as directory:
                root=Path(directory);module=self.prepare(root)
                if kind=='changed-script':(root/'client.py').write_text('变化',encoding='utf-8')
                elif kind=='missing-runner':
                    path=root/'supervisor-plan.json';row=json.loads(path.read_text());del row['supervisor_files']['control_supervisor_runner.py'];path.write_text(json.dumps(row))
                else:
                    path=root/'server-approval.json';row=json.loads(path.read_text())
                    row['permission_confirmed' if kind=='unconfirmed' else 'task_id']=False if kind=='unconfirmed' else '另一个任务'
                    path.write_text(json.dumps(row))
                with self.assertRaises(RuntimeError):module.run(root)
                self.assertFalse((root/'runner-start.json').exists())
                self.assertFalse(list(root.glob('witness-*')))

    def test_nonzero_client_code_preserves_exact_supervisor_failure_and_no_retry(self):
        with tempfile.TemporaryDirectory(prefix='pt-runner-nonzero-') as directory:
            root=Path(directory);module=self.prepare(root,client_code='import time;time.sleep(.3);raise SystemExit(7)')
            with self.assertRaisesRegex(RuntimeError,'含失败码'):module.run(root)
            error=json.loads((root/'runner-error.json').read_text())
            chain=json.loads((root/'supervisor-chain-exit.json').read_text())
            self.assertEqual(chain['client_popen_exit_code'],7)
            self.assertEqual(error['popen_result']['exit_code'],1)
            self.assertEqual(error['handle_exit_code'],1)
            self.assertEqual(error['restart_calls'],0)
            self.assertFalse((root/'runner-result.json').exists())
            self.assertEqual(len(list(root.glob('witness-*'))),1)

    def test_failure_to_hold_does_not_release_target_and_keeps_original_popen(self):
        with tempfile.TemporaryDirectory(prefix='pt-runner-hold-fail-') as directory:
            root=Path(directory);module=self.prepare(root)
            class Refuse:
                def hold(self,pid):raise OSError('定向持柄失败')
            # 真实子进程沿其原10秒未放行截止自行退出；不伪造release来加速。
            with self.assertRaisesRegex(OSError,'定向持柄失败'):module.run(root,api_factory=Refuse)
            error=json.loads((root/'runner-error.json').read_text())
            self.assertFalse(error['popen_result']['released'])
            self.assertNotEqual(error['popen_result']['exit_code'],0)
            self.assertFalse((root/'supervisor-identity.json').exists())
            witness=next(root.glob('witness-*'))
            self.assertFalse((witness/'release.json').exists())
            self.assertEqual(error['termination_calls'],0)

    def test_exit_identity_mismatch_keeps_original_exit_evidence_without_second_wait(self):
        with tempfile.TemporaryDirectory(prefix='pt-runner-audit-fail-') as directory:
            root=Path(directory);module=self.prepare(root)
            with patch.object(module,'audit_completion',side_effect=RuntimeError('实际身份不符')):
                with self.assertRaisesRegex(RuntimeError,'实际身份不符'):module.run(root)
            error=json.loads((root/'runner-error.json').read_text())
            self.assertEqual(error['popen_result']['exit_code'],0)
            self.assertEqual(error['handle_exit_code'],0)
            self.assertNotIn('wait_error',error)
            self.assertEqual(len(list(root.glob('witness-*/popen-exit.json'))),1)

    def test_completion_recomputes_process_list_instead_of_trusting_success_flags(self):
        with tempfile.TemporaryDirectory(prefix='pt-runner-proof-') as directory:
            root=Path(directory);module=self.prepare(root)
            (root/'supervisor-identity.json').write_text(json.dumps(dict(pid=123,birth=456,plan_sha256='方案')))
            chain=dict(supervisor_pid=123,supervisor_birth=456,verified=True,capture_errors=[],
                       all_exited=True,all_exit0=True,client_popen_exit_code=0,processes=[])
            for processes in ([],[dict(pid=789,birth=999,exit_code=7)],
                              [dict(pid=789,birth=999,exit_code=0)]*2):
                chain['processes']=processes
                (root/'supervisor-chain-exit.json').write_text(json.dumps(chain))
                with self.subTest(processes=processes),self.assertRaisesRegex(RuntimeError,'子孙退出记录'):
                    module.audit_completion(root,dict(pid=123,birth=456),
                        dict(pid=123,actual_pid=123,exit_code=0),0,'方案')

    def test_cli_works_from_venv_and_records_result_without_external_agent_gate(self):
        with tempfile.TemporaryDirectory(prefix='pt-runner-cli-') as directory:
            root=Path(directory);self.prepare(root)
            proc=subprocess.run([sys.executable,'-X','utf8',str(root/'control_supervisor_runner.py'),'--root',str(root)],
                capture_output=True,text=True,encoding='utf-8',timeout=15)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertTrue(json.loads(proc.stdout)['verified'])
            result=json.loads((root/'runner-result.json').read_text())
            self.assertEqual(result['supervisor_exit_code'],0)


if __name__=='__main__':unittest.main(verbosity=2)
