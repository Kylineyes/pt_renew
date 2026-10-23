# 原文字形运行对照步骤

本步骤接续 [原文字形静态证据](legacy-text.md)。已观察到原程序在研究样例启动页之后绘制文字，恢复原样默认配置的 C21 场景还显示了参考十字与尺标；实际文件名、对象属性和独立字形对照仍未确认。所有工具笔画结果仍为静态推导，`runtime_verified` 保持 `false`。

## verification-33 子 agent 验证与验收

从 `050c713` 分发独立静态复核和运行验证任务，分别见 [Information、Status 与宏键静态复核](legacy-menu-static-validation.md) 和 [原菜单运行核验与桌面观测诊断](legacy-menu-runtime-validation.md)。静态复核确认菜单分派与宏初始化，修正 Status 的文件名为去目录后名称与扩展名，并细化单个 Esc 取消输出的条件。

运行诊断发现 Windows-MCP 0.8.8 在 `use_ui_tree=false` 时主动跳过窗口枚举，故 verification-29/32 的空窗口元数据不能证明焦点异常。新场景通过完整 UI 快照及 Win32 HWND/PID 观测核对窗口归属；随后单连接启动全新无 DFT 副本，DOSBox 客户区只有黑底与白横线，未取得 AUTOTRAX 启动页，因而停止，未发送键鼠输入。原安装 99 项及既有、新建两份 103 项副本前后摘要均一致，相关进程已退出。

本轮没有取得菜单响应、实际载入文件名或文字对象参数证据，`runtime_verified` 保持 `false`。启动工具将目标 stdout/stderr 丢弃，本轮无法恢复；后续独立场景先补充 DOSBox 自身日志及配置来源，再判断启动阻塞，继续按单连接、逐步截图和控制边界推进。

## verification-31 菜单与键盘静态路径

已从 `d9f9506` 的最新 `origin/dev` 建立 `research/legacy-menu-static`，带入 verification-29/30 尚未提交的记录。离线分析已将菜单文件装载、段解析、绘制调用、主菜单 Enter 入口、KEY 覆盖装载和宏展开路径串联，详细地址、重定位交叉核对及复核工具见 [原菜单、宏与键盘分派的静态路径](legacy-menu-keypath.md)。这些结果仍为静态证据；尚未证明此前场景实际载入菜单、PCB 或宏。

verification-32 仅在新目录和单个连接中检查桌面：`ControlStatus=ready`、generation 1，截图可见 Orca 窗口，但元数据仍报告没有活动窗口及打开的窗口。因焦点观测不一致而停止，未启动 DOSBox、未发送键鼠输入。`runtime_verified` 保持 `false`，产品仍为 0.9.0。

## verification-29 DOSBox 焦点检查

从 `d9f9506` 建立 `research/legacy-menu-keypath`。开始前未发现 DOSBox、AUTOTRAX 或本轮桌面客户端进程；无 DFT 隔离副本为 103 个文件，其文件名集合和 SHA-256 与 verification-20 清单一致。原安装未挂载，本轮仅使用该隔离副本。

