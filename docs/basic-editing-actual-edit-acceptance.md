# 0.11.0 实际编辑 GUI 验收

固定部署候选的主要编辑闭环及常规关闭保护已通过真实 Windows GUI 验证：移动、撤销/重做、删除/恢复、分支历史、数值拒绝、只读对象与 LIB 隔离、移动后的端点测量、NET 分析清空/重算，以及关闭/换图取消均取得实际证据。候选已正常退出，部署包、源输入和实验副本的 **23/7/7 文件集合及 SHA-256 前后完全一致**，本任务客户端及已知子进程均已退出。

本 Task 结果为 **failed**：主要产品编辑闭环及关闭保护取得了真实通过证据，但收尾审计发现，在用户新增“争用后退让完整 180 秒”的要求后，运行中客户端仍有 4 处沿用旧的短周期门禁轮询，恢复后约 10 秒就继续输入，未满足该硬约束。两次显式 180 秒退让不能抵消这项执行偏差。本轮没有确认产品缺陷，也不宣称完整发布验收通过；严格文本焦点、旧式菜单完整一致性、极远位置 reset、异步迟到结果竞态和系统会话结束保护仍有未验证边界。

## 固定对象与执行环境

| 项目 | 核验值 |
| --- | --- |
| Task / Dispatch | `task_6f057224ca14` / `ctx_89830f33645c` |
| 实际 Pi 配置 | `PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`；沿用既有会话 |
| 工作分支 | `Kylineyes/verify-text-screen-sol` |
| 候选提交 | `b0e5ac7761f13690b5310bbc913ab7bfd2691d08` |
| EXE | `C:/Users/rikideng/orca/workspaces/pt_renew/feat-basic-editing/.local-analysis/basic-editing/release-candidate/pt-renew.exe` |
| EXE SHA-256 | `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8` |
| 本轮目标 | PID `22140`，主窗口 HWND `2690000`，原生类 `Qt6120QWindowIcon` |
| supported.pcb | 204 字节，SHA-256 `cc3bd87d4f9c077b05b8619969114fca493bddba552aa95c1485a764c7de6d30` |
| 证据目录 | `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/` |

启动使用固定部署包，PATH 仅含 Windows 系统目录，清理 Qt/QML/SDK/VS 相关变量，没有 offscreen 替代。六份合成材料及 manifest 复制到本轮新目录后使用，没有修改原安装、用户板图、原库或产品源码。每次输入前检查 ControlStatus 和实际前景 PID/HWND，对话框也须属于目标；坐标按 Snapshot 提供的倍率 2.0 换算。工具 schema 在桌面调用前离线核对，Type 均提供 loc，App 使用短名 `PT Renew`。

## A、B：移动与编辑历史

A 通过。原自由线为 `(100,100)→(400,500)`，宽 10mil、长 500mil。实际输入 ΔX=100、ΔY=−50 并提交后，重新选中得到 `(200,50)→(500,450)`，宽度/长度不变，仍属于自由图元、来源第 2 行；标题 dirty、工作修订 2→3，原输入 SHA 与工作修订分别展示。

B 通过。在画布 Ctrl+Z 回到原端点和 clean，Ctrl+Y 回到移动位置；选中移动后的线并 Delete，图元数 5→4、走线数 3→2；从编辑菜单撤销后恢复同一移动位置、来源及 500mil 几何。随后执行重做删除、多步撤销回原位置/clean，撤销后新删除使 Redo 禁用，旧分支不能再重做。

| 断言 | 实际截图 |
| --- | --- |
| 移动后属性、dirty、修订与 SHA 分离 | [010-moved-select](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/010-moved-select-post-00.png) |
| Undo 原位置及 clean | [003-undo-select](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/003-undo-select-post-00.png) |
| Redo 移动 | [005-redo-select](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/005-redo-select-post-00.png) |
| 删除后从菜单撤销恢复 | [009-restored-select](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/009-restored-select-post-00.png) |
| 多步撤销回 clean | [013-clean-select](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/013-clean-select-post-00.png) |
| 新编辑清空 Redo 分支 | [015-branch-history](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/015-branch-history-post-00.png) |

## C、D：输入保护与只读隔离

C 数值保护通过。移动框提交 0/0 不新增历史，仍 clean、修订 12、Undo 禁用；1.5、nan、999999 分别被拒绝，没有修改板图/修订；取消同样没有加入历史。曾执行文本 Ctrl+A、Delete、Ctrl+Z，但非法值提交后可能仍在按钮焦点，没有另作明确重新点击输入框、文字变化和历史的完整复验，因此**文本焦点保护不计严格通过**。菜单和现代快捷键分别完成了相应动作，旧式按键菜单的完整一致性未独立覆盖。

D 已执行隔离通过。元件内部线属性显示归属 U1，移动菜单禁用，Delete 不改变数量/修订；焊盘 Delete 无效；隐藏顶层后在原自由线位置点击/Delete 没有误删，恢复顶层后几何完整。加载合成 LIB 的预览中执行 Delete、Ctrl+Z、Ctrl+Y，预览保持只读且主板不变。保存/另存为均明确“未实现”且禁用。移动时底层隐藏及 100% 视图保持；极远位置移动后显式 reset 适配未执行。

