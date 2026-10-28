"""离线重放控制健康日志，按区间并集核对阶段覆盖；不导入桌面控制包。"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

INDICATOR_THREAD = 'windows-mcp-control-indicator'


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def union_seconds(intervals, start, end):
    """裁剪后合并重叠区间，嵌套阶段不重复计时。"""
    clipped = sorted((max(start, a), min(end, b)) for a, b in intervals
                     if a < end and b > start)
    covered = 0.0
    right = start
    for left, finish in clipped:
        if finish > right:
            covered += finish - max(left, right)
            right = finish
    return covered


def replay(rows):
    """只使用日志所含证据，覆盖率是墙钟区间关联，不是CPU归因。"""
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError('日志行必须是对象')
    if not rows or rows[-1].get('event') != 'trace-closed':
        raise ValueError('日志缺少正常关闭记录，不能作为完整重放输入')
    if rows[-1].get('dropped') != 0:
        raise ValueError('日志记录有丢失，不能作为完整重放输入')
    if any(r.get('event') == 'trace-closed' for r in rows[:-1]):
        raise ValueError('日志中间出现关闭记录，可能拼接了多个运行')
    for row in rows:
        if not isinstance(row.get('event'), str) or not finite(row.get('monotonic')):
            raise ValueError('日志事件名或单调时间无效')

    samples = [r for r in rows if r['event'] == 'indicator-health-sample']
    if not samples:
        raise ValueError('日志没有实际健康采样')
    reasons = Counter()
    stale = []
    for row in samples:
        if type(row.get('healthy')) is not bool:
            raise ValueError('健康判定返回值不是布尔值')
        alive = row.get('alive', 'missing')
        if alive is not None and type(alive) is not bool:
            raise ValueError('健康采样缺少有效线程状态')
        if alive is True and (type(row.get('stopping')) is not bool or 'error' not in row):
            raise ValueError('健康采样缺少停止或错误状态')
        if alive is True and row['stopping'] is False and row['error'] is None:
            now, heartbeat, age = (row.get(k) for k in ('now', 'heartbeat', 'heartbeat_age_seconds'))
            if not all(finite(v) for v in (now, heartbeat, age)) or age != now-heartbeat:
                raise ValueError('健康采样的年龄与实际时间值不一致')
            expected = 0 <= age <= 1.0
            reason = 'healthy' if expected else 'future' if age < 0 else 'stale'
            if reason == 'stale':
                stale.append(row)
        else:
            # 原短路路径不应读取时间或心跳；不把缺字段当作短路证据。
            if any(row.get(k) is not None for k in ('now', 'heartbeat', 'heartbeat_age_seconds')):
                raise ValueError('健康短路路径却含心跳读取值')
            expected = False
            reason = 'absent' if row.get('alive') is None else 'dead' if not row['alive'] else 'stopping' if row['stopping'] else 'error'
        if row['healthy'] != expected:
            raise ValueError('健康返回值与原1秒判定不一致')
        reasons[reason] += 1

    phases = [r for r in rows if r['event'] == 'indicator-phase' and r.get('thread') == INDICATOR_THREAD]
    for phase in phases:
        if not all(finite(phase.get(k)) for k in ('started', 'finished', 'duration_seconds')):
            raise ValueError('阶段时间无效')
        if phase['finished'] < phase['started'] or not math.isclose(
                phase['duration_seconds'], phase['finished']-phase['started'], abs_tol=1e-9):
            raise ValueError('阶段耗时与起止时间不一致')
    groups = []
    for heartbeat in sorted({r['heartbeat'] for r in stale}):
        failures = sorted((r for r in stale if r['heartbeat'] == heartbeat), key=lambda r: r['now'])
        # 同一个旧心跳的多个观察点只报告一个停更区间。
        end = failures[-1]['now']
        overlapping = [p for p in phases if p['started'] < end and p['finished'] > heartbeat]
        intervals = [(p['started'], p['finished']) for p in overlapping]
        covered = union_seconds(intervals, heartbeat, end)
        first = failures[0]
        completed = [(p['started'], p['finished']) for p in overlapping if p['finished'] <= first['now']]
        observed = first.get('phase')
        if observed is not None:
            if not finite(observed.get('started')) or not heartbeat <= observed['started'] <= first['now']:
                # 观察到的阶段可能早于旧心跳，不额外宣称该部分有效覆盖。
                observed = None
            else:
                completed.append((observed['started'], first['now']))
        visible_coverage = union_seconds(completed, heartbeat, first['now'])
        events = [r for r in rows if heartbeat <= r['monotonic'] <= end]
        next_sample = min((r for r in samples if r.get('healthy') and finite(r.get('now')) and r['now'] > end),
                          key=lambda r: r['now'], default=None)
        groups.append(dict(
            heartbeat=heartbeat, last_stale_sample=end, stale_samples=len(failures),
            duration_seconds=end-heartbeat, measured_phase_union_seconds=covered,
            uncovered_seconds=max(0.0, end-heartbeat-covered),
            phase_coverage_fraction=covered/(end-heartbeat),
            first_stale_visible_phase_union_seconds=visible_coverage,
            first_stale_visible_coverage_fraction=visible_coverage/(first['now']-heartbeat),
            phases=[{k: p[k] for k in ('name','started','finished','duration_seconds','parent')} for p in overlapping],
            event_counts=dict(Counter(r['event'] for r in events)),
            hook_events=sum(r['event']=='hook-event' for r in events),
            processed_input_events=sum(r['event']=='input-processed' for r in events),
            observations=[{k: f.get(k) for k in ('now','heartbeat_age_seconds','thread','phase')} for f in failures],
            next_healthy_sample=({k:next_sample[k] for k in ('now','heartbeat','heartbeat_age_seconds')} if next_sample else None)))
    return dict(trace_rows=len(rows), samples=len(samples), sample_reasons=dict(reasons),
                stale_heartbeat_intervals=groups, event_counts=dict(Counter(r['event'] for r in rows)),
                fail_open=[{k:r.get(k) for k in ('monotonic','thread','source','probes')} for r in rows if r['event']=='fail-open'],
                interpretation='区间并集仅反映已记录调用的墙钟覆盖；不证明CPU耗时、底层API根因或无诊断环境因果。',
                desktop_requests=0)


def main():
    parser = argparse.ArgumentParser(description='离线重放控制健康及阶段日志，不访问桌面')
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.trace.resolve():
        parser.error('输出不能覆盖输入日志')
    raw = args.trace.read_bytes()
    try:
        report = replay([json.loads(line) for line in raw.decode('utf-8-sig').splitlines()])
    except (ValueError, TypeError, KeyError) as error:
        parser.exit(1, '离线重放失败：'+str(error)+'\n')
    report.update(source=str(args.trace.resolve()), source_sha256=hashlib.sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
    print(json.dumps(dict(samples=report['samples'], reasons=report['sample_reasons'],
                          intervals=[dict(heartbeat=g['heartbeat'], duration=g['duration_seconds'],
                                          phase_coverage=g['phase_coverage_fraction'], hooks=g['hook_events'],
                                          processed=g['processed_input_events']) for g in report['stale_heartbeat_intervals']],
                          desktop_requests=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
