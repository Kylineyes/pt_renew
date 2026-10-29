# 第三份冻结候选的自建诊断窗关闭现场

2026-10-29，本轮Task `task_2978396a0432` / Dispatch `ctx_f2162fee7cf9` / Run `run_dc31bcdf4756`结论为 **failed**。实际首图0/0→终图1/1、双Tk回调、7个正常资源寿命7663次上传及零账本、本组3420次健康采样取得有效证据；唯一`close-owned`在发送原Shortcut前因非目标前景拒绝，Alt+F4调用0。监督器还在较早时刻发生账本文件替换PermissionError，监督器及外层原链退出1，子孙完整退出证明缺失。硬截止后诊断窗仍活，精确身份已留存，没有补关、恢复或重试。

## 独立任务及冻结

独立分支`verify/control-owned-close-v3-live`，基线`acb9c87743676dffe86631cdf658357e8e663c1f`；候选包含`837baf8`的见证器原截止内身份读取与构造异常Popen所有权修复。上一Task `task_304e9df22f4d` / Dispatch `ctx_818a32eb5b79`已failed结算，只读，不由本轮补验。

实际Pi环境与原JSONL的model/thinking/assistant记录均核对为`deng/gpt-6.1-sol high`，按本轮指令沿用session `01a18648-535d-720b-998d-63e4e0d5c42b`。[模型记录](../.local-analysis/control-owned-close-v3-live/model-after.json)保存原JSONL路径、快照摘要及逐条assistant元数据；[会话原快照](../.local-analysis/control-owned-close-v3-live/session-after.jsonl)含本会话两次真实read图片调用，父只审计日志，不冒称父读图。

已完整读四份要求文档并重新审阅见证器、专用关闭及client/budget/step/批准接入。140项原离线测试日志为`tests-handshake-fixed.log`，16.318秒、OK；源码未改，不重复全测。候选为主工作树`main-2/.local-analysis/control-owned-close/frozen-v3/candidate`，111文件，清单SHA-256 `85da8a4b12ba0eab3de813697640935d08c1169fbd845bc563d93ec3c02a5873`。

新运行副本为主`main-2/.local-analysis/control-owned-close-v3/execution`，client/tools/isolated同级，R为其中client。全111源码、17客户端、13工具、77包、3监督器摘要完整核对，`client/plan.json`未修改；copytree已有空inbox，使用`mkdir(exist_ok=True)`，没有恢复旧执行目录。[准备材料](../.local-analysis/control-owned-close-v3-live/prepared.json)和[离线审阅索引](../.local-analysis/control-owned-close-v3-live/offline-review.md)保存实际身份和完整摘要。

父审阅回复`msg_6dcabc521474`同时绑定两批准，仅更新新消息ID和permission_confirmed。新监督器方案摘要`56939e767bd96af128ed763e6744e1dd194ab0e22b32df7d3d46a2649cf23f3c`，外层脚本摘要`4ab1572b831cdbf6477b29ed777bdb7a7e7533940af2a0be489cd219a326a383`。[原批准消息](../.local-analysis/control-owned-close-v3-live/task-approval-messages.json)和[服务前离线预检](../.local-analysis/control-owned-close-v3-live/preflight.json)保留。父向用户说明预计启动时间及8～12分钟/600秒诊断900秒收尾范围后执行，没有重复索权或等待代理消息的短握手进程。

## GUI、回调及时间边界

基础Python原Popen连续链recorder→owner→launcher→runner仅启动一次；runner直接运行冻结`control_supervisor_runner.py --root R`，内部自行持柄放行，父另独立持recorder/owner精确句柄。新见证器这次成功读取实际监督器身份并放行，不能据此改写旧任务失败。

服务预算记录`started=915603.32172`，原诊断截止`916203.32172`、收尾截止`916503.32172`，未重置。被动初始ready耗时约10.168秒，未追逐ready重连。唯一窗口PID `66968` / birth `134377322138115927` / HWND `15010430`，映像为基础`pythonw.exe`，标题“PT Renew 控制诊断试验”、类`TkTopLevel`；UIA核对及一次原App激活后验通过。

