"""只读提取安装 Shortcut 原 AST，以假 user32 验证键序列；不导入桌面包或加载 DLL。"""
from __future__ import annotations

import argparse
import ast
import __future__
import builtins
import copy
import ctypes
from ctypes import wintypes
try:
    import ctypes._layout as ctypes_layout
except ImportError:
    ctypes_layout = None
import enum
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

DEFAULT_SOURCE = Path('C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Lib/site-packages/windows_mcp')
SOURCE_FILES = ('tools/input.py', 'desktop/service.py', 'uia/core.py', 'uia/enums.py')
SCAN_FIXTURE = {0x10: 0x2A, 0x49: 0x17, 0x53: 0x1F, 0x0D: 0x1C,
                0x1B: 1, 0x7A: 0x57, 0x73: 0x3E, 0x11: 0x1D, 0x12: 0x38,
                0x28: 0x50, 0x26: 0x48}
CASES = ('shift+i', 'Shift+I', ' shift + i ', 'shift+s', 'enter', 'return', 'esc',
         'escape', 'down', 'up', 'i', 'I', 's', 'f11+p', 'lshift+i', 'shift+中', '😀', '+')


def compile_selected(nodes, scope):
    """只执行选中定义；删除装饰器，拒绝导入或动态执行等旁路。"""
    nodes = copy.deepcopy(nodes)
    denied = {'eval', 'exec', 'open', '__import__', 'compile', 'getattr', 'setattr', 'globals', 'locals', 'vars'}
    module = ast.Module(body=nodes, type_ignores=[])
    for node in ast.walk(module):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise ValueError('选中 AST 含不允许的导入或作用域修改')
        if isinstance(node, ast.Name) and node.id.startswith('__'):
            raise ValueError('选中 AST 含不允许的内建命名空间访问')
        if isinstance(node, ast.Attribute) and node.attr.startswith('__'):
            raise ValueError('选中 AST 含不允许的反射属性')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in denied:
            raise ValueError('选中 AST 含动态执行或文件访问')
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.decorator_list = []
    exec(compile(ast.fix_missing_locations(module), '<只读安装函数原AST+假API>', 'exec',
                 flags=__future__.annotations.compiler_flag, dont_inherit=True), scope)


def find_definition(tree, name, kind):
    matches = [n for n in ast.walk(tree) if isinstance(n, kind) and getattr(n, 'name', None) == name]
    if len(matches) != 1:
        raise ValueError('原定义不唯一或缺失：' + name)
    return matches[0]


