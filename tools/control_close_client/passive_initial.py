"""只读取当前新链已有JSONL，保守观察初始条件，不调用桌面/控制API。"""
import json
from control_surface_approval import surface_initial_ready


def evaluate(rows, now, started):
    if now-started < 10.:
        return dict(ready=False, reason='新链观察不足10秒')
    if any(r.get('event')=='trace-closed' for r in rows):
        return dict(ready=False, reason='控制日志已关闭')
    resource=surface_initial_ready(rows)
    if not resource['ready']:return resource
    controls=[r for r in rows if isinstance(r.get('control'),dict) and 'state' in r['control']]
    health=[r for r in rows if r.get('event')=='indicator-health-sample']
    if not controls or not health:
        return dict(ready=False, reason='缺少原状态或新鲜健康记录')
    control=max(controls,key=lambda r:r['monotonic'])
    latest=max(health,key=lambda r:r['monotonic'])
    if not 0<=now-latest['monotonic']<=2. or latest.get('healthy') is not True:
        return dict(ready=False, reason='健康日志不新鲜或未健康')
    inputs=[r['monotonic'] for r in rows if r.get('event') in ('input-processed','hook-event')]
    last=max(inputs,default=started)
    if not 0<=now-last or now-last<10.:
        return dict(ready=False, reason='最近10秒有记录输入',last_recorded_input=last)
    state=control['control']
    if state.get('state')!='ready' or state.get('emergency') is not False:
        return dict(ready=False, reason='原状态未ready或异常')
    if any(state.get(n)!=0 for n in ('pressed_count','mouse_down_count')):
        return dict(ready=False, reason='原状态存在保持输入或未知')
    return dict(ready=True, reason='已有日志显示原ready且10秒无输入记录',
                state_record_monotonic=control['monotonic'],health_record_monotonic=latest['monotonic'],
                last_recorded_input=last,observed_at=now,desktop_requests=0)


def read_rows(path):
    if not path.exists():return []
    data=path.read_bytes()
    # 仅处理已完整写入的行，尾部写到一半留待下一次；其余损坏输入拒绝。
    lines=data.split(b'\n')[:-1]
    return [json.loads(line) for line in lines if line.strip()]
