"""独立只读UIA子进程的有界等待；超时保留原Popen，禁止重试与强杀。"""
from __future__ import annotations

import asyncio
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import uuid

from .core import SECOND, digest, positive, require
from .events import decode_object
from .process import OriginalHandleApi
from .product import tree_hashes


async def pause(seconds):
    await asyncio.sleep(seconds)


class BoundedUiaProbe:
    def __init__(self, ledger, owner, creator, *, interpreter, interpreter_sha256,
                 package_root, package_files, module_root, module_files, evidence_root,
                 deadline_ns, enabled=False, timeout_ns=5 * SECOND, max_queries=32,
                 popen=None, handle_api=None, sleeper=pause, nonce_factory=None, registry=None, registry_parent='product'):
        require(positive(deadline_ns) and deadline_ns <= ledger.cleanup_deadline_ns
                and positive(timeout_ns) and timeout_ns <= 5 * SECOND
                and type(max_queries) is int and 0 < max_queries <= 32, '探针原总截止/单次5秒上限/次数边界无效')
        self.ledger, self.owner, self.creator = ledger, owner, creator
        self.registry, self.registry_parent = registry, registry_parent
        self.interpreter, self.interpreter_sha256 = Path(interpreter).resolve(), interpreter_sha256
        self.package_root, self.module_root = Path(package_root).resolve(), Path(module_root).resolve()
        self.package_files, self.module_files = dict(package_files), dict(module_files)
        self.root = Path(evidence_root).resolve()
        self._deadline_ns = deadline_ns
        self.enabled, self.timeout_ns, self.max_queries = enabled is True, timeout_ns, max_queries
        self.popen, self.handle_api, self.sleeper = popen or subprocess.Popen, handle_api or OriginalHandleApi(), sleeper
        self.nonce_factory = nonce_factory or (lambda: str(uuid.uuid4()))
        self.children = []
        self.active = False
        self.failed = False

    @property
    def deadline_ns(self):
        return self._deadline_ns

    def product_identity(self):
        require(self.owner.process is not None and self.owner.process is self.creator.process
                and self.owner.process_identity is not None and self.owner.process.poll() is None,
                '探针只能观察本客户端原Popen创建的存活产品')
        current = self.creator.inspect_created(self.owner.process)
        require(current == self.owner.process_identity, 'UIA探针前后产品原句柄身份改变')
        return current

    def sources(self):
        require(self.interpreter.is_file() and digest(self.interpreter.read_bytes()) == self.interpreter_sha256,
                '探针解释器与冻结摘要不符')
        require(len(self.package_files) == 77 and tree_hashes(self.package_root / 'windows_mcp', ignore_bytecode=True)
                == self.package_files, '探针UIA来源不是冻结77文件包')
        require({'async_product_client/probe_worker.py', 'async_product_client/native.py',
                 'async_product_client/core.py', 'async_product_client/product.py',
                 'async_product_client/events.py', 'async_product_client/race.py',
                 'async_product_client/file_dialog.py', 'async_product_client/commands.py',
                 'async_product_client/batch.py',
                 'async_product_client/__init__.py'} <= self.module_files.keys(),
                '探针模块冻结集合不完整')
        package_names = {p.relative_to(self.module_root).as_posix()
                         for p in (self.module_root / 'async_product_client').glob('*.py')}
        require(package_names <= self.module_files.keys(), '探针包存在未冻结的Python模块')
        actual = {name: digest((self.module_root / name).read_bytes()) for name in self.module_files}
        require(actual == self.module_files and not any((self.module_root / name).is_symlink() for name in self.module_files),
                '探针模块与冻结摘要不符或包含链接')

    async def inspect(self, hwnd, pid):
        return await self._query(hwnd, pid, kind='single-uia')

    async def observe(self):
        identity = self.owner.identity
        require(identity is not None, '整窗观察前必须已有精确主HWND绑定')
        return await self._query(identity.hwnd, identity.pid, kind='native-observation')

    async def _query(self, hwnd, pid, *, kind):
        self.ledger.desktop_allowed()
        require(self.enabled and not self.active and not self.failed
                and len(self.children) < self.max_queries and positive(hwnd), '探针禁用、正在执行、已有失败或次数耗尽')
        try:
            deadline = self.ledger.call_deadline(self.timeout_ns, deadline_ns=self.deadline_ns)
            info = self.product_identity()
            require(pid == info['pid'], '探针目标PID与原Popen不一致')
            self.sources()
            self.ledger.remaining(deadline)
        except BaseException:
            self.failed = True
            raise
        self.active = True
        child = None
        try:
            if not self.children:
                self.root.mkdir(parents=True, exist_ok=False)
            folder = self.root / f'{len(self.children) + 1:04}'
            folder.mkdir(exist_ok=False)
            request = dict(schema_version=1, context=asdict(self.ledger.context), nonce=self.nonce_factory(),
                           target=dict(info, hwnd=hwnd), query_kind=kind, deadline_ns=deadline,
                           created_mono_ns=self.ledger.clock.monotonic_ns(),
                           package_root=str(self.package_root), package_files=self.package_files,
                           module_root=str(self.module_root), module_files=self.module_files,
                           interpreter=str(self.interpreter), interpreter_sha256=self.interpreter_sha256,
                           readonly=True, input_calls=0)
            require(str(uuid.UUID(request['nonce'])) == request['nonce'], '探针nonce无效')
            request_path = folder / 'request.json'
            with request_path.open('x', encoding='utf-8') as out:
                json.dump(request, out, ensure_ascii=False, indent=2)
            stdout = (folder / 'stdout.log').open('xb')
            try: stderr = (folder / 'stderr.log').open('xb')
            except BaseException:
                stdout.close(); raise
            child = dict(process=None, identity=None, folder=str(folder), streams=[stdout, stderr],
                         request_sha256=digest(request_path.read_bytes()), request=request,
                         exit_code=None, accepted=False, outcome='unknown')
            self.children.append(child)
            self.ledger.desktop_allowed()
            self.product_identity()
            require(self.ledger.clock.monotonic_ns() < deadline, '创建探针前原截止已到')
            self.ledger.event('uia_probe_attempt', folder=str(folder), request_sha256=child['request_sha256'], hwnd=hwnd)
            self.ledger.remaining(deadline)
            # 直接创建并立即保存原Popen；不存在短命shell或中间启动器。
            child['process'] = self.popen([str(self.interpreter), '-B', '-X', 'utf8',
                                         str(self.module_root / 'async_product_client/probe_worker.py'), str(request_path)],
                                         cwd=str(folder), stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                         shell=False, close_fds=True)
            require(child['process'] is not None, '探针创建结果未知，不允许重试')
            if self.registry is not None:
                child['registry_key'] = f'uia-probe-{len(self.children)}'
                self.registry.created(child['registry_key'], child['process'], role='probe', parent=self.registry_parent)
            child['identity'] = self.handle_api.inspect(child['process'])
            require(child['identity'].get('pid') == child['process'].pid
                    and child['identity'].get('original_handle') is True
                    and positive(child['identity'].get('birth')) and positive(child['identity'].get('handle'))
                    and Path(child['identity'].get('image', '')).resolve() == self.interpreter,
                    '探针原Popen句柄身份未知')
            if self.registry is not None:
                self.registry.identified(child['registry_key'], child['process'], child['identity'])
            self.ledger.event('uia_probe_created', identity=child['identity'], original_popen=True)
            while True:
                self.ledger.desktop_allowed()
                require(self.ledger.clock.monotonic_ns() < deadline, 'UIA探针超出原截止，保留原Popen且不重试')
                code = child['process'].poll()
                if code is not None:
                    require(type(code) is int and code == child['process'].returncode, '探针原Popen退出证据不一致')
                    child['exit_code'] = code
                    child['outcome'] = 'exited'
                    self.close_streams(child)
                    if self.registry is not None:
                        self.registry.exited(child['registry_key'], child['process'], code)
                    self.ledger.event('uia_probe_exit', identity=child['identity'], original_popen=True, exit_code=code)
                    require(code == 0, '只读探针非0退出')
                    break
                remaining = (deadline - self.ledger.clock.monotonic_ns()) / SECOND
                require(remaining > .001, '探针原截止余量不足1毫秒')
                await asyncio.wait_for(self.sleeper(min(.1, remaining / 2)), timeout=min(1., remaining))
            self.product_identity()
            require(digest(request_path.read_bytes()) == child['request_sha256'], '探针执行期间request被改写')
            raw = (folder / 'result.json').read_bytes()
            result = decode_object(raw)
            require(result.get('nonce') == request['nonce'] and result.get('context') == request['context']
                    and result.get('request_sha256') == child['request_sha256']
                    and result.get('target') == request['target'] and result.get('child_pid') == child['process'].pid
                    and result.get('completed') is True and result.get('readonly') is True
                    and type(result.get('input_calls')) is int and result['input_calls'] == 0
                    and result.get('com_uninitialized') is True and result.get('dpi_restored') is True,
                    '只读探针结果身份/nonce/原请求/COM或DPI恢复证据不符')
            require(type(result.get('started_ns')) is int and type(result.get('finished_ns')) is int
                    and request['created_mono_ns'] <= result['started_ns'] <= result['finished_ns']
                    <= self.ledger.clock.monotonic_ns() < deadline, '探针时序越过原截止或时钟矛盾')
            require(result.get('query_kind', 'single-uia') == kind, '探针结果类型与原请求不符')
            if kind == 'native-observation':
                from .batch import validate_observation
                row = result.get('native')
                validate_observation(row, self.owner.identity)
            else:
                row = result.get('uia')
                require(isinstance(row, dict) and row.get('readonly') is True
                        and row.get('root', {}).get('pid') == pid and row['root'].get('hwnd') == hwnd,
                        '探针UIA根不属于精确请求窗口')
            self.sources()
            self.ledger.desktop_allowed()
            require(self.ledger.clock.monotonic_ns() < deadline, '最终核对耗时跨越探针原截止')
            child['result_sha256'] = digest(raw)
            self.ledger.event('uia_probe_accepted', identity=child['identity'], request_sha256=child['request_sha256'],
                              result_sha256=child['result_sha256'], original_popen=True)
            self.ledger.remaining(deadline)
            child['accepted'] = True
            return row
        except BaseException:
            self.failed = True
            if child is not None:
                stop_path = Path(child['folder']) / 'stop-requested'
                with stop_path.open('xb') as out: out.write(b'parent-failed\n')
                child['stop_requested'] = True
            if child is not None and child['process'] is None:
                self.close_streams(child)
            raise
        finally:
            self.active = False

    @staticmethod
    def close_streams(child):
        for stream in child['streams']: stream.close()

    def reap(self):
        """失败后仅本地poll原Popen；不读取新UIA结果、不解除失败或提升原结论。"""
        require(not self.active, '不能同时执行探针与本地退出核对')
        for child in self.children:
            if child['process'] is not None and child['exit_code'] is None:
                code = child['process'].poll()
                if code is not None:
                    require(type(code) is int and code == child['process'].returncode, '原探针退出证据未知')
                    child.update(exit_code=code, outcome='exited')
                    self.close_streams(child)
                    if self.registry is not None and 'registry_key' in child:
                        self.registry.exited(child['registry_key'], child['process'], code)
                    self.ledger.event('uia_probe_reaped', original_popen=True, pid=child['process'].pid,
                                      exit_code=code, accepted=child['accepted'])
        return [dict(pid=child['process'].pid if child['process'] else None, exit_code=child['exit_code'],
                     accepted=child['accepted'], outcome=child['outcome']) for child in self.children]
