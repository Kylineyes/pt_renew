"""在批准的新隔离服务中记录健康判定原采样，并可选修正心跳读取顺序。"""
from __future__ import annotations

import functools
import threading
import time


def indicator_health_sample(indicator, clock=time.monotonic, *, heartbeat_first=False):
    """保持原短路顺序；返回判定实际使用的值，而非事后再读的快照。"""
    sample = dict(healthy=False, read_order='heartbeat-first' if heartbeat_first else 'clock-first',
                  alive=None, stopping=None, error=None, now=None, heartbeat=None,
                  heartbeat_age_seconds=None)
    if indicator is None:
        return sample
    sample['alive'] = indicator.thread.is_alive()
    if not sample['alive']:
        return sample
    sample['stopping'] = indicator.stopping
    if sample['stopping']:
        return sample
    error = indicator.error
    sample['error'] = type(error).__name__ if error is not None else None
    if error is not None:
        return sample
    if heartbeat_first:
        heartbeat = indicator.heartbeat
        now = clock()
    else:
        # 与原表达式 time.monotonic() - indicator.heartbeat 的求值顺序一致。
        now = clock()
        heartbeat = indicator.heartbeat
    age = now - heartbeat
    sample.update(now=now, heartbeat=heartbeat, heartbeat_age_seconds=age,
                  healthy=bool(0 <= age <= 1.0))
    return sample


def indicator_healthy(indicator, clock=time.monotonic):
    return indicator_health_sample(indicator, clock, heartbeat_first=True)['healthy']


def install_indicator_health(overlay, trace=None, *, heartbeat_first=True, phases=False,
                             clock=time.monotonic):
    """仅用于批准的新进程；默认采样模式须显式传 heartbeat_first=False。"""
    if getattr(overlay, '_pt_health_snapshot_installed', False):
        raise RuntimeError('指示层健康采样不可重复安装')
    # 阶段状态只由对应线程改写，供健康判定读取；不等待窗口线程或改变心跳。
    phase_state = threading.local()
    current_phases = {}

    def healthy():
        started = time.monotonic()
        with overlay._lock:
            indicator = overlay._instance
        sample = indicator_health_sample(indicator, clock, heartbeat_first=heartbeat_first)
        phase = current_phases.get(indicator.thread.ident) if indicator is not None else None
        finished = time.monotonic()
        if trace is not None:
            trace.emit('indicator-health-sample', **sample, started=started, finished=finished,
                       duration_seconds=finished-started, phase=phase,
                       phase_age_seconds=finished-phase['started'] if phase else None)
        return sample['healthy']

    def wrap(obj, name, label):
        original = getattr(obj, name)

        @functools.wraps(original)
        def measured(*args, **kwargs):
            started = time.monotonic()
            ident = threading.get_ident()
            previous = getattr(phase_state, 'phase', None)
            phase = dict(name=label, started=started, parent=previous['name'] if previous else None)
            phase_state.phase = phase
            current_phases[ident] = phase
            exception = None
            try:
                return original(*args, **kwargs)
            except BaseException as error:
                exception = type(error).__name__
                raise
            finally:
                finished = time.monotonic()
                phase_state.phase = previous
                if previous is None:
                    current_phases.pop(ident, None)
                else:
                    current_phases[ident] = previous
                # 不为每帧各条边写日志；慢阶段和异常保留完整耗时。
                if trace is not None and (finished-started >= .05 or exception is not None):
                    trace.emit('indicator-phase', **phase, finished=finished,
                               duration_seconds=finished-started, exception=exception)
        setattr(obj, name, measured)

    if phases:
        for name in ('_monitor_rects', '_build_layers'):
            wrap(overlay, name, name)
        for name in ('set_opacity', 'show', 'hide', 'move', 'close'):
            wrap(overlay._Layer, name, 'layer.'+name)
        wrap(overlay.flash_overlay, '_pump_messages', 'pump-messages')
        wrap(overlay._Indicator, 'change', 'change-and-acknowledge')
    overlay.is_healthy = healthy
    overlay._pt_health_snapshot_installed = True
    if trace is not None:
        trace.emit('indicator-health-installed', heartbeat_first=heartbeat_first,
                   phases=phases, threshold_seconds=1.0)
