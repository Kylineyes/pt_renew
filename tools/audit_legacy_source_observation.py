"""离线检查显式JSONL的单运行结构与配对；不采集目标、不判来源、不签GO。"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

# -I模式不自动加入脚本目录；只显式加载本工具固定同级依赖，不搜索工作目录。
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import legacy_source_api_buffers as api_buffers

MAX_BYTES = 4 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
MAX_EVENTS = 10000
UINT64_MAX = (1 << 64) - 1
COMMON = {'schema_version', 'run_id', 'seq', 'pid', 'creation_filetime', 'tid',
          'image_sha256', 'kind', 'utc_ns', 'monotonic_ns', 'data'}
KINDS = {'run_start', 'run_end', 'call_enter', 'call_return',
         'file_open', 'file_read', 'file_close'}
KINDS_V2 = KINDS | {'api_snapshot'}
SHELL_FOLDER_API = 'SHGetSpecialFolderPathA'
SHELL_FOLDER_SITES = {0xa56bbe: 0x1c, 0xa56bec: 0x1a}
CAPTURE_FIELDS = {'api', 'module_base', 'caller_rva', 'entry_rsp', 'return_address',
                  'hwnd', 'buffer_address', 'csidl', 'f_create', 'raw_bool',
                  'raw_hex', 'read_limit', 'read_complete', 'encoding'}
DOMAINS = {'directory_api', 'parse', 'file_io'}
LIMITATIONS = [
    '仅校验已提供事件及覆盖声明；seq连续或计数为零不能证明真实采集无遗漏',
    '不验证目录API参数和原缓冲、Property值、全部Host IO、实际令牌、路径隔离或采集器真实性',
    '不验证GET输出送达、CONFIG环境更新、目标实际退出或来源归因；完整性通过不构成执行批准',
]


class AuditError(ValueError):
    """带稳定代码的输入拒绝。"""
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def require(condition, code, detail):
    if not condition:
        raise AuditError(code, detail)


def integer(value, field, minimum=0, maximum=UINT64_MAX):
    require(type(value) is int and minimum <= value <= maximum,
            'invalid_integer', field + '必须是范围内的精确整数，拒绝布尔和浮点')
    return value


def text(value, field):
    require(isinstance(value, str) and 0 < len(value) <= 1024
            and value.strip() and not any(ord(c) < 32 or ord(c) == 127
                                        or 0xd800 <= ord(c) <= 0xdfff for c in value),
            'invalid_text', field + '必须是非空、有界且无控制字符的字符串')
    return value


def fields(value, expected):
    require(type(value) is dict and set(value) == set(expected),
            'invalid_fields', '字段集合不符，应为：' + ', '.join(sorted(expected)))


def filetime(value):
    if isinstance(value, str):
        require(re.fullmatch(r'[1-9][0-9]{0,19}', value) is not None,
                'invalid_filetime', '创建FILETIME须为无前导零的正十进制字符串或精确整数')
        value = int(value)
    return integer(value, 'creation_filetime', 1)


def coverage(data):
    fields(data, {'from', 'until', 'domains'})
    require(data['from'] == 'before_first_target_instruction'
            and data['until'] == 'process_exit', 'insufficient_coverage', '覆盖起止范围不足')
    domains = data['domains']
    require(type(domains) is list and all(type(x) is str for x in domains)
            and len(domains) == len(DOMAINS) and set(domains) == DOMAINS,
            'insufficient_coverage', '覆盖域须恰好包含目录API、解析和文件IO，且不得重复')


def outcome(data):
    require(type(data['success']) is bool, 'invalid_outcome', 'success须为JSON布尔')
    if data['success']:
        require(data['error'] is None, 'invalid_outcome', '成功事件的error须为null')
    else:
        integer(data['error'], 'error')


def _base(source):
    return {'schema_version': 1, 'integrity_passed': False, 'source_attribution': None,
            'execution_ready': False, 'input': source, 'identity': None, 'issues': [],
            'summary': {'events_checked': 0, 'counts': {}, 'pending_calls': [], 'open_ids': []},
            'limitations': list(LIMITATIONS)}


def _json_bytes(value):
    """解码器的bytes字段显式转为无损十六进制对象，不改原输入。"""
    if type(value) is bytes:
        return {'encoding': 'hex', 'hex': value.hex()}
    if type(value) is dict:
        return {key: _json_bytes(item) for key, item in value.items()}
    if type(value) is list:
        return [_json_bytes(item) for item in value]
    return value


def _decode_capture(capture):
    """仅核冻结capture字段并调用已有解码器，不补采集事实。"""
    fields(capture, CAPTURE_FIELDS)
    require(capture['api'] == SHELL_FOLDER_API, 'invalid_capture_api', 'capture的API名不符')
    base = integer(capture['module_base'], 'module_base', 1)
    caller = integer(capture['caller_rva'], 'caller_rva')
    require(caller in SHELL_FOLDER_SITES, 'invalid_call_site', '不支持该调用站点RVA')
    require(base + caller <= UINT64_MAX, 'address_overflow', 'module_base加RVA溢出')
    rsp = integer(capture['entry_rsp'], 'entry_rsp', 1)
    require(rsp + 8 <= UINT64_MAX, 'address_overflow', 'entry_rsp加8溢出')
    integer(capture['return_address'], 'return_address', 1)
    integer(capture['hwnd'], 'hwnd', 0, 0)
    buffer_address = integer(capture['buffer_address'], 'buffer_address', 1)
    csidl = integer(capture['csidl'], 'csidl', 0, (1 << 32) - 1)
    require(csidl == SHELL_FOLDER_SITES[caller], 'site_csidl_mismatch', '调用站点与CSIDL不对应')
    integer(capture['f_create'], 'f_create', 0, 0)
    integer(capture['raw_bool'], 'raw_bool', -(1 << 31), (1 << 31) - 1)
    limit = integer(capture['read_limit'], 'read_limit', 1, 0x104)
    require(buffer_address + limit <= UINT64_MAX, 'address_overflow', '缓冲地址加读取上限溢出')
    raw_hex = capture['raw_hex']
    require(type(raw_hex) is str and len(raw_hex) <= 520 and len(raw_hex) % 2 == 0
            and re.fullmatch(r'[0-9a-f]*', raw_hex) is not None,
            'invalid_raw_hex', 'raw_hex须为有界、偶数长度的小写十六进制原字节')
    raw = bytes.fromhex(raw_hex)
    require(len(raw) <= limit, 'capture_overread', '原字节长度超过声明读取上限')
    require(type(capture['read_complete']) is bool, 'invalid_read_complete', 'read_complete须为严格bool')
    try:
        decoded = api_buffers.decode_shell_folder(
            raw_bool=capture['raw_bool'], raw_bytes=raw, read_limit=limit,
            read_complete=capture['read_complete'], encoding=capture['encoding'])
    except ValueError as error:
        raise AuditError('invalid_capture_buffer', str(error)) from error
    return decoded


def _issue(report, code, detail, line=None):
    report['issues'].append({'line': line, 'code': code, 'detail': detail})


def _validate(events, source):
    report = _base(source)
    stacks, calls, opens, handles, used_opens = {}, {}, {}, {}, set()
    counts = Counter()
    identity = None
    start_coverage = None
    ended = False
    last_mono = None
    version = None
    for index, event in enumerate(events):
        try:
            require(not ended, 'after_end', '结束摘要后仍有事件')
            fields(event, COMMON)
            event_version = integer(event['schema_version'], 'schema_version', 1, 2)
            if version is None:
                version = event_version
                if version == 2:
                    report['schema_version'] = 2
                    report['api_snapshots'] = {}
                    report['limitations'][1] = (
                        'v2仅核提供的Shell32有界快照与调用绑定；不证实际采集、Property、windir、全部Host IO或隔离')
            require(event_version == version, 'mixed_schema_versions', '同一输入不能混用schema版本')
            integer(event['seq'], 'seq')
            require(event['seq'] == index, 'sequence_gap', 'seq必须从0开始连续，不能跳号、重复或重排')
            pid = integer(event['pid'], 'pid', 1, (1 << 32) - 1)
            tid = integer(event['tid'], 'tid', 1, (1 << 32) - 1)
            created = filetime(event['creation_filetime'])
            run = text(event['run_id'], 'run_id')
            image = event['image_sha256']
            require(isinstance(image, str) and re.fullmatch(r'[0-9a-f]{64}', image) is not None,
                    'invalid_image', '映像SHA须为64位小写十六进制')
            current = (run, pid, created, image)
            if identity is None:
                identity = current
                report['identity'] = {'run_id': run, 'pid': pid,
                                      'creation_filetime': str(created), 'image_sha256': image}
            require(current == identity, 'identity_changed', '单运行的run_id、PID、创建FILETIME或映像SHA改变')
            integer(event['utc_ns'], 'utc_ns')
            mono = integer(event['monotonic_ns'], 'monotonic_ns')
            require(last_mono is None or mono >= last_mono, 'clock_reversed', '单调时点倒退')
            last_mono = mono
            kind = event['kind']
            allowed_kinds = KINDS_V2 if version == 2 else KINDS
            require(type(kind) is str and kind in allowed_kinds, 'unknown_kind', '不支持的事件kind')
            data = event['data']
            require(type(data) is dict, 'invalid_fields', 'data须为对象')
            require(index != 0 or kind == 'run_start', 'missing_start', '首条须为启动摘要')
            stack = stacks.setdefault(tid, [])
            if kind in {'run_start', 'run_end'}:
                expected = {'coverage', 'lost_events', 'truncated_events'}
                if kind == 'run_end':
                    expected |= {'complete', 'event_count'}
                fields(data, expected)
                coverage(data['coverage'])
                integer(data['lost_events'], 'lost_events')
                integer(data['truncated_events'], 'truncated_events')
                require(data['lost_events'] == 0 and data['truncated_events'] == 0,
                        'collection_loss', '摘要声明了丢失或截断，不能通过')
                if kind == 'run_start':
                    require(index == 0, 'duplicate_start', '单运行只能有一个启动摘要')
                    start_coverage = data['coverage']
                else:
                    require(data['coverage'] == start_coverage, 'coverage_changed', '起止摘要覆盖声明不一致')
                    require(data['complete'] is True, 'incomplete_end', '结束摘要未声明完整')
                    integer(data['event_count'], 'event_count', 1, MAX_EVENTS)
                    require(data['event_count'] == index + 1, 'count_mismatch', 'event_count应含本条结束摘要')
                    ended = True
            elif kind == 'call_enter':
                fields(data, {'call_id', 'operation', 'name', 'phase', 'path'})
                call_id = text(data['call_id'], 'call_id')
                require(call_id not in calls, 'duplicate_call', 'call_id全运行不可复用')
                require(data['operation'] in ('api', 'parse'), 'invalid_operation', 'operation仅支持api或parse')
                text(data['name'], 'name')
                text(data['phase'], 'phase')
                if data['operation'] == 'parse':
                    text(data['path'], 'path')
                else:
                    require(data['path'] is None, 'invalid_path', 'api调用的path字段须为null，本版不解码缓冲')
                    if version == 2:
                        require(data['name'] == SHELL_FOLDER_API, 'unsupported_v2_api', 'v2仅支持约定的Shell32 API调用')
                calls[call_id] = {'tid': tid, 'data': data, 'returned': False, 'snapshot': None}
                stack.append(call_id)
            elif kind == 'api_snapshot':
                fields(data, {'call_id', 'capture'})
                call_id = text(data['call_id'], 'call_id')
                require(call_id in calls, 'orphan_snapshot', '快照没有对应的进入事件')
                call = calls[call_id]
                require(not call['returned'] and call['tid'] == tid and stack and stack[-1] == call_id
                        and call['data']['operation'] == 'api',
                        'snapshot_mismatch', '快照须绑定同TID栈顶且尚未返回的API调用')
                require(call['snapshot'] is None, 'duplicate_snapshot', '同一API调用只能有一条快照')
                decoded = _decode_capture(data['capture'])
                bound = {'line': index + 1, 'seq': event['seq'], 'tid': tid,
                         'capture': data['capture'], 'decoded': _json_bytes(decoded), 'accepted': False}
                report['api_snapshots'][call_id] = bound
                require(data['capture']['read_complete'], 'incomplete_snapshot', '快照读取不完整，即使已有NUL也不能通过')
                require(data['capture']['raw_bool'] == 0 or decoded['status'] != 'unknown',
                        'unknown_snapshot', 'API成功但缓冲解释未知，不能通过快照检查')
                call['snapshot'] = data['capture']
                bound['accepted'] = True
            elif kind == 'call_return':
                fields(data, {'call_id', 'result'})
                call_id = text(data['call_id'], 'call_id')
                integer(data['result'], 'result', -(1 << 63), UINT64_MAX)
                require(call_id in calls, 'orphan_return', '返回没有对应进入事件')
                call = calls[call_id]
                require(not call['returned'], 'duplicate_return', '同一调用重复返回')
                require(call['tid'] == tid and stack and stack[-1] == call_id,
                        'return_mismatch', '返回线程或嵌套顺序错配')
                if call['data']['operation'] == 'parse':
                    require(data['result'] in (0, 1), 'invalid_parse_result', 'parse返回须为原始AL的0或1')
                    require(not any(x['parse_call_id'] == call_id for x in opens.values()),
                            'parse_has_open_file', 'parse返回前仍有未成功关闭的文件')
                elif version == 2:
                    require(call['snapshot'] is not None, 'missing_snapshot', 'v2 API返回前缺少唯一原快照')
                    require(data['result'] == call['snapshot']['raw_bool'],
                            'snapshot_return_mismatch', '原返回result与快照raw_bool不一致')
                stack.pop()
                call['returned'] = True
            else:
                if kind == 'file_open':
                    fields(data, {'open_id', 'parse_call_id', 'path', 'success', 'handle', 'error'})
                    open_id = text(data['open_id'], 'open_id')
                    require(open_id not in used_opens, 'duplicate_open', '每次打开尝试必须有全新open_id')
                    parse_id = text(data['parse_call_id'], 'parse_call_id')
                    require(parse_id in stack and calls[parse_id]['data']['operation'] == 'parse',
                            'invalid_parse_link', '文件打开须关联本线程仍活动的parse调用')
                    text(data['path'], 'path')
                    outcome(data)
                    if data['success']:
                        handle = text(data['handle'], 'handle')
                        require(handle not in handles, 'handle_already_open', '活动句柄重复绑定，不能按路径合并')
                        opens[open_id] = {'parse_call_id': parse_id, 'tid': tid, 'handle': handle}
                        handles[handle] = open_id
                    else:
                        require(data['handle'] is None, 'failed_open_handle', '失败打开不得有有效handle')
                    used_opens.add(open_id)
                else:
                    expected = {'open_id', 'success', 'error'}
                    if kind == 'file_read':
                        expected |= {'parse_call_id', 'offset', 'requested', 'transferred'}
                    fields(data, expected)
                    open_id = text(data['open_id'], 'open_id')
                    require(open_id in opens, 'unknown_open', '读／关闭没有活动的成功打开')
                    opened = opens[open_id]
                    require(opened['tid'] == tid and opened['parse_call_id'] in stack,
                            'invalid_parse_link', 'v1文件操作须在原线程及所属parse生命周期内')
                    outcome(data)
                    if kind == 'file_read':
                        require(data['parse_call_id'] == opened['parse_call_id'],
                                'invalid_parse_link', '读事件的parse关联与打开不一致')
                        offset = integer(data['offset'], 'offset')
                        requested = integer(data['requested'], 'requested')
                        transferred = integer(data['transferred'], 'transferred')
                        require(transferred <= requested and offset + transferred <= UINT64_MAX,
                                'invalid_read_size', '实际读取超请求或偏移溢出')
                    elif data['success']:
                        del handles[opened['handle']]
                        del opens[open_id]
            counts[kind] += 1
            report['summary']['events_checked'] += 1
        except AuditError as error:
            _issue(report, error.code, str(error), index + 1)
            break
    if not events:
        _issue(report, 'empty_input', '没有任何事件')
    if not ended:
        _issue(report, 'missing_end', '未取得有效结束摘要')
    pending = [key for key, value in calls.items() if not value['returned']]
    if pending:
        _issue(report, 'unreturned_call', '存在未返回的调用')
    if opens:
        _issue(report, 'unclosed_file', '存在未成功关闭的文件')
    report['summary'].update(counts=dict(counts), pending_calls=pending, open_ids=list(opens))
    report['integrity_passed'] = not report['issues']
    return report


def _reject_number(value):
    raise ValueError('拒绝非整数JSON数值：' + value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('拒绝重复JSON键：' + key)
        result[key] = value
    return result


def _audit_raw(raw, source):
    if len(raw) > MAX_BYTES:
        report = _base(source)
        _issue(report, 'input_too_large', '输入超过有界字节数')
        return report
    lines = raw.split(b'\n')
    if lines[-1] == b'':
        lines.pop()
    if len(lines) > MAX_EVENTS:
        report = _base(source)
        _issue(report, 'too_many_events', '事件数量超过上限')
        return report
    events = []
    for index, line in enumerate(lines):
        try:
            require(len(line) <= MAX_LINE_BYTES, 'line_too_large', '单行超过字节上限')
            event = json.loads(line.decode('utf-8'), object_pairs_hook=_unique_object,
                               parse_float=_reject_number, parse_constant=_reject_number)
            events.append(event)
        except (UnicodeError, ValueError, RecursionError) as error:
            report = _base(source)
            _issue(report, getattr(error, 'code', 'invalid_json'), str(error), index + 1)
            return report
    return _validate(events, source)


def audit_jsonl(path):
    """只读调用者给出的一个文件；超限只摘要读取前缀，不冒称完整输入SHA。"""
    path = Path(path)
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    source = {'kind': 'jsonl', 'path': str(path), 'bytes_read': len(raw),
              'sha256': hashlib.sha256(raw).hexdigest(),
              'sha256_scope': 'read_prefix' if len(raw) > MAX_BYTES else 'full_input'}
    return _audit_raw(raw, source)


def audit_events(events):
    """内存接口接受单个JSON事件列表，摘要针对确定的UTF-8规范化序列。"""
    require(type(events) is list, 'invalid_events', '内存输入须为事件列表')
    require(len(events) <= MAX_EVENTS, 'too_many_events', '事件数量超过上限')
    try:
        raw = ('\n'.join(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False) for x in events) + ('\n' if events else '')).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError('内存输入不能序列化为受支持的JSONL：' + str(error)) from error
    source = {'kind': 'memory', 'bytes_read': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
              'sha256_scope': 'canonical_jsonl'}
    return _audit_raw(raw, source)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='唯一显式输入JSONL，不自动寻找其它材料')
    parser.add_argument('--output', type=Path, help='排他创建的新JSON报告，默认标准输出')
    args = parser.parse_args(argv)
    try:
        report = audit_jsonl(args.input)
        payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output is None:
            sys.stdout.write(payload)
        else:
            with args.output.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(payload)
    except (OSError, ValueError) as error:
        parser.exit(2, '错误：' + str(error) + '\n')
    return 0 if report['integrity_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
