"""持续监督实际兼容性客户端；沿用原600/900截止及原Popen报告链。"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from async_product_client.client_driver import authorize
from async_product_client.core import SECOND, require
from async_product_client.runtime import FrozenProgram


def authorize_child(ledger, child_root, configuration):
    require(set(configuration) == {'client_program', 'client_configuration'}, '监督器冻结配置字段不符')
    program = FrozenProgram(**configuration['client_program'])
    require(program.entry == 'async_product_client/client_driver.py', '监督器只能创建冻结产品客户端')
    proxy = SimpleNamespace(enabled=True, relay=SimpleNamespace(role='client'), ledger=ledger, root=child_root)
    authorize(proxy, configuration['client_configuration'])
    program.verify()
    service = FrozenProgram(**configuration['client_configuration']['service_program'])
    product = configuration['client_configuration']['product']
    require(program.interpreter == service.interpreter and program.interpreter_sha256 == service.interpreter_sha256
            and program.root == service.root and dict(program.files) == dict(service.files)
            and program.python_environment == service.python_environment
            and product['module_root'] == program.root and product['module_files'] == dict(program.files),
            '客户端、服务和探针必须共享本轮完整冻结源码与基础解释器依赖')
    return program


async def await_original_exit(runtime, key):
    process = runtime.children[key]['process']
    while process.poll() is None:
        remaining = (runtime.ledger.cleanup_deadline_ns - runtime.ledger.clock.monotonic_ns()) / SECOND
        require(remaining > 0, '原创建者900秒截止已到，保留原Popen和未知状态')
        await asyncio.sleep(min(.1, remaining))
    await runtime.wait_child(key)


async def run(runtime, configuration):
    require(runtime.enabled and runtime.relay.role == 'supervisor', '监督器未显式启用或角色不符')
    program = authorize_child(runtime.ledger, runtime.root / 'client', configuration)
    with runtime.ledger.operation('create-client', runtime.ledger.token):
        runtime.spawn('client', role='client', program=program, configuration=configuration['client_configuration'])
    await await_original_exit(runtime, 'client')
    runtime.accept_report('client')
    return 0
