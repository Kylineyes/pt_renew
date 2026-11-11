"""常驻驱动的只读采样线程；不创建窗口、不发送输入、不改变 DPI。"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
import queue
import threading
import time

from observe_legacy_click import Observer, sample_for, validate


def check_sample(row, hwnd, pid, require_foreground=False):
    """失败即拒绝继续；命中预测为空不等同于 API 失败或真实接收者。"""
    failures = []
    def visit(value):
        if isinstance(value, dict):
            if value.get('failed'):
                failures.append({'api': value['api'], 'win32_error': value.get('win32_error')})
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(row)
    target = next((w for w in row['windows'] if w['hwnd'] == hwnd), None)
    if not target or target['pid'] != pid:
        failures.append({'identity': '目标 HWND/PID 不符'})
    if require_foreground and any(row[key]['value'] != hwnd for key in ('foreground_before', 'foreground_after')):
        failures.append({'foreground': '输入前目标不是稳定前景'})
    return failures


class SamplingJob:
    def __init__(self, path, hwnd, pid, point, duration, interval, require_foreground):
        validate([hwnd], point, duration, interval)
        self.path = Path(path)
        self.hwnd, self.pid, self.point = hwnd, pid, point
        self.duration, self.interval = duration, interval
        self.require_foreground = require_foreground
        self.ready = threading.Event()
        self.done = threading.Event()
        self.cancel = threading.Event()
        self.summary = None
        self.first_failures = None


class SamplingWorker:
    """同一进程的线程预先启动；队列触发，不在聚焦后创建进程。"""
    def __init__(self, *, observer_factory=Observer):
        self.factory = observer_factory
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, name='legacy-readonly-observer', daemon=False)
        self.thread.start()

    def submit(self, job):
        if not self.thread.is_alive():
            raise RuntimeError('采样线程已退出')
        self.queue.put(job)
        return job

    def _run(self):
        while (job := self.queue.get()) is not None:
            rows = []
            failures = []
            try:
                # 排他创建和接口加载均在观测线程；不继承其它线程的临时 DPI 设置。
                with job.path.open('x', encoding='utf-8') as output:
                    def emit(value):
                        output.write(json.dumps(value, ensure_ascii=False) + '\n')
                        output.flush()
                    before = time.perf_counter_ns()
                    utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    after = time.perf_counter_ns()
                    emit({'kind': 'header', 'clock': 'perf_counter_ns', 'utc': utc,
                          'utc_anchor_ns': [before, after], 'thread_id': threading.get_native_id(),
                          'hwnd': job.hwnd, 'pid': job.pid, 'point': job.point})
                    observer = self.factory()
                    observer.cancelled = job.cancel.is_set
                    def record(row):
                        errors = check_sample(row, job.hwnd, job.pid,
                                              job.require_foreground and not rows)
                        rows.append(row)
                        failures.extend(errors)
                        emit({'kind': 'sample', **row})
                        if len(rows) == 1:
                            job.first_failures = errors
                            job.ready.set()
                        if errors:
                            job.cancel.set()
                    result = sample_for(observer, [job.hwnd], job.point, job.duration, job.interval,
                                        record, stop=job.cancel.is_set)
                    gaps = [b['start_ns'] - a['start_ns'] for a, b in zip(rows, rows[1:])]
                    job.summary = {**result, 'failures': failures,
                        'first_sample_start_ns': rows[0]['start_ns'] if rows else None,
                        'last_sample_end_ns': rows[-1]['end_ns'] if rows else None,
                        'max_sample_ns': max((r['end_ns'] - r['start_ns'] for r in rows), default=0),
                        'max_start_gap_ns': max(gaps, default=0),
                        'cancelled': job.cancel.is_set()}
                    emit({'kind': 'end', **job.summary})
            except BaseException as error:
                job.summary = {'error': type(error).__name__ + ': ' + str(error)}
                job.first_failures = [{'error': job.summary['error']}]
            finally:
                job.ready.set()
                job.done.set()

    def close(self, timeout=5):
        self.queue.put(None)
        self.thread.join(timeout)
        return not self.thread.is_alive()


def require_coverage(job, send_ns=None, receive_ns=None):
    """50 ms 是本候选的漏采拒绝线，不是 Windows 事件分辨率保证。"""
    if not job.done.is_set():
        raise RuntimeError('采样尚未真实结束')
    result = job.summary
    if result.get('error') or result.get('failures') or result.get('cancelled'):
        raise RuntimeError('只读查询失败或取消：' + json.dumps(result, ensure_ascii=False))
    if result['samples'] < 2 or result['max_sample_ns'] > 30_000_000 or result['max_start_gap_ns'] > 50_000_000:
        raise RuntimeError('采样耗时或间隔不足以支持本次诊断')
    if send_ns is not None and not (result['first_sample_start_ns'] < send_ns <= receive_ns < result['last_sample_end_ns'] - 100_000_000):
        raise RuntimeError('采样未覆盖完整公开 RPC 及至少 100 ms 后段')
    return result
