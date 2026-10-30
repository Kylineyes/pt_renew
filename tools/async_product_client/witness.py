"""跨创建者原Popen见证交换；每份子报告由父保存的原对象退出记录约束。"""
from __future__ import annotations

import json

from .core import digest, positive, require
from .events import decode_object


def identity_key(row):
    require(isinstance(row, dict) and positive(row.get('pid')) and positive(row.get('birth'))
            and positive(row.get('handle')) and row.get('original_handle') is True
            and isinstance(row.get('image'), str) and bool(row['image']), '跨创建者原进程身份不完整')
    return row['pid'], row['birth'], row['image'].casefold()


def pack(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def audit_relay(raw, *, context, expected_identity, expected_role, seen=None):
    """调用方必须由父原Popen绑定expected身份；报告文件本身不能成为该来源证明。"""
    row = decode_object(raw)
    require(row.get('schema_version') == 1 and row.get('context') == context
            and row.get('role') == expected_role and identity_key(row.get('self')) == identity_key(expected_identity),
            '跨创建者报告上下文/角色/父原Popen身份不符')
    seen = set() if seen is None else seen
    key = identity_key(row['self'])
    require(key not in seen, '跨创建者报告环路/重复PID及birth')
    seen.add(key)
    local = row.get('local')
    require(isinstance(local, dict) and local.get('sealed') is True
            and not local.get('discovered_gaps') and not local.get('missing_roles')
            and local.get('lifecycle_complete') is True and local.get('action_succeeded') is True
            and local.get('failed_id') is None and local.get('gui_verified') is False
            and local.get('unknown_short_lived_descendants_covered') is False, '本创建者原退出账本不完整或已有失败')
    entries, relays = local.get('entries'), row.get('children')
    require(isinstance(entries, dict) and isinstance(relays, dict) and set(relays) <= set(entries), '子报告未对应本创建者账本键')
    roles = {expected_role}
    for name, entry in entries.items():
        require(entry.get('identity') is not None and identity_key(entry['identity'])[0] == entry.get('pid')
                and type(entry.get('exit_code')) is int and entry['exit_code'] == 0
                and entry.get('accepted_exit') is True, '子进程缺少父原Popen身份/退出0')
        role = entry.get('role')
        require(role in ('product', 'probe', 'service', 'client', 'supervisor'), '未知进程角色')
        require(entry.get('parent') is None or entry['parent'] in entries, '本地原Popen父键不在账本')
        ancestors, parent = {name}, entry.get('parent')
        while parent is not None:
            require(parent in entries and parent not in ancestors, '本地原Popen父键形成环路')
            ancestors.add(parent); parent = entries[parent].get('parent')
        roles.add(role)
        if role in ('service', 'client', 'supervisor'):
            require(name in relays, '服务/客户端/监督器缺少其创建者账本报告')
        if name in relays:
            child = relays[name]
            require(set(child) == {'sha256', 'report'} and isinstance(child['report'], str), '子报告协议不符')
            child_raw = child['report'].encode('utf-8')
            require(digest(child_raw) == child['sha256'], '子报告原字节摘要不符')
            audited = audit_relay(child_raw, context=context, expected_identity=entry['identity'], expected_role=role, seen=seen)
            roles.update(audited['roles'])
        else:
            child_key = identity_key(entry['identity'])
            require(child_key not in seen, '原Popen出现在多个见证节点')
            seen.add(child_key)
    return dict(roles=sorted(roles), identities=len(seen), report_sha256=digest(raw), gui_verified=False,
                unknown_short_lived_descendants_covered=False)


class CreatorRelay:
    """在本创建者退出前封存局部原Popen账本，交给持有本创建者原Popen的上层。"""

    def __init__(self, ledger, registry, *, self_identity, role):
        require(registry.ledger is ledger and role in ('service', 'client', 'supervisor'), '见证relay组件/角色不符')
        identity_key(self_identity)
        self.ledger, self.registry = ledger, registry
        self.self_identity, self.role = dict(self_identity), role
        self.children = {}
        self.used = False

    def accept_child(self, key, raw):
        require(not self.used and key not in self.children and key in self.registry.entries, '子见证报告重复或账本键未知')
        entry = self.registry.entries[key]
        code = entry['process'].poll()
        require(type(code) is int and code == 0, '子报告必须等本创建者保存的原Popen退出0')
        self.registry.exited(key, entry['process'], code)
        require(entry['identity'] is not None, '父账本缺少原创建身份，不能用子报告补作身份')
        context = dict(task_id=self.ledger.context.task_id, dispatch_id=self.ledger.context.dispatch_id,
                       run_id=self.ledger.context.run_id, session_id=self.ledger.context.session_id,
                       provider=self.ledger.context.provider, model=self.ledger.context.model, thinking=self.ledger.context.thinking)
        audit_relay(raw, context=context, expected_identity=entry['identity'], expected_role=entry['role'])
        self.children[key] = dict(sha256=digest(raw), report=raw.decode('utf-8'))
        self.ledger.event('child_relay_accepted', key=key, report_sha256=digest(raw), original_popen=True)

    def seal(self):
        require(not self.used, '创建者报告已封存')
        self.used = True
        local = self.registry.seal()
        local['sealed'] = True
        from dataclasses import asdict
        row = dict(schema_version=1, context=asdict(self.ledger.context), role=self.role,
                   self=self.self_identity, local=local, children=dict(self.children))
        raw = pack(row)
        # 原账本失败也可供诊断保存；验证器必须明确拒绝，不能包装成成功。
        self.ledger.event('creator_relay_sealed', role=self.role, report_sha256=digest(raw),
                          local_complete=local['lifecycle_complete'], action_succeeded=local['action_succeeded'])
        return raw


class RootWitness:
    """最外层已有原Popen的终态审计；不启动进程、不从PID接管、不自行给GUI通过。"""

    def __init__(self, *, context, process, identity, role='supervisor'):
        from dataclasses import asdict
        require(process is not None and process.pid == identity_key(identity)[0] and process.poll() is None,
                '根见证必须在仍存活时绑定创建者保存的原Popen')
        self.context, self.process, self.identity, self.role = asdict(context), process, dict(identity), role
        self.used = False

    def finish(self, raw):
        require(not self.used, '根见证终态机会已经消费')
        self.used = True
        code = self.process.poll()
        require(self.process.pid == self.identity['pid'] and type(code) is int and code == 0
                and self.process.returncode == code, '最外层原Popen尚未退出0或身份改变')
        result = audit_relay(raw, context=self.context, expected_identity=self.identity, expected_role=self.role)
        require({'supervisor', 'client', 'service', 'product'} <= set(result['roles']), '整条见证链仍缺必需角色')
        return dict(result, original_root_popen_exit=code, all_disclosed_processes_exit0=True,
                    lifecycle_complete=True, ready_for_live=False, gui_verified=False)
