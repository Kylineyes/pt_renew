"""执行一份新UIA对象核验批准；无产品、控制服务、截图、输入或窗口查询入口。"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import time

from async_product_client.core import Clock, Context, Ledger, SECOND, digest, require
from async_product_client.events import decode_object
from async_product_client.runtime import write_once
from async_product_client.uia_object import UiaObjectOwner


def authorize(configuration):
    require(set(configuration) == {'context', 'approval', 'approval_sha256', 'session_file', 'session_prefix_bytes',
                                  'session_prefix_sha256', 'evidence_root', 'materials'}, '对象核验配置协议不符')
    context = Context(**configuration['context'])
    raw = Path(configuration['approval']).read_bytes()
    require(digest(raw) == configuration['approval_sha256'], '本轮批准原字节摘要改变')
    approval = decode_object(raw)
    require(approval.get('context') == asdict(context) and approval.get('scope') == 'uia-object-only'
            and approval.get('permission_confirmed') is True and approval.get('permission') and approval.get('message_id')
            and approval.get('max_object_creations') == 1 and approval.get('max_desktop_queries') == 0
            and approval.get('max_product_launches') == approval.get('max_control_services') == 0
            and approval.get('probe_seconds') == 5 and approval.get('diagnostic_seconds') == 600
            and approval.get('total_seconds') == 900 and approval.get('ready_for_live') is False
            and approval.get('evidence_root') == configuration['evidence_root'], '本轮UIA对象批准范围、授权或原预算不符')
    actual = tuple(os.environ.get(name) for name in ('PI_PROVIDER', 'PI_MODEL', 'PI_REASONING_LEVEL', 'PI_SESSION_ID'))
    require(actual == (context.provider, context.model, context.thinking, context.session_id), '实际Pi环境与本轮上下文不符')
    size = configuration['session_prefix_bytes']
    require(type(size) is int and size > 0, '缺少原Pi会话前缀')
    with Path(configuration['session_file']).open('rb') as source: prefix = source.read(size)
    require(len(prefix) == size and digest(prefix) == configuration['session_prefix_sha256'], '原Pi会话已核验前缀被改写')
    header = decode_object(prefix.splitlines()[0])
    require(header.get('type') == 'session' and header.get('id') == context.session_id, '原Pi会话头身份不符')
    return context


def run(configuration):
    clock = Clock(); started = clock.monotonic_ns()
    context = authorize(configuration)
    root = Path(configuration['evidence_root']).resolve(); root.mkdir(parents=True, exist_ok=False)
    events = (root / 'ledger.jsonl').open('x', encoding='utf-8')
    def emit(row):
        events.write(json.dumps(row, ensure_ascii=False) + '\n'); events.flush(); os.fsync(events.fileno())
    ledger = Ledger(context=context, cleanup_deadline_ns=started + 900 * SECOND, clock=clock, enabled=True, emit=emit)
    ledger.diagnostic_deadline_ns = started + 600 * SECOND
    owner = UiaObjectOwner(ledger, root / 'object-probe', enabled=True)
    write_once(root / 'run-started.json', json.dumps(dict(context=asdict(context), started_ns=started,
               diagnostic_deadline_ns=ledger.diagnostic_deadline_ns, cleanup_deadline_ns=ledger.cleanup_deadline_ns), ensure_ascii=False).encode('utf-8'))
    failure = None; result = None
    try:
        owner.start('object-start', ledger.token, materials=configuration['materials'])
        while owner.poll() is None:
            require(clock.monotonic_ns() < owner.deadline, '父等待已越过原5秒，保留原Popen且不重试')
            time.sleep(min(.01, max(0., (owner.deadline - clock.monotonic_ns()) / SECOND)))
        result = owner.finish('object-finish', ledger.token, materials=configuration['materials'])
        with ledger.operation('object-settle', ledger.token, deadline_ns=owner.deadline):
            write_once(root / 'verified.json', json.dumps(dict(context=asdict(context), original_identity=owner.identity,
                original_exit=owner.exit_code, result=result, elapsed_seconds=(clock.monotonic_ns()-started)/SECOND,
                ready_for_live=False, qt_verified=False, desktop_queries=0), ensure_ascii=False, indent=2).encode('utf-8'))
    except BaseException as error:
        failure = dict(error=type(error).__name__, reason=str(error))
        ledger.fail('object-probe', failure['reason']); owner.stop()
        write_once(root / 'failure.json', json.dumps(dict(failure, failed_id=ledger.failed, token=ledger.token,
            not_before_ns=ledger.not_before_ns, original_identity=owner.identity, original_exit=owner.exit_code,
            stop_requested=bool(owner.process and owner.process.poll() is None), deadline_ns=owner.deadline,
            accepted=False, ready_for_live=False), ensure_ascii=False, indent=2).encode('utf-8'))
        # 失败组仅本地原Popen等待和保留首次冷却，不执行任何新UIA/native/状态/截图/输入。
        deadline_unknown = False
        while clock.monotonic_ns() < ledger.not_before_ns or owner.process is not None and owner.poll() is None:
            if clock.monotonic_ns() >= ledger.cleanup_deadline_ns and not deadline_unknown:
                write_once(root / 'deadline-unknown.json', b'{"ready_for_live":false,"original_popen_preserved":true}')
                deadline_unknown = True
            time.sleep(.1)
    finally:
        if owner.process is not None: owner.poll()
        report = dict(context=asdict(context), original_identity=owner.identity, original_exit=owner.exit_code,
                      failed_id=ledger.failed, token=ledger.token, not_before_ns=ledger.not_before_ns,
                      deadline_ns=owner.deadline, finished_ns=clock.monotonic_ns(), elapsed_seconds=(clock.monotonic_ns()-started)/SECOND,
                      accepted=owner.accepted and ledger.failed is None and clock.monotonic_ns() < owner.deadline,
                      failure=failure, actual_object_processes=int(owner.process is not None), desktop_queries=0,
                      product_launches=0, control_services=0, screenshots=0, inputs=0, ready_for_live=False, qt_verified=False)
        write_once(root / 'final-result.json', json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'))
        if report['accepted'] and clock.monotonic_ns() >= owner.deadline:
            ledger.fail('object-final-persist', '最终回执持久化越过原5秒截止')
            report.update(accepted=False, failed_id=ledger.failed, token=ledger.token, not_before_ns=ledger.not_before_ns)
            write_once(root / 'final-result-rejected.json', json.dumps(report, ensure_ascii=False).encode('utf-8'))
            while clock.monotonic_ns() < ledger.not_before_ns: time.sleep(.1)
        events.close()
    return report


if __name__ == '__main__':
    require(len(sys.argv) == 2, '需要本轮完整UIA对象配置文件')
    report = run(decode_object(Path(sys.argv[1]).read_bytes()))
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['accepted'] else 1)
