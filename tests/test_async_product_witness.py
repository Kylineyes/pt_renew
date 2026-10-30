"""跨创建者见证交换变异测试；只保存假原Popen，JSON不是独立来源证明。"""
import json
from dataclasses import asdict
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from async_product_client.core import Context,Ledger,digest
from async_product_client.lifecycle import ProcessRegistry
from async_product_client.witness import CreatorRelay,RootWitness,audit_relay,pack


class Process:
    def __init__(self,pid):self.pid,self.returncode=pid,None
    def poll(self):return self.returncode


def identity(pid):return dict(pid=pid,birth=pid*100,handle=pid+1000,image='C:/frozen/python.exe',original_handle=True)


class WitnessTests(unittest.TestCase):
    def fixture(self):
        context=Context('task','dispatch','client-run','session')
        ledgers={role:Ledger(context=context,cleanup_deadline_ns=10**30) for role in ('supervisor','client','service')}
        regs={role:ProcessRegistry(ledgers[role],required_roles=roles) for role,roles in
              [('supervisor',('client',)),('client',('product','service')),('service',())]}
        p={role:Process(pid) for role,pid in [('supervisor',10),('client',20),('service',30),('product',40)]}
        for parent,role in [('supervisor','client'),('client','service'),('client','product')]:
            regs[parent].created(role,p[role],role=role)
            regs[parent].identified(role,p[role],identity(p[role].pid))
        relays={role:CreatorRelay(ledgers[role],regs[role],self_identity=identity(p[role].pid),role=role)
                for role in ledgers}
        root=RootWitness(context=context,process=p['supervisor'],identity=identity(10))
        return context,ledgers,regs,p,relays,root

    def chain(self):
        context,ledgers,regs,p,relays,root=self.fixture()
        service=relays['service'].seal();p['service'].returncode=0
        relays['client'].accept_child('service',service)
        p['product'].returncode=0
        client=relays['client'].seal();p['client'].returncode=0
        relays['supervisor'].accept_child('client',client)
        top=relays['supervisor'].seal();p['supervisor'].returncode=0
        return context,ledgers,regs,p,relays,root,top

    def test_three_creators_and_leaf_original_popen_exchange_complete_only_lifecycle(self):
        context,ledgers,regs,p,relays,root,raw=self.chain()
        result=root.finish(raw)
        self.assertEqual(set(result['roles']),{'supervisor','client','service','product'})
        self.assertTrue(result['lifecycle_complete'])
        self.assertEqual(result['original_root_popen_exit'],0)
        self.assertFalse(result['ready_for_live'])
        self.assertFalse(result['gui_verified'])
        self.assertFalse(result['unknown_short_lived_descendants_covered'])
        self.assertIs(regs['client'].entries['product']['process'],p['product'])
        with self.assertRaises(ValueError):root.finish(raw)

    def test_child_report_while_alive_or_missing_parent_original_identity_is_rejected(self):
        context,ledgers,regs,p,relays,root=self.fixture()
        raw=relays['service'].seal()
        with self.assertRaises(ValueError):relays['client'].accept_child('service',raw)
        p['service'].returncode=0
        regs['client'].entries['service']['identity']=None
        with self.assertRaises(ValueError):relays['client'].accept_child('service',raw)
        self.assertEqual(relays['client'].children,{})

    def test_context_identity_digest_role_missing_child_and_duplicate_process_mutations_reject(self):
        context,ledgers,regs,p,relays,root,raw=self.chain()
        for mode in ('context','identity','digest','role','child','duplicate','nonzero','gap','missing-role','parent-cycle'):
            row=json.loads(raw)
            if mode=='context':row['context']['task_id']='old'
            if mode=='identity':row['self']['birth']+=1
            if mode=='digest':row['children']['client']['sha256']='0'*64
            if mode=='role':row['role']='client'
            if mode=='child':row['children']={}
            if mode=='duplicate':
                row['local']['entries']['other']=dict(row['local']['entries']['client'],role='product')
            if mode=='nonzero':row['local']['entries']['client']['exit_code']=1
            if mode=='gap':row['local']['discovered_gaps']={'child':{'pid':99}}
            if mode=='missing-role':row['local']['missing_roles']=['client']
            if mode=='parent-cycle':row['local']['entries']['client']['parent']='client'
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                audit_relay(pack(row),context=asdict(context),expected_identity=identity(10),expected_role='supervisor')

    def test_action_failure_later_zero_and_missing_required_global_roles_do_not_pass_root(self):
        context,ledgers,regs,p,relays,root=self.fixture()
        ledgers['service'].failed='input-failure';ledgers['service'].token='old';ledgers['service'].not_before_ns=777
        raw=relays['service'].seal();p['service'].returncode=0
        with self.assertRaises(ValueError):relays['client'].accept_child('service',raw)
        self.assertEqual((ledgers['service'].failed,ledgers['service'].token,ledgers['service'].not_before_ns),
                         ('input-failure','old',777))
        registry=ProcessRegistry(ledgers['supervisor'],required_roles=())
        leaf=CreatorRelay(ledgers['supervisor'],registry,self_identity=identity(10),role='supervisor').seal()
        p['supervisor'].returncode=0
        with self.assertRaises(ValueError):root.finish(leaf)

    def test_nonzero_or_changed_root_object_identity_prevents_use_of_valid_report(self):
        for mode in ('nonzero','pid','alive'):
            context,ledgers,regs,p,relays,root,raw=self.chain()
            if mode=='nonzero':p['supervisor'].returncode=1
            if mode=='pid':p['supervisor'].pid=100
            if mode=='alive':p['supervisor'].returncode=None
            with self.subTest(mode=mode),self.assertRaises(ValueError):root.finish(raw)
            self.assertTrue(root.used)


if __name__=='__main__':unittest.main(verbosity=2)
