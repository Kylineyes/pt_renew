"""独立UIA对象兼容性子入口；只创建原自动化单例，不枚举或查询桌面。"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))
from async_product_client.core import Context, digest, require
from async_product_client.events import decode_object
from async_product_client.product import tree_hashes


def create_object(package):
    require('windows_mcp' not in sys.modules, 'UIA对象只能从本次冻结77文件包首次导入')
    sys.path.insert(0, str(package))
    import windows_mcp.uia as uia
    import windows_mcp.uia.core as core
    require(Path(uia.__file__).resolve() == package / 'windows_mcp/uia/__init__.py'
            and Path(core.__file__).resolve() == package / 'windows_mcp/uia/core.py', '实际UIA导入来源不符')
    # events.py类定义应已创建原单例；不再次调用instance，不触发查询或事件订阅。
    client = core._AutomationClient._instance
    require(client is not None and client.IUIAutomation is not None and client.ViewWalker is not None,
            '原UIA自动化对象或原RawViewWalker未创建')
    return dict(uia_source=str(Path(uia.__file__).resolve()), core_source=str(Path(core.__file__).resolve()),
                automation_type=type(client.IUIAutomation).__name__, walker_type=type(client.ViewWalker).__name__,
                object_created=True, object_creations=1, desktop_queries=0, event_subscriptions=0)


def execute(request_path, *, load=create_object, clock=time.monotonic_ns):
    path = Path(request_path).resolve(); raw = path.read_bytes(); request = decode_object(raw)
    result = dict(schema_version=1, request_sha256=digest(raw), nonce=request['nonce'], context=request['context'],
                  pid=os.getpid(), started_ns=clock(), completed=False, desktop_queries=0, event_subscriptions=0,
                  product_launches=0, control_services=0, object_created=False, ready_for_live=False)
    timings = {}
    def checkpoint():
        require(clock() < request['deadline_ns'] and not (path.parent / 'stop-requested').exists(),
                '真实UIA对象核验超过原5秒截止或父已要求停止')
    try:
        require(request.get('purpose') == 'uia-object-only' and request.get('enabled') is True
                and request.get('max_object_creations') == 1 and request.get('max_desktop_queries') == 0,
                'UIA对象核验未启用或范围不符')
        Context(**request['context']); checkpoint()
        require(Path(sys.executable).resolve() == Path(request['interpreter']).resolve()
                and digest(Path(sys.executable).read_bytes()) == request['interpreter_sha256'], '基础解释器摘要不符')
        package = Path(request['package_root']).resolve()
        require(tree_hashes(TOOLS, ignore_bytecode=True) == request['module_files']
                and len(request['package_files']) == 77
                and tree_hashes(package / 'windows_mcp', ignore_bytecode=True) == request['package_files'],
                '完整源码或77文件包摘要改变')
        timings['sources_verified_ns'] = clock(); checkpoint()
        from async_product_client.probe_workspace import ProbeWorkspace
        from async_product_client.com_apartment import ApartmentTrace
        from async_product_client.uia_object import validate_uia_object_apartment
        workspace = ProbeWorkspace(request['python_environment'], path.parent / 'runtime', readonly_roots=(TOOLS, package))
        workspace.prepare(); timings['workspace_prepared_ns'] = clock(); checkpoint()
        with workspace:
            trace = ApartmentTrace(checkpoint=checkpoint)
            try:
                with trace:
                    checkpoint()
                    observed = load(package)
                    require(observed.get('object_created') is True and observed.get('object_creations') == 1
                            and observed.get('desktop_queries') == observed.get('event_subscriptions') == 0,
                            'UIA对象核验混入查询/订阅或对象数量未知')
                    result.update(observed); timings['object_created_ns'] = clock(); checkpoint()
            finally: result['com_apartment'] = trace.report()
            validate_uia_object_apartment(result['com_apartment']); checkpoint()
        timings['cleanup_verified_ns'] = clock(); checkpoint()
        require(path.read_bytes() == raw, '对象核验原请求被修改')
        result['completed'] = True
    except BaseException as error:
        result.update(error=type(error).__name__, reason=str(error))
    result.update(timings=timings, finished_ns=clock())
    with (path.parent / 'object-result.json').open('x', encoding='utf-8') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.flush(); os.fsync(output.fileno())
    return 0 if result['completed'] else 1


if __name__ == '__main__':
    require(len(sys.argv) == 2, '需要一个本轮已批准UIA对象请求')
    raise SystemExit(execute(sys.argv[1]))
