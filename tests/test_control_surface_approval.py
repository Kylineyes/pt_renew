"""只读批准、独立新身份与日志前置条件测试，不导入桌面或MCP。"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from control_surface_approval import CLIENT_FILES,TOOL_FILES,require_client_approval,surface_initial_ready


class SurfaceApprovalTests(unittest.TestCase):
    @contextmanager
    def candidate(self):
        with tempfile.TemporaryDirectory(prefix='pt-candidate-') as directory:
            base=Path(directory);root=base/'client';tools=base/'tools';package=base/'isolated'
            root.mkdir();tools.mkdir();(package/'windows_mcp').mkdir(parents=True)
            for name in CLIENT_FILES:(root/name).write_text('客户端冻结文件',encoding='utf-8')
            for name in TOOL_FILES:(tools/name).write_text('工具冻结文件',encoding='utf-8')
            (root/'window.py').write_bytes((tools/'control_test_window.py').read_bytes())
            manifest=package/'package-manifest.json'
            manifest.write_text(json.dumps(dict(files={})),encoding='utf-8')
            approval=dict(mode='diagnostics-only',task_id='task_111111111111',dispatch_id='ctx_222222222222',
                message_id='msg_新批准',permission_confirmed=True,permission='本轮明确许可的记录',
                evidence_root=str(root),tools_root=str(tools),package_root=str(package),
                provider='测试提供方',session_id='新的独立会话',max_connections=1,max_groups=1,max_windows=1,
                max_snapshots=4,diagnostic_seconds=600,total_seconds=900,
                indicator_bitmap_surface=True,indicator_health_sampling=True,indicator_health_fix=True,
                app_refresh_fix=True,initial_target_activation=True,indicator_bitmap_timing=False,
                reviewed_files_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in CLIENT_FILES})
            hashes={name:hashlib.sha256((tools/name).read_bytes()).hexdigest() for name in TOOL_FILES}
            approval.update(geometry_sha256=hashes['control_geometry.py'],target_activation_sha256=hashes['control_target_activation.py'])
            server={**approval,'launcher_files':hashes,'package_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}
            env=dict(PI_PROVIDER='测试提供方',PI_MODEL='gpt-6.1-sol',PI_REASONING_LEVEL='high',PI_SESSION_ID='新的独立会话')
            yield root,tools,package,approval,server,env

    def check(self,root,tools,package,approval,server,env):
        for name,value in (('phase-two-approval.json',approval),('server-approval.json',server)):
            (root/name).write_text(json.dumps(value),encoding='utf-8')
        return require_client_approval(root,tools,package,environ=env)

    def test_new_approval_requires_actual_model_permissions_and_unused_run_directory(self):
        with self.candidate() as args:
            root,tools,package,approval,server,env=args
            with self.assertRaises(FileNotFoundError):require_client_approval(root,tools,package,environ=env)
            self.assertEqual(self.check(*args),approval)
            for field,value in (('permission_confirmed',False),('task_id','task_47e20595fdcb'),
                                ('session_id','01a1739a-82f6-76cf-9ffc-c63e95be56d4'),
                                ('total_seconds',1800),('max_groups',True)):
                bad=deepcopy(approval);bad[field]=value
                with self.subTest(field=field),self.assertRaises(RuntimeError):
                    self.check(root,tools,package,bad,server,env)
            wrong=dict(env,PI_MODEL='其他模型')
            with self.assertRaises(RuntimeError):self.check(root,tools,package,approval,server,wrong)
            for name in ('live-state.json','runtime-limits.json','client-fatal.json'):
                (root/name).write_text('{}',encoding='utf-8')
                with self.subTest(name=name),self.assertRaisesRegex(RuntimeError,'禁止重连'):
                    self.check(*args)
                (root/name).unlink()

    def test_client_and_service_flags_hashes_and_directory_escape_cannot_diverge(self):
        with self.candidate() as args:
            root,tools,package,approval,server,env=args
            for field,value in (('indicator_bitmap_surface',False),('indicator_bitmap_timing',True),
                                ('message_id','其他消息')):
                bad=deepcopy(server);bad[field]=value
                with self.subTest(field=field),self.assertRaises(RuntimeError):
                    self.check(root,tools,package,approval,bad,env)
            bad=deepcopy(approval);bad['reviewed_files_sha256']['../outside']='0'*64
            with self.assertRaisesRegex(RuntimeError,'批准目录'):self.check(root,tools,package,bad,server,env)
            (tools/'control_bitmap_surface_model.py').write_text('变化',encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'审阅后变化'):self.check(*args)

    def test_package_file_set_change_is_refused_before_any_native_import(self):
        with self.candidate() as args:
            root,tools,package,approval,server,env=args
            (package/'windows_mcp/新增.py').write_text('变化',encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'隔离包文件集合'):self.check(*args)

    def test_close_requires_explicit_matching_flags_and_frozen_module(self):
        with self.candidate() as args:
            root,tools,package,approval,server,env=args
            self.check(*args)
            with self.assertRaisesRegex(RuntimeError,'显式批准'):
                require_client_approval(root,tools,package,environ=env,require_owned_close=True)
            module='control_owned_close.py'
            (tools/module).write_text('专用关闭模块',encoding='utf-8')
            sha=hashlib.sha256((tools/module).read_bytes()).hexdigest()
            approval.update(owned_diagnostic_close=True,owned_close_sha256=sha)
            server.update(owned_diagnostic_close=True,owned_close_sha256=sha)
            server['launcher_files'][module]=sha
            self.assertEqual(self.check(*args),approval)
            self.assertEqual(require_client_approval(root,tools,package,environ=env,require_owned_close=True),approval)
            for field,value in [('owned_diagnostic_close',False),('owned_close_sha256','0'*64)]:
                bad=deepcopy(server);bad[field]=value
                with self.assertRaises(RuntimeError):self.check(root,tools,package,approval,bad,env)
            bad=deepcopy(server);del bad['launcher_files'][module]
            with self.assertRaises(RuntimeError):self.check(root,tools,package,approval,bad,env)
            (tools/module).write_text('发生变化',encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'审阅后变化'):self.check(*args)

    def test_passive_readiness_requires_one_install_and_no_resource_failure(self):
        installed=dict(event='indicator-surface-installed',max_surfaces=64,max_bitmap_bytes=64*1024*1024)
        self.assertFalse(surface_initial_ready([])['ready'])
        self.assertTrue(surface_initial_ready([installed])['ready'])
        for rows in ([installed,installed],[dict(installed,max_surfaces=65)],
                     [installed,dict(event='indicator-surface-operation',exception='OSError')],
                     [installed,dict(event='indicator-surface-owner-exit',resources=dict(failed=True))]):
            with self.subTest(rows=rows):
                result=surface_initial_ready(rows)
                self.assertFalse(result['ready']);self.assertTrue(result['fatal'])


if __name__=='__main__':unittest.main(verbosity=2)
