# 下一阶段：控制限定验收完成后转向产品竞争准备

2026-10-29，[监督器快照修复后的完整关闭现场](control-close-journal-live.md)按本组限定范围通过：实际双图0/0→1/1、双Tk回调、一次原Shortcut Alt+F4严格成功回执→客户端原Popen退出0→退役→stop，全链无拒绝；7个正常资源寿命3625次上传零账本、2880次实际健康采样全healthy，以及监督器/9个已发现子孙/已知外层原退出链均通过。快照发生1次临时PermissionError重试，持续失败0，不等于全部文件首次写入成功。

本组基线`dev=671259c`，Run `run_5fe071294ef6` / Task `task_be586c71f149` / Dispatch `ctx_9bdfefbc4379`，两批准绑定`msg_584c9cfcd3b5`。原started=930969.9231912，600秒诊断截止931569.9231912、900秒收尾截止931869.9231912；实际服务759.3414292秒约12分39秒，超过最初5～10分钟预计，仍在原预算内。此前所有failed、token、截止及退出证据缺口保持原样，不因本组通过追溯改写。

稳定产品/dist仍0.10.0；固定0.11.0及NET/铜完整竞争仍未通过，原字形runtime_verified=false。控制组通过不等于产品、长期健康稳定或性能倍率通过，50ms子孙轮询仍不能排除未知短命进程。

## 已完成的控制边界

专用关闭实现见[实现说明](control-owned-close.md)：默认禁用，仅本轮客户端创建并保存的原Popen可绑定；关闭前保留原门禁、精确PID/birth/image/HWND/title/class和前景核验，正常动作不额外ControlStatus。一次原Shortcut的Alt+F4尝试即消费机会，严格核对冻结回执；最多5秒原Popen退出0后退役，随后stop。普通Guard/DiagnosticGuard输入后验保持，本组Click/普通Shortcut也实际通过post_native。

工具错误、取消、超时、身份不符、非0退出或传输未知均保守失败，结果未知不重发、不通过WM_CLOSE或其它入口补发。首次真实拒绝完整120秒零桌面请求，failed/token/原截止不清；失败组不恢复、不追加第二组或新连接追逐ready。关闭前至少保留35秒工具、5秒退出和40秒停止余量，600/900预算不重算。

[快照修复](control-supervisor-snapshot-journal.md)只对周期账本有界写入，持续失败锁存并继续持原进程直到退出；本组retry_count=1/failure_count=0，真实重试恢复有证据，失败路径仍主要靠离线测试。最终必要报告写入也可能失败，不能宣称根除所有权限问题。

此前[第三候选现场](control-owned-close-v3-live.md)仍failed；遗留窗66968已由[独立生命周期](control-residual-lifecycle.md)于18:14:27一次WM_CLOSE、新查询句柄exit0正常退出，非原Popen/GUI验收。其原日志476字节前缀和157文件发送前备份保持，仅窗口自然追加两条关闭记录。本组新窗39620则由原Popen正常退出，无已知遗留或后台控制服务。

本轮没有源码变化，沿用149项控制测试通过结果，不重复测试或累加历史计数。有效冻结候选仍为`.local-analysis/control-owned-close-v3/frozen-next/candidate`，111文件，清单SHA `f5ebb7a8b4dfb6b50b378fd54e0ab4d47cedd693607b159391f287cabb066b0e`。它已在本组获得限定现场证据，旧候选和本组execution不可覆盖重跑；以后每次仍使用新副本、新Task/Dispatch/批准/证据及原截止。

## 下一步先离线准备产品竞争

不自动启动产品或重复控制诊断组。下一项工作从最新dev独立分支开始，完整读取[异步结果判据](async-result-boundaries.md)、[实验开发](async-experiment-development.md)及[既有竞争边界](async-races-adaptive.md)，核对固定/实验源码、EXE和输入摘要。先形成可审阅的新产品验收方案，明确采用哪一候选、剩余缺口、单步入口、时间分配、实际模型、精确进程与正常退出归属，再安排必要GUI。

实验竞争必须同应用时钟证明：`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`。真实GUI编辑、新修订、几何、dirty、NET来源图和最终图必须共同成立；cancel后的discarded不能补作有效release。不能用控制诊断窗专用关闭接口操作产品，必须另行设计产品精确归属与正常生命周期。

NET和铜分别冻结新范围、输入与不变对照，不能因为实验通过让原固定候选自动通过。对既有正向对照先核对有效性，无源码变化不盲重跑全矩阵；门闩时限、编辑与实际读图时间能否落在同一窗口内要在启动前评估。读图检查点以外可串行批次执行，但每条依赖成功回执，失败立停，不能预排输入或读图前点击。

## 后续现场通用要求

用户已多次明确授权必要控制电脑，授权保持，不重复索权。先完成代码/测试/冻结摘要/执行顺序材料，执行前说明具体预计开始时间、预计用时和范围；新Task/Dispatch/分支/批准/证据目录独立。截图与GUI由Pi `gpt-6.1-sol high`执行并核对实际PI环境及原JSONL模型/推理/读图记录，模型不可用如实报告不替换；纯逆向使用Pi `glm-5.3 high`。

沿用基础Python原Popen直启本机连续runner、立即持柄放行；所有慢预检和父审阅在握手进程创建前完成，不添加等待代理消息的短闸门。Screenshot有image且必须实际read，已执行输入后观察失败不重发；不放宽指示层1秒阈值、不改活内存/心跳/输入保持集合、不换入口绕拒绝。所有完成条件、失败收尾和进程退出证据分项报告，迟到查询句柄不冒充原Popen。

固定候选900000mil极端位置属性、受控会话结束等剩余项，以及新增图元、另存为、未知字段往返、元件放置、布线、完整DRC、生产输出和原字形兼容，继续分别规划；未实现或未验证能力不得宣称可用。原安装、原库/板图只读，写入测试只用隔离副本；截图、包、产物和.local-analysis不提交。
