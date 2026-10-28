# 控制工具截图诊断：首次基线在目标恢复阶段受阻

本轮结论为 **failed**：唯一诊断连接和自建窗口正常启动，但初始窗口不在前景，原`App switch`恢复返回not found，随后本地预算又拒绝唯一diagnose。没有进入真实Snapshot、Click或Shortcut，因而没有取得实际图像、按钮/快捷键输入确认或截图内部轨迹，原NET/铜竞争的截图拒绝根因仍未知。窗口及全部控制链均已正常exit0，未启动第二连接，不把收尾或离线修复测试计为现场通过。

- Task：`task_bb8bca1bbfb9`；Dispatch：`ctx_5e11c1301247`；Run：`run_22b5092f9df3`。
- 分支：`verify/control-snapshot-diagnostics`，从fetch后`origin/dev=621afcd10478b0051d840765d26b3020aec93c84`建立；只提交本报告，不合并或推送。
- 原Pi session：`01a1739a-82f6-76cf-9ffc-c63e95be56d4`；环境、JSONL model/reasoning变化及实际assistant记录核对为`deng/gpt-6.1-sol high`，没有替换模型。
- 新证据：`../.local-analysis/control-snapshot-diagnostics/`。所有旧任务已结算，旧候选和控制链exit0原件保留；没有恢复旧PID或投递旧inbox。

父拥有`tools/control_diagnostics.py`、`tools/run_control_diagnostics.py`和相关测试，本工作者没有修改这些文件。父包装在隔离副本上记录bounded只读控制字段、阶段、异常与status diagnostics，原门禁判定及异常保持；77文件包副本与原安装字节一致。父7项原控制器语义回归属于离线证据，不代表截图现场通过。

新客户端沿用旧Guard原字节：普通键鼠不额外ControlStatus预检，但保留输入桌面、稳定前景、PID/HWND、完整映像及创建时间核验，实际拒绝停链、120秒静默、唯一请求ID/parent token、不排队、不重发已执行输入、Snapshot必须有image。仅适配自建窗口标题`PT Renew 控制诊断试验`、受限动作预算、父指定server参数和真实`call_tool`起止日志。使用MCP已有解释器与Tk9.0，未安装依赖。

自建窗口只显示按钮与快捷键回调计数。程序只在真实输入回调更新相应计数，没有程序接口模拟点击或计数；绑定`Ctrl+Shift+F8`，正常关闭走原`WM_DELETE_WINDOW`回调。预算最多一个连接、两个组，每组Snapshot→窗口内Click→Shortcut→Snapshot，总上限六个Snapshot；真实拒绝后不继续输入探测，最多一次同连接diagnose和一次观察只供收尾。Click额外要求位于当前核验的自建窗口矩形内，第一张实际图核对后才允许选坐标。

6项定向离线测试通过，覆盖两组/截图预算、真实拒绝后停止输入/单次诊断及观察、已执行关闭不重发、初始非前景不推进组、原120秒锁存、适配器pacer之后真实调用起止及原错误回执保存。它们未覆盖专用restore结果与预算联动，现场暴露此缺口，不能把6项通过解释为全部恢复分支已测。父以新批准`msg_84532174c971`冻结17项客户端文件及启动器/manifest后才开始唯一连接。

| 步骤 | 直接事实 | 边界 |
| --- | --- | --- |
| 初始化 | launcher2980、client40832；首次本地d001早于live-state生成而FileNotFound | 没有投inbox或执行Launch，错误保留；没有重连 |
| d004启动 | 自建Tk窗口PID39100、创建时间`134376385734130137`、HWND8391014 | 一个测试窗口，产品候选启动0 |
| d005/d006 | 第一组建立；首Snapshot在原生前检非目标前景，executed=false，截止`822162.6161304` | 预算记录一次Snapshot请求尝试，真实Snapshot调用0；完整120秒静默 |
| d007恢复 | 到期ControlStatus ready/generation1；唯一指定标题/PID/映像/创建时间检查通过后调用原App | `is_error=true`，完整错误：`Error calling tool 'App': Application Pt Renew 控制诊断试验 not found.`；执行状态unknown，不自动重试 |
| d010诊断 | 父要求一次diagnose；实际返回`AssertionError: 拒绝后最多一次同连接诊断` | 本地预算先拒绝，ControlStatus/native调用均0，不能写成工具拒绝或当前前景已确认 |
| 正常收尾 | 父`msg_2242ac03e7a8`限定一次精确身份WM_CLOSE，原Tk回调正常退出 | 不发送键鼠，不改变计数，不作GUI通过或输入证据 |

原生保存快照能看到标题完全一致的TkTopLevel：PID39100、HWND8391014、rect `[1000,550,1916,1089]`，与前景Weixin不同。原`App`内部通过UIA窗口列表模糊查找返回not found，不能用原生可见性代替工具查找成功。父在真实`Desktop.switch_app`加假窗口的离线复现中证实：有旧缓存时refresh_count0/activation0、not found；独立验证强制刷新后refresh_count1/activation1、成功。该复现证明缓存缺陷可达，**没有读取本次运行的缓存内容，不能声称现场完全由它触发**，更不能归因为旧截图失败。

