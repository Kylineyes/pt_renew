"""独立STA只读UIA探针；仅由绑定原Popen的父客户端以冻结request启动。"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
import time

# 以绝对脚本执行时只加入冻结tools目录，不能依赖当前目录下的同名包。
TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))
from async_product_client.core import digest, require
from async_product_client.events import decode_object
from async_product_client.product import tree_hashes


def execute(request_path, *, query=None, clock=time.monotonic_ns):
    path = Path(request_path).resolve()
    require(path.is_file() and not path.is_symlink(), '只读探针request不存在或是链接')
    require(not (path.parent / 'result.json').exists(), '探针结果已经存在，禁止重复执行')
    raw = path.read_bytes()
    request = decode_object(raw)
    started = clock()
    result = dict(schema_version=1, context=request['context'], nonce=request['nonce'],
                  target=request['target'], query_kind=request.get('query_kind', 'single-uia'),
                  child_pid=os.getpid(), request_sha256=digest(raw),
                  started_ns=started, completed=False, readonly=True, input_calls=0,
                  com_uninitialized=False, dpi_restored=False)
    try:
        require(request.get('schema_version') == 1 and request.get('readonly') is True
                and type(request.get('input_calls')) is int and request['input_calls'] == 0
                and type(request.get('created_mono_ns')) is int and type(request.get('deadline_ns')) is int
                and request['created_mono_ns'] <= started < request['deadline_ns'], '探针请求协议/原截止无效')
        require(Path(request['interpreter']).resolve() == Path(sys.executable).resolve()
                and digest(Path(sys.executable).read_bytes()) == request['interpreter_sha256'], '探针解释器未冻结')
        module_root = Path(request['module_root']).resolve()
        require(module_root == TOOLS and request.get('module_files')
                and all(digest((module_root / name).read_bytes()) == sha for name, sha in request['module_files'].items()),
                '探针冻结模块改变')
        package = Path(request['package_root']).resolve()
        require(len(request['package_files']) == 77
                and tree_hashes(package / 'windows_mcp', ignore_bytecode=True) == request['package_files'],
                '探针冻结UIA包改变')
        require(clock() < request['deadline_ns'], '加载UIA之前已经超过原截止')
        def checkpoint():
            require(not (path.parent / 'stop-requested').exists() and clock() < request['deadline_ns'],
                    '父已请求停止或探针原截止已到，禁止后续UIA/native查询')
        checkpoint()
        target = request['target']
        # query仅供离线测试注入；正式入口固定run_uia，不能从request选择可执行代码。
        kind = request.get('query_kind', 'single-uia')
        require(kind in ('single-uia', 'native-observation'), '探针观察类型未冻结')
        queried = query(target, package) if query is not None else run_uia(target, package, checkpoint=checkpoint, kind=kind)
        result.update(queried)
        require(result.get('com_uninitialized') is True and result.get('dpi_restored') is True,
                'COM/DPI恢复证据不完整')
        if kind == 'single-uia':
            require(result.get('uia', {}).get('readonly') is True, '只读UIA证据不完整')
        else:
            from async_product_client.batch import validate_observation
            from async_product_client.core import Identity
            validate_observation(result.get('native'), Identity(target['pid'], target['birth'], target['image'], target['hwnd']))
        checkpoint()
        require(path.read_bytes() == raw, '探针执行后请求改变')
        result['completed'] = True
    except BaseException as error:
        result.update(completed=False, error=type(error).__name__, reason=str(error))
    result['finished_ns'] = clock()
    with (path.parent / 'result.json').open('x', encoding='utf-8') as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.flush(); os.fsync(out.fileno())
    return 0 if result['completed'] else 1


def run_uia(target, package, *, checkpoint, kind='single-uia'):
    require(os.name == 'nt', 'COM探针仅支持Windows')
    from async_product_client.native import ReadOnlyUia, ReadOnlyWin32
    native = ReadOnlyWin32()
    user = native.load()
    ole = ctypes.OleDLL('ole32')
    ole.CoInitializeEx.argtypes, ole.CoInitializeEx.restype = [ctypes.c_void_p, wintypes.DWORD], ctypes.c_long
    ole.CoUninitialize.argtypes, ole.CoUninitialize.restype = [], None
    require(ole.CoInitializeEx(None, 2) >= 0, '独立STA线程COM初始化失败')
    result = dict(com_uninitialized=False, dpi_restored=False)
    try:
        previous = user.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
        require(bool(previous), '独立UIA探针无法进入物理DPI上下文')
        try:
            checkpoint()
            before = native.window(target['hwnd'])
            checkpoint()
            foreground = native.foreground()
            checkpoint()
            desktop = native.desktop()
            checkpoint()
            foreground_row = native.window(foreground)
            require(before['pid'] == target['pid'] and before['visible'] is True
                    and desktop == 'Default' and foreground_row['pid'] == target['pid'],
                    '独立探针前目标PID/HWND/输入桌面/前景不符')
            require('windows_mcp' not in sys.modules, '探针已提前加载非冻结UIA包')
            sys.path.insert(0, str(package))
            import windows_mcp.uia as uia
            checkpoint()
            bridge = ReadOnlyUia(uia, package_root=package, checkpoint=checkpoint)
            from async_product_client.batch import TargetQueryHandle
            try:
                with TargetQueryHandle(target) as query_handle:
                    if kind == 'native-observation':
                        import asyncio
                        from async_product_client.batch import validate_observation
                        from async_product_client.core import Identity
                        from async_product_client.native import collect_native
                        identity = Identity(target['pid'], target['birth'], target['image'], target['hwnd'])
                        def verify():
                            checkpoint(); query_handle.verify()
                        result['native'] = asyncio.run(collect_native(identity, native, bridge,
                                                                     checkpoint=checkpoint, verify_identity=verify))
                        validate_observation(result['native'], identity)
                    else:
                        query_handle.verify()
                        result['uia'] = bridge.inspect(target['hwnd'], target['pid'])
                        checkpoint(); query_handle.verify()
            finally:
                checkpoint()
            after = native.window(target['hwnd'])
            checkpoint()
            desktop_after = native.desktop()
            checkpoint()
            foreground_after = native.foreground()
            require(after == before and desktop_after == 'Default'
                    and foreground_after == foreground, '独立UIA探针结束时原目标/前景改变')
        finally:
            require(bool(user.SetThreadDpiAwarenessContext(previous)), '独立UIA探针无法恢复线程DPI上下文')
            result['dpi_restored'] = True
    finally:
        ole.CoUninitialize()
        result['com_uninitialized'] = True
    return result


if __name__ == '__main__':
    require(len(sys.argv) == 2, '探针只接受一个冻结request路径')
    raise SystemExit(execute(sys.argv[1]))