| 断言 | 实际截图 |
| --- | --- |
| 零位移不新增历史 | [021-zero-history](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/021-zero-history-post-00.png) |
| 小数、nan、越界拒绝 | [026-fraction](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/026-c-fraction-submit-post-00.png)、[028-nan](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/028-c-nan-submit-post-00.png)、[030-overflow](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/030-c-overflow-submit-post-00.png) |
| 取消与历史不变 | [035-cancel-history](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/035-c-cancel-history-post-00.png) |
| 元件内部线移动禁用 | [038-component-move](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/038-d-component-move-post-00.png) |
| 焊盘及隐藏层不能误删 | [042-pad-delete](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/042-d-pad-delete-post-00.png)、[045-hidden-delete](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/045-d-hidden-delete-post-00.png) |
| LIB 预览焦点隔离 | [060-lib-redo](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/060-lib-redo-post-00.png) |
| 保存/另存为未实现且禁用 | [047-file-menu](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/047-d-file-menu-post-00.png) |

## E、F：测量与分析失效

E 通过。先开启端点捕捉并测原线得到 500mil，真实移动后选择和旧测量结果清空，底层隐藏和视图保持；移动后的新端点重新捕捉为 `(200,50)→(500,450)`，ΔX=300、ΔY=400、距离 500mil，两端均显示来源第 2 行的模型几何捕捉。随后退出测量、Undo/Redo，旧结果没有复现，画面分别回原位置和移动位置，最后 Undo 回 clean。

F 通过。加载合成 `editing.net`，两节点唯一映射到 U1 焊盘，受限铜层分析显示支持模型内连接 1、分离 0。删除连接两个焊盘的自由线后，旧铜结论立即清空、NET 和节点映射保留；重新分析显示连接 0、分离 1。Undo 恢复走线时再次清空旧结论；重算恢复连接 1、分离 0。界面始终明确受限模型、非完整 DRC；不等于完整电气检查或生产放行。异步迟到结果竞态没有现场稳定构造，不用自动测试或源码推断 GUI 通过。

| 断言 | 实际截图 |
| --- | --- |
| 原端点测量 500mil | [065-measure-second](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/065-measure-second-post-00.png) |
| 移动后旧结果清空、底层隐藏保留 | [081-measure-panel](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-01/081-e-measure-panel-post-00.png) |
| 新端点重捕捉 500mil | [006-e-second-retry](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/006-e-second-retry-post-00.png) |
| Undo/Redo 更新状态 | [010-undo](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/010-e-undo-retry-post-00.png)、[011-redo](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/011-e-redo-retry-post-00.png) |
| 原分析已连接 | [019-copper](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/019-f-copper-post-00.png) |
| 删除清空分析、保留 NET | [021-delete](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/021-f-delete-post-00.png) |
| 重算分离 | [022-separated](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/022-f-reanalyze-separated-post-00.png) |
| Undo 再次清空、重算连接 | [023-undo](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/023-f-undo-post-00.png)、[024-connected](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/024-f-reanalyze-connected-post-00.png) |

## G、H：取消、加载失败、放弃及正常退出

G 的四种取消路径均取得保留工作画面：dirty 时 Ctrl+W、换入 `empty.pcb`、从文件菜单退出、点击窗口关闭按钮，均出现“放弃更改 / 取消”，默认取消。分别取消后仍保留原工作副本和 dirty，随后实际执行 Undo 恢复走线、Redo 删除。Ctrl+W、菜单退出和窗口关闭均有关键状态截图；换图取消后 Undo 的 048 截图返回闪烁层未关闭而没有图像，客户端误把 `is_error=false` 视为完成并继续，故该轮 Undo 几何缺直接截图，不能按完整视觉历史链通过，后续 Redo 和保留工作画面可见。

`invalid.pcb` 因第 2 行 UNKNOWN 解析失败，状态栏明确当前工作副本和历史已保留，实际 Undo/Redo 有效。不存在的 `missing.pcb` 被 Windows 原生文件对话框拒绝，确认并取消对话框后工作与历史同样保留；这是对话框拒绝路径，未宣称覆盖文件选择后瞬时消失的读取竞态。

确认放弃后成功换入 `empty.pcb`：0 图元、clean、NET 清空、Undo/Redo 禁用。再次载入 supported、Delete 后 Ctrl+W 并确认放弃，回到“尚未打开文件”。最后重新加载 supported，Delete 后点击窗口关闭，确认放弃合成内存更改，候选进程正常退出。菜单退出的“取消”独立执行；菜单退出确认放弃未另起进程单独复测。

