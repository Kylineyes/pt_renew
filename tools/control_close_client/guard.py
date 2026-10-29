"""统一桌面请求状态机；可注入假时钟/假工具，导入本模块不接触桌面。"""
import datetime
import json
import re
import time
from dataclasses import dataclass
from guard_protocol_errors import control_error_code

INPUTS = frozenset({'Click','Type','Shortcut','Scroll','Move','App','Launch'})
ALLOWED = INPUTS | {'Snapshot'}
ERROR = re.compile(r'^\s*(?:\[\s*\")?(?:error\b|failed\b|exception\b|无法(?:捕获|获取|执行)|(?:捕获|调用|执行|截图).{0,15}(?:失败|错误))', re.I)

class SystemClock:
    def monotonic(self): return time.monotonic()
    def wall(self): return time.time()

@dataclass
class Halt(Exception):
    reason: str
    executed: object = False
    def __str__(self): return self.reason

class Guard:
    """所有工具及原生检查只能由此类发起；失败仅显式诊断可恢复，不自动重试。"""
    def __init__(self, transport, native, emit, clock=None):
        self.transport, self.native, self.emit = transport, native, emit
        self.clock = clock or SystemClock()
        self.target = None
        self.not_before = 0.0
        self.failed = None
        self.diagnosis = None
        self.serial = 0
        self.token = 'start'
        self.seen = set()
        self.busy = False

    def event(self, kind, **data):
        record = dict(kind=kind, monotonic=self.clock.monotonic(), wall=self.clock.wall(), **data)
        self.emit(record)
        return record

    def state(self):
        return dict(token=self.token, failed=self.failed, diagnosis=self.diagnosis,
                    not_before_monotonic=self.not_before, target=self.target, busy=self.busy)

    def cool_check(self):
        if self.clock.monotonic() < self.not_before:
            raise Halt('完整120秒尚未结束，禁止任何桌面/原生请求')

    def retreat(self, reason):
        now = self.clock.monotonic()
        self.not_before = now + 120.0
        self.diagnosis = None
        self.event('retreat', reason=reason, not_before_monotonic=self.not_before,
                   not_before_wall=self.clock.wall()+120.0, duration_seconds=120,
                   no_desktop_requests_before_deadline=True)
        raise Halt(reason)

    async def raw(self, tool, args):
        # 即使经诊断、聚焦或启动入口也必须过同一时限。
        self.cool_check()
        self.event('tool_request', tool=tool, arguments=args)
        try:
            row = await self.transport(tool, args)
        except Exception as error:
            self.retreat('工具调用异常，执行结果未知：'+str(error))
        self.event('tool_result', tool=tool, result=row)
        content = '\n'.join(row.get('text', []))
        control_code = control_error_code(row)
        if control_code:
            self.retreat('工具回执报告控制争用：'+control_code+' '+content)
        if row.get('is_error'):
            raise Halt('工具错误：'+content)
        if ERROR.search(content):
            raise Halt('工具文本返回错误：'+content)
        if tool == 'Snapshot' and not row.get('images'):
            raise Halt('截图没有图像，不能算通过')
        return row

    async def observe_native(self):
        self.cool_check()
        self.event('native_request')
        try:
            native = await self.native()
        except Exception as error:
            self.retreat('原生只读检查失败：'+str(error))
        self.event('native_result', result=native)
        # 输入桌面而非线程桌面；不可读或非Default均拒绝。
        if native.get('input_desktop') != 'Default' or native.get('locked') is not False:
            self.retreat('锁屏/输入桌面不可确认')
        if not native.get('foreground_stable'):
            self.retreat('原生前景在检查中变化')
        if self.target:
            f = native.get('foreground', {})
            windows = native.get('windows', [])
            owned = [w for w in windows if w.get('pid') == self.target['pid']]
            match = [w for w in owned if w.get('hwnd') == f.get('hwnd')]
            if f.get('pid') != self.target['pid'] or not match or not f.get('hwnd'):
                self.retreat('非目标前景或目标PID/HWND归属不匹配')
            if f.get('image', '').casefold() != self.target['image'].casefold():
                self.retreat('目标进程映像不匹配')
        return native

    async def gate(self, check_status=False):
        self.cool_check()
        if not check_status:
            # 用户要求正常键鼠直接执行；仅保留目标归属检查，实际工具拒绝仍停链。
            return await self.observe_native()
        row = await self.raw('ControlStatus', {})
        try:
            state = row.get('structured_content') or json.loads('\n'.join(row['text']))
        except (ValueError,KeyError,TypeError):
            self.retreat('控制状态不可解析')
        if not isinstance(state,dict) or state.get('state') not in ('ready','ai'):
            self.retreat('ControlStatus='+str(state))
        return await self.observe_native()

    def bind(self, pid, image):
        if self.target:
            raise Halt('已有目标，禁止替换进程绑定')
        if not isinstance(pid,int) or pid <= 0 or not image:
            raise Halt('目标绑定无效')
        self.target = dict(pid=pid,image=image)
        self.event('target_bound', target=self.target)

    def retire(self, pid, exit_code):
        if self.busy or not self.target or self.target['pid'] != pid or exit_code is None:
            raise Halt('必须有本绑定进程已退出的正面证据')
        self.event('target_retired',pid=pid,exit_code=exit_code)
        self.target=None
        # 故障锁存与120秒截止不因生命周期结束清零。

    def require_arguments(self, tool, args):
        if tool not in ALLOWED:
            raise Halt('禁止未列入的工具入口：'+tool)
        if tool == 'Type' and not (args.get('loc') or args.get('label')):
            raise Halt('Type必须提供loc或label')
        if tool == 'App' and args != {'mode':'switch','name':'PT Renew'}:
            raise Halt('聚焦只允许明确PT Renew短名，禁止其他App模式')
        if tool != 'Launch' and not self.target:
            raise Halt('目标尚未绑定，禁止输入或截图')
        if tool == 'Launch' and self.target:
            raise Halt('已有目标，不能重复启动')

    async def perform(self, request):
        """一次一条，parent来自前次成功token；失败后后续排队请求全部拒绝。"""
        ident = request['id']
        if ident in self.seen:
            return dict(completed=False, reason='重复ID禁止重发（动作可能已执行）', executed='不重发')
        self.seen.add(ident)
        if self.busy:
            return dict(completed=False, reason='已有请求执行中，禁止排队', executed=False)
        if self.failed:
            return dict(completed=False, reason='失败链未诊断恢复，禁止后续动作', executed=False)
        if request.get('parent') != self.token:
            return dict(completed=False, reason='前次成功token不匹配，拒绝排队或过期请求', executed=False)
        self.busy = True
        attempted = False
        executed = False
        phase = 'preflight'
        try:
            tool,args = request['tool'],request.get('arguments',{})
            self.require_arguments(tool,args)
            await self.gate()
            phase = 'action'
            attempted = True
            row = await self.raw(tool,args)
            executed = True
            if tool == 'Launch':
                self.bind(row['pid'],row['image'])
            if request.get('capture',False) and tool != 'Snapshot':
                phase = 'post_capture'
                await self.gate()
                await self.raw('Snapshot',{'use_vision':True,'use_annotation':False,'use_ui_tree':False})
                # 截图可改变前景，后验仍只读查原生归属。
                await self.observe_native()
            elif tool != 'Launch':
                phase = 'post_native'
                await self.observe_native()
            self.token = ident
            result = dict(completed=True,executed=executed,token=self.token,phase=phase)
        except Exception as error:
            self.failed = ident
            self.diagnosis = None
            outcome = True if executed else ('unknown' if attempted else False)
            result = dict(completed=False,reason=str(error),executed=outcome,phase=phase,
                          failed_id=ident,not_before_monotonic=self.not_before)
            self.event('chain_halted', **result)
        finally:
            self.busy = False
        self.event('request_complete',id=ident,result=result)
        return result

    async def diagnose(self, ident):
        """只读且有界，无等待/重连/聚焦；截止前零调用，到期仍争用重新120秒。"""
        if self.busy:
            return dict(completed=False,reason='已有请求，不能并行诊断')
        self.busy = True
        try:
            await self.gate(check_status=True)
            self.serial += 1
            self.diagnosis = f'{ident}:{self.serial}'
            return dict(completed=True,diagnosis=self.diagnosis,failed_id=self.failed,
                        target=self.target,explicit_resume_required=True)
        except Exception as error:
            self.diagnosis = None
            return dict(completed=False,reason=str(error),not_before_monotonic=self.not_before)
        finally:
            self.busy = False

    def resume(self, failed_id, diagnosis, token):
        """人工审阅诊断后只清锁存；不发动作，不恢复旧队列，不重发失败动作。"""
        self.cool_check()
        if self.busy or not self.failed or failed_id != self.failed or diagnosis != self.diagnosis or not diagnosis:
            raise Halt('恢复必须引用当前失败和最新成功诊断')
        if token in self.seen or not token:
            raise Halt('恢复token必须唯一')
        self.seen.add(token)
        self.failed,self.diagnosis,self.token = None,None,token
        self.event('explicit_resume', failed_id=failed_id,token=token)
        return dict(completed=True,token=token,action_sent=False)
