"""隔离副本App查找修复：激活前刷新窗口列表，保留原查找/激活/后验。"""
from __future__ import annotations

import functools


def install_app_refresh(desktop_class):
    """只用于明确批准的新进程；不改变ControlToolGate或强制前景成功。"""
    if getattr(desktop_class, '_pt_app_refresh_installed', False):
        raise RuntimeError('同一隔离进程禁止重复安装App刷新修复')
    original = desktop_class.switch_app

    @functools.wraps(original)
    def switch_app(self, name):
        # 原版本仅在缓存为空时刷新；已打开新窗口时非空旧缓存会漏掉目标。
        # 刷新失败原样传播，不拿旧结果继续激活。
        self.get_state()
        return original(self, name)

    desktop_class.switch_app = switch_app
    desktop_class._pt_app_refresh_installed = True