新建 `.local-analysis/verification-29/desktop-check/` 和 DOSBox 配置，捕获目录指向该新场景，启动参数为 `PT C21.PCB`。同一 Windows-MCP 连接先查得 `ControlStatus=ready` 并截图；启动后取得标题 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms` 和 AUTOTRAX 1.57 启动页。其后一次控制查询返回 `user`、generation 16、`wait_seconds=2.4502866999828257`；等待恢复后调用窗口切换，工具报告切换到 DOSBox。截图显示 DOSBox 小窗口在 Orca 桌面前景，但 MCP 窗口元数据仍报告 `No active window found`、`No windows found`，两类观察不一致，不能据截图单独确认键盘焦点。再次确认 `ready` 后点击截图所示 DOSBox 标题栏 `(300,120)`，工具报告点击成功；后续截图仍可见该 DOSBox 启动页，但窗口焦点状态仍未由工具确认。

因无法交叉确认焦点，停止场景，没有发送 Enter、宏或其他键盘操作；因此没有观察启动页之后的程序行为，不能判断 C21 是否载入，也不能解释菜单/宏响应或此前窗口变化原因。只终止本轮启动的 DOSBox PID 4864 和临时桌面客户端 PID 59956。运行后复核隔离副本仍为 103 个文件且与运行前清单 0 项差异；进程检查未发现 DOSBox、AUTOTRAX 或 Windows-MCP 客户端残留。截图、逐步状态、命令返回、配置和核验留在被 Git 忽略的 `.local-analysis/verification-29/desktop-check/`。

本轮没有取得新的程序行为证据；`runtime_verified` 继续为 `false`，静态工具证据继续标记为 `static_instruction_derivation`。未进行端点拟合、方向/缩放扩展、Qt 字形接入或铜层判定；没有运行构建或 CTest。

## verification-30 桌面控制等待

在 verification-29 之后新建 `.local-analysis/verification-30/scenario/`，并重新核对无 DFT 隔离副本 103 个文件与 verification-20 清单一致；开始时没有 DOSBox、AUTOTRAX 或本轮客户端残留。新 Windows-MCP 连接首次 `ControlStatus` 返回 `user`、generation 2、`wait_seconds=9.98607709998032`。随后仅请求新桌面截图；客户端按门禁最多等待 30 秒，状态未恢复，截图工具未调用。没有启动 DOSBox、没有发送键鼠输入，输入来源未知；停止本轮客户端后进程检查无相关残留。该场景没有新增原程序运行证据。

## verification-28 LIST_COMPS 只读入口探测

从同步的 `dev`（`e879f7f`）建立 `research/legacy-text-runtime-observation-2`。运行前确认无 DOSBox 残留，并逐项核对无 DFT 隔离副本 103 个文件；`C21.PCB` SHA-256 为 `09f16e0c4fb7e0380e15285b8d610f6963e73ad349c9168cb28626f34c0a3f85`。`TRAXEDIT.KEY` 将 `Alt+F10` 定义为 `LIST_COMPS`，宏序列为 `Esc, Esc, I, C`；`TRAXEDIT.MNU` 的 `Information` 子菜单含 `Components`、`Status`。这些是静态菜单证据，不证明运行响应。

新连接先取得桌面截图，`ControlStatus=ready`、generation 1；随后启动隔离无 DFT C21 配置，启动前状态为 `ai`、generation 2。核对标题 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms` 与 AUTOTRAX 1.57 启动页，聚焦后按 Enter。画面出现灰底、红色 A 轮廓和白色十字，但仍无文件名、对象属性或参考尺标。发送 `Alt+F10` 后截图未见可辨变化，未出现 `COMPONENTS PLACED` 或任何对象列表。

接着按静态宏序列逐步发送。第一个 Esc 后截图仍显示 DOSBox；第二个 Esc 后截图转为两个 Windows Terminal 窗口覆盖前景，DOSBox 窗口不可见。该次 `ControlStatus` 返回仍为 `ready`/`ai`，但画面切换原因未知。由于余下的 `I`、`C` 命令此前已排队，二键仍被发送；这两步不作为 AUTOTRAX 行为证据。随后立即结束客户端；客户端退出后 DOSBox 进程也消失。没有发送保存或编辑命令。

DOSBox 释放文件后复核无 DFT 隔离副本的 103 个文件集合与 SHA-256，均和运行前清单一致；原安装 99 个文件也与基线一致。截图、门禁记录、命令及摘要保存在被 Git 忽略的 `.local-analysis/verification-28/scenario/`。本轮没有确认菜单/列表入口、实际板图载入、文件名或文字对象状态；未进行坐标拟合、Qt 字形接入或铜层判定变更。`runtime_verified` 保持 `false`，静态工具证据仍为 `static_instruction_derivation`；未运行构建或 CTest。

## verification-27 无 DFT 菜单候选运行

从同步的 `dev`（`69da3fb`）建立 `research/legacy-text-runtime-followup`。先核对原安装 99 个文件及 SHA-256 基线，并逐项核对无 DFT 隔离副本 103 个文件；`C21.PCB` SHA-256 为 `09f16e0c4fb7e0380e15285b8d610f6963e73ad349c9168cb28626f34c0a3f85`。启动配置挂载既有无 DFT 隔离副本，DOSBox 捕获目录设为新场景目录；输入未修改。

前置 verification-25 连接状态为 `ready`、generation 1，并取得空桌面截图后结束连接。verification-26 在新连接取得初始截图，状态为 `ready`；启动请求返回 PID 53476，但客户端随后因将 `command-001-gate.json` 误识别为命令而异常退出，未取得启动后截图或发送键鼠输入。之后未发现该 DOSBox 进程。本次不复用前两轮命令文件，在 verification-27 新连接中重新取初始截图，再于同一连接启动无 DFT 的 C21 场景。

