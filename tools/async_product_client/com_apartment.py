"""独立子进程COM初始化计数；模块局部ctypes代理保留原API及返回值。"""
from __future__ import annotations

import atexit
import builtins
import ctypes
import gc
import importlib.abc
import importlib.machinery
import sys
import threading
from types import ModuleType

from .core import require


class ApartmentStopped(BaseException):
    """穿过原UIA的except Exception，确保停止检查不会被其初始化兼容分支吞掉。"""


class FunctionProxy:
    def __init__(self, function, name, trace):
        object.__setattr__(self, 'function', function)
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'trace', trace)

    def __getattr__(self, name): return getattr(self.function, name)
    def __setattr__(self, name, value): setattr(self.function, name, value)

    def __call__(self, *args):
        trace = self.trace
        require(threading.get_ident() == trace.thread, 'COM调用越过原STA线程')
        if self.name != 'CoUninitialize':
            try: trace.checkpoint()
            except BaseException as error:
                raise ApartmentStopped('COM原初始化检查点已停止：' + str(error)) from error
        else: require(trace.balance > 0, 'COM释放次数超过本线程已证实的初始化次数')
        row = dict(api=self.name, returned=False, thread=trace.thread)
        trace.calls.append(row)
        value = self.function(*args)
        row.update(returned=True, result=value)
        if self.name == 'CoUninitialize':
            trace.balance -= 1
        elif value is None or isinstance(value, int) and value >= 0:
            if self.name == 'CoInitializeEx':
                require(len(args) == 2 and args[1] == 2, 'COM初始化不是冻结STA模式')
            trace.balance += 1
        else:
            require(False, 'COM初始化原HRESULT失败，不能假定已取得一次初始化')
        row['balance'] = trace.balance
        return value


class OleProxy:
    def __init__(self, library, trace):
        self.library, self.trace, self.functions = library, trace, {}

    def __getattr__(self, name):
        value = getattr(self.library, name)
        if name not in ('CoInitialize', 'CoInitializeEx', 'CoUninitialize'): return value
        if name not in self.functions: self.functions[name] = FunctionProxy(value, name, self.trace)
        return self.functions[name]


class CtypesProxy(ModuleType):
    def __init__(self, source, trace):
        super().__init__('ctypes')
        self.source, self.trace = source, trace

    def __getattr__(self, name):
        if name in ('OleDLL', 'WinDLL'):
            original = getattr(self.source, name)
            def load(path, *args, **kwargs):
                library = original(path, *args, **kwargs)
                return self.trace.ole(library) if str(path).casefold() in ('ole32', 'ole32.dll') else library
            return load
        if name == 'windll':
            source, trace = self.source.windll, self.trace
            class Loader:
                def __getattr__(self, name):
                    library = getattr(source, name)
                    return trace.ole(library) if name.casefold() == 'ole32' else library
            return Loader()
        return getattr(self.source, name)


class ImportLoader(importlib.abc.Loader):
    def __init__(self, original, trace): self.original, self.trace = original, trace
    def create_module(self, spec): return self.original.create_module(spec)

    def exec_module(self, module):
        original_import = builtins.__import__
        proxy = CtypesProxy(ctypes, self.trace)
        def local_import(name, globals=None, locals=None, fromlist=(), level=0):
            imported = original_import(name, globals, locals, fromlist, level)
            if name == 'atexit' and module.__name__ == 'comtypes':
                trace = self.trace
                class ExitProxy:
                    def __getattr__(self, name): return getattr(imported, name)
                    def register(self, callback, *args, **kwargs):
                        trace.shutdown_callbacks.append((callback, args, kwargs))
                        return callback
                return ExitProxy()
            return proxy if name == 'ctypes' or name.startswith('ctypes.') and not fromlist else imported
        module.__dict__['__builtins__'] = dict(vars(builtins), __import__=local_import)
        self.original.exec_module(module)
        if module.__name__ == 'windows_mcp.uia.core':
            # 原enums的星号导出含ctypes，会覆盖前面的局部import；单例延迟创建前必须重新绑定同一代理。
            module.ctypes = proxy
            require(module.ctypes is proxy, 'UIA星号导入后ctypes代理丢失')
            original_time = module.time
            trace = self.trace
            class TimeProxy:
                def __getattr__(self, name): return getattr(original_time, name)
                def sleep(self, seconds):
                    trace.checkpoint()
                    raise ValueError('只读探针拒绝原UIA内部等待重试，保留第一次异常')
            module.time = TimeProxy()


