# 独立异步实验构建：NET与铜层结果门闩

本轮已在独立分支`experiment/async-result-barrier`实现同步门闩、事件记录、控制器及自动验证，代码提交`98a4321`。基于固定编辑提交`b0e5ac7761f13690b5310bbc913ab7bfd2691d08`，不是稳定0.10.0产品更新。实验源码不得整体合入dev；稳定发布包和原固定0.11.0候选没有替换。

**Debug/Release实验构建各12/12组CTest通过，普通关闭开关的Release相关回归3/3通过。尚未进行真实桌面或鼠标键盘验收。** 自动验证使用`offscreen`及程序接口，不把这些结果记作固定候选的现场通过。用户要求在操作鼠标键盘前先告知；本轮未操控桌面。

## 实现与证明边界

CMake开关`PT_ENABLE_ASYNC_EXPERIMENT`默认为OFF，当前实验实现仅支持Windows。关闭时不编译`src/experiment/AsyncExperiment.cpp`，应用没有实验命令行选项。打开时版本显示`0.11.0-async-experiment`，主窗口带“独立异步实验构建”标识；启动时还需显式传入新证据目录、任务类型与持有者PID才启用门闩。实验能力不会自动读取旧审批、旧inbox或旧生命周期ID。

| 位置 | 行为 |
| --- | --- |
| `src/experiment/AsyncExperiment.h/.cpp` | 每个运行有新UUID，异步请求有独立ID。只阻塞配置类型的第一个目标请求，可跳过指定数量；后续不再次布置门闩 |
| `src/io/LegacyNetlistReader.cpp` | 在实际Qt工作线程成功打开NET、通过大小检查后，`file.read`前进入门闩。原生文件框及GUI线程不参与等待 |
| `src/geometry/CopperConnectivity.cpp` | 实际算法入口、10000ms预算计时之前等待。描述为“已进入算法任务并受控暂停”，不是持续进行几何计算 |
| `src/ui/NetlistBrowser.cpp` | 记录请求身份、工作函数返回、完成回调的接受/丢弃决定。原NET代次条件和铜层代次/文档/网表身份条件保留原样 |
| `src/ui/MainWindow.cpp` | 工作文档发布后记录修订、走线数量、dirty及当前NET摘要。该事件本身不证明鼠标键盘操作或截图内容 |
| `tools/async_barrier_control.py` | 可持有新实验候选直到退出，或按单个请求清单发送release/cancel命名事件。发送前核对PID与创建时间，不发送鼠标键盘 |

应用进程独占JSONL记录并串行化事件序号、`QElapsedTimer`纳秒和墙钟毫秒；事件中的单调时间属于该运行的应用时钟域。后台进入与GUI完成回调还记录不同的线程ID。所有实际控制事件使用`Local\\PtRenewAsync-运行UUID-请求ID-动作`命名，不提供通用产品命令通道。

等待以最多1秒的本地块检查持有者进程、取消事件和释放事件，默认看门狗60秒。持有者退出、控制端取消、等待失败、日志/门闩初始化失败或超时都使实验记为`aborted`并结束等待；原工作函数和原产品淘汰逻辑仍继续执行，不能借“实验失败”让产品强制丢弃结果。取消及持有者退出优先于同时置位的release。门闩若误在GUI线程调用，直接中止实验，不阻塞界面。

`callback-accepted/discarded`记录原完成回调的判断决定；截图和最终状态仍需独立核对。`worker-returned`记录原读取/计算函数已返回到异步包装层，之后由QFuture交付GUI回调，不代表操作系统线程已经退出。看门狗从`gate-ready`开始，不保证整个算法或产品在60秒内退出。日志不能落盘的运行没有有效证据，不得记通过。

## 自动验证

新增`tests/AsyncExperimentTests.cpp`使用小型合成板、NET_A及不同名称/摘要的NET_B。测试不显示真实窗口，不发送系统级输入；事件循环心跳确认工作线程等待时主线程可继续处理事件，删除通过现有`MainWindow::deleteSelectedTrack`接口执行。

- NET正向对照接受B；竞争实验在B实际读取前完成删除，再释放，验证B成功读取但原代次判断丢弃B，A身份和摘要保留。
- 铜层正向对照显示旧板内支持模型已连接；竞争实验在算法入口等待期间删除关键走线，验证新修订发布后，旧修订计算返回仍被原判断丢弃，旧结论不恢复。
- 两类均检查`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`，其中正向对照没有`document-published`。
- release通过实际Python控制器跨进程发送；错误进程创建时间清单被拒绝，后台未被提前释放。
- 另验证跳过与单次使用、看门狗、取消、持有者退出、GUI线程误入、拒绝覆盖旧证据和无效配置。中止仍可沿原路径得到成功NET，但事件明确标记实验无效。

| 配置 | 结果 | 含义 |
| --- | --- | --- |
| 实验Debug | 12/12组CTest通过 | 新实验QtTest12 passed，含初始化/清理；已有产品测试一并通过 |
| 实验Release | 12/12组CTest通过 | 同上；不是额外12种产品能力 |
| 普通Release，开关OFF | 编辑/NET/铜层3/3组通过 | 普通构建不编译实验实现，命令行拒绝实验参数 |
| CLI与交付核验 | 通过 | 实验/普通版本区分、配置拒绝、8条正向/竞争事件时间线、原材料摘要及新部署摘要 |

