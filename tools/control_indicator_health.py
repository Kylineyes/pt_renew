"""指示层心跳快照：先取心跳再取当前时间，避免并发更新产生伪负年龄。"""
from __future__ import annotations
import time


def indicator_healthy(indicator, clock=time.monotonic):
    if indicator is None:
        return False
    # 原实现先time.monotonic()再读heartbeat；两次读取间owner可写入更新后的值。
    # 先冻结心跳只会稍微保守，不会把未来/过期/停止/错误状态当健康。
    heartbeat=indicator.heartbeat
    now=clock()
    return bool(indicator.thread.is_alive() and not indicator.stopping
                and indicator.error is None and 0<=now-heartbeat<=1.0)


def install_indicator_health(overlay):
    """只安装到批准的新隔离服务，保持原1秒阈值和故障拒绝。"""
    if getattr(overlay,'_pt_health_snapshot_installed',False):
        raise RuntimeError('指示层健康读取修复不可重复安装')
    def healthy():
        with overlay._lock:
            indicator=overlay._instance
        return indicator_healthy(indicator)
    overlay.is_healthy=healthy
    overlay._pt_health_snapshot_installed=True
