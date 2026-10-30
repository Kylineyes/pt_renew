"""生产产品组件装配；所有创建对象持续留在同一客户端，默认禁用。"""
from __future__ import annotations

from pathlib import Path

from .batch import BatchProductNative
from .core import require
from .discovery import ProductMainDiscovery
from .events import ApplicationJournal
from .process import OwnedProductProcess
from .probe import BoundedUiaProbe
from .product import ProductIO, ProductOwner, WindowPolicy
from .review import ReviewGate
from .session import ProductSession
from .shutdown import ShutdownCoordinator
from .store import ReviewStore
from .transport import McpProductTransport


class ProductBootstrap:
    def __init__(self, runtime, connection, evidence_root, *, enabled=False):
        require(connection.runtime is runtime and runtime.relay is not None and runtime.relay.role == 'client',
                '产品必须由同一持续客户端及其原服务连接创建')
        self.runtime, self.connection, self.ledger = runtime, connection, runtime.ledger
        self.root, self.enabled = Path(evidence_root).resolve(), enabled is True
        self.owner = ProductOwner(self.ledger)
        self.creator = self.probe = self.discovery = self.transport = self.session = None
        self.used = False
        self.shutdown = ShutdownCoordinator(self.ledger, self.owner, registry=runtime.registry, connection=connection)

    async def start(self, ident, parent, **configuration):
        try:
            return await self._start(ident, parent, **configuration)
        except BaseException:
            self.shutdown.stop_probes()
            raise

    async def _start(self, ident, parent, *, kind, deployment, manifest, board, board_sha256, a, b, environment,
                    interpreter, interpreter_sha256, package_root, package_files, module_root, module_files,
                    verifier, validate, diagnostic_deadline_ns, revision=2, discovery_api=None, python_environment=None):
        with self.ledger.operation(ident, parent, deadline_ns=diagnostic_deadline_ns):
            require(self.enabled and not self.used and self.connection.initialized,
                    '产品装配禁用、机会已消费或原MCP服务未初始化')
            self.used = True
            self.ledger.diagnostic_deadline_ns = min(self.ledger.diagnostic_deadline_ns, diagnostic_deadline_ns)
            self.root.mkdir(parents=True, exist_ok=False)
            self.creator = OwnedProductProcess(self.ledger, kind=kind, experiment_directory=self.root / 'application',
                                               board_copy=board, evidence_root=self.root / 'product', enabled=True,
                                               handle_api=self.runtime.handles, registry=self.runtime.registry, initial_net=a)
            self.shutdown.creator = self.creator
            a.verify(); b.verify()
            self.owner.launch(deployment=deployment, manifest=manifest,
                              inputs={str(Path(board).resolve()): board_sha256, a.path: a.sha256, b.path: b.sha256},
                              environment=environment, factory=self.creator, inspect_created=self.creator.inspect_created)
            self.probe = BoundedUiaProbe(self.ledger, self.owner, self.creator, interpreter=interpreter,
                                         interpreter_sha256=interpreter_sha256, package_root=package_root,
                                         package_files=package_files, module_root=module_root, module_files=module_files,
                                         evidence_root=self.root / 'probes', deadline_ns=self.ledger.cleanup_deadline_ns,
                                         enabled=True, handle_api=self.runtime.handles, registry=self.runtime.registry,
                                         python_environment=python_environment)
            self.shutdown.probe = self.probe
            policy = WindowPolicy(Path(board).name)
            self.discovery = ProductMainDiscovery(self.ledger, self.owner, self.creator, policy,
                                                   uia=self.probe, api=discovery_api, enabled=True)
            await self.discovery.run(loaded=True)
            native = BatchProductNative(self.ledger, self.owner, self.creator, self.probe, enabled=True)
            self.transport = McpProductTransport(self.ledger, self.connection, self.root / 'mcp', enabled=True, validate=validate)
            io = ProductIO(self.ledger, self.owner, policy, native=native, transport=self.transport,
                           snapshot=self.transport.snapshot)
            store = ReviewStore(self.root / 'reviews')
            reviews = ReviewGate(self.ledger, self.owner.identity, verifier, publish=store.request, publish_ack=store.ack)
            journal = ApplicationJournal(self.ledger, self.owner, self.creator, kind=kind,
                                         current_identity=self.runtime.handles.current_identity)
            self.session = ProductSession(self.ledger, io, reviews, journal, a=a, b=b,
                                           board_sha256=board_sha256, revision=revision,
                                           diagnostic_deadline_ns=diagnostic_deadline_ns, enabled=True)
            self.shutdown.session = self.session
        return self.session
