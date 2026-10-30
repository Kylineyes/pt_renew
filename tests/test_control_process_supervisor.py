"""监督器的假进程账本与真实无GUI进程链测试，不导入桌面或MCP。"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_process_supervisor import ChainWitness,SnapshotJournal,validate_plan
import control_process_supervisor as supervisor
from unittest.mock import Mock, patch
from control_witness_launch import WitnessLaunch


class FakeProcessApi:
    def __init__(self):
        self.rows=[];self.births={1:100,2:200,3:300,9:50};self.exit={};self.closed=[];self.fail=set()
    def hold(self,pid,expected_birth=None):
        if pid in self.fail:raise OSError('进程查询失败')
        birth=self.births[pid]
        if expected_birth is not None and birth!=expected_birth:raise RuntimeError('身份变化')
        return (pid,birth),birth
    def poll(self,handle):return self.exit.get(handle)
    def close(self,handle):self.closed.append(handle)
    def processes(self):return self.rows


class SupervisorTests(unittest.TestCase):
    def test_snapshot_write_retries_only_permission_errors_and_latches_exhaustion(self):
        pauses=[]
        writer=Mock(side_effect=[PermissionError('暂不可替换'),None])
        journal=SnapshotJournal(writer,pauses.append)
        self.assertTrue(journal.write(Path('快照.json'),{}))
        self.assertEqual((writer.call_count,journal.retry_count,journal.failure_count),(2,1,0))
        self.assertEqual(pauses,[.01])
        writer=Mock(side_effect=PermissionError('持续不可替换'))
        journal=SnapshotJournal(writer,pauses.append)
        self.assertFalse(journal.write(Path('快照.json'),{}))
        self.assertEqual((writer.call_count,journal.retry_count,journal.failure_count),(3,2,1))
        self.assertIn('PermissionError',journal.errors[0]['reason'])
        journal.writer=Mock()
        self.assertTrue(journal.write(Path('快照.json'),{}))
        self.assertEqual(journal.failure_count,1)
        journal.writer=Mock(side_effect=OSError('磁盘写入失败'))
        for _ in range(70):self.assertFalse(journal.write(Path('快照.json'),{}))
        self.assertEqual(journal.failure_count,71)
        self.assertEqual(len(journal.errors),64)
        self.assertEqual(journal.writer.call_count,70)

    def test_snapshot_failure_keeps_original_client_until_normal_exit_and_reports_failure(self):
        with tempfile.TemporaryDirectory(prefix='pt-supervisor-snapshot-') as directory:
            root=Path(directory)
            (root/'client.py').write_text("import time\nfrom pathlib import Path\ntime.sleep(.3)\nPath('正常退出前标记').write_text('已完成')\n",encoding='utf-8')
            plan=root/'supervisor-plan.json';plan.write_text(json.dumps(dict(scan_interval_seconds=.05)),encoding='utf-8')
            real_save=supervisor.save
            writes=[]
            def failing_snapshot(path,row):
                if path.name=='supervisor-chain-held.json':
                    writes.append(row)
                    raise PermissionError('注入持续快照拒绝')
                return real_save(path,row)
            with patch.object(supervisor,'validate_plan',return_value=Path(sys.executable).resolve()),patch.object(supervisor,'save',side_effect=failing_snapshot):
                code=supervisor.main(plan)
            self.assertEqual(code,1)
            self.assertTrue((root/'正常退出前标记').is_file())
            self.assertFalse((root/'supervisor-fatal.json').exists())
            report=json.loads((root/'supervisor-chain-exit.json').read_text(encoding='utf-8'))
            self.assertEqual(report['client_popen_exit_code'],0)
            self.assertTrue(report['all_exited'] and report['all_exit0'])
            self.assertFalse(report['verified'])
            self.assertGreater(report['snapshot_failure_count'],0)
            self.assertEqual(len(writes),report['snapshot_failure_count']*3)
            self.assertEqual(report['snapshot_retry_count'],report['snapshot_failure_count']*2)
            self.assertTrue(all(p['exit_code']==0 for p in report['processes']))

    def test_descendants_reconstructed_out_of_order_and_nonzero_exit_kept(self):
        api=FakeProcessApi();chain=ChainWitness(api);chain.hold(1)
        api.rows=[dict(pid=3,parent=2),dict(pid=2,parent=1),dict(pid=9,parent=0)]
        chain.scan();self.assertEqual(len(chain.entries),3)
        api.exit={(1,100):0,(2,200):7,(3,300):0}
        chain.scan();row=chain.report()
        self.assertTrue(row['all_exited']);self.assertFalse(row['all_exit0']);self.assertFalse(row['verified'])
        self.assertEqual(next(p for p in row['processes'] if p['pid']==2)['exit_code'],7)
        chain.close();self.assertEqual(len(api.closed),3)

    def test_pid_reuse_and_query_failure_cannot_be_silently_skipped(self):
        for pid in (9,2):
            api=FakeProcessApi();chain=ChainWitness(api);chain.hold(1)
            api.rows=[dict(pid=pid,parent=1)]
            if pid==2:api.fail.add(2)
            chain.scan();self.assertTrue(chain.report()['capture_errors'])
            api.exit[(1,100)]=0;chain.scan()
            self.assertFalse(chain.report()['verified'])
            chain.close()

    def test_exited_parent_cannot_claim_unrelated_child_by_reused_pid(self):
        api=FakeProcessApi();chain=ChainWitness(api);chain.hold(1)
        api.exit[(1,100)]=0;api.rows=[dict(pid=2,parent=1)]
        chain.scan();self.assertEqual(len(chain.entries),1)
        self.assertTrue(chain.report()['all_exit0'])
        self.assertIn('不能排除',chain.report()['limitation'])
        chain.close()

    def plan(self,root):
        path=root/'client.py';path.write_text('客户端占位',encoding='utf-8')
        from shutil import copyfile
        supervisor_files={}
        for name in ('control_process_supervisor.py','control_witness_launch.py'):
            copyfile(Path(__file__).resolve().parents[1]/'tools'/name,root/name)
            supervisor_files[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
        plan=dict(schema_version=1,purpose='control-client-witness',task_id='task_新的离线测试',
                  dispatch_id='ctx_新的离线测试',diagnostic_seconds=600,total_seconds=900,scan_interval_seconds=.05,
                  client_interpreter=str(Path(sys.executable).resolve()),
                  client_files={'client.py':hashlib.sha256(path.read_bytes()).hexdigest()},
                  supervisor_files=supervisor_files,_source_sha256='假方案摘要')
        # 真实main运行于基础Python；此定向调用注入不同exe来核对独立环境条件。
        approval=dict(permission_confirmed=True,permission='无GUI测试字段',message_id='假批准',
                      diagnostic_seconds=600,total_seconds=900,
                      task_id=plan['task_id'],dispatch_id=plan['dispatch_id'],supervisor_plan_sha256='假方案摘要')
        for name in ('server-approval.json','phase-two-approval.json'):
            (root/name).write_text(json.dumps(approval),encoding='utf-8')
        return plan

    def test_missing_approval_changed_script_old_state_and_wrong_interpreter_rejected(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='pt-supervisor-plan-') as directory:
            root=Path(directory);plan=self.plan(root)
            with self.assertRaisesRegex(RuntimeError,'独立MCP环境'):validate_plan(plan,root)
            with patch('control_process_supervisor.sys.executable',str(root/'基础python.exe')):
                self.assertTrue(validate_plan(plan,root).is_file())
                for field,value in (('total_seconds',1800),('task_id','其他任务'),('_source_sha256','错误摘要')):
                    bad=deepcopy(plan);bad[field]=value
                    with self.subTest(field=field),self.assertRaises(RuntimeError):validate_plan(bad,root)
                (root/'runtime-limits.json').write_text('{}')
                with self.assertRaisesRegex(RuntimeError,'禁止重启'):validate_plan(plan,root)
                (root/'runtime-limits.json').unlink()
                (root/'client.py').write_text('变化',encoding='utf-8')
                with self.assertRaisesRegex(RuntimeError,'冻结文件'):validate_plan(plan,root)

    def test_real_direct_supervisor_and_explicit_venv_child_chain_share_exact_exit_proof(self):
        with tempfile.TemporaryDirectory(prefix='pt-supervisor-live-cli-') as directory:
            root=Path(directory)
            source=Path(__file__).resolve().parents[1]/'tools/control_process_supervisor.py'
            shutil.copyfile(source,root/source.name)
            # 明确使用venv启动器产生一层真实重定向；客户端/孙进程均仅标准库，无GUI。
            text="""import json,os,subprocess,sys,time
