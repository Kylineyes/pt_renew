"""离线日志重放的时间并集、证据边界及损坏输入测试，无桌面导入。"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from replay_control_health import replay, union_seconds, INDICATOR_THREAD


def sample(now, beat, healthy, **extra):
    return dict(event='indicator-health-sample', monotonic=now, now=now, heartbeat=beat,
                heartbeat_age_seconds=now-beat, alive=True, stopping=False, error=None,
                healthy=healthy, thread='看门狗', phase=None, **extra)


def phase(start, end, name='阶段', parent=None):
    return dict(event='indicator-phase', monotonic=end, started=start, finished=end,
                duration_seconds=end-start, thread=INDICATOR_THREAD, name=name, parent=parent)


def closed():
    return dict(event='trace-closed', monotonic=20., dropped=0)


class ReplayTests(unittest.TestCase):
    def test_union_clips_nested_overlapping_and_adjacent_intervals(self):
        self.assertAlmostEqual(union_seconds([(-1, .2), (0, .4), (.1, .3), (.4, .8), (.7, 2)], 0, 1), 1)
        self.assertEqual(union_seconds([(2,3)], 0,1), 0)

    def test_same_heartbeat_groups_samples_and_keeps_hindsight_separate(self):
        first=sample(1.1,0.,False)
        first['phase']=dict(name='透明度',started=.6)
        rows=[phase(.1,.6), first, phase(.6,1.2), sample(1.25,0.,False),
              dict(event='hook-event',monotonic=1.3), sample(1.4,1.35,True), closed()]
        report=replay(rows)
        self.assertEqual(report['sample_reasons'],{'stale':2,'healthy':1})
        group=report['stale_heartbeat_intervals'][0]
        self.assertEqual(group['stale_samples'],2)
        self.assertAlmostEqual(group['measured_phase_union_seconds'],1.1)
        self.assertAlmostEqual(group['first_stale_visible_phase_union_seconds'],1.)
        self.assertEqual(group['hook_events'],0)
        self.assertEqual(report['event_counts']['hook-event'],1)
        self.assertAlmostEqual(group['next_healthy_sample']['heartbeat'],1.35)

    def test_completed_parent_and_child_not_double_counted(self):
        rows=[phase(.1,.9),phase(.2,.8,parent='阶段'),sample(1.1,0.,False),closed()]
        self.assertAlmostEqual(replay(rows)['stale_heartbeat_intervals'][0]['measured_phase_union_seconds'],.8)

    def test_never_infers_missing_phase_as_unobserved_cpu_time(self):
        result=replay([sample(1.1,0.,False),closed()])['stale_heartbeat_intervals'][0]
        self.assertEqual(result['measured_phase_union_seconds'],0)
        self.assertAlmostEqual(result['uncovered_seconds'],1.1)
        self.assertIn('不证明CPU',replay([sample(1.1,0.,False),closed()])['interpretation'])

    def test_threshold_and_future_samples_match_original_rule(self):
        report=replay([sample(1.,0.,True), sample(1.,2.,False),closed()])
        self.assertEqual(report['sample_reasons'],{'healthy':1,'future':1})
        self.assertEqual(report['stale_heartbeat_intervals'],[])

    def test_short_circuit_with_no_heartbeat_is_preserved(self):
        row=dict(event='indicator-health-sample',monotonic=1.,healthy=False,alive=False,
                 stopping=None,error=None,now=None,heartbeat=None,heartbeat_age_seconds=None)
        self.assertEqual(replay([row,closed()])['sample_reasons'],{'dead':1})
        row['now']=1.
        with self.assertRaisesRegex(ValueError,'短路'):replay([row,closed()])

    def test_incomplete_dropped_or_concatenated_trace_rejected(self):
        for rows in ([sample(1.,0.,True)], [sample(1.,0.,True),dict(event='trace-closed',monotonic=2.,dropped=1)],
                     [sample(1.,0.,True),closed(),closed()]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):replay(rows)

    def test_contradictory_health_and_phase_evidence_rejected(self):
        for bad in (sample(1.1,0.,True), dict(sample(1.1,0.,False),heartbeat_age_seconds=.1),
                    dict(sample(1.1,0.,False),now=float('nan'))):
            with self.subTest(bad=bad),self.assertRaises(ValueError):replay([bad,closed()])
        malformed=[dict(sample(1.,0.,True),alive=1),dict(sample(1.,0.,True),stopping=None)]
        for row in malformed:
            with self.assertRaises(ValueError):replay([row,closed()])
        with self.assertRaises(ValueError):replay([[],closed()])
        bad_phase=dict(phase(.1,.9),duration_seconds=.9)
        with self.assertRaises(ValueError):replay([bad_phase,sample(1.1,0.,False),closed()])


if __name__=='__main__':
    unittest.main(verbosity=2)
