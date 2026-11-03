# 新增走线内部核心边界审查

2026-11-03，本轮对 `TrackPlacementSession`、`TrackPlacementController`、`BoardEditSession` 及现有测试进行了定向一致性审查。**在现有公开 API、不可变文档快照、同线程串行调用的使用条件下，未发现需要修改源码的可复现功能缺陷。** 本提交仅增加本报告，没有新增框架、修改产品行为或添加没有缺陷依据的回归测试；不存在“旧代码失败、修复后通过”的修复结论。

## 固定候选与范围

- 固定受审源码候选、起始 `HEAD` 与本轮核对的 `origin/dev`：`3fd6e5fa2b241ef8c61bf6ecd7b46c4839b34be6`。
- 工作分支：`fix/track-core-boundaries`；工作树：`review-track-core-boundaries`。报告提交后的应用源码仍与该固定候选一致，报告提交 SHA 由本轮完成回执及本机 `final-state.json` 记录。
- 先读 `AGENTS.md` 和 `docs/agent-handoff-20261103-pcb-check.md`；实际测试文件是 `tests/TrackPlacementTests.cpp`、`tests/TrackPlacementControllerTests.cpp`、`tests/EditingTests.cpp`，协调者已批准对应文件范围。
- 实际 Pi 会话为 `01a1a161-c684-75ff-8e81-5918e22bf0ce`，环境和会话前置记录均为 `deng/gpt-6.1-sol`、`high`，本会话工具成功执行；详见本机 `session.json`。
- 对 `TrackCreationTests.cpp`、`TrackPlacementUiTests.cpp` 及 MainWindow、BoardCanvas、writer、planner、能力门的相关路径仅阅读或运行已有测试，没有修改。

## 审查结果

| 边界 | 源码判断与行为证据 | 结论 |
| --- | --- | --- |
| 放置绑定与失效 | `TrackPlacementSession::checkContext` 同时核对文档指针、会话修订、文档 `workingRevision`、PCB 作用域及目标层可见性；失效执行完整取消。`confirmRechecksEveryContextBoundary`、`staleContextCancelsAtEveryEntry` 覆盖换文档、改修订、隐藏层、空文档及相同修订号的独立会话。 | 旧预览不能通过确认转交新上下文。 |
| 候选参数失败 | `begin` 在改成员前完成参数校验；`invalidBeginPreservesActivePreview` 明确覆盖候选文档不同且候选参数非法时仍保留原预览。非法坐标及零长度终点保留上一次有效预览。 | 这是既有失败保持契约，不能把它本身认作缺陷。 |
| 后端拒绝与重试 | Controller 先 `prepareRequest`，后同步调用 `addTrack`，只有成功才取消。`backendRefusalPreservesPreviewAndSavedRedoBranch` 在真实 200000 条走线容量限制下两次拒绝，核对文档、修订、预览、dirty、redo 和保存点，随后 redo 恢复 clean。 | 返回失败不会吞掉合法预览、截断重做分支或消耗新增身份。 |
| 预览与取消 | 放置预览只记录几何和上下文，不调用编辑后端；控制器 undo/redo 即使没有历史也先取消。已有测试核对预览、两阶段取消、重复取消及最终 Created 序号。 | 预览和取消不 dirty，不分配身份。 |
| Loaded 与 Created 身份 | reset 校验 Loaded 身份非零、来源行一致且不重复；Created 仅在 `record` 成功后递增。撤销/重做重放同一个身份；另起分支继续递增。`loadedIdentityUsesOriginalTagLines`、`addMoveDeleteUndoRedoRestoresIdentitiesAndOrder` 及非法身份数据行已实跑。 | 受审路径无身份复用、索引错位或原输入被改写的问题。 |
| 保存点与分支 | `dirty` 比较当前历史位置和有效保存位置；仅成功 `record` 后截断 redo，并作废被截断分支中的保存位置。`branchDoesNotReuseIdentitiesOrOldSavedPosition` 验证相同历史位置不能错误恢复已放弃的保存点。 | 历史位置和几何相同不被误当成保存成功。 |
| 返回 false 的原子性 | 参数/作用域/修订/容量检查在提交前完成；`apply` 对现有记录和身份进行校验后构造新工作文档。非法新增、非法位移、过期选择及后端容量拒绝均已有真实行为断言。 | 本轮实跑的返回 false 路径保留工作快照、修订、历史与保存点。 |
| 几何与原数据 | 公开新增/移动路径只产生有限、范围内的整数 mil；在该域内 QPointF 比较不会把相差 1 mil 的端点认成相同。工作副本保留原始字节、摘要、未编辑图元及未解释 extra。20 万条板图历史测试验证副本释放与原件保持。 | 未以篡改只读快照或修改私有成员制造缺陷。 |

### 失败 begin 与调用方通知的具体边界

Controller 没有订阅 BoardEditSession 的变化通知，`placement()` 也是只读状态查询。若另一个内部消费者直接改变编辑会话，再调用一个参数非法的 `begin`，旧放置状态可能继续保留，直到显式 `checkContext`、`setStart`、`previewEnd`、`commit` 或取消操作。现有 `staleContextCancelsAtEveryEntry` 的“每个入口”指其四个数据化入口，不包括 `begin` 和只读查询；本报告不扩大该测试名称的覆盖含义。

检查现有消费者后，没有发现上述状态滞后导致跨文档提交或产品预览未取消的可复现路径：