每配置的新增QtTest12项已包含在12组CTest中，Debug和Release重复相同测试，不应简单加总为独立覆盖项。首次实验测试11项通过后增加了GUI线程拒绝与实际Python释放/身份拒绝检查；最终统计采用12项。字体目录缺失的offscreen警告不影响本次非像素断言；未用这些测试判断实际字体渲染。

## 工作区、部署和本机证据

工作区为`C:/Users/rikideng/orca/workspaces/pt_renew/experiment-async-result-barrier`，构建目录`build/async-debug`、`build/async-release`和`build/plain-release`。证据位于[本轮证据目录](C:/Users/rikideng/orca/workspaces/pt_renew/experiment-async-result-barrier/.local-analysis/async-experiment/)，Git不包含构建、部署、截图或输入副本。

独立部署为`.local-analysis/async-experiment/release-candidate/pt-renew.exe`：

- 实验EXE SHA-256：`782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`，624128字节；部署22文件，全部摘要见`deployment-manifest.json`。
- 原固定候选EXE仍为`dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8`；稳定dist EXE仍为`726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1`。
- `verification-summary.json`保存两个配置共8条对照/竞争时间线、CLI结果，以及固定部署23、源输入7、既有隔离输入7、稳定dist22文件与上轮基线相同的集合/大小/SHA核验。
- `debug-final-traces/`与`release-traces/`保留逐例事件、请求清单及合成输入摘要；`gui-inputs/`是从Release测试保留副本复制的新现场材料，含`board.pcb`、`a.net`、`b.net`，其摘要另存`gui-inputs-manifest.json`。
- `ctest-debug.log`、`ctest-release.log`、`ctest-plain.log`及构建日志保存原件；PowerShell5的Tee日志为UTF-16，交付检查按BOM识别，不改写原日志。

本轮没有子代理派发，没有创建或复用已结算Task/Dispatch。没有真实桌面候选或控制客户端需要收尾；CLI与自动测试进程退出均由父进程等待回执确认。没有新增真实GUI截图、正常GUI关闭或固定候选通过记录。

## 构建和后续现场使用

```powershell
& ./scripts/Enter-QtEnv.ps1
cmake -S . -B build/async-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -DPT_ENABLE_ASYNC_EXPERIMENT=ON
cmake --build build/async-debug
$env:QT_QPA_PLATFORM='offscreen'
ctest --test-dir build/async-debug --output-on-failure
```

现场前先告知用户需要鼠标键盘并协调使用桌面的时段。核对新候选/部署/输入/驱动摘要、PID/创建时间/HWND、实际Pi模型和新执行身份；真实窗口移除offscreen及SDK插件环境。所有截图验收使用指定`deng/gpt-6.1-sol high`，不能复用旧批准文件或旧Task/Dispatch。

以下命令由专用终端运行，会启动并持有**真实GUI**；本轮未执行该命令。路径按实际工作区填写，外层目录必须全新：

```powershell
python tools/async_barrier_control.py launch --candidate C:/Users/rikideng/orca/workspaces/pt_renew/experiment-async-result-barrier/.local-analysis/async-experiment/release-candidate/pt-renew.exe --directory C:/Users/rikideng/orca/workspaces/pt_renew/experiment-async-result-barrier/.local-analysis/async-experiment/gui-net-01 --kind net --skip 1 -- C:/Users/rikideng/orca/workspaces/pt_renew/experiment-async-result-barrier/.local-analysis/async-experiment/gui-inputs/board.pcb --netlist C:/Users/rikideng/orca/workspaces/pt_renew/experiment-async-result-barrier/.local-analysis/async-experiment/gui-inputs/a.net
```

`--skip 1`只跳过A通过异步入口的首次加载；下一次GUI打开B才布置NET门闩。控制器会清理自身子进程的Qt/SDK变量并限制PATH，使用独立部署的qwindows。A加载、B文件框关闭、`gate-ready`及进程归属都必须实际观察；若顺序不符，停止该次，不根据skip数猜测已经命中正确请求。

确认真实画布删除、新修订/几何/dirty截图后，另一个终端针对`events/request-N.json`中的实际N释放：

```powershell
python tools/async_barrier_control.py release --directory C:/Users/rikideng/orca/workspaces/pt_renew/experiment-async-result-barrier/.local-analysis/async-experiment/gui-net-01/events --request 2
```

控制器成功回执只证明事件置位，必须再核对应用`gate-released`、`worker-returned`、`callback-discarded`及最终截图。铜层改用`--kind copper --skip 0`，先完成A加载再点击分析；不要把命令行加载NET的次数当作铜分析次数。

每类现场最多一次正向对照与一次竞争，遵守上一轮实验协议的60秒门闩上限及180秒争用静默。争用时本地cancel或持有者退出可防后台遗留，但该次记aborted，不增加预算或续写成通过。正常关闭实验应用后持有者记录退出码，核对输入/候选摘要、事件和截图索引。

下一步为通知用户后进行该独立候选真实GUI验收。本轮自动验证不改变NET/铜层固定候选现场未覆盖、900000mil极端属性未覆盖、系统会话结束未覆盖或原字形`runtime_verified=false`。稳定产品继续0.10.0，main仅用户操作。