本会话先实际read[首图](../.local-analysis/control-owned-close-v3-live/original-evidence/0003-Snapshot-00.png)，确认按钮/快捷键均0。原图1920×1080，工具回执明确屏幕3840×2160、坐标倍率2.0；核验物理rect `[1500,825,2874,1634]`，图上按钮边界约`[988,603,1198,654]`，中心换算后唯一Click为`[2186,1257]`，落在物理rect内。见[首图计算记录](../.local-analysis/control-owned-close-v3-live/first-image-observation.json)。随后唯一Ctrl+Shift+F8成功，再实际read[终图](../.local-analysis/control-owned-close-v3-live/original-evidence/0006-Snapshot-00.png)，确认1/1。

| 回调 | 原工具start | Tk真实回调 | 原工具end | 结论 |
| --- | --- | --- | --- | --- |
| Click | 916015.9078645 | 916015.9731906 | 916016.4753256 | 在工具区间内，计数1/0 |
| Ctrl+Shift+F8 | 916062.4724872 | 916062.5088199 | 916063.0466545 | 在工具区间内，计数1/1 |

[原调用记录](../.local-analysis/control-owned-close-v3-live/original-evidence/actual-calls.jsonl)为App1、Snapshot2、Click1、Shortcut1、ControlStatus0；窗口创建1，连接1，诊断组1。窗口stdout/stderr均空，未出现回调异常。最后诊断工具end为`916138.969407`，距600秒截止约64.352秒；运行中读图和步骤间隔占用了预算，实际已接近诊断末段，不能用预计8～12分钟替代原时钟。

## 专用关闭失败与冷却

唯一`v3-s09-close`在`916262.4248255`附近进入关闭前置检查，距原收尾截止约240.897秒，满足80秒预留。原native回执显示当前前景为WindowsTerminal PID `38652` / HWND `3606888`，目标窗口仍在枚举中；这只证明当时前景状态，不能归因具体操作者或把原因改称工具发送失败。

[关闭原回执](../.local-analysis/control-owned-close-v3-live/original-evidence/v3-s09-close-complete.json)为`completed=false, executed=false, tool_call_sent=false, returned=false, retired=false`，phase=preflight。没有原关闭Shortcut起止或成功回执，未等待原Popen退出。failed保持`v3-s09-close`，token保持`v3-s08-after`；not_before为`916382.4248255`，原截止不变。

首次拒绝后立停，完整120秒内没有输入、截图、ControlStatus或原生桌面请求；冻结事件与actual-calls独立核对，直到原硬截止也没有新桌面请求。没有resume/restore/第二组/新连接/重发/WM_CLOSE/强杀，没有退役或stop。原硬截止[回执](../.local-analysis/control-owned-close-v3-live/original-evidence/hard-deadline-exit.json)记录window_exit=null、outstanding_window=true，不因窗口未退出添加生命周期入口。

服务trace自然正常关闭于`916503.3769842`，从started计900.0552642秒；这是硬截止触发后服务正常退出的收尾开销，没有在截止后追加桌面动作。该组不能宣称在8～12分钟完成关闭，也不能宣称所有控制相关进程已退出。

## 资源及健康的独立重算

冻结审计器读取同一原trace，SHA-256 `c85a1e91f4b700451afb11258b4c0ae09762ce60193ee6507cf60d76a2cb0ae4`，11563行，唯一正常trace-closed、dropped=0。

[资源审计](../.local-analysis/control-owned-close-v3-live/surface-audit.json)核对7个正常资源寿命、7663次真实上传。GetDC/ReleaseDC各7670，CreateCompatibleDC/CreateDIBSection/memmove/DeleteDC/DeleteObject各7，SelectObject14，UpdateLayeredWindow7663；全部正常资源阶段无异常，最终surfaces、reserved_bytes及全部DC/bitmap/selected账本为0。

[健康重放](../.local-analysis/control-owned-close-v3-live/health-replay.json)核对3420次实际采样全部healthy，stale区间0、fail-open0，1秒原阈值保持。这只证明本组采样及正常资源记录；不证明长期稳定、性能倍率、无诊断CPU因果或产品验收。

## 监督器故障、原退出与遗留

