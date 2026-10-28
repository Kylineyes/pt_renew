# 不可变图层资源复用现场验收记录

本次完成唯一自建诊断窗口的双图、双真实回调及原生资源正常寿命取证：图中计数由0/0变为1/1，7个surface完成8509次上传并退役，资源账本归零；1188条健康采样均为healthy。**整体验收未完全通过**：正常Alt+F4关闭后原前景检查保守锁存；最终还发现实际监督器进程缺少独立精确句柄退出记录，不能宣称完整退出链均已验收。没有重新启动、补做第二组或修改冻结候选。

## 身份、批准与冻结范围

本次Run为`run_3cd747640832`，Task为`task_142ea7a86a8d`，Dispatch为`ctx_af9c3c5211fd`。验收分支实际名称为`Kylineyes/verify-control-bitmap-surface-live`，从`dev=9e4bdb6fe0bcadc82c8649008b1c0ea90b5aa7c8`建立；仅提交本报告，由父工作区审核整合，不合并dev/main、不推送。

实际环境为`PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`、`PI_SESSION_ID=01a18478-da17-72cd-a114-3faf5c2359f1`。`PI_SESSION_FILE`为`C:\Users\rikideng\.pi\agent\sessions\--C--Users-rikideng-orca-workspaces-pt_renew-verify-control-bitmap-surface-live--\2026-10-28T21-44-35-096Z_01a18478-da17-72cd-a114-3faf5c2359f1.jsonl`。核对了原JSONL的session、model_change、thinking_level_change和实际assistant工具调用字段，没有恢复旧会话或替换模型，见[实际模型](../../main-2/.local-analysis/control-bitmap-surface/live/model.json)及[JSONL读取证明](../../main-2/.local-analysis/control-bitmap-surface/live/model-jsonl-proof.json)。

用户许可为“你控制电脑（15分钟单组方案）”，父随后转达补充“需要控制电脑验收允许控制”。新[服务批准](../../main-2/.local-analysis/control-bitmap-surface/live/server-approval.json)与[客户端批准](../../main-2/.local-analysis/control-bitmap-surface/live/phase-two-approval.json)绑定本Task/Dispatch、实际provider/session及批准消息`msg_1a6c61a97e8d`；准备期间均为false/null，父审阅后才设为true并启动。父精确持有外层见证器后，以`msg_91f09129fff9`允许释放[启动闸门](../../main-2/.local-analysis/control-bitmap-surface/live/supervisor-start.json)。

唯一运行证据目录为主工作区`C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/control-bitmap-surface/live`。冻结源仅使用`candidate-final`；107文件由隔离包77、包清单1、工具12、客户端17组成，运行批准绑定其中10个工具。17份客户端原样复制到live，tools_root/package_root仍指向冻结candidate-final，UIA确实从本轮批准package_root读取。旧candidate/candidate-v2、中间模板、旧inbox和假API轨迹均未运行。

[运行前摘要](../../main-2/.local-analysis/control-bitmap-surface/live/before.json)与[运行后摘要](../../main-2/.local-analysis/control-bitmap-surface/live/after.json)核对：原控制包77、旧隔离77、稳定22、固定23、实验22，以及冻结候选107和复制客户端17的文件集合与SHA-256完全一致。产品源码、tools、tests、dist及冻结候选没有变更，本机证据不入Git。

## 单组GUI与原工具调用

服务原始`t0=881484.7400924`，被动观察于`881494.9402321`完成，耗时约10.20秒。只读新链日志确认原ready、健康记录、保持集合和唯一`indicator-surface-installed`，且资源未失败，才Launch，见[初始观察](../../main-2/.local-analysis/control-bitmap-surface/live/initial-observation.json)。

唯一自建窗PID30384、birth134376980420992563、HWND5115138，映像为既有CPython3.14.8的pythonw.exe。只读[UIA前置](../../main-2/.local-analysis/control-bitmap-surface/live/uia-preflight.json)核对唯一标题、TkTopLevel、WindowPattern、PID/HWND/映像/创建时间及原工具窗口枚举；来源路径属于candidate-final。随后只执行一次原App初始激活，精确前景后验通过，再begin-group。

