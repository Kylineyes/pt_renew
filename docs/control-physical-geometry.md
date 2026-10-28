# 物理窗口矩形修复与有界诊断组验证

本轮按限定目标 **succeeded**：在一个新诊断连接、一个自建窗口中，UIA/原工具枚举前置通过，App恢复后首张原Snapshot实际读图为0/0；物理矩形包含按钮坐标，随后一次真实Click、一次`Ctrl+Shift+F8`和最终原Snapshot顺序执行成功，最终图已实际读取按钮/快捷键计数1/1。全部进程正常exit0。窗口逐输入回调日志存在独立缺口，下文明确披露；本次成功范围只是坐标Guard及这一组GUI，不代表历史CONTROL_UNAVAILABLE或产品NET/铜竞争已通过。

本轮Task `task_30f766b66866`、Dispatch `ctx_900f441db397`、Run `run_22b5092f9df3`，沿用Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`。环境、JSONL模型/推理记录及实际assistant核对`deng/gpt-6.1-sol high`。分支`verify/control-physical-geometry`从本地`origin/dev=621afcd10478b0051d840765d26b3020aec93c84`建立，新证据`../.local-analysis/control-physical-geometry/`；仅提交本报告，不合并推送，父持有tools/tests。

| 历史阶段 | 保留结论 |
| --- | --- |
| 初诊断基线 | failed，App not found与恢复预算断言，未进入截图 |
| App/预算修复验收 | failed，预算唯一诊断已可达，App仍not found，未进入截图 |
| 可缩放窗口兼容 | failed，UIA/原枚举、App和首图通过；物理点与DPI虚拟化rect比较导致本地Click未调用 |
| 本轮物理矩形修复 | 限定单组通过：真实输入后图像0/0→1/1；旧失败不改写，历史控制故障仍未知 |

新驱动只针对我们自己的坐标边界错误适配。原native逻辑rect保留，`DiagnosticGuard.observe_native`新增父`physical_window_rect`读取，前后用持有进程句柄核验目标PID、精确birth、完整映像和HWND归属。父函数临时切线程`PER_MONITOR_AWARE_V2`读取GetWindowRect后finally恢复原DPI context；未知或恢复失败拒绝，不猜矩形、不按1.5手乘、不删除边界保护。last_rect只接受`coordinate_space=physical-desktop-pixels`、有效矩形及线程恢复true，Click工具前验证点在内。

本地边界拒绝的新语义也已单独处理：若在调用transport前拒绝，返回`executed=false,tool_call_sent=false`并追加事实校正事件；原底层attempted日志不抹去，真正工具调用异常仍保留unknown和失败锁存。3项新增定向测试覆盖物理点进工具、逻辑/界外点零调用、明确false与真实传输异常unknown的区别，全部通过。未重跑旧测试集；父几何6项回归是另有离线证据，本轮不重复叠加。

新批准`msg_cf104996b2fc`绑定19项客户端文件及父几何摘要`8e5840d9f66c388c88e95e09bde4af8dcc4c6ef628e0a701bb6f40ca80bc1ee6`，父server的3启动器/77包manifest及新Task/Dispatch分别核验。保留可缩放窗口、原UIA前置、App刷新、恢复预算、120秒与原ControlToolGate，不加载父后续health修复。旧compat全部exit0是新连接前置，没有恢复旧PID或向旧inbox续投。

| 步骤 | 本次直接结果 |
| --- | --- |
| g001/g002 | 唯一自建PID9392、birth`134376529269810550`、HWND16188842；CanMinimize/CanMaximize均true，原Desktop.get_windows确含同HWND；探针只读无激活/输入并exit0 |
| g003/g004 | 唯一组建立；首图前非目标前景，executed=false，无真实Snapshot；完整120秒后恢复 |
| g005/g006 | 原App刷新恢复成功、原生后验通过，显式resume |
| g007首图 | `0004`原Snapshot有效且已实际读图0/0，Original3840×2160/返回1920×1080/倍率2 |
| 物理几何 | 逻辑rect `[1000,550,1916,1089]`保留，物理rect `[1500,825,2874,1634]`，coordinate_space明确且线程context已恢复 |
| g008 Click | 图按钮中心约(1093,628)，按回执×2传(2186,1256)，在物理rect内；一次真实Click成功，不再被逻辑rect拒绝 |
| g009/g010 | 一次真实`Ctrl+Shift+F8`及原Snapshot均成功；`0007`最终图实际读到按钮1/快捷键1，唯一组完整结束 |
| g011关闭 | 优先Alt+F4的原生前检看到非目标终端，executed=false，未调用关闭Shortcut，完整120秒静默 |
| g012/g013/g014 | 仅本Popen精确身份一次WM_CLOSE生命周期正常关闭，Popen exit0退役；持有五链精确身份句柄后正常stop，全部exit0 |

调用顺序经同Guard逐步await且失败即停。本次Click、测试Shortcut和最终Snapshot在同一依赖命令段顺序执行，之前首图已读；没有第二Click、第二快捷键、第二组或连接，没有为补结果重发。原Snapshot use_vision=true/use_ui_tree=false/use_annotation=false，无Screenshot、OS截屏或程序接口造计数。

真实MCP `call_tool`起点/结束均位于本地pacer等待后，共6对：ControlStatus、App、首Snapshot、Click、测试Shortcut、最终Snapshot。首图`836828.2212404→836828.4963771`，Click `837011.4960617→837012.0600338`，Shortcut `837012.3360231→837012.9030121`，最终图`837013.1848469→837013.4551737`，单位同主机monotonic秒；全部原工具回执is_error=false。间隔满足本地4秒节奏，本轮没有真实截图/输入控制拒绝，不用此事实宣称历史拒绝已消除。

**窗口逐回调日志不完整。** 冻结window.py的`record(kind,**fields)`与update中的`record('input-callback',kind=kind,...)`重名；update先增加counts/设置status，再尝试写日志，参数冲突会导致该输入日志无法写入。本次window-events确实没有两条input-callback；子窗口使用pythonw且未单独重定向stderr，没有保存原TypeError traceback，不能伪造“捕获到异常堆栈”。运行中没有修补或补试。首图0/0、最终图1/1和各一次真实工具调用是单组通过的直接依据；正常关闭和mainloop-returned另记录终态1/1，只确认终态，不能补作逐输入时间线。父也独立读图和actual-calls认可该限定范围。

controller trace与窗口日志分开：本轮trace561行正常`trace-closed/dropped=0`，含两次完整capture pause/resume和screenshot-return、一次cursor API对、10条低层hook；没有fail-open事件或真实CONTROL拒绝。trace零丢失不修复窗口日志缺口。此前compat成功截图后两次watch fail-open仍是旧轮独立证据，本轮未复现不能当作health根因或修复通过，门禁/健康阈值没有放宽。

收尾前g011发现前景已变为其他终端，原关闭输入未发送；原预算把关闭前检拒绝保留failed但refused仍false，唯一diagnose不适用，本轮没有为了该条件再试诊断或输入。完整截止后用已批准的自建生命周期请求，只对本Popen核验birth/image/HWND/title/TkTopLevel，发送一次WM_CLOSE，原Tk正常关闭回调退出，`keyboard_mouse_calls=0,termination_calls=0`。它不是诊断输入或GUI关闭成功证据。Popen与探针exit0，原failed=`g011-close`、token=`g010-final`及budget/截止保存，未清状态或重连。

五链28572/32540/39248/40104/64624停止前均持有精确创建时间匹配查询句柄，正常stop后全部exit0，无强杀或残留。两次Guard前景拒绝均完整120秒，审计`early_requests=[]`。19客户端、父3启动器及1几何工具冻结摘要、原安装与隔离77文件、稳定22/固定23/实验22部署文件名集合/字节/SHA前后保持。未启动任何PT Renew候选、产品竞争或产品测试，稳定0.10.0、main和历史验收结论不变，原Pi终端保留。

本地证据入口（Git忽略目录）：

- [模型会话](../.local-analysis/control-physical-geometry/model.json)、[19摘要与3项测试](../.local-analysis/control-physical-geometry/checkpoint-offline.json)、[测试日志](../.local-analysis/control-physical-geometry/targeted-tests.log)、[客户端批准含几何摘要](../.local-analysis/control-physical-geometry/phase-two-approval.json)、[父启动批准](../.local-analysis/control-physical-geometry/parent-audits/geometry-approval.json)。
- [本次UIA前置](../.local-analysis/control-physical-geometry/uia-preflight.json)、[首图0004](../.local-analysis/control-physical-geometry/0004-Snapshot-00.png)、[首图倍率](../.local-analysis/control-physical-geometry/0004-Snapshot.json)、[物理矩形/点包含审计](../.local-analysis/control-physical-geometry/geometry-audit.json)、[真实Click原回执](../.local-analysis/control-physical-geometry/0005-Click-raw.json)、[测试Shortcut原回执](../.local-analysis/control-physical-geometry/0006-Shortcut-raw.json)、[最终1/1图0007](../.local-analysis/control-physical-geometry/0007-Snapshot-00.png)。
- [真实调用起止](../.local-analysis/control-physical-geometry/actual-calls.jsonl)、[controller trace](../.local-analysis/control-physical-geometry/controller-trace.jsonl)、[trace范围/限制](../.local-analysis/control-physical-geometry/trace-summary.json)、[窗口日志缺口](../.local-analysis/control-physical-geometry/window-log-limitation.json)、[窗口原始日志](../.local-analysis/control-physical-geometry/window-events.jsonl)。
- [生命周期精确关闭](../.local-analysis/control-physical-geometry/lifecycle-close-result.json)、[窗口Popen exit0](../.local-analysis/control-physical-geometry/window-exit.json)、[五链句柄exit0](../.local-analysis/control-physical-geometry/chain-exit.json)、[原failed/budget保存](../.local-analysis/control-physical-geometry/pre-stop-state.json)、[门禁审计](../.local-analysis/control-physical-geometry/control-audit.json)、[完整性](../.local-analysis/control-physical-geometry/integrity-result.json)、[结果与限制](../.local-analysis/control-physical-geometry/verification-summary.json)、[证据索引](../.local-analysis/control-physical-geometry/evidence-index.json)。
