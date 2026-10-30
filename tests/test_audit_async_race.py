"""异步离线证据的实质变异测试；假事件/时钟，不启动Qt、门闩或桌面。"""
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_async_race import audit_events,image_review_intervals,timing_readiness

A='a'*64;B='b'*64;BOARD='c'*64


def events(kind='net',mode='control'):
    source=[dict(event='run-started',kind='',request_id='',kind_configured=kind,skip=1 if kind=='net' else 0,watchdog_ms=60000),
        dict(event='request-created',kind='net',request_id='1',gated=False,revision='2'),
        dict(event='worker-entered',kind='net',request_id='1'),
        dict(event='worker-returned',kind='net',request_id='1',success=True,result_sha256=A),
        dict(event='callback-accepted',kind='net',request_id='1',experiment_aborted=False,accepted=True),
        dict(event='request-created',kind=kind,request_id='2',gated=True,generation='4',revision='2',previous_net_sha256=A,board_sha256=BOARD,net_sha256=A),
        dict(event='worker-entered',kind=kind,request_id='2',thread_id='22',stage='net-file-open-before-read' if kind=='net' else 'copper-entry-before-budget'),
        dict(event='gate-ready',kind=kind,request_id='2',thread_id='22')]
    if mode=='race':source.append(dict(event='document-published',kind='',request_id='',revision='3',dirty=True,tracks='0',net_sha256=A))
    source.extend([dict(event='gate-released',kind=kind,request_id='2',thread_id='22'),
        dict(event='worker-returned',kind=kind,request_id='2',thread_id='22',success=True,result_sha256=B,net_sha256=A,limit_reached=False,revision='2'),
        dict(event='callback-accepted' if mode=='control' else 'callback-discarded',kind=kind,request_id='2',accepted=mode=='control',experiment_aborted=False,
             captured_generation='4',current_generation='4' if mode=='control' else '5',revision='2' if mode=='control' else '3',
             generation_matches=mode=='control',board_matches=mode=='control',net_matches=True,captured_revision='2',current_revision='2' if mode=='control' else '3'),
        dict(event='run-stopped',kind='',request_id='')])
    for n,row in enumerate(source,1):
        row.update(run_id='run-uuid',pid='42',sequence=str(n),monotonic_ns=str(n*100000000),wall_ms=str(n*100),thread_id=row.get('thread_id','11'))
    return source