verification-27 初始 `ControlStatus` 为 `ready`、generation 1；启动前为 `ai`、generation 2。启动页截图确认完整标题 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms` 和 AUTOTRAX 1.57。点击标题栏聚焦后，逐步核对状态并发送 Enter；后续画面显示灰色背景、红色 A 线条和白色十字，与既有无 DFT 观察相符。该画面没有菜单、文件名、对象属性或参考尺标，不能独立确认 C21 已实际载入。

随后逐键发送候选 `Esc, Esc, I, B`，每键前再次查询状态并在键后截图。四张后续截图均未见可辨画面变化，没有出现 `Information`、`Board Dimensions` 或 `Status` 信息。该候选仍未被验证为菜单快捷序列，也未获得板图载入、文件名或文字对象状态证据。点击 DOSBox 窗口关闭按钮后取得桌面截图；结束时无 DOSBox 或场景客户端残留。原安装 99 个文件与基线一致，无 DFT 隔离副本 103 个文件的集合与 SHA-256 也与运行前清单完全一致。

本地命令、逐步返回、门禁状态、截图及运行摘要保存在被 Git 忽略的 `.local-analysis/verification-27/scenario/`；此前启动中断记录在 `.local-analysis/verification-25/` 和 `.local-analysis/verification-26/`。本轮没有保存、编辑或修改输入，也没有进行端点拟合、方向/缩放对照、Qt 字形接入或铜层判定变更。`runtime_verified` 继续为 `false`，静态工具证据继续标记为 `static_instruction_derivation`；未运行构建或 CTest。

## 菜单文件与按键候选

只读检查 verification-20 无 DFT 隔离副本中的 `TRAXEDIT.MNU` 与 `TRAXEDIT.KEY`；两者 SHA-256 均与原安装基线相符。MNU 的 `#MAIN` 列出 `Information`，其子菜单含 `Board Dimensions` 与 `Status`。KEY 将 `REDRAW` 映射到 `F9`、`RECENTRE` 映射到 `F10`，并有 `LIST_PLANE` 宏序列 `Esc, Esc, I, P`。这些文件说明存在菜单结构和宏定义，不证明程序在先前画面中已载入菜单，亦不代表相应操作已运行成功。

据菜单层级与宏序列，`Esc, Esc, I, B` 是进入 `Information → Board Dimensions` 的待验证命令候选，不是已确认快捷键。本轮在新的 `.local-analysis/verification-22/information-probe/` 中先请求桌面截图；同连接 30 秒内 16 次 `ControlStatus` 查询均为 `user`、generation 为 2，`wait_seconds` 约 9.66 至 10 秒。超时后停止客户端，截图请求未执行，未启动 DOSBox、未发送按键或鼠标操作；输入来源未知，未更改控制门禁。原目录 99 个文件集合与 SHA-256 符合基线，C21.PCB 与场景清单匹配，KEY/MNU 与原安装摘要匹配，无本轮残留进程。返回与摘要留存在被忽略的 `.local-analysis/verification-22/`。

桌面恢复后优先用新连接和新截图，在隔离 C21 无 DFT 场景中执行并观察该候选命令。若菜单确实响应，再检查 `Information` 下的 `Board Dimensions`、`Status` 等信息项是否提供实际板图/载入状态；若不能确认文件名或文字属性，再回到静态读取路径定位可观察入口。此项仍只是静态导出的检查路径，`runtime_verified` 保持 `false`。

随后从 `dev` 的 `944c3bf` 建立 `research/legacy-text-information-probe`，在新的 `.local-analysis/verification-23/information-probe/` 中请求先取得桌面截图。30 秒内 16 次 `ControlStatus` 查询均为 `user`、generation 为 2，`wait_seconds` 范围为 8.28 至 9.999 秒；超时后客户端停止，截图请求未执行，也未启动 DOSBox 或发送键鼠操作。输入来源未知，未重试场景或修改门禁。无 DFT 副本 103 个文件与 verification-20 清单匹配，原安装 99 个文件集合及 SHA-256 符合基线，结束时无本轮桌面客户端或 DOSBox 残留。日志和摘要留在被忽略的 `.local-analysis/verification-23/`。候选 `Esc, Esc, I, B` 仍未运行验证。

