# 健康采样验证：采样有效，真实心跳滞后仍未解决

本轮限定诊断取证目标 **succeeded**：双健康开关在新隔离服务明确启用，5444条实际健康采样逐行重算一致；一个GUI组首图0/0→最终图1/1、两回调和空stderr及全链正常退出证据完整。**健康稳定性未通过**：3次真实心跳年龄超过原1秒阈值，两次看门狗fail-open仍发生。心跳先读不能消除真实滞后，具体底层原因与历史全部截图拒绝根因仍unknown，不能把本Task结果称为可靠性修复通过。

本轮Task `task_2e0cc599ee61`、Dispatch `ctx_95024c79b018`、Run `run_e136aa13bab5`；保留Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`的环境、JSONL及实际assistant均核对`deng/gpt-6.1-sol high`。分支`verify/control-health-validation`从已结算日志组`b239aba514b54f68954e582380be170388cf9e54`建立，证据`../../verify-text-screen-sol/.local-analysis/control-health-validation/`，旧任务/证据不改。本轮只提交本报告，不合并推送。

准备差分只有新身份/批准路径、`indicator_health_sampling=true`、`indicator_health_fix=true`和健康模块摘要校验，动作驱动及可复用测试窗与日志组字节一致。父在question `msg_aab787ac7be5`批准18驱动、4启动器（含control_indicator_health.py）、几何工具及77包manifest后才连接；健康模块摘要`6642363c162eb8fa143a47ceb7dbe72467ddf23fb34c8b1a79e7c1c8c6eb4ab4`。只做语法/字节/新批准核验，不重跑无变化产品或旧测试，父已有相关测试证据不与现场累加。原ControlToolGate、1秒阈值、故障拒绝与120秒门禁保持，没有向原安装部署或热改。

唯一窗口PID47340、birth`134376693621161223`、HWND7015642，UIA/原Desktop枚举前置通过。初始非目标前景h004未发Snapshot，完整120秒后原App恢复及显式resume成功。`0004`首图实际读0/0，原3840×2160/返回1920×1080/倍率2；物理rect `[1500,825,2874,1634]`包含点(2186,1256)。h008真实Click及h009 Ctrl+Shift+F8各一次，h010 `0007`最终图实际读1/1；两个回调分别落在对应工具call_tool起止内，计数1/0→1/1。窗口stdout/stderr均0字节、正常关闭终态1/1，无callback-error。没有第二组、连接、测试输入或人为冻结/改心跳制造故障。

trace有且仅一次`indicator-health-installed`，`heartbeat_first=true, phases=true, threshold_seconds=1.0`。采样记录的是实际判定使用值，逐行校验read_order、alive/stopping/error短路、`age=now-heartbeat`及`healthy=(0<=age<=1)`；5444行全部一致、mismatch0，年龄最小0.0000146秒、最大1.0781844秒，负年龄0。本次没有indicator-none/线程死亡/stopping/error短路样本，不把未出现路径称为现场覆盖。5441次healthy、3次stale如下。

| monotonic判定时刻 | 心跳年龄（秒） | 线程 | 当时可见阶段 / phase_age（秒） |
| --- | ---: | --- | --- |
| 853268.4351185 | 1.0048655 | windows-mcp-input-watch | layer.set_opacity / 0.1240624 |
| 853268.5084374 | 1.0781844 | windows-mcp-input | pump-messages / 0.0000357 |
| 853589.2920167 | 1.0193396 | windows-mcp-input-watch | layer.set_opacity / 0.1105856 |

第一/第三条同线程后续分别在853268.4824420、853589.2925376记录`control.py:_watch:554`的fail-open，原已求值`indicator_ok=false,desktop_ok=true`，活控制线程及指示层仍alive。这个链证明本次真实过期导致原健康拒绝路径可达，不是伪负年龄；第二条输入线程false不另推断一个_watch事件。两成功Snapshot与随后fail-open的时间邻近不证明截图因果，更不能证明所有历史CONTROL_UNAVAILABLE来源。

32条慢阶段（>=0.05秒或异常时记录）：_build_layers1、change-and-acknowledge5、_monitor_rects2、layer.set_opacity9、layer.hide2、pump-messages13；均无异常。最长pump-messages约0.4996500秒，最长_monitor_rects约0.4354969秒。健康采样有597次观察到阶段，包含健康时的_build_layers/_monitor_rects/layer/pump等；4847次阶段为空，标为阶段unknown。可见阶段及phase_age只是采样时的关联，不足以将整个超过1秒间隙归因于透明度API、单个阶段、累积工作或系统调度中的某一项。

完整trace247057行，末尾trace-closed/dropped0，未报告写入错误；包括5444健康样本、32阶段、130743条input-processed、110201条hook-event、288对rehook-recovery。高频诊断开销可能改变调度，没有无诊断同条件对照，不能外推为原工具长期性能或历史故障必然原因，不归因用户。日志零丢失仅支持本次记录完整，phase空值、精确底层慢因及长期可靠性仍unknown。

关闭优先Alt+F4，但h011前检非目标，executed=false、没有调用该关闭Shortcut。完整120秒后h012仅对本Popen精确身份一次WM_CLOSE生命周期正常关闭，原日志normal-close/mainloop-returned1/1，h013原Popen确认exit0后退役；没有再向已死窗口发送消息，没有日志组的多余生命周期请求。五链44840/61712/63132/64700/72612停止前持有精确创建时间句柄，h014正常stop后全部exit0，UIA探针exit0，termination_calls0。原failed/token/budget/截止保留，2次Guard退避审计`early_requests=[]`。父独立持有窗口及链身份也全部exit0，并独立验证健康/回调时序；图像内容由指定工作者实际读图，父审计不冒称父读图。

最终18驱动、父4启动器及几何摘要相符；原安装与隔离包各77文件、稳定22/固定23/实验22部署的文件名集合/字节/SHA前后保持。稳定/dist仍0.10.0，main未操作，未启动固定/实验候选或NET/铜竞争，工具小窗不替产品验收。下一步只建议有界离线研究真实心跳更新间隙和诊断开销，不能放宽阈值、关指示层或增加未批准现场轮次。

本地证据入口（Git忽略目录）：

- [模型/会话](../../verify-text-screen-sol/.local-analysis/control-health-validation/model.json)、[差分与18摘要](../../verify-text-screen-sol/.local-analysis/control-health-validation/checkpoint-offline.json)、[新客户端批准](../../verify-text-screen-sol/.local-analysis/control-health-validation/phase-two-approval.json)、[父健康批准](../../verify-text-screen-sol/.local-analysis/control-health-validation/parent-audits/health-approval.json)。
- [首图0/0](../../verify-text-screen-sol/.local-analysis/control-health-validation/0004-Snapshot-00.png)、[最终图1/1](../../verify-text-screen-sol/.local-analysis/control-health-validation/0007-Snapshot-00.png)、[窗口回调原件](../../verify-text-screen-sol/.local-analysis/control-health-validation/window-events.jsonl)、[窗口stderr](../../verify-text-screen-sol/.local-analysis/control-health-validation/window-stderr.log)、[回调审计](../../verify-text-screen-sol/.local-analysis/control-health-validation/callback-audit.json)、[原工具调用起止](../../verify-text-screen-sol/.local-analysis/control-health-validation/actual-calls.jsonl)。
- [完整controller trace](../../verify-text-screen-sol/.local-analysis/control-health-validation/controller-trace.jsonl)、[逐行健康/阶段/fail-open审计](../../verify-text-screen-sol/.local-analysis/control-health-validation/health-sample-audit.json)、[父健康独立审计](../../verify-text-screen-sol/.local-analysis/control-health-validation/parent-audits/health-independent-audit.json)、[父回调独立审计](../../verify-text-screen-sol/.local-analysis/control-health-validation/parent-audits/health-callback-independent-audit.json)。
- [精确生命周期关闭](../../verify-text-screen-sol/.local-analysis/control-health-validation/lifecycle-close-result.json)、[Popen exit0](../../verify-text-screen-sol/.local-analysis/control-health-validation/window-exit.json)、[五链句柄exit0](../../verify-text-screen-sol/.local-analysis/control-health-validation/chain-exit.json)、[父退出见证](../../verify-text-screen-sol/.local-analysis/control-health-validation/parent-audits/health-chain-witness-state.json)、[门禁审计](../../verify-text-screen-sol/.local-analysis/control-health-validation/control-audit.json)、[完整性](../../verify-text-screen-sol/.local-analysis/control-health-validation/integrity-result.json)、[限定结果/unknown](../../verify-text-screen-sol/.local-analysis/control-health-validation/verification-summary.json)、[证据索引](../../verify-text-screen-sol/.local-analysis/control-health-validation/evidence-index.json)。
