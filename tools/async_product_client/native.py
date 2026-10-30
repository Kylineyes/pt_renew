"""可信原生窗口采集与只读UIA桥接；默认禁用，不激活、截图或发送输入。"""
from __future__ import annotations

import inspect
import os
from pathlib import Path

from .core import positive, require
from .product import MODAL_TITLE
from .file_dialog import FILE_CLASS, FILE_TITLE
from .commands import COMMANDS


class ReadOnlyWin32:
    def __init__(self):
        self.user = None

    def load(self):
        if self.user is None:
            import ctypes
            from ctypes import wintypes
            require(os.name == 'nt', '窗口采集仅支持Windows')
            user = ctypes.WinDLL('user32', use_last_error=True)
            signatures = {
                'SetThreadDpiAwarenessContext': (ctypes.c_void_p, [ctypes.c_void_p]),
                'GetWindowRect': (wintypes.BOOL, [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]),
                'GetForegroundWindow': (wintypes.HWND, []),
                'GetWindowThreadProcessId': (wintypes.DWORD, [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]),
                'IsWindowVisible': (wintypes.BOOL, [wintypes.HWND]),
                'IsWindowEnabled': (wintypes.BOOL, [wintypes.HWND]),
                'GetWindow': (wintypes.HWND, [wintypes.HWND, wintypes.UINT]),
                'GetWindowTextW': (ctypes.c_int, [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]),
                'GetClassNameW': (ctypes.c_int, [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]),
                'OpenInputDesktop': (wintypes.HANDLE, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]),
                'CloseDesktop': (wintypes.BOOL, [wintypes.HANDLE]),
                'GetUserObjectInformationW': (wintypes.BOOL, [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                                                            wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)])}
            for name, (result, arguments) in signatures.items():
                method = getattr(user, name); method.restype, method.argtypes = result, arguments
            self.user = user
        return self.user

    def desktop(self):
        import ctypes
        from ctypes import wintypes
        user = self.load()
        handle = user.OpenInputDesktop(0, False, 1)
        require(bool(handle), '无法读取当前输入桌面')
        try:
            name = ctypes.create_unicode_buffer(512); needed = wintypes.DWORD()
            require(bool(user.GetUserObjectInformationW(handle, 2, name, ctypes.sizeof(name), ctypes.byref(needed))),
                    '输入桌面名称未知')
            return name.value
        finally:
            require(bool(user.CloseDesktop(handle)), '输入桌面句柄释放失败')

    def foreground(self):
        hwnd = self.load().GetForegroundWindow()
        require(positive(hwnd), '前景HWND未知')
        return hwnd

    def enumerate(self, pid):
        import ctypes
        from ctypes import wintypes
        user = self.load()
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user.EnumWindows.argtypes, user.EnumWindows.restype = [callback_type, wintypes.LPARAM], wintypes.BOOL
        found, errors = [], []
        def visit(hwnd, param):
            try:
                process = wintypes.DWORD()
                if user.IsWindowVisible(hwnd):
                    require(positive(user.GetWindowThreadProcessId(hwnd, ctypes.byref(process))), '窗口枚举PID未知')
                    if process.value == pid: found.append(hwnd)
                return True
            except BaseException as error:
                errors.append(error)
                return False
        callback = callback_type(visit)
        require(bool(user.EnumWindows(callback, 0)) and not errors, '可见窗口枚举失败')
        require(len(found) == len(set(found)), '原生窗口枚举重复HWND')
        return found

    def window(self, hwnd):
        import ctypes
        from ctypes import wintypes
        user = self.load()
        pid = wintypes.DWORD()
        require(positive(user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))) and positive(pid.value),
                '窗口归属PID未知')
        title, cls = ctypes.create_unicode_buffer(32768), ctypes.create_unicode_buffer(512)
        user.GetWindowTextW(hwnd, title, len(title))
        require(user.GetClassNameW(hwnd, cls, len(cls)) > 0, '窗口类未知')
        return dict(hwnd=hwnd, pid=pid.value, title=title.value, cls=cls.value,
                    owner=user.GetWindow(hwnd, 4) or 0, enabled=bool(user.IsWindowEnabled(hwnd)),
                    visible=bool(user.IsWindowVisible(hwnd)))

    def geometry(self, hwnd):
        from control_geometry import physical_window_rect
        return physical_window_rect(hwnd, self.load())


