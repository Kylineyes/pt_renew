"""隔离修复的合成夹具回归；仅文件/假Popen，不启动原软件/控制服务/桌面。"""
import ast
import contextlib
import copy
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import legacy_runtime_config as isolation
import legacy_observation_owner as owner
import prepare_legacy_click_observation as click
import prepare_legacy_capture as capture
import prepare_legacy_state as state
import prepare_legacy_navigation as navigation

# 只读自己的历史driver/gate/submit模板；临时源、运行输入和所有计划均为合成数据。
SOURCE = Path('C:/Users/rikideng/orca/workspaces/pt_renew/review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate')
SITE = Path('C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Lib/site-packages/windows_mcp')
REPO = Path(__file__).resolve().parents[1]


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def config(slot):
    return f'''[log]
logfile={slot/'dosbox-startup.log'}
files=normal
exec=normal
gui=normal
misc=normal
[sdl]
fullscreen=false
output=opengl
autolock=false
windowposition=100,100
showmenu=true
[dosbox]
machine=vgaonly
memsize=16
fastbioslogo=true
quit warning=false
captures={slot/'captures'}
[cpu]
core=normal
cycles=fixed 10000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{slot/'runtime'}"
mount d "{slot/'runtime'}"
c:
cd \\pt
pt SYN1.PCB
'''


def junction(alias, target):
    if os.name == 'nt':
        result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(alias), str(target)], capture_output=True)
        if result.returncode: raise AssertionError(result.stderr)
    else: alias.symlink_to(target, target_is_directory=True)


def remove_alias(alias):
    if os.name == 'nt': os.rmdir(alias)
    else: alias.unlink()


@unittest.skipUnless((SOURCE/'desktop_session.py').is_file() and (SITE/'__main__.py').is_file(),
                     '需要本机只读历史自有模板和已装MCP源；不下载、不导入、不运行')
