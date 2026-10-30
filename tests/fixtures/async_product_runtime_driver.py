"""新建无GUI原Popen链测试驱动；不导入Qt、Win32桌面或控制包。"""
import asyncio
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from async_product_client.connection import OriginalMcpConnection
from async_product_client.runtime import FrozenProgram


async def server():
    while True:
        raw = await asyncio.to_thread(sys.stdin.buffer.readline)
        if not raw: return 0
        row = json.loads(raw)
        if 'id' not in row: continue
        if row['method'] == 'initialize': result = dict(protocolVersion='2024-11-05', capabilities={})
        elif row['method'] == 'tools/list':
            result = dict(tools=[dict(name=name, inputSchema={'type': 'object'}) for name in ('Snapshot', 'Click', 'Shortcut', 'Type')])
        elif row['method'] == 'tools/call':
            result = dict(isError=False, content=[dict(type='text', text='无GUI协议测试回执')])
        else: raise ValueError('测试服务收到未知方法')
        sys.stdout.write(json.dumps(dict(jsonrpc='2.0', id=row['id'], result=result)) + '\n'); sys.stdout.flush()


async def run(runtime, configuration):
    role = runtime.relay.role
    if role == 'service': return await server()
    program = FrozenProgram(**configuration['program'])
    key = 'client' if role == 'supervisor' else 'service'
    with runtime.ledger.operation('create-' + key, runtime.ledger.token):
        process = runtime.spawn(key, role=key, program=program, configuration=configuration, pipes=key == 'service')
    if role == 'client':
        # 一条仅等待stdin EOF的标准库子进程，角色模拟产品；不是产品或GUI证明。
        product = subprocess.Popen([sys.executable, '-B', '-X', 'utf8', '-c', 'import sys; sys.stdin.buffer.read()'],
                                   stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        runtime.registry.created('product', product, role='product')
        runtime.registry.identified('product', product, runtime.handles.inspect(product))
        connection = OriginalMcpConnection(runtime, 'service', enabled=True,
                                           result_factory=lambda row: SimpleNamespace(model_dump=lambda **kw: row))
        try:
            with runtime.ledger.operation('initialize', runtime.ledger.token): await connection.initialize()
            with runtime.ledger.operation('protocol', runtime.ledger.token):
                result = await connection.call_tool('Click', dict(loc=[1, 2]))
                assert result.model_dump()['content'][0]['text'] == '无GUI协议测试回执'
        finally:
            product.stdin.close()
            code = await asyncio.to_thread(product.wait, timeout=5)
            runtime.registry.exited('product', product, code)
        await connection.close()
    else:
        await runtime.wait_child(key)
        runtime.accept_report(key)
    return 0
