"""只持有本轮控制链查询句柄，等待正常stop；不访问桌面/不结束进程。"""
from pathlib import Path
import json,subprocess,time
from process_witness import ProcessWitness,process_birth
R=Path(__file__).resolve().parent
rows=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command','Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,ExecutablePath | ConvertTo-Json -Compress'],text=True,encoding='utf-8-sig'))
ids={json.loads((R/'launcher.json').read_text(encoding='utf-8-sig'))['launcher_pid'],json.loads((R/'client-identity.json').read_text(encoding='utf-8-sig'))['pid']};changed=True
while changed:
 changed=False
 for row in rows:
  if row['ParentProcessId'] in ids and row['ProcessId'] not in ids:ids.add(row['ProcessId']);changed=True
witnesses=[]
for pid in sorted(ids):
 birth=process_birth(pid)
 if birth is not None:witnesses.append((pid,birth,ProcessWitness(pid,birth)))
(R/'chain-held.json').write_text(json.dumps(dict(processes=[dict(pid=p,birth=b) for p,b,w in witnesses],monotonic=time.monotonic()),indent=2),encoding='utf-8')
end=time.monotonic()+60
while time.monotonic()<end:
 if all(w.poll() is not None for _,_,w in witnesses):break
 time.sleep(.2)
result=dict(processes=[dict(pid=p,birth=b,exit_code=w.poll()) for p,b,w in witnesses],termination_calls=0,wall=time.time())
result['all_exited']=all(r['exit_code'] is not None for r in result['processes'])
(R/'chain-exit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
