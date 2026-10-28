# 控制工具修复验收：预算恢复生效，App目标恢复仍受阻

本轮总体 **failed**：独立副本明确加载App刷新修复，恢复失败也正确进入新预算的refused状态，唯一diagnose实际执行，解决了前一基线的预算层断言；但真实App仍返回not found，随后只读诊断仍为非目标前景，未完成所要求的单组GUI序列。真实Snapshot、Click、Shortcut均为0，无有效图像或输入回调，不能判截图可靠性通过，历史NET/铜截图拒绝根因仍未知。唯一新窗口和完整控制链已正常exit0，不追加连接或窗口组。

- 本轮Task：`task_e389a3ccfaef`；Dispatch：`ctx_1f7869a00c74`；Run：`run_22b5092f9df3`，与已failed结算的基线Task分开。
- 分支：`verify/control-snapshot-fix`，从本地`origin/dev=621afcd10478b0051d840765d26b3020aec93c84`建立；基线分支和目录原件保留。本轮仅新增本报告，不合并推送。
- 保留Pi session：`01a1739a-82f6-76cf-9ffc-c63e95be56d4`，环境、JSONL model/reasoning变化及实际assistant记录均核对`deng/gpt-6.1-sol high`。
- 新证据：`../.local-analysis/control-snapshot-fix/`；新批准`msg_f57fc5c4defa`，18项客户端冻结、3项父启动器及77文件manifest绑定新Task/Dispatch。

本轮只新建一个指定标题Tk窗口，不启动任何产品候选。旧基线窗口39100与五控制链exit0前置已核对，未继承旧live-state、失败记录或inbox；本次从新任务状态启动，不把重启等同于消除拒绝。父持有tools/tests，工作者未修改父文件、安装包或隔离包字节。

新运行使用父指定`run_control_diagnostics.py`和`repair-approval.json`，显式`app_refresh_fix=true`，trace记录`app-refresh-fix-installed`，实际来源在已冻结的isolated目录。App修复先`get_state()`刷新窗口列表，再调用原`switch_app`，原窗口查找、激活与前景后验及ControlToolGate保持。客户端复制父Budget并仅缩为一组/四次截图，在restore分支调用`budget.restored(row)`；恢复失败后不继续组，保留一次诊断和一次观察只供收尾。原Guard字节、120秒、无image失败、唯一ID/parent、不排队及已执行动作不重发均保留。

仅新增3项针对性离线测试：恢复失败允许唯一诊断并拒绝输入、恢复成功后只一组、四次截图尝试上限，全部通过，0真实GUI/MCP。未重跑旧6项或父回归全集；父App刷新、预算及只读包装测试分别属于离线证据，不写成本次真实GUI通过。新窗口/客户端与正常生命周期关闭代码在批准前准备，运行后没有热改。

| 步骤 | 本次直接证据 | 判定与预算 |
| --- | --- | --- |
| f001/f002 | 唯一窗口PID65224，创建时间`134376429960216602`；client21804、launcher66940；创建唯一组 | 计数0/0，产品启动0 |
| f003首图 | 原生前检非目标前景，executed=false，截止`826585.2323526` | 预算一次Snapshot尝试，真实Snapshot0，未推进阶段 |
| f004目标恢复 | 完整120秒后ControlStatus允许，原生核对唯一标题/映像/birth/HWND9112128后真实App | `Error calling tool 'App': Application Pt Renew 控制诊断试验 not found.`，is_error=true、executed=unknown，停止组，不重发 |
| 预算恢复 | f004返回后`refused=true`、diagnoses0 | 与基线false不同，新增联动实际生效；不等于目标恢复成功 |
| f007唯一diagnose | App错误后额外完整120秒静默，实际ControlStatus及native执行，原生仍非目标前景 | 本次无预算AssertionError，diagnoses1；再次120秒锁存至`827019.4209059`，无第二诊断或观察 |
| f008/f009 | 截止后仅精确Popen身份一次WM_CLOSE生命周期关闭，原Tk回调正常返回，原Popen exit0退役 | 不作键鼠或GUI通过证据，计数仍0/0 |
| f010 | 先持有五链查询句柄，再正常stop，全部exit0 | 无强杀、无残留连接 |

