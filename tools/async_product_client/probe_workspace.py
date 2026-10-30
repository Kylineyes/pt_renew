"""独立探针的私有依赖/缓存工作副本；冻结来源及可执行字节只读。"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

from .core import require
from .probe_environment import freeze_probe_environment, validate_probe_environment
from .python_environment import environment


class ProbeWorkspace:
    def __init__(self, profile, root, *, readonly_roots=()):
        self.source = validate_probe_environment(environment(profile))
        self.root = Path(root).resolve()
        self.readonly_roots = tuple(Path(path).resolve() for path in readonly_roots)
        self.private = None
        self.previous_temp = None

    def prepare(self):
        self.root.mkdir(exist_ok=False)
        self.private = environment(freeze_probe_environment(self.source.__dict__, self.root / 'dependencies'))
        (self.root / 'temp').mkdir()
        self.readonly_roots += (Path(self.source.root).resolve(), Path(self.private.root).resolve())
        return self.private

    def audit(self, event, args):
        paths = []
        if event == 'open':
            path, mode, flags = args
            writing = (isinstance(mode, str) and any(letter in mode for letter in ('w', 'a', 'x', '+'))
                       or isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writing: paths.append(path)
        elif event in ('os.remove', 'os.rmdir', 'os.mkdir', 'os.chmod', 'os.truncate'):
            paths.append(args[0])
        elif event in ('os.rename', 'os.link', 'os.symlink'):
            paths.extend(args[:2])
        for value in paths:
            if isinstance(value, (str, bytes, os.PathLike)):
                path = Path(os.fsdecode(value)).resolve()
                require(not any(path == root or path.is_relative_to(root) for root in self.readonly_roots),
                        '探针禁止修改冻结来源或私有可执行依赖；缓存损坏不能自动重建')

    def __enter__(self):
        require(self.private is not None, '探针私有依赖尚未准备')
        self.previous_temp = tempfile.tempdir
        tempfile.tempdir = str(self.root / 'temp')
        # 仅在独立子进程安装，随子进程退出；不修改全局安装、包字节或原锁等待实现。
        sys.addaudithook(self.audit)
        try:
            self.private.activate()
            return self
        except BaseException:
            tempfile.tempdir = self.previous_temp
            raise

    def verify(self):
        self.source.verify()
        self.private.verify()

    def __exit__(self, kind, error, traceback):
        tempfile.tempdir = self.previous_temp
        self.verify()
