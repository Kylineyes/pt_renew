"""新资源实验客户端的离线批准核验；不导入MCP、Win32或启动进程。"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

CLIENT_FILES = frozenset(('client.py','step.py','driver.py','Step.ps1','window.py','guard.py',
    'diagnostic_guard.py','guard_protocol_errors.py','budget.py','snapshot_pacer.py','lifecycle.py',
    'uia_probe.py','process_witness.py','inspect_legacy_desktop.py','hold-chain.py','passive_initial.py','plan.json'))
TOOL_FILES = frozenset(('run_control_diagnostics.py','control_diagnostics.py','control_indicator_health.py',
    'control_bitmap_surface.py','control_bitmap_surface_model.py','control_surface_approval.py',
    'control_app_refresh.py','control_geometry.py','control_target_activation.py','control_test_window.py'))


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def verify_files(root, values, required):
    require(isinstance(values, dict) and required <= values.keys(), '批准缺少完整冻结文件集合')
    for name, expected in values.items():
        path = (root/name).resolve()
        require(path.is_relative_to(root) and path.is_file(), '冻结文件不属于批准目录：'+name)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, '冻结文件审阅后变化：'+name)


def require_client_approval(root, tools_root, package_root, *, environ=None, require_owned_close=False):
    root, tools_root, package_root = (Path(p).resolve() for p in (root, tools_root, package_root))
    approval = load(root/'phase-two-approval.json')
    env = os.environ if environ is None else environ
    require(approval.get('permission_confirmed') is True and bool(approval.get('permission'))
            and bool(approval.get('message_id')), '缺少本轮明确桌面许可及新批准消息')
    require(approval.get('mode') == 'diagnostics-only' and approval.get('evidence_root') == str(root), '批准范围或证据目录不符')
    require(bool(re.fullmatch(r'task_[0-9a-f]{12}', str(approval.get('task_id'))))
            and bool(re.fullmatch(r'ctx_[0-9a-f]{12}', str(approval.get('dispatch_id')))), '必须绑定本轮新Task/Dispatch')
    require(approval['task_id'] not in ('task_47e20595fdcb','task_ab514403da21','task_371c96f46645',
            'task_f45a13630a8b','task_e972187b97ac','task_142ea7a86a8d'), '禁止复用已结算现场任务')
    expected = (approval.get('provider'), 'gpt-6.1-sol', 'high', approval.get('session_id'))
    actual = tuple(env.get(name) for name in ('PI_PROVIDER','PI_MODEL','PI_REASONING_LEVEL','PI_SESSION_ID'))
    require(bool(expected[0]) and bool(expected[3]) and expected == actual, '实际Pi模型、推理强度或新会话不符')
    require(expected[3] not in ('01a1739a-82f6-76cf-9ffc-c63e95be56d4',
                               '01a18223-76b0-706a-a9fc-2b5a89788f37'), '禁止恢复只读或已结算原会话')
    require(all(type(approval.get(name)) is int and approval[name] == value for name, value in
                dict(max_connections=1,max_groups=1,max_windows=1,max_snapshots=4,
                     diagnostic_seconds=600,total_seconds=900).items()), '客户端数量或截止预算不符')
    require(not any((root/name).exists() for name in ('live-state.json','runtime-limits.json','client-fatal.json')),
            '已有运行状态或截止原件，禁止重连或重置')
    require(approval.get('tools_root') == str(tools_root) and approval.get('package_root') == str(package_root),
            '必须使用本轮冻结工具及隔离包')
    verify_files(root, approval.get('reviewed_files_sha256'), CLIENT_FILES)
    server = load(root/'server-approval.json')
    for name in ('mode','task_id','dispatch_id','message_id','permission','permission_confirmed',
                 'diagnostic_seconds','total_seconds'):
        require(server.get(name) == approval.get(name), '客户端与服务批准不一致：'+name)
    for name in ('indicator_bitmap_surface','indicator_health_sampling','indicator_health_fix',
                 'app_refresh_fix','initial_target_activation'):
        require(approval.get(name) is True and server.get(name) is True, '必须同时批准本轮全部实验条件：'+name)
    require(approval.get('indicator_bitmap_timing') is False and server.get('indicator_bitmap_timing') is False,
            '资源实验不能混用旧位图计时')
    verify_files(tools_root, server.get('launcher_files'), TOOL_FILES)
    close_enabled = approval.get('owned_diagnostic_close', False)
    require(type(close_enabled) is bool, '专用关闭开关必须是布尔值')
    require(close_enabled == server.get('owned_diagnostic_close', False), '客户端与服务的专用关闭批准不一致')
    require(not require_owned_close or close_enabled, '本候选必须显式批准专用关闭')
    if close_enabled:
        module = 'control_owned_close.py'
        verify_files(tools_root, server['launcher_files'], TOOL_FILES | {module})
        require(approval.get('owned_close_sha256') == server.get('owned_close_sha256')
                == server['launcher_files'][module], '专用关闭模块摘要不符')
    for name, file in (('geometry_sha256','control_geometry.py'),
                       ('target_activation_sha256','control_target_activation.py')):
        require(approval.get(name) == server['launcher_files'][file] == server.get(name), '客户端辅助模块摘要不符：'+name)
    manifest = package_root/'package-manifest.json'
    require(server.get('package_manifest_sha256') == hashlib.sha256(manifest.read_bytes()).hexdigest(), '隔离包清单审阅后变化')
    package = package_root/'windows_mcp'
    expected_files = load(manifest)['files']
    actual_files = {p.relative_to(package).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in package.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                    and p.suffix not in ('.pyc','.pyo')}
    require(expected_files == actual_files, '隔离包文件集合或摘要变化')
    require((root/'window.py').read_bytes() == (tools_root/'control_test_window.py').read_bytes(), '测试窗与冻结工具不同')
    return approval


def surface_initial_ready(rows):
    """只读现有日志的实验附加条件，不触发任何桌面或状态探测。"""
    installed = [row for row in rows if row.get('event') == 'indicator-surface-installed']
    if len(installed) != 1:
        return dict(ready=False,reason='缺少唯一资源实验安装记录',fatal=len(installed)>1)
    if installed[0].get('max_surfaces') != 64 or installed[0].get('max_bitmap_bytes') != 64*1024*1024:
        return dict(ready=False,reason='资源实验预算与冻结方案不同',fatal=True)
    if any(row.get('exception') is not None or row.get('resources',{}).get('failed') is True
           for row in rows if row.get('event','').startswith('indicator-surface-')):
        return dict(ready=False,reason='资源实验已失败，禁止创建测试窗',fatal=True)
    return dict(ready=True,reason='资源实验安装及失败锁存检查通过',fatal=False)
