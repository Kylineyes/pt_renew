# 监督器快照修复后的完整关闭现场

2026-10-29，本轮Task `task_be586c71f149` / Dispatch `ctx_9bdfefbc4379` / Run `run_5fe071294ef6`按限定范围 **succeeded**。本会话实际读两图0/0→1/1，双Tk回调落在原工具区间；唯一专用关闭取得严格成功回执、客户端原Popen退出0、退役及stop，全链无拒绝。正常资源7寿命3625上传及零账本、本组2880健康采样全部healthy、监督器与9个已发现子孙和已知外层原退出链均通过。快照发生一次临时权限重试，retry_count=1、failure_count=0；不宣称全部写入首次成功。

## 冻结、模型与批准

独立分支`verify/control-close-journal-live`，基线`671259c7c877039a43158e38738e0c33a8a7eb9b`。候选包含`a37ed03`的周期快照有界重试及失败锁存、原Popen持续等待修复，专用关闭和Guard未改。候选相关142项及最新149项原测试日志已核对为OK；源码未改，不重复全测，不把离线测试数相加。

实际Pi环境和原JSONL的model/thinking/assistant记录一致为`deng/gpt-6.1-sol high`，沿用session `01a18648-535d-720b-998d-63e4e0d5c42b`，不凭终端标题判断。[模型元数据](../.local-analysis/control-close-journal-live/model-after.json)保存原JSONL路径与摘要，[原会话快照](../.local-analysis/control-close-journal-live/session-after.jsonl)保留实际工具记录；两图由本会话实际read，父仅独立审计调用先后及回调，不冒称父读图。

候选为主工作树`main-2/.local-analysis/control-owned-close-v3/frozen-next/candidate`，111文件，清单SHA-256 `f5ebb7a8b4dfb6b50b378fd54e0ab4d47cedd693607b159391f287cabb066b0e`。新副本为主`.local-analysis/control-close-journal-live/execution`，R为client，tools/isolated同级；17客户端、13工具、77包、3监督器和完整111源码摘要核对，`client/plan.json`未改。[准备摘要](../.local-analysis/control-close-journal-live/prepared.json)及[离线审阅](../.local-analysis/control-close-journal-live/offline-review.md)保留。

新方案SHA-256 `955e074b48261000041499d53fb81b2fd45f6ed70b549f141bcee0561b180e6b`，父批准回复`msg_584c9cfcd3b5`同步绑定双方批准，只改message_id及permission_confirmed。全部原实验开关及owned_diagnostic_close模块摘要齐全，慢预检在启动前完成。见[原批准消息](../.local-analysis/control-close-journal-live/task-approval-messages.json)和[离线预检](../.local-analysis/control-close-journal-live/preflight.json)。用户既有必要控制授权持续有效，父说明具体时间/范围后批准，没有重复索权。

新[连续见证脚本](../.local-analysis/control-close-journal-live/launch-and-wait.py)以核验基础Python原Popen启动recorder→owner→launcher→runner，各层保存实际PID/birth/image/script及原Popen/原查询句柄；父独立持recorder/owner。runner直接运行冻结入口，内层持柄放行不等待代理消息。一次批准消息归档调用在服务前超时；只读核对当时没有批准归档、预检、启动回执或运行状态后，单独归档/预检并执行唯一启动，没有重启服务。新PowerShell串行辅助脚本首次离线Parser因无BOM中文解码报错，启动前加UTF8 BOM并复核通过；冻结源码未改。

## 单组GUI与输入证据

服务前准备[三段串行入口](../.local-analysis/control-close-journal-live/execute-phase.ps1)，每步依原Step.ps1成功回执才下一步，失败抛错，不排队、不重发；在真实读图处暂停。第一段launch→UIA→一次原App激活→begin-group→snapshot；首图实际read后第二段唯一Click→Ctrl+Shift+F8→snapshot；终图实际read后第三段close-owned→仅成功退役才stop。所有独立请求及回执保留。

