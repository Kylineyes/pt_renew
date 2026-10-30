"""显式产品兼容性命令路由与单请求邮箱；不自动读图、输入或启动竞争。"""
from __future__ import annotations

import asyncio
from dataclasses import asdict
import json
from pathlib import Path
import re

from .core import SECOND, digest, require
from .events import decode_object
from .runtime import write_once


class ProductDriver:
    def __init__(self, ledger, *, start, shutdown, enabled=False, max_requests=32):
        require(type(max_requests) is int and 0 < max_requests <= 32, '兼容性命令次数无效')
        self.ledger, self.start, self.shutdown = ledger, start, shutdown
        self.enabled, self.max_requests = enabled is True, max_requests
        self.session = None
        self.started = self.stopped = False
        self.seen = set()

    def envelope(self, row):
        require(self.enabled and not self.stopped and isinstance(row, dict)
                and set(row) == {'context', 'id', 'parent', 'action', 'arguments'}
                and row['context'] == asdict(self.ledger.context), '命令未启用、已停止、上下文或协议不符')
        ident = row['id']
        require(isinstance(ident, str) and re.fullmatch('[A-Za-z0-9_-]+', ident)
                and ident not in self.seen and len(self.seen) < self.max_requests
                and row['parent'] == self.ledger.token and isinstance(row['arguments'], dict), '命令ID/次数/原token/参数无效')
        self.seen.add(ident)
        return ident, row['parent'], row['action'], row['arguments']

    async def execute(self, row):
        ident, parent, action, args = self.envelope(row)
        try:
            if action == 'start':
                require(not self.started and not args, '产品兼容性只能启动一次，参数来自冻结配置')
                self.started = True
                self.session = await self.start(ident, parent)
                return self.session.report()
            if action == 'stop':
                require(not args, '正常stop不接受外部参数')
                with self.ledger.operation(ident, parent, cleanup=True):
                    result = await self.shutdown.stop_service()
                    self.stopped = True
                return dict(service_report_sha256=digest(result))
            session = self.session or self.shutdown.session
            require(session is not None, '必须先完成同客户端原身份装配')
            if self.session is None:
                require(action in ('cancel-file', 'close'), '初始化失败后仅可使用已保留组件正常收尾')
            methods = {'prepare': session.prepare, 'ack-baseline': session.ack_baseline,
                       'command-image': session.capture_command, 'command-ack': session.ack_command,
                       'command-click': session.invoke_command, 'file': session.file_step,
                       'cancel-file': session.cancel_file_step, 'close': session.close_step}
            require(action in methods, '兼容性驱动不提供竞争、release或任意工具入口')
            if action == 'command-click':
                require(session.journal.kind == 'net', '兼容性任务不能触发铜门闩请求')
            if action == 'file':
                require(args.get('action') in ('start', 'ack', 'type', 'choose')
                        and (args.get('action') != 'choose' or args.get('choice') == 'cancel'),
                        '兼容性文件框只可读图、输入冻结路径及明确取消，不能打开目标B')
            if self.ledger.failed is not None:
                require(action in ('cancel-file', 'close'), '失败后只允许原冷却后的明确正常收尾')
            return await methods[action](ident, parent, **args)
        except BaseException as error:
            self.shutdown.fail(ident, error)
            raise

    def report(self):
        return dict(context=asdict(self.ledger.context), token=self.ledger.token, failed_id=self.ledger.failed,
                    not_before_ns=self.ledger.not_before_ns, diagnostic_deadline_ns=self.ledger.diagnostic_deadline_ns,
                    cleanup_deadline_ns=self.ledger.cleanup_deadline_ns, gate_trigger_ns=self.ledger.gate_trigger_ns,
                    started=self.started, stopped=self.stopped,
                    session=self.session.report() if self.session is not None else None,
                    ready_for_live=False, gui_verified=False)


class DriverMailbox:
    def __init__(self, driver, root, *, pause=asyncio.sleep):
        self.driver, self.root, self.pause = driver, Path(root).resolve(), pause
        self.inbox, self.replies = self.root / 'inbox', self.root / 'replies'
        self.processed = {}
        self.number = 0

    def initialize(self):
        self.inbox.mkdir(exist_ok=False); self.replies.mkdir(exist_ok=False)
        write_once(self.root / 'driver-ready.json', json.dumps(self.driver.report(), ensure_ascii=False).encode('utf-8'))

    async def step(self):
        for path, expected in self.processed.items():
            require(path.is_file() and digest(path.read_bytes()) == expected, '已消费命令原件被修改或删除')
        pending = sorted(path for path in self.inbox.glob('*.json') if path not in self.processed)
        if not pending: return False
        require(len(pending) == 1, '只接受唯一在途命令，不能预排后续输入')
        path = pending[0]
        require(not path.is_symlink(), '命令原件不能是链接')
        raw = path.read_bytes()
        self.processed[path] = digest(raw)
        self.number += 1
        reply = dict(number=self.number, request_sha256=digest(raw), completed=False)
        try:
            row = decode_object(raw)
            require(path.name == row.get('id', '') + '.json', '命令文件名与唯一ID不符')
            cleanup = row.get('action') in ('cancel-file', 'close', 'stop')
            deadline = self.driver.ledger.cleanup_deadline_ns if cleanup else self.driver.ledger.current_deadline_ns
            reply['deadline_ns'] = deadline
            reply['result'] = await self.driver.execute(row)
            reply['completed'] = True
        except BaseException as error:
            self.driver.shutdown.fail('mailbox-' + str(self.number), error)
            reply.update(error=type(error).__name__, reason=str(error))
        reply['state'] = self.driver.report()
        write_once(self.replies / f'{self.number:04}.json', json.dumps(reply, ensure_ascii=False).encode('utf-8'))
        if reply['completed']:
            if self.driver.ledger.clock.monotonic_ns() >= reply['deadline_ns']:
                self.driver.shutdown.fail('mailbox-persist-' + str(self.number), ValueError('命令回执落盘越过原截止'))
                write_once(self.replies / f'{self.number:04}-rejected.json',
                           json.dumps(self.driver.report(), ensure_ascii=False).encode('utf-8'))
        return True

    async def run(self):
        self.initialize()
        ledger = self.driver.ledger
        while not self.driver.stopped:
            require(ledger.clock.monotonic_ns() < ledger.cleanup_deadline_ns, '客户端原900秒截止已到，停止命令处理')
            try: changed = await self.step()
            except BaseException as error:
                self.driver.shutdown.fail('mailbox-protocol', error)
                # 队列/原件破坏不可恢复；交由创建者保留原对象并发布失败。
                raise
            if not changed:
                self.driver.shutdown.poll()
                remaining = (ledger.cleanup_deadline_ns - ledger.clock.monotonic_ns()) / SECOND
                require(remaining > 0, '客户端原收尾截止已到')
                await self.pause(min(.05, remaining))
        return 0 if ledger.failed is None else 1


def submit(root, row):
    root = Path(root).resolve()
    ready = decode_object((root / 'driver-ready.json').read_bytes())
    require(row.get('context') == ready.get('context') and isinstance(row.get('id'), str)
            and re.fullmatch('[A-Za-z0-9_-]+', row['id']), '提交命令上下文/ID不符')
    require((root / 'inbox').is_dir() and not (root / 'inbox').is_symlink(), '本轮命令目录无效')
    path = root / 'inbox' / (row['id'] + '.json')
    write_once(path, json.dumps(row, ensure_ascii=False).encode('utf-8'))
    return path