f007保存的原生快照显示前景为Weixin，诊断窗口仍为PID65224/HWND9112128、TkTopLevel、完整标题`PT Renew 控制诊断试验`、rect `[1000,550,1916,1089]`。它证明窗口存在及同一身份，不能代替App的UIA查找成功或Snapshot。普通门禁没有为非目标前景发送Alt+F4，因此本轮无GUI关闭输入，使用的是预先明确授权的自建应用生命周期收尾。

父在本轮结束前告知另一个独立可达过滤路径：原`Desktop.get_windows`要求WindowPattern同时CanMinimize和CanMaximize，而本窗口脚本设置`resizable(False,False)`。父用真实`get_windows`加假控件的零桌面复现得到CanMaximize=false返回0个窗口、true返回1个。该证据支持不可最大化窗口可能被过滤，**本次没有取得对应现场UIA属性或窗口列表，所以不能确认它就是本次not found的全部原因**。此前缓存缺陷及本次过滤路径是不同条件；App刷新加载且仍失败，不能写成App现场修复已通过，也不能转而声称已找到旧截图故障根因。没有热改本窗口resizable设置、重复App或补跑候选。

`actual-calls.jsonl`在pacer等待后记录真实MCP起点/结束，原raw回执完整保留。本次只有三对调用：ControlStatus `826670.7007611→826670.7042246`、App `826670.7247439→826685.2248259`、唯一诊断ControlStatus `826899.404862→826899.4080219`，均为同主机monotonic秒。没有实际Snapshot，4秒节奏没有现场样本；没有通过Screenshot、OS截屏或程序接口补图。Tk逻辑屏幕记录2560×1440不是图片倍率证据，本轮没有有效图可核对坐标或计数。

trace共320行，含一次App刷新安装标记、154对rehook-recovery、原状态变迁及App begin/end，正常`trace-closed/dropped=0`，未报告写入错误。没有capture-pause/resume、screenshot、cursor-api、低层键鼠hook或fail-open事件，不能据日志空白断言这些未执行路径安全，也不把时间邻近当根因。诊断status附加字段未改变原state/generation/wait含义。

收尾严格限制在本client Popen自建窗口：先核对精确进程创建时间、完整pythonw映像、HWND→PID、完整标题和TkTopLevel，再一次`PostMessageW(WM_CLOSE)`，窗口原`WM_DELETE_WINDOW`回调记录normal-close/mainloop-returned，计数保持0/0。f009用原Popen证明exit0，未TerminateProcess；当前没有产品或其他窗口被关闭。原failed=`f003-initial`、token=`f001-launch`、截止、refused=true/diagnoses1状态保存未清除。

停止前持有21804/28716/31192/66940/71432五个精确创建时间查询句柄，正常stop后均退出码0。2次Guard原生拒绝均完整120秒，另有App错误后120秒外部静默记录，三段审计`early_requests=[]`；生命周期请求也在最后截止后，停止后没有再发桌面请求。原安装与隔离包各77文件、18项客户端冻结、父3项启动器及稳定22/固定23/实验22部署前后摘要相符。稳定仍0.10.0，固定0.11.0及产品竞争验收未通过状态不变；未改dist/main或原安装，未运行产品测试。

本地证据入口（Git忽略目录）：

- [模型与会话](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/model.json)、[新方案与18摘要](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/checkpoint-offline.json)、[3项变更测试](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/targeted-tests.log)、[新客户端批准](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/phase-two-approval.json)、[父修复启动批准](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/parent-audits/repair-approval.json)。
- [App完整原回执](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/0003-App-raw.json)、[真实调用起止](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/actual-calls.jsonl)、[f007唯一诊断原结果](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/f007-diagnose-complete.json)、[对应原生窗口快照](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/events/00022-native_result.json)、[父不可最大化过滤复现及限制](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/parent-audits/nonresizable-reproduction.json)。
- [控制器trace](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/controller-trace.jsonl)、[trace汇总](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/trace-summary.json)、[窗口原回调计数](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/window-events.jsonl)、[限定生命周期关闭](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/lifecycle-close-result.json)、[窗口Popen exit0](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/window-exit.json)、[五链句柄exit0](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/chain-exit.json)。
- [120秒审计](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/control-audit.json)、[完整性](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/integrity-result.json)、[最终结果与未覆盖](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/verification-summary.json)、[原failed/budget保存](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/pre-stop-state.json)、[证据索引](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/control-snapshot-fix/evidence-index.json)。