随后从 `dev` 的 `773c015` 建立 `research/legacy-text-information-probe-2`，在新的 `.local-analysis/verification-24/information-probe/` 中用同一连接成功取得初始桌面截图，初始 `ControlStatus` 为 `ready`、generation 为 1。启动 DOSBox 前的控制检查变为 `user`、generation 为 4；客户端等待 30 秒、16 次查询后超时，最后 `wait_seconds=9.941726699995343`。DOSBox 启动请求未执行，没有发送键鼠输入；输入来源未知。无 DFT 副本 103 个文件与 verification-20 清单匹配，原安装 99 个文件集合与 SHA-256 基线一致，结束时无 DOSBox 或本轮客户端残留。新桌面图、日志和摘要保存在被忽略的 `.local-analysis/verification-24/`。这次与 verification-23 不同，初始截图已取得；菜单候选仍未执行验证。

## 无 DFT 场景配对运行

从 `dev` 的 `0575ca3` 建立 `research/legacy-text-defaults-control`，在新的 `.local-analysis/verification-21/without-dft/` 中复制桌面客户端并使用同一 Windows-MCP 连接完成此前缺少的无 DFT 场景。启动前再次逐文件核对 verification-20 两个运行副本：无 DFT 为 103 个文件，有 DFT 为 104 个文件；除后者原样 `TRAXEDIT.DFT`（SHA-256 `df3b18617d7ab58b1f9380437d0e9238b22f55d3f54388b18a7b3f80f6decd8b`）外，其余集合与摘要相符。两份配置都执行 `pt C21.PCB`，模拟器参数和挂载目录配置不变。

