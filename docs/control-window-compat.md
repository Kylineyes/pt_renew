# 诊断窗口兼容前置与单组验证

本轮总体 **failed**：允许缩放的新窗口已由实际UIA及原工具枚举确认可发现，原App恢复成功，首张真实Snapshot明确显示按钮/快捷键计数0/0。但按截图倍率换算的物理Click坐标，与客户端DPI虚拟化的原生窗口矩形被直接比较，触发本地保护拒绝；没有真实Click或测试快捷键调用，单组没有达到计数1/1。随后只执行唯一诊断/观察并正常GUI退出，窗口、只读探针和整条控制链均exit0，没有追加组或连接。

本轮Task `task_82d78df9e34c`、Dispatch `ctx_1dbebe2effc3`，沿用Run `run_22b5092f9df3`；原Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`的环境、JSONL及实际assistant记录均核对`deng/gpt-6.1-sol high`。分支`verify/control-window-compat`从本地`origin/dev=621afcd10478b0051d840765d26b3020aec93c84`建立，证据为`../.local-analysis/control-window-compat/`，仅提交本报告、不合并推送。父拥有tools/tests，工作者没有修改父文件或第三方安装。

| 阶段 | 结果及不能外推的边界 |
| --- | --- |
| 旧基线：control-snapshot-diagnostics | failed，App not found及恢复预算断言，真实Snapshot/Click/Shortcut均0；旧报告不改 |
| 缓存/预算修复验收：control-snapshot-fix | failed，App刷新已加载仍not found；预算唯一diagnose可达，真实Snapshot/诊断输入仍0；旧报告不改 |
| 本轮可缩放窗口 | UIA/原工具枚举、App恢复、首真实Snapshot子项通过；Click本地坐标空间检查拒绝，单组failed，未复现截图工具拒绝 |

本轮只将窗口`resizable(False,False)`改为`True,True`，保留初始几何、标题与只在真实输入回调计数的逻辑。新UIA探针在独立子进程的单一COM线程中，先核对本client持有Popen的精确PID/birth/完整映像与唯一标题HWND，再读取WindowPattern及原`Desktop.get_windows()`枚举，不激活、不输入、不放宽原过滤。客户端要求前置成功才允许组、目标恢复或Snapshot/Click。新批准`msg_604c4ae31478`绑定19文件、父3启动器和77文件包manifest，`app_refresh_fix=true`；新身份、inbox、state与前两轮分开，不继承旧failed为ready。

4项新路径离线测试通过：可缩放配置、属性/身份/原枚举缺一拒绝、前置失败不建组、一组/四次截图预算。没有重跑旧回归。准备时本地生成摘要命令有一次引号SyntaxError，导致question先于摘要生成发送；原错误保留并向父纠正。随后实际4测试/19摘要落盘，父确认以落盘材料逐项核验后才生成双批准，现场未提前启动。

| 步骤 | 直接事实 |
| --- | --- |
| w001/w002 | 唯一窗口PID14800、创建时间`134376473117570841`、HWND14616978；UIA原生身份匹配 |
| 实际UIA前置 | ControlType50032/WindowControl、ClassName TkTopLevel、完整Name正确、CanMinimize=true、CanMaximize=true，原工具枚举确含同PID/HWND；activation_calls0/input_calls0，探针exit0 |
| w003/w004 | 建立唯一组，首Snapshot前原生非目标前景拒绝executed=false，完整120秒截止`830977.2296304` |
| w005/w006 | 原App刷新恢复成功、原生后验通过，显式resume，不改工具窗口过滤 |
| w007 | `0004`有效Snapshot已实际读图，计数0/0；原尺寸3840×2160、图片1920×1080、回执倍率2 |
| w008 | 图中按钮约(1093,628)，按回执传物理坐标(2186,1256)，本地DiagnosticGuard矩形断言拒绝，尚未进入真实Click |
| w009/w010/w011 | 保守120秒静默后唯一diagnose成功、显式resume、唯一观察图`0006`有效已读，仍0/0；未补发按钮或测试快捷键 |
| w012/w013 | 原Shortcut Alt+F4正常关闭，输入已执行后目标消失导致post_native锁存；原Popen确认exit0并retire，不重发 |
| w014 | 停止前持有五链精确身份查询句柄，正常stop后全部exit0；没有生命周期WM_CLOSE或强杀 |

本地Click边界有明确调用证据：Snapshot回执要求图像坐标乘2，原生保存的rect却为`[1000,550,1916,1089]`，图中窗口物理位置明显不同。客户端将这两个坐标空间直接比较，`DiagnosticGuard.raw`在调用`super.raw`/transport前抛出`Click必须位于当前核验的自建窗口矩形内`。原perform先设置attempted，故旧回执写`executed=unknown`，原件不改；以actual-calls中没有Click、窗口无input-callback及具体抛出路径校正为**实际Click未发送**。这不是USER_CONTROL或CONTROL_UNAVAILABLE，不靠改坐标重发来掩盖驱动错误。父随后准备的物理矩形工具及回归没有加载本次实例。

两张有效图分别是组前首图和中止后的唯一观察图，不是完整组首尾图，均实际读取显示计数0/0。测试`ctrl+shift+f8`没有发送；本次唯一Shortcut是正常关闭的Alt+F4，不能混计为测试回调。窗口只记录window-ready、normal-close、mainloop-returned，计数始终0/0。原Snapshot参数保持use_vision=true/use_ui_tree=false/use_annotation=false，没有Screenshot、OS截屏或程序接口补图。

实际`call_tool`起点/结束单列保存，位于pacer等待后，共6对：ControlStatus、App、首Snapshot、唯一诊断ControlStatus、观察Snapshot、Alt+F4。两Snapshot真实调用分别为`831023.5183149→831023.8376679`、`831590.0435975→831590.3138417`，均成功返回图像；完成至下次开始远超4秒，只代表本次有界样本，不宣称4秒节奏修复工具。原is_error/text/structured/images及完整raw回执保留。

本次trace488行，正常`trace-closed/dropped=0`，未报告写入错误。两次`screenshot-enter→capture-pause→capture-resume(restored=true)→screenshot-return`完整，内部原图3840×2160，回执图下采样。**两张截图成功后，trace又各记录一次看门狗fail-open**，均为`control.py:_watch:554`，保留已求值`indicator_ok=false、desktop_ok=true`；记录时monitor_alive=true、active_calls0、emergency=true，首条指示层心跳年龄约1.078095秒。第二条记录瞬间年龄约0.000398秒并不推翻先前求值的false，因为字段为非原子快照、探测与日志时刻不同。原源码该分支在健康条件失败后调用fail-open，这支持本次指示层健康路径确实触发；没有额外采集health_probe内部细节，不能断言唯一底层原因或归因人为操作。

这两次fail-open发生在成功截图之后，不把时间邻近写成“截图导致故障”，不声称已复现历史截图CONTROL拒绝。本轮Click拒绝来自独立本地矩形断言；trace没有cursor-api调用，4条低层hook事件与正常Alt+F4关闭相关，不扩展为未执行的Click证据。完整trace已交父只读解释，历史NET/铜竞争仍failed，旧截图根因仍待独立确认。

一次初始Guard退避、本地Click拒绝后额外120秒静默、关闭后目标消失的Guard截止均保留。事件审计`early_requests=[]`；关闭退出后的retire、持有句柄及stop是本地生命周期操作，没有再发桌面请求。pre-stop-state保留token=`w011-observe`、failed=`w012-close`、not_before=`831891.3741435`、refused=true/diagnoses1/observations1/stage1，没有清除失败或重连。

窗口原Popen、只读UIA探针均exit0。五控制链12760/41348/67832/69596/72112在stop前持有查询句柄、创建时间核验后全部退出码0，termination_calls0，没有当前残留窗口/链。19项客户端冻结、父3启动器、原安装及隔离包各77文件均摘要一致；稳定22/固定23/实验22部署的文件名集合、字节数和SHA前后不变。产品候选启动0、产品/NET/铜竞争测试0，稳定0.10.0、main及前两轮failed报告保持，保留原Pi终端。

本地证据入口（Git忽略目录）：

- [原模型/会话](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/model.json)、[方案/19摘要/4测试](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/checkpoint-offline.json)、[测试日志](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/targeted-tests.log)、[客户端批准](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/phase-two-approval.json)、[父启动批准](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/parent-audits/compat-approval.json)。
- [本次只读UIA前置](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/uia-preflight.json)、[探针exit0](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/uia-probe-exit.json)、[App原回执](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/0003-App-raw.json)、[首图0004](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/0004-Snapshot-00.png)、[首图倍率原回执](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/0004-Snapshot.json)。
- [Click执行状态事实校正](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/click-execution-correction.json)、[唯一观察图0006](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/0006-Snapshot-00.png)、[真实调用起止](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/actual-calls.jsonl)、[完整trace](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/controller-trace.jsonl)、[trace汇总及两fail-open字段](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/trace-summary.json)。
- [窗口回调日志](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/window-events.jsonl)、[Popen exit0](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/window-exit.json)、[五链持有句柄exit0](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/chain-exit.json)、[原failed/budget保存](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/pre-stop-state.json)、[120秒审计](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/control-audit.json)、[完整性](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/integrity-result.json)、[结果与边界](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/verification-summary.json)、[证据索引](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-window-compat/evidence-index.json)。
