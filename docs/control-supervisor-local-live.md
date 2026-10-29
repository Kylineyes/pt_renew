# 本机连续启动器真实单组验收

本轮完成唯一一次真实现场验收：首图实际读取按钮/快捷键计数 **0/0**，一次按钮点击与一次 Ctrl+Shift+F8 后，终图实际读取 **1/1**；两次窗口回调都落在各自工具调用区间内。资源寿命、健康采样与完整已发现进程链退出分别通过。唯一 Alt+F4 已正常关闭窗口，但冻结客户端随后仍检查目标前景，触发 `s09-close` 后验拒绝，因此**完整无拒绝生命周期未通过**，不能把本轮写成全绿或长期稳定通过。

工作分支 `Kylineyes/verify-control-local-runner-live`，基线 `05e6cb05157a50fe5bf40eefb73718c095e2f8f5`。只新增本文及本机忽略证据，未修改 tools、tests、产品或既有文档；未合并 dev/main、未推送。

## 实际模型、任务与批准

实际运行器为 Pi，环境 `PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`，会话 `01a185da-259e-7031-a404-17572feabd0a`。原始 JSONL 的 `model_change`、`thinking_level_change` 与实际 assistant 消息均核对一致，未替换模型。证据见[模型核对](../.local-analysis/control-supervisor-local-live/model.json)、[启动前原始会话副本](../.local-analysis/control-supervisor-local-live/session-before.jsonl)及[审计后会话副本](../.local-analysis/control-supervisor-local-live/session-after.jsonl)。

本轮 Task `task_f45a13630a8b`、Dispatch `ctx_d0c7d529aa48`；父 source-ready 审阅批准消息为 `msg_d1dc0cf65510`。两份批准在启动前共同绑定方案 SHA256 `96ca53bfc141556f3e854ecbf47ebb4db8cd5de5a6a43c1fa86292a18ca6c962`，随后置 `permission_confirmed=true`、`message_id=msg_d1dc0cf65510`。此前保持 false/null，未启动 MCP 或访问桌面。批准保留用户允许的15分钟、一个自建窗、一个连接、一组双图双回调，诊断600秒、收尾900秒范围；资源实验、健康采样修复、App刷新和初始激活均为 true，旧 bitmap timing 为 false，geometry/activation 摘要与冻结工具一致。

[方案](../../main-2/.local-analysis/control-supervisor-local-runner/live/supervisor-plan.json)、[服务批准](../../main-2/.local-analysis/control-supervisor-local-runner/live/server-approval.json)与[客户端批准](../../main-2/.local-analysis/control-supervisor-local-runner/live/phase-two-approval.json)分别绑定17客户端与3监督器模块、实际会话、10项运行工具和隔离包清单。客户端自身完成任务、批准、真实模型、旧状态拒绝校验，没有绕过拒绝或热改源码。

## 离线冻结与连续启动

新建主工作区 `.local-analysis/control-supervisor-local-runner/live/` 及空 inbox，将唯一新 candidate 的 client20文件按原字节复制。`tools_root/package_root` 保留指向该新 candidate，未运行旧 direct/live、surface/live 或旧 outer-driver/worker-holder。候选110文件与其 manifest 一致，原控制包77、旧隔离77以及三套部署22/23/22文件与历史摘要一致；旧 direct109、surface107候选也均一致。启动后重算全部集合与 live20冻结摘要未变，见[before](../.local-analysis/control-supervisor-local-live/before.json)、[准备清单](../.local-analysis/control-supervisor-local-live/source-prepared.json)及[after审计](../.local-analysis/control-supervisor-local-live/after.json)。

[解释器探针](../.local-analysis/control-supervisor-local-live/preflight.json)提前证实基础 Python 3.15.2 的实际 PID 等于原 Popen PID；MCP venv 重定向至基础3.14.8，控制客户端仍使用冻结 venv，未混用解释器。证据侧[launch-and-wait.py](../.local-analysis/control-supervisor-local-live/launch-and-wait.py)启动前 SHA256 为 `8993f15cb71b26a1de50e923edf3600bd71ab38cce69abcc958dfc75f650a7cc`：基础 Python owner 只保留原 Popen 等待 launcher，launcher 直接 Popen 基础 Python 执行 live/control_supervisor_runner.py --root live，并持有原查询句柄、记录 PID/创建时间和真实退出码。runner 自行完成监督器 PID 握手、持柄与 release，没有代理往返、父放行短闸门或额外300秒闸门；父只读持 owner 精确身份辅助见证。