from pathlib import Path
Path('runtime-limits.json').write_text(json.dumps(dict(started=time.monotonic(),diagnostic_deadline=time.monotonic()+600,cleanup_deadline=time.monotonic()+900)))
Path('fake-client-identity.json').write_text(json.dumps(dict(pid=os.getpid(),executable=sys.executable)))
p=subprocess.Popen([sys.executable,'-I','-S','-c','import time;time.sleep(.4)'])
p.wait();time.sleep(.2)
"""
            (root/'client.py').write_text(text,encoding='utf-8')
            witness_source=source.with_name('control_witness_launch.py')
            shutil.copyfile(witness_source,root/witness_source.name)
            supervisor_files={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                              for name in (source.name,witness_source.name)}
            plan=dict(schema_version=1,purpose='control-client-witness',task_id='task_命令行测试',dispatch_id='ctx_命令行测试',
                      diagnostic_seconds=600,total_seconds=900,scan_interval_seconds=.05,
                      client_interpreter=str(Path(sys.executable).resolve()),
                      client_files={'client.py':hashlib.sha256((root/'client.py').read_bytes()).hexdigest()},
                      supervisor_files=supervisor_files)
            plan_path=root/'supervisor-plan.json';plan_path.write_text(json.dumps(plan),encoding='utf-8')
            approval=dict(permission_confirmed=True,permission='只运行无GUI假客户端',message_id='假批准',
                          diagnostic_seconds=600,total_seconds=900,
                          task_id=plan['task_id'],dispatch_id=plan['dispatch_id'],
                          supervisor_plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest())
            for name in ('server-approval.json','phase-two-approval.json'):
                (root/name).write_text(json.dumps(approval),encoding='utf-8')
            launch=WitnessLaunch(root/source.name,root/'witness')
            self.assertFalse((root/'supervisor-identity.json').exists())
            launch.release();result=launch.wait(15)
            if result['exit_code']!=0:
                proof=(root/'supervisor-chain-exit.json').read_text(encoding='utf-8') if (root/'supervisor-chain-exit.json').exists() else '缺少退出账本'
                self.fail((launch.directory/'stderr.log').read_text(encoding='utf-8')+'\n'+proof)
            actual=json.loads((root/'supervisor-identity.json').read_text())
            chain=json.loads((root/'supervisor-chain-exit.json').read_text())
            client=json.loads((root/'fake-client-identity.json').read_text())
            self.assertEqual(actual['pid'],result['pid'])
            self.assertEqual(chain['supervisor_pid'],result['actual_pid'])
            self.assertEqual(actual['client_interpreter'],str(Path(sys.executable).resolve()))
            self.assertNotEqual(actual['interpreter'],actual['client_interpreter'])
            self.assertTrue(chain['verified'])
            self.assertFalse(chain['capture_errors'])
            self.assertGreaterEqual(len(chain['processes']),2)
            self.assertIn(client['pid'],[p['pid'] for p in chain['processes']])
            self.assertTrue(all(p['exit_code']==0 for p in chain['processes']))
            self.assertEqual(chain['termination_calls'],0)


if __name__=='__main__':unittest.main(verbosity=2)