同连接先取得新的桌面截图，再启动 `.local-analysis/verification-20/dosbox-without-dft.conf`。核对完整窗口标题 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms` 及 AUTOTRAX 1.57 启动页后，点击标题栏聚焦并按 Enter。`.local-analysis/verification-21/without-dft/result-007.png` 显示灰色背景、红色 A 状线条和白色十字；没有观察到有 DFT 场景 `verification-20/paired-run/result-006.png` 中的黑色背景、灰色参考十字及非对称尺标。两者启动页均显示 `VGA 640x480`，该驱动名称不能区分 DFT 是否读取。发送 F 后 `result-009.png` 画面未见变化；两图摘要不同，不记录为像素完全相同。菜单、实际文件名、文字对象属性和可见图层状态仍未显示。

两次运行使用同一 C21 输入和等价 DOSBox 配置，启动前两个隔离目录唯一文件差异是 DFT，运行后文件清单和摘要仍与各自启动前清单相符。因而可以记录有无 DFT 场景的显示结果不同，且差异与 DFT 文件是否存在相关；但运行发生在不同连接/时刻，不能据此确认原程序读取了 DFT 的哪些内容、定位具体字段或解释菜单为何不可见。命令行中的 `C21.PCB` 也不是实际载入文件名或对象状态的独立证据。

点击新截图中的 DOSBox 关闭按钮后，`result-011.png` 返回桌面，进程核对确认 DOSBox 退出；停止同连接客户端后无本轮 DOSBox 或桌面客户端残留。原安装目录 99 个文件集合与 SHA-256 基线一致。此次只完成默认配置配对观察，未进行端点拟合、方向/缩放检查、Qt 字形接入或铜层判定变更；`runtime_verified` 仍为 `false`。同连接命令、返回、截图及输入清单保存在被忽略的 `.local-analysis/verification-21/without-dft/`，不提交本地证据。

## 默认配置诊断的前序记录

`research/legacy-text-defaults-diagnosis` 基于同步的 `dev`（`a581f67`）。既有 `.local-analysis/verification-11/prepare-text.py` 在建立副本时将 `TRAXEDIT.DFT` 改名为 `TRAXEDIT.OLD`，后续 C00/C20/C21 场景沿用了这个无 DFT 目录。原 DFT 含历史绝对路径、显示及其他默认参数，不能未经核对直接将其视为可复用的应用配置。

为检查配置缺失的影响，在 `.local-analysis/verification-20/` 新建 `runtime-without-dft/pt/` 与 `runtime-with-dft/pt/`，前者复制既有隔离输入，后者额外恢复原样 DFT。启动前逐文件摘要核对表明，两个副本唯一文件差异是 `TRAXEDIT.DFT`，其 SHA-256 为 `df3b18617d7ab58b1f9380437d0e9238b22f55d3f54388b18a7b3f80f6decd8b`。两个 DOSBox 配置均执行 `pt C21.PCB`，C、D 盘均只挂载各自隔离目录；未修改原安装或既有运行目录。

此前在本目录两次尝试取得首张截图，各等待 30 秒、16 次查询均为 `user`，没有截图或启动目标。用户随后再次授权继续，在新的 `paired-run/` 同连接中取得 `ready` 和新桌面截图，启动有 DFT 的副本并核对 AUTOTRAX 1.57 启动页。启动页显示 `VGA 640x480`，但此前无 DFT 的启动页也有该驱动名，因此驱动名本身不能证明 DFT 已成功读取，更不能证明某个具体设置已经生效。

核对标题栏、聚焦并按 Enter 后，`paired-run/result-006.png` 显示**黑色背景、红色 A、灰色参考十字与非对称尺标，以及贯穿视图的白色十字**。这是首次取得参考标记可见的研究画面。菜单、实际文件名和对象属性仍未出现；按 F 后 `result-008.png` 与前图 SHA-256 相同。点击窗口关闭按钮后，`result-010.png` 与进程核对确认 DOSBox 已退出。

接着启动无 DFT 副本之前，控制状态连续 30 秒、16 次查询均为 `user`、generation 为 24，最后 `wait_seconds=5.722367600013968`；超时后连接停止，未执行该次启动请求，输入来源未知。**本轮配对尚未完成**：恢复 DFT 的场景出现了参考标记，但只能与此前不同轮次的灰底场景比较，尚不能把差异归因到 DFT 的某个字段，也没有定位菜单缺失原因。没有修改门禁、阈值、hooks 或第三方包。

前后核验：原目录 99 个文件集合及 SHA-256 符合基线，既有三项二进制与 C00/C20/C21 摘要一致；新建两个副本的完整文件集合与摘要也完全未变，结束时无本轮桌面客户端、Windows-MCP 或 DOSBox 进程。本地保留 `experiment.json`、`inputs-*-before/after.json`、`verification-summary.json`、配置、逐步返回及截图；原文件、配置内容、截图和笔画数据不提交。已有 Ghidra 项目按 `-noanalysis -readOnly` 做了配置与菜单锚点扫描，尚未确认 DFT 读取或缺省初始化路径，静态输出仅留本地。

下一步优先查明菜单、实际载入文件名、文字对象参数和可见图层为何不可见；不要根据本次背景/参考标记差异猜测 DFT 字段或认定对象已载入。原样 DFT 含历史启动路径，须先取得文件和对象状态证据，再进行端点、交点、整数缩放及方向对照。产品仍为 0.9.0，未接入 Qt 字形或铜层模型；前序诊断仅更新研究文档，未重跑构建或 CTest。

## C21 现场结果

在 `research/legacy-text-c21-observation` 分支（基于 `804263a`）取得新的桌面截图，通过同一 Windows-MCP 连接启动隔离 `dosbox-c21.conf`。核对 AUTOTRAX 1.57 启动页后点击标题栏聚焦并按 Enter，局部截图显示灰色背景、红色 A 和白色十字，仍没有菜单、实际文件名、对象属性或 11 层参考尺标。随后发送 Esc、F，下一张截图与此前截图完全相同。

与前次 C20 截图相比，C21 的 A 显示大小和位置不同，但没有独立可见尺标，不能据此拟合比例、验证字高或确认参考走线已加载。参考走线宽度改为 10 仍未让菜单、属性或尺标出现，灰色画面原因继续保留未知。

准备发送 F9 时，操作前 30 秒内 16 次控制查询始终为 `user`、generation 为 20，最后 `wait_seconds=8.987158999952953`；超时后连接停止，未发送 F9，未取得重绘后的截图，也未重试。输入来源未知。当前安装的 Windows-MCP 未提供申请控制权或弹窗批准的公开接口；其公开 `ControlStatus` 只返回状态，正常桌面调用在 `ready` 或 `ai` 时取得控制，不因会话中的授权文字覆盖 `user` 状态。本轮仅只读核对工具注册和状态实现，没有修改包、hooks、门禁或阈值。

`.local-analysis/verification-19/` 保留同连接客户端、逐步命令和返回、截图、输入核验及摘要：`result-003.png` 为启动页，`result-006.png` 为 Enter 之后画面，`result-009.png` 为 Esc、F 之后画面。原目录 99 个文件集合及 SHA-256 前后符合基线，隔离三项二进制与 C00/C20/C21 摘要一致，结束时无本轮桌面客户端、Windows-MCP 或 DOSBox 残留。

本轮已取得 C21 启动页之后的绘制观察，尚未取得完整载入或独立字形对照证据，`runtime_verified` 保持 `false`。下一步应诊断菜单、属性及参考层不可见的原因，取得实际文件和对象状态后再继续字形测量。产品仍为 0.9.0，没有 Qt 或铜层接入变更；仅更新研究文档，未重跑构建或 CTest。

## C20 现场结果

在 `research/legacy-text-c20-live` 分支（基于 `308ddc0`）重新取得 `ControlStatus=ready` 和真实桌面截图。同一连接启动隔离 `dosbox-c20.conf`，核对新的 AUTOTRAX 1.57 启动页，点击标题栏聚焦并按 Enter。后续局部截图出现红色 A 和白色十字，但没有菜单、实际文件名、对象属性或参考尺标。这次已观察到无参考走线配置下启动页之后的绘制，仍不足以确认编辑器完整载入或完成字形对照。

右键和 `E` 操作后的截图未见变化；`Alt+F4` 调用后窗口仍在，下一张截图中部分笔画变为青色，十字位置改变。仅记录先后观察，不确定该快捷键在 DOSBox 或原程序中的实际作用，也不据此认定程序完全不响应、对象已被选中或编辑成功。随后点击新截图中的窗口关闭按钮，截图及进程核对确认 DOSBox 已退出。

C20 没有参考走线仍出现与此前 C00 相似的灰色背景和 A，因而移除走线未让菜单或属性出现；这不是对灰色画面原因的完整排除。准备启动 C21 时，操作前 30 秒内 16 次控制查询始终为 `user`、generation 为 28，最后 `wait_seconds=5.466629399976227`；等待超时后停止连接，未执行 C21 启动请求。输入来源未知，未重试或绕过门禁。

本地 `.local-analysis/verification-17/` 保留同连接客户端、逐步命令与返回、截图、前后输入核验和摘要。`result-003.png` 为启动页，`result-006/008/010.png` 为红色 A，`result-012.png` 为后续颜色及十字变化，`result-014.png` 为关闭后的桌面。原目录 99 个文件集合及 SHA-256 前后符合基线，隔离三项二进制与 C00/C20/C21 摘要一致，结束时无本轮进程残留。

下一步需在正常空闲状态下运行 C21，并继续核对菜单、文件名、对象属性及独立尺标。`runtime_verified` 仍为 `false`，静态工具证据标记不变，未进行坐标拟合或 Qt/铜层字形接入；产品仍为 0.9.0。本次只更新研究文档，未重跑构建或 CTest。

### C21 后续尝试

随后从同步的 `dev`（`528c109`）建立 `research/legacy-text-c21-live`，在 `.local-analysis/verification-18/` 使用新连接尝试先取得桌面截图。首次截图前等待 30 秒，16 次 `ControlStatus` 查询均为 `user`、generation 为 2，最后 `wait_seconds=9.999470599985216`；倒计时多次接近 10 秒，输入来源未知。超时后停止场景，没有调用截图、启动 C21 或发送输入，也没有重试或改变门禁。原目录 99 个文件集合及 SHA-256、隔离三项二进制与 C00/C20/C21 摘要前后均核验通过，结束时无本轮进程残留。该目录保留日志、错误返回、输入核验与摘要；没有新增运行结论。


## 前次 C20 场景等待记录

从与 `origin/dev` 同步的 `6b5b22f` 建立 `research/legacy-text-c20-runtime`，先核对输入与遗留进程，再在新的 `.local-analysis/verification-16/` 中启动同连接桌面客户端。首次截图前等待 30 秒，16 次公开 `ControlStatus` 查询始终为 `user`、generation 为 2，倒计时在约 9.50 至 10.00 秒之间反复重置；最后返回 `wait_seconds=9.99860739998985`。这些返回不能识别输入来源。

等待超时后客户端停止；未调用截图、启动 DOSBox 或发送按键，没有重试场景或切换其他桌面入口，也没有修改第三方包、门禁、阈值或 hooks。`C20.PCB` 的启动页之后观察仍未完成，`C21.PCB` 仍未运行；此前 C00 红色 A 画面的证据边界不变。

原目录 99 个文件集合及 SHA-256 在尝试前后均符合基线，隔离三项二进制与 C00/C20/C21 摘要一致。结束时未发现本轮桌面客户端、Windows-MCP 或 DOSBox 进程。日志、输入核验和摘要留在上述本地目录；仅更新研究记录，未重跑构建或 CTest，产品仍为 0.9.0。

下一步仍是在桌面正常空闲后完成 C20 的启动页之后观察，核对菜单、文件名与对象属性，再与 C00/C21 对照。尚未取得新运行证据，不接入 Qt 字形或铜层几何，不扩大方向支持范围。

## 输入与方向字段

先复用 `.local-analysis/verification-11/runtime/pt/`。单字符 `A` 的配置为 `.local-analysis/verification-12/dosbox-single.conf`，启动命令为 `pt C00.PCB`，两个盘符均只挂载既有隔离 runtime。`C00.PCB` 已复制到隔离目录，SHA-256 为 `96f838cf5e0cb86763357c4a11ec81f7b87053573981afa5df0a0ecbf2e1a1c8`，仍未确认被原程序载入。旧 `dosbox-text.conf` 对应九组混合样例，不作为首次单字符验证入口。

启动前核对隔离副本的 `PT.EXE`、`TRAXEDIT.OVR`、`GRAPH.DRV` 摘要及样例摘要；配置只能挂载隔离目录。保留既有输入和配置，新增样例使用不同文件名，并记录实际加载文件的摘要。

**文件方向到内部方向已有条件静态路径，运行映射仍需验证。** 后续只读研究核对了 `FS` 第四整数经当前变换状态处理后，写入对象方向 byte，保存路径也输出该 byte，详见 [PCB 文字字段的静态路径](legacy-pcb-text-path.md)。当前 Qt 读取器只接受文件方向值 `0..3` 和 `16..19`；这只是重建程序的支持范围，不能证明原程序的完整接受范围。既有九组 `TEXT.PCB` 中包含文件方向值 `32`，不能仅凭内部解释器支持 `0x20` 就认定该记录能载入或产生 Y 镜像。

因此先使用方向值 `0` 的独立文件建立载入证据，再逐项检查其他方向。若文件被拒绝、字段被归一化或对象属性与请求不一致，应单独记录；不能将载入问题当成笔画解释差异。Y 镜像及组合已有文件读取与保存字段的静态依据，但还需确认实际加载及当前变换状态，再逐项开展运行对照。

## 样例顺序与判据

每个文件只含一条文字，文字原点固定为 `(2000, 2000)`，笔宽 1、图层 1；11 层提供十字原点及非对称尺标。比较时记录两层是否可见，截图保留尺标和应用状态，不用文字自身的外观反推原点或比例。

| 顺序 | 输入 | 需要回答的问题 |
| --- | --- | --- |
| 1 | 单字符 `A`、`F`，高度 240，方向 0 | 文件是否实际载入；字符、位置、高度、图层及方向属性是否符合请求 |
| 2 | 同一视图中的原点、尺标和字符 | 坐标轴方向、像素比例、笔画端点、交点及可见边界是否与静态推导对应 |
| 3 | `AA`、`A A`、单个空格，高度 240 | 第二字符起点、空白移动是否一致；纯空格须结合属性或后续字符判断，空白画面不足以证明载入 |
| 4 | `A`、`AA`，高度 251、252，与 240 对照 | 静态整数缩放分别为 20、21；同视图下是否出现预期的保持与变化 |
| 5 | `F`，文件方向候选 `1..3`、`16..19` | 非对称笔画和原点的对应关系；逐项核对文件方向到内部旋转、镜像的映射 |
| 6 | Y 镜像和旋转、双镜像组合 | 映射有证据后再构造输入，逐项核对变换顺序 |
| 7 | 同一对象改变视图缩放、笔宽 | 何时进入替代路径，线宽及像素边界如何变化；与中心线比较分开记录 |

比较端点时先用尺标建立板坐标到画面坐标的关系，包含画面 Y 轴方向和视图平移。线宽、像素取整、裁剪或替代显示可能改变可见边界；保留测量值和残差，不以形状相似或随意的像素容差宣布一致。样例推导使用内部方向值时，须明确记录文件字段映射是已验证还是假设。

每次观察记录输入 SHA-256、原程序与驱动 SHA-256、配置、实际加载证据、对象属性、缩放、可见层、截图路径、静态请求参数和差异。分别标记“已观察”“推断”“未知”；截图、笔画导出、原字节和反编译结果只留在被忽略的本地目录。画面一致也不能证明运行时字体指针从未变化或铜面积已经恢复。

## 桌面操作与证据边界

Windows-MCP 的公开 `ControlStatus` 曾返回 `ready`，并已取得真实桌面截图和 AUTOTRAX 1.57 启动页。使用完整标题 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms` 切换成功，同一连接中的 Enter 调用成功返回；随后完整 UI 树截图超时，仍没有编辑器画面、实际文件名或对象属性证据。启动页和按键调用成功不足以证明样例载入。

