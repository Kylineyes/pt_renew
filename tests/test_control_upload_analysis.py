"""验证旧计时日志的区间边界与裁剪预算，全程不导入桌面包。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from analyze_control_uploads import API_COUNTS, analyze, overlap_bounds
from replay_control_health import INDICATOR_THREAD


def fixture():
    # 上传实际耗时0.4秒，日志允许起点位于[0.2, 0.4]；不能将0.4当作精确起点。
    rows = [dict(event='indicator-bitmap-timing-installed', monotonic=0., schema_version=1),
            dict(event='indicator-phase', monotonic=.2, started=.1, finished=.2,
                 duration_seconds=.1, name='_monitor_rects', parent=None, thread=INDICATOR_THREAD)]
    stages = {name: dict(calls=count, duration_seconds=.04) for name, count in API_COUNTS.items()}
    rows += [dict(event='indicator-bitmap-upload', monotonic=.8, thread=INDICATOR_THREAD,
                  duration_seconds=.4, measured_api_seconds=.36, outside_api_seconds=.04,
                  width=1, height=1, bgra_bytes=4, exception=None, stages=stages),
             dict(event='indicator-health-sample', monotonic=1.1, now=1.1, heartbeat=0.,
                  heartbeat_age_seconds=1.1, healthy=False, alive=True, stopping=False,
                  error=None, phase=None),
             dict(event='trace-closed', monotonic=2., dropped=0)]
    return rows


class UploadAnalysisTests(unittest.TestCase):
    def test_emission_timestamp_is_only_latest_finish(self):
        upload = analyze(fixture())['stale_intervals'][0]['last_stale_window']['uploads'][0]
        self.assertAlmostEqual(upload['earliest_start'], .2)
        self.assertAlmostEqual(upload['latest_start'], .4)
        self.assertAlmostEqual(upload['earliest_finish'], .6)
        self.assertAlmostEqual(upload['latest_finish'], .8)
        self.assertAlmostEqual(upload['emission_slack_bound_seconds'], .2)

    def test_fixed_length_overlap_bounds_cover_moving_intervals(self):
        self.assertEqual(overlap_bounds(0., 2., 1., 1., 2.), (0., 1.))
        self.assertEqual(overlap_bounds(0., 2., 1., -1., 4.), (1., 1.))
        self.assertEqual(overlap_bounds(0., 2., 1., 4., 5.), (0., 0.))
        # 逐点独立核对边界，防止区间包含关系和短观察窗被当作线性比例。
        for left, right in ((.2,.3), (.5,1.7), (-1.,.8), (1.8,3.2)):
            lo, hi = overlap_bounds(0., 2., 1., left, right)
            for step in range(201):
                start = step/100
                actual = max(0., min(start+1, right)-max(start, left))
                self.assertLessEqual(lo, actual+1e-12)
                self.assertGreaterEqual(hi+1e-12, actual)

    def test_crossing_cutoff_never_assigns_future_api_total_to_past(self):
        from analyze_control_uploads import summarize_window, upload_windows
        report = summarize_window(upload_windows(fixture()), [], 0., .5)
        upload = report['uploads'][0]
        self.assertAlmostEqual(upload['overlap_lower_seconds'], .1)
        self.assertAlmostEqual(upload['overlap_upper_seconds'], .3)
        bounds = report['removable_api_wall_bounds']['immutable_surface']
        self.assertAlmostEqual(bounds['lower_seconds'], 0.)
        self.assertAlmostEqual(bounds['upper_seconds'], .24)
        self.assertFalse(upload['record_emitted_by_cutoff'])
        # 已知阶段与上传重叠只能取并集。
        phases = [dict(started=.1, finished=.8)]
        report = summarize_window(upload_windows(fixture()), phases, 0., .5)
        self.assertAlmostEqual(report['phase_and_upload_union_lower_seconds'], .4)
        self.assertAlmostEqual(report['phase_and_upload_union_upper_seconds'], .4)

    def test_enclosing_phase_narrows_bounds_without_changing_visible_evidence(self):
        rows = fixture()
        rows.insert(3, dict(event='indicator-phase', monotonic=.9, started=.35, finished=.85,
                            duration_seconds=.5, name='layer.set_opacity', parent=None,
                            thread=INDICATOR_THREAD))
        result = analyze(rows)
        upload = result['stale_intervals'][0]['last_stale_window']['uploads'][0]
        self.assertAlmostEqual(upload['earliest_start'], .35)
        self.assertAlmostEqual(upload['latest_start'], .4)
        self.assertEqual(result['health_replay']['stale_heartbeat_intervals'][0]['observations'][0]['phase'], None)

    def test_full_upload_costs_exact_but_not_claimed_as_saved_cpu(self):
        report = analyze(fixture())
        window = report['stale_intervals'][0]['last_stale_window']
        for key in ('upload_overlap_lower_seconds','upload_overlap_upper_seconds'):
            self.assertAlmostEqual(window[key], .4)
        for value in window['removable_api_wall_bounds']['immutable_surface'].values():
            self.assertAlmostEqual(value, .24)
        self.assertIn('不是预计提速', report['interpretation'])
        self.assertEqual(report['desktop_requests'], 0)

    def test_missing_or_contradictory_upload_evidence_rejected(self):
        cases = [('exception','OSError'), ('width',0), ('bgra_bytes',8),
                 ('measured_api_seconds',.1), ('duration_seconds',-.1),
                 ('outside_api_seconds',float('nan')), ('thread','其他线程')]
        for key, value in cases:
            rows = fixture()
            rows[2][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                analyze(rows)
        for mutate in (lambda r: r[2]['stages'].pop('DeleteDC'),
                       lambda r: r[2]['stages']['SelectObject'].update(calls=1),
                       lambda r: r[2]['stages']['memmove'].update(duration_seconds=-.1),
                       lambda r: r[0].update(schema_version=2),
                       lambda r: r.insert(1,deepcopy(r[0])),
                       lambda r: r[2].update(duration_seconds=.9, outside_api_seconds=.54)):
            rows=fixture()
            mutate(rows)
            with self.assertRaises(ValueError): analyze(rows)

    def test_newer_observed_heartbeat_excludes_later_upload_from_old_timeout(self):
        rows=fixture()[:-1]
        rows.append(dict(event='indicator-health-sample',monotonic=1.95,now=1.95,
                         heartbeat=1.9,heartbeat_age_seconds=1.95-1.9,healthy=True,
                         alive=True,stopping=False,error=None,phase=None))
        future=deepcopy(rows[2])
        future['monotonic']=5.8
        rows += [future,dict(event='trace-closed',monotonic=6.,dropped=0)]
        group=analyze(rows)['stale_intervals'][0]
        self.assertEqual(len(group['last_stale_window']['uploads']),1)
        # 到恢复采样的上下文只能承认后来上传至多与[1.9,1.95]重叠，
        # 不能将整段0.4秒成本记为超时之前已发生。
        later=group['context_window']['uploads'][1]
        self.assertAlmostEqual(later['earliest_start'],1.9)
        self.assertAlmostEqual(later['overlap_lower_seconds'],0.)
        self.assertAlmostEqual(later['overlap_upper_seconds'],.05)

    def test_same_thread_time_reversal_or_missing_anchor_rejected(self):
        rows=fixture()
        rows[2]['monotonic']=.15
        with self.assertRaisesRegex(ValueError,'倒退'): analyze(rows)
        rows=fixture()
        del rows[1]
        with self.assertRaisesRegex(ValueError,'边界'): analyze(rows)


if __name__ == '__main__':
    unittest.main(verbosity=2)
