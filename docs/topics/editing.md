# 编辑、历史与保存

[文档导航](../README.md) · [当前进度](../../PROGRESS.md) · [完整资料索引](../reference-index.md)

## 先看结论

| 范围 | 当前状态 |
| --- | --- |
| 发布的 v0.11.0-alpha | 只读，不含下述开发编辑功能 |
| dev 普通用户路径 | 已载入自由 FT 整线移动／删除、Undo/Redo、保存点及另存全新 PCB |
| 内部显式新增路径 | 身份、预览、提交、编码、插入、画布及 MainWindow 显式另存闭环已实现 |
| 正式新增入口 | 能力门 false；菜单、F3、P→T 禁用；默认保存路径拒绝 Created |

<a id="explore-ex-007"></a>

原 AUTOTRAX 自建单线保存重开未完成，新增默认字段未知。内部接口与合成样例不能替代该证据；存在 NETDEF 时继续拒绝新增。

[探索 EX-007](../exploration-backlog.md#ex-007)。

## 第一层分析：一次修改需要哪些身份

Loaded 走线绑定原标签行，Created 使用会话内单调非零身份。选择引用还必须匹配当前文档与修订，不能将旧索引套到新文档。编辑产生新工作快照，原始输入字节保持冻结。

预览只是临时几何：不 dirty、不分配身份。确认成功才进入历史；后端拒绝保留合法预览。撤销／重做重放身份，分支不复用已分配序号；dirty 比较历史位置与有效保存点，不能只比较几何是否看起来相同。

## 第二层分析：从取点到新文件

| 环节 | 实现入口 | 必须满足的条件 |
| --- | --- | --- |
| 编辑与历史 | [BoardEditSession.h](../../src/application/BoardEditSession.h) | 作用域、修订、整数范围、身份、容量 |
| 预览与取消 | [TrackPlacementSession.h](../../src/application/TrackPlacementSession.h) | 起终点、上下文和目标层持续有效 |
| 提交控制 | [TrackPlacementController.h](../../src/application/TrackPlacementController.h) | 成功才结束预览；失败保留状态 |
| 新 FT 编码 | [LegacyFreeTrackCodec.h](../../src/io/LegacyFreeTrackCodec.h) | 调用方明确给出六／七字段、extra 与换行 |
| 插入预检 | [LegacyTrackInsertionPlanner.h](../../src/io/LegacyTrackInsertionPlanner.h) | 严格确认顶层插入点；当前拒绝新增 NETDEF |
| 校验与发布 | [LegacyPcbWriter.h](../../src/io/LegacyPcbWriter.h) | 字节与几何复核，全新目标、不覆盖原件 |
| 主窗闭环 | [MainWindow.h](../../src/ui/MainWindow.h) | 内部 saveAsFileWithCreated 显式参数；发布成功才标保存点 |

已有 FT 移动只替换四个坐标词，删除只移除该记录；其他字段、空白、换行和未知附加值原样保留。输出先重解析比较，再写目标同目录临时文件并改名发布。取消和失败保留工作、历史及 dirty；Ctrl+S 覆盖保存未开放。

内部新增支持有限整数 mil、坐标 ±1000000、宽 1..1000000、层 1/6，零长拒绝；取点不隐含取整或网格吸附。换图、模态、隐藏目标层、测量及历史操作取消放置，避免预览跨上下文提交。

## 第三层分析：实现完成与产品开放分开验收

已测候选有 Debug/Release 各 24/24 CTest；核心定向审查另有 82 passed（含初始化／清理）。主窗生命周期和保存有独立真实 Qt 现场，更早内部 Created 已完成显式参数另存与输出重开。它们的范围见下列报告，不等于正式新增入口、全场景焦点或原软件兼容通过。

## 下一步怎样推进

<a id="explore-ex-029"></a>

先完成[原软件取证](legacy.md)的可靠连续观察、文件状态及单线保存重开，核定输出字段；再复用已有显式路径连接默认策略与唯一能力门。之后验收菜单／F3／P→T、文本焦点、取点、取消、图层、历史、原生另存和产品输出的原软件重开。

[探索 EX-029](../exploration-backlog.md#ex-029)。

## 按需深入

- [普通编辑与另存](../pcb-save-as.md)、[精确写出边界](../pcb-writer-boundaries.md)。
- [新增设计](../free-track-creation-design.md) → [历史身份](../free-track-history-core.md) → [插入预检](../track-insertion-plan.md)。
- [主窗与画布](../track-placement-ui.md)、[显式新增另存](../mainwindow-created-save.md)。
- [核心审查](../track-core-boundary-review.md)、[主窗保存现场](../parallel-save-hardening-live.md)、[显式新增现场](../mainwindow-created-save-live.md)。