唯一诊断窗PID `39620` / birth `134377475189979104` / HWND `7739364`，映像基础pythonw.exe，标题“PT Renew 控制诊断试验”、类TkTopLevel，UIA完整核对与原App激活后验通过。原Snapshot返回1920×1080图、原屏幕3840×2160、倍率2.0；物理rect为`[1500,825,2874,1634]`，线程DPI上下文恢复。实际[首图](../.local-analysis/control-close-journal-live/original-evidence/0003-Snapshot-00.png)显示0/0，图上按钮约`[988,603,1198,654]`，中心乘2.0后唯一Click `[2186,1257]`，位于物理rect内；见[坐标与读图记录](../.local-analysis/control-close-journal-live/first-image-observation.json)。实际[终图](../.local-analysis/control-close-journal-live/original-evidence/0006-Snapshot-00.png)显示1/1。

| 回调 | 原工具start | Tk真实回调 | 原工具end | 结果 |
| --- | --- | --- | --- | --- |
| Click | 931324.4381895 | 931324.5049036 | 931325.0069521 | 回调在区间内，1/0 |
| Ctrl+Shift+F8 | 931325.2574802 | 931325.2858942 | 931325.8235 | 回调在区间内，1/1 |

[原工具起止](../.local-analysis/control-close-journal-live/original-evidence/actual-calls.jsonl)为App1、Snapshot2、Click1、Shortcut2（诊断和关闭各一次）、ControlStatus0。仅一个连接/窗/组，未追加图像、聚焦或输入。窗口stdout/stderr空，真实回调无异常。没有更改指示层、原1秒阈值、心跳或保持输入集合。

## 唯一专用关闭与预算

| 关闭链事件 | 单调时间 | 原证据 |
| --- | --- | --- |
| close-owned请求 | 931728.543009 | 当前token与唯一原Popen绑定 |
| 原Shortcut起始 | 931728.5534015 | 只发送一次alt+f4 |
| Tk normal-close | 931728.5839129 | 计数保持1/1 |
| Tk mainloop-returned | 931728.5918546 | 自然关闭回调 |
| 原工具返回 | 931729.1174869 | `tool=Shortcut, arguments={shortcut:alt+f4}, is_error=false, text=[Pressed alt+f4.]` |
| 客户端原Popen退出 | 931729.1205314 | exit0，original_popen=true |
| 原绑定退役 | 931729.1227933 | 同PID退出0 |
| client stop | 931729.2441587 | 成功关闭已退役后停止 |

[关闭原回执](../.local-analysis/control-close-journal-live/original-evidence/j-s09-close-complete.json)、[原Popen窗口退出](../.local-analysis/control-close-journal-live/original-evidence/window-exit.json)、[真实窗口日志](../.local-analysis/control-close-journal-live/original-evidence/window-events.jsonl)及[stop回执](../.local-analysis/control-close-journal-live/original-evidence/j-s10-stop-complete.json)完整保留。关闭后没有再要求消失目标保持前景，也没有额外retire。最终failed=null、not_before=0、target=null、token=j-s09-close，事件中retreat/chain_halted/queue_rejected均0。没有WM_CLOSE、强杀、恢复或新连接。

原started `930969.9231912`，600秒诊断截止`931569.9231912`，900秒收尾截止`931869.9231912`，没有重置。最后诊断工具end `931326.308236`在600秒内；关闭开始剩141.3801822秒，满足35+5+40至少80秒。trace正常关闭`931729.2646204`，服务实际759.3414292秒，约12分39秒；超过父启动前预计5～10分钟，仍在原600/900硬预算内，不能把预计时间写成实际时长。两次真实读图检查点及模型往返占用服务内时间，详细审计在服务退出后执行。

## 资源、健康及快照结果

冻结audit_control_surfaces/replay_control_health独立读取同一原trace，6937行，唯一trace-closed、dropped=0，SHA-256 `fc2230c1d4b4dc38688e06aeae2ef7304cb0d90bbfe11fd86d7be5184b81a37f`。

[资源审计](../.local-analysis/control-close-journal-live/surface-audit.json)核对7个正常资源寿命、3625次上传，GetDC/ReleaseDC各3632，CreateCompatibleDC/CreateDIBSection/memmove/DeleteDC/DeleteObject各7，SelectObject14，UpdateLayeredWindow3625；最终surfaces/reserved_bytes/DC/bitmap/selected账本均0，正常阶段无API失败。

[健康重放](../.local-analysis/control-close-journal-live/health-replay.json)为2880次实际采样全部healthy，stale区间0、fail-open0。结果仅限本组，不证明长期稳定或性能倍率，上传数不与不等长旧样本直接比较提速。