class RuntimeIsolationTests(unittest.TestCase):
    def setUp(self):
        evidence = REPO/'.local-analysis/ex-003-live'
        isolation.confined(evidence, REPO/'.local-analysis')
        evidence.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-isolation-', dir=evidence)
        self.root = Path(self.temp.name)
        self.install = self.root/'original'; self.install.mkdir()
        (self.install/'DATA.BIN').write_bytes(b'only synthetic input')
        (self.install/'TRAXEDIT.DFT').write_bytes(b'synthetic old defaults')
        self.physical = self.root/'archive-source'; self.physical.mkdir()
        old = self.physical/'slot-retry-01'
        (old/'inputs').mkdir(parents=True)
        (old/'inputs/SYN1.PCB').write_bytes(b'PCB FILE 4\r\nENDPCB\r\n')
        for name in ('desktop_session.py', 'review_gate.py', 'submit.py'):
            shutil.copyfile(SOURCE/name, self.physical/name)
        self.alias = self.root/'logical-source'; junction(self.alias, self.physical)
        self.logical_slot = self.alias/'slot-retry-01'
        (old/'SYN1.conf').write_text(config(self.logical_slot), encoding='utf-8')
        self.template = {'slot': str(self.logical_slot), 'base_python': sys.executable,
            'control_argv': [sys.executable, '-I', '-c',
                f'import site,runpy;site.addsitedir({str(SITE.parent)!r});runpy.run_module("windows_mcp",run_name="__main__")', 'serve'],
            'target': {'argv': [sys.executable, '-conf', str(old/'SYN1.conf')], 'input_sha256': digest(old/'inputs/SYN1.PCB'),
                       'executable_sha256': digest(sys.executable)},
            'frozen_files': [],
            'runtime_manifest': {'DATA.BIN': {'bytes': 20, 'sha256': digest(self.install/'DATA.BIN')},
                                 'SYN1.PCB': {'bytes': (old/'inputs/SYN1.PCB').stat().st_size, 'sha256': digest(old/'inputs/SYN1.PCB')}},
            'inputs_manifest': {'SYN1.PCB': {'bytes': (old/'inputs/SYN1.PCB').stat().st_size, 'sha256': digest(old/'inputs/SYN1.PCB')}}}
        self.template['runtime_manifest']['DATA.BIN']['bytes'] = (self.install/'DATA.BIN').stat().st_size
        dump(old/'live-plan.json', self.template)
        self.args = dict(source=str(self.alias), installation=str(self.install), session='fake-session', task='fake-task', dispatch='fake-dispatch')
        self.count = 0

    def tearDown(self):
        # 不递归跟随联接；明确只删除本用例创建的别名，再释放临时夹具。
        if self.alias.exists(): remove_alias(self.alias)
        self.temp.cleanup()

    def generated(self, generator=click.prepare):
        self.count += 1
        destination = self.root/('package-'+str(self.count))
        with contextlib.redirect_stdout(io.StringIO()): generator(destination=str(destination), **self.args)
        plan = json.loads((destination/'slot/live-plan.json').read_text(encoding='utf-8'))
        return destination, plan

    def test_real_logical_source_alias_is_rebound_for_every_generator(self):
        self.assertNotEqual(str(self.logical_slot), str(self.logical_slot.resolve()))
        text = (self.physical/'slot-retry-01/SYN1.conf').read_text(encoding='utf-8')
        self.assertEqual(text.count(str(self.logical_slot.resolve())), 0)  # 原事故精确复现。
        for generator in (click.prepare, capture.prepare_capture, state.prepare_state, navigation.prepare_navigation):
            with self.subTest(generator=generator.__name__):
                package, plan = self.generated(generator)
                result = isolation.validate_runtime_plan(plan, runtime_root=package/'slot', driver_path=package/'desktop_session.py')
                final = (package/'slot/SYN1.conf').read_text(encoding='utf-8')
                self.assertNotIn(str(self.logical_slot), final)
                self.assertNotIn(str(self.logical_slot.resolve()), final)
                self.assertTrue(result['logical_physical_equal'])
                self.assertEqual(final.count(str(package/'slot')), 4)
                self.assertEqual((package/'slot/runtime/pt/DATA.BIN').stat().st_nlink, 1)
                self.assertEqual(isolation.parse_config(final)[0]['sdl', 'output'], 'opengl')

    def test_each_derived_final_gate_rejects_corruption_introduced_after_base(self):
        def corrupt_after(base):
            def wrapper(**kwargs):
                base(**kwargs)
                path=Path(kwargs['destination'])/'slot/SYN1.conf'
                path.write_text(path.read_text(encoding='utf-8').replace('logfile=', 'unreviewed-path='),encoding='utf-8')
            return wrapper
        for module,dependency,base,generator in (
            (capture,'prepare',click.prepare,capture.prepare_capture),
            (state,'prepare_capture',capture.prepare_capture,state.prepare_state),
            (navigation,'prepare_capture',capture.prepare_capture,navigation.prepare_navigation)):
            with self.subTest(generator=generator.__name__), patch.object(module,dependency,side_effect=corrupt_after(base)):
                with self.assertRaises(ValueError):self.generated(generator)

    def test_template_missing_duplicate_or_unknown_commands_rejected_before_copy(self):
        template = config(self.logical_slot)
        variants = [template.replace('logfile=', ';logfile='),
            template.replace('[dosbox]', '[dosbox]\ncaptures=wrong'),
            template.replace('mount d ', 'mount c '),
            template.replace('mount d ', ';mount d '), template+'echo unexpected\n',
            template.replace('pt SYN1.PCB', 'pt OTHER.PCB > OUT.TXT'),
            template.replace('[cpu]', '[unknown]\nx=y\n[cpu]')]
        for i, text in enumerate(variants):
            with self.subTest(i=i):
                (self.physical/'slot-retry-01/SYN1.conf').write_text(text, encoding='utf-8')
                destination = self.root/('rejected-'+str(i))
                with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
                    click.prepare(destination=str(destination), **self.args)
                self.assertFalse(destination.exists())

    def test_actual_old_log_capture_and_mount_paths_all_rejected(self):
        package, plan = self.generated()
        path = package/'slot/SYN1.conf'; text = path.read_text(encoding='utf-8')
        pairs = [(str(package/'slot/dosbox-startup.log'), str(self.logical_slot/'dosbox-startup.log')),
                 (str(package/'slot/captures'), str(self.logical_slot/'captures')),
                 ('mount c "'+str(package/'slot/runtime')+'"', 'mount c "'+str(self.logical_slot/'runtime')+'"'),
                 ('mount d "'+str(package/'slot/runtime')+'"', 'mount d "'+str(self.logical_slot/'runtime')+'"')]
        for a, b in pairs:
            with self.subTest(path=a):
                path.write_text(text.replace(a, b), encoding='utf-8')
                with self.assertRaises(ValueError): isolation.validate_runtime_plan(plan, check_bytes=False)
        path.write_text(text, encoding='utf-8')
        isolation.validate_runtime_plan(plan)

    def test_all_execution_path_mutations_rejected_even_with_unchanged_config(self):
        package, plan = self.generated()
        mutations = [lambda p: p.update(slot=str(self.logical_slot)),
            lambda p: p['launch_argv'].__setitem__(3, str(self.logical_slot)),
            lambda p: p['launch_argv'].append('unexpected'),
            lambda p: p.update(driver=str(self.root/'other.py')),
            lambda p: p['target'].update(cwd=str(self.logical_slot/'runtime/pt')),
            lambda p: p['target'].update(input=str(self.root/'other.PCB')),
            lambda p: p['target'].update(output=str(self.root/'outside.PCB')),
            lambda p: p['target']['argv'].extend(['-conf', 'unexpected.conf']),
            lambda p: p['control_argv'].__setitem__(4, 'raise SystemExit(0)'),
            lambda p: p['control_argv'].append('--config=outside')]
        for i, mutate in enumerate(mutations):
            with self.subTest(i=i):
                value = copy.deepcopy(plan); mutate(value)
                with self.assertRaises((ValueError, FileNotFoundError)): isolation.validate_runtime_plan(value, runtime_root=package/'slot', check_bytes=False)
        with self.assertRaises(ValueError): isolation.validate_runtime_plan(plan, runtime_root=self.alias/'slot')
        with self.assertRaises(ValueError): isolation.validate_runtime_plan(plan, driver_path=self.root/'not-driver.py')

    def test_directory_junction_and_hardlink_write_escapes(self):
        package, plan = self.generated()
        slot = package/'slot'
        outside = self.root/'outside'; outside.mkdir()
        for name in ('captures', 'runtime'):
            original = slot/name; backup = slot/(name+'-saved'); original.rename(backup)
            junction(original, outside)
            try:
                with self.assertRaises(ValueError): isolation.validate_runtime_plan(plan)
            finally:
                remove_alias(original); backup.rename(original)
        for relative in ('dosbox-startup.log', 'owner-created.json', 'captures/new.png', 'runtime/pt/DATA2.BIN', 'inbox/request.json'):
            outside_file = outside/'shared'; outside_file.write_bytes(b'original outside bytes')
            linked = slot/relative; linked.parent.mkdir(parents=True, exist_ok=True); os.link(outside_file, linked)
            try:
                with self.subTest(relative=relative), self.assertRaises(ValueError): isolation.validate_runtime_plan(plan)
                self.assertEqual(outside_file.read_bytes(), b'original outside bytes')
            finally: linked.unlink()
        alias_slot = self.root/'aliased-slot'; junction(alias_slot, slot)
        try:
            bad = copy.deepcopy(plan); bad['slot'] = str(alias_slot)
            with self.assertRaises(ValueError): isolation.validate_runtime_plan(bad)
        finally: remove_alias(alias_slot)
    def test_file_symbolic_link_write_escape(self):
        package, plan = self.generated()
        slot = package/'slot'
        outside = self.root/'symbolic-outside'; outside.write_bytes(b'outside original')
        # 权限不足只跳过这一独立例，不掩盖联接/硬链接的实际结果。
        sym = slot/'symlink.log'
        try: sym.symlink_to(outside)
        except OSError as error:
            self.skipTest('实际文件符号链接权限不可用：' + str(error))
        else:
            try:
                with self.assertRaises(ValueError): isolation.validate_runtime_plan(plan)
            finally: sym.unlink()

    def test_service_environment_and_stream_targets_remain_in_slot(self):
        package, plan = self.generated()
        result = isolation.service_environment(package/'slot', {'PATH':'preserved','APPDATA':'outside'})
        self.assertEqual(result['PATH'],'preserved')
        for key in ('USERPROFILE','APPDATA','LOCALAPPDATA','TEMP','TMP','XDG_CONFIG_HOME','UV_CACHE_DIR'):
            self.assertTrue(Path(result[key]).is_relative_to(package/'slot/service-profile'))
        isolation.validate_runtime_plan(plan)

    def test_actual_launch_rechecks_after_preflight_before_target_creation(self):
        package, plan = self.generated(); scope, tree = self.driver_definitions(package)
        branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="tool == 'Launch'")
        calls=[]
        def after_preflight_digest(path):
            # 真正preflight已通过，后续目标EXE摘要查询期间模拟计划路径变化。
            if str(path)==plan['target']['argv'][0]: plan['target']['output']=str(self.root/'outside.PCB')
            return digest(path)
        scope.update(plan=plan,baseline=True,target=None,launched=False,name='changed-after-preflight',sha=after_preflight_digest,
            rpc=types.SimpleNamespace(gate=lambda name:None,remaining=lambda:100),
            subprocess=types.SimpleNamespace(Popen=lambda *a,**k:calls.append('target')),save=lambda *a:None)
        with self.assertRaises(ValueError):exec(compile(ast.Module(body=branch.body,type_ignores=[]),'<真实Launch二次门>', 'exec'),scope)
        self.assertEqual(calls,[])

    def test_destination_alias_and_existing_hardlinked_file_rejected_before_write(self):
        real=self.root/'destination-real';real.mkdir();alias=self.root/'destination-alias';junction(alias,real)
        try:
            with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):click.prepare(destination=str(alias/'new'), **self.args)
            self.assertEqual(list(real.iterdir()),[])
        finally:remove_alias(alias)
        package,plan=self.generated(); original=(package/'desktop_session.py').read_bytes()
        outside=self.root/'driver-original';shutil.copyfile(package/'desktop_session.py',outside)
        (package/'desktop_session.py').unlink();os.link(outside,package/'desktop_session.py')
        with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):click.prepare(destination=str(package),refresh=True,**self.args)
        self.assertEqual(outside.read_bytes(),original)

    def test_powershell_actual_file_invalid_semantics_zero_owner_or_driver(self):
        if os.name != 'nt': self.skipTest('需要既有 Windows PowerShell')
        package,plan=self.generated();slot=package/'slot'
        now=datetime.datetime.now(datetime.timezone.utc)
        plan['target']['cwd']=str(self.root/'outside');dump(slot/'live-plan.json',plan)
        dump(slot/'go-start.json',{**{k:plan[k] for k in ('task','dispatch','session')},
            'approved_plan_sha256':digest(slot/'live-plan.json'),'start_utc':(now-datetime.timedelta(seconds=1)).isoformat(),
            'deadline_utc':(now+datetime.timedelta(minutes=20)).isoformat()})
        initial=set(slot.iterdir())
        for detach in (False,True):
            argv=['powershell.exe','-NoProfile','-File',str(REPO/'tools/Start-LegacyObservationOwner.ps1'),'-Slot',str(slot)]
            if detach:argv.append('-Detach')
            result=subprocess.run(argv,capture_output=True,timeout=15)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(initial,set(slot.iterdir()))

    def test_probe_and_extra_output_commands_rejected_at_final_state_gate(self):
        package,plan=self.generated(state.prepare_state);path=package/'slot/SYN1.conf'
        original=path.read_text(encoding='utf-8')
        for text in (original.replace('> C:\\OUTPUT.TXT','> D:\\OUTPUT.TXT'),
                     original.replace('pt SYN1.PCB','pt SYN1.PCB > C:\\UNREVIEWED.TXT'),
                     original.replace('[mixer]','[extra]\npath=outside\n[mixer]')):
            with self.subTest(text=text[-80:]):
                path.write_text(text,encoding='utf-8')
                with self.assertRaises(ValueError):isolation.validate_runtime_plan(plan,check_bytes=False)
        path.write_text(original,encoding='utf-8');isolation.validate_runtime_plan(plan)

    def test_owner_actual_main_invalid_plan_zero_driver_and_no_output_files(self):
        package, plan = self.generated()
        slot = package/'slot'; plan['target']['cwd'] = str(self.logical_slot/'runtime/pt'); dump(slot/'live-plan.json', plan)
        before = sorted(x.name for x in slot.iterdir())
        with patch.object(sys, 'argv', ['owner', str(slot)]), patch.object(owner.subprocess, 'Popen') as spawn:
            with self.assertRaises(ValueError): owner.main()
            spawn.assert_not_called()
        self.assertEqual(before, sorted(x.name for x in slot.iterdir()))

    def test_actual_driver_prefix_invalid_plan_zero_native_import_or_dll(self):
        package, plan = self.generated()
        slot = package/'slot'; plan['target']['output'] = str(self.root/'outside.PCB'); dump(slot/'live-plan.json', plan)
        # 执行直到原native import之前的实际顶层代码（含隔离验证）。
        text = (package/'desktop_session.py').read_text(encoding='utf-8')
        prefix = text[:text.index('from inspect_legacy_desktop import inspect_desktop')]
        with patch.object(sys, 'argv', ['driver', str(slot)]):
            with self.assertRaises(ValueError): exec(compile(prefix, '<实际driver顶层前缀>', 'exec'), {'__file__': str(package/'desktop_session.py')})

    def test_owner_legal_plan_fake_original_popen_wait_zero(self):
        package, plan = self.generated()
        slot = package/'slot'
        now = datetime.datetime.now(datetime.timezone.utc)
        dump(slot/'go-start.json', {**{k:plan[k] for k in ('task','dispatch','session')},
            'approved_plan_sha256':digest(slot/'live-plan.json'), 'start_utc':(now-datetime.timedelta(seconds=1)).isoformat(),
            'deadline_utc':(now+datetime.timedelta(minutes=20)).isoformat()})
        fake = types.SimpleNamespace(wait=lambda: 0)
        with patch.object(sys, 'argv', ['owner', str(slot)]), patch.object(owner.subprocess, 'CREATE_NO_WINDOW', 0, create=True), \
             patch.object(owner.subprocess, 'Popen', return_value=fake) as spawn, patch.object(owner, 'identity', return_value={'pid':-1,'original_handle':-2}):
            self.assertEqual(owner.main(), 0)
            spawn.assert_called_once()
        self.assertEqual(json.loads((slot/'driver-exit.json').read_text(encoding='utf-8'))['wait_return'], 0)

    def driver_definitions(self, package):
        tree = ast.parse((package/'desktop_session.py').read_text(encoding='utf-8'))
        scope = dict(Path=Path, json=json, hashlib=hashlib, ROOT=package/'slot', __file__=str(package/'desktop_session.py'),
                     validate_runtime_plan=isolation.validate_runtime_plan, datetime=datetime, time=types.SimpleNamespace(time=lambda:0))
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))], type_ignores=[]), '<当前driver纯定义>', 'exec'), scope)
        return scope, tree

    def test_actual_driver_main_invalid_plan_zero_rpc_start_or_baseline(self):
        package, plan = self.generated()
        scope, tree = self.driver_definitions(package)
        plan['target']['cwd'] = str(self.root/'outside'); dump(package/'slot/live-plan.json', plan)
        calls=[]
        scope.update(dpi_init_result=False, os=os, sys=sys, save=lambda *a:None, stamp=lambda:'synthetic', Rpc=lambda:calls.append('Rpc'))
        with self.assertRaises(ValueError): scope['main']()
        self.assertEqual(calls, [])

    def test_service_popen_exception_closes_both_open_streams(self):
        package,plan=self.generated();scope,tree=self.driver_definitions(package)
        rpc=types.SimpleNamespace(p=None)
        scope.update(os=os,service_environment=isolation.service_environment,
            subprocess=types.SimpleNamespace(Popen=lambda *a,**k:(_ for _ in ()).throw(OSError('synthetic spawn failure')),PIPE=-1,CREATE_NO_WINDOW=0))
        with self.assertRaises(OSError):scope['Rpc'].start(rpc,plan)
        self.assertTrue(rpc.raw.closed);self.assertTrue(rpc.err.closed)
        for name in ('control-stderr.bin','control-stdout.jsonl'):
            path=package/'slot'/name;path.unlink();self.assertFalse(path.exists())

    def test_target_popen_exception_closes_both_parent_streams(self):
        package,plan=self.generated();scope,tree=self.driver_definitions(package)
        branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="tool == 'Launch'")
        scope.update(plan=plan,baseline=True,target=None,launched=False,name='spawn-error',os=os,service_environment=isolation.service_environment,
            rpc=types.SimpleNamespace(gate=lambda name:None,remaining=lambda:100),
            subprocess=types.SimpleNamespace(Popen=lambda *a,**k:(_ for _ in ()).throw(OSError('synthetic spawn failure'))),save=lambda *a:None)
        with self.assertRaises(OSError):exec(compile(ast.Module(body=branch.body,type_ignores=[]),'<真实Launch创建失败>', 'exec'),scope)
        self.assertTrue(scope['out'].closed);self.assertTrue(scope['err'].closed)
        for suffix in ('stdout','stderr'):(package/'slot'/('spawn-error.'+suffix+'.bin')).unlink()

    def test_valid_target_launch_and_service_start_only_use_fake_popen(self):
        package,plan=self.generated();scope,tree=self.driver_definitions(package)
        calls=[]; fake_process=types.SimpleNamespace(pid=-1)
        def spawn(argv,**kwargs):calls.append(list(argv));return fake_process
        class NoThread:
            def __init__(self,*a,**k):pass
            def start(self):pass
        scope.update(os=os,service_environment=isolation.service_environment,
            process_identity=lambda p:{'actual_image':plan['target']['argv'][0]},save=lambda *a:None,stamp=lambda:'synthetic',
            threading=types.SimpleNamespace(Thread=NoThread),
            subprocess=types.SimpleNamespace(Popen=spawn,PIPE=-1,CREATE_NO_WINDOW=0))
        rpc=types.SimpleNamespace(p=None,reader=lambda:None,call=lambda *a:None,write=lambda *a:None)
        try:scope['Rpc'].start(rpc,plan)
        finally:
            if getattr(rpc,'raw',None):rpc.raw.close()
            if getattr(rpc,'err',None):rpc.err.close()
        self.assertEqual(calls,[plan['control_argv']])
        # 执行真实Launch至Popen及其身份取得即停止，避免任何后图/原生枚举。
        branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="tool == 'Launch'")
        class StopAfterIdentity(Exception):pass
        scope.update(plan=plan,baseline=True,target=None,launched=False,name='positive-target',os=os,service_environment=isolation.service_environment,
            rpc=types.SimpleNamespace(gate=lambda name:None,remaining=lambda:100),
            process_identity=lambda p:(_ for _ in ()).throw(StopAfterIdentity()))
        with self.assertRaises(StopAfterIdentity):exec(compile(ast.Module(body=branch.body,type_ignores=[]),'<真实Launch正向假创建>', 'exec'),scope)
        self.assertEqual(calls,[plan['control_argv'],plan['target']['argv']])
        self.assertTrue(scope['out'].closed);self.assertTrue(scope['err'].closed)

    def test_actual_rpc_start_invalid_plan_before_stream_open_and_popen(self):
        package, plan = self.generated(); scope, tree = self.driver_definitions(package)
        # 不构造Rpc（避免queue依赖），直接调用真实start未绑定方法。
        plan['target']['input'] = str(self.root/'other.PCB')
        before=set((package/'slot').iterdir()); calls=[]
        scope['subprocess']=types.SimpleNamespace(Popen=lambda *a,**k:calls.append('service'))
        with self.assertRaises(ValueError): scope['Rpc'].start(types.SimpleNamespace(), plan)
        self.assertEqual(calls, []); self.assertEqual(before,set((package/'slot').iterdir()))

    def test_target_actual_launch_branch_revalidates_before_target_popen(self):
        package, plan = self.generated(); scope, tree = self.driver_definitions(package)
        # 执行真实Launch分支；该分支先gate后原preflight，隔离错误不能越过到Popen/截图。
        branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="tool == 'Launch'")
        plan['target']['output']=str(self.root/'outside.PCB')
        calls=[]
        scope.update(plan=plan, baseline=True, target=None, launched=False, name='synthetic-launch',
            rpc=types.SimpleNamespace(gate=lambda name:None, remaining=lambda:100),
            subprocess=types.SimpleNamespace(Popen=lambda *a,**k:calls.append('target')), save=lambda *a:None)
        with self.assertRaises(ValueError): exec(compile(ast.Module(body=branch.body,type_ignores=[]),'<真实Launch分支>', 'exec'),scope)
        self.assertEqual(calls,[])


if __name__ == '__main__': unittest.main(verbosity=2)
