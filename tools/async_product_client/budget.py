"""统一会话的离线调用预算；冻结拒绝上限不是执行耗时保证，绝不自动授予live-ready。"""
from __future__ import annotations

from .core import require

# 每次ProductNative对每个可见窗前后各启动一个独立探针。
# 数字来自当前统一编排的显式observe/capture路径，需用完整假流程计数交叉验证。
NATIVE_WINDOWS = {
    'baseline': (1, 1),
    'command_image': (1, 1, 1, 1),
    'command_ack': (1, 1),
    'net_command_click': (1, 2),
    'copper_command_click': (1, 1),
    'file_image': (2, 2, 2),
    'file_ack': (2, 2),
    'file_type_and_image': (2, 2, 2, 2),
    'file_path_ack': (2, 2),
    'file_open': (2, 1),
    'gate_image': (1, 1),
    'edit_and_image': (1, 1, 1, 1, 1, 1),
    'final_image': (1, 1),
    'dirty_close_and_image': (1, 2, 2),
    'discard': (2,),
}


def session_budget(kind):
    require(kind in ('net', 'copper'), '会话预算种类无效')
    pre = ['baseline', 'command_image', 'command_ack', kind + '_command_click']
    if kind == 'net': pre += ['file_image', 'file_ack', 'file_type_and_image', 'file_path_ack', 'file_open']
    critical = ['gate_image', 'edit_and_image']
    after = ['final_image', 'dirty_close_and_image', 'discard']
    phases = pre + critical + after
    native_count = sum(len(NATIVE_WINDOWS[name]) for name in phases)
    probes = {name: 2 * sum(NATIVE_WINDOWS[name]) for name in phases}
    return dict(kind=kind, native_observations=native_count, probe_queries=sum(probes.values()),
                probe_queries_before_gate=sum(probes[name] for name in pre),
                probe_queries_t1=probes['gate_image'],
                probe_queries_gate_through_edit=sum(probes[name] for name in critical),
                phase_probe_queries=probes, frozen_probe_limit=32, probe_query_timeout_ms=5000,
                exceeds_frozen_probe_limit=sum(probes.values()) > 32,
                t1_probe_configured_wait_sum_seconds=probes['gate_image'] * 5,
                t2_probe_configured_wait_sum_seconds=sum(probes[name] for name in critical) * 5,
                snapshot_tool_timeout_seconds=35, t1_deadline_seconds=20, t2_deadline_seconds=50,
                original_watchdog_seconds=60, ready_for_live=False, runtime_timing_verified=False,
                reason='当前调用数量超冻结探针预算；配置等待上限之和已耗尽门槛，且未计实际模型/工具/CPU/持久化成本',
                interpretation='这里只核对当前调用结构和配置拒绝上限，不是耗时测量、未来上界或产品现场批准')