## 图像、坐标及回调

[初始被动观察](../../main-2/.local-analysis/control-supervisor-local-runner/live/initial-observation.json)在原 t0 后约10.085秒完成，只读日志显示 ready、资源 installed 且无失败。随后唯一 Launch 创建 PID27364，自建窗 UIA 核对 `TkTopLevel`、标题、PID/创建时间/HWND/映像，并通过原工具枚举；原 App 初始激活一次及精确前景后验通过，再 begin-group。

[首张原图](../../main-2/.local-analysis/control-supervisor-local-runner/live/0003-Snapshot-00.png)通过 read 实际查看，显示按钮0、快捷键0；[终张原图](../../main-2/.local-analysis/control-supervisor-local-runner/live/0006-Snapshot-00.png)通过 read 实际查看，显示按钮1、快捷键1。每张 PNG 为1920×1080，工具当次报告原桌面3840×2160、倍率2.0；当次物理矩形为 `[1500,825,2874,1634]`，坐标空间 physical-desktop-pixels、PER_MONITOR_AWARE_V2且线程上下文恢复。依据首图按钮约 `(1093,628)` 图像坐标，实际唯一点击使用物理坐标 `(2186,1256)`，未照抄历史坐标。

[实际调用日志](../../main-2/.local-analysis/control-supervisor-local-runner/live/actual-calls.jsonl)与[窗口回调日志](../../main-2/.local-analysis/control-supervisor-local-runner/live/window-events.jsonl)核对如下，时间均为同机 monotonic 秒：

| 输入 | call_tool 开始 | 回调 | call_tool 结束 | 计数 |
| --- | ---: | ---: | ---: | --- |
| 唯一 Click | 904877.7116159 | 904877.7782802 | 904878.2799898 | 1/0 |
| 唯一 Ctrl+Shift+F8 | 904897.7611422 | 904897.7974060 | 904898.3346294 | 1/1 |

窗口 stdout/stderr 长度均为0，无 callback-error；正常路径 ControlStatus 调用为0。总计一次原 App、两张 Snapshot、一次 Click、一次诊断 Shortcut及一次关闭 Shortcut；Launch为冻结客户端本地创建。

## 关闭拒绝、冷却与预算

唯一 Alt+F4 的实际工具区间为 `904969.7230045–904970.2779854`，工具 `is_error=false`，窗口在 `904969.7484171` 记录 normal-close，在 `904969.7574353` 记录 mainloop-returned，计数均保持1/1。随后冻结 Guard 仍执行目标前景后验，因窗口正常消失而返回 `completed=false/executed=true/phase=post_native`。这与正常关闭目标相冲突，是本轮暴露的守卫边界；本轮未修改冻结源码。

[关闭结果](../../main-2/.local-analysis/control-supervisor-local-runner/live/s09-close-complete.json)和[最终状态](../../main-2/.local-analysis/control-supervisor-local-runner/live/live-state.json)保留 failed=`s09-close`、token=`s08-after`、refused=true、cleanup=true、close_outcome=true。原120秒截止 `905090.2889986` 保留，期间客户端无新增 tool_request/native_request；未额外输入、截图、状态查询或原生桌面访问，未 diagnose、restore/resume、重连、第二组或重发关闭。到期后只执行 retire，取得原窗口 Popen exit0，再 stop；没有 WM_CLOSE补发、强杀或重启。

[原始预算](../../main-2/.local-analysis/control-supervisor-local-runner/live/runtime-limits.json)从客户端 t0=`904688.4145435` 起计，诊断截止 `905288.4145435`、收尾截止 `905588.4145435`，保留35秒请求余量。监督器/runner退出约在 t0+501.7秒，launcher约 t0+501.718秒，均早于原600/900秒截止，没有延期或重算 t0。

