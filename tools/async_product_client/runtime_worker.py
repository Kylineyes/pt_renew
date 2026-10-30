"""实际创建者子入口；等待父原Popen绑定后才加载冻结驱动，不提供默认现场任务。"""
from __future__ import annotations

import asyncio
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from async_product_client.core import Context, Ledger, SECOND, digest, require
from async_product_client.events import decode_object
from async_product_client.process import OriginalHandleApi
from async_product_client.runtime import CreatorRuntime, FrozenProgram, write_once


async def run(plan_path, expected_sha256):
    path = Path(plan_path).resolve()
    runtime, ledger, failure = None, None, None
    try:
        raw = path.read_bytes()
        require(digest(raw) == expected_sha256 and not path.is_symlink(), '创建者启动计划原字节摘要不符')
        plan = decode_object(raw)
        require(plan.get('schema_version') == 1 and plan.get('enabled') is True
                and plan.get('role') in ('supervisor', 'client', 'service'), '创建者计划未显式启用或角色无效')
        program = FrozenProgram(**plan['program'])
        interpreter, root = program.verify()
        require(Path(sys.executable).resolve() == interpreter, '实际解释器与冻结计划不符')
        ledger = Ledger(context=Context(**plan['context']), cleanup_deadline_ns=plan['cleanup_deadline_ns'], enabled=True)
        ledger.diagnostic_deadline_ns = min(plan['diagnostic_deadline_ns'], ledger.cleanup_deadline_ns)
        deadline = min(ledger.diagnostic_deadline_ns, ledger.clock.monotonic_ns() + 35 * SECOND)
        while not (path.parent / 'parent-binding.json').exists():
            require(ledger.clock.monotonic_ns() < deadline, '父原Popen身份绑定等待超过原截止')
            await asyncio.sleep(min(.1, (deadline - ledger.clock.monotonic_ns()) / SECOND))
        binding = decode_object((path.parent / 'parent-binding.json').read_bytes())
        current = OriginalHandleApi().current_identity()
        identity = binding.get('identity', {})
        require(binding.get('context') == asdict(ledger.context) and binding.get('launch_sha256') == expected_sha256
                and identity.get('pid') == current['pid'] and identity.get('birth') == current['birth']
                and identity.get('original_handle') is True and Path(identity.get('image', '')).resolve() == interpreter,
                '父原Popen绑定与当前实际进程身份不符')
        roles = {'supervisor': ('client',), 'client': ('service', 'product'), 'service': ()}
        runtime = CreatorRuntime(ledger, path.parent, self_identity=identity, role=plan['role'],
                                 required_roles=roles[plan['role']], enabled=True)
        require(ledger.clock.monotonic_ns() < deadline, '冻结驱动加载前原截止已到')
        spec = importlib.util.spec_from_file_location('pt_frozen_creator_driver', root / program.entry)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ledger.time_left()
        result = await module.run(runtime, plan['configuration'])
        require(type(result) is int and result == 0, '冻结创建者驱动未正常返回0')
    except BaseException as error:
        failure = dict(error=type(error).__name__, reason=str(error), monotonic_ns=time.monotonic_ns())
        if ledger is not None:
            try: ledger.fail('creator-runtime', failure['reason'])
            except BaseException: pass
    finally:
        if runtime is not None:
            try:
                if any(entry['process'].poll() is None for entry in runtime.registry.entries.values()):
                    failure = failure or dict(error='PendingOriginalPopen', reason='创建者驱动结束时仍有原子进程存活')
                    try: ledger.fail('creator-runtime', failure['reason'])
                    except BaseException: pass
                    await runtime.drain_after_failure()
                runtime.poll()
                runtime.publish(launch_sha256=expected_sha256)
                if not runtime.registry.report()['action_succeeded']:
                    failure = failure or dict(error='IncompleteLifecycle', reason='原创建者子链尚未全部正常退出0')
            except BaseException as error:
                failure = failure or dict(error=type(error).__name__, reason=str(error))
        if failure is not None:
            write_once(path.parent / 'creator-failure.json', json.dumps(failure, ensure_ascii=False).encode('utf-8'))
    return 1 if failure is not None else 0


if __name__ == '__main__':
    require(len(sys.argv) == 3, '需要新启动计划路径和原字节摘要')
    raise SystemExit(asyncio.run(run(sys.argv[1], sys.argv[2])))
