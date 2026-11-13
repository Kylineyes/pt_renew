"""真实PowerShell只读有界等待的无GUI文件夹具；不启动原软件或控制服务。"""
import json
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
SCRIPT=REPO/'tools/Wait-LegacyFileStep.ps1'
BINDING={'task':'task_fixture','dispatch':'ctx_fixture','session':'fixture-session'}
OLD='1'*32
NEW='2'*32

class LegacyFileWaitTests(unittest.TestCase):
    def setUp(self):
        root=REPO/'.local-analysis/legacy-file-step-tests'
        root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='wait-',dir=root)
        self.addCleanup(self.temp.cleanup)
        self.slot=Path(self.temp.name)/'slot'
        (self.slot/'submit-queue').mkdir(parents=True)
        self.packet={**BINDING,'previous':'step-005-old-post','nonce':OLD,
                     'request':{'name':'one-key','tool':'Shortcut','purpose':'navigate_down','arguments':{'shortcut':'down'}}}
        self.state={**BINDING,'step':'step-006-one-key-post','nonce':NEW,'host':[{'path':str(self.slot/'step-006-one-key-post-00.png')}],
                    'guest':[],'needs_guest':True,'menu_open':False,'rounds_completed':1}
        self.put('submit-queue/packet-one-key.json',self.packet)

    def put(self,name,value):
        (self.slot/name).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')

    def complete(self,state=None,submitted=True):
        state=self.state if state is None else state
        self.put('current-state.json',state)
        self.put('step-006-one-key-post-observation.json',state)
        self.put('step-006-one-key-complete.json',{'completed':True})
        (self.slot/'submit-queue/packet-one-key.json').rename(self.slot/'submit-queue/packet-one-key.submitted')
        self.put('submit-queue/packet-one-key.result',{'packet':'packet-one-key.json','submitted':submitted,'error':'合成拒绝' if not submitted else None})

    def run_wait(self,timeout=2000):
        binary=shutil.which('powershell.exe') or shutil.which('powershell')
        self.assertIsNotNone(binary,'本组必须执行本机真实PowerShell，不能假通过或skip')
        process=subprocess.run([binary,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(SCRIPT),
            '-Slot',str(self.slot),'-Task',BINDING['task'],'-Dispatch',BINDING['dispatch'],'-Session',BINDING['session'],
            '-Previous','step-005-old-post','-Nonce',OLD,'-Name','one-key','-TimeoutMs',str(timeout)],
            capture_output=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertFalse(process.stderr,process.stderr.decode('utf-8',errors='replace'))
        result=json.loads(process.stdout.decode('utf-8-sig'))
        return process.returncode,result

    def test_ready_and_readonly(self):
        self.complete()
        before={p.relative_to(self.slot).as_posix():p.read_bytes() for p in self.slot.rglob('*') if p.is_file()}
        rc,result=self.run_wait()
        self.assertEqual((rc,result['status']),(0,'ready'))
        self.assertEqual(result['state'],self.state)
        self.assertEqual(before,{p.relative_to(self.slot).as_posix():p.read_bytes() for p in self.slot.rglob('*') if p.is_file()})

    def test_delayed_completion_uses_original_packet(self):
        def finish():
            time.sleep(1)
            self.complete()
        worker=threading.Thread(target=finish)
        worker.start()
        try:
            rc,result=self.run_wait(5000)
        finally:
            worker.join()
        self.assertEqual((rc,result['status']),(0,'ready'))
        self.assertGreaterEqual(result['elapsed_ms'],250)
        self.assertEqual(len(list((self.slot/'submit-queue').glob('*.submitted'))),1)
        self.assertFalse(list((self.slot/'submit-queue').glob('*.json')))

    def test_timeout_pending_without_state_read_or_rewrite(self):
        original=(self.slot/'submit-queue/packet-one-key.json').read_bytes()
        rc,result=self.run_wait(300)
        self.assertEqual((rc,result['status']),(0,'pending'))
        self.assertGreaterEqual(result['elapsed_ms'],300)
        self.assertLess(result['elapsed_ms'],1500)
        self.assertNotIn('state',result)
        self.assertEqual(original,(self.slot/'submit-queue/packet-one-key.json').read_bytes())

    def test_owner_refusal(self):
        self.complete(submitted=False)
        rc,result=self.run_wait()
        self.assertEqual((rc,result['status']),(3,'refused'))
        self.assertNotIn('state',result)

    def test_old_state_after_complete_is_error(self):
        self.complete({**self.state,'step':'step-005-old-post','nonce':OLD})
        rc,result=self.run_wait()
        self.assertEqual((rc,result['status']),(2,'error'))
        self.assertIn('旧步骤',result['reason'])

    def test_packet_wrong_identity(self):
        self.put('submit-queue/packet-one-key.json',{**self.packet,'session':'other-session'})
        rc,result=self.run_wait()
        self.assertEqual((rc,result['status']),(2,'error'))
        self.assertIn('身份',result['reason'])

    def test_new_state_wrong_identity(self):
        self.complete({**self.state,'task':'task_other'})
        rc,result=self.run_wait()
        self.assertEqual((rc,result['status']),(2,'error'))
        self.assertIn('身份',result['reason'])

    def test_wrong_nonce_original_packet(self):
        self.put('submit-queue/packet-one-key.json',{**self.packet,'nonce':'3'*32})
        rc,result=self.run_wait()
        self.assertEqual((rc,result['status']),(2,'error'))
        self.assertIn('不是当前请求',result['reason'])

    def test_driver_stopped_refuses_before_new_state(self):
        self.put('stopped-error.json',{'at':'合成停止'})
        rc,result=self.run_wait()
        self.assertEqual((rc,result['status']),(3,'refused'))
        self.assertNotIn('state',result)

    def test_duplicate_packet_versions_are_error(self):
        self.put('submit-queue/packet-one-key.submitted',self.packet)
        rc,result=self.run_wait()
        self.assertEqual((rc,result['status']),(2,'error'))
        self.assertIn('多个版本',result['reason'])

if __name__=='__main__':
    unittest.main()
