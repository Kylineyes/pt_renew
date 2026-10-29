# 已完成控制限定验收，产品竞争先做离线准备

2026-10-29，最近控制现场[监督器快照修复后的完整关闭](control-close-journal-live.md)限定通过：双图0/0→1/1、双回调、一次close-owned严格返回/客户端原Popen exit0/退役/stop，全链无拒绝；资源7寿命3625上传零账本、健康2880全healthy。快照实际有1次临时权限重试、失败0。服务实际759.341429秒约12分39，在原600/900秒预算内但超过最初预计。未知短命子进程覆盖、长期稳定及性能倍率限制保持。

固定0.11.0及独立实验NET/铜竞争仍未通过。只读前置、正向对照与60秒门闩内实际读图时间结论见[离线预检](async-race-offline-preflight.md)：旧正向对照事件/摘要复核有效，旧两竞争保持aborted；最近控制组截图结束到实际read完成71.019/88.949秒，完整到下一工具动作327.085/402.250秒，不能直接满足冻结60秒看门狗。

本阶段只提交了不启动产品的离线审计工具`tools/audit_async_race.py`和10项变异测试；产品客户端的具体状态、read/ack关联与正常退出要求见[实现约束](async-product-client-contract.md)。实际控制图片仍要求本会话read，审计工具绝不从事件数据授予GUI通过。独立归档图片时序演练在准备阶段遭遇指定模型反复连接错误/超时，已按未执行failed结算，worker abandoned、资源保留，无worker_done；request/read/ack均0，不能给出60秒实测结论。原件和结算见[演练报告](async-image-review-rehearsal.md)。本轮未启动产品、门闩、控制MCP或桌面输入，不形成新GUI通过。接手基线为新独立分支`feat/async-race-offline-preflight`，来自`dev=77d81d6`。

## 当前离线结果

- 固定源码`feat-basic-editing=b0e5ac7761f13690b5310bbc913ab7bfd2691d08`；实验源码`experiment/async-result-barrier=c4e3ec5e82bf1a022e523ec8844d0665d7b93234`。独立实验EXE摘要`782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`、22文件；固定候选EXE`dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8`、23文件；稳定dist EXE`726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1`、22文件。均全摘要不变，不重建/覆盖。
- 合成输入副本与原20字节A/B网表及162字节板图摘要匹配，不写原输入。
- 历史NET/copper对照的新应用事件解析均满足有效release时间线及A/B或铜摘要，历史Popen退出0；它们是引用的历史对照，非本阶段新GUI。
- 历史NET/copper竞争虽有revision3/dirty/0走线/A来源及旧结果discarded，但两个运行均有`aborted`、无有效`gate-released`，均保持未通过。旧回执未改。
- 最近控制组两次实际读图完成区间71.019秒/88.949秒；到下一原动作的完整区间327.085秒/402.250秒。由截图结束、会话实际read记录与下一原工具调用的墙钟时间关联重算，不是纯模型推理计时；不声称未来时间数学界。
- 方案`.local-analysis/async-race-offline-preflight/plan.json`标`offline-preparation-only`、`ready_for_live=false`、`max_product_launches=0`、无任务/许可。不得因某次离线演练快而自行改成live-ready。

## 下一个阶段的阻断项

1. 冻结60秒不能放宽；先离线完结request/read/ack关口的健壮性与时序演练。每张门闩图、编辑确认图都须真实调用指定模型read并检查image成功、图hash、实际模型/session、修订/几何/dirty/NET来源；缺图、超时、门闩已返回/aborted一律停，不能预写ack或事后补图。
2. 产品专用生命周期尚未设计：要精确绑定实验EXE及原Popen/创建时间/HWND，覆盖主窗和dirty放弃模态；未保存时一次关闭命令后必须核实正常关闭对话框动作及原Popen退出码。不能复用诊断Tk窗专用close-owned，也不能以临时查询句柄代替原Popen。
3. 为NET和铜分别冻结不变对照、输入摘要、运行顺序和最多一次竞争，使用全新Task/Dispatch/分支/批准/证据。现场中正常控制仍每步单条核对、失败即停；拒绝后完整120秒零桌面请求，不重连绕过。
4. 有效竞争严格要求同应用时钟`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`及真实GUI删除/new revision/geometry/dirty/A来源/终图。cancel路径discard不通过。为节省门闩内时间可在运行前准备所有审阅材料并让连续worker逐步调用；实际读图检查点必须人工/指定Pi完整完成，不能自动图像判定冒充。
5. 实验通过不提升固定候选。固定0.11.0的900000mil极端属性、受控系统会话结束等仍缺。新增图元、另存为/未知字段往返、元件移动、布线、完整DRC、生产输出、原字形runtime兼容分别规划；未经验证不宣称可用。

下一会话先阅读本机`.local-analysis/NEXT_AGENT_BRIEF.md`、`AGENTS.md`、`SESSION_HANDOFF.md`及本文，再从最新dev新建独立开发分支。先实现并测试read/request/ack关口和产品Qt主窗/dirty模态的原Popen正常退出状态机，补齐纯离线失败路径，保留默认禁用；可并行推进这两项独立模块，但只在集成后冻结新客户端。指定模型可用后另立新的离线图片时序演练任务，不恢复本次failed/abandoned上下文。时限与生命周期均验证后才准备NET、铜分别一次的新现场，新批准是具体可审阅结果的最后一步。本轮交付不包含可用产品竞争客户端或有效现场批准。

用户已持续授权必要控制电脑，不重复索权；每次现场前先完成可审阅方案并说明具体开始时间/预计时长/范围。截图/GUI使用Pi `deng/gpt-6.1-sol high`且核对环境与JSONL。下一步由后续会话先审阅本报告、[离线预检](async-race-offline-preflight.md)、[产品客户端约束](async-product-client-contract.md)与[现有判据](async-result-boundaries.md)，只在T1/T2/T3时限可观测并且原进程正常退出路径冻结后，才决定是否请求父批准新现场；本方案目前不能启动产品。
