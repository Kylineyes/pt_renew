# UIA对象生命周期修复与新单次核验

从 `dev=1789c328639181dc29508e3610448f029721237a` 建立 `fix/uia-object-lifecycle-review`，完整审阅交接、首次failed和离线代理修复后，补齐清理与最终回执的失败分支，再以全新Task执行一次对象核验。本组限定通过，产品仍 `ready_for_live=false`；首次失败Task及其批准、冻结、120秒结算保持原结果。

## 修复及离线验证

`com_apartment.py` 继续在core执行后、events创建原单例前重绑定模块局部ctypes代理，停止异常仍穿过原包的 `except Exception`。本轮增加清理完成标记与异常记录：原退出回调先消费再执行，每个至多一次；普通回调失败后继续处理其他回调和已知COM余额，原释放调用未返回时停止后续释放，不以旧余额重复调用。部分core导入尚无单例类时也清理已取得的初始化；清理抛错即使余额已归零也不报告 `balanced=true`。原观察异常保留，清理错误附加记录。

`run_async_uia_object.py` 的最终回执统一进入 `finalize`。构造回执前已越5秒、最终写盘越时或抛异常都锁存首次失败，保留token与原截止；拒绝回执或失败审计盘不可写也不跳过完整120秒本地等待。未知原Popen继续持有，迟到exit0不能清失败。

新增9项测试，其中COM专项新增6项，最终回执新增3项含6种时钟/磁盘故障模式。初次假API回归保留了3个失败及1个错误的复现日志，修复后仓库 **428项通过，40.386秒**；独立冻结候选 **234项通过，42.528秒**。测试使用假COM、窗口、时钟和无GUI标准库进程，不将其当真实Qt验收。早期测试工具60秒外部超时的未完成日志单独保留，完整回归另存，不将截断日志补作通过。

## 新任务与真实结果

新Orca Run `run_95717b0022a0`，Task `task_49c2158f60ce`，Dispatch `ctx_15cecb4855e4`；工作者独立分支 `verify/uia-object-lifecycle`。通过 [orchestration技能](C:/Users/rikideng/.pi/agent/skills/orchestration/SKILL.md) 与 [orca-cli技能](C:/Users/rikideng/.agents/skills/orca-cli/SKILL.md) 创建指定Pi会话，显式 `deng/gpt-6.1-sol high`、禁用自动MCP连接。实际session为 `1ad5d64c-f53d-4a80-8a0c-d97720126a8b`，原JSONL、环境与工具回执均另存核对。

工作者首先只读审阅，指出最终回执两处缺口；父补实现与假测试后，工作者再次审阅确认。新批准消息 `msg_0f34cb968233`，最终材料回复 `msg_e60e97f3295d`，未先启动握手或对象等批准。向用户说明计划2026-10-31 00:10（UTC+8）、预计整体3分钟；材料核对完成后实际唯一工具执行为 **00:13:40.281170～00:13:41.598159**，原runner退出0，外层工具区间1.3169555秒。

| 原始证据 | 本组结果 |
| --- | --- |
| 直接创建的原Popen | PID35196 / birth134378504205474034 / handle352；基础Python与实际子PID相同，原exit0 |
| 原单例 | 已导入类定义创建的 `_instance`，IUIAutomation及RawViewWalker均存在；不再次调用instance |
| 原COM线程 | 30664；CoInitializeEx HRESULT0、CoInitializeEx HRESULT1、CoInitialize HRESULT1 |
| 清理 | 三次CoUninitialize全部原调用返回，余额3→2→1→0；cleanup_completed=true，cleanup_errors为空 |
| 原5秒 | 原5秒截止在预检起点7401253993800ns起算，最终记录7402351233500ns；至记录1.0972397秒，至外层观察运行器退出1.1150096秒（含最终落盘），原截止7406253993800ns不变 |
| 判定 | completed=true，accepted=true，failed_id=null；本组没有拒绝或120秒冷却触发 |
| 现场范围 | 对象一次；窗口/桌面查询、事件订阅、截图、输入、PT产品、控制服务均0 |

父审计只读核对原创建者的证据，父不冒称自己持有该子Popen。独立[工作者报告](uia-object-lifecycle-worker.md)记录实际工具、原JSONL唯一调用及最终结算。唯一worker_done `msg_49a3119187da` 已父验收、ack `delivery_9cff13a6c847`；worker-release为 `external_terminal retained/processAction=none`，reclaimable为0，闲置Pi终端不代表活Task或对象服务，不复用已结算上下文。报告原提交 `793fc5f` 已整合到父分支。

## 冻结、证据及下一步

新实际候选6623文件，manifest SHA256 `f2514ebdd8e1daa57ac62e2703d8b088e98d27d2f443a277943a4d88963eef7e`；配置SHA256 `e38cc6c45e970a2820238d24d1b6e78be07d0bb67e850dd2d6507156bcff62cb`，批准SHA256 `cb711f5486ff7da82d224c823a90cd73f7b689369966b88c220b0cdd18b3855f`。执行后全部候选、配置/批准及私有156文件依赖摘要一致。旧实际6622文件候选、上一6623文件离线候选及旧worker170文件也逐项核对不变；没有覆盖原安装、全局依赖或旧冻结。

父证据 `.local-analysis/uia-object-lifecycle-review/` 包含 `freeze-final-verification.json`、`readonly-before-final.json`、`tests-all-final.log`、`tests-frozen-final.log`、新 `frozen-final/`、`live-materials/` 与 `parent-live-audit.json`。工作者原件位于 `../verify-uia-object-lifecycle/.local-analysis/uia-object-lifecycle/`，含原session、执行器/子结果、原账本、前后摘要及工具区间。原始DLL完整加载清单未采集，不声称额外DLL加载为零。

下一步转入**真实Qt/完整冷探针兼容性准备**：先只读审阅服务启动、初始A接受、主HWND绑定、精确标题/owner/DPI/前景、双轮UIA以及未绑定/unknown收尾，再准备新指定Pi任务及全部冻结材料，说明具体时间/预计时长和范围后执行。对象成功不能代替Qt/文件框或全链正常退出；客户端基线/read、路径Type后验/read、取消/clean与dirty关闭及外层原退出链仍待真实验证。兼容性驱动继续拒绝B打开/铜触发/Delete/release。

本组单次耗时不代表后续冷探针或全动作上界。NET/铜含发现仍31/22次，共享32次上限；原5秒、20/50/55/60、35/5/40及600/900预算不扩大。完整竞争须在前述兼容性与退出链通过后重新评估全动作预算，当前不启动NET/铜竞争，也不发布新产品。
