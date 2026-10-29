# 归档图片顺序阅读演练：准备阶段未执行

2026-10-29，为评估冻结60秒门闩内两次实际读图的可行性，单独安排纯离线演练。Run `run_468e4cf9cbed` / Task `task_75f8102028b0` / Dispatch `ctx_1bed19e5ff05`，独立分支`verify/async-image-review-rehearsal`来自`dev=77d81d6`。演练未开始，Task已记录failed，Dispatch记录failed、worker状态abandoned；没有worker_done，父未伪造完成消息。放弃回执processAction=none，可能仍活的Pi终端保留，reclaimable为空。

沿用Pi `deng/gpt-6.1-sol high`，session `01a18648-535d-720b-998d-63e4e0d5c42b`，实际环境及原JSONL错误记录模型一致。[环境原件](../.local-analysis/async-image-review-rehearsal/environment-before.json)保存PI字段；[父会话快照](../.local-analysis/async-image-review-rehearsal/parent-session-final.jsonl)及[未执行审计](../.local-analysis/async-image-review-rehearsal/parent-unexecuted-audit.json)保存8条本Task期间模型连接失败/Request timed out记录。首次三次重试失败后只沿原会话继续准备，没有另起模型或新Task绕过不可用；随后连接错误再次发生，父明确取消尚未开始的可选演练并封存监督上下文。

演练意图仅是：准备完成后request-1→指定会话实际read历史门闩图A→ack-1→request-2→实际read历史取消后图B→ack-2，并从request-1持久化到ack-2保存完整耗时。不启动产品、不截图、不设置release/cancel或键鼠。A为历史`0012-Snapshot-00.png`，B为历史`0017-Snapshot-00.png`；B本来就是取消后的事后图，不能重称为门闩内编辑证据。源图SHA分别`cfc5b6d131c0a3eb101bfd6ce61af00e759c3cb43185d980ca9f9d77ca721879`、`d19a49589be94668e822ad4cb98d470c5776d820625f86749db0f0a006b1d480`，前后未变。

准备脚本`rehearsal.py`最初错误地从assistant顶层读取thinkingLevel，随后在request开始前改为message字段；父又指出将indent多行JSON误按JSONL读取的缺陷。当前准备脚本及失败原件保留，**未经过完整契约验证，不应直接运行**。没有request-1/request-2、ack-1/ack-2、start或timing-result，实际image read为0；不能报告“读图超过60秒”或“60秒可行”，可行性保持unverified。准备阶段的长耗时与模型错误也不能换算成一次已开始演练的用时。

父侧另完成[产品竞争离线预检](async-race-offline-preflight.md)及10项审计测试，冻结产品/输入/历史对照/旧失败原件未改。本次演练没有产生新的实际图像观察、产品GUI或时序通过，产品启动0、桌面请求0。下一步先实现并测试read/ack和产品原Popen/Qt模态正常退出关口，指定模型可用且满足冻结时限设计后再另立任务；不恢复本Task，不自动替换模型或启动产品竞争。

本报告由父协调器根据原记录整理，worker未提交报告或宣称完成。准备文件原件在`../verify-control-owned-close-live/.local-analysis/async-image-review-rehearsal/`，父副本在`.local-analysis/async-image-review-rehearsal/`；模型错误/Orca结算回执及父审计源在`.local-analysis/async-race-offline-preflight/`。保留终端不等于本Task仍活，不能再次投递旧Dispatch；后续若直接由用户明确要求新工作，须以新上下文处理。
