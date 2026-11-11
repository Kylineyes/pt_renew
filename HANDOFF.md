# 开发接手步骤

先读[当前能力](PROGRESS.md)，再按[软件主题](docs/README.md)选择本次问题。本页提供操作顺序；详细材料、原会话与现场约束集中在[技术交接](docs/agent-handoff-20261104-capture.md)，最新增量为[菜单点击离线审计](docs/native-menu-click-audit.md)。

## 最短阅读路径

1. 阅读[AGENTS](AGENTS.md)，确认语言、独立分支、原件保护、临时材料复用和验证要求；探索任务先按[工作规则](docs/exploration-workflow.md)从[工程逻辑待办](docs/exploration-backlog.md)领取一项，登记并同步归属。
2. 核对实际 git status / log 与 origin/dev；分支或历史文档中的 SHA 不代替实时状态。
3. 阅读[PROGRESS](PROGRESS.md)了解已完成与阻塞，再进入相关主题。当前 FT 默认字段及正式新增缺口读[编辑保存](docs/topics/editing.md)和[原软件研究](docs/topics/legacy.md)。
4. 需要继续现场时完整读取[技术交接](docs/agent-handoff-20261104-capture.md)、[两槽结果](docs/native-capture-checkpoint.md)和[最新审计](docs/native-menu-click-audit.md)；不能直接运行旧计划或恢复旧 GO。
5. 选定具体变更后，从最新 dev 建独立分支，复用已有实现、工具、可用会话与构建，按对应模块验收，再 no-ff 合 dev 并推送。main 由用户操作。

## 接手时优先确认的边界

普通 dev 已有载入自由 FT 编辑和受限另存；内部显式新增闭环也已完成。正式新增门仍 false，默认 writer / 主窗拒绝 Created，有 NETDEF 的新增仍拒绝。先补原软件单线保存重开和默认字段依据，再复用显式路径，不重做模块或直接翻门。

最新离线审计已排除 Click 自动应用截图比例的路径；没有确定点击期间前景变化的根因。[首轮四项独立探索](PROGRESS.md#工程探索队列)已沉淀只读观测候选、宏／Repeat／Un-Delete 静态模型、FT extra 读写与局部消费者、LIB 目录状态。EX-001／006／008／017 全部保留受阻，不恢复已结算任务追通过。下一步消费这些报告，按具体剩余条件研究或组织有明确问题的短现场；本轮模型授权为四个 Pi 会话均 `deng/gpt-6.1-sol high`，长期模型分工仍按 AGENTS。

## 本机材料和工程环境

本机工作区为 C:/Users/rikideng/orca/workspaces/pt_renew/main-2。忽略目录入口 .local-analysis/CURRENT_AGENT_HANDOFF.md、可发送提示词 .local-analysis/handoff-capture-20261104/NEW_SESSION_PROMPT.txt；菜单审计材料在 .local-analysis/native-capture-checkpoint/，现场原件在技术交接指定的相邻工作树。远端 clone 不包含这些材料。

开始先盘点工具、依赖、归档和 build；不为接手复制整套现场。冻结材料、原图及失败记录保持只读，旧原件及唯一输入不做写入试验。Qt 环境与命令见[工程主题](docs/topics/engineering.md)和[开发环境](docs/qt-development.md)。

## 历史与深入阅读

[完整资料索引](docs/reference-index.md)按软件问题查证据。原根交接全文保存在[历史交接](docs/history/root-handoff.md)，旧会话长记录保存在[历史会话](docs/history/root-session-handoff.md)，旧进度在[历史进度](docs/history/root-progress.md)。它们用于追溯阶段，不作为当前能力表或可执行现场指令。
