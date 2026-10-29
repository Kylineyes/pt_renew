# 产品NET／铜竞争的离线预检

2026-10-29，从`dev=77d81d6`建立独立`feat/async-race-offline-preflight`。本阶段核对固定/实验部署、输入、历史正向对照、旧失败和当前读图时序，新增纯离线审计工具；产品启动、桌面请求、门闩release/cancel均0，没有新增产品GUI通过。

冻结实验源码`experiment/async-result-barrier=c4e3ec5e82bf1a022e523ec8844d0665d7b93234`（实验实现`98a4321`），EXE SHA-256 `782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`，部署22文件与原`deployment-manifest.json`逐字节摘要一致。固定源码`b0e5ac7761f13690b5310bbc913ab7bfd2691d08`及固定23文件、稳定22文件保持原样，未重建或合并实验代码。

输入新复制到`.local-analysis/async-race-offline-preflight/inputs`，来源是历史合成测试副本，不修改原板/库。board.pcb为162字节，SHA `85bddf0ba67e081955eaa207f97db9c172c1c686827b6f467ec819a1511bbaf3`；a.net/b.net各20字节，分别`130e3b1e50c62762d72c57d73fc79955ec1d724c70cffad4ee0a9dd755baa974`与`fc8cc17bc6cb8d0e584cf6f7489130326adccc621f6d4f6fffb68bf7363ca77b`。新副本与实验gui-inputs、历史对照/竞争input上下文相同。

## 历史证据与新增审计

`tools/audit_async_race.py`不导入Qt/Win32，不启动进程、显示图片或控制事件。它验证单一应用run/PID、连续sequence、无损整数纳秒时间、唯一目标请求、A实际读取/接受、B或铜输入摘要、工作与GUI线程、冻结入口、原代次/身份淘汰、未中止的唯一release，以及竞争dirty/零走线/新修订/A来源。事件链通过仍返回`gui_verified=false`，不能代替指定会话实际读图、真实输入、图像内容或原Popen退出。

历史NET正向对照37300、铜正向对照39768的文件摘要均与旧冻结一致，原Popen回执exit0；新工具重算两者有效`worker-entered < gate-ready < gate-released < worker-returned < callback-accepted`，门闩等待分别0.7054815秒、1.7546608秒，未编辑/未中止。这里只重新核对事件与摘要，历史GUI结论引用[原四运行报告](async-gui-recovered-120.md)，本阶段没有重新读历史对照图或重跑对照。

历史自适应NET66732/铜54752仍为`aborted`：确有文档修订3/dirty/零走线/A来源及后续discarded，但缺有效gate-released，callback含experiment_aborted=true；返回前等候约4.8899712/5.0610711秒不能包装成有效竞争。新工具明确返回`event_chain_verified=false/status=aborted`，旧failed不改。

旧`critical_segment.py`在抓取门闩图、自动定位及Delete后用文档日志断言，随后直接`self.session.signal('release',rid)`，将`requires_actual_image_review=True`写在释放后的完成记录。它没有等待代理读门闩图及编辑确认图的执行检查点，不能满足现阶段“真实读图确认后release”的要求，禁止原样执行。自动定位可以辅助确定点击位置，但不替代实际read或新修订/几何/dirty/NET来源观察。

## 60秒窗口的实际限制

冻结`AsyncExperiment.cpp`明确拒绝watchdogMilliseconds大于60000，命令行控制器没有扩大时限入口；NET在文件成功打开后、read前等待，铜在算法预算启动前等待。保持该上限，不能热改原EXE或用大输入/暂停整个产品制造通过。

最近[成功控制组](control-close-journal-live.md)有两次实际read，纯离线从原工具call_tool-end、原JSONL read开始/返回以及下一动作起点重算：

| 检查点 | 截图结束→read返回 | 截图结束→下一原动作 |
| --- | ---: | ---: |
| 首图→Click | 88.948728秒 | 327.084982秒 |
| 终图→Alt+F4 | 71.018699秒 | 402.250393秒 |

两次仅到read返回已各自超过60秒。完整检查点包含模型往返、工具调度、上下文与步骤整理，不能称为纯模型推理耗时；它们也不是未来时间的数学上下界。即使将最快完整历史区间重复用于门闩图、编辑确认图两个检查点，观察估算仍为654.169964秒，而且还未计截图/选择/Delete/释放成本。因此当前没有证据支持可在冻结窗口内可靠执行，不启动产品竞争。

为检验更紧凑的可行方式，另立只读归档图片的[离线时序演练](async-image-review-rehearsal.md)，但指定Pi模型反复连接错误和超时，准备阶段即终止；request/read/ack均未开始，Task failed、worker abandoned，无worker_done，终端保留。没有形成新的演练用时，60秒可行性仍unverified，不把未执行等同超时。父侧[预检结果](../.local-analysis/async-race-offline-preflight/final-verification.json)和原事件/实际read区间重算有效。后续即使离线演练小于60秒，也不能当未来上界、产品现场通过或有效批准。

## 下一份可执行方案需要补齐的内容

当前[方案文件](../.local-analysis/async-race-offline-preflight/plan.json)为`offline-preparation-only`、`ready_for_live=false`、`max_product_launches=0`、Task/Dispatch为空、permission_confirmed=false。它冻结意图和阻断项，不是可运行批准。产品客户端具体状态和接口要求见[实现约束](async-product-client-contract.md)。

1. 先完成读图request/ack联动的离线契约与实测，再判断在60秒内包括所有步骤是否有足够余量。检查点只接受本次唯一图hash、指定实际模型/session和成功image回执；请求超时、缺图、门闩已aborted/returned必须失败，不能提前release、预写ack或事后补图。
2. 产品专用客户端必须重新实现Qt主窗与dirty放弃模态的精确归属、原Popen持有和正常退出。诊断窗`close-owned`固定Tk/title身份，不能修改它来接受产品PID；产品未保存时“发AltF4”并不等于进程已退出。原链见证要覆盖产品持有者、客户端、服务及已发现子孙，不能靠迟到PID不存在推退出0。
3. NET和铜分开规划新Task/Dispatch/分支/证据，引用已核对对照；每类最多一次新竞争，不启动盲重试。先冻结完整新客户端、模块、控制包、实验EXE、输入与分项完成/失败收尾，再说明实际时间和范围，按用户持续必要控制授权执行；截图使用Pi gpt-6.1-sol high，核对实际环境/JSONL。
4. 门闩内必须满足`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`，由真实GUI删除与门闩内新修订/几何/dirty/NET来源图及最终图共同佐证；cancel后discard仍不通过。所有正常输入保持原门禁和目标后验，拒绝完整120秒零桌面请求，原门闩看门狗可自然aborted但不能补记有效释放，不换连接绕拒绝。

新增10项实质变异测试全部通过，使用假事件/时钟/JSONL，覆盖双类型对照/竞争、cancel伪通过拒绝、运行/序号/时钟/线程混淆、错误摘要/代次/修订/dirty、成功image/实际read先后，以及“快历史样本也不能自动批准现场”。见[测试输出](../.local-analysis/async-race-offline-preflight/tests-audit-final.log)。与既有149项控制测试属于不同工具范围，不简单相加或复跑无变化产品矩阵。[只读基线](../.local-analysis/async-race-offline-preflight/readonly-before.json)完整保存固定/实验/稳定、旧对照/竞争、最新控制现场及源码/测试摘要，前后全同，证据/截图不入Git。
