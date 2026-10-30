"""冻结依赖加载的无GUI驱动；不导入windows_mcp、COM/UIA或输入模块。"""
import importlib
import importlib.metadata
import json
from pathlib import Path
import sys

from async_product_client.core import require
from async_product_client.runtime import write_once


async def run(runtime, configuration):
    require(set(configuration) == {'dependency_root'}, '无GUI依赖核验配置不符')
    root = Path(configuration['dependency_root']).resolve()
    names = ('mcp.types', 'pydantic', 'jsonschema', 'anyio', 'PIL.Image', 'numpy')
    modules = {}
    for name in names:
        module = importlib.import_module(name)
        path = Path(module.__file__).resolve()
        require(path.is_relative_to(root), '实际依赖导入来源不在冻结副本：' + name)
        modules[name] = str(path)
    require('windows_mcp' not in sys.modules and 'pythoncom' not in sys.modules and 'comtypes' not in sys.modules,
            '无GUI依赖核验意外加载控制包或COM')
    row = dict(pid=runtime.relay.self_identity['pid'], executable=sys.executable,
               isolated=sys.flags.isolated, no_site=sys.flags.no_site, modules=modules,
               versions={name: importlib.metadata.version(name) for name in ('mcp', 'pydantic', 'jsonschema', 'anyio', 'pillow', 'numpy')},
               control_package_loaded=False, actual_uia_com_probes=0, desktop_requests=0, product_launches=0,
               ready_for_live=False)
    write_once(runtime.root / 'dependency-result.json', json.dumps(row, ensure_ascii=False).encode('utf-8'))
    return 0