连续约 10 秒无输入且无键鼠按住时，控制状态可恢复。每步前查询 `ControlStatus`，最多等待 30 秒；等待超时或出现 `CONTROL_PREEMPTED` 后停止当前场景，保留状态，不盲目重放动作。倒计时重置只证明工具持续检测到输入事件，不能据此判断是用户操作、设备抖动还是其他输入源。

启动、截图核对目标、切换、按键及后续截图应保持同一连接。客户端会话结束后曾观察到目标进程消失，跨轮必须重新核对进程并取得新截图，不能沿用旧坐标。常规 DOS 画面优先使用 `use_ui_tree=false`；在新截图确认目标范围后使用局部 `region`，完整 UI 树只在需要识别窗口时查询。

## 准备情况与本轮探测

前一研究分支 `research/legacy-text-runtime` 准备了 16 个独立 PCB 样例及静态推导，保存在 `.local-analysis/verification-12/prepared-cases/`。它们覆盖表中前五项所需输入，每份清单明确标记文件方向映射未验证、运行未验证；Y 镜像及组合没有作为已确认文件编码加入。除已复制的 `C00.PCB` 外，其余样例尚未复制到运行目录；没有任何一份完成原程序载入确认。

本轮从已同步的 `dev`（`45e424d`）建立 `research/legacy-text-runtime-check`，使用同一 Windows-MCP 连接，首先等待控制空闲以取得新截图。30 秒内状态始终为 `user`，16 次查询中倒计时多次回到约 10 秒，generation 从 1 变为 3；等待超时后停止，未调用截图、启动或按键工具，未启动 DOSBox。这里的 generation 变化不用于推断输入来源。

