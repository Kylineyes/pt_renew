"""原服务Popen的MCP标准输入输出连接；不使用另行创建服务的stdio_client。"""
from __future__ import annotations

import asyncio
import json
import queue
import threading

from .core import SECOND, digest, require
from .runtime import write_once
from .events import decode_object


class OriginalMcpConnection:
    def __init__(self, runtime, key, *, enabled=False, result_factory=None):
        self.runtime, self.ledger, self.key = runtime, runtime.ledger, key
        child = runtime.children[key]
        require(runtime.registry.entries[key]['role'] == 'service' and child['identity'] is not None,
                'MCP连接必须绑定本客户端创建并核验的原服务Popen')
        self.process = child['process']
        require(self.process is not None and self.process.stdin is not None and self.process.stdout is not None,
                '原服务Popen没有独占标准输入输出管道')
        self.enabled, self.result_factory = enabled is True, result_factory
        self.responses = queue.Queue(maxsize=128)
        self.reader = None
        self.counter = 0
        self.busy = self.failed = self.closed = self.initialized = False
        self.initialize_used = False
        self.schemas = {}
        self.calls = []

    def read_loop(self):
        try:
            while True:
                raw = self.process.stdout.readline(16 * 1024 * 1024 + 1)
                if not raw: self.responses.put_nowait(('eof', None)); return
                require(len(raw) <= 16 * 1024 * 1024 and raw.endswith(b'\n'), '原MCP服务返回超长或不完整行')
                self.responses.put_nowait(('message', (decode_object(raw), raw)))
        except BaseException as error:
            try: self.responses.put_nowait(('error', type(error).__name__ + ': ' + str(error)))
            except queue.Full: self.failed = True

    def send(self, row):
        require(not self.closed and self.process.poll() is None, '原MCP服务已退出或连接已关闭')
        raw = json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n'
        self.process.stdin.write(raw); self.process.stdin.flush()

    async def rpc(self, method, params, *, deadline_ns):
        self.ledger.desktop_allowed()
        require(self.enabled and not self.busy and not self.failed and not self.closed, '原MCP连接禁用、忙或已有未知失败')
        self.busy = True
        self.counter += 1; ident = self.counter
        row = dict(id=ident, method=method, attempted=True, returned=False)
        self.calls.append(row)
        try:
            if self.reader is None:
                self.reader = threading.Thread(target=self.read_loop, name='pt-mcp-original-popen', daemon=True)
                self.reader.start()
            self.ledger.remaining(deadline_ns)
            self.send(dict(jsonrpc='2.0', id=ident, method=method, params=params))
            while True:
                remaining = self.ledger.remaining(deadline_ns)
                try: kind, message = await asyncio.to_thread(self.responses.get, True, min(.1, remaining))
                except queue.Empty: continue
                require(kind == 'message', '原MCP服务断开或读管道失败')
                message, raw = message
                require(message.get('jsonrpc') == '2.0', '原MCP服务回执协议未知')
                if 'id' not in message:
                    require(message.get('method', '').startswith('notifications/'), '原服务发送未知通知')
                    continue
                require(type(message['id']) is int and message['id'] == ident
                        and 'error' not in message and 'result' in message, '原MCP回执ID不符或服务报告错误')
                row['returned'] = True
                child = self.runtime.children[self.key]
                write_once(child['folder'] / f'rpc-{ident:04}-reply.json', raw)
                self.ledger.event('original_mcp_reply', id=ident, method=method, sha256=digest(raw),
                                  service_identity=child['identity'], original_popen=True)
                self.ledger.remaining(deadline_ns)
                require(not self.failed, '原MCP读管道已经失败或队列溢出')
                return message['result']
        except BaseException:
            self.failed = True
            raise
        finally:
            self.busy = False

    async def initialize(self):
        require(not self.initialize_used and not self.ledger.cleanup_active, '原MCP连接只初始化一次且不能在失败收尾重新初始化')
        self.initialize_used = True
        deadline = self.ledger.call_deadline(35 * SECOND)
        result = await self.rpc('initialize', dict(protocolVersion='2024-11-05', capabilities={},
                                                 clientInfo=dict(name='pt-renew-product-client', version='1')), deadline_ns=deadline)
        require(result.get('protocolVersion') == '2024-11-05' and isinstance(result.get('capabilities'), dict),
                '原MCP服务初始化协议不符，需要另行冻结兼容性')
        self.ledger.remaining(deadline)
        self.send(dict(jsonrpc='2.0', method='notifications/initialized'))
        listed = await self.rpc('tools/list', {}, deadline_ns=deadline)
        tools = listed.get('tools')
        require(isinstance(tools, list) and all(isinstance(tool.get('name'), str) and isinstance(tool.get('inputSchema'), dict)
                                               for tool in tools), '原服务工具schema缺失')
        self.schemas = {tool['name']: tool['inputSchema'] for tool in tools}
        require(len(self.schemas) == len(tools) and {'Snapshot', 'Click', 'Shortcut', 'Type'} <= self.schemas.keys(),
                '原服务缺少产品所需工具或名称重复')
        self.ledger.remaining(deadline)
        self.initialized = True
        return self.schemas

    async def call_tool(self, tool, arguments):
        require(self.initialized and tool in self.schemas, '原MCP连接尚未初始化或工具未公布')
        deadline = self.ledger.call_deadline(35 * SECOND)
        result = await self.rpc('tools/call', dict(name=tool, arguments=arguments), deadline_ns=deadline)
        if self.result_factory is None:
            from mcp.types import CallToolResult
            value = CallToolResult.model_validate(result)
        else:
            value = self.result_factory(result)
        self.ledger.remaining(deadline)
        return value

    async def close(self):
        """产品先收尾后由上层显式EOF；不发送桌面请求，不强杀，不把EOF当退出证明。"""
        require(not self.closed and not self.busy, '不能重复关闭或在原工具调用期间关闭连接')
        self.closed = True
        self.process.stdin.close()
        await self.runtime.wait_child(self.key)
        if self.reader is not None:
            await asyncio.to_thread(self.reader.join, .5)
            require(not self.reader.is_alive(), '原服务已退出但读管道线程仍未知')
        self.process.stdout.close()
        return self.runtime.accept_report(self.key)
