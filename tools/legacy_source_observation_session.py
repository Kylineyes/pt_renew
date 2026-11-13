"""纯数据Shell32事件组装与失败封存；不连接进程、不读取本机时间或编码。"""
from contextlib import contextmanager
from copy import deepcopy

import audit_legacy_source_observation as audit
import legacy_source_call_capture as capture

IDENTITY_FIELDS = {'run_id', 'pid', 'creation_filetime', 'image_sha256'}
STAMP_FIELDS = {'tid', 'utc_ns', 'monotonic_ns'}
APPEND_KINDS = {'call_enter', 'call_return', 'file_open', 'file_read', 'file_close'}


class ObservationSessionError(ValueError):
    """session已封存或调用输入／配对不符合约定。"""


def _fields(value, expected):
    if type(value) is not dict or set(value) != expected:
        raise ObservationSessionError('字段须恰含：' + ', '.join(sorted(expected)))
    return deepcopy(value)


class ObservationSession:
    """单运行、串行调用的组装器；TID交错是输入数据，不创建线程或目标。"""

    def __init__(self, identity, *, start_at, coverage, lost_events, truncated_events, read_memory):
        self._identity = _fields(identity, IDENTITY_FIELDS)
        if not callable(read_memory):
            raise ObservationSessionError('read_memory必须由调用方显式提供')
        self._read_memory = read_memory
        self._events = []
        self._calls = {}
        self._stacks = {}
        self._diagnostics = []
        self._state = 'active'
        self._busy = False
        self._next_call = 1
        self._attempt = {}
        with self._operation('start'):
            self._emit('run_start', {'coverage': deepcopy(coverage), 'lost_events': lost_events,
                                    'truncated_events': truncated_events}, self._stamp(start_at))

    def _record_failure(self, code, detail, exception_type=None):
        self._state = 'failed'
        self._diagnostics.append({'code': code, 'detail': detail, 'exception_type': exception_type,
                                  'prefix_event_count': len(self._events),
                                  'attempt': deepcopy(self._attempt)})

    def _reject(self, code, detail, exception_type=None):
        self._record_failure(code, detail, exception_type)
        raise ObservationSessionError(detail)

    @contextmanager
    def _operation(self, stage):
        if self._state != 'active':
            self._reject('session_sealed', 'session已结束或失败封存，不能再次追加或结束')
        if self._busy:
            self._reject('reentrant_operation', '内存回调内不能重入修改session')
        self._busy = True
        self._attempt = {'stage': stage}
        try:
            yield
        except ObservationSessionError as error:
            if self._state != 'failed':
                self._reject('invalid_input', str(error), type(error).__name__)
            raise
        except Exception as error:
            self._reject(stage + '_failed', str(error), type(error).__name__)
        except BaseException as error:
            # 中断仍原样传播，但不允许调用方捕获后续接成成功session。
            self._record_failure(stage + '_interrupted', str(error), type(error).__name__)
            raise
        finally:
            self._busy = False

    def _stamp(self, at):
        at = _fields(at, STAMP_FIELDS)
        for name in STAMP_FIELDS:
            maximum = (1 << 32) - 1 if name == 'tid' else (1 << 64) - 1
            minimum = 1 if name == 'tid' else 0
            if type(at[name]) is not int or not minimum <= at[name] <= maximum:
                raise ObservationSessionError(name + '必须是范围内的精确整数，拒绝布尔和浮点')
        return at

    def _emit(self, kind, data, at, *, final=False):
        row = {'schema_version': 2, **deepcopy(self._identity), 'seq': len(self._events),
               **deepcopy(at), 'kind': kind, 'data': deepcopy(data)}
        candidate = [*self._events, row]
        # 不复制审计算法；未结束前仅容许可审的未返回调用和未关闭文件。
        checked = audit.audit_events(candidate)
        self._events = candidate
        allowed = set() if final else {'missing_end', 'unreturned_call', 'unclosed_file'}
        problems = [item for item in checked['issues'] if item['code'] not in allowed]
        if problems:
            self._reject('audit_rejected', problems[0]['code'] + '：' + problems[0]['detail'])
        return row

    def _matching(self, call_id, tid, operation):
        if type(call_id) is not str or call_id not in self._calls:
            self._reject('orphan_call', '没有该call_id的进入状态')
        call = self._calls[call_id]
        stack = self._stacks.get(tid, [])
        if call['returned'] or call['tid'] != tid or not stack or stack[-1] != call_id:
            self._reject('call_mismatch', '重复、跨线程或非栈顶返回，禁止读取缓冲')
        if call['operation'] != operation:
            self._reject('wrong_operation', '调用类型不符，禁止绕过API生产者')
        return call

    def begin_api(self, registers, *, module_base, caller_rva, encoding, read_limit, phase, at):
        """先保存进入事件，再调用真实提取组件的begin；不读返回缓冲。"""
        with self._operation('begin'):
            at = self._stamp(at)
            registers = deepcopy(registers)
            call_id = 'session-api-' + str(self._next_call)
            self._next_call += 1
            self._attempt.update(call_id=call_id, at=deepcopy(at))
            self._emit('call_enter', {'call_id': call_id, 'operation': 'api',
                                     'name': 'SHGetSpecialFolderPathA', 'phase': phase, 'path': None}, at)
            call = {'tid': at['tid'], 'operation': 'api', 'entry': None, 'returned': False}
            self._calls[call_id] = call
            self._stacks.setdefault(at['tid'], []).append(call_id)
            call['entry'] = capture.begin_shell_folder_call(
                registers, module_base=module_base, caller_rva=caller_rva, encoding=encoding,
                read_limit=read_limit, read_memory=self._read_memory)
            if self._state != 'active':
                raise ObservationSessionError('回调期间session已封存')
            return call_id

    def return_api(self, call_id, registers, *, snapshot_at, return_at):
        """先核ID／线程栈和两个显式时点，再finish并分别生成快照及返回事件。"""
        with self._operation('return'):
            snapshot_at, return_at = self._stamp(snapshot_at), self._stamp(return_at)
            self._attempt.update(call_id=call_id if type(call_id) is str else None,
                                 snapshot_at=deepcopy(snapshot_at), return_at=deepcopy(return_at))
            if snapshot_at['tid'] != return_at['tid']:
                self._reject('call_mismatch', '快照和返回的TID必须相同')
            call = self._matching(call_id, snapshot_at['tid'], 'api')
            if (snapshot_at['monotonic_ns'] < self._events[-1]['monotonic_ns']
                    or return_at['monotonic_ns'] < snapshot_at['monotonic_ns']):
                self._reject('invalid_return_time', '快照或返回时点倒退，禁止读取缓冲')
            result = capture.finish_shell_folder_call(
                call['entry'], deepcopy(registers), read_memory=self._read_memory)
            if self._state != 'active':
                raise ObservationSessionError('回调期间session已封存')
            self._emit('api_snapshot', {'call_id': call_id, 'capture': result}, snapshot_at)
            self._emit('call_return', {'call_id': call_id, 'result': result['raw_bool']}, return_at)
            self._stacks[snapshot_at['tid']].pop()
            call['returned'] = True
            return deepcopy(result)

    def append(self, kind, data, *, at):
        """仅追加原parse／file事件；API进入、快照和返回必须走生产者接口。"""
        with self._operation('append'):
            at = self._stamp(at)
            data = deepcopy(data)
            if type(kind) is not str or kind not in APPEND_KINDS or type(data) is not dict:
                self._reject('forbidden_event', '只允许原parse调用及file_open/read/close事件')
            if kind == 'call_enter' and data.get('operation') != 'parse':
                self._reject('forbidden_event', '不能从追加接口伪造API进入事件')
            call = None
            if kind == 'call_return':
                call = self._matching(data.get('call_id'), at['tid'], 'parse')
            self._emit(kind, data, at)
            if kind == 'call_enter':
                call_id = data['call_id']
                self._calls[call_id] = {'tid': at['tid'], 'operation': 'parse',
                                        'entry': None, 'returned': False}
                self._stacks.setdefault(at['tid'], []).append(call_id)
            elif kind == 'call_return':
                self._stacks[at['tid']].pop()
                call['returned'] = True

    def end(self, *, at, coverage, lost_events, truncated_events, complete):
        """明确结束声明；缺调用或声明不完整时返回失败封存报告，不补返回。"""
        with self._operation('end'):
            at = self._stamp(at)
            try:
                self._emit('run_end', {'coverage': deepcopy(coverage), 'lost_events': lost_events,
                                      'truncated_events': truncated_events, 'complete': complete,
                                      'event_count': len(self._events) + 1}, at, final=True)
            except ObservationSessionError:
                return self.report()
            self._state = 'ended'
            return self.report()

    def report(self):
        """独立副本含实际组装前缀及其审计；不是外部原始采集文件摘要。"""
        checked = audit.audit_events(deepcopy(self._events))
        return {'state': self._state, 'events': deepcopy(self._events), 'audit': checked,
                'diagnostics': deepcopy(self._diagnostics),
                'pending_calls': [{'call_id': key, 'tid': value['tid'],
                                   'operation': value['operation'], 'entry_ready': value['entry'] is not None}
                                  for key, value in self._calls.items() if not value['returned']],
                'integrity_passed': self._state == 'ended' and checked['integrity_passed'] and not self._diagnostics,
                'source_attribution': None, 'execution_ready': False,
                'digest_scope': '仅组装事件的canonical_jsonl，不是外部原始采集文件'}