## 资源、健康与精确退出

运行候选中的冻结 `audit_control_surfaces.py` 和 `replay_control_health.py`，均为离线重放。[资源审计](../.local-analysis/control-supervisor-local-live/surface-audit.json)验证7个完整资源寿命、8887次上传，API计数如下：GetDC/ReleaseDC各8894，CreateCompatibleDC/CreateDIBSection/memmove/DeleteDC/DeleteObject各7，SelectObject14，UpdateLayeredWindow8887。owner-exit、shutdown均正常，trace-closed dropped0，退出 surfaces/reserved_bytes/DC/bitmap/selected_bitmap 全0，failed=false。[健康重放](../.local-analysis/control-supervisor-local-live/health-replay.json)为1898样本全部 healthy，无 stale 区间。这只覆盖本次有界单组，不证明长期稳定或性能倍率。

| 层级 | 实际 PID | 创建时间 FILETIME | 原退出证据 |
| --- | ---: | ---: | --- |
| 证据侧 owner | 29084 | 134377212254503815 | 原 Start-Process身份一致，父原精确句柄exit0 |
| 证据侧 launcher | 30772 | 134377212255320757 | owner原Popen wait0、原句柄0 |
| runner | 62600 | 134377212255961324 | launcher原Popen wait0、原句柄0 |
| 实际监督器 | 58784 | 134377212257949452 | runner内WitnessLaunch原Popen wait0、原句柄0 |
| 自建窗口 | 27364 | 134377212730770019 | 客户端原Popen retire exit0 |

[runner-held](../../main-2/.local-analysis/control-supervisor-local-runner/live/runner-held.json)、[监督器身份](../../main-2/.local-analysis/control-supervisor-local-runner/live/supervisor-identity.json)、[监督器链退出](../../main-2/.local-analysis/control-supervisor-local-runner/live/supervisor-chain-exit.json)与[runner-result](../../main-2/.local-analysis/control-supervisor-local-runner/live/runner-result.json)中实际监督器 PID/创建时间一致，方案SHA匹配，Witness目录的identity/popen-exit对应同一实际PID且退出0。链报告发现9个精确子孙身份，全部exit0、无重复、capture_errors为空，client原Popen0；未用进程当前不存在或venv父外壳0代替实际退出。

证据侧[runner原持柄](../.local-analysis/control-supervisor-local-live/runner-popen-held.json)/[退出](../.local-analysis/control-supervisor-local-live/runner-popen-exit.json)、[launcher原持柄](../.local-analysis/control-supervisor-local-live/launcher-popen-held.json)/[退出](../.local-analysis/control-supervisor-local-live/launcher-popen-exit.json)分别对应同一PID/创建时间且Popen与句柄均0。短命UIA探针另保留[原communicate退出回执](../../main-2/.local-analysis/control-supervisor-local-runner/live/uia-probe-exit.json)，窗口另保留[原Popen退出回执](../../main-2/.local-analysis/control-supervisor-local-runner/live/window-exit.json)。监督器每50ms枚举，无法排除整个生命周期短于采样间隔的未知进程；这些证据不声称无限覆盖。

owner 的[原始启动记录](../.local-analysis/control-supervisor-local-live/owner-start-process.json)与[自身身份](../.local-analysis/control-supervisor-local-live/owner-identity.json)一致，父在运行期间保存[精确持柄](../../main-2/.local-analysis/control-supervisor-local-runner/parent-owner-held.json)，并从同一原句柄取得[真实exit0](../../main-2/.local-analysis/control-supervisor-local-runner/parent-owner-exit.json)，未以当前不存在替代退出。父[独立全链审计](../../main-2/.local-analysis/control-supervisor-local-runner/parent-independent-live-audit.json)另外核对11113行 trace、closed/dropped0、原图 read 记录、回调、冻结集合和全部已知退出，服务寿命为501.2558秒；与本 worker 的独立离线审计结论一致。

本轮未续验。待后续独立任务修复关闭后的目标前景守卫边界，再用新的任务、批准及证据目录验证；本轮首次失败与所有原件保持。
