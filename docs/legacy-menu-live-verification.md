# verification-35：菜单、工作文件名与启动日志现场验证

本轮直接操作取得了新的运行证据：AUTOTRAX 1.57 启动页、主菜单、Information 菜单、Status 状态页均已截图；状态页显示工作文件名 `C21.PCB`、`Strings=1`。同轮 DOSBox 日志记录指定配置加载、PT 执行及 MNU、KEY、C21 文件打开请求。**字形独立运行对照仍未完成，`runtime_verified=false`，产品保持 0.9.0。**

这将前序“菜单是否响应、当前工作文件名是否可见”的未知缩小为现场事实；不证明所有输入图元完整入模，也没有取得文字对象属性。样例内有 4 条 `FT` 参考走线记录，Status 却显示 `Tracks=0`，差异原因仍未知。

基线为 `origin/dev=0f91ece`，开发分支 `research/direct-startup-verification`。用户已授权代理直接截图和操作桌面。本轮只修改研究文档；原程序、配置、截图、运行日志与客户端均留在忽略目录，不提交原软件材料。

## 场景、日志与身份

证据目录为 `C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/verification-35/`。下文文件名均相对于该目录。完整输入清单、动作和返回值由 `verification-summary.json` 索引。

从 verification-34 的已核对方案创建全新无 `TRAXEDIT.DFT` 副本，配置仅替换捕获目录、日志目录与 C/D 隔离挂载路径；保留 `output=opengl`、`machine=vgaonly`、`core=normal`、`cycles=fixed 10000` 和 `pt C21.PCB` 启动序列。日志使用 `[log] logfile`，开启 `exec/files/vga/int10/gui=normal`。没有更改本机安装或用户配置，没有更换后端来解释前序黑屏。

客户端使用唯一 Windows-MCP stdio 连接，宿主 Python 隐藏控制台启动。启动目标前通过同一连接查询 ControlStatus，使用本地 `subprocess.Popen` 启动本轮隔离目标，stdout/stderr 各自保存，不使用会丢弃标准流的 MCP App 启动路径。

