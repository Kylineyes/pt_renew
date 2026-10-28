"""独立离线核对正常资源寿命与API次数，不加载控制或原生适配器。"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

EXPECTED = {
    'initialize': dict(GetDC=1,CreateCompatibleDC=1,CreateDIBSection=1,SelectObject=1,memmove=1,ReleaseDC=1),
    'upload': dict(GetDC=1,UpdateLayeredWindow=1,ReleaseDC=1),
    'retire': dict(SelectObject=1,DeleteDC=1,DeleteObject=1),
}


def audit(rows):
    if (not rows or rows[-1].get('event') != 'trace-closed' or rows[-1].get('dropped') != 0
            or any(row.get('event') == 'trace-closed' for row in rows[:-1])):
        raise ValueError('需要正常关闭、无丢失的单次日志')
    installed = [row for row in rows if row.get('event') == 'indicator-surface-installed']
    if len(installed) != 1 or installed[0].get('schema_version') != 1:
        raise ValueError('缺少唯一资源实验安装记录')
    if installed[0].get('max_surfaces') != 64 or installed[0].get('max_bitmap_bytes') != 64*1024*1024:
        raise ValueError('资源预算与冻结方案不同')
    active, retired, counts = {}, set(), Counter()
    installed_seen = False
    uploaded = set()
    shutdown = owner_exit = 0
    uploads = 0

    def resources():
        return dict(surfaces=len(active),reserved_bytes=sum(w*h*4 for w,h in active.values()),failed=False,
                    screen_dc_count=0,memory_dc_count=len(active),bitmap_count=len(active),selected_bitmap_count=len(active))

    for row in rows:
        event = row.get('event')
        if event == 'indicator-surface-installed':
            installed_seen = True
        elif event == 'indicator-surface-operation':
            if not installed_seen:
                raise ValueError('安装记录之前出现资源操作')
            if shutdown or owner_exit:
                raise ValueError('退出记录之后仍有资源操作')
            ident, operation = row.get('surface_id'), row.get('operation')
            width, height = row.get('width'), row.get('height')
            if (type(ident) is not int or ident <= 0 or operation not in EXPECTED or
                    type(width) is not int or type(height) is not int or width <= 0 or height <= 0 or
                    row.get('bgra_bytes') != width*height*4):
                raise ValueError('资源身份、尺寸或阶段无效')
            if row.get('exception', '缺失') is not None:
                raise ValueError('存在异常操作，不能作为正常寿命验收')
            stages = row.get('stages')
            if not isinstance(stages,dict) or set(stages) != set(EXPECTED[operation]):
                raise ValueError('资源API集合不符')
            for name, stage in stages.items():
                value=stage.get('duration_seconds')
                if (type(stage.get('calls')) is not int or stage['calls'] != EXPECTED[operation][name]
                        or type(stage.get('failures')) is not int or stage['failures'] != 0 or
                        type(value) not in (int,float) or not math.isfinite(value) or value < 0):
                    raise ValueError('资源API次数、失败或耗时不符')
                counts[name] += stage['calls']
            times=[row.get(name) for name in ('started','finished','duration_seconds')]
            if (any(type(v) not in (int,float) or not math.isfinite(v) for v in times)
                    or times[1] < times[0] or abs(times[1]-times[0]-times[2]) > 1e-8
                    or sum(stage['duration_seconds'] for stage in stages.values()) > times[2]+1e-8):
                raise ValueError('资源操作时间矛盾')
            if operation == 'initialize':
                if ident in active or ident in retired or ident != len(active)+len(retired)+1:
                    raise ValueError('重复初始化、跳过或复用已退役资源身份')
                active[ident]=(width,height)
            else:
                if active.get(ident) != (width,height):
                    raise ValueError('上传或退役不属于同一资源寿命')
                if operation == 'retire':
                    if ident not in uploaded:
                        raise ValueError('资源寿命缺少正常上传')
                    del active[ident]
                    retired.add(ident)
                else:
                    uploads+=1
                    uploaded.add(ident)
            if len(active)>64 or resources()['reserved_bytes']>64*1024*1024:
                raise ValueError('正常记录超过冻结资源预算')
            if row.get('resources') != resources():
                raise ValueError('资源快照与独立寿命重算不一致')
        elif event in ('indicator-surface-owner-exit','indicator-surface-shutdown'):
            if active or row.get('resources') != resources():
                raise ValueError('退出时仍有资源或失败锁存')
            if event.endswith('owner-exit'):
                if owner_exit or shutdown or row.get('cleanup_errors') != 0:
                    raise ValueError('所属线程退出记录不完整或重复')
                owner_exit+=1
            else:
                if shutdown or not owner_exit or row.get('balanced') is not True:
                    raise ValueError('服务退出缺少所属线程退役及零账本证明')
                shutdown+=1
    if active or not retired or not uploads or not shutdown:
        raise ValueError('没有完整的正常上传寿命及服务退出记录')
    return dict(verified=True,surfaces=len(retired),uploads=uploads,api_calls=dict(counts),
                resources_at_exit=resources(),desktop_requests=0,
                limitation='仅证明正常资源记录的内部一致性，不证明真实图像、GUI回调、性能改善或控制稳定。')


def main():
    parser=argparse.ArgumentParser(description='离线核对正常图层资源寿命与API次数')
    parser.add_argument('--trace',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.trace.resolve() == args.output.resolve():parser.error('不能覆盖输入日志')
    raw=args.trace.read_bytes()
    try:
        result=audit([json.loads(line) for line in raw.decode('utf-8-sig').splitlines()])
    except (ValueError,TypeError,KeyError,AttributeError) as error:
        parser.exit(1,'资源审计失败：'+str(error)+'\n')
    result.update(source=str(args.trace.resolve()),source_sha256=hashlib.sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as out:json.dump(result,out,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
