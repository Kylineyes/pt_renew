# 产品回执与原Popen适配已补，实际读图时序仍缺

2026-10-30最新结果见[原始回执与原Popen适配报告](async-product-evidence-adapters.md)。从`dev=883f333`独立分支完成默认禁用的原MCP结果/PNG/region物理倍率及原Popen创建/原句柄身份适配，另加全新顺序读图计时器与显式UTF-8预检。新增20项及仓库254项Python测试通过；10组旧参考摘要不变，产品/桌面请求0，ready_for_live=false。

新只读图片Task `task_70c8976c2e7e` / Dispatch `ctx_1e46f88cbaf6`已按**failed结算**：实际Pi `deng/gpt-6.1-sol high`及12条assistant记录核验通过，预检PowerShell编码错误发生在init之前，依约停止。request/read/ack均0，无timing-result；父已验收唯一done并ack，external_terminal保留、processAction=none、reclaimable0。修复后的Python UTF-8 preflight只在父新分支，不写回旧冻结或恢复该任务。后续不能重复投递本次或更早failed/abandoned上下文。

下一步继续补native/UIA可信主窗/文件框/dirty模态数据、应用原run UUID与Task绑定、门闩原事件/唯一release以及原Popen外层全链见证；再冻结并测试。实际指定模型两图read兼容性及T1/T2用时仍未取得，不因模型本次可响应而当时限通过。当前没有可运行的产品现场客户端或新现场批准。

以下保留前阶段结果和共同约束；最新实现范围以上述报告为准。

2026-10-30，从已核对的`dev=f81576f`独立分支`feat/async-product-client-offline`完成[产品客户端离线实现](async-product-client-offline.md)：request/read/ack、一次真实编辑的编排接口、产品Qt主窗/dirty模态及原Popen正常退出状态机均可注入假API测试，默认禁用。新增30项测试、仓库234项Python测试全部通过；没有启动产品/控制服务/输入钩子或运行旧演练，没有新Task/Dispatch/批准。**ready_for_live=false、max_product_launches=0。**

此前控制限定通过保持：[完整关闭现场](control-close-journal-live.md)有双图/回调、一次诊断关闭严格回执→原Popen0→退役→stop，全链无拒绝；资源7寿命3625上传零账本、2880健康全healthy。未知短命进程、长期稳定及性能倍率仍未证明。产品稳定0.10.0、固定0.11.0与独立实验各自的验收边界不变。

## 本阶段可审阅结果

- 新`tools/async_product_client/`只依赖标准库；共享身份、ID/token/忙/排队和原截止，失败不清锁存。request/ack写入新证据目录，唯一图hash及实际read回执不能复用。
- 实际read须从绑定原会话JSONL核对`deng/gpt-6.1-sol/high`、session、调用及成功image的原字节hash，指定会话另作内容判断；不会把辅助`observed=true`或应用日志当作读图。
- 原Popen由唯一创建器直接返回并立即持有，创建前核对完整部署/输入及清理环境，按精确主HWND和动态允许标题验证；dirty模态核对同PID/birth/image和owner，实际read后才明确一次“放弃更改”点击。
- 普通选择/Delete保留前景后验，Delete要求canvas焦点；正常关闭后单独等待原Popen，不再要求已消失窗口保持前景。输入未知/错误不因后来退出0改成功；退役只证明生命周期结束。
- `tools/freeze_async_product.py`生成新离线候选，包含核心、测试、文档、3个标准库见证器、实验22文件、控制包77文件及新输入3份；不生成批准或开启预算。固定23、稳定22及旧对照/竞争/控制证据全摘要按历史同口径复核不变。

冻结时限设计为从目标请求**触发之前**的原本地单调时钟起算：T1门闩图实际read/ack严格小于20秒；T2编辑图实际read/ack严格小于50秒；T3严格小于55秒且应用时钟余量大于5秒时才开始唯一release；回执及应用释放均在原60秒内。本地事件wait每块至多1秒，35/5/40秒正常退出余量及失败120秒零桌面请求不变。这些是执行门槛，尚无新的实际模型计时证明。

## 下一阶段顺序

1. **实际read兼容性与时限仍待验证。** 本次全新任务在预检编码错误后已failed结算；后续只能在新的具体任务和新上下文里使用已测试并冻结的UTF-8预检。指定模型可用时另立新上下文，离线验证成功read image的原记录格式，以及新request→read→ack两图顺序计时。当前验证器会拒绝变换/删减image的记录，若需适配先冻结可审计变换链。旧[未执行演练](async-image-review-rehearsal.md)保持failed/abandoned，不能恢复、续投或直接执行其准备脚本。一次快速结果也不能给未来耗时提供保证。
2. **继续补齐现场适配器与见证链接入。** 现在已有默认禁用的原MCP结果/PNG/region及原Popen创建/原句柄适配，仍缺native/UIA可信数据、文件框阶段、应用UUID绑定和产品全链启动器；已复制见证器不等于已完成接入。必须保持持续owner、原Popen/原句柄、精确窗口和普通输入后验，先补假API回归再冻结所有模块/包/EXE/输入。
3. **条件满足后再形成新现场。** NET与铜分别使用新Task/Dispatch/分支/证据及最终审阅材料，每类最多一次竞争，引用不变对照；说明具体开始时间、预计时长和桌面/进程范围后，在用户持续必要控制授权内执行。不先启动短握手进程等批准，不重复已成功的诊断组，不增加组/连接追逐ready。
4. **完整产品判据独立验收。** 同应用时钟必须满足`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`，并有门闩内真实删除、新修订/dirty/零走线/A来源图和终图。cancel后的discard不通过，核心的协议`settled`也不能替代完整事件/GUI审计。固定候选仍不能由实验通过代替。

## 交接与授权边界

接手先完整读本机`.local-analysis/NEXT_AGENT_BRIEF.md`、[AGENTS.md](../AGENTS.md)、[SESSION_HANDOFF.md](../SESSION_HANDOFF.md)、本文及[实现报告](async-product-client-offline.md)。本轮补充简报另写`.local-analysis/async-product-client-offline/NEXT_AGENT_BRIEF.md`，原简报和全部旧任务/失败/批准/归档证据保持只读。

必要控制授权持续，不重复索权；每次现场先完成具体可审阅结果并说明实际时间与范围。本阶段没有安排现场，不虚构开始时间。首次真实拒绝完整120秒无输入/截图/状态/原生桌面请求；Snapshot须有image且指定会话实际read，输入后观察失败只补观察不重发；不关闭指示层、不放宽1秒阈值、不热改或绕拒绝。

后续原字形runtime、固定900000mil极端属性/受控会话结束、新增图元、另存为/未知字段往返、元件放置/布线、完整DRC、生产输出仍分别规划。没有新的产品GUI通过或发布版本升级。
