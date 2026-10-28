"""自建诊断窗首次激活：只调原App工具，不导入桌面API或更改门禁状态。"""
from __future__ import annotations

import re

TITLE = 'PT Renew 控制诊断试验'


class InitialTargetActivation:
    """在绑定/UIA核验后、诊断组开始前最多尝试一次，失败保持原锁存。"""

    def __init__(self):
        self.used = False

    async def run(self, guard, ident, parent, *, uia_ready, groups_started):
        if self.used:
            return dict(completed=False, executed=False, tool_call_sent=False,
                        reason='初始激活机会已消费，禁止自动重试')
        # 不让失败链、重复ID或并行调用进入任何桌面路径。
        if (guard.busy or guard.failed or not isinstance(ident, str)
                or re.fullmatch(r'[a-zA-Z0-9_-]+', ident) is None or ident in guard.seen
                or parent != guard.token or not uia_ready or groups_started != 0
                or not guard.target or not getattr(guard, 'expected_birth', None)
                or not getattr(guard, 'expected_hwnd', None)):
            return dict(completed=False, executed=False, tool_call_sent=False,
                        reason='初始激活必须引用未失败的已绑定/UIA核验目标及当前token，且尚未开始组')
        self.used = True
        guard.seen.add(ident)
        guard.busy = True
        sent = False
        returned = False
        try:
            guard.cool_check()
            guard.require_arguments('App', dict(mode='switch', name=TITLE))
            guard.event('native_request', purpose='initial_activation_identity')
            native = await guard.native()
            guard.event('native_result', purpose='initial_activation_identity', result=native)
            if (native.get('input_desktop') != 'Default' or native.get('locked') is not False
                    or native.get('foreground_stable') is not True):
                raise ValueError('初始激活前输入桌面或前景稳定性不可确认')
            matches = [w for w in native.get('windows', []) if w.get('title') == TITLE]
            target = guard.target
            if len(matches) != 1:
                raise ValueError('初始激活前同名窗口不唯一')
            window = matches[0]
            if (window.get('pid') != target['pid']
                    or window.get('birth') != guard.expected_birth
                    or window.get('hwnd') != guard.expected_hwnd
                    or window.get('image', '').casefold() != target['image'].casefold()
                    or window.get('cls') != 'TkTopLevel'):
                raise ValueError('初始激活前目标PID/创建时间/HWND/映像/类不符')
            guard.cool_check()
            # 首次激活允许当前前景为其他窗口，原App工具内部仍过ControlToolGate。
            # 不额外ControlStatus、不原生激活、不清failed或输入集合。
            sent = True
            await guard.raw('App', dict(mode='switch', name=TITLE))
            returned = True
            await guard.observe_native()
            guard.token = ident
            result = dict(completed=True, executed=True, tool_call_sent=True,
                          token=ident, reason='原App返回且精确目标前景后验通过')
        except Exception as error:
            guard.failed = ident
            guard.diagnosis = None
            # raw/observe_native可能已设置截止，未设置时按原120秒退避一次。
            if guard.not_before <= guard.clock.monotonic():
                try:
                    guard.retreat('初始激活失败：'+str(error))
                except Exception:
                    pass
            result = dict(completed=False, executed=True if returned else 'unknown' if sent else False,
                          tool_call_sent=sent, reason=str(error), failed_id=ident,
                          not_before_monotonic=guard.not_before)
        finally:
            guard.busy = False
        guard.event('initial_activation_complete', id=ident, result=result)
        return result
