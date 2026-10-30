"""单次真实UIA对象核验的原Popen所有者；默认禁用，超时保留对象。"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import uuid

from .com_apartment import validate_com_report
from .core import SECOND, digest, positive, require
from .events import decode_object
from .process import OriginalHandleApi
from .product import tree_hashes
from .probe_environment import validate_probe_environment
from .python_environment import environment


def validate_uia_object_apartment(row):
    validate_com_report(row)
    counts = {name: sum(call['api'] == name for call in row['calls'])
              for name in ('CoInitializeEx', 'CoInitialize', 'CoUninitialize')}
    require(counts == dict(CoInitializeEx=2, CoInitialize=1, CoUninitialize=3),
            '真实UIA对象必须有显式/自动/原UIA三次成功初始化和三次释放')
    return row


class UiaObjectOwner:
    def __init__(self, ledger, root, *, enabled=False, popen=None, handles=None):
        self.ledger, self.root, self.enabled = ledger, Path(root).resolve(), enabled is True
        self.popen, self.handles = popen or subprocess.Popen, handles or OriginalHandleApi()
        self.used = False
        self.process = self.identity = self.request = None
        self.streams = []
        self.exit_code = None
        self.accepted = False
        self.deadline = None

    def sources(self, materials):
        require(set(materials) == {'interpreter', 'interpreter_sha256', 'module_root', 'module_files',
                                  'package_root', 'package_files', 'python_environment'}, 'UIA核验材料字段不符')
        interpreter = Path(materials['interpreter']).resolve()
        require(not (interpreter.parent.parent / 'pyvenv.cfg').exists()
                and digest(interpreter.read_bytes()) == materials['interpreter_sha256'], 'UIA核验必须直接使用冻结基础解释器')
        root = Path(materials['module_root']).resolve()
        require('probe_async_uia_object.py' in materials['module_files']
                and tree_hashes(root, ignore_bytecode=True) == materials['module_files'], 'UIA核验完整模块集合不符')
        require(len(materials['package_files']) == 77
                and tree_hashes(Path(materials['package_root']) / 'windows_mcp', ignore_bytecode=True) == materials['package_files'],
                'UIA核验完整77文件包不符')
        validate_probe_environment(environment(materials['python_environment']))
        return interpreter, root

    def start(self, ident, parent, *, materials):
        deadline = min(self.ledger.current_deadline_ns, self.ledger.clock.monotonic_ns() + 5 * SECOND)
        with self.ledger.operation(ident, parent, deadline_ns=deadline):
            require(self.enabled and not self.used and not self.root.exists(), 'UIA对象核验禁用、机会已消费或证据目录已存在')
            self.used = True; self.deadline = deadline
            interpreter, modules = self.sources(materials)
            self.root.mkdir(parents=True, exist_ok=False)
            self.request = dict(materials, schema_version=1, purpose='uia-object-only', enabled=True,
                                context=asdict(self.ledger.context), nonce=str(uuid.uuid4()),
                                max_object_creations=1, max_desktop_queries=0, deadline_ns=deadline,
                                created_ns=self.ledger.clock.monotonic_ns())
            with (self.root / 'request.json').open('x', encoding='utf-8') as output:
                json.dump(self.request, output, ensure_ascii=False, indent=2)
            try:
                for name in ('stdout.log', 'stderr.log'): self.streams.append((self.root / name).open('xb'))
                self.ledger.desktop_allowed()
                self.process = self.popen([str(interpreter), '-I', '-S', '-B', '-X', 'utf8',
                                           str(modules / 'probe_async_uia_object.py'), str(self.root / 'request.json')],
                                          cwd=self.root, stdin=subprocess.DEVNULL, stdout=self.streams[0], stderr=self.streams[1],
                                          shell=False, close_fds=True)
                require(self.process is not None, 'UIA对象创建结果未知，不允许再次创建')
                self.identity = self.handles.inspect(self.process)
                require(self.identity.get('pid') == self.process.pid and self.identity.get('original_handle') is True
                        and positive(self.identity.get('birth')) and positive(self.identity.get('handle'))
                        and Path(self.identity.get('image', '')).resolve() == interpreter,
                        'UIA对象子进程原创建身份不符')
            except BaseException:
                if self.process is None: self.close_streams()
                raise
        return self.identity

    def poll(self):
        require(self.process is not None, '尚无本轮原Popen')
        code = self.process.poll()
        if code is not None:
            require(type(code) is int and code == self.process.returncode, '原UIA核验退出码未知')
            self.exit_code = code; self.close_streams()
        return code

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            path = self.root / 'stop-requested'
            if not path.exists():
                with path.open('xb') as output: output.write(b'parent-original-deadline\n')

    def finish(self, ident, parent, *, materials):
        with self.ledger.operation(ident, parent, deadline_ns=self.deadline):
            require(self.enabled and self.used and self.process is not None and not self.accepted,
                    'UIA核验未启动或结果已消费')
            require(self.poll() == 0 and self.identity is not None, '原UIA核验尚未退出0或缺创建时身份')
            request_raw = (self.root / 'request.json').read_bytes()
            require(decode_object(request_raw) == self.request, 'UIA核验原请求被修改')
            result = decode_object((self.root / 'object-result.json').read_bytes())
            require(result.get('completed') is True and result.get('pid') == self.process.pid
                    and result.get('context') == asdict(self.ledger.context) and result.get('nonce') == self.request['nonce']
                    and result.get('request_sha256') == digest((self.root / 'request.json').read_bytes())
                    and result.get('object_created') is True and result.get('object_creations') == 1
                    and result.get('desktop_queries') == result.get('event_subscriptions') == 0,
                    '原UIA对象结果/上下文/范围不符')
            require(type(result.get('started_ns')) is int and type(result.get('finished_ns')) is int
                    and self.request['created_ns'] <= result['started_ns'] <= result['finished_ns']
                    <= self.ledger.clock.monotonic_ns() < self.deadline, 'UIA对象核验原时钟或截止不符')
            validate_uia_object_apartment(result.get('com_apartment'))
            self.sources(materials)
            self.ledger.desktop_allowed()
            self.ledger.event('uia_object_verified', original_identity=self.identity, original_exit=0, result=result)
        self.accepted = True
        return result

    def close_streams(self):
        for stream in self.streams: stream.close()