class ReadOnlyUia:
    """只读已冻结模块；调用方负责COM线程初始化及有界探针生命周期，不接受外部UIA JSON。"""

    def __init__(self, uia, *, package_root, checkpoint=None):
        root = Path(package_root).resolve()
        require(Path(uia.__file__).resolve().is_relative_to(root / 'windows_mcp/uia'), 'UIA模块不来自冻结包')
        self.uia = uia
        self.checkpoint = checkpoint or (lambda: None)

    def element(self, control):
        self.checkpoint()
        require(control is not None, 'UIA控件不存在')
        fields = {'pid': ('ProcessId', int), 'hwnd': ('NativeWindowHandle', int), 'name': ('Name', str),
                  'cls': ('ClassName', str), 'automation_id': ('AutomationId', str),
                  'control_type': ('ControlType', int), 'enabled': ('IsEnabled', bool), 'offscreen': ('IsOffscreen', bool)}
        row = {}
        for name, (attribute, convert) in fields.items():
            self.checkpoint()
            row[name] = convert(getattr(control, attribute))
        return row

    def inspect(self, hwnd, pid):
        self.checkpoint()
        root = self.uia.ControlFromHandle(hwnd)
        root_row = self.element(root)
        require(root_row['pid'] == pid and root_row['hwnd'] == hwnd, 'UIA根身份与原HWND/PID不同')
        self.checkpoint()
        pattern = root.GetPattern(self.uia.PatternId.WindowPattern)
        self.checkpoint()
        result = dict(root=root_row, modal=bool(pattern.IsModal) if pattern else None,
                      buttons=[], focus=None, readonly=True)
        file_dialog = root_row['name'] == FILE_TITLE and root_row['cls'] == FILE_CLASS
        main_commands = root_row['automation_id'] == 'mainWindow'
        if main_commands: result['commands'] = []
        if file_dialog: result['file_elements'] = []
        if root_row['name'] == MODAL_TITLE or file_dialog or main_commands:
            pending, count = [(root, 0)], 0
            while pending:
                control, depth = pending.pop()
                count += 1
                require(count <= (2048 if main_commands else 256) and depth <= (16 if main_commands else 8),
                        'UIA只读子树超出冻结数量/深度边界')
                row = self.element(control)
                require(row['pid'] == pid, 'UIA模态子树混入其他PID')
                if main_commands and row['automation_id'] in COMMANDS:
                    require(row['control_type'] == 50000 and row['name'] == COMMANDS[row['automation_id']],
                            'NET可见命令objectName/名称/类型不符')
                    self.checkpoint(); box = control.BoundingRectangle
                    row.update(rect=[box.left, box.top, box.right, box.bottom], descendant_verified=True)
                    result['commands'].append(row)
                elif file_dialog and ((row['control_type'] == 50004 and row['automation_id'] == '1148')
                                    or (row['control_type'] == 50000 and row['automation_id'] in ('1', '2'))):
                    self.checkpoint()
                    box = control.BoundingRectangle
                    row.update(rect=[box.left, box.top, box.right, box.bottom], descendant_verified=True)
                    if row['control_type'] == 50004:
                        self.checkpoint()
                        value = control.GetPattern(self.uia.PatternId.ValuePattern)
                        require(value is not None, '文件名控件不支持只读ValuePattern')
                        self.checkpoint(); row['value'] = value.Value
                        self.checkpoint(); row['read_only'] = bool(value.IsReadOnly)
                    result['file_elements'].append(row)
                elif row['control_type'] == 50000 and not file_dialog and not main_commands:
                    require(row['name'] in ('放弃更改', '取消'), 'dirty模态出现未知按钮')
                    self.checkpoint()
                    box = control.BoundingRectangle
                    self.checkpoint()
                    legacy = control.GetLegacyIAccessiblePattern()
                    self.checkpoint()
                    row.update(rect=[box.left, box.top, box.right, box.bottom],
                               default=bool(int(legacy.State) & 0x100) if legacy else None,
                               descendant_verified=True)
                    result['buttons'].append(row)
                self.checkpoint()
                for child in control.GetChildren(): pending.append((child, depth + 1))
        self.checkpoint()
        focused = self.uia.GetFocusedControl()
        if focused is not None:
            focus = self.element(focused)
            parent, matched = focused, False
            for _ in range(16):
                if parent is None: break
                parent_row = self.element(parent)
                if parent_row['pid'] != pid: break
                if parent_row['hwnd'] == hwnd:
                    matched = True; break
                self.checkpoint()
                parent = parent.GetParentControl()
            focus['descendant_verified'] = matched
            result['focus'] = focus
        return result


async def query_uia(uia, hwnd, pid):
    row = uia.inspect(hwnd, pid)
    return await row if inspect.isawaitable(row) else row


