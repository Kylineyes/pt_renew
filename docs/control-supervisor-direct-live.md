# 直启监督器现场验收的启动前超时记录

本轮仅完成离线冻结核验和外层证据进程精确退出取证，现场验收未执行，整体按failed结算。外层driver在等待父持柄放行期间达到自身300秒启动前闸门期限，自行exit1；父许可回复及放行文件晚于该退出，监督器、控制客户端、MCP服务和自建窗口均未启动。没有重启、第二连接或第二组，也没有修改冻结源码来绕过期限。

## 本轮身份与批准

基线为`dev=a189389608bef20f59bebb09b83ba0de1bb089f4`，独立分支为`Kylineyes/verify-control-supervisor-direct-live`。Run为`run_6c0b4be9202f`，Task为`task_e972187b97ac`，Dispatch为`ctx_3a7ad6cbe5f7`；旧现场的failed Task没有恢复。本分支只提交本报告，不修改tools、tests、产品或既有文档，不合并dev/main、不推送。

实际环境为`PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`、`PI_SESSION_ID=01a1857f-0c9a-76fd-9e95-24e00935a192`。原会话文件为`C:\Users\rikideng\.pi\agent\sessions\--C--Users-rikideng-orca-workspaces-pt_renew-verify-control-supervisor-direct-live--\2026-10-29T02-30-58-458Z_01a1857f-0c9a-76fd-9e95-24e00935a192.jsonl`；已核对session、model_change、thinking_level_change及实际assistant工具调用的provider/model/thinkingLevel，未替换模型。见[模型环境](../../main-2/.local-analysis/control-supervisor-direct-launch/live/model.json)、[JSONL核对](../../main-2/.local-analysis/control-supervisor-direct-launch/live/model-jsonl-proof.json)和[启动前原JSONL副本](../../main-2/.local-analysis/control-supervisor-direct-launch/live/model-session-before.jsonl)。

用户此前已授权必要控制验收，本轮范围仍限15分钟、一个自建窗口、一个连接、一组双图双回调，服务600秒诊断、900秒收尾。两份新批准在source-ready时保持false/null，父审阅后才以`msg_75c09f673600`绑定true；见[服务批准](../../main-2/.local-analysis/control-supervisor-direct-launch/live/server-approval.json)和[客户端批准](../../main-2/.local-analysis/control-supervisor-direct-launch/live/phase-two-approval.json)。父以`msg_1b458e5f77d0`确认已持外层精确身份并允许释放闸门，该回复到达时driver已超时退出；内部冻结核验没有向用户重复索权。

## 冻结与启动架构

本轮证据目录为主工作区`.local-analysis/control-supervisor-direct-launch/live`，候选为同目录上级的`candidate`。[109文件清单](../../main-2/.local-analysis/control-supervisor-direct-launch/candidate-manifest.json)包含包77、包清单1、工具12、客户端及监督器19；17客户端及2监督器按原字节复制至live，inbox新建且始终为空，tools_root/package_root仍指向冻结candidate。旧`control-bitmap-surface/candidate-final/live`只读保留。

[本轮监督方案](../../main-2/.local-analysis/control-supervisor-direct-launch/live/supervisor-plan.json)填入新Task/Dispatch，SHA-256为`5e6d24e46442e3812fec12f36ccaa836c84da5cbc2b8cc6a10f61a5b197e072b`，两批准均绑定。17 reviewed_files来自本轮候选，服务绑定10个runtime工具；资源、health sampling/fix、app refresh、initial activation均为true，旧bitmap timing为false，geometry和target_activation摘要保持冻结值。

证据侧新增[outer-driver.py](../../main-2/.local-analysis/control-supervisor-direct-launch/live/outer-driver.py)及[worker-holder.py](../../main-2/.local-analysis/control-supervisor-direct-launch/live/worker-holder.py)仅使用标准库，父审阅记录见[parent-source-ready.json](../../main-2/.local-analysis/control-supervisor-direct-launch/parent-source-ready.json)。最终源码SHA-256分别为`4bbdb693605720020ef09ca2d00f59ec79d7052b50221a25bfa1d160817d094c`和`ef3e2941e6f5123d9d338fb89dea2d2fcbb8744d7e6ab34c67c203ea16b61dde`；它们不属于冻结19份客户端，未改动candidate。

