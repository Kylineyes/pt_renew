"""实际产品兼容性客户端入口；只处理本轮冻结配置和逐条显式命令。"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path

from async_product_client.bootstrap import ProductBootstrap
from async_product_client.connection import OriginalMcpConnection
from async_product_client.core import digest, require
from async_product_client.driver import DriverMailbox, ProductDriver
from async_product_client.events import decode_object
from async_product_client.file_dialog import NetFileSpec
from async_product_client.product import ProductOwner, tree_hashes
from async_product_client.python_environment import environment
from async_product_client.review import PiReadVerifier
from async_product_client.runtime import FrozenProgram
from async_product_client.shutdown import ShutdownCoordinator


EXPERIMENT_SHA = '782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac'


def verify_materials(configuration):
    service = FrozenProgram(**configuration['service_program'])
    require(service.entry == 'async_product_client/service_driver.py' and service.python_environment is not None,
            '实际服务须使用冻结服务入口及基础解释器依赖')
    service.verify()
    server = configuration['service_configuration']
    require(set(server) == {'package_root', 'trace', 'approval', 'approval_sha256'}
            and digest(Path(server['approval']).read_bytes()) == server['approval_sha256'], '服务材料或原批准摘要不符')
    product = configuration['product']
    require(set(product) == {'kind', 'deployment', 'manifest', 'board', 'board_sha256', 'a', 'b', 'environment',
                             'interpreter', 'interpreter_sha256', 'package_root', 'package_files', 'module_root',
                             'module_files', 'diagnostic_deadline_ns', 'revision', 'python_environment'},
            '产品配置含未冻结参数或缺少依赖材料')
    require(product['kind'] in ('net', 'copper') and product['revision'] == 2
            and len(product['manifest']) == 22 and product['manifest'].get('pt-renew.exe') == EXPERIMENT_SHA
            and tree_hashes(product['deployment']) == product['manifest'], '实验22文件部署或原修订不符')
    board = Path(product['board'])
    a, b = NetFileSpec(**product['a']), NetFileSpec(**product['b']); a.verify(); b.verify()
    require(board.name == 'board.pcb' and not board.is_symlink() and a.sha256 != b.sha256
            and board.parent.resolve() == Path(a.path).parent == Path(b.path).parent
            and digest(board.read_bytes()) == product['board_sha256'], '新输入三副本或冻结摘要不符')
    require(len(product['package_files']) == 77 and tree_hashes(Path(product['package_root']) / 'windows_mcp', ignore_bytecode=True)
            == product['package_files'] and product['package_root'] == server['package_root'], '服务/探针未共享完整冻结77文件包')
    require(tree_hashes(product['module_root'], ignore_bytecode=True) == product['module_files'], '产品探针完整模块摘要不符')
    dependencies = environment(product['python_environment'])
    require(dependencies is not None and product['python_environment'] == service.python_environment
            and Path(product['interpreter']).resolve() == Path(service.interpreter).resolve()
            and product['interpreter_sha256'] == service.interpreter_sha256, '服务/探针必须共享直接基础解释器及冻结依赖')
    dependencies.verify()
    require(not any(name.upper().startswith(('QT_', 'QML', 'PT_ASYNC_', 'PT_RENEW_ASYNC_', 'PT_ENABLE_ASYNC', 'PYTHON'))
                    for name in product['environment']), '产品继承环境未清理Qt/实验/Python变量')


def authorize(runtime, configuration):
    require(runtime.enabled and runtime.relay.role == 'client' and set(configuration) == {
        'approval', 'approval_sha256', 'service_program', 'service_configuration', 'product', 'session_file', 'schemas'},
        '客户端角色、启用状态或冻结配置协议不符')
    raw = Path(configuration['approval']).read_bytes()
    require(digest(raw) == configuration['approval_sha256'], '本轮客户端批准原字节改变')
    row = decode_object(raw)
    ledger = runtime.ledger
    require(row.get('context') == asdict(ledger.context) and row.get('scope') == 'product-compatibility'
            and row.get('permission_confirmed') is True and row.get('permission') and row.get('message_id')
            and row.get('evidence_root') == str(runtime.root) and row.get('max_product_launches') == 1
            and row.get('max_connections') == 1 and row.get('max_probe_queries') == 32
            and row.get('diagnostic_deadline_ns') == ledger.diagnostic_deadline_ns
            and row.get('cleanup_deadline_ns') == ledger.cleanup_deadline_ns,
            '客户端本轮上下文/兼容性范围/持续授权/唯一机会或原截止不符')
    actual = tuple(os.environ.get(name) for name in ('PI_PROVIDER', 'PI_MODEL', 'PI_REASONING_LEVEL', 'PI_SESSION_ID'))
    require(actual == (ledger.context.provider, ledger.context.model, ledger.context.thinking, ledger.context.session_id),
            '客户端实际Pi模型/推理强度/session环境不符')
    first = Path(configuration['session_file']).open('rb')
    try: session = decode_object(first.readline())
    finally: first.close()
    require(session.get('type') == 'session' and session.get('id') == ledger.context.session_id,
            '客户端实际read会话首记录与本轮绑定不符')
    require(isinstance(configuration['schemas'], dict) and {'Snapshot', 'Click', 'Shortcut', 'Type'} <= configuration['schemas'].keys(),
            '客户端缺少待逐字比较的冻结原工具schema')
    verify_materials(configuration)
    require(configuration['product']['diagnostic_deadline_ns'] == ledger.diagnostic_deadline_ns,
            '产品材料试图重置原诊断截止')
    server = decode_object(Path(configuration['service_configuration']['approval']).read_bytes())
    require(server.get('task_id') == ledger.context.task_id and server.get('dispatch_id') == ledger.context.dispatch_id
            and server.get('client_run_id') == ledger.context.run_id and server.get('session_id') == ledger.context.session_id
            and server.get('mode') == 'diagnostics-only' and server.get('permission_confirmed') is True
            and server.get('permission') == row['permission'] and server.get('message_id') == row['message_id']
            and server.get('diagnostic_seconds') == 600 and server.get('total_seconds') == 900,
            '本轮服务批准与客户端上下文、持续授权或原预算不符')
    launcher = server.get('launcher_files', {})
    files = dict(configuration['service_program']['files'])
    require({'run_control_diagnostics.py', 'control_diagnostics.py'} <= launcher.keys()
            and all(files.get(name) == sha for name, sha in launcher.items()), '服务启动器未完全绑定本轮冻结模块')
    return row


async def run(runtime, configuration):
    authorize(runtime, configuration)
    ledger = runtime.ledger
    shutdown = ShutdownCoordinator(ledger, ProductOwner(ledger), registry=runtime.registry)
    driver = None
    async def start(ident, parent):
        with ledger.operation(ident + '-service', parent):
            runtime.spawn('service', role='service', program=FrozenProgram(**configuration['service_program']),
                          configuration=configuration['service_configuration'], pipes=True)
            connection = OriginalMcpConnection(runtime, 'service', enabled=True)
            driver.shutdown.connection = connection
            schemas = await connection.initialize()
            require(schemas == configuration['schemas'], '实际服务工具schema与本轮冻结参考不同')
        bootstrap = ProductBootstrap(runtime, connection, runtime.root / 'product-session', enabled=True)
        driver.shutdown = bootstrap.shutdown
        arguments = dict(configuration['product'])
        arguments['a'] = NetFileSpec(**arguments['a']); arguments['b'] = NetFileSpec(**arguments['b'])
        require(arguments.get('diagnostic_deadline_ns') == ledger.diagnostic_deadline_ns,
                '产品配置试图更换原诊断截止')
        from jsonschema.validators import validator_for
        validators = {}
        for name, schema in schemas.items():
            cls = validator_for(schema); cls.check_schema(schema); validators[name] = cls(schema)
        def validate(tool, args): validators[tool].validate(args)
        arguments.update(verifier=PiReadVerifier(configuration['session_file']), validate=validate)
        return await bootstrap.start(ident, ledger.token, **arguments)
    driver = ProductDriver(ledger, start=start, shutdown=shutdown, enabled=True)
    try:
        return await DriverMailbox(driver, runtime.root).run()
    except BaseException as error:
        driver.shutdown.fail('client-driver', error)
        raise
