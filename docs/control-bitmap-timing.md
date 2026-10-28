# 位图上传计时现场：门禁受阻，未进入有效上传路径

本轮 **failed**：唯一诊断组在首图前非目标前景被阻止，完整120秒后恢复前ControlStatus为user；到期唯一诊断仍为user，故停止本组。实际Snapshot、Click、Shortcut均0，没有位图上传样本，不能判计时模块通过、失败或给出API成本；上传成本结论为unknown。未追加组或连接，窗口与整链在t0后约14分06秒正常退出，未超过本次30分钟许可。

Task `task_371c96f46645`、Dispatch `ctx_1aa4e6fd282a`、Run `run_3da0a4eb0ac6`；分支`verify/control-bitmap-timing`基于fetch后`origin/dev=c80a7fe98bfba2ce47370bf1a40718b74d2bbb90`。原Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`的环境、JSONL和实际assistant均核对`deng/gpt-6.1-sol high`。父source-ready后核对新client及18文件/5启动器、几何/健康/位图摘要、77包清单，question `msg_7ddce2e6e885`新双批准通过才启动；本次用户“你先控制电脑”承接30分钟方案，不是等待新授权。只提交本报告，不改父tools/tests、不合并推送。

服务启动前记录t0 monotonic `859112.2685206`及墙钟，诊断截止`860612.2685206`（25分钟）、收尾截止`860912.2685206`（30分钟）。client在请求、工具调用前核对截止，原120秒、失败锁存、归属、image要求与ControlToolGate保持。新窗口PID72448、birth `134376756476732010`、HWND7014688；UIA CanMinimize/CanMaximize及原Desktop枚举通过，探针只读无激活/输入。没有产品候选或其他工程窗口操作。

| 事件 | 本次结果 |
| --- | --- |
| b004首图 | 原生前检非目标前景，executed=false，未调用Snapshot，完整120秒静默 |
| b005一次恢复 | ControlStatus user/generation2/wait约9.996秒，恢复动作未发送，预算refused=true；完整120秒静默 |
| b008唯一诊断 | 同连接ControlStatus仍user/generation4/wait约9.9999秒，再锁存120秒；不再复查或恢复测试 |
| b009/b010 | 最后截止后仅本Popen精确PID/birth/image/HWND/title/class一次WM_CLOSE生命周期正常关闭，原Popen exit0退役 |
| b011 | stop前持有完整五链精确句柄，正常stop后全部exit0；trace关闭时t0后845.7586秒，链退出墙钟约846.3614秒 |

两个ControlStatus是实际原工具返回，is_error=false但状态不允许，不能当作控制成功或归因用户正在操作；原structured diagnostics和文字完整保留。没有App、截图或输入探测，未重发已执行动作，没有换入口、force ready、改阈值、故意冻结线程或伪造慢上传。窗口仅window-ready、normal-close、mainloop-returned，计数始终0/0；stdout/stderr均空，不冒称取得首终图或两输入回调。

trace338863行，末尾trace-closed/dropped0，未报告写入错误。确认`indicator-bitmap-timing-installed`的schema_version1、scope=`windows-mcp-control-indicator`、pixel_contents_recorded=false；health installed为heartbeat_first=true/phases=true/threshold_seconds1.0。**indicator-bitmap-upload为0**，因此尺寸/字节/各API次数与时间、总耗时、API百分比、top慢上传、异常路径和正常SelectObject2次/所有清理完整性均无样本可验。不能把空集合写成API成本为零或清理通过；仅确认模块加载，未进入有效计时范围。

3209条健康样本逐行重算一致，均healthy，age约0.0000154～0.0640978秒；phase记录0、fail-open0。指示层未进入active上传范围，这不证明上传健康稳定或历史截图故障已修。trace另有152935 hook-event及182371 input-processed，高频诊断可能影响调度，不据这些事件归因用户或识别未采集的行为来源。

三次120秒退避审计`early_requests=[]`；原failed=`b004-initial`、token=`b001-launch`、budget及截止归档不清。窗口与UIA探针exit0；五控制链17108/21748/63564/69412/70256在停止前持有创建时间匹配句柄并全部exit0，termination_calls0。父另持有含窗口等五身份独立确认exit0。窗口关闭仅生命周期，不作GUI验收证据。源窗口为与父相同的CRLF副本；工作区临时换行对齐在全链退出后恢复，无可复用代码变更入提交。

父独立审计与本地审计一致：18驱动、5启动器及几何摘要未变，原安装/隔离包各77文件、稳定22/固定23/实验22部署文件名集合/字节/SHA前后保持。稳定/dist仍0.10.0、main不动；固定候选和NET/铜竞争未通过状态不变。本次机会已消费，无慢复现也不追加现场，完整API成本仍待另有明确范围。

本地证据入口（Git忽略目录）：

- [模型/原会话](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/model.json)、[冻结清单](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/checkpoint-offline.json)、[新客户端批准](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/phase-two-approval.json)、[父批准](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/parent-audits/approval.json)、[t0与截止](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/runtime-limits.json)。
- [第一次状态原回执](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/0002-ControlStatus-raw.json)、[唯一诊断原回执](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/0003-ControlStatus-raw.json)、[实际调用起止](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/actual-calls.jsonl)、[完整trace](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/controller-trace.jsonl)、[位图无样本审计](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/bitmap-audit.json)、[健康样本审计](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/health-audit.json)。
- [窗口终态日志](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/window-events.jsonl)、[窗口stderr](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/window-stderr.log)、[Popen exit0](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/window-exit.json)、[五链句柄exit0](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/chain-exit.json)、[门禁及运行时限审计](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/runtime-audit.json)、[完整性](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/integrity-result.json)、[父独立审计](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/parent-audits/independent-audit.json)、[限定结果](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/verification-summary.json)、[证据索引](../../verify-text-screen-sol/.local-analysis/control-bitmap-timing/evidence-index.json)。
