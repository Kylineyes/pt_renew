"""原Popen创建/原句柄身份适配；默认禁用，无查询PID接管、无强杀或现场命令入口。"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

from .core import positive, require


class OriginalHandleApi:
    """仅在显式调用时加载kernel32，使用Popen原句柄，不调用OpenProcess。"""

    def __init__(self):
        self.kernel = None

    def load(self):
        if self.kernel is None:
            import ctypes
            from ctypes import wintypes
            require(os.name == 'nt', '原句柄适配仅支持Windows')
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.GetCurrentProcess.argtypes = []
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            kernel.GetProcessId.argtypes = [wintypes.HANDLE]
            kernel.GetProcessId.restype = wintypes.DWORD
            kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
            kernel.GetProcessTimes.restype = wintypes.BOOL
            kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                         ctypes.POINTER(wintypes.DWORD)]
            kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.WaitForSingleObject.restype = wintypes.DWORD
            self.kernel = kernel
        return self.kernel

    def current_identity(self):
        import ctypes
        from ctypes import wintypes
        kernel = self.load()
        handle = kernel.GetCurrentProcess()
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        require(kernel.GetProcessId(handle) == os.getpid(), '当前客户端原句柄PID不符')
        return dict(pid=os.getpid(), birth=(times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
                    original_handle=True)

    def inspect(self, process):
        import ctypes
        from ctypes import wintypes
        require(isinstance(process, subprocess.Popen) and process.poll() is None, '只能核对创建时保存的存活原Popen')
        handle = int(process._handle)
        require(positive(handle), 'Popen原句柄不存在')
        kernel = self.load()
        require(kernel.WaitForSingleObject(handle, 0) == 258, '原句柄已退出或查询未知')
        require(kernel.GetProcessId(handle) == process.pid, '原Popen句柄与PID不匹配')
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        birth = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        image = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(image))
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        require(kernel.WaitForSingleObject(handle, 0) == 258 and kernel.GetProcessId(handle) == process.pid,
                '核对期间原进程退出或身份变化')
        return dict(pid=process.pid, birth=birth, image=image.value, handle=handle, original_handle=True)


class OwnedProductProcess:
    """供ProductOwner注入的创建器；客户端自身持续持有Popen和实验owner身份。"""

    def __init__(self, ledger, *, kind, experiment_directory, board_copy, evidence_root,
                 enabled=False, popen=None, handle_api=None, owner_pid=None, registry=None, registry_key='product', initial_net=None):
        require(kind in ('net', 'copper'), '实验种类无效')
        self.ledger, self.kind = ledger, kind
        self.registry, self.registry_key = registry, registry_key
        self.initial_net = initial_net
        self.experiment_directory = Path(experiment_directory).resolve()
        self.board_copy = Path(board_copy).resolve()
        self.root = Path(evidence_root).resolve()
        self.enabled = enabled is True
        self.popen = popen or subprocess.Popen
        self.handle_api = handle_api or OriginalHandleApi()
        self.owner_pid = os.getpid() if owner_pid is None else owner_pid
        self.process = None
        self.identity = None
        self.used = False
        self.streams = []

    def __call__(self, argv, *, cwd, env):
        self.ledger.desktop_allowed()
        require(self.enabled and not self.used and self.process is None, '原Popen创建器默认禁用或机会已消费')
        require(positive(self.owner_pid) and self.owner_pid == os.getpid(), '实验owner必须是持续存活的当前客户端')
        require(len(argv) == 1 and Path(argv[0]).resolve() == Path(cwd).resolve() / 'pt-renew.exe',
                '创建器只能补充已核对实验EXE的固定参数')
        require(self.board_copy.is_file() and self.board_copy.name == 'board.pcb', '缺少本轮只读板副本')
        require(not self.root.exists() and not self.experiment_directory.exists(), '必须使用全新创建日志和应用实验目录')
        require(self.root != self.experiment_directory and not self.root.is_relative_to(self.experiment_directory),
                '应用事件目录必须与客户端日志目录分离')
        if self.initial_net is not None:
            from .file_dialog import NetFileSpec
            require(type(self.initial_net) is NetFileSpec and Path(self.initial_net.path).name == 'a.net',
                    '初始命令行网表只能是冻结A副本')
            self.initial_net.verify()
        self.used = True
        self.root.mkdir(parents=True, exist_ok=False)
        self.experiment_directory.mkdir(parents=True, exist_ok=False)
        try:
            for name in ('stdout.log', 'stderr.log'):
                self.streams.append((self.root / name).open('xb'))
            command = [argv[0], '--async-experiment-dir', str(self.experiment_directory),
                       '--async-experiment-kind', self.kind, '--async-experiment-owner', str(self.owner_pid),
                       '--async-experiment-skip', '1' if self.kind == 'net' else '0']
            if self.initial_net is not None: command += ['--netlist', self.initial_net.path]
            command.append(str(self.board_copy))
            self.ledger.desktop_allowed()
            self.ledger.event('product_popen_attempt', command=command, owner_pid=self.owner_pid,
                              stdout=str(self.root / 'stdout.log'), stderr=str(self.root / 'stderr.log'))
            self.ledger.desktop_allowed()
            # Popen原对象在任何身份回调前保存；不存在中间PowerShell或短命owner。
            self.process = self.popen(command, cwd=cwd, env=dict(env), stdin=subprocess.DEVNULL,
                                      stdout=self.streams[0], stderr=self.streams[1], shell=False,
                                      close_fds=True)
            require(self.process is not None, '创建结果未知，不允许重复启动')
            if self.registry is not None:
                self.registry.created(self.registry_key, self.process, role='product')
            return self.process
        except BaseException:
            if self.process is None:
                self.close_streams()
            raise

    def inspect_created(self, process):
        require(process is self.process and self.used, '禁止按PID或新Popen对象接管产品')
        self.identity = self.handle_api.inspect(process)
        require(self.identity['pid'] == process.pid and self.identity.get('original_handle') is True,
                '创建后的原句柄核验失败')
        if self.registry is not None:
            row = self.registry.entries[self.registry_key]
            if row['identity'] is None: self.registry.identified(self.registry_key, process, self.identity)
            else: require(row['identity'] == self.identity, '账本中的原产品身份改变')
        return dict(self.identity)

    def close_streams(self):
        for stream in self.streams:
            stream.close()

    def observe_exit(self):
        """本地原Popen退出后关闭日志；不触碰桌面，也不清除失败锁存。"""
        require(self.process is not None, '没有本创建器的原Popen')
        code = self.process.poll()
        require(type(code) is int, '原Popen尚未退出或状态未知')
        self.close_streams()
        if self.registry is not None: self.registry.exited(self.registry_key, self.process, code)
        self.ledger.event('product_creator_exit', pid=self.process.pid, original_popen=True, exit_code=code)
        return code
