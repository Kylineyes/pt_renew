"""Windows PowerShell 5.1 真实 -File 离线加载；在任何现场进程创建前退出。"""
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(sys.platform == 'win32' and shutil.which('powershell.exe'), '需要现有 Windows PowerShell')
class OwnerFileLoadingTests(unittest.TestCase):
    def test_real_file_preflight_rejects_early_and_expired_before_any_creation(self):
        script = Path(__file__).resolve().parents[1] / 'tools/Start-LegacyObservationOwner.ps1'
        with tempfile.TemporaryDirectory(prefix='pt-renew-time-guard-') as directory:
            root=Path(directory)
            plan={'slot':str(root),'session':'fake-session','task':'fake-task','dispatch':'fake-dispatch'}
            data=json.dumps(plan).encode('utf-8')
            (root/'live-plan.json').write_bytes(data)
            now=datetime.datetime.now(datetime.timezone.utc)
            for phase,start,end,expected in (
                ('early',now+datetime.timedelta(minutes=5),now+datetime.timedelta(minutes=55),1),
                ('business-expired',now-datetime.timedelta(minutes=50),now+datetime.timedelta(minutes=6),1),
                ('legal',now-datetime.timedelta(minutes=1),now+datetime.timedelta(minutes=40),0)):
                approval={**{k:plan[k] for k in ('session','task','dispatch')},'approved_plan_sha256':hashlib.sha256(data).hexdigest(),
                    'start_utc':start.isoformat(),'deadline_utc':end.isoformat()}
                (root/'go-start.json').write_text(json.dumps(approval),encoding='utf-8')
                for detach in (False,True):
                    with self.subTest(phase=phase,detach=detach):
                        argv=['powershell.exe','-NoProfile','-File',str(script),'-Slot',str(root),'-PreflightOnly']
                        if detach:argv.append('-Detach')
                        run=subprocess.run(argv,capture_output=True,timeout=15)
                        self.assertEqual(run.returncode,expected,run.stderr.decode('utf-8',errors='replace'))
                        if expected==0:
                            result=json.loads(run.stdout.decode('utf-8-sig'))
                            self.assertTrue(result['before_any_process_creation'])
                        self.assertEqual(sorted(p.name for p in root.iterdir()),['go-start.json','live-plan.json'])

    def test_semantic_precheck_elapsed_rechecks_both_creation_boundaries(self):
        script=Path(__file__).resolve().parents[1]/'tools/Start-LegacyObservationOwner.ps1'
        source=script.read_text(encoding='utf-8-sig')
        guard_function=source[source.index('function Assert-LegacyObservationStart {'):source.index('$taskSlot = [IO.Path]::GetFullPath($Slot)')]
        guard_line=next(line.strip() for line in source.splitlines() if line.startswith('Assert-LegacyObservationStart -Plan'))
        detach=source[source.index('if ($Detach) {'):source.index('$taskRepository =')]
        self.assertLess(detach.index('& $taskPlan.base_python'),detach.index(guard_line))
        self.assertLess(detach.index(guard_line),detach.index('Start-Process -FilePath'))
        owner_part=source[source.index('$taskProcess.StartInfo ='):]
        self.assertLess(owner_part.index(guard_line),owner_part.index('$taskProcess.Start()'))
        actual_guard=guard_line.replace('([DateTimeOffset]::UtcNow)','$script:taskClock')
        body=guard_function+'''
$taskPlan=@{slot='C:\\fake-slot';session='s';task='t';dispatch='d'}
$taskApproval=@{approved_plan_sha256='sha';session='s';task='t';dispatch='d';start_utc='2026-11-12T04:00:00Z';deadline_utc='2026-11-12T05:00:00Z'}
$taskPlanSha='sha';$taskSlot='C:\\fake-slot'
$taskRows=@()
foreach ($taskBoundary in @('hidden-host','owner')) {
 foreach ($taskEnd in @('2026-11-12T04:52:59Z','2026-11-12T04:53:00Z')) {
  $script:taskClock=[DateTimeOffset]::Parse('2026-11-12T04:52:58Z')
  $taskCreates=0
  try {
'''+actual_guard+'''
   # 假语义预检不创建进程，仅推进时钟；不用真实sleep。
   $script:taskClock=[DateTimeOffset]::Parse($taskEnd)
'''+actual_guard+'''
   $taskCreates+=1
   $taskRejected=$false
  } catch { $taskRejected=$true }
  $taskRows+=@{boundary=$taskBoundary;ending=$taskEnd;fake_creates=$taskCreates;rejected=$taskRejected}
 }
}
$taskRows | ConvertTo-Json
'''
        run=subprocess.run(['powershell.exe','-NoProfile','-EncodedCommand',base64.b64encode(body.encode('utf-16le')).decode('ascii')],capture_output=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr.decode('utf-8',errors='replace'))
        rows=json.loads(run.stdout.decode('utf-8-sig'))
        self.assertEqual([r['fake_creates'] for r in rows],[1,0,1,0])
        self.assertEqual([r['rejected'] for r in rows],[False,True,False,True])

    def test_exact_start_guard_with_fake_creation_has_zero_calls_outside_window(self):
        script=Path(__file__).resolve().parents[1]/'tools/Start-LegacyObservationOwner.ps1'
        source=script.read_text(encoding='utf-8-sig')
        function=source[source.index('function Assert-LegacyObservationStart {'):source.index('$taskSlot = [IO.Path]::GetFullPath($Slot)')]
        # 只执行原guard函数；Start-Process在本离线作用域中为计数假函数。
        body=function+'''\n$script:taskFakeCreates=0
function Start-Process { $script:taskFakeCreates += 1 }
$taskPlan=@{slot='C:\\fake-slot';session='s';task='t';dispatch='d'}
$taskGo=@{approved_plan_sha256='sha';session='s';task='t';dispatch='d';start_utc='2026-11-12T04:00:00Z';deadline_utc='2026-11-12T05:00:00Z'}
$taskResults=@()
foreach ($taskTime in @('2026-11-12T03:59:59Z','2026-11-12T04:00:00Z','2026-11-12T04:52:59Z','2026-11-12T04:53:00Z','2026-11-12T05:01:00Z')) {
 $script:taskFakeCreates=0
 try {
  Assert-LegacyObservationStart -Plan $taskPlan -Approval $taskGo -PlanSha256 'sha' -ResolvedSlot 'C:\\fake-slot' -NowUtc ([DateTimeOffset]::Parse($taskTime))
  Start-Process
  $taskRejected=$false
 } catch { $taskRejected=$true }
 $taskResults+=@{at=$taskTime;rejected=$taskRejected;fake_creates=$script:taskFakeCreates}
}
$taskResults | ConvertTo-Json
'''
        run=subprocess.run(['powershell.exe','-NoProfile','-EncodedCommand',base64.b64encode(body.encode('utf-16le')).decode('ascii')],capture_output=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr.decode('utf-8',errors='replace'))
        rows=json.loads(run.stdout.decode('utf-8-sig'))
        self.assertEqual([x['fake_creates'] for x in rows],[0,1,1,0,0])
        self.assertEqual([x['rejected'] for x in rows],[True,False,False,True,True])

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
