# 并行推进与父验收：原软件短观察和新增核心

本轮按用户要求分三个独立方向派发 Pi，由父协调者验收。从 `dev=origin/dev=3fd6e5fa2b241ef8c61bf6ecd7b46c4839b34be6` 建立集成分支 `feat/native-evidence-wave`，Run 为 `run_b8a733941bf1`。

**已完成新增核心无修复审查和原软件短观察的离线方案；没有取得新的连续客体截图、文件状态或单线保存重开样例。** GLM 静态路线遭配额失败，原软件路线因连接错误与明显延迟没有进入现场。产品源码不变，默认 FT 字段仍未知，普通新增入口继续关闭。

## 分工与文件所有权

| 方向 | 分支／工作树 | 修改范围 | 实际指定模型 |
| --- | --- | --- | --- |
| 原软件短观察及单线样例 | `verify/native-short-observation`／`native-startup-diagnosis` | 仅新专题报告、全新忽略证据目录；本次实际交付离线报告与材料 | 沿用 Pi `deng/gpt-6.1-sol high` |
| 默认 FT 字段静态数据流 | `research/native-ft-defaults`／`research-native-ft-defaults` | 仅新静态报告及隔离分析目录；实际零工具、零修改 | Pi `glm/glm-5.3 high` |
| 新增核心边界审查与必要修复 | `fix/track-core-boundaries`／`review-track-core-boundaries` | 三个 application 模块及对应测试、独立报告；实际仅提交报告 | Pi `deng/gpt-6.1-sol high` |

三个方向不共享写入文件、构建或证据目录。父维护综合报告、进度入口和集成，不在子任务执行期间直接编辑子工作树。UI、writer、reader、codec、planner 和根 CMake 没有交叉修改；本轮也没有修改这些文件。原软件与 Qt 桌面串行，本次没有放行任何新桌面现场。

## 已验收：新增核心审查

`task_232eecda5bd4`／`ctx_d37c6bae647f`，Pi 会话 `01a1a161-c684-75ff-8e81-5918e22bf0ce`。父核对原 JSONL 的模型／推理事件、实际 assistant 与成功工具均为 `deng/gpt-6.1-sol high`。报告提交 `2220e02f28788945964d96edec8b1826a5f71f35` 只有 [新增核心边界审查](track-core-boundary-review.md)，已 no-ff 合入集成分支。

| 本轮定向验证 | 结果 | 原创建调用同步等待 |
| --- | --- | --- |
| Debug 核心 CTest 三组 | 3/3；QtTest 分别 11、25、28 passed | 退出 0，0.8598324 秒 |
| EditingTests 四个核心槽 | 12 passed | 退出 0，0.9726023 秒 |
| 消费者通知／失败路径四槽，offscreen | 6 passed | 退出 0，1.4996648 秒 |

合计 82 passed、0 failed、0 skipped，含各进程初始化与清理，不是 82 个独立功能。公开 API、不可变工作快照、同线程串行调用条件下，未发现需要修复的可复现功能缺陷。非法 begin 保留原有效预览是既有失败保持契约；提交路径仍复核文档／修订，现有消费者有换图、改层等主动取消通知。本轮没有为产出硬改，也没有添加无缺陷依据的测试或框架。

父独立阅读相关源码与测试契约，复核三份原测试日志及退出记录，并逐项核对 11 个源码／测试、5 个 EXE 和 13 个证据条目摘要。父本地审计脚本初版以子串 `0% tests passed` 误匹配 `100% tests passed`，首次失败保留在父会话；改为行首判断后通过，没有修改子原日志。验收只接受无修复审查与所列定向结果，不扩大为真实 GUI 或原软件兼容通过。

报告提交没有改变受审源码。历史 Debug／Release 各 24/24 保持原冻结候选范围，本轮没有重跑完整矩阵；offscreen 模态／通知验证不替代真实桌面、原生另存为或菜单 F3 验收。

## 失败：GLM 静态路线

`task_cf496b960677`／`ctx_a701fac57fcd`，Pi 会话 `01a1a161-c8dc-70df-8ad5-63ec2b17af3d`。原模型／推理事件为 `glm/glm-5.3 high`；三次原始错误为 `exceed quota limit`，最后一次为 `model concurrency limit exceeded`。四条 assistant 都是空内容错误，工具调用及工具结果均 0，没有产生静态报告或 worker_done。