def find_assignment(tree, name):
    matches = [n for n in tree.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(matches) != 1:
        raise ValueError('原常量不唯一或缺失：' + name)
    return matches[0]


class ShortcutReplay:
    def __init__(self, source=DEFAULT_SOURCE):
        self.source = Path(source)
        self.contents = {name: (self.source/name).read_bytes() for name in SOURCE_FILES}
        self.trees = {name: ast.parse(data.decode('utf-8-sig')) for name, data in self.contents.items()}
        self.sources = [{'path': str(self.source/name), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                        for name, data in self.contents.items()]
        self.selected = []

    def unchanged(self):
        return all((self.source/name).read_bytes() == data for name, data in self.contents.items())

    def trace(self, shortcut, *, send_input_returns=(), scan_map=None, fail_checkpoint=False,
              keybd_raises_at=None):
        calls, sleeps, text_calls, control = [], [], [], []
        now = [0]
        returns = iter(send_input_returns)
        scans = SCAN_FIXTURE if scan_map is None else scan_map
        keyboard_calls = [0]
        def record(api, **fields):
            row = {'api': api, 'at_ns': now[0], **fields}
            calls.append(row)
            return row
        def keybd(vk, scan, flags, extra):
            keyboard_calls[0] += 1
            record('keybd_event', vk=int(vk), scan=int(scan), flags=int(flags), extra=int(extra))
            if keyboard_calls[0] == keybd_raises_at:
                raise RuntimeError('假 keybd_event 异常')
            return 0  # 原包装返回 None；此假返回不代表真实 void API 有成功码。
        def send_input(number, pointer, size):
            item = pointer._obj
            value = item.union.ki
            result = next(returns, 1)
            record('SendInput', count=int(number), size=int(size.value), input_type=int(item.type),
                   vk=int(value.wVk), scan=int(value.wScan), flags=int(value.dwFlags), result=result)
            return result
        def map_virtual_key(vk, mode):
            result = scans.get(int(vk), 0)
            record('MapVirtualKeyA', vk=int(vk), mode=int(mode), result=result)
            return result
        def forbidden_vk_scan(*args):
            raise AssertionError('公开 Shortcut 默认 charMode=True 不应查询 VkKeyScanW')
        def sleep(seconds):
            sleeps.append({'at_ns': now[0], 'seconds': seconds})
            now[0] += round(seconds*1e9)
        def checkpoint():
            control.append({'event': 'checkpoint', 'at_ns': now[0]})
            if fail_checkpoint:
                raise RuntimeError('假公开服务 checkpoint 拒绝')
        fake_ctypes = SimpleNamespace(Structure=ctypes.Structure, Union=ctypes.Union, wintypes=wintypes,
            c_int=ctypes.c_int, sizeof=ctypes.sizeof, byref=ctypes.byref,
            windll=SimpleNamespace(user32=SimpleNamespace(keybd_event=keybd, SendInput=send_input,
                MapVirtualKeyA=map_virtual_key, VkKeyScanW=forbidden_vk_scan)))
        # 白名单内建函数；不提供导入、真实 ctypes.windll 或文件/进程入口。
        safe_builtins = {name: getattr(builtins, name) for name in ('__build_class__', 'len', 'range', 'int',
            'str', 'ord', 'type', 'isinstance', 'enumerate', 'ValueError', 'TypeError')}
        def structure_import(name, *args, **kwargs):
            # Python 3.15 的 ctypes.Structure 元类会从受限命名空间请求已加载的 ctypes。
            # 源 AST 的 import/__import__ 已拒绝；此处不允许导入任何其它模块。
            if name == 'ctypes':
                return ctypes
            if name == 'ctypes._layout' and ctypes_layout is not None:
                return ctypes_layout
            raise ImportError('拒绝结构元类的其它导入：' + name)
        safe_builtins['__import__'] = structure_import
        scope = {'__name__': 'offline_shortcut_replay', '__builtins__': safe_builtins,
                 'ctypes': fake_ctypes, 'IntEnum': enum.IntEnum, 'IntFlag': enum.IntFlag,
                 'time': SimpleNamespace(sleep=sleep)}
        enums = self.trees['uia/enums.py']
        nodes = [find_definition(enums, name, ast.ClassDef) for name in
                 ('KeyboardEventFlag', 'InputType', 'Keys', 'MOUSEINPUT', 'KEYBDINPUT', 'HARDWAREINPUT', '_INPUTUnion', 'INPUT')]
        nodes += [find_assignment(enums, name) for name in ('SpecialKeyNames', 'CharacterCodes')]
        compile_selected(nodes, scope)
        core = self.trees['uia/core.py']
        core_nodes = [find_assignment(core, 'OPERATION_WAIT_TIME'), find_assignment(core, '_SCKeys')]
        core_nodes += [find_definition(core, name, ast.FunctionDef) for name in
                       ('keybd_event', '_CreateInput', 'KeyboardInput', 'SendInput', 'SendUnicodeChar', '_VKtoSC', 'SendKeys')]
        compile_selected(core_nodes, scope)
        def send_keys(text, **kwargs):
            text_calls.append({'text': text, 'kwargs': kwargs})
            return scope['SendKeys'](text, **kwargs)
        owner = SimpleNamespace(checkpoint_current=checkpoint,
            record_step_current=lambda: control.append({'event': 'record_step', 'at_ns': now[0]}))
        scope.update(get_controller=lambda: owner, uia=SimpleNamespace(SendKeys=send_keys))
        service = self.trees['desktop/service.py']
        service_nodes = [find_assignment(service, '_KEY_ALIASES'), find_definition(service, 'shortcut', ast.FunctionDef)]
        compile_selected(service_nodes, scope)
        desktop = SimpleNamespace(shortcut=lambda value: scope['shortcut'](None, value))
        scope['get_desktop'] = lambda: desktop
        tool_node = find_definition(self.trees['tools/input.py'], 'shortcut_tool', ast.FunctionDef)
        compile_selected([tool_node], scope)
        self.selected = [{'source': source, 'name': getattr(n, 'name', '常量'),
                          'line': n.lineno, 'end_line': n.end_lineno,
                          'ast_sha256': hashlib.sha256(ast.dump(n, include_attributes=False).encode()).hexdigest()}
                         for source, definitions in [('uia/enums.py', nodes), ('uia/core.py', core_nodes),
                             ('desktop/service.py', service_nodes), ('tools/input.py', [tool_node])]
                         for n in definitions]
        try:
            result = scope['shortcut_tool'](shortcut)
            error = None
        except Exception as exc:
            result, error = None, {'type': type(exc).__name__, 'message': str(exc)}
        return {'shortcut': shortcut, 'simulation': {'send_input_returns': list(send_input_returns),
                    'empty_scan_map': scan_map == {}, 'fail_checkpoint': fail_checkpoint, 'keybd_raises_at': keybd_raises_at},
                'sendkeys': text_calls, 'calls': calls, 'sleeps': sleeps,
                'control': control, 'result': result, 'error': error, 'nominal_sleep_ns': now[0],
                'scan_fixture': {str(k): v for k, v in scans.items()},
                'note': 'MapVirtualKeyA和SendInput返回均为假值，不是现场扫描码/实际接收者；未执行装饰器/公门/线程/钩子'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE, help='只读安装Python源码根目录')
    parser.add_argument('--case', action='append', help='假回放的公开Shortcut参数，可重复')
    parser.add_argument('--output', type=Path, required=True, help='新建JSON，拒绝覆盖')
    args = parser.parse_args()
    # 排他性先于源码执行；全部输入只到内存假API。
    with args.output.open('x', encoding='utf-8') as output:
        replay = ShortcutReplay(args.source)
        results = [replay.trace(value) for value in (args.case or CASES)]
        results += [replay.trace('i', send_input_returns=(0, 1)), replay.trace('i', send_input_returns=(1, 0)),
                    replay.trace('shift+i', scan_map={}), replay.trace('shift+i', fail_checkpoint=True),
                    replay.trace('shift+i', keybd_raises_at=2)]
        if not replay.unchanged():
            raise RuntimeError('原源码输入字节发生变化')
        unexpected_errors = [row['error'] for row in results if row['error']
            and row['error']['type'] not in ('ValueError', 'RuntimeError')
            and not (row['shortcut'] == '+' and row['error']['type'] == 'TypeError'
                     and 'ord() expected a character' in row['error']['message'])]
        report = {'scope': '严格离线原AST+假键盘API；未导入桌面/COM/UIA包、未加载真实user32或发输入、未启动目标/控制服务或写新GO',
                  'sources': replay.sources, 'source_bytes_unchanged': True, 'unexpected_harness_errors': unexpected_errors,
                  'windows_mcp_modules_imported': sorted(name for name in sys.modules if name == 'windows_mcp' or name.startswith('windows_mcp.')),
                  'selected_definitions': replay.selected, 'results': results}
        json.dump(report, output, ensure_ascii=False, indent=2)
    if unexpected_errors:
        raise RuntimeError('假执行环境有未预期错误，不能把生成报告视为验证通过')
    print(json.dumps({'cases': len(results), 'sources': len(replay.sources), 'unchanged': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
