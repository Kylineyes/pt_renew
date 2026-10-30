"""创建者的实际启动、原Popen持有及报告交换；默认禁用，不从PID接管。"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import subprocess

from .core import SECOND, digest, positive, require
from .events import decode_object
from .lifecycle import ProcessRegistry
from .process import OriginalHandleApi
from .product import original_wait, tree_hashes
from .witness import CreatorRelay, RootWitness


def write_once(path, raw):
    """发布为新文件；读取者只接收带原摘要的完整字节，不替换旧报告。"""
    path = Path(path)
    staging = path.with_name(path.name + '.publishing')
    with staging.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    # 硬链接只在目标不存在时原子发布完整文件；读者不会遇到半份绑定或报告。
    os.link(staging, path)
    staging.unlink()


@dataclass(frozen=True)
class FrozenProgram:
    interpreter: str
    interpreter_sha256: str
    root: str
    files: tuple
    entry: str
    python_environment: dict | None = None

    def verify(self):
        interpreter, root = Path(self.interpreter).resolve(), Path(self.root).resolve()
        require(interpreter.is_file() and not Path(self.interpreter).is_symlink()
                and digest(interpreter.read_bytes()) == self.interpreter_sha256, '启动解释器摘要不符')
        require(not (interpreter.parent.parent / 'pyvenv.cfg').is_file(),
                '虚拟环境重定向器会创建非原Popen执行进程，必须使用基础解释器加冻结依赖')
        files = dict(self.files)
        require(len(files) == len(self.files) and self.entry in files
                and 'async_product_client/runtime_worker.py' in files
                and tree_hashes(root, ignore_bytecode=True) == files, '启动模块完整冻结集合不符')
        entry = root / self.entry
        require(entry.resolve().is_relative_to(root) and entry.suffix == '.py', '冻结入口越界或类型无效')
        from .python_environment import environment
        dependencies = environment(self.python_environment)
        if dependencies is not None: dependencies.verify()
        return interpreter, root


class CreatorRuntime:
    """每个实际创建者各持一个实例；服务/客户端/监督器报告均由其原父进程验收。"""

    def __init__(self, ledger, evidence_root, *, self_identity=None, role=None, required_roles=(),
                 enabled=False, popen=None, handle_api=None):
        self.ledger, self.root = ledger, Path(evidence_root).resolve()
        self.enabled = enabled is True
        self.popen, self.handles = popen or subprocess.Popen, handle_api or OriginalHandleApi()
        self.registry = ProcessRegistry(ledger, required_roles=required_roles)
        self.relay = (CreatorRelay(ledger, self.registry, self_identity=self_identity, role=role)
                      if self_identity is not None else None)
        self.children = {}
        self.published = False

    def spawn(self, key, *, role, program, configuration=None, pipes=False):
        self.ledger.desktop_allowed()
        require(self.enabled and not self.published and not self.ledger.cleanup_active
                and key not in self.children and key not in self.registry.entries and key not in self.registry.gaps
                and role in ('supervisor', 'client', 'service') and type(program) is FrozenProgram,
                '创建者启动禁用、机会已消费或角色/冻结入口无效')
        deadline = self.ledger.call_deadline(35 * SECOND)
        interpreter, module_root = program.verify()
        # 消费机会先于持久化及Popen；任一失败不得复用此键重试。
        child = dict(process=None, identity=None, streams=[], report=None, outcome='unknown')
        self.children[key] = child
        self.root.mkdir(parents=True, exist_ok=True)
        folder = self.root / key
        require(folder.parent == self.root, '创建者证据键不能包含路径')
        folder.mkdir(exist_ok=False); child['folder'] = folder
        plan = dict(schema_version=1, context=asdict(self.ledger.context), role=role,
                    startup_deadline_ns=deadline,
                    diagnostic_deadline_ns=self.ledger.diagnostic_deadline_ns,
                    cleanup_deadline_ns=self.ledger.cleanup_deadline_ns,
                    program=asdict(program), configuration=configuration or {}, enabled=True)
        raw = json.dumps(plan, ensure_ascii=False, sort_keys=True).encode('utf-8')
        write_once(folder / 'launch.json', raw)
        child['launch_sha256'] = digest(raw)
        try:
            for name in (('stderr.log',) if pipes else ('stdout.log', 'stderr.log')):
                child['streams'].append((folder / name).open('xb'))
            isolation = ['-I', '-S'] if program.python_environment is not None else []
            command = [str(interpreter), *isolation, '-B', '-X', 'utf8',
                       str(module_root / 'async_product_client/runtime_worker.py'),
                       str(folder / 'launch.json'), child['launch_sha256']]
            self.ledger.event('creator_launch_attempt', key=key, role=role, command=command)
            self.ledger.remaining(deadline)
            child['process'] = self.popen(command, cwd=str(folder), stdin=subprocess.PIPE if pipes else subprocess.DEVNULL,
                                          stdout=subprocess.PIPE if pipes else child['streams'][0],
                                          stderr=child['streams'][-1], shell=False, close_fds=True)
            require(child['process'] is not None, '创建结果未知，保留启动机会')
            self.registry.created(key, child['process'], role=role)
            child['identity'] = self.handles.inspect(child['process'])
            self.registry.identified(key, child['process'], child['identity'])
            require(Path(child['identity']['image']).resolve() == interpreter, '原子进程映像与冻结解释器不符')
            self.ledger.remaining(deadline)
            # 子进程先等待；只有父保存并核对原Popen后才发布绑定，不另启短命握手程序。
            binding = dict(context=asdict(self.ledger.context), identity=child['identity'], launch_sha256=digest(raw))
            write_once(folder / 'parent-binding.json', json.dumps(binding, ensure_ascii=False).encode('utf-8'))
            self.ledger.remaining(deadline)
            child['outcome'] = 'running'
            return child['process']
        except BaseException:
            if child['process'] is None:
                self.close_streams(child)
            raise

    @staticmethod
    def close_streams(child):
        for stream in child['streams']: stream.close()

    def discovered(self, key, *, pid, birth, parent):
        # 发现清单不能凭一份子报告自动消除；没有原对象就是永久缺口。
        self.registry.discovered(key, pid=pid, birth=birth, parent=parent)

    async def wait_child(self, key, *, waiter=original_wait, wait_ns=5 * SECOND):
        require(key in self.children and positive(wait_ns) and wait_ns <= 5 * SECOND, '未知原子进程或等待上限无效')
        child = self.children[key]; process = child['process']
        require(process is not None, '没有原Popen，不能按PID补建退出证明')
        deadline = min(self.ledger.cleanup_deadline_ns, self.ledger.clock.monotonic_ns() + wait_ns)
        remaining = (deadline - self.ledger.clock.monotonic_ns()) / SECOND
        require(remaining > 0, '原创建者收尾截止已到')
        code = await asyncio.wait_for(waiter(process, remaining), remaining)
        self.registry.exited(key, process, code)
        child['outcome'] = 'exited'
        self.close_streams(child)
        require(self.ledger.clock.monotonic_ns() < deadline and type(code) is int and code == 0,
                '原子进程未在原截止内正常退出0')
        return code

    def accept_report(self, key):
        require(self.relay is not None and key in self.children, '最外层或未知创建者不能替子进程发布报告')
        child = self.children[key]
        require(child['identity'] is not None and child['process'].poll() == 0, '子报告之前须核验创建时身份及原退出0')
        folder = child['folder']
        raw = (folder / 'creator-report.json').read_bytes()
        receipt = decode_object((folder / 'creator-report-receipt.json').read_bytes())
        require(receipt == dict(sha256=digest(raw), launch_sha256=child['launch_sha256']), '子报告发布回执摘要不符')
        self.relay.accept_child(key, raw)
        child['report'] = raw
        return raw

    def publish(self, *, launch_sha256):
        require(not self.published and self.relay is not None, '创建者不能重复发布或缺少上层身份绑定')
        self.published = True
        raw = self.relay.seal()
        self.root.mkdir(parents=True, exist_ok=True)
        write_once(self.root / 'creator-report.json', raw)
        receipt = dict(sha256=digest(raw), launch_sha256=launch_sha256)
        write_once(self.root / 'creator-report-receipt.json', json.dumps(receipt).encode('utf-8'))
        return raw

    def root_witness(self, key):
        child = self.children[key]
        require(self.relay is None and child['identity'] is not None, '根见证缺少创建时原身份')
        return RootWitness(context=self.ledger.context, process=child['process'], identity=child['identity'],
                           role=self.registry.entries[key]['role'])

    async def drain_after_failure(self):
        """失败后只保留原对象及本地退出观察；900秒后仍未知则继续被动持有，绝不新发控制请求。"""
        require(self.ledger.failed is not None and not self.ledger.busy, '仅失败终态可进入被动原对象持有')
        pending = [row for row in self.registry.entries.values() if row['process'].poll() is None]
        if not pending: return self.poll()
        write_once(self.root / 'creator-pending.json', json.dumps(self.registry.report(), ensure_ascii=False).encode('utf-8'))
        deadline_recorded = False
        while pending:
            # 仅所有产品/探针/下层创建者已退出后，向本创建者直接持有的服务发送一次正常EOF。
            nonservices = [row for row in pending if row['role'] != 'service']
            if not nonservices:
                for child in self.children.values():
                    process = child['process']
                    if process is not None and process.poll() is None and process.stdin is not None and not process.stdin.closed:
                        process.stdin.close()
            if self.ledger.clock.monotonic_ns() >= self.ledger.cleanup_deadline_ns and not deadline_recorded:
                write_once(self.root / 'creator-deadline-unknown.json',
                           json.dumps(self.registry.report(), ensure_ascii=False).encode('utf-8'))
                deadline_recorded = True
            await asyncio.sleep(.1)
            try: self.poll()
            except BaseException:
                # 外部审计写入失败不能让创建者丢弃尚存活的原对象。
                pass
            pending = [row for row in self.registry.entries.values() if row['process'].poll() is None]
        return self.registry.report()

    def poll(self):
        result = self.registry.poll()
        for child in self.children.values():
            if child['process'] is not None and child['process'].poll() is not None:
                child['outcome'] = 'exited'; self.close_streams(child)
        return result
