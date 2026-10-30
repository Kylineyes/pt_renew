"""仅测隔离探针依赖导入与COM初始化；不创建自动化对象、不访问桌面。"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))
from async_product_client.core import digest, require
from async_product_client.events import decode_object
from async_product_client.product import tree_hashes


def execute(request_path):
    path = Path(request_path).resolve()
    request_raw = path.read_bytes(); request = decode_object(request_raw)
    result = dict(schema_version=1, request_sha256=digest(request_raw), pid=os.getpid(), completed=False,
                  desktop_queries=0, control_services=0, product_launches=0, uia_object_created=False,
                  started_ns=time.monotonic_ns(), ready_for_live=False)
    timings = {}
    def checkpoint():
        require(time.monotonic_ns() < request['deadline_ns'] and not (path.parent / 'stop-requested').exists(),
                '依赖导入核验超过原5秒截止或父已要求停止')
    try:
        require(request.get('purpose') == 'probe-import-only' and request.get('schema_version') == 1,
                '只支持新建依赖导入核验请求')
        checkpoint()
        require(Path(sys.executable).resolve() == Path(request['interpreter']).resolve()
                and digest(Path(sys.executable).read_bytes()) == request['interpreter_sha256'], '基础解释器不符')
        require(tree_hashes(TOOLS, ignore_bytecode=True) == request['module_files']
                and tree_hashes(Path(request['package_root']) / 'windows_mcp', ignore_bytecode=True) == request['package_files'],
                '核验源码或完整77文件包改变')
        timings['sources_verified_ns'] = time.monotonic_ns()
        from async_product_client.probe_workspace import ProbeWorkspace
        from async_product_client.com_apartment import ApartmentTrace, validate_com_report
        workspace = ProbeWorkspace(request['python_environment'], path.parent / 'runtime',
                                   readonly_roots=(TOOLS, request['package_root']))
        workspace.prepare(); checkpoint()
        timings['workspace_prepared_ns'] = time.monotonic_ns()
        with workspace:
            timings['dependencies_activated_ns'] = time.monotonic_ns()
            trace = ApartmentTrace(checkpoint=checkpoint)
            try:
                with trace:
                    import comtypes
                    import comtypes.client
                    checkpoint()
                    require(comtypes.client.gen_dir == str(Path(workspace.private.root) / 'comtypes/gen'),
                            'comtypes缓存目录不是本次私有副本')
                    require('windows_mcp' not in sys.modules and 'numpy' not in sys.modules and 'pythoncom' not in sys.modules,
                            '导入核验意外加载控制包或额外依赖')
                    result['comtypes_file'] = comtypes.__file__
                    result['comtypes_version'] = comtypes.__version__
                    timings['comtypes_imported_ns'] = time.monotonic_ns()
            finally: result['com_apartment'] = trace.report()
            validate_com_report(result['com_apartment'])
            checkpoint()
        timings['workspace_verified_ns'] = time.monotonic_ns()
        checkpoint()
        result['completed'] = True
    except BaseException as error:
        result.update(error=type(error).__name__, reason=str(error))
    result.update(timings=timings, finished_ns=time.monotonic_ns())
    with (path.parent / 'import-result.json').open('x', encoding='utf-8') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.flush(); os.fsync(output.fileno())
    return 0 if result['completed'] else 1


if __name__ == '__main__':
    require(len(sys.argv) == 2, '需要一个全新离线导入请求文件')
    raise SystemExit(execute(sys.argv[1]))
