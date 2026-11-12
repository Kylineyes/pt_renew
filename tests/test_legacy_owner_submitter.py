"""owner文件线程合成回归；原submit运行，driver/Popen为假对象，无桌面。"""
import base64
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time
import types
import unittest
from unittest.mock import patch
import test_legacy_runtime_config as fixtures

owner = fixtures.owner
isolation = fixtures.isolation
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')


class OwnerSubmitterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.RuntimeIsolationTests()
        self.fixture.setUp()
        self.session = self.fixture.root/'synthetic-session.jsonl'
        self.session.write_text(json.dumps({'type':'session','id':'fake-session'})+'\n', encoding='utf-8')
        self.package, self.plan = self.fixture.generated(lambda **args: fixtures.navigation.prepare_navigation(
            file_submitter_session=str(self.session), **args))
        self.root = self.package/'slot'
        self.driver_done = threading.Event()
        self.driver = types.SimpleNamespace(poll=lambda:0 if self.driver_done.is_set() else None)
        self.workers = []
        self.approval()
        (self.root/'inbox').mkdir()
        spec=importlib.util.spec_from_file_location('synthetic_gate',self.package/'review_gate.py')
        self.gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.gate)
        self.png=self.root/'synthetic.png';self.png.write_bytes(PNG)
        self.state=self.gate.publish(self.root,self.plan,'synthetic-baseline',[{'path':str(self.png)}])
        self.review()
        with self.session.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps({'message':{'role':'toolResult','content':[{'type':'image','data':base64.b64encode(PNG).decode()}]}})+'\n')

    def tearDown(self):
        for worker in self.workers:
            if worker.started and worker.thread.is_alive():worker.stop()
        self.fixture.tearDown()

    def approval(self, *, expired=False, wrong=False):
        now=datetime.datetime.now(datetime.timezone.utc)
        fixtures.dump(self.root/'go-start.json',{**{k:self.plan[k] for k in ('session','task','dispatch')},
            'session':'wrong' if wrong else self.plan['session'],
            'approved_plan_sha256':fixtures.digest(self.root/'live-plan.json'),
            'start_utc':(now-datetime.timedelta(minutes=20 if expired else 1)).isoformat(),
            'deadline_utc':(now+datetime.timedelta(minutes=-1 if expired else 30)).isoformat()})

    def review(self):
        s=self.state
        fixtures.dump(self.root/(s['step']+'-host-read-review.json'),{
            **{k:self.plan[k] for k in ('session','task','dispatch')},'step':s['step'],'nonce':s['nonce'],
            'model':'deng/gpt-6.1-sol','thinking':'high','images':s['host'],'observation':'合成原图，只验证协议'})

    def worker(self):
        worker=owner.FileSubmitter(self.root,self.plan,self.driver)
        self.workers.append(worker)
        return worker

    def packet(self, name='launch-owned', tool='Launch', **extra):
        s=self.state
        packet={**{k:self.plan[k] for k in ('session','task','dispatch')},'previous':s['step'],'nonce':s['nonce'],
            'request':{'name':name,'tool':tool,**extra}}
        path=self.root/'submit-queue'/('packet-'+name+'.json')
        fixtures.dump(path,packet)
        return path

    def test_real_frozen_submit_and_gate_accept_unique_packet(self):
        worker=self.worker();path=self.packet()
        with patch.object(owner.subprocess,'Popen') as spawn:
            hashes=worker.submit(path)
            spawn.assert_not_called()
        self.assertEqual(hashes,[hashlib.sha256(PNG).hexdigest()])
        self.assertEqual(json.loads((self.root/'inbox/request-launch-owned.json').read_text(encoding='utf-8')),
                         json.loads(path.read_text(encoding='utf-8')))
        with self.assertRaises(RuntimeError):worker.submit(path)

    def test_bad_tool_nonce_and_missing_image_receipt_do_not_publish(self):
        worker=self.worker()
        bad=self.packet('bad-focus','FocusOwned')
        with self.assertRaisesRegex(RuntimeError,'其它业务'):worker.submit(bad)
        bad.unlink()
        path=self.packet();packet=json.loads(path.read_text(encoding='utf-8'));packet['nonce']='stale';fixtures.dump(path,packet)
        with self.assertRaisesRegex(RuntimeError,'当前步骤'):worker.submit(path)
        self.session.write_text(json.dumps({'type':'session','id':'fake-session'})+'\n',encoding='utf-8')
        worker.receipts.clear();worker.session_offset=0
        with self.assertRaisesRegex(RuntimeError,'SHA缺失'):worker.submit(path)
        self.assertEqual(list((self.root/'inbox').iterdir()),[])

    def test_driver_exit_stop_and_deadline_prevent_new_requests(self):
        worker=self.worker();path=self.packet()
        self.driver_done.set()
        with self.assertRaisesRegex(RuntimeError,'driver已退出'):worker.submit(path)
        self.driver_done.clear();worker.stop_event.set()
        with self.assertRaisesRegex(RuntimeError,'已停止'):worker.submit(path)
        worker.stop_event.clear();self.approval(expired=True)
        with self.assertRaisesRegex(RuntimeError,'时段'):worker.submit(path)
        self.assertEqual(list((self.root/'inbox').iterdir()),[])

    def test_expensive_image_check_crossing_business_deadline_rejected(self):
        worker=self.worker();path=self.packet()
        now=datetime.datetime.now(datetime.timezone.utc).timestamp()
        with patch.object(owner,'approval_window',return_value=now+421), \
             patch.object(owner.time,'time',side_effect=[now,now+2]):
            with self.assertRaisesRegex(RuntimeError,'预检耗时'):worker.submit(path)
        self.assertEqual(list((self.root/'inbox').iterdir()),[])

    def test_link_and_hardlink_packets_rejected_without_external_write(self):
        worker=self.worker();outside=self.fixture.root/'external.json';outside.write_text('{}',encoding='utf-8')
        path=worker.queue/'packet-shared.json';os.link(outside,path)
        with self.assertRaises(ValueError):worker.submit(path)
        self.assertEqual(outside.read_text(encoding='utf-8'),'{}');path.unlink()
        worker.queue.rmdir();fixtures.junction(worker.queue,self.fixture.root/'original')
        try:
            with self.assertRaises(ValueError):worker.submit(worker.queue/'packet.json')
        finally:fixtures.remove_alias(worker.queue)

    def test_refusal_keeps_visible_error_then_original_lifecycle_channel(self):
        worker=self.worker();path=self.packet('bad-focus','FocusOwned')
        worker.start()
        # 只等本测试线程的完成事件；不等待真实现场或用sleep推进120秒。
        limit=time.monotonic()+3
        while not path.with_suffix('.result').exists() and time.monotonic()<limit:
            threading.Event().wait(.01)
        worker.stop()
        result=json.loads(path.with_suffix('.result').read_text(encoding='utf-8'))
        self.assertFalse(result['submitted']);self.assertIn('其它业务',result['error'])
        self.assertTrue((self.root/'stop-business.json').exists())
        self.assertTrue(json.loads((self.root/'submit-thread-exit.json').read_text(encoding='utf-8'))['joined'])
        self.assertEqual(list((self.root/'inbox').iterdir()),[])
        # 用假时钟使拒绝静默已满；不重启线程，仅检验同一原submit生命周期。
        worker.stop_event.clear();worker.quiet_until=0
        path=self.packet('wait-original','WaitExit')
        worker.submit(path)
        self.assertTrue((self.root/'inbox/request-wait-original.json').exists())
        (self.root/'inbox/request-wait-original.json').unlink()
        path=self.packet('attempt-business')
        with self.assertRaisesRegex(RuntimeError,'禁止恢复业务'):worker.submit(path)

    def test_multiple_packets_rejected_and_joined(self):
        worker=self.worker();self.packet('first');self.packet('second')
        worker.start()
        limit=time.monotonic()+3
        while len(list(worker.queue.glob('*.result')))<2 and time.monotonic()<limit:
            threading.Event().wait(.01)
        worker.stop()
        self.assertEqual(len(list(worker.queue.glob('*.rejected'))),2)
        self.assertEqual(list((self.root/'inbox').iterdir()),[])

    def test_owner_invalid_expired_and_wrong_identity_zero_driver_and_thread(self):
        for variant in ('expired','identity','invalid'):
            self.approval(expired=variant=='expired',wrong=variant=='identity')
            if variant=='invalid':
                changed=json.loads((self.root/'live-plan.json').read_text(encoding='utf-8'))
                changed['target']['cwd']=str(self.fixture.root/'outside');fixtures.dump(self.root/'live-plan.json',changed)
            before=set(self.root.iterdir())
            with patch.object(sys,'argv',['owner',str(self.root)]), \
                 patch.object(owner.subprocess,'Popen') as spawn,patch.object(owner,'FileSubmitter') as factory:
                with self.assertRaises((RuntimeError,ValueError)):owner.main()
                spawn.assert_not_called();factory.assert_not_called()
            self.assertEqual(set(self.root.iterdir()),before)

    def test_owner_actual_main_wait_then_stop_join_without_helper_process(self):
        started=threading.Event();real_save=owner.FileSubmitter.save
        def save(worker,path,value):
            real_save(worker,path,value)
            if path.name=='submit-thread-started.json':started.set()
        def wait():
            self.assertTrue(started.wait(3));self.driver_done.set();return 0
        self.driver.wait=wait
        with patch.object(sys,'argv',['owner',str(self.root)]),patch.object(owner.FileSubmitter,'save',save), \
             patch.object(owner.subprocess,'CREATE_NO_WINDOW',0,create=True), \
             patch.object(owner.subprocess,'Popen',return_value=self.driver) as spawn, \
             patch.object(owner,'identity',return_value={'pid':-1,'original_handle':-2}):
            self.assertEqual(owner.main(),0)
            spawn.assert_called_once()
        self.assertTrue(json.loads((self.root/'submit-thread-exit.json').read_text(encoding='utf-8'))['joined'])
        self.assertEqual(json.loads((self.root/'driver-exit.json').read_text(encoding='utf-8'))['wait_return'],0)

    def test_late_join_evidence_failure_still_joins(self):
        worker=self.worker();worker.started=True
        joined=[]
        worker.thread=types.SimpleNamespace(join=lambda timeout=None:joined.append(timeout),is_alive=unittest.mock.Mock(side_effect=[True]))
        real_save=worker.save
        def save(path,value):
            if path.name=='submit-thread-late-join.json':raise OSError('合成超时证据失败')
            real_save(path,value)
        with patch.object(worker,'save',side_effect=save):
            with self.assertRaises(OSError):worker.stop()
        self.assertEqual(joined,[5,None])
        worker.started=False

    def test_owner_internal_thread_failure_not_reported_as_success(self):
        self.driver.wait=unittest.mock.Mock(return_value=0)
        failed=types.SimpleNamespace(start=lambda:None,stop=unittest.mock.Mock(),error='合成内部异常')
        with patch.object(sys,'argv',['owner',str(self.root)]),patch.object(owner.subprocess,'CREATE_NO_WINDOW',0,create=True), \
             patch.object(owner.subprocess,'Popen',return_value=self.driver),patch.object(owner,'identity',return_value={'pid':-1}), \
             patch.object(owner,'FileSubmitter',return_value=failed):
            with self.assertRaisesRegex(RuntimeError,'文件投递线程失败'):owner.main()
        self.driver.wait.assert_called_once();failed.stop.assert_called_once()
        self.assertEqual(json.loads((self.root/'driver-exit.json').read_text(encoding='utf-8'))['wait_return'],0)

    def test_stopped_or_exited_thread_does_not_publish_pending_packet(self):
        worker=self.worker();path=self.packet()
        self.driver_done.set()
        worker.start();worker.thread.join(timeout=3);worker.stop()
        self.assertTrue(path.exists())
        self.assertEqual(list((self.root/'inbox').iterdir()),[])
        with self.assertRaisesRegex(RuntimeError,'已退出|已停止'):worker.submit(path)

    def test_real_file_feature_invalid_semantics_stops_before_any_creation(self):
        if os.name!='nt':self.skipTest('需要现有Windows PowerShell')
        # 读取真实新计划及新字段；坏queue在任何owner/driver或投递线程之前拒绝。
        changed=json.loads((self.root/'live-plan.json').read_text(encoding='utf-8'))
        changed['file_submitter']['queue']=str(self.fixture.root/'external-queue')
        fixtures.dump(self.root/'live-plan.json',changed);self.approval()
        before=set(self.root.iterdir())
        for detach in (False,True):
            argv=['powershell.exe','-NoProfile','-File',str(fixtures.REPO/'tools/Start-LegacyObservationOwner.ps1'),'-Slot',str(self.root)]
            if detach:argv.append('-Detach')
            run=fixtures.subprocess.run(argv,capture_output=True,timeout=15)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(set(self.root.iterdir()),before)
        self.assertFalse((self.fixture.root/'external-queue').exists())

    def test_session_incremental_partial_line_and_truncation(self):
        worker=self.worker();path=self.packet()
        with self.session.open('ab') as stream:stream.write(b'{"message":')
        worker.submit(path)
        offset=worker.session_offset
        self.assertLess(offset,self.session.stat().st_size)
        self.session.write_text('{}\n',encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError,'被截断'):worker.require_images(json.loads(path.read_text(encoding='utf-8')))

    def test_feature_queue_source_and_frozen_owner_rejected(self):
        import copy
        for mutate in (
            lambda p:p['file_submitter'].update(queue=str(self.fixture.root/'outside')),
            lambda p:p['file_submitter'].update(version=2),
            lambda p:p['file_submitter'].update(session_file=str(self.png)),
            lambda p:p.update(frozen_files=[f for f in p['frozen_files'] if not f['path'].endswith('legacy_observation_owner.py')])):
            value=copy.deepcopy(self.plan);mutate(value)
            with self.assertRaises((RuntimeError,ValueError)):isolation.validate_runtime_plan(value)
        self.session.write_text(json.dumps({'type':'session','id':'wrong'})+'\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'会话身份'):isolation.validate_runtime_plan(self.plan)
        self.assertFalse((self.root/'submit-queue').exists())

    def test_thread_internal_failure_visible_and_joined(self):
        worker=self.worker();save=worker.save
        def fail_once(path,value):
            if path.name=='submit-thread-started.json':raise OSError('合成线程日志失败')
            return save(path,value)
        with patch.object(worker,'save',side_effect=fail_once):
            worker.start();worker.thread.join(timeout=3);worker.stop()
        self.assertIn('合成线程日志失败',worker.error)
        self.assertTrue((self.root/'submit-thread-error.json').exists())
        self.assertTrue((self.root/'stop-business.json').exists())
        self.assertTrue(json.loads((self.root/'submit-thread-exit.json').read_text(encoding='utf-8'))['joined'])

    def test_owner_driver_created_save_failure_and_wait_interruption_still_wait(self):
        self.driver.wait=unittest.mock.Mock(return_value=0)
        fixtures.dump(self.root/'driver-created.json',{'preserved':'不可覆盖'})
        with patch.object(sys,'argv',['owner',str(self.root)]),patch.object(owner.subprocess,'CREATE_NO_WINDOW',0,create=True), \
             patch.object(owner.subprocess,'Popen',return_value=self.driver),patch.object(owner,'identity',return_value={'pid':-1}):
            with self.assertRaises(FileExistsError):owner.main()
        self.driver.wait.assert_called_once()
        self.assertFalse((self.root/'submit-queue').exists())
        for name in ('driver-created.json','driver-exit.json','driver-stdout.bin','driver-stderr.bin'):(self.root/name).unlink()
        self.driver.wait=unittest.mock.Mock(side_effect=[InterruptedError('合成wait中断'),0])
        with patch.object(sys,'argv',['owner',str(self.root)]),patch.object(owner.subprocess,'CREATE_NO_WINDOW',0,create=True), \
             patch.object(owner.subprocess,'Popen',return_value=self.driver),patch.object(owner,'identity',return_value={'pid':-1}):
            with self.assertRaises(InterruptedError):owner.main()
        self.assertEqual(self.driver.wait.call_count,2)
        self.assertTrue(json.loads((self.root/'submit-thread-exit.json').read_text(encoding='utf-8'))['joined'])
        self.assertEqual(json.loads((self.root/'driver-exit.json').read_text(encoding='utf-8'))['wait_return'],0)

    def test_identity_and_thread_start_errors_still_wait_original_driver(self):
        self.driver.wait=unittest.mock.Mock(return_value=0)
        with patch.object(sys,'argv',['owner',str(self.root)]),patch.object(owner.subprocess,'CREATE_NO_WINDOW',0,create=True), \
             patch.object(owner.subprocess,'Popen',return_value=self.driver),patch.object(owner,'identity',side_effect=ValueError('合成身份失败')):
            with self.assertRaises(ValueError):owner.main()
        self.driver.wait.assert_called_once()
        self.assertFalse((self.root/'submit-queue').exists())
        for name in ('driver-exit.json','driver-stdout.bin','driver-stderr.bin'):(self.root/name).unlink()
        self.driver.wait.reset_mock()
        with patch.object(sys,'argv',['owner',str(self.root)]),patch.object(owner.subprocess,'CREATE_NO_WINDOW',0,create=True), \
             patch.object(owner.subprocess,'Popen',return_value=self.driver),patch.object(owner,'identity',return_value={'pid':-1}), \
             patch.object(owner.threading.Thread,'start',side_effect=RuntimeError('合成启动失败')):
            with self.assertRaisesRegex(RuntimeError,'合成启动失败'):owner.main()
        self.driver.wait.assert_called_once()


if __name__=='__main__':unittest.main()
