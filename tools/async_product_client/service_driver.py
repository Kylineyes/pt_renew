"""在本服务原Popen内部运行冻结控制启动器；不另启服务进程，不复用旧批准。"""
from __future__ import annotations

import asyncio
from pathlib import Path

from async_product_client.core import digest, require
from async_product_client.events import decode_object


async def run(runtime, configuration):
    require(runtime.enabled and runtime.relay.role == 'service' and not runtime.registry.entries,
            '控制服务入口只可在本轮已绑定服务创建者运行')
    require(set(configuration) == {'package_root', 'trace', 'approval', 'approval_sha256'}, '服务配置含未冻结字段')
    approval_path = Path(configuration['approval']).resolve()
    raw = approval_path.read_bytes()
    require(digest(raw) == configuration['approval_sha256'], '服务批准原字节摘要改变')
    approval = decode_object(raw)
    ledger = runtime.ledger
    require(approval.get('task_id') == ledger.context.task_id and approval.get('dispatch_id') == ledger.context.dispatch_id
            and approval.get('permission_confirmed') is True and approval.get('permission') and approval.get('message_id')
            and approval.get('diagnostic_seconds') == 600 and approval.get('total_seconds') == 900,
            '本轮服务批准上下文、持续控制授权或原600/900预算不符')
    require(approval.get('client_run_id') == ledger.context.run_id and approval.get('session_id') == ledger.context.session_id,
            '服务批准未绑定本轮客户端run及指定Pi会话')
    # 源文件、77文件包及全部可选包装仍由原serve核验；不修改门禁/指示层/阈值。
    from run_control_diagnostics import serve
    ledger.time_left()
    await asyncio.to_thread(serve, configuration['package_root'], configuration['trace'], str(approval_path))
    return 0
