"""常驻采样的离线回归：线程、取消、时间覆盖及拒绝；无 Win32。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from legacy_click_sampling import SamplingJob, SamplingWorker, check_sample, require_coverage


def row():
    start = time.perf_counter_ns()
    return {'start_ns': start, 'end_ns': time.perf_counter_ns(),
            'windows': [{'hwnd': 12, 'pid': 34}],
            'foreground_before': {'value': 12}, 'foreground_after': {'value': 12}}


class SamplingTests(unittest.TestCase):
    def test_actual_thread_trigger_first_ack_end_and_join(self):
        calls = []
        class Fake:
            def sample(self, *args):
                calls.append(threading.get_ident())
                return row()
        with tempfile.TemporaryDirectory(prefix='pt-renew-ex001-') as directory:
            worker = SamplingWorker(observer_factory=Fake)
            try:
                job = worker.submit(SamplingJob(Path(directory) / 'trace.jsonl', 12, 34, [1, 2], .08, .01, True))
                self.assertTrue(job.ready.wait(2))
                self.assertEqual(job.first_failures, [])
                self.assertTrue(job.done.wait(2))
                self.assertGreaterEqual(require_coverage(job)['samples'], 2)
                records = [json.loads(x) for x in job.path.read_text(encoding='utf-8').splitlines()]
                self.assertEqual(records[0]['kind'], 'header')
                self.assertEqual(records[-1]['kind'], 'end')
                self.assertTrue(all(x != threading.get_ident() for x in calls))
            finally:
                self.assertTrue(worker.close())

    def test_first_failure_cancels_before_new_sample_and_thread_survives(self):
        class Fake:
            def sample(self, *args):
                value = row()
                value['query'] = {'api': 'GetCursorPos', 'failed': True, 'win32_error': 5}
                return value
        with tempfile.TemporaryDirectory(prefix='pt-renew-ex001-') as directory:
            worker = SamplingWorker(observer_factory=Fake)
            try:
                job = worker.submit(SamplingJob(Path(directory) / 'trace.jsonl', 12, 34, [1, 2], 1, .01, True))
                self.assertTrue(job.done.wait(2))
                self.assertEqual(job.summary['samples'], 1)
                self.assertTrue(job.first_failures)
                with self.assertRaises(RuntimeError): require_coverage(job)
            finally:
                self.assertTrue(worker.close())

    def test_existing_output_failure_signals_both_events_without_factory(self):
        def forbidden(): raise AssertionError('不能加载接口')
        with tempfile.TemporaryDirectory(prefix='pt-renew-ex001-') as directory:
            path = Path(directory) / 'trace.jsonl'
            path.write_text('原件', encoding='utf-8')
            worker = SamplingWorker(observer_factory=forbidden)
            try:
                job = worker.submit(SamplingJob(path, 12, 34, [1, 2], .05, .01, False))
                self.assertTrue(job.done.wait(2))
                self.assertTrue(job.ready.is_set())
                self.assertIn('FileExistsError', job.summary['error'])
                self.assertTrue(job.cancel.is_set())
                self.assertIsNotNone(job.failure)
                self.assertEqual(path.read_text(encoding='utf-8'), '原件')
            finally:
                self.assertTrue(worker.close())

    def test_identity_and_foreground_not_inferred_from_success(self):
        value = row()
        value['windows'][0]['pid'] = 99
        value['foreground_after']['value'] = 88
        self.assertEqual(len(check_sample(value, 12, 34, True)), 2)
        self.assertEqual(len(check_sample(value, 12, 34, False)), 1)

    def test_coverage_boundaries_and_no_premature_success(self):
        job = SamplingJob('unused', 12, 34, [1, 2], 2, .01, True)
        job.summary = {'samples': 100, 'failures': [], 'cancelled': False,
                       'max_sample_ns': 1_000_000, 'max_start_gap_ns': 11_000_000,
                       'first_sample_start_ns': 10, 'last_sample_end_ns': 2_000_000_000}
        with self.assertRaises(RuntimeError): require_coverage(job, 100, 500_000_000)
        job.done.set()
        require_coverage(job, 100, 500_000_000)
        for key, value in [('max_start_gap_ns', 50_000_001), ('max_sample_ns', 30_000_001),
                           ('samples', 1), ('last_sample_end_ns', 550_000_000)]:
            original = copy.deepcopy(job.summary)
            job.summary[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                require_coverage(job, 100, 500_000_000)
            job.summary = original
        with self.assertRaises(RuntimeError): require_coverage(job, 1, 500_000_000)

    def test_success_then_failure_and_exception_block_click(self):
        job = SamplingJob('unused', 12, 34, [1, 2], 2, .01, True)
        first = row()
        job.accept(first)
        job.guard(require_running=True, require_foreground=True, clock=lambda: first['end_ns'])
        second = row()
        second['query'] = {'api': 'GetCursorPos', 'failed': True, 'win32_error': 5}
        job.accept(second)
        sent = []
        with self.assertRaises(RuntimeError):
            job.guard(require_running=True, require_foreground=True)
            sent.append('Click')
        self.assertEqual(sent, [])
        self.assertEqual(job.first_failures, [])
        self.assertTrue(job.cancel.is_set())
        self.assertIsNotNone(job.failure)

        class Broken:
            def sample(self, *args): raise OSError('接口异常')
        with tempfile.TemporaryDirectory(prefix='pt-renew-ex001-') as directory:
            worker = SamplingWorker(observer_factory=Broken)
            try:
                broken = worker.submit(SamplingJob(Path(directory)/'trace.jsonl', 12, 34, [1, 2], 1, .01, True))
                self.assertTrue(broken.done.wait(2))
                self.assertTrue(broken.cancel.is_set())
                with self.assertRaisesRegex(RuntimeError, '接口异常'): broken.guard()
            finally:
                self.assertTrue(worker.close())

    def test_online_duration_gap_and_stale_or_early_end_signals(self):
        for change in ('duration', 'gap', 'stale', 'early_end', 'foreground'):
            with self.subTest(change=change):
                job = SamplingJob('unused', 12, 34, [1, 2], 2, .01, True)
                first = row()
                job.accept(first)
                next_row = copy.deepcopy(first)
                next_row['start_ns'] += 10_000_000
                next_row['end_ns'] += 10_000_000
                if change == 'duration': next_row['end_ns'] = next_row['start_ns'] + 30_000_001
                if change == 'gap':
                    next_row['start_ns'] = first['start_ns'] + 50_000_001
                    next_row['end_ns'] = next_row['start_ns'] + 1
                if change == 'foreground': next_row['foreground_after']['value'] = 99
                job.accept(next_row)
                if change == 'early_end': job.done.set()
                now = next_row['end_ns'] + (50_000_001 if change == 'stale' else 0)
                with self.assertRaises(RuntimeError):
                    job.guard(require_running=True, require_foreground=True, clock=lambda: now)
                self.assertTrue(job.cancel.is_set())
                self.assertIsNotNone(job.failure)

    def test_blocked_call_is_not_claimed_stopped_by_budget_or_join(self):
        entered, release = threading.Event(), threading.Event()
        class Slow:
            def sample(self, *args):
                entered.set()
                release.wait()
                return row()
        with tempfile.TemporaryDirectory(prefix='pt-renew-ex001-') as directory:
            worker = SamplingWorker(observer_factory=Slow)
            job = worker.submit(SamplingJob(Path(directory) / 'trace.jsonl', 12, 34, [1, 2], .005, .005, False))
            try:
                self.assertTrue(entered.wait(2))
                self.assertFalse(worker.close(timeout=.01))
                self.assertFalse(job.done.is_set())
            finally:
                release.set()
                worker.thread.join(2)
            self.assertFalse(worker.thread.is_alive())
            self.assertTrue(job.done.is_set())


if __name__ == '__main__': unittest.main(verbosity=2)
