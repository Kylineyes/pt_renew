"""可信窗口/只读UIA适配的假API测试；零真实窗口、COM、截图和输入。"""
import copy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from async_product_client.native import ProductNative, ReadOnlyUia, ReadOnlyWin32
from async_product_client.product import WindowPolicy, MODAL_TITLE
from test_async_product_client import Rig


class Fixture:
    def __init__(self, root, *, dirty=False):
        self.rig = Rig(root); self.rig.launch(); self.rig.dirty = dirty
        self.creator = SimpleNamespace(process=self.rig.process, inspect_created=self.rig.inspect)
        main = self.rig.main_window()
        self.rows = {99: {k: main[k] for k in ('pid', 'hwnd', 'title', 'cls', 'owner')}}
        self.rows[99].update(enabled=not dirty, visible=True)
        self.rects = {99: main['rect']}
        if dirty:
            modal = self.rig.modal_window()
            self.rows[101] = {k: modal[k] for k in ('pid', 'hwnd', 'title', 'cls', 'owner')}
            self.rows[101].update(enabled=True, visible=True)
            self.rects[101] = modal['rect']
        self.foreground = 101 if dirty else 99
        self.desktop = 'Default'
        self.calls = []
        self.uia_rows = {}
        for hwnd, row in self.rows.items():
            self.uia_rows[hwnd] = dict(root=dict(pid=42, hwnd=hwnd, name=row['title'], cls=row['cls'], enabled=row['enabled']),
                                       readonly=True, modal=dirty and hwnd == 101,
                                       focus=dict(pid=42, descendant_verified=True, automation_id='boardCanvas',
                                                  name='板图工作区', control_type=50033, enabled=True, offscreen=False), buttons=[])
        if dirty:
            self.uia_rows[101]['buttons'] = [dict(pid=42, name=name, rect=rect, control_type=50000,
                                                 descendant_verified=True, enabled=True, offscreen=False,
                                                 default=name == '取消')
                                               for name, rect in self.rig.modal_window()['buttons'].items()]
        fixture = self
        class Api:
            def desktop(self): fixture.calls.append('desktop'); return fixture.desktop
            def foreground(self): fixture.calls.append('foreground'); return fixture.foreground
            def enumerate(self, pid): fixture.calls.append('enumerate'); return list(fixture.rows)
            def window(self, hwnd): fixture.calls.append(('window', hwnd)); return copy.deepcopy(fixture.rows[hwnd])
            def geometry(self, hwnd):
                fixture.calls.append(('geometry', hwnd))
                return dict(rect=list(fixture.rects[hwnd]), coordinate_space='physical-desktop-pixels',
                            thread_context_restored=True, dpi_context='PER_MONITOR_AWARE_V2')
        class Uia:
            def inspect(self, hwnd, pid): fixture.calls.append(('uia', hwnd)); return copy.deepcopy(fixture.uia_rows[hwnd])
        self.api, self.uia = Api(), Uia()
        self.collector = ProductNative(self.rig.ledger, self.rig.owner, self.creator, uia=self.uia, api=self.api, enabled=True)

    async def run(self):
        with self.rig.ledger.operation('native', self.rig.ledger.token):
            return await self.collector()


class NativeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, **kwargs):
        path = self.root / str(len(list(self.root.iterdir()))); path.mkdir()
        return Fixture(path, **kwargs)

    async def test_precise_main_and_same_class_modal_are_distinguished_by_hwnd_and_owner(self):
        for dirty in (False, True):
            f = self.fixture(dirty=dirty)
            row = await f.run()
            target = f.rig.policy.check(row, f.rig.owner.identity, stage='dirty-modal' if dirty else 'main', dirty=dirty)
            self.assertEqual(target['hwnd'], 101 if dirty else 99)
            self.assertEqual(target['birth'], 100)
            if dirty:
                self.assertEqual(target['default_button'], '取消')
                self.assertEqual(set(target['buttons']), {'放弃更改', '取消'})
                self.assertEqual(row['windows'][0]['cls'], row['windows'][1]['cls'])
                self.assertFalse(row['windows'][0]['enabled'])
            else:
                self.assertEqual(target['focus_kind'], 'canvas')
            self.assertEqual(f.rig.calls, [])
            self.assertEqual(f.rig.ledger.not_before_ns, 0)

    async def test_disabled_busy_cooldown_and_missing_uia_make_zero_native_queries(self):
        for mode in ('disabled', 'busy', 'cooldown', 'uia'):
            f = self.fixture()
            if mode == 'disabled': f.collector.enabled = False
            if mode == 'busy': f.rig.ledger.busy = True
            if mode == 'cooldown': f.rig.ledger.not_before_ns = f.rig.clock.now + 120_000_000_000
            if mode == 'uia': f.collector.uia = None
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.calls, [])

    async def test_locked_non_target_foreground_missing_main_or_recycled_pid_refuses(self):
        for mode in ('locked', 'foreground', 'main', 'pid', 'object'):
            f = self.fixture()
            if mode == 'locked': f.desktop = 'Winlogon'
            if mode == 'foreground': f.foreground = 888
            if mode == 'main': f.rows = {}
            if mode == 'pid': f.rows[99]['pid'] = 43
            if mode == 'object': f.creator.process = object()
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.rig.calls, [])
            self.assertEqual(f.collector.observations, [])

    async def test_uia_root_identity_and_title_class_enabled_crosscheck_are_mandatory(self):
        for key, value in [('pid', 43), ('hwnd', 100), ('name', 'other'), ('cls', 'Tk'), ('enabled', False)]:
            f = self.fixture(); f.uia_rows[99]['root'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.collector.observations, [])

    async def test_focus_unknown_text_other_pid_or_offscreen_never_promotes_to_canvas(self):
        cases = [('automation_id', 'search', 'unknown'), ('control_type', 50004, 'text'),
                 ('descendant_verified', False, 'unknown'), ('pid', 43, 'unknown'),
                 ('enabled', False, 'unknown'), ('offscreen', True, 'unknown')]
        for field, value, expected in cases:
            f = self.fixture(); f.uia_rows[99]['focus'][field] = value
            row = await f.run()
            self.assertEqual(row['foreground']['focus_kind'], expected)
            self.assertEqual(f.rig.calls, [])

    async def test_modal_owner_default_button_duplicate_wrong_pid_outside_rect_and_nonmodal_fail_closed(self):
        for mode in ('owner', 'default', 'duplicate', 'pid', 'outside', 'nonmodal', 'main-enabled', 'unknown-default'):
            f = self.fixture(dirty=True)
            buttons = f.uia_rows[101]['buttons']
            if mode == 'owner': f.rows[101]['owner'] = 123
            if mode == 'default': buttons[0]['default'], buttons[1]['default'] = True, False
            if mode == 'duplicate': buttons.append(dict(buttons[0]))
            if mode == 'pid': buttons[0]['pid'] = 43
            if mode == 'outside': buttons[0]['rect'] = [0, 0, 100, 100]
            if mode == 'nonmodal': f.uia_rows[101]['modal'] = False
            if mode == 'main-enabled':
                f.rows[99]['enabled'] = True; f.uia_rows[99]['root']['enabled'] = True
            if mode == 'unknown-default': buttons[0]['default'] = None
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.rig.calls, [])

    async def test_foreground_geometry_or_hwnd_set_changed_during_probe_cannot_return_snapshot(self):
        for mode in ('foreground', 'geometry', 'handles', 'desktop', 'window'):
            f = self.fixture()
            original = f.uia.inspect
            def inspect(hwnd, pid):
                row = original(hwnd, pid)
                if mode == 'foreground': f.foreground = 100
                if mode == 'geometry': f.rects[99][0] += 10
                if mode == 'handles':
                    f.rows[102] = dict(f.rows[99], hwnd=102); f.rects[102] = list(f.rects[99])
                if mode == 'desktop': f.desktop = 'Winlogon'
                if mode == 'window': f.rows[99]['title'] = 'changed'
                return row
            f.uia.inspect = inspect
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.collector.observations, [])

    async def test_other_window_or_focus_change_during_collection_is_caught_by_final_crosscheck(self):
        for mode in ('main-title', 'focus'):
            f = self.fixture(dirty=mode == 'main-title')
            original = f.uia.inspect
            calls = []
            def inspect(hwnd, pid):
                calls.append(hwnd)
                row = original(hwnd, pid)
                if mode == 'main-title' and hwnd == 101 and len(calls) <= 2:
                    f.rows[99]['title'] = 'changed while probing modal'
                if mode == 'focus' and len(calls) == 1:
                    f.uia_rows[99]['focus']['control_type'] = 50004
                return row
            f.uia.inspect = inspect
            with self.subTest(mode=mode), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.collector.observations, [])

    async def test_physical_dpi_restore_unknown_or_bad_geometry_does_not_reach_inputs(self):
        for field, value in [('coordinate_space', 'logical'), ('thread_context_restored', False)]:
            f = self.fixture()
            original = f.api.geometry
            f.api.geometry = lambda hwnd: dict(original(hwnd), **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError): await f.run()
            self.assertEqual(f.rig.calls, [])

    def test_default_win32_adapter_does_not_load_desktop_at_import_or_construction(self):
        api = ReadOnlyWin32()
        self.assertIsNone(api.user)
        self.assertFalse(hasattr(api, 'send_input'))
        self.assertFalse(hasattr(api, 'activate'))

    def test_uia_bridge_only_reads_bounded_subtree_and_focused_ancestry(self):
        trace = []
        class Control:
            def __init__(self, name, hwnd, control_type=50032, parent=None, state=0):
                self.Name, self.NativeWindowHandle, self.ControlType = name, hwnd, control_type
                self.ProcessId, self.ClassName, self.AutomationId = 42, 'Qt6120QWindowIcon', 'dialog'
                self.IsEnabled, self.IsOffscreen = True, False
                self.BoundingRectangle = SimpleNamespace(left=200, top=200, right=300, bottom=250)
                self.parent, self.state, self.children = parent, state, []
            def GetPattern(self, pattern): trace.append('pattern'); return SimpleNamespace(IsModal=True)
            def GetLegacyIAccessiblePattern(self): trace.append('legacy'); return SimpleNamespace(State=self.state)
            def GetChildren(self): trace.append('children'); return self.children
            def GetParentControl(self): trace.append('parent'); return self.parent
        root = Control(MODAL_TITLE, 101)
        discard = Control('放弃更改', 0, 50000, root)
        cancel = Control('取消', 0, 50000, root, state=0x100)
        root.children = [discard, cancel]
        uia = SimpleNamespace(__file__=str(self.root / 'package/windows_mcp/uia/__init__.py'),
                              PatternId=SimpleNamespace(WindowPattern=10009),
                              ControlFromHandle=lambda hwnd: root, GetFocusedControl=lambda: cancel)
        bridge = ReadOnlyUia(uia, package_root=self.root / 'package')
        result = bridge.inspect(101, 42)
        self.assertTrue(result['readonly'] and result['modal'])
        self.assertEqual([row['name'] for row in result['buttons'] if row['default']], ['取消'])
        self.assertTrue(result['focus']['descendant_verified'])
        self.assertTrue(all(name in ('pattern', 'legacy', 'children', 'parent') for name in trace))
        root.children = [root]
        with self.assertRaises(ValueError): bridge.inspect(101, 42)
        with self.assertRaises(ValueError): ReadOnlyUia(uia, package_root=self.root / 'wrong-package')


if __name__ == '__main__': unittest.main(verbosity=2)