监督器PID `66892` / birth `134377321408778195`成功握手并运行，但约15:28:14替换`supervisor-chain-held.json.tmp`→`supervisor-chain-held.json`发生PermissionError。原[监督器fatal](../.local-analysis/control-owned-close-v3-live/original-evidence/supervisor-fatal.json)保留原子孙账本和client_popen_exit_code=null；其后账本不再更新，缺少`supervisor-chain-exit.json`。runner读取缺失退出报告而失败，保留[原Popen及句柄证据](../.local-analysis/control-owned-close-v3-live/original-evidence/runner-error.json)，没有强杀或重启。

| 进程 | PID / birth | 原证据 |
| --- | --- | --- |
| 监督器 | 66892 / 134377321408778195 | 原Popen=1、原查询句柄=1，实际身份/握手一致 |
| runner | 43336 / 134377321406801205 | launcher所持原Popen=1、原句柄=1 |
| launcher | 6000 / 134377321406046900 | owner所持原Popen=1、原句柄=1 |
| owner | 29384 / 134377321405271390 | recorder所持原Popen=1、原句柄=1；父独立句柄=1 |
| recorder | 29820 / 134377321404282941 | 父独立原查询句柄=1；Start-Process创建，无recorder原Popen证明 |

上述原件见[runner](../.local-analysis/control-owned-close-v3-live/runner-popen-exit.json)、[launcher](../.local-analysis/control-owned-close-v3-live/launcher-popen-exit.json)、[owner](../.local-analysis/control-owned-close-v3-live/owner-popen-exit.json)、[父owner](../.local-analysis/control-owned-close-v3-live/parent-owner-exit.json)、[父recorder](../.local-analysis/control-owned-close-v3-live/parent-recorder-exit.json)。其中verified=true只指退出码一致，绝非exit0或任务成功。

监督器停止前已发现9个子孙，UIA两个进程38032/birth134377322327682509和25596/birth134377322327757710原持柄exit0，UIA原subprocess回执也为0。客户端/解释器/服务等其余退出码原账本为null；晚到只读OpenProcess失败不补成exit0。子孙窗口66968/birth134377322138115927在`916999.5823846`晚到精确查询时仍live，映像为`C:/Users/rikideng/scoop/persist/uv/python/versions/cpython-3.14.8-windows-x86_64-none/pythonw.exe`，HWND/标题/类以上述本轮原核验为准；没有再请求桌面。

[遗留查询](../.local-analysis/control-owned-close-v3-live/residual-processes.json)和[最终独立审计](../.local-analysis/control-owned-close-v3-live/final-audit.json)保存每个PID/birth和证据缺口。50ms枚举不能排除未知短命进程，本轮监督器中途故障也使已发现链不完整；原Popen与迟到句柄证据严格区分，当前PID不存在不能替代原始退出码。遗留窗口仍需负责人另行安排独立生命周期处理，本Task没有关窗补验授权或动作。

## 分项结论及保护核对

| 验收项 | 本轮结果 |
| --- | --- |
| 实际双图0/0→1/1、双回调落原工具区间 | 通过，仅限本组 |
| 专用关闭一次成功→原Popen退出0→退役→stop，全链无拒绝 | 失败，preflight拒绝且关闭工具调用0 |
| 正常资源寿命/API/最终零账本 | 通过，7寿命7663上传 |
| 本组健康采样 | 通过，3420全部healthy |
| 监督器/全部已发现子孙/外层原链exit0 | 失败，已知链exit1、子孙原证据缺口及窗口live |
| 完整现场任务 | failed，不由分项通过覆盖 |

[前后只读摘要](../.local-analysis/control-owned-close-v3-live/readonly-after.json)核对旧live172、旧candidate110、原包77、稳定/固定/实验22/23/22、v1/v2/v3各111、旧失败execution119及旧worker证据42文件集合及摘要全同。执行副本111源码、方案和绑定后的双方批准均未变化。未改产品src、dist、原安装、其它工程或旧failed/token/截止。

本轮原回执/两图/回调/trace/stdout/stderr/批准/退出与遗留证据保存在本工作树`.local-analysis/control-owned-close-v3-live/`，其中original-evidence为只读归档副本；主`.local-analysis/control-owned-close-v3/execution/`保留实际原件。证据不入Git，分支仅提交本报告，不自行合dev或推main；旧任务结果不改，后续修复与新验收另行处理。本组结果不扩展为固定0.11.0、NET/铜完整竞争、长期稳定或性能通过。
