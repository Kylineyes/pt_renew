# 当前能力与推进顺序

本页汇总当前状态；[文档导航](docs/README.md)按软件主题解释模型、实现与证据，[HANDOFF](HANDOFF.md)提供接手步骤。历史阶段进度已移至[原根进度记录](docs/history/root-progress.md)，其中版本和“当前”措辞按原阶段理解。

## 当前软件能力

已发布 v0.11.0-alpha 是只读版；当前 dev 的产品源码沿用已测 d2ee381 基线，最近工作为菜单点击离线审计、文档组织及工程探索待办与协作规则，未发布新的编辑安装包。

| 软件部分 | 已完成 | 尚未完成／验证边界 |
| --- | --- | --- |
| [板图文件](docs/topics/board.md) | PCB 严格读取、图层预览、来源／布局、只读 pt-pcb-check | 全部历史变体、精确文字与部分轮廓、原软件兼容 |
| [交互与测量](docs/topics/interaction.md) | 统一命令、旧式及现代入口、选择、定位、测量、端点捕捉 | 最大板图性能及制造测量验收 |
| [编辑保存](docs/topics/editing.md) | dev 自由 FT 移动／删除、历史、保存点、全新目标另存；内部显式新增闭环 | 正式新增门 false，默认 Created 拒绝，有 NETDEF 的新增拒绝，覆盖保存未开放 |
| [封装库](docs/topics/library.md) | LIB 只读浏览、筛选及字节来源 | 放置／替换／元件编辑、库写入及原软件完整对照 |
| [网络检查](docs/topics/connectivity.md) | NET / NETDEF 受限读取、引脚映射、受限铜分析 | 真实 NETDEF、几何覆盖、完整 DRC、布线与生产输出 |
| [原软件研究](docs/topics/legacy.md) | 菜单及文字局部证据、输入语义、两槽取证与最新离线点击审计 | 连续客体图、当前文件状态、自建单线保存重开、默认字段 |

## 已有验证与最新增量

- 固定产品候选 Debug / Release 各 24/24 CTest；核心定向审查另有 82 passed（含初始化／清理），范围见[技术交接](docs/agent-handoff-20261104-capture.md)。
- [真实 Qt 核心现场](docs/parallel-save-hardening-live.md)及[内部显式新增另存现场](docs/mainwindow-created-save-live.md)各有独立证据，不扩展为正式新增或原软件兼容通过。
- [最新点击审计](docs/native-menu-click-audit.md)完成第二槽原图、坐标、RPC、前景及原会话对齐，三项原 AST 假鼠标验证通过。没有自动乘二，前景变化根因仍未定。
- 两槽原软件捕获均 failed，guest PNG 为 0，NEWFT 未生成；正常退出证据保留。没有新的 GUI 通过结论。

本文档整理只调整阅读结构与现有结论的入口，没有改变产品或重跑完整构建／CTest。测试数字均保留各固定候选与原执行范围，不累加成当前整体覆盖数量。

## 工程探索队列

工程未知、缺证和待设计规则已归并到[探索待办](docs/exploration-backlog.md)，每项与原文细节双向链接。探索 agent 按[领取与沉淀规则](docs/exploration-workflow.md)领取、扩展阅读、修正文档、追加新未知；完成后把知识写回文档并删除事项。

当前取证主线从 [EX-001 菜单点击期间的前景观测](docs/exploration-backlog.md#ex-001)开始，再依赖连续客体图、单线默认编码和正式新增接入。队列不是产品已开放能力表，既有失败与验证范围仍按上文保留。

## 后续按依赖推进

1. [最小只读观测候选已完成离线验证](docs/native-menu-click-audit.md#readonly-observer-offline)，10/10 假 API 通过但没有实机兼容或动作后验；EX-001 保留，下一步按明确假设另行组织短现场，不盲改坐标。
2. 据明确诊断目标安排短现场，先建立一次可靠菜单动作后验，再取得两轮新 640×480 客体 PNG 并实际读取。
3. 核实 Information / Status 的工作文件名和图元计数；确认空板、层宽端点后新建单段，另存全新 8.3 文件并由原 AUTOTRAX 重开。
4. 将字节、图像、日志和参数共同核定的默认策略接入已有显式实现，开放唯一能力门，再做正式产品入口及输出重开验收。

库放置、完整 DRC、布线及生产输出按各主题的研究缺口推进；没有前置证据时不重复搭建已有新增核心或扩展通用控制框架。

## 查详细依据

[技术交接](docs/agent-handoff-20261104-capture.md)集中保留固定候选、当前任务边界、并行约束与本机材料路径；[完整索引](docs/reference-index.md)提供各阶段报告。旧交接、计划和失败均保留，历史批准不自动成为新现场批准。
