# 新增走线输出与界面接入的并行集成

本轮在 `fbda57f` 之后并行推进原软件菜单与单线取证、显式参数输出、走线画布工具接入，由协调者审阅、集成与统一验收。新增输出和界面内部路径已接通；**原 AUTOTRAX 默认字段尚未核定，产品新增命令仍未开放**。原件只读、仅另存全新文件和生产输出未实现等既有边界保持。

## 实现结果

- [显式参数输出](track-explicit-output.md)：`LegacyPcbWriter::prepareWithCreated`／`saveAsWithCreated` 复用插入预检和显式编码器，支持 Created 段与旧段移动／删除混合输出。六／七字段、换行和可选附加整数均由调用方明确提供，不产生默认值；原 `prepare`／`saveAs` 仍拒绝 Created。
- [主窗与画布接入](track-placement-ui.md)：现有控制器已有真实 MainWindow 消费者，画布绘制临时几何，整数面板明确列出实际坐标、宽度和层后提交。取消、换图、隐藏层、模态边界和撤销重做共用状态管理。`trackPlacementUserEntryAvailable()` 保持 `false`，菜单／F3／旧式 P→T 不允许用户新增。
- [菜单离线校准](native-menu-calibration.md)：旧 File 点击已经包含裁剪原点，不能把误选简单归为漏加偏移。旧小写 f／i 与 Shift 修饰字母走不同输入通道，需以新现场核对；DOS 鼠标误选原因尚未确定。

写出校验包括 200000 条实际语法记录容量、64 MiB 整体大小、冻结原字节与摘要、载入／新建身份顺序、输出重解析和重载行身份、旧对象／NETDEF 语义及同目录临时文件不覆盖发布。存在新增时仍拒绝尾部或交错 NETDEF。七字段附加值是显式输出投影，不反写到 Created 内存对象，也不解释其电气含义。

新建提交后沿用 `publishWorkingDocument()`，清除旧选择、测量和铜分析，重新映射外部 NET；迟到回调继续受已有文档身份和代次规则约束。没有重新实现历史、布局、状态、预检或编码器。

## 分工与提交

| 任务 | 独立分支／文件所有权 | 实现提交 |
| --- | --- | --- |
| 显式新增输出 | `feat/track-explicit-output`；writer 两文件、新专项和独立说明 | `ac6329b` |
| 主窗、画布及命令入口准备 | `feat/track-placement-ui`；MainWindow、BoardCanvas、CommandCatalog、新专项和独立说明 | `57e8971` |
| 既有交互回归修复 | 同一 UI worker；MainWindow／BoardCanvas、自有专项和说明 | `4c3b764` |
| 原软件取证 | `verify/native-menu-calibration`；两个独立报告与本机证据 | 见最终现场报告 |
| 正式构建注册和跨模块验收 | 协调者 `feat/track-native-integration`；根 CMake、工作流专项、集成说明 | `4518e1c` 及后续集成提交 |

各实现 worker 没有修改共享 CMake 或其他 worker 的文件。协调者核对交集后使用有中文说明的 no-ff 合并；产品源码冻结在 `bd885c148b48e40edbfee6d30582a59d86732ff6`。所有 Pi worker 的实际 model、thinking、assistant 和成功工具事件均独立核验为 `deng/gpt-6.1-sol high`；原软件与产品真实窗口仅由同一时刻的一名指定模型 worker 操作。未派发新的纯二进制逆向任务。

本轮 Run 为 `run_98316b665261`。原软件监督附加首次因原会话忙在 agent_readiness 超时，未注入任务；待真实会话结束该轮后，以同一 Task／会话重试为 `ctx_001465cfe3a8`，没有启动重复操作者。writer 为 `ctx_22083073e23c`；UI 实现为 `ctx_bfda0b57884d`；同一 UI 会话后续真实窗口验收为 `ctx_fb7a2a49bf0f`。生命周期结算和释放事实见本机证据，不把 Pi 闲置或 external 终端 retained 当作 OS 进程已退出。

## 构建与回归

正式 Debug／Release 配置、全量构建和 CTest 最终真实 wait 返回均为 **0**，CTest 各 **22/22**。Debug CTest **227.04 秒**，Release **31.86 秒**。新增 writer 专项包含真实大记录数与 64 MiB 边界，正式预算为 300 秒；不是用截断日志或超时中断来判断通过。

| 新增正式专项 | QtTest 通过项，含初始化／清理 | 行为 |
| --- | --- | --- |
| `TrackCreatedWritingTests` | 67 | 真实 writer、显式编码、容量／字节边界、混合编辑、语义／身份、防覆盖与失败清理 |
| `TrackPlacementUiTests` | 13 | 入口能力门、预览／整数面板、上下文与统一取消、Created 编辑、文本焦点和旧交互保护 |
| `TrackCreatedWorkflowTests` | 5 | 控制器与主窗实际提交、取消下一段、显式保存、保存点、撤销重做、重开身份与原输入字节保持 |

跨模块测试不把合成附加值当作原软件默认值。直接显式 writer 成功不自动标记 MainWindow 保存点；未开放的产品另存路径仍拒绝新增。核心工作流只有收到真实文件发布成功后才调用 `markSaved()`，验证保存后撤销／重做及截断分支的 dirty 语义。重开输出成为新载入来源，走线身份按输出行重新建立。

首轮集成 Debug 为 **20/22**，真实 CTest 返回 **8**，没有隐藏失败：

1. 打开另存框前无条件取消全部交互，清掉旧选择，使“文件框期间修改修订应阻止陈旧保存”的旧测试无法执行移动。
2. BoardCanvas 在空闲状态也消费 Esc，阻止 LIB 预览无选择时向对话框传播 Esc 并关闭。