本Pi worker使用read工具实际读取[首图0003](../../main-2/.local-analysis/control-bitmap-surface/live/0003-Snapshot-00.png)和[终图0006](../../main-2/.local-analysis/control-bitmap-surface/live/0006-Snapshot-00.png)，分别看到按钮/快捷键计数0/0和1/1。父只读审计调用和日志，不冒称父读图。[读图记录](../../main-2/.local-analysis/control-bitmap-surface/live/visual-review.json)保留判断依据：原图3840×2160，返回图1920×1080，倍率2.0；物理窗口矩形为[1500,825,2874,1634]，按钮点击物理坐标为[2188,1256]，没有混用逻辑DPI矩形。

[原工具起止](../../main-2/.local-analysis/control-bitmap-surface/live/actual-calls.jsonl)只有App1、Snapshot2、Click1、Shortcut2；两个Shortcut分别为Ctrl+Shift+F8和正常Alt+F4，ControlStatus0。原Step.ps1/driver每次只提交一项，无输入重发、额外截图、重连或第二组。

| 真实回调 | 原工具开始 | 回调时刻 | 原工具结束 | 回调后计数 |
| --- | --- | --- | --- | --- |
| Click | 881591.8697975 | 881591.9344489 | 881592.4363253 | 1/0 |
| Ctrl+Shift+F8 | 881603.5456676 | 881603.5771427 | 881604.1112452 | 1/1 |

[窗口事件原件](../../main-2/.local-analysis/control-bitmap-surface/live/window-events.jsonl)的两条真实Tk回调分别位于上述原call_tool起止内，window-stdout.log和window-stderr.log均为0字节，没有callback-error。

## 正常关闭、故障锁存与时间预算

a009于`881658.251497`开始唯一Alt+F4，原工具正常返回。窗口记录normal-close/mainloop-returned，随后post_native发现目标窗口消失，保守拒绝“非目标前景或目标PID/HWND归属不匹配”；[a009原结果](../../main-2/.local-analysis/control-bitmap-surface/live/a009-complete.json)明确`executed=true`。这不是一次无失败的完整请求链，不能用窗口正常关闭覆盖掉锁存。

a010只查询原Popen退出码并退役，保存[窗口exit0](../../main-2/.local-analysis/control-bitmap-surface/live/window-exit.json)。未再次Alt+F4、WM_CLOSE、restore-target、resume或诊断。`failed=a009`、`token=a008`、refused/cleanup及`close_outcome=true`均保留在[最终状态](../../main-2/.local-analysis/control-bitmap-surface/live/live-state.json)。

首次拒绝在`881658.8203022`建立120秒截止`881778.8203022`，期间没有新增输入、截图、状态或原生桌面请求；精确Popen退役不访问桌面。完整冷却结束后又过约22秒，才提交a011原stop。服务日志在`881801.1927921`正常closed，持续316.4527秒，约5分16秒。

[原始预算](../../main-2/.local-analysis/control-bitmap-surface/live/runtime-limits.json)始终不改：诊断截止`882084.7400924`，收尾截止`882384.7400924`。全部诊断动作在600秒内，停止服务和已记录进程退出在900秒内，没有自动延期或重新起算。

## 原生API寿命与健康

对本次真实[controller-trace](../../main-2/.local-analysis/control-bitmap-surface/live/controller-trace.jsonl)运行冻结`audit_control_surfaces.py`，得到[独立资源审计](../../main-2/.local-analysis/control-bitmap-surface/live/surface-audit.json)：9958行日志，7个正常寿命，8509次真实上传，异常0。

| 操作 | 每寿命/每次的正常API集合 | 本次合计 |
| --- | --- | --- |
| initialize | GetDC、CreateCompatibleDC、CreateDIBSection、SelectObject、memmove、ReleaseDC各1 | 7次初始化/复制 |
| upload | GetDC、UpdateLayeredWindow、ReleaseDC各1 | 8509次完整上传 |
| retire | SelectObject、DeleteDC、DeleteObject各1 | 7次退役 |