class EventTests(unittest.TestCase):
    def audit(self,rows,kind='net',mode='control'):
        return audit_events(rows,kind=kind,mode=mode,a_sha256=A,b_sha256=B,board_sha256=BOARD)

    def test_both_controls_and_races_event_chain_pass_never_grants_gui(self):
        for kind in ('net','copper'):
            for mode in ('control','race'):
                result=self.audit(events(kind,mode),kind,mode)
                self.assertTrue(result['event_chain_verified'])
                self.assertFalse(result['gui_verified'])
                self.assertEqual(result['status'],mode+'_events_pass')

    def test_cancel_discard_stays_aborted_and_cannot_acquire_release(self):
        rows=events('net','race')
        release=next(x for x in rows if x['event']=='gate-released');release['event']='aborted'
        next(x for x in rows if x['event']=='callback-discarded')['experiment_aborted']=True
        result=self.audit(rows,mode='race')
        self.assertFalse(result['event_chain_verified']);self.assertEqual(result['status'],'aborted')
        release['event']='gate-released'
        with self.assertRaisesRegex(ValueError,'矛盾'):self.audit(rows,mode='race')

    def test_mixed_run_pid_sequence_or_clock_rejected(self):
        for field,value in [('pid','43'),('run_id','other'),('sequence','99'),('monotonic_ns','0'),('monotonic_ns',1.5),('monotonic_ns',True)]:
            rows=events();rows[6][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.audit(rows)
        rows=events();rows.pop()
        with self.assertRaises(ValueError):self.audit(rows)

    def test_missing_or_duplicate_gate_release_and_wrong_thread_or_stage_rejected(self):
        changes=[('gate-ready','event','ignored'),('gate-released','event','gate-ready'),
                 ('worker-entered','thread_id','11'),('worker-entered','stage','before-file-open')]
        for event,field,value in changes:
            rows=events();next(x for x in rows if x['event']==event and x['request_id']=='2')[field]=value
            with self.subTest(event=event),self.assertRaises(ValueError):self.audit(rows)
        rows=events();rows[0]['watchdog_ms']=60001
        with self.assertRaises(ValueError):self.audit(rows)
        rows=events();rows[0]['watchdog_ms']=10
        with self.assertRaisesRegex(ValueError,'看门狗'):self.audit(rows)

    def test_input_success_generation_and_revision_cannot_be_fabricated(self):
        cases=[('net','worker-returned','result_sha256',A),('net','request-created','previous_net_sha256',B),
               ('copper','worker-returned','limit_reached',True),('copper','request-created','board_sha256',B),
               ('copper','callback-accepted','board_matches',False),('net','callback-accepted','current_generation',None)]
        for kind,event,field,value in cases:
            rows=events(kind);next(x for x in rows if x['event']==event and x['request_id']=='2')[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.audit(rows,kind)

    def test_callback_cannot_belong_to_other_request_or_rename_acceptance(self):
        for field,value in [('captured_generation','99'),('accepted',False)]:
            rows=events();next(x for x in rows if x['event']=='callback-accepted' and x['request_id']=='2')[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.audit(rows)
        rows=events();rows[4]['accepted']=False
        with self.assertRaisesRegex(ValueError,'A未有效接受'):self.audit(rows)
        rows=events();rows[1]['request_id']='2'
        with self.assertRaises(ValueError):self.audit(rows)

    def test_edit_dirty_tracks_net_and_actual_original_discard_are_required(self):
        for field,value in [('dirty',False),('tracks','1'),('net_sha256',B),('revision','2')]:
            rows=events('net','race');next(x for x in rows if x['event']=='document-published')[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.audit(rows,mode='race')
        rows=events('copper','race');next(x for x in rows if x['event']=='callback-discarded')['net_matches']=False
        with self.assertRaises(ValueError):self.audit(rows,'copper','race')
        rows=events('net','race');next(x for x in rows if x['event']=='callback-discarded')['accepted']=True
        with self.assertRaises(ValueError):self.audit(rows,mode='race')


class ReviewTimingTests(unittest.TestCase):
    def data(self):
        stamp=lambda n:datetime.fromtimestamp(n,timezone.utc).isoformat()
        calls=[dict(event='call_tool-start',call='0001-Snapshot',tool='Snapshot',wall=1),
               dict(event='call_tool-end',call='0001-Snapshot',tool='Snapshot',wall=2,is_error=False),
               dict(event='call_tool-start',call='0002-Click',tool='Click',wall=402)]
        session=[dict(id='read-call',timestamp=stamp(10),message=dict(role='assistant',content=[dict(type='toolCall',name='read',id='tool-1',arguments=dict(path='C:/run/0001-Snapshot-00.png'))])),
                 dict(id='read-result',timestamp=stamp(11),message=dict(role='toolResult',toolCallId='tool-1',isError=False,content=[dict(type='image')]))]
        return calls,session

    def test_measures_whole_checkpoint_not_pure_model_latency(self):
        calls,session=self.data();sample=image_review_intervals(calls,session,runtime_root='C:/run')[0]
        self.assertEqual(sample['snapshot_to_read_complete_seconds'],9)
        self.assertEqual(sample['snapshot_to_next_tool_seconds'],400)
        self.assertEqual(sample['read_result_record'],'read-result')
        report=timing_readiness([sample])
        self.assertFalse(report['ready_for_live']);self.assertEqual(report['observed_checkpoint_sum_seconds'],800)
        self.assertTrue(report['observed_samples_exceed_window'])
        self.assertEqual(report['observed_fastest_read_complete_seconds'],9)
        with self.assertRaises(ValueError):timing_readiness([dict(sample,snapshot_to_read_complete_seconds=float('nan'))])

    def test_no_image_error_missing_result_wrong_path_or_inverted_time_refused(self):
        for mode in ('no-image','error','missing','wrong-path','late-result'):
            calls,session=self.data()
            if mode=='no-image':session[1]['message']['content']=[]
            elif mode=='error':session[1]['message']['isError']=True
            elif mode=='missing':session.pop()
            elif mode=='wrong-path':session[0]['message']['content'][0]['arguments']['path']='C:/other/0001-Snapshot-00.png'
            else:session[1]['timestamp']=datetime.fromtimestamp(500,timezone.utc).isoformat()
            with self.subTest(mode=mode),self.assertRaises(ValueError):image_review_intervals(calls,session,runtime_root='C:/run')

    def test_fast_sample_alone_cannot_authorize_live_or_weaken_watchdog(self):
        report=timing_readiness([dict(snapshot_to_next_tool_seconds=.1)])
        self.assertFalse(report['ready_for_live']);self.assertFalse(report['observed_samples_exceed_window'])
        for value in (float('nan'),float('inf'),-1):
            with self.assertRaises(ValueError):timing_readiness([dict(snapshot_to_next_tool_seconds=value)])
        with self.assertRaises(ValueError):timing_readiness([dict(snapshot_to_next_tool_seconds=1)],watchdog_seconds=900)
        with self.assertRaises(ValueError):timing_readiness([dict(snapshot_to_next_tool_seconds=1)],minimum_review_checkpoints=1)


if __name__=='__main__':unittest.main(verbosity=2)