class ProductNative:
    def __init__(self, ledger, owner, creator, *, uia, enabled=False, api=None):
        self.ledger, self.owner, self.creator = ledger, owner, creator
        self.uia, self.api = uia, api or ReadOnlyWin32()
        self.enabled = enabled is True
        self.observations = []

    def identity(self):
        self.owner.alive()
        require(self.owner.process is self.creator.process
                and self.creator.inspect_created(self.owner.process) == self.owner.process_identity,
                '可信窗口采集的原Popen/句柄身份改变')
        return self.owner.identity

    async def __call__(self):
        self.ledger.desktop_allowed()
        require(self.enabled and self.uia is not None, '窗口采集默认禁用或缺少可信只读UIA探针')
        identity = self.identity()
        desktop = self.api.desktop()
        require(desktop == 'Default', '锁屏或输入桌面未知')
        foreground = self.api.foreground()
        handles = self.api.enumerate(identity.pid)
        require(identity.hwnd in handles and foreground in handles and len(handles) == len(set(handles)),
                '精确主HWND缺失、非目标前景或窗口枚举重复')
        windows, raw_windows, geometries, uia_rows = [], {}, {}, {}
        for hwnd in handles:
            self.ledger.desktop_allowed()
            before = self.api.window(hwnd)
            require(before['pid'] == identity.pid and before['visible'] is True, '窗口PID/可见性改变')
            geometry = self.api.geometry(hwnd)
            require(geometry.get('coordinate_space') == 'physical-desktop-pixels'
                    and geometry.get('thread_context_restored') is True, '物理rect或DPI线程恢复未知')
            uia = await query_uia(self.uia, hwnd, identity.pid)
            self.ledger.desktop_allowed()
            root = uia.get('root', {})
            require(uia.get('readonly') is True and root.get('pid') == identity.pid and root.get('hwnd') == hwnd
                    and root.get('name') == before['title'] and root.get('cls') == before['cls']
                    and root.get('enabled') == before['enabled'], '只读UIA根与原生窗口身份不符')
            require(self.api.window(hwnd) == before and self.api.geometry(hwnd) == geometry,
                    'UIA采集前后原窗口/物理rect改变')
            self.identity()
            raw_windows[hwnd], geometries[hwnd], uia_rows[hwnd] = before, geometry, uia
            row = dict(before, birth=identity.birth, image=identity.image, **geometry, focus_kind='unknown')
            focus = uia.get('focus') or {}
            if (focus.get('pid') == identity.pid and focus.get('descendant_verified') is True
                    and focus.get('enabled') is True and focus.get('offscreen') is False):
                if focus.get('automation_id') == 'boardCanvas' and focus.get('name') == '板图工作区' and focus.get('control_type') == 50033:
                    row['focus_kind'] = 'canvas'
                elif focus.get('control_type') in (50004, 50030): row['focus_kind'] = 'text'
            if 'commands' in uia:
                commands = {}
                for button in uia['commands']:
                    key = button.get('automation_id')
                    require(key in COMMANDS and key not in commands, 'NET可见命令ID未知或重复')
                    commands[key] = button
                row['commands'] = commands
            if before['title'] == MODAL_TITLE:
                require(hwnd != identity.hwnd and before['owner'] == identity.hwnd and uia.get('modal') is True,
                        'dirty模态缺少同原生owner及UIA模态证明')
                buttons, default = {}, []
                for button in uia.get('buttons', []):
                    name, box = button.get('name'), button.get('rect', [])
                    require(name in ('放弃更改', '取消') and name not in buttons and button.get('pid') == identity.pid
                            and button.get('control_type') == 50000 and button.get('descendant_verified') is True
                            and button.get('enabled') is True and button.get('offscreen') is False
                            and type(button.get('default')) is bool and len(box) == 4
                            and all(type(x) is int for x in box)
                            and row['rect'][0] <= box[0] < box[2] <= row['rect'][2]
                            and row['rect'][1] <= box[1] < box[3] <= row['rect'][3], 'dirty模态按钮归属/物理矩形/默认状态未知')
                    buttons[name] = box
                    if button['default']: default.append(name)
                require(set(buttons) == {'放弃更改', '取消'} and default == ['取消'], 'dirty模态必须唯一默认取消和明确放弃按钮')
                row.update(modal=True, default_button='取消', buttons=buttons)
            if before['cls'] == FILE_CLASS and before['title'] == FILE_TITLE:
                require(hwnd != identity.hwnd and before['owner'] == identity.hwnd and uia.get('modal') is True,
                        '原生文件框owner或模态关系不符')
                elements = {}
                for element in uia.get('file_elements', []):
                    key = {'1148': 'filename', '1': 'open', '2': 'cancel'}.get(element.get('automation_id'))
                    require(key is not None and key not in elements, '文件框控件ID缺失或重复')
                    elements[key] = element
                row.update(modal=True, file_controls=elements, file_focus=focus)
            windows.append(row)
        main = next(row for row in windows if row['hwnd'] == identity.hwnd)
        if any(row.get('modal') is True for row in windows):
            require(main['enabled'] is False, 'dirty模态存在时主窗并未禁用')
        self.ledger.desktop_allowed()
        for hwnd in handles:
            self.ledger.desktop_allowed()
            uia_after = await query_uia(self.uia, hwnd, identity.pid)
            self.ledger.desktop_allowed()
            require(self.api.window(hwnd) == raw_windows[hwnd] and self.api.geometry(hwnd) == geometries[hwnd]
                    and uia_after == uia_rows[hwnd],
                    '采集其他窗口期间原窗口/焦点/按钮状态改变')
        require(self.api.desktop() == desktop and self.api.foreground() == foreground
                and set(self.api.enumerate(identity.pid)) == set(handles), '窗口采集结束前桌面/前景/窗口集合改变')
        self.identity()
        result = dict(input_desktop=desktop, locked=False, foreground_stable=True,
                      foreground=next(row for row in windows if row['hwnd'] == foreground), windows=windows)
        self.observations.append(result)
        self.ledger.event('product_native_observation', result=result, readonly=True)
        return result
