# 独立异步实验候选GUI验收：受控阻塞

本轮未完成NET/铜层真实GUI对照与竞争验收。NET正向对照在打开B之前遇到`user`并中止，三个完整180秒截止后的只读复查仍被拒绝；父要求停止自动桌面计划并保留原连接及候选。**本Task结算failed，正常关闭和清理未完成，不能宣称实验或固定0.11.0候选通过。** 稳定产品保持0.10.0。

## 对象与离线准备

- Task：`task_173ed3eebb79`；Dispatch：`ctx_f4aea03b6bef`；Run：`run_de333c61159e`。
- 工作分支：`verify/async-experiment-gui`，从fetch后的最新`origin/dev`建立；只提交本报告，不合并、不推送，不操作main。
- 原Pi会话：`01a1739a-82f6-76cf-9ffc-c63e95be56d4`；环境、JSONL最后模型/推理及最近assistant记录均为`deng/gpt-6.1-sol high`，未换模型或新建会话。
- 实验源码HEAD：`c4e3ec5e82bf1a022e523ec8844d0665d7b93234`，代码`98a4321`；部署EXE SHA-256：`782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`。
- 本轮证据根：[async-experiment-gui](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/)。原固定EXE仍为`dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8`；没有替换实验部署、固定候选或稳定dist。

完整读取主工作区AGENTS、SESSION_HANDOFF、异步实验开发报告及边界协议后，复制旧驱动到新目录，原件保存provenance；没有修改旧材料。新客户端只接受当前Task/Dispatch、实验SHA、新证据根及本轮批准摘要。通用`CONTROL_*`完整180秒静默、失败锁存、唯一动作ID、不排队、image必需、已执行输入不重发及显式目标恢复均保留。每步核对PID/HWND/映像/创建时间；主窗口按实验标记和绑定HWND识别，目标原生或同类Qt对话框不误当画布。

[最终离线摘要](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/offline-summary.json)82项通过（原61项加本轮21项适配），0失败/错误/跳过，真实候选启动和桌面请求均为0。父独立复验同样82项通过并冻结28文件，见[父审阅](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/parent-audits/offline-review.json)；初次摘要刷新时差保留，没有用旧摘要替代最终源码审阅。父明确批准`msg_d8e9399a8547`并写本轮[phase-two-approval.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/phase-two-approval.json)后才启动现场，未复用旧批准。

新增运行路径包括`ExperimentSession`四次生命周期预算、持续owner/Popen退出见证、输入/skip绑定，以及`CriticalSegment.run`逐步await Guard。关键段要求实际worker-entered/gate-ready、主HWND、截图载荷、新修订/dirty/零走线/A摘要、尚未返回，才release；失败只可本地cancel，禁止失败或忙碌时release。最终GUI仍须实际读图，不用日志替代。NET配置kind=net/skip=1，铜配置kind=copper/skip=0；每类对照失败不进入竞争，不补试。

## 实际现场与机会消费

实际客户端PID50048（launcher31708）持续持有候选Popen，也作为`--async-experiment-owner`。唯一启动为NET对照：候选PID2020、创建时间FILETIME`134374989405547867`；owner创建时间`134374989304233763`。单一MCP连接保持至阻塞交付，没有重连或运行时修改驱动。

a001启动成功；a002截图前归属检查发现QQ前景，截图和输入未发送，完整180秒静默后a003显式restore-target成功、a004显式resume。没有向QQ输入或重发Launch。实际屏幕3840×2160、返回1920×1080、比例2，坐标依据本次图像。

实际查看的[0007图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/0007-Snapshot-00.png)显示“独立异步实验构建”、`board.pcb`、隔离`a.net`来源、NET_A、两个唯一映射节点、3图元/1走线、clean修订2；来源摘要为`130e3b1e50c62762d72c57d73fc79955ec1d724c70cffad4ee0a9dd755baa974`，与A输入匹配。应用请求1成功读取A并callback-accepted，gated=false，符合skip=1；这只证明初始A加载，不是B正向对照通过。

随后最大化并打开NET原生文件框，实际查看0013图；Type后实际查看[0017图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/0017-Snapshot-00.png)，确认文件名为本任务隔离`inputs\b.net`。a009关键段在trigger预检即得到`user`，generation12、executed=false；打开点击未发送，没有B请求、gate-ready、编辑或release。关键段标记aborted/consumed，不把A成功或正确路径截图算B对照通过。

| 原定机会 | 实际结果 |
| --- | --- |
| NET正向对照 | 启动1次，触发B前控制争用中止；消费机会，未通过 |
| NET竞争 | 对照未通过，未进入，不追加NET运行 |
| 铜正向对照 | 原进程正常关闭持续受阻，按父收敛指令未进入 |
| 铜竞争 | 铜对照未进入，未进入 |

总预算4，实际启动1，有效对照/竞争时间线0。没有进入60秒门闩，因此没有“看门狗中止”或有效释放记录；本地关键段aborted与应用实验aborted事件是不同事实，不能混写。没有Delete、document-published或旧结果丢弃现场证据。

## 争用、停止与残留

a009记录截止`685059.1203961`；完整到期后a011只读ControlStatus仍user，generation22，重设`685456.1859052`。再完整到期后a012仍user，generation24，截止`685849.1802668`；再到期后a013仍user，generation26，截止`686259.8917363`。每次只发一次到期检查，没有短轮询；拒绝后未继续原生检查、截图或输入。墙钟及单调时间见本轮events和retreat记录，不能将user归因为已知人工来源。

父`msg_b51712805a40`限定最后一次到期复查，`msg_000dc8cbf668`确认a013即最后一次并要求阻塞交付。此后没有桌面、ControlStatus或原生桌面请求，没有新铜进程，没有强关、换入口或修改第三方包。正常取消文件框、关闭及句柄exit0均未发生，不能声称已清理。

保留状态：failed=`a009-net-control-segment`，not_before=`686259.8917363`，busy=false，inbox为空；原候选仍停在最后已知NET文件框。父和工作者仅作精确进程身份查询，六个链身份为2020、17396、20036、36396、40648、50048，另有launcher31708；实际创建时间及存活结果见[residual-identities.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/residual-identities.json)。**客户端和候选仍存，退出码未知。** Pi终端保留；本Task结算后不再向旧inbox投递，后续清理需新任务明确接手这些身份和状态。

## 材料完整性与交付

[完整性核验](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/integrity-result.json)确认实验部署22、稳定dist22、来源输入3、隔离输入3的文件集合、大小和SHA-256前后相同，原固定EXE摘要不变。只读进程查询不结束进程；没有产品、实验源码或部署修改。

[verification-summary.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/verification-summary.json)、[checkpoint-blocked.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/checkpoint-blocked.json)保存机会消费、控制截止和未清理残留；[证据索引](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/evidence-index.json)与[index-verification.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-experiment-gui/index-verification.json)核对文件字节数/SHA及报告本地链接，动态live-state和最终结算回执单列。文档检查通过后仅提交本报告，父代理负责集成。

本轮属于受控环境阻塞，不是已发现产品异步淘汰缺陷。实验候选NET/铜层正向与竞争均未取得验收结论；原固定候选现场未覆盖及总体验收未通过保持不变，900000mil、系统会话结束和原字形`runtime_verified=false`不扩范围。