预算缺口有直接代码及运行证据：专用`restore-target`在客户端独立分支返回，未交给`budget.result`，故App实际错误后`budget.refused`仍false；而`Budget.check(diagnose)`要求refused为true，d010在任何桌面请求前拒绝。没有修改运行内存或热改源码来清此条件，没有以人工前景操作掩盖预算断路。父后续App刷新及预算修复的离线验证属于未来版本，未在本次实例加载，另一次现场仍需独立冻结批准；本轮第二连接为0。

真实调用起止在`actual-calls.jsonl`单独记录，位于pacer等待之后，原`is_error/text/structured/images`及完整MCP原始回执另存。实际仅有两对调用：ControlStatus `822232.5372207→822232.5427599`；App `822232.5607884→822247.8959882`，单位均为同一主机monotonic秒。没有Snapshot调用，因此4秒节奏没有现场样本，不声称截图倍率、计数可视状态或capture pause/resume已验证。Tk自身记录逻辑屏幕2560×1440只能作窗口日志，不能代替实际Snapshot桌面/图片倍率核对。

控制器trace完整收尾565行，末行`trace-closed/dropped=0`，未报告写入错误。事件包含diagnostics-installed、原状态变迁、App的begin/end、277对rehook-recovery及一个tick状态处理；没有capture、screenshot、cursor-api、低层键鼠hook或fail-open轨迹。零丢失只能说明本次日志正常收尾，不能把没有执行的截图路径称为已诊断或从时间邻近推断原因。原ControlStatus增加diagnostics，但state/generation/wait原字段保留，本次ready不能外推未来截图可用。

收尾新增范围明确只针对本任务自建程序：持有查询句柄核对完整pythonw映像和精确创建时间，再核对HWND→PID、完整标题及TkTopLevel，发送一次`PostMessageW(WM_CLOSE)`；窗口原日志记录normal-close/mainloop-returned，计数始终0/0。独立持有句柄与客户端d011的原Popen均确认exit0并retire，没有TerminateProcess或任何键鼠清理输入。它不适用于产品候选或其他窗口，不计测试动作成功。

控制链停止前持有五个精确身份查询句柄：2980、23224、25200、40832、41832，d012正常stop后全部退出码0。原failed=`d006-initial`、token=`d004-launch`、截止及budget保存在pre-stop-state，没有删除state或重置门禁；当前没有残留窗口或控制链，Pi终端保留。19条Guard事件的一次120秒退避审计`early_requests=[]`，额外生命周期收尾发生在到期后，未用于恢复探测。

停止后的本地审计确认17项客户端冻结、保存的本次父启动器源码、原安装77及隔离包77文件SHA与批准相符；稳定22、固定23、实验22部署的文件名集合、字节数、SHA前后相符。父随后告知仅在旧链全部退出后，才为未来运行修改启动器、增加默认关闭的App刷新批准字段；本次实际运行源码已另存provenance，不将该后续版本记为本次加载或重新覆盖原冻结证据。稳定产品仍0.10.0，固定0.11.0及NET/铜竞争未通过状态不变；未启动任何固定/实验候选，未重跑竞争或产品测试，未改dist/main、第三方原安装或父工具/测试文件。

本地证据入口（Git忽略目录，远端克隆不带入）：

- [原会话/模型](../.local-analysis/control-snapshot-diagnostics/model.json)、[方案及17摘要](../.local-analysis/control-snapshot-diagnostics/checkpoint-offline.json)、[6项定向测试](../.local-analysis/control-snapshot-diagnostics/targeted-tests.log)、[客户端批准](../.local-analysis/control-snapshot-diagnostics/phase-two-approval.json)、[父启动器批准](../.local-analysis/control-snapshot-diagnostics/parent-audits/approval.json)。
- [原App完整回执](../.local-analysis/control-snapshot-diagnostics/0003-App-raw.json)、[真实调用起止](../.local-analysis/control-snapshot-diagnostics/actual-calls.jsonl)、[d010本地预算拒绝](../.local-analysis/control-snapshot-diagnostics/d010-diagnose-complete.json)、[父离线缓存复现及限制](../.local-analysis/control-snapshot-diagnostics/parent-audits/app-cache-reproduction.json)。
- [本次控制器trace](../.local-analysis/control-snapshot-diagnostics/controller-trace.jsonl)、[trace汇总](../.local-analysis/control-snapshot-diagnostics/trace-summary.json)、[原生窗口恢复前快照](../.local-analysis/control-snapshot-diagnostics/events/00016-native_result.json)、[窗口回调日志](../.local-analysis/control-snapshot-diagnostics/window-events.jsonl)。
- [限定正常关闭身份及exit0](../.local-analysis/control-snapshot-diagnostics/normal-close-result.json)、[Popen退役](../.local-analysis/control-snapshot-diagnostics/window-exit.json)、[五链持有句柄exit0](../.local-analysis/control-snapshot-diagnostics/chain-exit.json)、[原状态保存](../.local-analysis/control-snapshot-diagnostics/pre-stop-state.json)。
- [120秒审计](../.local-analysis/control-snapshot-diagnostics/control-audit.json)、[完整性结果](../.local-analysis/control-snapshot-diagnostics/integrity-result.json)、[结果与未覆盖](../.local-analysis/control-snapshot-diagnostics/verification-summary.json)、[证据索引](../.local-analysis/control-snapshot-diagnostics/evidence-index.json)。
