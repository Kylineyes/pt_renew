"""基础Python加完整冻结依赖；不经虚拟环境重定向器，不执行任意.pth代码。"""
from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import sys
from typing import ClassVar

from .core import require, valid_hash
from .product import tree_hashes


@dataclass(frozen=True)
class PythonEnvironment:
    root: str
    files: dict
    version: tuple

    _active: ClassVar = None
    _dll_handles: ClassVar[list] = []

    def verify(self):
        root = Path(self.root)
        require(root.is_absolute() and root.is_dir() and not root.is_symlink() and not root.is_junction(),
                '冻结依赖目录必须是独立绝对目录')
        require(tuple(self.version) == sys.version_info[:3] and self.files
                and all(isinstance(name, str) and valid_hash(sha) for name, sha in self.files.items()),
                '冻结依赖Python版本或完整摘要无效')
        require(tree_hashes(root, ignore_bytecode=True) == self.files, '完整依赖集合或摘要改变')
        paths, bootstrap = [root.resolve()], False
        for name in sorted(self.files):
            if '/' in name or not name.endswith('.pth'): continue
            for line in (root / name).read_text(encoding='utf-8-sig').splitlines():
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.startswith(('import ', 'import\t')):
                    require(line == 'import pywin32_bootstrap' and not bootstrap,
                            '冻结依赖.pth含未支持的执行行或重复bootstrap')
                    bootstrap = True
                else:
                    path = (root / line).resolve()
                    require(path.is_relative_to(root.resolve()) and path.is_dir(), '.pth依赖路径越界或不存在')
                    paths.append(path)
        if bootstrap:
            require('win32/lib/pywin32_bootstrap.py' in self.files and (root / 'pywin32_system32').is_dir(),
                    'pywin32启动模块或DLL目录未冻结')
        return paths, bootstrap

    def activate(self):
        paths, bootstrap = self.verify()
        identity = (str(Path(self.root).resolve()), tuple(sorted(self.files.items())), tuple(self.version))
        require(type(self)._active is None or type(self)._active == identity, '同一创建者禁止切换冻结依赖环境')
        if type(self)._active is not None: return
        # -I -S启动后只允许stdlib、冻结tools及本依赖；禁止用户site和继承PYTHONPATH。
        require(sys.flags.isolated == 1 and sys.flags.no_site == 1, '冻结依赖须由基础解释器以-I -S启动')
        for path in reversed(paths):
            if str(path) not in sys.path: sys.path.insert(0, str(path))
        if bootstrap:
            handle = os.add_dll_directory(str(Path(self.root) / 'pywin32_system32'))
            type(self)._dll_handles.append(handle)
            module = importlib.import_module('pywin32_bootstrap')
            require(Path(module.__file__).resolve() == Path(self.root).resolve() / 'win32/lib/pywin32_bootstrap.py',
                    'pywin32实际bootstrap不属于冻结副本')
        type(self)._active = identity


def environment(value):
    if value is None: return None
    require(isinstance(value, dict) and set(value) == {'root', 'files', 'version'}, '冻结Python依赖协议不符')
    return PythonEnvironment(**value)