- MainWindow 在请求读取、同步读取、清空文档、发布编辑结果及相关交互切换时主动取消放置；移动/删除成功后通过 `publishWorkingDocument` 发布并取消。
- BoardCanvas 换文档先发 `interactionCancelRequested`；改图层发 `trackPlacementContextChanged`，MainWindow 据活动放置的目标层重新核对。隐藏非目标层保留活动放置，隐藏目标层取消。
- MainWindow 每次取点、更新终点和提交前再检查画布/会话文档一致性、读取状态、模态状态、库预览状态及目标层可见性。Controller 提交还会再检查文档与修订。
- 已有 `modalLayerDocumentAndMeasurementCancel` 与 `staleRevisionFailsBeforeCommit` 本轮 offscreen 实跑通过，前者覆盖目标层、换图、模态、测量、读取失败/成功、面板隐藏、关闭等取消路径，后者模拟另一消费者改修订后拒绝旧预览提交。

因此本轮不改变 Session 的失败保持契约，也不单凭状态查询可能滞后来增加控制器行为。后续新增消费者须沿用显式通知/上下文检查约定；若修改这些消费者，应按具体实际路径重新验收。

## 本轮构建与测试

独立构建目录为 `build/track-core-boundary-review-debug`，使用 `scripts/Enter-QtEnv.ps1` 启用既有 Qt 6.12.0、MSVC x64 14.51.36231 和 Ninja。配置及所列目标构建均同步等待完成，真实退出码 0；没有使用其他工作树的 build 或 dist。

```powershell
& ./scripts/Enter-QtEnv.ps1
cmake -S . -B build/track-core-boundary-review-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON
cmake --build build/track-core-boundary-review-debug --target pt-track-placement-tests pt-track-placement-controller-tests pt-editing-tests pt-track-creation-tests -j 4
$env:QT_QPA_PLATFORM = 'offscreen'
ctest --test-dir build/track-core-boundary-review-debug -R '^pt-(track-placement|track-placement-controller|track-creation)-tests$' --output-on-failure
& ./build/track-core-boundary-review-debug/pt-editing-tests.exe historyRestoresOrderPropertiesAndOriginal rejectsForeignScopeAndStaleIdentifiers invalidOrZeroMovementHasNoHistory boundaryCoordinatesAndLargeBoardHistory -o .local-analysis/track-core-boundary-review/editing-core-tests.txt,txt
cmake --build build/track-core-boundary-review-debug --target pt-track-placement-ui-tests -j 4
& ./build/track-core-boundary-review-debug/pt-track-placement-ui-tests.exe previewCancelAndFailuresDoNotAllocateIdentityOrHistory modalLayerDocumentAndMeasurementCancel backendFailurePreservesPreviewAndHistory staleRevisionFailsBeforeCommit -o .local-analysis/track-core-boundary-review/consumer-offscreen-tests.txt,txt
```

| 实际执行 | 结果 | 同步真实等待 |
| --- | --- | --- |
| CTest 三组核心测试 | 3/3 组通过；TrackPlacement 11、Controller 25、TrackCreation 28 passed | 退出 0，外层计时 0.8598324 秒；CTest 自报 0.74 秒 |
| EditingTests 四个核心槽 | 12 passed，含 7 个无效位移数据行及初始化/清理 | 退出 0，外层计时 0.9726023 秒；QtTest 自报 467 ms |
| TrackPlacementUiTests 四个通知/失败槽，offscreen | 6 passed，含初始化/清理 | 退出 0，外层计时 1.4996648 秒；QtTest 自报 1106 ms |

以上 QtTest 数量均含各进程初始化和清理，不是独立功能数量；合计 82 passed、0 failed、0 skipped。offscreen 原日志保留 Qt 字体目录缺失及 `propagateSizeHints` 插件提示；未下载字体或改运行环境来消除提示。

没有源码修改或新增失败复现，因此未扩跑全套、Release 或重复历史 GUI 验收。消费者四槽仅用于核对本次审查的通知与拒绝路径，不代表整套 UI 测试通过。

## 仍未验证及保留的产品边界

- 未启动桌面 Qt、未截图、未进行真实键鼠或原生另存为对话框验收；offscreen 模态/焦点行为不等于真实 Windows 桌面通过。菜单/F3/旧式 P→T、文本焦点、真实窗口切换及图层预览应由父协调者另行安排指定 Pi 验收。
- 本轮失败原子性结论针对公开 API 返回 false 的受审路径，不覆盖内存分配异常、非串行调用或绕过只读快照约束的外部写入。
- 原 AUTOTRAX 默认字段、兼容保存重开及 NETDEF 排序证据不属于本轮；未推定默认编码。`trackPlacementUserEntryAvailable()` 仍 false，默认 writer 仍拒绝 Created，planner 仍拒绝有 NETDEF 的新增；本轮没有改这些边界。
- `markSaved` 只记录同步调用时的当前位置。本轮未引入异步保存接口或扩大其完成回调契约；真实文件发布是否成功仍由已有保存消费者负责判断。

## 本机证据与交付

证据根为本工作树 `.local-analysis/track-core-boundary-review/`，属于忽略目录，不随 Git 报告提交。包含 `session.json`、配置/构建日志、`baseline-core-tests.log`、三个核心测试原始结果副本、`baseline-core-wait.json`、`editing-core-tests.txt`、`editing-core-wait.json`、`consumer-offscreen-tests.txt`、`consumer-offscreen-wait.json` 以及最终源码/可执行文件/证据摘要和提交状态 `final-state.json`。命令输出中的本地时间为 UTC+08:00，Pi 会话前置记录使用 UTC。

仅将本报告提交到工作分支；没有合并 dev、推送远端、操作 main/tag 或修改旧证据。本轮交付结果是有实跑证据的无修复审查，由父协调者决定后续集成和真实 GUI 验收安排。
