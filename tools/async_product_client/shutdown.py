"""任意初始化/运行阶段的收尾清单；本地观察不解除失败，不强杀未知进程。"""
from __future__ import annotations

from pathlib import Path

from .core import SECOND, require


class ShutdownCoordinator:
    def __init__(self, ledger, owner, *, creator=None, probe=None, registry=None, session=None, connection=None):
        self.ledger, self.owner = ledger, owner
        self.creator, self.probe, self.registry = creator, probe, registry
        self.session, self.connection = session, connection
        self.errors = []
        self.service_stop_used = False

    def stop_probes(self):
        """仅发布本地停止标记；在途COM仍可未知，不将父等待超时当作已经停止。"""
        if self.probe is None: return
        for child in self.probe.children:
            if child['process'] is not None and child['exit_code'] is None:
                path = Path(child['folder']) / 'stop-requested'
                if not path.exists():
                    with path.open('xb') as output: output.write(b'normal-shutdown\n')
                child['stop_requested'] = True

    def fail(self, ident, error):
        try: self.ledger.fail(ident, type(error).__name__ + ': ' + str(error))
        finally: self.stop_probes()

    def poll(self):
        """120秒期间也只做原Popen本地poll及落盘，不发native/截图/输入请求。"""
        probes = self.probe.reap() if self.probe is not None else []
        process = self.owner.process or (self.creator.process if self.creator is not None else None)
        code = process.poll() if process is not None else None
        if process is not None and code is not None and self.creator is not None:
            self.creator.observe_exit()
        local = self.registry.poll() if self.registry is not None else None
        blocked = any(row['exit_code'] is None for row in probes)
        now = self.ledger.clock.monotonic_ns()
        if now >= self.ledger.cleanup_deadline_ns:
            action = 'deadline-exhausted'
        elif now < self.ledger.not_before_ns:
            action = 'wait-original-cooldown'
        elif process is None:
            action = 'stop-service' if self.connection is not None else 'publish-local-report'
        elif code is not None:
            action = 'stop-service' if self.connection is not None else 'publish-local-report'
        elif blocked or self.probe is not None and self.probe.failed:
            action = 'preserve-unknown-probe'
        elif self.owner.identity is None or self.owner.process_identity is None or self.session is None:
            action = 'preserve-unbound-product'
        elif (self.session.stage in ('file-open', 'file-active')
              or self.session.command is not None and self.session.command.command == 'netlistOpen'
              and self.session.command.used and self.ledger.gate_trigger_ns is None and self.session.stage != 'cancelled'):
            action = 'read-and-cancel-file-dialog'
        else:
            action = 'explicit-product-close'
        identity = self.owner.process_identity or (getattr(self.creator, 'identity', None) if self.creator is not None else None)
        identity_known = (process is None and not self.owner.launch_used
                          or process is not None and identity is not None and identity.get('pid') == process.pid
                          and identity.get('original_handle') is True)
        lifecycle = (identity_known and not blocked and (process is None or type(code) is int and code == 0)
                     and (local is None or local['lifecycle_complete']))
        return dict(next_action=action, original_product_exit=code, probes=probes, registry=local,
                    lifecycle_complete=lifecycle, action_succeeded=lifecycle and self.ledger.failed is None,
                    failed_id=self.ledger.failed, token=self.ledger.token, not_before_ns=self.ledger.not_before_ns,
                    cleanup_deadline_ns=self.ledger.cleanup_deadline_ns, errors=list(self.errors),
                    ready_for_live=False, gui_verified=False)

    async def stop_service(self):
        """唯一正常EOF；产品及已发现探针先有原退出证明，保留原40秒服务余量。"""
        require(not self.service_stop_used and self.connection is not None, '服务停止机会已消费或没有本轮连接')
        report = self.poll()
        require(report['next_action'] == 'stop-service' and all(row['exit_code'] == 0 for row in report['probes'])
                and self.ledger.clock.monotonic_ns() + 40 * SECOND < self.ledger.cleanup_deadline_ns,
                '产品/探针未正常退出、120秒未满或原服务收尾余量不足')
        self.service_stop_used = True
        return await self.connection.close()