| 项目 | 实际证据 |
| --- | --- |
| DOSBox-X | `2026.10.01 Commit b6abbd5`，SDL2 64 位；映像 SHA-256 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832` |
| 本轮目标 | PID 47704，父 PID 5772，为本轮客户端；SDL 窗口 HWND 1904154，session 3 |
| 完整窗口标题 | `DOSBox-X 2026.10.01: PT - 10000 cycles/ms` |
| 配置来源 | `dosbox-stderr.log` 第 2 行明确记录 `CONFIG: Loaded config file` 指向本轮绝对路径，第 3 行记录本轮隔离 `pt` 工作目录 |
| 实际后端信息 | 日志记录 `OpenGL Version : 4.6.0 NVIDIA 560.94`；本轮确实取得启动页，不由此推导 verification-33 黑屏根因 |
| 保留日志 | `dosbox-startup.log` 7556 字节，`dosbox-stderr.log` 8605 字节，`dosbox-stdout.log` 0 字节；空 stdout 不代表无输出，启动与文件访问记录在前两者中 |

日志记录了本轮指定配置成功加载，未观察到其他配置的加载行；不能据此证明所有默认搜索和覆盖实现。版本、工作目录、配置路径、日志打开和 PT 执行是本轮实际观测，不再只是启动前计划。

## 已实际核对的阶段

每次桌面动作前查询 ControlStatus；每次变更后再次查询并截图。键盘动作前后均保存只读 Win32 前景 HWND/PID 观测，步骤 4 至 13 的相关键盘调用前后都属于本轮 PID 47704。没有将 `use_ui_tree=false` 的空窗口元数据解释为焦点丢失。

| 步骤 | 动作与可见结果 | 主要证据 |
| --- | --- | --- |
| 1 | `ControlStatus=ready`，完整 UI 快照与原生前景都指向 Orca，建立桌面基线 | `step-001-initial.json`、`step-001-initial-00.png` |
| 2–3 | 启动一次隔离 DOSBox；启动后即时截图早于目标显示，随后新完整快照确认 AUTOTRAX 1.57 启动页及 `VGA 640x480` | `step-002-launch.json`、`step-003-startup-00.png`、对应原生窗口记录 |
| 4 | 单独 Enter 关闭启动页，画面出现灰底红色 A 与白色十字；日志新增 `C21.PCB` 打开请求 | `step-004-dismiss-startup-post-00.png`；`dosbox-startup.log` 第 129–130 行 |
| 5 | 再单独 Enter，AUTOTRAX 主菜单实际出现 | `step-005-main-menu-post-00.png` |
| 6–11 | 字母输入未立即进入 Information；截图出现输入法候选条。单个 Esc 取消候选，再用 Ctrl+Space 切换当前输入状态，出现 ASCII 指示；普通 `i` 仍无可辨菜单变化 | `step-008-information-uppercase-post-00.png`、`step-009-cancel-ime-composition-post-00.png`、`step-010-ime-toggle-post-00.png`、`step-011-information-ascii-post-00.png` |
| 12 | 在上述 ASCII 状态发送 `Shift+I`，实际进入 INFORMATION 子菜单 | `step-012-information-key-event-post-00.png` |
| 13 | 单独 `Shift+S`，实际进入 STATUS；读取工作文件名与计数 | `step-013-status-post-00.png`、`status-crop-4x.png` |

原始截图保存工具返回的整屏画面。`*-crop*.png` 仅从整屏图固定裁剪并用最近邻放大，便于阅读；它们不增加原图分辨率，不替代原截图，也不能用于字形端点拟合。

### Status 读数与载入边界

| 可见字段 | 现场读数 |
| --- | --- |
| Work File Name | `C21.PCB` |
| Library | `TRAXSTD.LIB` |
| Current Path | `C:\PT` |
| Arcs / Components / Fills / Holes / Pads | 均为 0 |
| Strings | 1 |
| Tracks / Vias | 均为 0 |

同轮日志中的文件打开请求与状态页工作文件名、文字计数及红色 A 画面相互支持。文件名经静态路径核对是去目录后的名称与扩展名，不能单独证明完整来源路径。本轮 C/D 只挂载已核对的新隔离副本，但完整图元读取仍须另外验证。

`C21.PCB` 本地记录统计为 `FS=1、FT=4`。`Strings=1` 与单文字记录一致；`Tracks=0` 与四条参考走线记录不一致。参考标记在本轮无 DFT 画面也未出现。尚未定位这是读取、筛选、模型构建还是统计路径的问题，不能仅以文件名和 A 轮廓宣布 C21 全部内容完整载入。

## 字母输入通道的现场限制

本机 Windows-MCP 0.8.8 的 `desktop/service.py:988–1000` 将单字符 Shortcut 直接拼入 SendKeys 文本；其 `uia/core.py` 的 SendKeys 分支将普通字符交给 Unicode 输入，而修饰键下匹配字符会走虚拟键事件路径。只读源码与本轮观察一起说明，工具报告 `Pressed i` 不等于 DOS 环境已经收到等价物理键事件。

本轮先观察到输入法候选，再取消候选并切换当前窗口输入状态；之后普通 `i` 未改变菜单，`Shift+I` 则进入 Information，`Shift+S` 进入 Status。可以记录这一组合下的实际行为，不能据此声称原程序只接受大写字母、所有无响应都由输入法造成，或历史命令已经送达。

没有测试 Alt+F10 或宏展开。日志还明确提示 DOSBox 的 `Alt-F10` 用于配置；它与 KEY 中的 Alt+F10 绑定存在宿主处理冲突的可能，本轮不通过组合键重放来判断。KEY 打开记录和手动菜单成功也不证明宏已触发。

## 结束位置、异常与清理

Status 证据取得后，为提高可读性尝试用 MCP `App(mode=resize)` 将本轮窗口调到 1280×1024。外层窗口扩大，但客体图面未同步扩大，截图出现黑色区域及重绘残影。该操作没有提供更好的字形证据，是本轮不必要的窗口调整；保留原始返回和截图，后续取证优先使用原图裁剪或另行验证的客体原生捕获方式。

随后只执行恢复窗口尺寸的动作，没有发送新的程序命令。恢复至 662×566 后，原生前景和截图显示 Orca 已到前景，DOSBox 的 Status 仍局部可见。焦点变化原因未知，不能用 `ControlStatus=ai` 代替目标焦点；在该状态下停止键盘交互，没有执行计划中的 Status Esc 返回或文字属性入口。

本轮已请求仅关闭自身 PID 的 `CloseTarget`。该动作前连续 16 次 ControlStatus 返回 `user`，30 秒内未恢复，客户端抛出异常并退出；**窗口关闭动作本身没有执行**。未重连、未发送输入、未更改控制门、阈值、hooks 或第三方包。

客户端退出后，本地启动的 DOSBox 仍存在。清理时先用 CIM 核对 PID 47704、父 PID 5772、映像与包含 `verification-35` 的唯一配置命令行，记录在 `owned-target-cleanup-before.json`，再仅对该 PID 执行 `Stop-Process`。初次进程查询短暂仍见命令行为空的退出条目；后续 `Get-Process` 和 CIM 均无该目标及本轮客户端/MCP，最终记录为 `processes-final-confirmed.json`。没有清理共享 Windows Terminal 或其他应用。

## 验证与下一步

原安装 99 个文件、既有和新副本各 103 个文件的完整集合与 SHA-256 前后相同，没有新增、丢失或内容差异。输入仍无 `TRAXEDIT.DFT`；没有保存板图或状态报告。`check-inputs.py before/after` 和 `summarize.py` 均已实际运行通过；汇总同时核对关键动作前后 PID、文件日志、前景变化、16 次 user 门禁、未执行关闭动作及最终退出记录。

本轮只更新文档，不修改 Qt、字形工具、方向缩放、铜层或发布包，不需要 Qt 构建或 CTest。运行证据支持菜单与工作文件名的上述特定结论；**文字内容、位置、高度、方向、线宽等对象属性未在界面核对，四条 FT 参考记录的计数差异未解释，独立字形行为对照未完成**，`runtime_verified=false`。

后续在新的隔离场景保持原窗口尺寸及单连接控制，优先观察文字属性并取消返回；离线追踪或独立最小样例应说明 FT 记录为何未体现于 Status，再开展参考尺标、端点和方向对照。本轮已经证明日志方案可用，无需继续把“日志尚未执行”作为当前阻塞；verification-33 的黑屏历史根因和 verification-28 的窗口变化原因仍未知。