本轮日志和输入核对保存在被忽略的 `.local-analysis/verification-13/`。运行前后均核对了 99 个原始文件的集合及 SHA-256，与既有基线一致；隔离副本三项二进制和 `C00.PCB` 摘要符合预期。结束时没有本轮桌面客户端、Windows-MCP 或 DOSBox 进程。

## 后续现场调试

在 `research/legacy-text-desktop-live` 分支继续调试时，Windows-MCP 已实际恢复 `ready`，在同一连接内启动 `dosbox-single.conf` 并取得 AUTOTRAX 1.57 启动页。核对新截图中的窗口标题栏后点击聚焦并按 Enter，后续多张截图出现红色单字符 `A` 和白色十字光标，说明启动页之后已经发生文字绘制。这比此前只有启动页的证据更进一步，但**尚不足以确认编辑器完成载入或完成单字符行为对照**。

该画面没有显示菜单、实际文件名、对象属性或 11 层参考尺标；发送 `E`、Esc、Space 和 End 均未取得可见变化，完整标题切换调用成功也未改变这一现象。没有据此断言程序崩溃、文件格式错误或某条走线造成停滞。A 的外观不能代替独立坐标尺标和属性核对，不能仅凭该画面确认方向字段映射、缩放或中心线一致。

为区分参考走线与加载流程的影响，在隔离 runtime 另建了 `C20.PCB`（保留 A、移除参考走线）与 `C21.PCB`（参考走线宽度由 1 改为 10），原 `C00.PCB` 保持原样。关闭首个 DOSBox 后，在同一连接启动 `C20.PCB` 对应配置并取得启动页；下一次聚焦动作前控制状态变为 `user`，30 秒等待超时，未发送该轮 Enter。此后仅以新连接尝试等待空闲和获取新截图，再次等待 30 秒超时，未调用截图或交互。因此 `C20.PCB` 尚未进入绘制对照，`C21.PCB` 未启动，两者均不能用于解释首个样例的现象。

本轮截图、逐步命令和返回、诊断样例及摘要保存在 `.local-analysis/verification-14/`，不提交原软件或截图。原目录 99 个文件集合及 SHA-256 调试前后均符合基线，隔离三项二进制和 `C00.PCB` 摘要未变；结束时没有本轮 DOSBox、Windows-MCP 或客户端进程。只更新研究文档，差异检查通过，未重跑构建或 CTest，产品仍为 0.9.0，`runtime_verified` 保持 `false`。

后续先在正常空闲状态下完成 `C20.PCB` 的启动页之后观察，确认是否能出现菜单和属性；再对照 `C00.PCB` 或 `C21.PCB`，逐项排除加载与显示问题。取得实际文件名、对象属性和参考尺标之前，仍不开展坐标拟合或字形接入。
