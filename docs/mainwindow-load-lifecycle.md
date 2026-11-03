# 主窗后台载入生命周期修复

本次从 `0655a004a2772e3624f73eb9cb3341ded0f7ef74` 的独立分支 `fix/mainwindow-load-lifecycle` 开发，仅修改主窗及既有 EditingTests。普通新增走线能力门、显式新增编码和保存路径保持现有边界。

## 触发与结果

| 触发 | 旧行为 | 修复行为 |
| --- | --- | --- |
| 后台读取尚未完成时调用同步 `inspectFile`，同步成功或失败 | 只增加代次，旧 `m_loading` 继续禁止打开和保存，直到已作废任务完成 | 同步探测接管代次并立即解除旧载入状态，成功显示新板，失败保留原修改和历史 |
| 后台读取期间关闭板图或窗口，随后取消放弃确认 | 待载入结果已经作废，但打开、另存仍被旧读取锁住 | 关闭意图即放弃待载入结果；取消只保留当前工作副本，打开和保存立即恢复 |
| 关闭作废旧任务后立即同步打开板图，再开始新后台读取；旧任务先完成 | 旧 finished 在代次检查前设置 `m_loading=false` 并启用动作，能解锁仍在读取的新任务 | 旧任务只回收自身，不能修改新任务的 loading、动作或文档，也不发载入完成信号 |
| 成功读取等待放弃确认期间再次调用同步探测，即使第二次探测失败 | 外层确认返回后仍应用旧结果，覆盖应保留的工作副本 | 确认返回后核对代次；作废结果不换图、不发过期完成信号 |
| 放弃确认框内重入成功探测、关闭板图或关闭窗口 | 递归弹出第二个放弃确认框，外层随后仍可能换图 | 同一时刻只接受一个放弃确认；重入操作拒绝，并使外层代次失效 |
| 确认框的嵌套事件循环期间通过主窗 API 再编辑当前副本 | 原确认可以丢掉确认显示之后的新修改 | 核对修订及文档快照，旧确认失效，保留新编辑及历史 |

`closeEvent` 与“文件 → 关闭”在取消时仍使原载入代次失效，这是保留旧行为中“关闭意图放弃载入”的语义；本次让 loading 和动作立即与该语义一致。取消关闭不清空工作副本、撤销重做或保存元数据。

## 最小实现

- `invalidatePendingLoad()` 统一增加代次、解除 loading，并刷新打开与编辑动作；用于同步探测、关闭／清空和现有会话关闭确认路径。
- finished 回调先判断代次，再修改 loading 和动作；完成应用之后再次判断代次，避免确认框嵌套事件循环让旧请求继续发送 `boardLoadFinished`。
- `applyReadResult` 接收请求的代次，在进入和确认返回之后核对，失败仍保留原工作副本。
- `confirmDiscard` 使用私有重入标记，返回时核对代次、修订及文档指针；不引入公开可变 loader 或生产测试开关。

后台读取仍只读取输入，不直接修改编辑会话。旧后台任务不强制终止，结束后由原 watcher 回收；其回调以主窗作为 Qt 连接上下文。

## 实际异步回归方法

`EditingTests.cpp` 中 `ReadQueue` 在单独测试进程内把全局 Qt 线程池临时限制为一个线程，先运行 `QSemaphore` 闸门任务，再调用真实 `requestOpenFile`。测试退出时释放全部闸门、等待线程池并恢复线程数，即使断言失败也不会留下被阻塞任务。

跨代测试顺序为：第一道闸门 → 旧真实读取 → 第二道闸门 → 新真实读取。测试先释放第一道闸门，确认第二道闸门已进入，并等待旧 watcher 实际销毁，此时新读取确定尚未执行；随后验证打开、另存、放置仍被新任务禁止。最后释放第二道闸门，验证只有新任务发成功信号并打开正确路径。测试没有按文件大小或固定延时猜测读取完成顺序。

模态测试通过 `QTimer` 在真实 `QMessageBox::exec()` 嵌套事件循环中发起主窗操作，并实际点击外层“放弃更改”。旧实现如递归弹框，会主动取消内层以便稳定报告失败，而非挂住自动化。

已评估并保留读取期间的既有移动／删除／Undo／Redo 策略：这些操作仍可编辑当前副本，另存和新增放置等待有效读取结束。闸门测试实际进行移动、删除、Undo、Redo，再让失败读取结束，验证文档指针、修订、dirty、redo 分支及后续保存动作不变；既有测试同时覆盖读取后拒绝放弃时保留历史。

## 构建与证据

环境：Pi 实际原记录为 `deng/gpt-6.1-sol`、`high`，会话 `01a19f99-6515-720c-9e03-ee00ab05152e`，已确认成功工具回执；Qt 6.12.0、MSVC x64，使用 `scripts/Enter-QtEnv.ps1`。本树隔离构建目录为 `build/debug`，全部自动化设置 `QT_QPA_PLATFORM=offscreen`。

本机证据根目录为 `.local-analysis/mainwindow-load-lifecycle/`，不提交构建或证据目录。

| 验证 | 结果 | 原日志及退出记录 |
| --- | --- | --- |
| 旧源码运行新增功能回归 | 3 通过、9 失败，进程 exit 9，耗时 1.296 秒 | `old-regression-3.txt`、`old-exit-3.json`；配置及构建 exit 0 |
| 修复后同一专项 | 12 通过、0 失败，exit 0 | `fixed-regression.txt`、`fixed-exit.json` |
| Debug 四组相关 CTest | editing、mainwindow-created-save、track-placement-ui、writing，4/4 通过，10.55 秒，exit 0 | `related-ctest.log`、`related-exit.json` |
| 只移除 finished 前置代次检查的敏感性实验 | 跨代测试在旧回调错误启用打开动作处失败，exit 1 | `mutation-regression.txt`、`mutation-exit.json` |
| 恢复前置代次检查并重新链接四个相关程序 | 同一跨代测试通过，exit 0 | `restored-build.log`、`restored-regression.txt`、`restored-exit.json` |
| 最后增加确认期间再次编辑的行，重建并跑完整 EditingTests | 34 通过、0 失败，6.851 秒，build/test exit 0 | `final-build.log`、`final-editing.txt`、`final-exit.json` |

四组 CTest 当时各组 QtTest 项数（包含初始化／清理）：Editing 33，MainWindowCreatedSave 31，TrackPlacementUi 13，Writing 40；最后仅增加 Editing 的确认期间编辑行，完整 Editing 变为 34。其余三组没有再作无关重复运行。

首轮测试编译因 `findChild<QFutureWatcher<T>*>` 缺少模板类本身的 `Q_OBJECT` 而失败，保留 `build-old.log`／`old-exit.json`；随后改用带元对象的 `QFutureWatcherBase`。中间版本用 finished 信号作观察点在模态嵌套中出现等待观察不稳，保留 `old-regression.txt`／`old-exit-2.json`；最终以 watcher 的 `destroyed` 信号证明回调已完整返回，旧实现产生稳定功能断言失败。此后功能回归未把编译错误或观察错误当作旧源码缺陷证据。

本任务只执行 offscreen 自动化，未抢占原软件现场桌面，不能据此宣称真实 GUI 已通过。最终候选的真实窗口交互以及全量 Debug／Release 由协调者统一验收；原 AUTOTRAX 格式兼容和产品新增开放不属于本次结论。
