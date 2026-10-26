# 异步实验接管续验：控制工具持续拒绝

用户已再次明确授权“你操作电脑进行验收”。本轮完成新任务对原连接的技术接管，但三次到期只读诊断仍返回`user`，隐藏进程延迟15秒后也被拒绝，因此没有执行鼠标键盘、截图或新实验。**本Task为failed/blocked，旧候选及客户端仍存，正常关闭未完成。** 阻塞是实际控制工具拒绝，不是授权缺失，不据此判断产品缺陷。

- Task：`task_92f676d5e13d`；Dispatch：`ctx_7072599ead1b`；Run：`run_4b8adf1b5599`。
- 分支：`verify/async-experiment-resume`，从fetch后的最新`origin/dev`建立；只提交本报告，不合并、不推送。
- 同一Pi会话`01a1739a-82f6-76cf-9ffc-c63e95be56d4`；环境与JSONL模型/推理记录均核对为`deng/gpt-6.1-sol high`。
- 证据根：[async-experiment-resume](../.local-analysis/async-experiment-resume/)。稳定产品及dist保持0.10.0，实验候选SHA仍为`782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`。

## 原连接接管

先只查询精确进程身份及本地文件。候选2020、client/owner50048、MCP链17396/20036/36396/40648及launcher31708的创建时间均与原记录一致。原state为busy=false、inbox空、token=`a008-net-b-path`、failed=`a009-net-control-segment`、截止`686259.8917363`已到。上轮28个冻结源码/配置摘要全部匹配，没有重写运行驱动、重跑82项或连接新MCP。

[adoption.json](../.local-analysis/async-experiment-resume/adoption.json)保存新Task/Dispatch、七个精确身份、13个已有请求ID、旧failed/token、双时钟截止及候选摘要。父`msg_b2296d95525c`明确批准最小接管后，将旧空inbox归档为`inbox-before-adoption`，原路径建立junction指向本轮新证据目录inbox。所有新请求仅写新inbox，携本Task/Dispatch和全新r-步骤ID，由同一长驻client和原MCP消费；未清零失败、截止或seen，未热改源码。原计划中文因PowerShell编码显示问号，保留原件并另存[文字校正](../.local-analysis/async-experiment-resume/adoption-text-correction.json)。

旧运行历史按明确授权追加事件和r-请求回执，未覆写旧静态材料。242个既有文件摘要核对只有运行态`retreat-current.json`按新拒绝更新，旧索引/截图/报告/源码不变；动态`live-state.json`另行核对。见[静态材料及junction审计](../.local-analysis/async-experiment-resume/old-static-audit.json)。

## 三次只读检查

| 本轮请求 | 实际结果 | 新单调截止 |
| --- | --- | --- |
| r-001-diagnose | 同连接ControlStatus=user，generation44；未继续原生检查 | 690258.5246562 |
| r-002-diagnose | 完整180秒后仍user，generation44 | 690557.5381259 |
| r-003-diagnose | 再完整到期后，以隐藏pythonw启动并本地延迟15秒才调用原提交器，仍user、generation44、wait约9.9秒 | 691127.2648819 |

[三个回执](../.local-analysis/async-experiment-resume/r-003-diagnose-receipt.json)与对应请求均留在新目录。没有短轮询，截止内没有输入、截图、ControlStatus或原生桌面请求；隐藏延迟只是正常调度，不修改门禁。不能从wait值推断用户或辅助窗口是已确认根因。

父`msg_6bb67d22fc11`及`msg_f0e342eb87af`确认三次已到边界，要求停止后续自动桌面并最小交付。此后仅作本地文件摘要和精确PID查询，不再诊断、不强关、不换入口或重连。

## 未完成及残留

本次新授权的NET/铜层各对照及竞争四个机会均**未进入、启动数0**；原候选没有正常退出，故没有启动新客户端或新隔离实验。不修改上轮failed，也没有把旧NET_A加载算作本轮对照通过。

七个原身份仍存，完整创建时间及当前state见[residual-identities.json](../.local-analysis/async-experiment-resume/residual-identities.json)。候选2020创建时间`134374989405547867`，client50048为`134374989304233763`；failed仍`a009-net-control-segment`，最新截止`691127.2648819`，busy=false，新inbox为空。未执行Escape、关闭、retire或stop，没有退出码0证据，不能声称已清理。

新inbox junction及空闲控制器保留，Pi终端保留。结算后不再投递本Task请求；未来新任务必须先核对身份、接管通道及继承状态，不能将新连接当作解锁。

## 本地核验与交付

[完整性结果](../.local-analysis/async-experiment-resume/integrity-result.json)确认实验部署22文件、稳定dist22文件、来源输入3文件、既有隔离输入3文件与上轮核验集合/大小/SHA相同，候选摘要未变。本轮没有新建实验输入，因为尚未完成旧连接清理。

[汇总](../.local-analysis/async-experiment-resume/verification-summary.json)、[证据索引](../.local-analysis/async-experiment-resume/evidence-index.json)及[index-verification.json](../.local-analysis/async-experiment-resume/index-verification.json)记录实际检查、残留和文件/链接核验。仅提交本报告，父负责文档集成；未改产品、实验源码、固定部署或第三方控制包。

本轮没有新增实验通过项，原固定0.11.0候选NET/铜层现场未覆盖及总体验收未通过保持不变；900000mil、系统会话和原字形不扩范围。
