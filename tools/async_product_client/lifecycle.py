"""同客户端原Popen账本；保存创建后未知身份，退出不改写动作失败。"""
from __future__ import annotations

from .core import positive, require


class ProcessRegistry:
    def __init__(self, ledger, *, required_roles=('product', 'service', 'client', 'supervisor')):
        require(required_roles and len(set(required_roles)) == len(required_roles), '进程角色清单无效')
        self.ledger, self.required_roles = ledger, tuple(required_roles)
        self.entries = {}
        self.gaps = {}
        self.sealed = False

    def created(self, key, process, *, role, parent=None):
        require(not self.sealed and isinstance(key, str) and key and key not in self.entries
                and process is not None and positive(process.pid)
                and all(row['process'] is not process for row in self.entries.values()),
                '原Popen账本已封存、键重复或创建对象无效')
        require(parent is None or parent in self.entries, '原Popen父角色不存在')
        # 先保存对象再发审计，emit失败不能导致所有权丢失。
        self.entries[key] = dict(process=process, role=role, parent=parent, pid=process.pid,
                                 identity=None, exit_code=None, accepted_exit=False)
        self.ledger.event('registry_created', key=key, role=role, parent=parent, pid=process.pid, original_popen=True)

    def identified(self, key, process, identity):
        require(not self.sealed and key in self.entries, '未知或封存原进程')
        row = self.entries[key]
        require(row['process'] is process and row['identity'] is None and process.pid == row['pid']
                and identity.get('pid') == row['pid'] and positive(identity.get('birth'))
                and positive(identity.get('handle')) and identity.get('original_handle') is True
                and isinstance(identity.get('image'), str) and identity['image'], '原Popen身份无效或重复')
        row['identity'] = dict(identity)
        self.ledger.event('registry_identified', key=key, identity=row['identity'])

    def exited(self, key, process, code):
        require(key in self.entries, '退出对象不在原账本')
        row = self.entries[key]
        require(row['process'] is process and process.pid == row['pid'] and type(code) is int
                and process.returncode == code, '原Popen退出码/对象不一致')
        require(row['exit_code'] is None or row['exit_code'] == code, '原退出码被改写')
        row['exit_code'] = code
        row['accepted_exit'] = row['identity'] is not None and code == 0
        self.ledger.event('registry_exit', key=key, original_popen=True, exit_code=code,
                          identity_verified=row['identity'] is not None)

    def discovered(self, key, *, pid, birth, parent):
        require(not self.sealed and positive(pid) and positive(birth) and key not in self.gaps,
                '子孙缺口身份无效或重复')
        # 不以随后打开的查询句柄冒充原Popen；未知子孙永久保留缺口。
        self.gaps[key] = dict(pid=pid, birth=birth, parent=parent,
                              reason='已发现子孙缺少本创建者保存的原Popen退出见证')
        self.ledger.event('registry_discovered_gap', key=key, **self.gaps[key])

    def poll(self):
        for key, row in self.entries.items():
            if row['exit_code'] is None:
                code = row['process'].poll()
                if code is not None: self.exited(key, row['process'], code)
        return self.report()

    def report(self):
        rows = {key: {k: v for k, v in row.items() if k != 'process'} for key, row in self.entries.items()}
        missing = sorted(set(self.required_roles) - {row['role'] for row in rows.values()})
        lifecycle = bool(rows) and not missing and not self.gaps and all(row['accepted_exit'] for row in rows.values())
        return dict(entries=rows, discovered_gaps=dict(self.gaps), missing_roles=missing,
                    lifecycle_complete=lifecycle, action_succeeded=lifecycle and self.ledger.failed is None,
                    failed_id=self.ledger.failed, token=self.ledger.token, not_before_ns=self.ledger.not_before_ns,
                    gui_verified=False, unknown_short_lived_descendants_covered=False)

    def seal(self):
        require(not self.sealed, '原进程账本已封存')
        self.poll()
        self.sealed = True
        row = self.report()
        self.ledger.event('registry_sealed', report=row)
        return row
