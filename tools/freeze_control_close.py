"""离线冻结专用关闭客户端；不产生批准、不启动进程或桌面请求。"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil

from control_surface_approval import CLIENT_FILES, TOOL_FILES
from run_control_diagnostics import digest, prepare

SUPERVISOR_FILES = ('control_process_supervisor.py','control_witness_launch.py','control_supervisor_runner.py')
EXTRA_TOOLS = {'control_owned_close.py','audit_control_surfaces.py','replay_control_health.py'}


def freeze(destination, package_source):
    source = Path(__file__).resolve().parent
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    candidate = destination/'candidate'
    client, tools = candidate/'client', candidate/'tools'
    client.mkdir(parents=True)
    tools.mkdir()
    (client/'inbox').mkdir()
    for name in CLIENT_FILES:
        shutil.copyfile(source/'control_close_client'/name, client/name)
    for name in SUPERVISOR_FILES:
        shutil.copyfile(source/name, client/name)
    for name in TOOL_FILES | EXTRA_TOOLS:
        shutil.copyfile(source/name, tools/name)
    # 测试窗只有一个权威源码；冻结时核对模板没有自行演化。
    if (client/'window.py').read_bytes() != (tools/'control_test_window.py').read_bytes():
        raise ValueError('测试窗模板与工具不同')
    prepare(package_source, candidate/'isolated')
    for path in list(client.glob('*.py')) + list(tools.glob('*.py')):
        ast.parse(path.read_text(encoding='utf-8-sig'))
    hashes = lambda root, names: {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
    plan = dict(schema_version=1,purpose='control-client-witness',task_id=None,dispatch_id=None,
        diagnostic_seconds=600,total_seconds=900,scan_interval_seconds=.05,
        client_interpreter='C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Scripts/python.exe',
        client_files=hashes(client,CLIENT_FILES),supervisor_files=hashes(client,SUPERVISOR_FILES))
    (destination/'supervisor-plan-template.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    files = digest(candidate)
    result = dict(candidate_files=len(files),files=files,client_files=plan['client_files'],
        supervisor_files=plan['supervisor_files'],permission_confirmed=False,task_id=None,dispatch_id=None,desktop_requests=0)
    (destination/'candidate-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='只离线冻结一次新候选，不生成许可或启动现场')
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--package-source',type=Path,required=True)
    args=parser.parse_args()
    result=freeze(args.destination,args.package_source)
    print(json.dumps(dict(candidate_files=result['candidate_files'],desktop_requests=0),ensure_ascii=False))