两项修复分别改为模态／文件边界仅取消临时走线，以及只在活动走线／测量时由画布消费 Esc。旧 Writing／Library 测试没有修改；worker 先复现具体用例失败，再验证 Writing 40、Library 26、UI 13 项通过。协调者合入后重跑完整 Debug，并首次运行完整 Release，两配置均 22/22。UI 最早专项曾发现 dock 析构回调访问已销毁成员，已在成员销毁前解除相应连接；失败日志也保留。

## 真实窗口与原软件边界

真实 GUI 和原软件生成样例单独记录，不以 offscreen 回归代替。

原软件首个计划时段为北京时间 11:25–11:40。实际只取得基线截图，尚未启动 DOSBox：辅助请求脚本的 PowerShell 内联 JSON 丢引号，并提前创建空请求文件，导致驱动本地解析失败。没有 App／Click／Shortcut／Type 或目标启动；驱动按既定两分钟静默收尾，保留原创建者真实退出回执。这是请求写入错误，不是公共控制门拒绝，也不是 AUTOTRAX 菜单或保存失败。修复先解析临时文件再原子发布，需离线验证后另报新现场时段。

后续真实现场结果以专门报告为准。界面现场首槽 12:16–12:31 取得诊断预览及取消不 dirty 的原图，关闭请求晚于截止；第二槽 12:33–13:03 取得诊断真实新增提交，图元数由 2 变 3、dirty 为 true 且预览清空，但撤销快捷键因窗口未获焦点被控制接口拒绝，恢复焦点重试晚于截止。两次原 owner 均实际 `forcedDeadlineTermination=true`、wait 返回 1，不能写成正常退出或完整 GUI 通过。后续继续同一 Pi 会话，先压缩上下文，再按原 API 的 `--restore-window` 提示核对焦点。诊断运行输入是独立合成副本，不改用户原件。

第三槽沿用同一 Pi 会话，经上下文压缩后继续。诊断窗口已实际验证整数输入、预览、新增提交和编辑菜单撤销／重做：撤销为 2 图元 clean，重做为 3 图元 dirty，均有指定模型实际读图。关闭确认框选择放弃后，原创建者记录 `waitReturn=0`、`forcedDeadlineTermination=false`。点击关闭后的 RPC 曾因目标已退出返回 `app_not_found`，以原持有 Popen 的真实 wait 记录确认退出，不将该竞态误写成仍存活或控制失败。

同槽普通产品原图确认“放置走线(T)（未实现）”禁用且标有 F3；选择已有自由走线，删除后为 1 图元 dirty，编辑菜单撤销后恢复 2 图元 clean，随后正常关闭且原 Popen wait 为 0。F3 被本机电脑控制接口以 `Unsupported key: F3` 拒绝；恢复焦点后的 Ctrl+Z 请求虽成功返回，现场画面未变化，改用菜单完成历史命令。P 文本输入还受 IME 预编辑影响。上述真实快捷键送达、完整文本焦点、隐藏目标层及原生另存框未在本轮全面通过；对应 QtTest 通过不替代这些真实窗口缺口。详细结果见[真实窗口报告](track-placement-live-verification.md)。

原软件随后按 13:35–14:05 新时段取得一个真实 DOSBox 进程，但窗口捕获与精确物理矩形屏幕图均为不可辨黑底白线；物理图与同一时刻窗口图摘要一致，不能仅归因 Orca 捕获。只操作宿主 Capture 菜单、Take screenshot 和正常关闭，客体截图目录没有产物；未确认 SYN1、空板或计数，未向客体发送 Return／Shift+I／编辑／保存，也没有生成 `FTNEW.PCB`。启动 owner 首次因 `-conf` 被自身参数解析拒绝，修正后才创建目标，该失败与软件运行失败分别记录。目标 PID 9716 由原 owner 63316 持有 Popen，05:55:07Z 真实 wait0，未强制终止；5 张现场图均有指定模型成功 image 回执。单 Return 启动转换建议处理时目标已经关闭，未执行，也未为建议重启。本轮完整单线 Task 按 failed 结算，详见[原软件现场报告](native-ft-created-roundtrip.md)。

没有“确认空板 → 原软件新建单线 → 全新保存 → 原软件重开”的完整证据前，不开放默认编码或产品新增入口。诊断程序通过显式 API 显示内部工具，只能证明对应界面行为，不能证明正式产品菜单已可新增或原软件兼容。

## 本机证据

相对当前协调工作树：

- `.local-analysis/track-native-wave/`：自包含任务 spec、模型原事件核验、两配置配置／构建／CTest 日志与原创建者逐步 wait 回执、最终集成和结算记录。首轮失败为 `checks-debug-1.*`，修复后 Debug 为 `checks-debug-2.*`，Release 为 `checks-release-1.*`。
- `../feat-track-explicit-output/.local-analysis/track-explicit-output/`：writer 原会话、独立专项 harness、初次失败与最终两配置退出记录。
- `../feat-track-placement-ui/.local-analysis/track-placement-ui/`：UI 实现原会话、析构／菜单 Esc 首轮失败、专项与既有回归最终记录。
- `../feat-track-placement-ui/.local-analysis/track-placement-live/`：集成源码冻结、两项旧回归修前／修后回执、诊断及真实窗口证据。
- `../verify-native-menu-calibration/.local-analysis/native-menu-calibration/`、`native-ft-created-roundtrip/`：离线原图审计、原软件现场各轮独立输入与驱动证据。

原安装、运行副本、截图、原 RPC、大板样例、构建和会话不提交。未操作 main、创建 tag 或发布。
