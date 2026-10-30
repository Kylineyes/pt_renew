"""UIA对象一次性入口契约；全用假进程/COM，不运行真实UIA。"""
from dataclasses import asdict
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools')); sys.path.insert(0,str(ROOT/'tests'))
from async_product_client.core import Context, Ledger, SECOND, digest
from async_product_client.product import tree_hashes
from async_product_client.probe_environment import GENERATED
from async_product_client.uia_object import UiaObjectOwner, validate_uia_object_apartment
from test_async_product_client import Clock
from run_async_uia_object import authorize
import probe_async_uia_object


def receipt():
    names = ('CoInitializeEx', 'CoInitializeEx', 'CoInitialize', 'CoUninitialize', 'CoUninitialize', 'CoUninitialize')
    balance = 0; calls=[]
    for name in names:
        balance += -1 if name=='CoUninitialize' else 1
        calls.append(dict(api=name,thread=123,returned=True,result=None if name=='CoUninitialize' else 0,balance=balance))
    return dict(thread=123,balance=0,balanced=True,calls=calls)


class ObjectTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.clock=Clock()
        self.context=Context('task-new','dispatch-new','run-new','session-new')
        self.ledger=Ledger(context=self.context,clock=self.clock,enabled=True,cleanup_deadline_ns=910*SECOND)
        self.modules=self.root/'modules';self.modules.mkdir()
        (self.modules/'probe_async_uia_object.py').write_text('# 假入口\n',encoding='utf-8')
        self.interpreter=self.root/'python.exe';self.interpreter.write_bytes(b'base-interpreter')
        self.package=self.root/'package';(self.package/'windows_mcp').mkdir(parents=True)
        for n in range(77):(self.package/'windows_mcp'/f'module{n}.py').write_bytes(str(n).encode())
        self.dependencies=self.root/'dependencies'
        for name in GENERATED|{'comtypes/__init__.py'}:
            path=self.dependencies/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'# fake')
        self.materials=dict(interpreter=str(self.interpreter),interpreter_sha256=digest(self.interpreter.read_bytes()),
            module_root=str(self.modules),module_files=tree_hashes(self.modules),package_root=str(self.package),
            package_files=tree_hashes(self.package/'windows_mcp'),python_environment=dict(root=str(self.dependencies),
            files=tree_hashes(self.dependencies),version=list(sys.version_info[:3])))
        self.process=SimpleNamespace(pid=42,returncode=None);self.process.poll=lambda:self.process.returncode
        self.calls=[]
        def popen(*args,**kwargs):self.calls.append((args,kwargs));return self.process
        self.handles=SimpleNamespace(inspect=lambda p:dict(pid=42,birth=100,handle=555,image=str(self.interpreter),original_handle=True))
        self.owner=UiaObjectOwner(self.ledger,self.root/'execution',enabled=True,popen=popen,handles=self.handles)
        self.addCleanup(self.owner.close_streams)

    def complete(self,**changes):
        request=self.owner.request
        result=dict(completed=True,pid=42,context=asdict(self.context),nonce=request['nonce'],
            request_sha256=digest((self.owner.root/'request.json').read_bytes()),object_created=True,object_creations=1,
            desktop_queries=0,event_subscriptions=0,started_ns=self.clock.now,finished_ns=self.clock.now,
            com_apartment=receipt(),**changes)
        (self.owner.root/'object-result.json').write_text(json.dumps(result),encoding='utf-8')
        self.process.returncode=0

    def test_original_object_identity_three_initializers_and_original_exit_are_required(self):
        self.owner.start('start-object','start',materials=self.materials);self.complete()
        result=self.owner.finish('finish-object',self.ledger.token,materials=self.materials)
        self.assertTrue(result['object_created']);self.assertTrue(self.owner.accepted)
        self.assertIs(self.owner.process,self.process);self.assertEqual(self.owner.exit_code,0)
        self.assertEqual(self.calls[0][0][0][1:3],['-I','-S'])
        self.assertEqual(len(self.calls),1);self.assertIsNone(self.ledger.failed)

    def test_disabled_missing_source_or_slow_precheck_create_no_process(self):
        self.owner.enabled=False
        with self.assertRaises(ValueError):self.owner.start('disabled','start',materials=self.materials)
        self.assertEqual(self.calls,[])
        other=UiaObjectOwner(Ledger(context=self.context,clock=self.clock,enabled=True,cleanup_deadline_ns=910*SECOND),
                             self.root/'other',enabled=True,popen=lambda *a,**kw:self.calls.append(a))
        original=other.sources
        def slow(materials):result=original(materials);self.clock.tick(5);return result
        other.sources=slow
        with self.assertRaises(ValueError):other.start('slow','start',materials=self.materials)
        self.assertEqual(self.calls,[]);self.assertTrue(other.used);other.close_streams()

    def test_late_exit_zero_only_updates_lifecycle_and_cannot_retry(self):
        self.owner.start('start-object','start',materials=self.materials)
        self.clock.tick(5)
        with self.assertRaises(ValueError):self.owner.finish('finish-object',self.ledger.token,materials=self.materials)
        saved=self.ledger.failed,self.ledger.token,self.ledger.not_before_ns
        self.owner.stop();self.process.returncode=0;self.assertEqual(self.owner.poll(),0)
        self.assertFalse(self.owner.accepted)
        self.assertEqual(saved,(self.ledger.failed,self.ledger.token,self.ledger.not_before_ns))
        self.assertEqual(len(self.calls),1)

    def test_identity_unknown_preserves_original_object(self):
        self.handles.inspect=lambda p:(_ for _ in ()).throw(ValueError('原句柄未知'))
        with self.assertRaises(ValueError):self.owner.start('start-object','start',materials=self.materials)
        self.assertIs(self.owner.process,self.process);self.assertIsNone(self.owner.identity)
        self.process.returncode=0;self.owner.poll();self.assertFalse(self.owner.accepted)

    def test_two_or_four_balanced_initializers_cannot_substitute_three(self):
        valid=receipt();validate_uia_object_apartment(valid)
        for changed in (dict(valid,calls=valid['calls'][:2]+valid['calls'][4:]),dict(valid,calls=valid['calls']+valid['calls'])):
            with self.assertRaises(ValueError):validate_uia_object_apartment(changed)

    def test_changed_request_or_wrong_context_never_accepts_original_exit_zero(self):
        self.owner.start('start-object','start',materials=self.materials);self.complete()
        path=self.owner.root/'request.json';row=json.loads(path.read_text());row['nonce']='old';path.write_text(json.dumps(row))
        with self.assertRaises(ValueError):self.owner.finish('finish-object',self.ledger.token,materials=self.materials)
        self.assertEqual(self.owner.exit_code,0);self.assertFalse(self.owner.accepted)

    def test_authorization_binds_exact_pi_prefix_context_and_scope_before_any_creation(self):
        session=self.root/'session.jsonl';raw=json.dumps(dict(type='session',id=self.context.session_id)).encode()+b'\n';session.write_bytes(raw)
        approval=dict(context=asdict(self.context),scope='uia-object-only',permission_confirmed=True,permission='本轮持续授权',
            message_id='new-message',max_object_creations=1,max_desktop_queries=0,max_product_launches=0,max_control_services=0,
            probe_seconds=5,diagnostic_seconds=600,total_seconds=900,ready_for_live=False,evidence_root=str(self.root/'run'))
        path=self.root/'approval.json';path.write_text(json.dumps(approval),encoding='utf-8')
        config=dict(context=asdict(self.context),approval=str(path),approval_sha256=digest(path.read_bytes()),session_file=str(session),
            session_prefix_bytes=len(raw),session_prefix_sha256=digest(raw),evidence_root=approval['evidence_root'],materials=self.materials)
        env=dict(PI_PROVIDER='deng',PI_MODEL='gpt-6.1-sol',PI_REASONING_LEVEL='high',PI_SESSION_ID=self.context.session_id)
        with patch.dict(os.environ,env):self.assertEqual(authorize(config),self.context)
        env['PI_MODEL']='other'
        with patch.dict(os.environ,env),self.assertRaises(ValueError):authorize(config)
        self.assertEqual(self.calls,[])

    def test_disabled_child_request_loads_no_com_or_uia(self):
        folder=self.root/'child';folder.mkdir();path=folder/'request.json'
        path.write_text(json.dumps(dict(context=asdict(self.context),nonce='new',purpose='uia-object-only',enabled=False,
                                          max_object_creations=1,max_desktop_queries=0,deadline_ns=self.clock.now+SECOND)),encoding='utf-8')
        loaded=[]
        self.assertEqual(probe_async_uia_object.execute(path,load=lambda p:loaded.append(p),clock=self.clock.monotonic_ns),1)
        self.assertEqual(loaded,[])
        self.assertFalse(json.loads((folder/'object-result.json').read_text(encoding='utf-8'))['completed'])


if __name__=='__main__':unittest.main()
