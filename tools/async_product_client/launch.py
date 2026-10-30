"""具体材料完整后唯一启动兼容性链；默认禁用，不生成批准或现场Task。"""
from __future__ import annotations

from .core import SECOND, require
from .runtime import CreatorRuntime, FrozenProgram
from .supervisor_driver import authorize_child, await_original_exit


class CompatibilityLaunch:
    def __init__(self, ledger, evidence_root, *, enabled=False):
        self.ledger, self.enabled = ledger, enabled is True
        self.runtime = CreatorRuntime(ledger, evidence_root, enabled=enabled)
        self.used = False
        self.witness = None

    def start(self, ident, parent, *, supervisor_program, configuration):
        deadline = min(self.ledger.diagnostic_deadline_ns, self.ledger.clock.monotonic_ns() + 35 * SECOND)
        with self.ledger.operation(ident, parent, deadline_ns=deadline):
            require(self.enabled and not self.used and not self.runtime.root.exists() and type(supervisor_program) is FrozenProgram
                    and supervisor_program.entry == 'async_product_client/supervisor_driver.py', '兼容性启动未启用、已消费或入口不符')
            # 在创建监督器/任何握手进程之前核对本轮具体材料及指定Pi会话。
            client = authorize_child(self.ledger, self.runtime.root / 'supervisor/client', configuration)
            require(supervisor_program.interpreter == client.interpreter
                    and supervisor_program.interpreter_sha256 == client.interpreter_sha256
                    and supervisor_program.root == client.root and dict(supervisor_program.files) == dict(client.files)
                    and supervisor_program.python_environment == client.python_environment,
                    '监督器不能使用不同源码/解释器/依赖')
            self.used = True
            self.runtime.spawn('supervisor', role='supervisor', program=supervisor_program, configuration=configuration)
            self.witness = self.runtime.root_witness('supervisor')
        return self.runtime.children['supervisor']['identity']

    async def finish(self):
        require(self.witness is not None, '兼容性根原Popen尚未绑定')
        await await_original_exit(self.runtime, 'supervisor')
        child = self.runtime.children['supervisor']
        from .core import digest
        from .events import decode_object
        raw = (child['folder'] / 'creator-report.json').read_bytes()
        receipt = decode_object((child['folder'] / 'creator-report-receipt.json').read_bytes())
        require(receipt == dict(sha256=digest(raw), launch_sha256=child['launch_sha256']), '根报告回执摘要不符')
        return self.witness.finish(raw)