class ApartmentTrace(importlib.abc.MetaPathFinder):
    def __init__(self, *, checkpoint=lambda: None, ole=None):
        self.checkpoint = checkpoint
        self.thread = threading.get_ident()
        self.shutdown_callbacks = []
        self.calls, self.balance, self.closed = [], 0, False
        self.library = ole
        self.proxies = {}
        self.installed = False

    def ole(self, library):
        key = id(library)
        if key not in self.proxies: self.proxies[key] = OleProxy(library, self)
        return self.proxies[key]

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in ('comtypes', 'windows_mcp.uia.core'): return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        require(spec is not None and spec.loader is not None, 'COM模块缺少原冻结加载器')
        spec.loader = ImportLoader(spec.loader, self)
        return spec

    def __enter__(self):
        require('comtypes' not in sys.modules and 'windows_mcp.uia' not in sys.modules,
                'COM计数必须在首次冻结依赖导入之前安装')
        require(getattr(sys, 'coinit_flags', 2) == 2, '独立探针的comtypes默认线程模型不是STA')
        self.checkpoint()
        sys.meta_path.insert(0, self); self.installed = True
        try:
            library = self.library if self.library is not None else ctypes.OleDLL('ole32')
            ole = self.ole(library)
            ole.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
            ole.CoInitializeEx.restype = ctypes.c_long
            ole.CoUninitialize.argtypes, ole.CoUninitialize.restype = [], None
            ole.CoInitializeEx(None, 2)
            self.library = library
            return self
        except BaseException:
            if self in sys.meta_path: sys.meta_path.remove(self)
            self.installed = False
            raise

    def close(self):
        require(not self.closed and threading.get_ident() == self.thread, 'COM清理重复或离开原线程')
        self.closed = True
        try:
            core = sys.modules.get('windows_mcp.uia.core')
            if core is not None:
                core._AutomationClient._instance = None
            gc.collect()
            for callback, args, kwargs in reversed(self.shutdown_callbacks): callback(*args, **kwargs)
            self.shutdown_callbacks.clear()
            ole = self.ole(self.library)
            while self.balance > 0: ole.CoUninitialize()
            require(self.balance == 0 and all(row['returned'] and 'balance' in row for row in self.calls),
                    'COM初始化/释放证据不完整')
        finally:
            if self in sys.meta_path: sys.meta_path.remove(self)
            self.installed = False

    def report(self):
        return dict(thread=self.thread, balance=self.balance, calls=self.calls,
                    balanced=self.closed and self.balance == 0
                    and all(row['returned'] and 'balance' in row for row in self.calls))

    def __exit__(self, kind, error, traceback):
        try: self.close()
        except BaseException as cleanup_error:
            if error is None: raise
            error.com_cleanup_error = type(cleanup_error).__name__ + ': ' + str(cleanup_error)


def validate_com_report(row):
    require(isinstance(row, dict) and type(row.get('thread')) is int and row['thread'] > 0
            and row.get('balanced') is True and type(row.get('balance')) is int and row['balance'] == 0
            and isinstance(row.get('calls'), list) and row['calls'], 'COM平衡原记录缺失或无效')
    balance = 0
    for call in row['calls']:
        require(call.get('thread') == row['thread'] and call.get('returned') is True
                and call.get('api') in ('CoInitialize', 'CoInitializeEx', 'CoUninitialize'), 'COM原线程/API/返回证据不符')
        if call['api'] == 'CoUninitialize': balance -= 1
        else:
            value = call.get('result')
            require(value is None or type(value) is int and value >= 0, 'COM初始化原HRESULT失败')
            balance += 1
        require(balance >= 0 and type(call.get('balance')) is int and call['balance'] == balance,
                'COM初始化/释放原顺序或余数不一致')
    require(balance == 0, 'COM原记录未归零')
    return row
