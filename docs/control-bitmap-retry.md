# 位图重试：初始观察通过，首图本地前景拒绝

本轮 **failed**：已有日志的初始保守观察通过，但唯一组首Snapshot前本地检查发现前景为Orca，目标测试窗存在却不在前景；动作未发送。实际ControlStatus/Snapshot/Click/Shortcut均0，位图上传0，API成本、慢上传及清理验证均为unknown。不能把本轮写成工具user拒绝、推断焦点变化来源，或声称计时/历史故障修复通过。

Task `task_ab514403da21` / Dispatch `ctx_ab825328a37d` / Run `run_bdf0b619f1e3`；原Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`的PI环境、JSONL及实际assistant核对`deng/gpt-6.1-sol high`。分支`verify/control-bitmap-retry`从`origin/dev=8760c4a18d8262f021925e27e1c371f6a5f3a874`建立；父source-ready后核对19驱动、5启动器/几何与77包清单，question `msg_43db13909bac`新双批准通过才启动，不复用旧任务/授权或重跑旧矩阵。

用户“允许”绑定15分钟方案。t0=`864350.2037088`，10分钟诊断/15分钟收尾硬截止；初始仅读已有trace约10.293秒后ready=true，健康日志新鲜且10秒无输入记录，Launch前被动复核也通过。这只是附加观察，不保留ready、不保证前景、不替代原门禁。唯一窗口PID20332/birth`134376810533515725`/HWND7276816及UIA原枚举通过；首图原生快照显示Default桌面、未锁、前景稳定，但前景是PID23024的Orca，故r004 executed=false。按本轮首次拒绝即消费机会，没有App恢复、快照重试、诊断或第二组。

完整120秒截止后，仅精确本Popen身份一次WM_CLOSE生命周期关闭；窗口ready/normal-close/mainloop终态均0/0，stdout/stderr空，Popen及UIA探针exit0。五链32424/43724/46972/49120/68512在收尾前持有匹配创建时间句柄，正常stop后全部exit0，无强杀；trace关闭t0+507.072秒（8分27），链退出墙钟约507.597秒，在15分钟内。早期只读见证120秒到期仍活的记录另名保留，最终退出依据是重新持有句柄后的实际exit0，不用缺失推断死亡。

trace2136行正常closed/dropped0，bitmap installed scope=`windows-mcp-control-indicator`及health heartbeat_first/phases/1秒阈值标记齐全；1925条实际健康采样逐行一致，false0、phase0、fail-open0。没有indicator-bitmap-upload，API次数/百分比/尺寸/字节/异常和SelectObject2次及清理完整性均无样本，不将空集当通过。父独立审计一致；原19驱动/5启动器/几何、原安装77/隔离77与稳定22/固定23/实验22部署摘要前后不变，门禁审计early_requests空。

本次只提交本报告，不改父tools/tests、不合并推送。稳定/dist仍0.10.0、main及产品NET/铜竞争未通过状态不变；窗口机会已消费，不再追加现场或新连接。

- [模型/会话](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/model.json)、[新批准](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/phase-two-approval.json)、[初始观察](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/initial-observation.json)、[首图前景原件](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/events/00009-native_result.json)、[空实际调用日志](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/actual-calls.jsonl)。
- [完整trace](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/controller-trace.jsonl)、[无上传/健康审计](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/bitmap-audit.json)、[运行时限与门禁](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/runtime-audit.json)、[窗口终态](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/window-events.jsonl)、[窗口stderr](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/window-stderr.log)、[Popen exit0](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/window-exit.json)、[五链句柄exit0](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/chain-exit.json)。
- [父独立审计](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/parent-audits/independent-audit.json)、[父退出见证](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/parent-audits/bitmap-chain-witness-state.json)、[完整性](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/integrity-result.json)、[限定结果](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/verification-summary.json)、[证据索引](../../verify-text-screen-sol/.local-analysis/control-bitmap-retry/evidence-index.json)。