| 断言 | 实际截图或原生记录 |
| --- | --- |
| Ctrl+W 放弃确认 | [028-close-observe](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/028-g-close-observe-00.png) |
| 损坏输入失败保留工作 | [034-invalid-load](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/034-g-invalid-load-post-00.png) |
| 不存在文件原生拒绝 | [039-missing-load](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/039-g-missing-load-post-00.png) |
| 换图放弃确认、取消后可撤销/重做 | [046-change-load](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/046-g-change-load-post-00.png)、[048-Undo 原生记录（截图失败）](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/048-g-change-undo-native-after.json)、[049-redo](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/049-g-change-redo-post-00.png) |
| 菜单退出与窗口关闭均提示保护 | [053-menu-exit](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/053-g-menu-exit-post-00.png)、[057-window-close](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/057-g-window-close-post-00.png) |
| 放弃换空板并清空历史 | [064-empty](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/064-g-empty-discard-post-00.png)、[065-empty-history](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/065-g-empty-history-post-00.png) |
| Ctrl+W 确认放弃后关闭文件 | [073-close-discard](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/073-g-close-discard-accept-post-00.png) |
| 最终窗口关闭确认与进程退出 | [079-h-close](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/recovery-02/079-h-close-post-00.png)、[target-normal-exit.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/target-normal-exit.json) |

H 清理通过。最终候选 PID22140 已不存在；三个阶段客户端/启动器的已知 PID11480、14652、16840、24372、44432、56592，以及观察到的 MCP overlay PID14372、31420、61176 均已退出，没有终止其他工程进程。候选 23 文件、来源输入 7 文件、副本 7 文件的文件名集合、字节数和 SHA-256 与启动前全部一致，原副本均未写回。

摘要证据为本轮目录下 `candidate-before/after.json`、`source-inputs-before/after.json`、`inputs-before/after.json`，综合结果见 [integrity-result.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/integrity-result.json)，进程清理见 [processes-final.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-actual-edit-acceptance/processes-final.json)。结构化汇总为 `verification-summary.json`；最终状态写完后生成 `evidence-index.json`，排除索引自身及动态状态，再逐项复核摘要。

## 环境中断及后续接手

本轮发生辅助 Terminal 抢前景、Click 返回 USER_CONTROL、多次截图闪烁未关闭，以及后置 Snapshot 返回 CONTROL_UNAVAILABLE。相关动作均保留原始返回与原生归属；焦点保护在向非目标输入前拦截，未把工具成功回执或其他应用画面当产品证据。收尾发现 048 的截图错误被包装成 `is_error=false`，本地驱动没有把“无图像且文本报错”当作失败，因此错误地继续下一步；该处截图明确缺失，不以原生标题单独替代几何证据。后续控制驱动还须增加这一响应检查。LIB 文件对话框曾拒绝正斜杠路径，改为 Windows 反斜杠路径后加载成功；没有把该路径输入错误当产品缺陷。

用户新增其他工程可能争用的说明后，已停用刚加入的自动聚焦，未继续每步切换目标。完成 180 秒无桌面请求退让后，同连接 ControlStatus 为 ready，原生前景仍为候选的 NET 文件对话框，继续 F/G。后来 050 文件菜单 Click 成功、后置 Snapshot 返回 CONTROL_UNAVAILABLE，立即再退让 180 秒；只读复查 ready、前景仍为候选，继续原菜单断点。没有因这些争用重建连接；不确认输入来源时保持未知。

**执行偏差：**停用自动聚焦时，没有同步处理运行中客户端原有的 `gate()` 短轮询。新增约束后的 `031-g-cancel-redo`、`039-g-missing-load`、`049-g-change-redo`、`057-g-window-close` 首次门禁均返回 `user`，运行中客户端仍每约 2 秒查询，约 10 秒恢复 ready 后继续相应输入，没有等待完整 180 秒。原始 `*-gate-00.json` 至恢复 ready 的 gate 文件以及前后原生归属均保留；这 4 处是本代理的执行错误，不能描述为合规退让。另有 `011-e-redo-retry` 的 user 短轮询发生在收到新增约束之前，与上述 4 处区分记录。发现偏差时桌面操作已结束、候选和全部本任务客户端已退出，未再发送输入；已向父代理升级并将本 Task 明确结算为 failed。详见 `control-retreat-audit.json`。

后续验收须先在客户端请求处理层落实“首次观察 user/非目标前景即停止动作，并留到 180 秒后才只读复查”，禁止保留旧短轮询自动恢复路径；本轮没有通过修改第三方控制包来绕过门禁。

后续只需按需要补齐以下未验证项，不必把已通过 A/B/E/F 的入口重新当作编辑验收：

- 明确点击移动输入框后的文本 Delete/Ctrl+Z，逐帧确认文字变化且板图历史不变。
- 旧式按键菜单与现代菜单/快捷键的完整一致性；其他未出现图元的只读保护。
- 极远位置移动后的显式 reset 适配；本轮仅确认正常移动时层状态/视图保持。
- 异步分析迟到结果及选择后文件消失等竞态。
- 换图取消后的 Undo 几何补截图；本轮 048 返回截图错误，只有后续 Redo 及工作保留画面。
- 菜单退出确认放弃的独立进程复测。
- 系统注销/关机保护：共享宿主没有执行，明确未验证。

未修改产品源码，未重新构建固定候选，未重复运行既有 Debug/Release 自动测试；本轮新增依据是实际 GUI 及文件/进程核验。只提交本报告，截图、合成实验副本和本地脚本保留在 Git 忽略目录，不合并、不推送。根交接文档由父代理根据本报告和上述剩余项整理。