累计GetDC/ReleaseDC各8516、CreateCompatibleDC/CreateDIBSection/memmove/DeleteDC/DeleteObject各7、SelectObject14、UpdateLayeredWindow8509。逐surface身份、尺寸/字节、API次数/失败数、分段与起止时间均与冻结正常schema一致。owner-exit和shutdown各1，cleanup_errors0、balanced=true，surface/屏幕DC/内存DC/位图/选择关系/保留字节余额全部0、failed=false；最后trace-closed/dropped0。

冻结`replay_control_health.py`的[健康重放](../../main-2/.local-analysis/control-bitmap-surface/live/health-replay.json)与原记录一致：1188样本均healthy，没有stale区间或fail-open。本次单组没有观察到过期，不能证明历史稳定性问题已修复。父独立审计记录上传墙钟总计约4.25547秒、最慢约0.108514秒；这些数包含诊断和调度成本，本次还增加50ms进程枚举开销，不能与历史不等长样本直接推导性能改善、CPU成本、倍率或唯一根因。

trace SHA-256为`231a46f329f303ba20106d0c5c24fc291b516e7ff0afd8449bd3c2911b1fa86d`。本次真实trace与离线fake-api-trace严格区分，假API测试未作为现场证据。

## 退出证据与未满足项

冻结hold-chain只在身份出现后枚举一次并等待60秒，无法覆盖本次启动与后续子孙。父事先审阅并批准证据侧[supervisor.py](../../main-2/.local-analysis/control-bitmap-surface/live/supervisor.py)和[launch-witness.py](../../main-2/.local-analysis/control-bitmap-surface/live/launch-witness.py)，摘要见[源码复核](../../main-2/.local-analysis/control-bitmap-surface/live/supervisor-source-review.json)。监督器不调用桌面、不结束进程、不热改客户端；仅用原Popen及ProcessWitness保存查询句柄并登记子孙，沿用原runtime-limits，不延长控制许可。

[监督器链退出](../../main-2/.local-analysis/control-bitmap-surface/live/supervisor-chain-exit.json)逐个精确见证15328、64868、67748、16540、70704、30384、42524、11528均exit0，包含客户端、服务子孙、唯一窗口及UIA探针链；capture_errors为空、termination_calls0。[UIA原子进程回执](../../main-2/.local-analysis/control-bitmap-surface/live/uia-probe-exit.json)也保存exit0。外层原Popen保存[监督器启动器28300的exit0](../../main-2/.local-analysis/control-bitmap-surface/live/supervisor-exit.json)；父[持柄原件](../../main-2/.local-analysis/control-bitmap-surface/parent-witness-held.json)及[退出原件](../../main-2/.local-analysis/control-bitmap-surface/parent-witness-exit.json)证明29836、11208均exit0。

**完整退出取证仍有缺口**：[launcher.json](../../main-2/.local-analysis/control-bitmap-surface/live/launcher.json)记录实际监督器PID66568/birth134376980173644750，[supervisor-launch.json](../../main-2/.local-analysis/control-bitmap-surface/live/supervisor-launch.json)记录外层Popen为venv启动器28300。66568没有独立持柄退出记录，不能以28300或PID列表消失替代其精确exit0，也不能事后对已结束PID补造证据。此项已在[退出限制](../../main-2/.local-analysis/control-bitmap-surface/live/exit-limitation.json)及父消息`msg_7d1b20a32444`明确升级，父以`msg_60af79ade97c`确认没有66568原持柄证据，并要求整体按failed结算。[当前身份查询](../../main-2/.local-analysis/control-bitmap-surface/live/supervisor-current-presence.json)仅显示已知PID66568当前不存在，不作为exit0证据；没有控制、终止、重启或事后伪补，本轮不补验。

[worker离线核对](../../main-2/.local-analysis/control-bitmap-surface/live/live-validation.json)和[父独立审计](../../main-2/.local-analysis/control-bitmap-surface/parent-independent-live-audit.json)支持双图/回调、正常资源路径、健康样本及已持柄进程的分项结论；这些审计中的既有all_exit0仅覆盖各自记录集合，不覆盖缺失的66568。整体验收按退出条件未完全满足记录为未通过。稳定产品仍0.10.0，固定0.11.0、NET／铜完整竞争及控制稳定性修复结论均不因本组改变。
