"""产品创建所有者、Qt窗口归属及输入；与诊断Tk关闭模块无依赖。"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from .core import Identity, SECOND, digest, positive, require

QT_CLASS = 'Qt6120QWindowIcon'
EXPERIMENT_SUFFIX = '【独立异步实验构建】'
MODAL_TITLE = '放弃工作副本更改？'


def tree_hashes(root, *, ignore_bytecode=False):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), '部署目录无效')
    paths = sorted(root.rglob('*'))
    require(not any(p.is_symlink() for p in paths), '冻结部署不能包含链接')
    return {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in paths
            if p.is_file() and (not ignore_bytecode
                                or '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo'))}


class ProductOwner:
    """创建后立即保存原Popen，身份读取失败也不丢失其所有权；从不重新按PID接管。"""

    def __init__(self, ledger):
        self.ledger = ledger
        self.process = None
        self.process_identity = None
        self.identity = None
        self.launch_used = False
        self.retired = False

    def launch(self, *, deployment, manifest, inputs, environment, factory, inspect_created):
        self.ledger.desktop_allowed()
        require(not self.launch_used and self.process is None, '产品启动机会已消费')
        require(len(manifest) == 22 and 'pt-renew.exe' in manifest
                and tree_hashes(deployment) == manifest, '实验完整22文件冻结部署不符')
        for path, sha in inputs.items():
            require(digest(Path(path).read_bytes()) == sha, '本轮输入副本摘要不符')
        require(bool(inputs), '缺少本轮输入副本')
        require(not any(k.upper().startswith(('QT_', 'QML', 'PT_ASYNC_', 'PT_RENEW_ASYNC_', 'PT_ENABLE_ASYNC'))
                        for k in environment),
                '继承环境含未清理Qt或旧实验变量')
        self.launch_used = True
        # factory的生产适配器必须在本客户端直接创建Popen；这里不提供现场适配器。
        self.process = factory([str(Path(deployment).resolve() / 'pt-renew.exe')],
                               cwd=str(Path(deployment).resolve()), env=dict(environment))
        require(self.process is not None, '创建器没有返回原Popen，启动结果未知')
        info = inspect_created(self.process)
        require(positive(self.process.pid) and self.process.poll() is None
                and info.get('pid') == self.process.pid and positive(info.get('birth'))
                and positive(info.get('handle')) and info.get('original_handle') is True
                and Path(info.get('image', '')).resolve() == (Path(deployment) / 'pt-renew.exe').resolve(),
                '原Popen/原句柄创建身份不符')
        self.process_identity = dict(info)
        self.ledger.event('product_created', identity=info, deployment=manifest, inputs=inputs,
                          environment_clean=True, environment_keys=sorted(environment), original_popen=True)

    def bind_main(self, hwnd):
        require(self.identity is None and self.process_identity is not None
                and self.process.poll() is None, '不能绑定已退出或未知的产品主窗')
        info = self.process_identity
        self.identity = Identity(info['pid'], info['birth'], info['image'], hwnd)
        return self.identity

    def alive(self):
        require(not self.retired and self.process is not None and self.identity is not None
                and self.process.pid == self.identity.pid and self.process.poll() is None,
                '原Popen已退出、身份改变或已退役')

    async def wait_exit(self, waiter, timeout_ns):
        require(self.process is not None and self.process_identity is not None,
                '没有本客户端创建的原Popen')
        require(positive(timeout_ns) and self.ledger.clock.monotonic_ns() + timeout_ns
                < self.ledger.cleanup_deadline_ns, '原Popen本地等待超出原收尾截止')
        code = await waiter(self.process, timeout_ns / SECOND)
        require(type(code) is int and self.process.returncode == code
                and self.process.pid == self.process_identity['pid'], '原Popen退出证据不一致')
        self.ledger.event('product_exit', pid=self.process.pid, birth=self.process_identity['birth'],
                          original_handle=self.process_identity['handle'], exit_code=code, original_popen=True)
        self.retired = True
        self.ledger.event('product_retired', exit_code=code)
        # 退役只证明生命周期结束，不能清失败或把非0改成0。
        require(code == 0 and self.ledger.clock.monotonic_ns() < self.ledger.cleanup_deadline_ns,
                '产品原Popen非0退出或原收尾截止已过')
        return code


async def original_wait(process, seconds):
    return await asyncio.to_thread(process.wait, timeout=seconds)


@dataclass(frozen=True)
class WindowPolicy:
    filename: str

    def title(self, dirty):
        require(self.filename and Path(self.filename).name == self.filename, '冻结文件名必须精确')
        return f'{self.filename}{" * 已修改" if dirty else ""} · 工作副本 · 不支持保存 · PT Renew' + EXPERIMENT_SUFFIX

    def check(self, native, identity, *, stage, dirty):
        require(native.get('input_desktop') == 'Default' and native.get('locked') is False
                and native.get('foreground_stable') is True, '输入桌面未知、锁定或前景不稳定')
        windows = native.get('windows', [])
        mains = [w for w in windows if w.get('hwnd') == identity.hwnd]
        require(len(mains) == 1 and identity.matches(mains[0]) and mains[0].get('owner') == 0
                and mains[0].get('cls') == QT_CLASS and mains[0].get('title') == self.title(dirty),
                '精确主HWND/PID/birth/image/类/允许标题不符')
        related = [w for w in windows if w.get('pid') == identity.pid and w.get('owner') == identity.hwnd]
        if stage == 'main':
            require(not related, '主窗输入阶段存在owned模态或文件框')
            target = mains[0]
        else:
            require(stage == 'dirty-modal' and dirty and len(related) == 1, '模态阶段或owner关系不唯一')
            target = related[0]
            modal_identity = Identity(identity.pid, identity.birth, identity.image, target.get('hwnd'))
            require(modal_identity.matches(target) and target['hwnd'] != identity.hwnd
                    and target.get('cls') == QT_CLASS and target.get('title') == MODAL_TITLE
                    and target.get('modal') is True and target.get('default_button') == '取消',
                    'dirty模态PID/birth/image/HWND/owner/标题/默认取消不符')
        foreground = native.get('foreground', {})
        require(foreground == target, '当前输入归属不是精确目标窗口')
        rect = target.get('rect', [])
        require(target.get('coordinate_space') == 'physical-desktop-pixels'
                and target.get('thread_context_restored') is True and len(rect) == 4
                and all(type(x) is int for x in rect) and rect[0] < rect[2] and rect[1] < rect[3],
                '物理矩形或DPI线程恢复证据缺失')
        return target


class ProductIO:
    def __init__(self, ledger, owner, policy, *, native, transport, snapshot):
        self.ledger, self.owner, self.policy = ledger, owner, policy
        self.native_api, self.transport, self.snapshot_api = native, transport, snapshot
        self.attempts = []

    async def observe(self, *, stage='main', dirty=False):
        self.ledger.desktop_allowed()
        self.owner.alive()
        self.ledger.event('native_request', stage=stage)
        row = await self.native_api()
        self.ledger.desktop_allowed()
        self.owner.alive()
        target = self.policy.check(row, self.owner.identity, stage=stage, dirty=dirty)
        self.ledger.event('native_result', stage=stage, result=row)
        return target

    async def _send(self, tool, arguments, expected_text):
        self.ledger.desktop_allowed()
        require((tool == 'Click' and set(arguments) == {'loc'})
                or (tool == 'Shortcut' and arguments.get('shortcut') in ('delete', 'alt+f4')
                    and set(arguments) == {'shortcut'}), '产品模块不提供通用文本/快捷键入口')
        attempt = dict(tool=tool, arguments=arguments, attempted=True, returned=False,
                       confirmed=False, outcome='unknown')
        self.attempts.append(attempt)
        self.ledger.event('input_attempt', **attempt)
        try:
            row = await self.transport(tool, arguments)
        except BaseException as error:
            self.ledger.event('input_unknown', error=type(error).__name__, **attempt)
            raise
        attempt['returned'] = True
        self.ledger.event('input_receipt', receipt=row, **attempt)
        require(isinstance(row, dict) and row.get('tool') == tool and row.get('arguments') == arguments
                and row.get('is_error') is False and row.get('text') == [expected_text],
                '原工具回执失败、未知或与冻结协议不符')
        attempt.update(confirmed=True, outcome='confirmed')
        self.ledger.event('input_returned', **attempt)
        self.ledger.desktop_allowed()
        return row

    @staticmethod
    def point(target, point):
        rect = target['rect']
        require(len(point) == 2 and all(type(x) is int for x in point)
                and rect[0] < point[0] < rect[2] and rect[1] < point[1] < rect[3],
                '点击不在实际图像换算后的物理窗口矩形内')

    async def click(self, point, *, dirty=False):
        target = await self.observe(dirty=dirty)
        self.point(target, point)
        await self._send('Click', dict(loc=list(point)), f'Single left clicked at ({point[0]},{point[1]}).')
        # 普通输入始终保留前景后验；此处没有关闭特例。
        await self.observe(dirty=dirty)

    async def delete(self):
        target = await self.observe(dirty=False)
        require(target.get('focus_kind') == 'canvas', 'Delete不能抢占文本或未知焦点')
        await self._send('Shortcut', dict(shortcut='delete'), 'Pressed delete.')
        await self.observe(dirty=True)

    async def capture(self, *, stage='main', dirty=False):
        target = await self.observe(stage=stage, dirty=dirty)
        self.ledger.desktop_allowed()
        shot = await self.snapshot_api(target)
        self.ledger.desktop_allowed()
        after = await self.observe(stage=stage, dirty=dirty)
        require(shot.hwnd == target['hwnd'] == after['hwnd']
                and tuple(target['rect']) == shot.physical_rect == tuple(after['rect']),
                '截图前后目标或物理矩形改变')
        return shot