已用原Popen探针核对基础解释器`C:\Users\rikideng\scoop\apps\python\3.15.2\python.exe`的实际PID等于Popen PID且exit0，见[基础解释器原件](../../main-2/.local-analysis/control-supervisor-direct-launch/live/base-python.json)。worker-holder直接以该基础Python的`-I -S`启动driver，原Popen一直持有至wait，并另持精确查询句柄复核退出；没有venv重定向外壳。driver设计为外部门先于WitnessLaunch构造，放行后才使用冻结WitnessLaunch直启监督器并自动完成其10秒握手release，客户端则由监督器显式选用冻结MCP venv解释器。这些后续路径本轮没有运行，不能把设计或历史离线测试当作本轮实际执行证据。

## 实际退出与时间线

| 实际进程 | 精确身份 | 退出正面证据 |
| --- | --- | --- |
| worker-holder | PID72056，birth134377152719906771 | 父持柄exit0 |
| outer-driver | PID66860，birth134377152720812578 | worker原Popen.wait exit1、独立精确句柄exit1；父持柄同为exit1 |

[worker-driver-held.json](../../main-2/.local-analysis/control-supervisor-direct-launch/live/worker-driver-held.json)记录原Popen参数、PID和创建时间；[worker-driver-exit.json](../../main-2/.local-analysis/control-supervisor-direct-launch/live/worker-driver-exit.json)直接证明退出码一致。父的[parent-held.json](../../main-2/.local-analysis/control-supervisor-direct-launch/parent-held.json)和[parent-exit.json](../../main-2/.local-analysis/control-supervisor-direct-launch/parent-exit.json)独立覆盖两进程；没有用PID当前不存在推断历史exit0。

文件时间显示两外层进程于2026-10-29 02:41:12 UTC启动，driver于02:46:12 UTC达到300秒门限并退出；[outer-driver-stderr.log](../../main-2/.local-analysis/control-supervisor-direct-launch/live/outer-driver-stderr.log)保留原RuntimeError“外部闸门300秒未放行，未启动监督器”。父放行后worker于02:47:10 UTC才写入[outer-driver-release.json](../../main-2/.local-analysis/control-supervisor-direct-launch/live/outer-driver-release.json)，随后发现超时，立即升级`msg_09422dd3e9d5`并询问父收口。晚到许可与失败原件均保留，没有修改门限、重启driver或恢复旧Task。

该300秒是外层证据进程启动前等待期限，与WitnessLaunch子进程自己的10秒身份期限、控制服务600/900秒预算各自独立。本轮未构造WitnessLaunch，因此没有实际监督器Popen、identity.json或supervisor-identity；没有客户端runtime-limits，服务预算从未起算，不能宣称在该预算内完成现场。父以`msg_c18c95430b2b`确认按failed收口、不重启，指出失败发生在启动编排等待阶段，并将后续本机持柄与放行自动化列为下一步；这不属于本轮模型、GUI或资源运行失败，既有115项离线测试结论仍保持其原有范围。

## 分项结果与限制

| 验收项 | 本轮结果 |
| --- | --- |
| GUI与原工具调用 | 未执行；Launch、UIA、App、Snapshot、Click、Shortcut、ControlStatus均未调用 |
| 图像实际read与双回调 | 未执行；没有首图0/0、终图1/1或窗口回调，不复用旧图或坐标 |
| 原生资源寿命与余额 | 未验证；无controller-trace，不能声称资源余额0、owner-exit/shutdown/closed或dropped0 |
| 健康重放 | 未验证；无本轮样本，不能声称healthy、无stale或稳定性修复 |
| 实际外层进程退出 | holder exit0、driver exit1均有精确持柄原件；driver失败码如实保留 |
| 监督器自身及客户端子孙链 | 未启动，未验收；不以外层进程退出替代 |

没有窗口，因此未执行Alt+F4、WM_CLOSE、退役、原stop或桌面冷却请求；没有failed/token状态可清除。没有本轮trace可供冻结`audit_control_surfaces.py`及`replay_control_health.py`审计，所以未运行它们来制造空数据通过结果。长期稳定性、性能倍率和产品竞争结论均未改变。

[before.json](../../main-2/.local-analysis/control-supervisor-direct-launch/live/before.json)与[after.json](../../main-2/.local-analysis/control-supervisor-direct-launch/live/after.json)核对原包77、旧隔离77、部署22/23/22、候选109及live19集合和SHA-256全部不变；after同时列出本轮应缺席的服务/窗口/调用证据，记录desktop_requests=0、service_started=false、supervisor_started=false、window_created=false。原证据及[证据摘要清单](../../main-2/.local-analysis/control-supervisor-direct-launch/live/evidence-manifest.json)留在.local-analysis，不提交Git。本轮失败事实应作为新安排前的审阅输入，不能在已结算Task上续投或追加现场。
