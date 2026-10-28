"""离线核对位图上传与心跳超时的重叠边界，不导入桌面包。"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import hashlib
import json
from pathlib import Path

from replay_control_health import INDICATOR_THREAD, finite, replay, union_seconds

API_COUNTS = dict(GetDC=1, CreateCompatibleDC=1, CreateDIBSection=1, memmove=1,
                  SelectObject=2, UpdateLayeredWindow=1, DeleteObject=1,
                  DeleteDC=1, ReleaseDC=1)
RESOURCE_APIS = ('CreateCompatibleDC', 'CreateDIBSection', 'SelectObject', 'DeleteObject', 'DeleteDC')
POLICIES = dict(memory_surface=RESOURCE_APIS, immutable_surface=RESOURCE_APIS + ('memmove',))
TOLERANCE = 1e-8


def overlap(start, end, left, right):
    return max(0.0, min(end, right) - max(start, left))


def overlap_bounds(earliest_start, latest_start, duration, left, right):
    """固定长度区间在起点范围内移动；不假定API的具体位置。"""
    def amount(start):
        return overlap(start, start + duration, left, right)
    points = [earliest_start, latest_start]
    points.extend(max(earliest_start, min(latest_start, value)) for value in (left, right-duration))
    return min(amount(earliest_start), amount(latest_start)), max(map(amount, points))


def upload_windows(rows):
    """以同线程前序事件和外层阶段约束schema 1的上传起止时间。"""
    installed = [r for r in rows if r['event'] == 'indicator-bitmap-timing-installed']
    if len(installed) != 1 or installed[0].get('schema_version') != 1:
        raise ValueError('需要唯一的schema 1位图计时安装记录')
    phases = [r for r in rows if r['event'] == 'indicator-phase'
              and r.get('thread') == INDICATOR_THREAD]
    # 心跳只由同一个显示线程在完整一轮结束后写入。早于上传记录发出的
    # 实际样本的心跳写入时间先于本次上传，防止把数分钟后的上传归入旧超时。
    beats = sorted((r['monotonic'], r['heartbeat']) for r in rows
                   if r['event'] == 'indicator-health-sample' and finite(r.get('heartbeat'))
                   and r.get('heartbeat_age_seconds', -1) >= 0)
    beat_times, beat_values = [], []
    latest_beat = float('-inf')
    for observed, heartbeat in beats:
        latest_beat = max(latest_beat, heartbeat)
        beat_times.append(observed)
        beat_values.append(latest_beat)
    previous = None
    uploads = []
    for line, row in enumerate(rows, 1):
        if row.get('thread') != INDICATOR_THREAD:
            if row['event'] == 'indicator-bitmap-upload':
                raise ValueError('位图记录不属于指示层线程')
            continue
        emitted = row['monotonic']
        if previous is not None and emitted < previous:
            raise ValueError('同线程事件时间倒退')
        if row['event'] == 'indicator-bitmap-upload':
            duration = row.get('duration_seconds')
            if not finite(duration) or duration < 0:
                raise ValueError('上传耗时无效')
            if 'exception' not in row or row['exception'] is not None:
                raise ValueError('本工具仅分析完整正常上传，不能外推异常清理')
            w, h, size = (row.get(k) for k in ('width', 'height', 'bgra_bytes'))
            if any(type(v) is not int or v <= 0 for v in (w, h, size)) or size != w*h*4:
                raise ValueError('上传尺寸与BGRA字节数不一致')
            stages = row.get('stages')
            if not isinstance(stages, dict) or set(stages) != set(API_COUNTS):
                raise ValueError('上传API集合不完整')
            for name, count in API_COUNTS.items():
                stage = stages[name]
                if (not isinstance(stage, dict) or type(stage.get('calls')) is not int
                        or stage['calls'] != count or not finite(stage.get('duration_seconds'))
                        or stage['duration_seconds'] < 0):
                    raise ValueError('上传API次数或耗时无效：' + name)
            measured = sum(s['duration_seconds'] for s in stages.values())
            if (not finite(row.get('measured_api_seconds')) or
                    abs(measured-row['measured_api_seconds']) > TOLERANCE or
                    not finite(row.get('outside_api_seconds')) or
                    abs(duration-measured-row['outside_api_seconds']) > TOLERANCE or
                    measured > duration+TOLERANCE):
                raise ValueError('上传总耗时与API分段不一致')
            # 原_push_bitmap内部不写trace，前一个同线程事件先于本次上传。
            # 外层阶段结束事件可晚于上传记录，此处只用于事后约束，不作当时证据。
            parents = [p for p in phases if p['name'] in ('layer.set_opacity', '_build_layers')
                       and p['started'] <= emitted-duration+TOLERANCE
                       and emitted <= p['finished']]
            anchors = ([previous] if previous is not None else []) + [p['started'] for p in parents]
            beat_index = bisect_right(beat_times, emitted)-1
            if beat_index >= 0:
                anchors.append(beat_values[beat_index])
            if not anchors:
                raise ValueError('上传缺少可核对的同线程起点边界')
            earliest = max(anchors)
            latest = emitted-duration
            if earliest > latest+TOLERANCE:
                raise ValueError('上传耗时超过同线程事件所允许的区间')
            earliest = min(earliest, latest)
            uploads.append(dict(line=line, earliest_start=earliest, latest_start=latest,
                                earliest_finish=earliest+duration, latest_finish=emitted,
                                emission_slack_bound_seconds=latest-earliest,
                                duration_seconds=duration, width=w, height=h, bgra_bytes=size,
                                stages=stages))
        previous = emitted
    if not uploads:
        raise ValueError('日志没有正常上传')
    return uploads


def summarize_window(uploads, phases, left, right):
    selected = []
    totals = {name: dict(lower_seconds=0.0, upper_seconds=0.0) for name in POLICIES}
    lower = upper = 0.0
    guaranteed, possible = [], []
    for upload in uploads:
        if upload['earliest_start'] >= right or upload['latest_finish'] <= left:
            continue
        duration = upload['duration_seconds']
        minimum, maximum = overlap_bounds(upload['earliest_start'], upload['latest_start'],
                                          duration, left, right)
        lower += minimum
        upper += maximum
        guaranteed.append((upload['latest_start'], upload['earliest_finish']))
        possible.append((upload['earliest_start'], upload['latest_finish']))
        budgets = {}
        for name, apis in POLICIES.items():
            cost = sum(upload['stages'][api]['duration_seconds'] for api in apis)
            # 无API时间戳，只能给出集合在裁剪区间内的占时上下界，不能按比例分摊。
            bounds = dict(lower_seconds=max(0.0, cost-(duration-minimum)),
                          upper_seconds=min(cost, maximum))
            budgets[name] = bounds
            for key, value in bounds.items():
                totals[name][key] += value
        selected.append(dict(**upload, overlap_lower_seconds=minimum, overlap_upper_seconds=maximum,
                             removable_api_wall_bounds=budgets,
                             record_emitted_by_cutoff=upload['latest_finish'] <= right))
    phase_intervals = [(p['started'], p['finished']) for p in phases]
    guaranteed = [(a, b) for a, b in guaranteed if a < b]
    return dict(start=left, end=right, duration_seconds=right-left, uploads=selected,
                upload_overlap_lower_seconds=lower,
                upload_overlap_upper_seconds=min(right-left, upper),
                phase_and_upload_union_lower_seconds=union_seconds(phase_intervals+guaranteed, left, right),
                phase_and_upload_union_upper_seconds=union_seconds(phase_intervals+possible, left, right),
                removable_api_wall_bounds=totals)


def analyze(rows):
    health = replay(rows)
    uploads = upload_windows(rows)
    phases = [r for r in rows if r['event'] == 'indicator-phase' and r.get('thread') == INDICATOR_THREAD]
    groups = []
    for group in health['stale_heartbeat_intervals']:
        beat = group['heartbeat']
        first = group['observations'][0]['now']
        last = group['last_stale_sample']
        observed_recovery = group['next_healthy_sample']
        context_end = observed_recovery['now'] if observed_recovery else last
        timeline = []
        for line, row in enumerate(rows, 1):
            if row['event'] == 'indicator-phase':
                relevant = row['started'] < context_end and row['finished'] > beat
                keys = ('event', 'monotonic', 'thread', 'name', 'started', 'finished', 'parent')
            else:
                relevant = beat <= row['monotonic'] <= context_end
                keys = ('event', 'monotonic', 'thread', 'healthy', 'now', 'heartbeat', 'phase', 'source', 'probes')
            if relevant and row['event'] != 'indicator-bitmap-upload':
                timeline.append(dict(line=line, **{k: row[k] for k in keys if k in row}))
        groups.append(dict(heartbeat=beat, first_stale=first, last_stale=last,
                           first_stale_window=summarize_window(uploads, phases, beat, first),
                           last_stale_window=summarize_window(uploads, phases, beat, last),
                           next_healthy_observation=observed_recovery,
                           context_window=summarize_window(uploads, phases, beat, context_end),
                           timeline=timeline))
    return dict(schema_version=1, health_replay=health, upload_count=len(uploads),
                api_calls=dict(Counter({api: len(uploads)*count for api, count in API_COUNTS.items()})),
                stale_intervals=groups, policies={name: list(apis) for name, apis in POLICIES.items()},
                desktop_requests=0,
                interpretation='上传记录时间戳晚于计时结束；起止与裁剪成本采用边界。API集合占时不是预计提速、CPU成本或根因证明。',
                assumptions=['输入使用同一单调时钟尺度（本机Python的perf_counter与monotonic相同）',
                             'schema 1原上传内部没有其他同线程trace，上传按同一线程顺序执行',
                             '心跳只在所属显示线程完成整轮后写入，上传记录发出前观察到的心跳先于本次上传',
                             '事后外层阶段仅约束区间；不冒充超时判定当时可见证据',
                             '复用预算仅适用于已初始化且尺寸、像素、所属图层不变的后续上传，初始化与退役成本另计'])


def main():
    parser = argparse.ArgumentParser(description='离线分析位图上传与心跳停更边界，不访问桌面')
    parser.add_argument('--trace', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.trace.resolve() == args.output.resolve():
        parser.error('输出不能覆盖输入日志')
    raw = args.trace.read_bytes()
    try:
        report = analyze([json.loads(line) for line in raw.decode('utf-8-sig').splitlines()])
    except (ValueError, TypeError, KeyError) as error:
        parser.exit(1, '离线分析失败：'+str(error)+'\n')
    report.update(source=str(args.trace.resolve()), source_sha256=hashlib.sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
    print(json.dumps(dict(upload_count=report['upload_count'],
                          stale_intervals=len(report['stale_intervals']), desktop_requests=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