父依据原 JSONL 最终错误和自动重试结束记录 abandon，再将 Task 明确记为 failed。没有替换模型、修改 provider 记录或重派绕过配额。abandon 的 `processAction=none` 只保留资源，不代表 Pi 操作系统进程退出；本轮没有增加 FT 默认字段证据。

## 未完成：原软件现场；已交付离线短方案

`task_53dde472a74d`／`ctx_5712b8eb277d` 沿用 Pi 会话 `01a19f6a-a52d-7333-95f3-2972829f4e9f`。原模型与推理事件、实际 assistant 及成功工具均核对为 `deng/gpt-6.1-sol high`。[子任务离线报告](native-short-observation.md) 提交 `1ea54249b2ad80206f892d873b756e444a3af30f` 只有该报告，父核对后已 no-ff 集成；唯一 worker_done 明确为 failed，父按真实目标未完成验收、release 并 ack。本轮先出现 Connection error／Request timed out，恢复后仍有数分钟的工具间隔，最长约 14 分钟；这些完整间隔包含模型请求、重试和调度，不能全部归因于纯推理耗时。

父在目标／服务启动前收敛为离线交付，没有给 GO。新分支上产生四份忽略材料：`prepare_offline.py`、`session-audit.json`、`reference-materials.json`、`short-plan.json`。方案 SHA-256 为 `72817fd675ef36fe5395296dd068b8fd304463d2ffaad2887479367d62232eb1`；父核对 9 项旧参考文件大小／SHA，确认脚本仅提取会话与参考材料，没有运行旧驱动、启动目标、建立服务或请求桌面。

短流程先以 F11+P 单次捕获，确认动作后新增非空的 640×480 客体 PNG 并实际 read，再独立捕获第二张、确认新文件并实际 read；连续观察可靠后才按图进入菜单、核对文件名与计数，并在父检查点之后尝试单线。旧 Shift+I／Shift+S 请求只作已有公开输入路径依据，不预排未知菜单业务。

这份方案**不是可执行新现场冻结**：新 slot、驱动／submit 的新上下文绑定与离线验证、原始输入／副本摘要、实时时钟起止仍须届时具体准备。拟议 30 分钟含最后 7 分钟正常收尾；当前调用延迟不足以可靠支持逐图判断和按时关闭，父于本轮回复要求只交离线结果、单线目标按 failed 结算。没有启动新目标或控制服务，不存在本轮目标迟到关闭事实。

父本轮独立读取历史 retry-01 的 Capture 菜单原图和 `captures/pt_000.png`：菜单显示 Take screenshot 为 F11+P、Take raw screenshot 为 F11+Ctrl+P；640×480 客体图是 AUTOTRAX 1.57 启动页，显示 PRESS ANY KEY TO START，没有工作文件名或图元计数。旧图复读仅核对后续方案依据，不计作本轮连续两图、快捷键实际触发或单线保存重开通过。

## 后续与证据入口

原软件路线应先恢复能持续完成工具与实际读图的同一指定 Pi 会话，再具体冻结新 slot；从连续两张客体图和文件状态开始，不重启旧服务、复用旧 inbox 或以历史 PID 收尾。默认 FT 编码仍必须以原 AUTOTRAX 新建、保存和重开的真实字节核定；可用正式 `pt-pcb-check` 只读核查结构，但严格解析不等于兼容。证据充分后才复用现有显式路径接正式新增入口，新增 NETDEF 仍拒绝。

父证据根为 `main-2/.local-analysis/native-evidence-wave/`，包含三路 spec／start 原回执、`session-audit-current.json`、GLM 失败结算、`parent-core-audit.json`、`parent-native-offline-audit.json`、`parent-image-review.json` 与最终 Git／任务结算。子核心证据在相邻工作树 `.local-analysis/track-core-boundary-review/`，原软件离线方案在相邻 `native-startup-diagnosis/.local-analysis/native-short-observation/`；均不提交原软件、截图或忽略材料。

任务结算及最终 dev／origin/dev SHA 以父忽略目录 `final-state.json` 为准。核心 succeeded、GLM failed／Dispatch abandoned、原软件 failed 均已结算，父已处理两份唯一 worker_done。外部 Pi 终端 release 的 retained／processAction none 不等于 Pi OS 退出；最终收件箱和 reclaimable 核对另存父结算记录。