SnapshotJournal实际`retry_count=1, failure_count=0, errors=[], truncated=false`。依据冻结实现，该一次重试来自周期快照临时PermissionError，第二次写入成功，原持柄/枚举继续；没有持续失败锁存，不等于所有文件写入首次成功或底层权限错误原因已消除。该修复的失败路径仍主要由离线测试覆盖，最终必要文件写入也不保证永不失败。

## 已知原退出链

| 进程 | PID / birth | 原退出证明 |
| --- | --- | --- |
| 监督器 | 69840 / 134377475074705323 | 握手/自身/runner身份一致；原Popen0、runner原查询句柄0 |
| runner | 51844 / 134377475072694882 | launcher持原Popen0、原句柄0 |
| launcher | 41692 / 134377475071922782 | owner持原Popen0、原句柄0 |
| owner | 26088 / 134377475071157290 | recorder持原Popen0、原句柄0；父独立原句柄0 |
| recorder | 61060 / 134377475070158431 | 父独立原查询句柄0；Start-Process创建，不冒称recorder原Popen证明 |

[监督器最终账本](../.local-analysis/control-close-journal-live/original-evidence/supervisor-chain-exit.json)含9个已发现子孙全部原持柄exit0，capture_errors空，客户端原Popen.wait=0；UIA原subprocess回执0，诊断窗另有客户端创建时原Popen退出0。runner独立重算完整processes而非仅信成功标记，见[runner结果](../.local-analysis/control-close-journal-live/original-evidence/runner-result.json)。外层见[runner原退出](../.local-analysis/control-close-journal-live/runner-popen-exit.json)、[launcher原退出](../.local-analysis/control-close-journal-live/launcher-popen-exit.json)、[owner原退出](../.local-analysis/control-close-journal-live/owner-popen-exit.json)、[父owner](../.local-analysis/control-close-journal-live/parent-owner-exit.json)、[父recorder](../.local-analysis/control-close-journal-live/parent-recorder-exit.json)。

没有runner-error、supervisor-fatal、client-fatal、硬截止遗留或退避原件，不以当前PID消失替代退出码。本轮已知链无遗留；50ms轮询仍不能排除整个寿命短于间隔的未知子进程，因此结论仅覆盖已发现且原持柄的链及独立原Popen探针。

## 分项结论与只读保护

| 项目 | 本轮结论 |
| --- | --- |
| 本会话双图0/0→1/1及双回调落真实工具区间 | 通过 |
| 一次专用Shortcut→严格返回→原Popen0→退役→stop且无拒绝 | 通过 |
| 正常资源寿命/API与零账本 | 通过，7寿命3625上传 |
| 本组健康 | 通过，2880全部healthy |
| 快照修复 | 本组通过，1次有界权限重试、0持续失败 |
| 监督器/9已发现子孙及已知外层原退出链 | 通过，exit0，范围限制保持 |
| 完整限定任务 | succeeded |

[独立最终审计](../.local-analysis/control-close-journal-live/final-audit.json)核对完整链和时限；父`parent-independent-live-audit.json`也独立核对本组成功边界。双方批准、方案和执行副本111源码均未变化。[只读前后摘要](../.local-analysis/control-close-journal-live/readonly-after.json)覆盖旧live172、旧candidate110、原包77及产品22/23/22，整个owned-close历史482、v3历史381、生命周期182、旧worker42及v3-worker204文件集合/SHA全同。

基线采用独立生命周期18:14:27收尾后的实际文件，包含旧窗口自然追加normal-close/mainloop-returned；旧发送前476字节前缀和157文件备份仍只读，不误称本轮变化。上一Task及更早failed/原退出缺口不因本轮成功改写。未改产品src、dist、原安装、其它工程或任何旧failed/token/截止。

本轮完整原回执、两图、回调、trace、stdout/stderr、批准和退出证据位于本工作树`.local-analysis/control-close-journal-live/`及主`.local-analysis/control-close-journal-live/execution/`，original-evidence为原件归档副本，证据不入Git。独立分支仅提交本报告，不自行合dev或推main；不启动产品竞争，不将本组成功提升为固定0.11.0、NET/铜完整竞争、长期稳定或性能改善。
