"""绑定原服务管道的MCP协议及生产装配回归；不运行真实控制服务。"""
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.bootstrap import ProductBootstrap
from async_product_client.connection import OriginalMcpConnection
from async_product_client.core import Context, Ledger, SECOND
from test_async_product_adapters import Clock


class ConnectionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = Ledger(context=Context('task', 'dispatch', 'run', 'session'), clock=Clock(),
                             cleanup_deadline_ns=1000 * SECOND, enabled=True)
        self.closed = []

    def fixture(self, rows):
        process = SimpleNamespace(pid=42, stdin=io.BytesIO(), stdout=io.BytesIO(b''.join(
            json.dumps(row).encode() + b'\n' for row in rows)), poll=lambda: None)
        runtime = SimpleNamespace(ledger=self.ledger, relay=SimpleNamespace(role='client'),
                                  registry=SimpleNamespace(entries={'service': dict(role='service')},
                                                           poll=lambda: dict(lifecycle_complete=False)),
                                  children={'service': dict(process=process, identity=dict(pid=42), folder=self.root)})
        async def wait(key): self.closed.append(key)
        runtime.wait_child = wait; runtime.accept_report = lambda key: '报告'.encode()
        return runtime, process, OriginalMcpConnection(runtime, 'service', enabled=True)

    def messages(self):
        return [dict(jsonrpc='2.0', id=1, result=dict(protocolVersion='2024-11-05', capabilities={})),
                dict(jsonrpc='2.0', id=2, result=dict(tools=[dict(name=name, inputSchema={'type': 'object'})
                                                        for name in ('Snapshot', 'Click', 'Shortcut', 'Type')])),
                dict(jsonrpc='2.0', id=3, result=dict(isError=False, content=[dict(type='text', text='原始回执')]))]

    async def test_original_pipe_initialize_schema_and_sdk_serialization(self):
        runtime, process, connection = self.fixture(self.messages())
        with self.ledger.operation('initialize', 'start'): await connection.initialize()
        with self.ledger.operation('call', self.ledger.token):
            result = await connection.call_tool('Click', dict(loc=[1, 2]))
        self.assertFalse(result.model_dump(mode='json')['is_error'])
        self.assertEqual(result.model_dump(mode='json')['content'][0]['text'], '原始回执')
        sent = [json.loads(row) for row in process.stdin.getvalue().splitlines()]
        self.assertEqual([row['method'] for row in sent], ['initialize', 'notifications/initialized', 'tools/list', 'tools/call'])
        self.assertEqual(json.loads((self.root / 'rpc-0003-reply.json').read_bytes())['id'], 3)
        self.assertEqual(await connection.close(), '报告'.encode())
        self.assertTrue(process.stdin.closed); self.assertTrue(process.stdout.closed)
        self.assertEqual(self.closed, ['service'])

    async def test_wrong_response_id_is_unknown_and_cannot_be_retried(self):
        runtime, process, connection = self.fixture([dict(jsonrpc='2.0', id=99, result={})])
        with self.assertRaises(ValueError):
            with self.ledger.operation('initialize', 'start'): await connection.initialize()
        self.assertTrue(connection.failed)
        sent = process.stdin.getvalue()
        with self.assertRaises(ValueError): await connection.initialize()
        self.assertEqual(process.stdin.getvalue(), sent)
        self.assertFalse(connection.closed)
        process.stdin.close(); process.stdout.close()

    async def test_changed_protocol_consumes_initialize_opportunity_without_reconnection(self):
        messages = self.messages(); messages[0]['result']['protocolVersion'] = 'unknown'
        runtime, process, connection = self.fixture(messages)
        with self.assertRaises(ValueError):
            with self.ledger.operation('initialize', 'start'): await connection.initialize()
        with self.assertRaises(ValueError): await connection.initialize()
        self.assertEqual(len(connection.calls), 1)
        process.stdin.close(); process.stdout.close()

    async def test_reply_persistence_cost_cannot_cross_t1_and_allow_another_rpc(self):
        runtime, process, connection = self.fixture(self.messages())
        self.ledger.arm_gate(self.ledger.clock.now)
        original_emit = self.ledger.emit
        def emit(row):
            original_emit(row)
            if row['kind'] == 'original_mcp_reply': self.ledger.clock.tick(20)
        self.ledger.emit = emit
        with self.assertRaises(ValueError):
            with self.ledger.operation('initialize', 'start'): await connection.initialize()
        self.assertTrue(connection.failed)
        self.assertEqual(len(connection.calls), 1)
        self.assertEqual(self.ledger.failed, 'initialize')
        self.assertEqual(len(process.stdin.getvalue().splitlines()), 1)
        process.stdin.close(); process.stdout.close()

    async def test_production_bootstrap_default_disabled_keeps_no_product(self):
        runtime, process, connection = self.fixture([])
        bootstrap = ProductBootstrap(runtime, connection, self.root / 'product')
        with self.assertRaises(ValueError):
            await bootstrap.start('bootstrap', 'start', kind='net', deployment='unused', manifest={},
                                  board='unused', board_sha256='a' * 64, a=None, b=None, environment={},
                                  interpreter='unused', interpreter_sha256='a' * 64, package_root='unused', package_files={},
                                  module_root='unused', module_files={}, verifier=None, validate=None,
                                  diagnostic_deadline_ns=600 * SECOND)
        self.assertIsNone(bootstrap.owner.process)
        self.assertIsNone(bootstrap.creator)
        self.assertFalse(bootstrap.used)
        self.assertEqual(bootstrap.shutdown.poll()['next_action'], 'wait-original-cooldown')
        process.stdin.close(); process.stdout.close()


if __name__ == '__main__': unittest.main()
