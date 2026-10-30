"""异步实验的离线证据审计与门闩时间预算；不导入Qt/Win32，不启动产品。"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name):
    require(type(value) is int or isinstance(value, str) and re.fullmatch(r'[0-9]+', value), name+'不是无损非负整数')
    result=int(value)
    require(result>=0,name+'不能为负数')
    return result


def audit_events(rows, *, kind, mode, a_sha256, b_sha256, board_sha256):
    """只判断应用日志链，图片/真实编辑与退出须另行核对，绝不由事件授予GUI通过。"""
    require(kind in ('net','copper') and mode in ('control','race'),'实验类型或模式无效')
    require(all(isinstance(x,str) and re.fullmatch(r'[0-9a-f]{64}',x) for x in (a_sha256,b_sha256,board_sha256))
            and a_sha256!=b_sha256,'输入摘要格式无效或A/B指纹相同')
    require(bool(rows) and all(isinstance(x,dict) for x in rows),'事件必须是非空对象序列')
    require(rows[0].get('event')=='run-started' and rows[-1].get('event')=='run-stopped','缺少单次完整启动/停止记录')
    run,pid=rows[0].get('run_id'),rows[0].get('pid')
    require(bool(run) and integer(pid,'PID')>0,'缺少运行身份')
    previous=-1
    for number,row in enumerate(rows,1):
        require(row.get('run_id')==run and row.get('pid')==pid,'混入不同运行或PID')
        require(integer(row.get('sequence'),'序号')==number,'事件序号缺失、重复或乱序')
        stamp=integer(row.get('monotonic_ns'),'应用时钟')
        require(stamp>previous,'应用时钟未严格递增')
        previous=stamp
    require(sum(x['event']=='run-started' for x in rows)==1 and sum(x['event']=='run-stopped' for x in rows)==1,'拼接了多次运行')
    start=rows[0]
    require(start.get('kind_configured')==kind and start.get('skip')==(1 if kind=='net' else 0),'类型或跳过规则不匹配')
    watchdog=integer(start.get('watchdog_ms'),'看门狗')
    require(0<watchdog<=60000,'看门狗超出冻结实验上限')
    gated=[x for x in rows if x['event']=='request-created' and x.get('gated') is True]
    require(len(gated)==1 and gated[0].get('kind')==kind,'必须恰有一个目标门闩请求')
    request=gated[0];rid=request.get('request_id')
    require(integer(rid,'请求ID')>0,'请求ID无效')
    request_rows=[x for x in rows if x.get('request_id')==rid]
    require(all(x.get('kind')==kind for x in request_rows),'请求类型混淆')
    def one(event):
        found=[x for x in request_rows if x['event']==event]
        require(len(found)==1,'缺少或重复事件：'+event)
        return found[0]
    entered,ready,returned=(one(x) for x in ('worker-entered','gate-ready','worker-returned'))
    require(one('request-created')==request,'请求ID被重复使用')
    callback_rows=[x for x in request_rows if x['event'] in ('callback-accepted','callback-discarded')]
    require(len(callback_rows)==1,'缺少唯一完成回调')
    callback=callback_rows[0]
    require(integer(request.get('revision'),'请求修订')>0,'请求修订无效')
    require(integer(entered.get('thread_id'),'工作线程')>0 and integer(callback.get('thread_id'),'GUI线程')>0,'线程身份缺失')
    if kind=='net':
        integer(callback.get('captured_generation'),'捕获代次');integer(callback.get('current_generation'),'当前代次')
        require(callback.get('captured_generation')==request.get('generation'),'回调捕获代次不属于原请求')
    require(type(callback.get('accepted')) is bool
            and callback['accepted']==(callback['event']=='callback-accepted'),'回调事件与原接受决定矛盾')
    ns=lambda x:integer(x['monotonic_ns'],'应用时钟')
    require(ns(request)<ns(entered)<ns(ready)<ns(returned)<ns(callback),'请求/进入/门闩/返回/回调顺序不符')
    require(entered.get('thread_id')!=callback.get('thread_id') and request.get('thread_id')==callback.get('thread_id'),'工作与GUI线程证据不符')
    require(entered.get('stage')==('net-file-open-before-read' if kind=='net' else 'copper-entry-before-budget'),'工作入口位置不符')
    initial=[x for x in rows if x['event']=='worker-returned' and x.get('kind')=='net'
             and x.get('request_id')!=rid and ns(x)<ns(request) and x.get('success') is True and x.get('result_sha256')==a_sha256]
    require(len(initial)==1,'缺少门闩前A读取成功证据')
    initial_id=initial[0]['request_id']
    initial_callbacks=[x for x in rows if x['event']=='callback-accepted' and x.get('request_id')==initial_id and ns(x)<ns(request)]
    require(len(initial_callbacks)==1 and initial_callbacks[0].get('experiment_aborted') is False
            and initial_callbacks[0].get('accepted') is True,'A未有效接受')
    if kind=='net':
        require(request.get('previous_net_sha256')==a_sha256 and returned.get('success') is True
                and returned.get('result_sha256')==b_sha256,'A/B读取摘要或成功状态不符')
    else:
        require(request.get('board_sha256')==board_sha256 and request.get('net_sha256')==a_sha256
                and returned.get('net_sha256')==a_sha256 and returned.get('limit_reached') is False
                and returned.get('revision')==request.get('revision'),'铜输入/旧修订或预算结果不符')
    aborts=[x for x in request_rows if x['event']=='aborted']
    releases=[x for x in request_rows if x['event']=='gate-released']
    publications=[x for x in rows if x['event']=='document-published']
    if aborts or callback.get('experiment_aborted') is True:
        require(not releases,'同一中止请求同时含有效释放，证据矛盾')
        require(len(aborts)==1 and callback.get('experiment_aborted') is True,'中止事件与回调标记不一致')
        require(ns(ready)<ns(aborts[0])<ns(returned),'中止事件不在门闩与返回之间')
        return dict(event_chain_verified=False,status='aborted',kind=kind,mode=mode,run_id=run,request_id=rid,
                    gui_verified=False,reason='中止后的丢弃或接受不构成有效竞争',gate_wait_seconds=(ns(returned)-ns(ready))/1e9)
    require(not any(x['event']=='aborted' for x in rows),'运行中存在其他中止，不能记有效实验')
    require(callback.get('experiment_aborted') is False and len(releases)==1,'缺少未中止的唯一有效释放')
    released=releases[0]
    require(ns(ready)<ns(released)<ns(returned),'有效释放未处于门闩与返回之间')
    require(ns(released)-ns(ready)<watchdog*1_000_000,'释放已超出冻结看门狗')
    if mode=='control':
        require(not publications and callback['event']=='callback-accepted' and callback.get('accepted') is True,'对照含编辑或未接受')
        if kind=='copper':
            require(all(callback.get(x) is True for x in ('generation_matches','board_matches','net_matches')),'铜对照身份不匹配')
        else:
            require(callback.get('captured_generation')==callback.get('current_generation'),'NET对照代次不符')
    else:
        require(len(publications)==1,'竞争必须恰有一次文档发布')
        published=publications[0]
        require(ns(ready)<ns(published)<ns(released),'文档发布不在有效门闩内')
        require(published.get('dirty') is True and integer(published.get('tracks'),'走线数')==0
                and integer(published.get('revision'),'新修订')>integer(request.get('revision'),'旧修订')
                and published.get('net_sha256')==a_sha256,'新文档修订/dirty/走线/A来源不符')
        require(callback['event']=='callback-discarded' and callback.get('accepted') is False,'旧结果没有被原回调拒绝')
        if kind=='net':
            require(callback.get('revision')==published.get('revision')
                    and callback.get('captured_generation')!=callback.get('current_generation'),'NET新修订或原代次淘汰证据不符')
        else:
            require(callback.get('captured_revision')==request.get('revision') and callback.get('current_revision')==published.get('revision')
                    and callback.get('generation_matches') is False and callback.get('board_matches') is False
                    and callback.get('net_matches') is True,'铜新修订或原身份淘汰证据不符')
    return dict(event_chain_verified=True,status='control_events_pass' if mode=='control' else 'race_events_pass',
                kind=kind,mode=mode,run_id=run,request_id=rid,gui_verified=False,watchdog_ms=watchdog,
                gate_wait_seconds=(ns(released)-ns(ready))/1e9,
                reason='仅应用时钟事件链通过，真实读图/编辑及原退出证据仍须独立判断')


def image_review_intervals(calls, session_rows, *, runtime_root):
    """截图工具结束到下一动作的观察区间；不冒称模型纯计算延迟或未来耗时上界。"""
    prefix=str(runtime_root).replace('\\','/').rstrip('/')+'/'
    starts={x['call']:x for x in calls if x.get('event')=='call_tool-start'}
    ends={x['call']:x for x in calls if x.get('event')=='call_tool-end'}
    require(len(starts)==sum(x.get('event')=='call_tool-start' for x in calls)
            and len(ends)==sum(x.get('event')=='call_tool-end' for x in calls),'工具调用ID重复')
    reads={};results={}
    timestamp=lambda row:datetime.fromisoformat(row['timestamp'].replace('Z','+00:00')).timestamp()
    for row in session_rows:
        message=row.get('message',{})
        if message.get('role')=='assistant':
            for part in message.get('content',[]):
                path=str(part.get('arguments',{}).get('path','')).replace('\\','/')
                if part.get('type')=='toolCall' and part.get('name')=='read' and path.startswith(prefix) and path.endswith('.png'):
                    reads[part['id']]=dict(path=path,started_wall=timestamp(row),record=row.get('id'))
        elif message.get('role')=='toolResult':
            results[message.get('toolCallId')]=(row,message)
    samples=[]
    for call,end in ends.items():
        if end.get('tool')!='Snapshot':continue
        require(call in starts and end.get('is_error') is False,'Snapshot回执失败或起点缺失')
        matching=[(ident,read) for ident,read in reads.items() if read['path']==prefix+call+'-00.png']
        require(len(matching)==1,'每张图必须有唯一实际read')
        ident,read=matching[0]
        require(ident in results,'read没有完成回执')
        record,message=results[ident]
        require(message.get('isError') is False and any(x.get('type')=='image' for x in message.get('content',[])),'read没有成功返回图像')
        completed=timestamp(record)
        following=sorted((x for x in starts.values() if x['wall']>end['wall']),key=lambda x:x['wall'])
        require(bool(following),'读图后缺少下一原工具调用')
        next_call=following[0]
        require(end['wall']<=read['started_wall']<=completed<=next_call['wall'],'跨日志墙钟先后矛盾')
        samples.append(dict(snapshot=call,image=read['path'],read_record=read['record'],read_result_record=record.get('id'),
            snapshot_end_wall=end['wall'],read_start_wall=read['started_wall'],read_complete_wall=completed,next_tool_start_wall=next_call['wall'],
            snapshot_to_read_complete_seconds=completed-end['wall'],snapshot_to_next_tool_seconds=next_call['wall']-end['wall']))
    require(bool(samples),'没有可核对的实际图像阅读样本')
    return samples


def timing_readiness(samples, *, watchdog_seconds=60, minimum_review_checkpoints=2):
    require(type(watchdog_seconds) in (int,float) and math.isfinite(watchdog_seconds) and 0<watchdog_seconds<=60,'冻结门闩时间无效')
    require(type(minimum_review_checkpoints) is int and minimum_review_checkpoints>=2,'不能删除门闩图和编辑确认图阅读检查点')
    durations=[x['snapshot_to_next_tool_seconds'] for x in samples]
    require(bool(durations) and all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in durations),'阅读观察区间无效')
    # 即使把最快历史区间重复用于每个必需检查点，也还没包含截图/输入/释放开销。
    read_completed=[x['snapshot_to_read_complete_seconds'] for x in samples if 'snapshot_to_read_complete_seconds' in x]
    require(all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in read_completed),'read完成观察区间无效')
    observed_estimate=min(durations)*minimum_review_checkpoints
    return dict(ready_for_live=False,watchdog_seconds=watchdog_seconds,minimum_review_checkpoints=minimum_review_checkpoints,
        observed_fastest_read_complete_seconds=min(read_completed) if read_completed else None,
        observed_fastest_checkpoint_seconds=min(durations),observed_checkpoint_sum_seconds=observed_estimate,
        observed_samples_exceed_window=observed_estimate>=watchdog_seconds,
        reason='已有检查点观察耗时超出门闩窗口' if observed_estimate>=watchdog_seconds else '历史样本仍不能给未来实际读图及动作提供上界，需另行可验证执行设计',
        interpretation='观察区间含模型往返、工具调度和步骤整理，不是纯推理延迟；不是未来耗时数学下界或上界。')


def main():
    parser=argparse.ArgumentParser(description='离线核对异步应用事件，不启动GUI或发送release')
    parser.add_argument('--events',type=Path,required=True)
    parser.add_argument('--context',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    context=json.loads(args.context.read_text(encoding='utf-8-sig'))
    raw=args.events.read_bytes();rows=[json.loads(x) for x in raw.decode('utf-8-sig').splitlines()]
    result=audit_events(rows,**context)
    result.update(source_sha256=hashlib.sha256(raw).hexdigest(),desktop_requests=0)
    with args.output.open('x',encoding='utf-8') as out:json.dump(result,out,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
