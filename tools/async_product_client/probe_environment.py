"""仅复制冻结依赖中的完整comtypes包，保留生成包装；无COM或桌面调用。"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import shutil

from .core import digest, require
from .python_environment import PythonEnvironment, environment

GENERATED = frozenset(('comtypes/gen/__init__.py', 'comtypes/gen/UIAutomationClient.py',
                       'comtypes/gen/_944DE083_8FB8_45CF_BCB7_C477ACB2F897_0_1_0.py',
                       'comtypes/gen/stdole.py', 'comtypes/gen/_00020430_0000_0000_C000_000000000046_0_2_0.py'))


def validate_probe_environment(profile):
    require(type(profile) is PythonEnvironment and profile.files and GENERATED <= profile.files.keys()
            and all(name.startswith('comtypes/') for name in profile.files),
            '探针依赖必须为完整comtypes包及已冻结的UIA/stdole包装')
    profile.verify()
    return profile


def freeze_probe_environment(source, destination):
    """离线完整复制同版本包；不按一次导入记录删文件，不修改源依赖。"""
    profile = environment(source)
    require(profile is not None, '缺少原完整Python依赖清单')
    profile.verify()
    files = {name: sha for name, sha in profile.files.items() if name.startswith('comtypes/')}
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    require(GENERATED <= files.keys(), '完整依赖缺少已生成UIAutomation/stdole包装')
    for name, sha in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(profile.root) / name, target)
        require(digest(target.read_bytes()) == sha, '复制时comtypes依赖改变')
    profile.verify()
    result = PythonEnvironment(str(destination), files, profile.version)
    validate_probe_environment(result)
    return asdict(result)
