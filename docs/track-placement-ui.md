# 走线放置的主窗与画布接入

本阶段把现有 `TrackPlacementController` 接入 `MainWindow`，复用其文档身份、修订、临时状态和提交校验。未改写控制器、编辑会话或 writer，也没有复制新增历史核心。

## 产品能力门

<a id="explore-ex-029"></a>

`pt::trackPlacementUserEntryAvailable()` 是唯一产品入口能力门，目前返回 `false`。`place.track` 因此仍显示“未实现”并禁用，菜单、F3、画布旧式 P→T 都使用同一个 QAction 和命令分派。F3 采用画布 `WidgetShortcut`，不抢文本框焦点。

[探索 EX-029](exploration-backlog.md#ex-029)。

原软件新增 FT 的默认编码尚未核定，当前基线 writer 仍拒绝新增。不得仅因本阶段的内部放置测试通过而打开能力门，也不能将测试中明确给出的宽度、层、无附加字段当作原软件默认值。后续须由协调者根据原软件证据和保存闭环验证决定开放；本阶段没有连接默认编码或新增保存参数。

能力门开放后的参数窗口代码已准备：宽度和层均为空白，须明确填写整数 mil 宽度及可见铜层 1/6。它通过同一个显式 begin 接口进入工具，没有假定默认值。当前禁用状态下不会出现该窗口。

## 显式内部接口

接口位于 `src/ui/MainWindow.h`，仅供测试、内部验收和后续产品命令复用；它们不是面向当前用户开放的新增入口。

| 接口 | 行为 |
| --- | --- |
| `beginTrackPlacement(int width, int layer, QString* error)` | 显式参数开始放置；拒绝无文档、库、隐藏目标层、读取中、模态窗口及画布文档身份不一致；合法开始后清除选择和测量，显示整数取点面板 |
| `setTrackPlacementStart(QPointF, QString*)` | 指定整数 mil 起点，进入等待终点状态 |
| `previewTrackPlacementEnd(QPointF, QString*)` | 更新有效临时终点，不创建永久身份、不改 dirty、修订或历史 |
| `commitTrackPlacement(QString*)` | 控制器成功新增后调用既有 `publishWorkingDocument()`；后端失败保留有效预览并返回原错误 |
| `pickTrackPlacementPoint(QPointF, QString*)` | 画布共享取点路径：第一次设起点，第二次先校验终点、再提交；非法第二点不会提交旧预览 |
| `cancelTrackPlacement()` | 幂等取消临时放置，不改工作文档 |
| `trackPlacement() const` | 只读控制器状态、参数和临时几何 |

核心仍校验宽度 1..1000000、层 1/6、端点 ±1000000、有限整数和非零长度；主窗不放宽限制。每次取点、预览和提交都经过控制器真实文档指针、编辑修订、文档修订及目标层可见性检查；画布与编辑会话文档身份也必须相同。

## 取点与预览

`BoardCanvas` 仅保存绘制所需的临时宽度、层、起终点，发出坐标信号，由主窗调用控制器。预览使用目标层颜色、实际线宽和端点标记，没有图元控件或永久身份。

画布按原始浮点坐标逆变换取点，不进行隐含网格捕捉、容差吸附或取整。点击落在非整数 mil 时明确提示使用整数取点面板，不修改文档。鼠标移动仅更新合法终点；无效移动不会覆盖上一有效预览。

整数取点面板支持有符号十进制整数 X/Y，不接受小数、非有限值或越界值。“使用此点”先指定起点，再指定终点预览；状态列出实际待提交起终点、宽度和层，再由“确认提交预览”完成提交。修改坐标输入会禁用提交按钮，须重新预览。画布第二次合法点击则直接提交。每次成功只新增一段，回到 Idle，不自动重复或推断下一段参数。

## 取消与既有行为

活动放置会在画布 Esc、主菜单 Esc、编辑菜单“取消当前工具 / 清除选择”、面板取消或隐藏、Undo/Redo、换图请求（包括失败的载入）、关闭板图、打开模态窗口、隐藏目标层、切换测量、定位其他图元或元件、打开库及失效的身份/修订时取消。Undo/Redo 即使没有相应历史，也先取消；文本框里的 Ctrl+Z/Ctrl+Y 仍归文本框。

模态窗口与另存为等命令仅取消走线临时放置，不额外清除既有选择；保存对话框期间发生文档修订仍由原保存保护拒绝旧快照。没有活动走线或测量的画布保持原 Esc 传播，LIB 预览第一次清选择，第二次仍能关闭所属对话框。

没有放置会话时，主菜单 Esc 维持原行为：只关菜单，不清除已有选择或测量。文本框内字母 P/T、F3 和 Esc 不触发画布工具。画布 Esc 与明确取消命令退出当前工具，已完成的只读测量结果仍按原规则保留。

提交后复用 `publishWorkingDocument()`：清除旧选择、测量和捕捉，保留视图参考范围及缩放，重新映射外部 NET，并使用原有 NetlistBrowser 的文档身份/代次规则使铜分析及迟到回调失效。没有修改该浏览器或异步核心。

新建 Created 走线的选择、移动、删除直接复用 `BoardEditSession::editable()`；该规则不依赖正数 source.line，而检查真实修订、有效会话身份和自由图元归属，因此不需要补造来源行。专项验证 Created 线可移动、删除，Undo/Redo 保留身份。

主窗析构在成员销毁前移除 qApp 事件过滤、解除 qApp、画布及走线面板到主窗的回调，避免子控件随后隐藏时访问已销毁的控制器或 QAction 容器。

## 验证与边界

本阶段仅使用 Windows Qt 6.12 / MSVC Debug、`QT_QPA_PLATFORM=offscreen` 验证，未启动可见桌面窗口，没有真实产品交互或截图验收。真实 GUI 由协调者排队验收；本阶段也不构成原软件新增 FT 或保存兼容证明。

新增 `tests/TrackPlacementUiTests.cpp`，11 项通过（含初始化/清理），覆盖能力门、画布与整数面板、预览不 dirty/不分配身份、非法点、取消、后端拒绝保留预览、成功发布、Created 编辑、Undo/Redo、模态/同步异步换图/隐藏层、失效修订、文本焦点。既有 Editing、Shell、Selection、Navigation、EndpointSnap 五组同步回归。最终 CTest 6/6，13.41 秒，构建、专项和 CTest 实际退出码均为 0。

测试通过忽略目录内独立 CMake harness 注册，未修改仓库 CMake 或既有测试；协调者需将新专项链接到 pt_ui / Qt6::Test 并注册 offscreen 执行。

本机证据：`.local-analysis/track-placement-ui/` 的 `session-audit.json`、`build-debug-final.log`、`track-placement-ui-debug.txt`、`ctest-debug-final.log`、`ctest-debug-final-exit.json`。首轮退出 8 的析构崩溃，以及第二轮菜单 Esc 回归失败亦保留在 `ctest-debug.log`、`ctest-debug-exit.json`、`ctest-debug-attempt2.log` 和对应退出回执中；最终通过不覆盖这些失败事实。
