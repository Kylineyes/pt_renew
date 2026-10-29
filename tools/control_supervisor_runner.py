"""本机连续核验、持柄、放行并等待监督器；所有批准在短握手期限前准备完成。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from control_process_supervisor import ProcessApi, load, validate_plan
from control_witness_launch import WitnessLaunch, base_python

RUNNER_NAME = 'control_supervisor_runner.py'


def write_once(path, row):
    with path.open('x', encoding='utf-8') as out:
        json.dump(row, out, ensure_ascii=False, indent=2)


def preflight(root, *, current_executable=sys.executable):
    """只有文件和标准库解释器探针；在创建监督器及10秒握手之前完成。"""
    root = Path(root).resolve(strict=True)
    plan_path = root/'supervisor-plan.json'
    raw = plan_path.read_bytes()
    plan = json.loads(raw.decode('utf-8-sig'))
    plan['_source_sha256'] = hashlib.sha256(raw).hexdigest()
    if RUNNER_NAME not in plan.get('supervisor_files', {}):
        raise RuntimeError('方案未冻结本机连续启动器')
    if (root/RUNNER_NAME).resolve() != Path(__file__).resolve():
        raise RuntimeError('必须运行本次证据目录中已冻结的启动器')
    for name in ('runner-start.json', 'runner-held.json', 'runner-result.json', 'runner-error.json'):
        if (root/name).exists():
            raise RuntimeError('已有启动器原件，禁止重复启动')
    client = Path(plan['client_interpreter']).resolve(strict=True)
    # 父进程可能使用MCP venv。先核验实际基础Python，再按监督器真实执行环境验证。
    resolved = base_python(current_executable)
    # validate_plan的解释器独立条件按将要运行监督器的基础解释器检查，
    # 不修改sys.executable，也不改变控制客户端解释器。
    validate_plan(plan, root, supervisor_executable=resolved)
    return root, plan, client, resolved


def audit_completion(root, held, popen_result, handle_exit, plan_sha256):
    """退出证明必须同时对应原Popen、原查询句柄及实际监督器身份。"""
    own = load(root/'supervisor-identity.json')
    chain = load(root/'supervisor-chain-exit.json')
    if not (held['pid'] == popen_result['pid'] == popen_result['actual_pid']
            == own['pid'] == chain['supervisor_pid']
            and held['birth'] == own['birth'] == chain['supervisor_birth']
            and own['plan_sha256'] == plan_sha256):
        raise RuntimeError('监督器实际身份、方案或原退出证明不一致')
    if popen_result['exit_code'] != handle_exit:
        raise RuntimeError('监督器原Popen与原句柄退出码不一致')
    processes = chain.get('processes')
    if (not isinstance(processes, list) or not processes
            or any(type(p.get('pid')) is not int or type(p.get('birth')) is not int
                   or type(p.get('exit_code')) is not int or p['exit_code'] != 0 for p in processes)
            or len({(p['pid'],p['birth']) for p in processes}) != len(processes)):
        raise RuntimeError('子孙退出记录缺失、重复或含失败码')
    if (handle_exit != 0 or chain.get('verified') is not True or chain.get('capture_errors')
            or chain.get('all_exited') is not True or chain.get('all_exit0') is not True
            or chain.get('client_popen_exit_code') != 0):
        raise RuntimeError('监督器或子孙退出未通过，保留原始失败码')
    return dict(verified=True, supervisor_pid=held['pid'], supervisor_birth=held['birth'],
                supervisor_exit_code=handle_exit, client_popen_exit_code=chain['client_popen_exit_code'],
                processes=chain['processes'], termination_calls=0, restart_calls=0)


def run(root, *, current_executable=sys.executable, api_factory=ProcessApi, launch_factory=WitnessLaunch):
    root, plan, client, resolved = preflight(root, current_executable=current_executable)
    # 同一进程只能有一个启动所有者；文件已存在时open('x')拒绝，无新监督器。
    write_once(root/'runner-start.json', dict(started=time.monotonic(), plan_sha256=plan['_source_sha256'],
        supervisor_interpreter=str(resolved), client_interpreter=str(client),
        note='批准和慢探针均已完成；下面持柄与放行本机连续执行，无代理消息等待'))
    api, launch, handle, held, popen_result = None, None, None, None, None
    try:
        api = api_factory()
        launch = launch_factory(root/'control_process_supervisor.py', root, interpreter=resolved)
        # WitnessLaunch已核验Popen PID与子进程实际PID/解释器/脚本摘要。
        # 同步持柄并保存创建时间，随后立即放行，不在10秒期限内等待外部消息。
        handle, birth = api.hold(launch.process.pid)
        if api.poll(handle) is not None:
            raise RuntimeError('监督器在本机持柄之前已经退出，不能放行')
        held = dict(pid=launch.process.pid, birth=birth, held=time.monotonic(),
                    identity=launch.identity, witness_directory=str(launch.directory))
        write_once(root/'runner-held.json', held)
        launch.release()
        popen_result = launch.wait()
        code = api.poll(handle)
        result = audit_completion(root, held, popen_result, code, plan['_source_sha256'])
        result.update(finished=time.monotonic(), plan_sha256=plan['_source_sha256'],
                      witness_directory=str(launch.directory))
        write_once(root/'runner-result.json', result)
        return result
    except BaseException as error:
        pending = getattr(error, 'pending_launch', None) or launch
        evidence = dict(error=type(error).__name__+': '+str(error), verified=False,
                        termination_calls=0, restart_calls=0,
                        held_identity=held, plan_sha256=plan['_source_sha256'])
        # 不清失败或重新启动。未放行child按其原10秒期限自行退出；
        # 已放行进程只等待原有正常生命周期，不能因父错误强杀。
        if pending is not None:
            try:
                if popen_result is None:
                    popen_result = pending.wait()
                evidence['popen_result'] = popen_result
            except BaseException as wait_error:
                evidence['wait_error'] = type(wait_error).__name__+': '+str(wait_error)
                error.pending_launch = pending
        if handle is not None:
            try:
                evidence['handle_exit_code'] = api.poll(handle)
            except BaseException as poll_error:
                evidence['handle_error'] = type(poll_error).__name__+': '+str(poll_error)
        write_once(root/'runner-error.json', evidence)
        raise
    finally:
        if handle is not None:
            api.close(handle)


def main():
    parser = argparse.ArgumentParser(description='已批准的本机连续监督器启动与退出见证')
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    result = run(args.root)
    print(json.dumps(dict(verified=result['verified'], supervisor_pid=result['supervisor_pid'],
                         exit_code=result['supervisor_exit_code']), ensure_ascii=False))


if __name__ == '__main__':
    main()
