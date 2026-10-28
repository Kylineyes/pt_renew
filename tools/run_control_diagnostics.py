"""复制控制包并启动隔离诊断或显式批准的资源实验，原安装与原控制门禁保持。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from control_diagnostics import TraceWriter, install


def digest(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and p.suffix not in ('.pyc', '.pyo')}


def prepare(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    package = destination/'windows_mcp'
    if source.name != 'windows_mcp' or not (source/'desktop/control.py').is_file():
        raise ValueError('来源不是可核验的windows_mcp包')
    before = digest(source)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, package, ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo'))
    after = digest(package)
    if before != after:
        raise RuntimeError('隔离副本与安装源码摘要不符')
    manifest = dict(source=str(source), package=str(package), files=before,
                    installed_writes=0, changes='仅通过独立启动器附加诊断或显式批准实验，包副本字节不改')
    with (destination/'package-manifest.json').open('x',encoding='utf-8') as out:
        json.dump(manifest,out,ensure_ascii=False,indent=2)
    return manifest


def serve(package_root, trace_path, approval_path):
    root = Path(package_root).resolve()
    manifest = json.loads((root/'package-manifest.json').read_text(encoding='utf-8'))
    if digest(root/'windows_mcp') != manifest['files']:
        raise RuntimeError('包副本在审阅后发生变化')
    approval = json.loads(Path(approval_path).read_text(encoding='utf-8-sig'))
    if approval['package_manifest_sha256'] != hashlib.sha256((root/'package-manifest.json').read_bytes()).hexdigest():
        raise RuntimeError('批准不匹配隔离包清单')
    if approval.get('mode') != 'diagnostics-only' or not approval.get('task_id') or not approval.get('dispatch_id'):
        raise RuntimeError('缺少本轮诊断任务批准')
    for name,sha in approval['launcher_files'].items():
        if hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() != sha:
            raise RuntimeError('诊断启动器审阅后变化：'+name)
    health_sampling = approval.get('indicator_health_sampling', False)
    health_fix = approval.get('indicator_health_fix', False)
    bitmap_timing = approval.get('indicator_bitmap_timing', False)
    bitmap_surface = approval.get('indicator_bitmap_surface', False)
    if type(bitmap_surface) is not bool:
        raise RuntimeError('图层资源复用选项必须是布尔值')
    if not isinstance(health_sampling, bool) or not isinstance(health_fix, bool):
        raise RuntimeError('指示层采样和修复选项必须是布尔值')
    if health_fix and not health_sampling:
        raise RuntimeError('指示层读取修复必须同时启用实际判定采样')
    if health_sampling and 'control_indicator_health.py' not in approval['launcher_files']:
        raise RuntimeError('指示层健康采样未列入批准摘要')
    if not isinstance(bitmap_timing, bool):
        raise RuntimeError('位图上传计时选项必须是布尔值')
    if bitmap_timing and (not health_sampling or 'control_bitmap_timing.py' not in approval['launcher_files']):
        raise RuntimeError('位图上传计时必须同时批准健康采样并冻结计时模块摘要')
    if bitmap_surface:
        required = {'run_control_diagnostics.py', 'control_diagnostics.py', 'control_indicator_health.py',
                    'control_bitmap_surface.py', 'control_bitmap_surface_model.py'}
        if not health_sampling or not health_fix or not required <= approval['launcher_files'].keys():
            raise RuntimeError('图层资源复用必须同时批准实际健康采样及读取修复，并冻结全部实验模块')
        if bitmap_timing:
            raise RuntimeError('图层资源复用不能同时启用旧位图计时')
        from control_bitmap_surface import SUPPORTED_SOURCES
        if any(manifest['files'].get(name) != sha for name, sha in SUPPORTED_SOURCES.items()):
            raise RuntimeError('图层资源复用不支持当前控制包源码版本')
        if (approval.get('permission_confirmed') is not True or not approval.get('permission')
                or not approval.get('message_id') or approval.get('diagnostic_seconds') != 600
                or approval.get('total_seconds') != 900):
            raise RuntimeError('资源实验缺少本轮明确桌面许可、批准消息或600/900秒预算')
    os.environ.update(ANONYMIZED_TELEMETRY='false', DO_NOT_TRACK='1',
                      WINDOWS_MCP_SCREENSHOT_BACKEND='pillow')
    sys.path.insert(0,str(root))
    from windows_mcp.desktop import control, control_overlay, service
    import windows_mcp.uia.core as uia_core
    for module in (control, control_overlay, control_overlay.flash_overlay):
        if not Path(module.__file__).resolve().is_relative_to(root/'windows_mcp'):
            raise RuntimeError('实际导入来源不是独立副本')
    trace = TraceWriter(Path(trace_path))
    surface_manager = None
    try:
        install(control,control_overlay,service,uia_core,trace)
        if approval.get('app_refresh_fix', False):
            if 'control_app_refresh.py' not in approval['launcher_files']:
                raise RuntimeError('App刷新修复未列入批准摘要')
            from control_app_refresh import install_app_refresh
            install_app_refresh(service.Desktop)
            trace.emit('app-refresh-fix-installed', package_source=str(Path(service.__file__).resolve()))
        if bitmap_surface:
            from control_bitmap_surface import install_bitmap_surface
            surface_manager = install_bitmap_surface(control_overlay, trace)
        if health_sampling:
            from control_indicator_health import install_indicator_health
            install_indicator_health(control_overlay, trace, heartbeat_first=health_fix, phases=True)
        if bitmap_timing:
            from control_bitmap_timing import install_bitmap_timing
            install_bitmap_timing(control_overlay.flash_overlay, trace)
        from windows_mcp.__main__ import main
        main(['serve'],standalone_mode=False)
    finally:
        try:
            if surface_manager is not None:
                surface_manager.audit_shutdown()
        finally:
            trace.close()


def main():
    parser=argparse.ArgumentParser(description='控制工具隔离副本与只读诊断启动器')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--source',required=True);p.add_argument('--destination',required=True)
    s=sub.add_parser('serve');s.add_argument('--package-root',required=True);s.add_argument('--trace',required=True);s.add_argument('--approval',required=True)
    args=parser.parse_args()
    if args.command=='prepare':
        row=prepare(args.source,args.destination)
        print(json.dumps(dict(package=row['package'],files=len(row['files']),installed_writes=0),ensure_ascii=False))
    else:
        serve(args.package_root,args.trace,args.approval)


if __name__=='__main__':
    main()
