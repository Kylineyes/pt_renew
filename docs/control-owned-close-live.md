# 精确自建诊断窗专用关闭：本轮启动失败

2026-10-29，本轮Task `task_304e9df22f4d` / Dispatch `ctx_818a32eb5b79` / Run `run_0ca568a11b7b`结论为 **failed**。唯一一次连续runner在读取监督器见证子进程的身份JSON时遇到`PermissionError`，未放行目标脚本，客户端、控制服务和诊断窗均未启动。没有调用桌面工具、输入或读取截图，不能形成新的GUI、关闭、资源或健康通过结论；未重试、未改运行源码或批准、未恢复任何旧任务。

验收分支`Kylineyes/verify-control-owned-close-live`初始基线`69bdc821952ebc57e2ae301cfd1be71b802f226c`，按父新冻结通知快进到源码`81ae57b7fe760dd814bdcccec60190dc1359a85c`。实际Pi环境、原JSONL的model/thinking记录及assistant记录一致为`deng/gpt-6.1-sol high`，session `01a18648-535d-720b-998d-63e4e0d5c42b`，不根据终端标题判断。见[模型证据](../.local-analysis/control-owned-close-live/model-after.json)和[原会话快照](../.local-analysis/control-owned-close-live/session-after.jsonl)。原JSONL路径完整保存在模型证据中。

## 冻结审阅与批准

已完整读`AGENTS.md`、`SESSION_HANDOFF.md`、`docs/control-next-stage.md`和`docs/control-owned-close.md`，审阅专用关闭模块、client/budget/step/driver/Step.ps1、原Guard/DiagnosticGuard、双方批准及连续监督器链。父在启动前补强了空白或畸形Shortcut回执的拒绝逻辑，提供第二份独立冻结；本轮仅使用`main-2/.local-analysis/control-owned-close/frozen-v2/candidate`，111文件，清单SHA-256为`cfca1f09dbc38ce905c0edb33d2b97120588775065598f4dad849c9341922103`。旧frozen保持只读。

第二版关闭路径只允许本轮客户端原Popen绑定，完成唯一诊断组后，经过原门禁和精确目标/前景检查，至多一次原Shortcut Alt+F4；严格核对冻结成功回执，再等待原Popen退出0并退役。错误、取消、未知和超时保留失败token/冷却/截止，普通输入的后验保持。限定范围离线审阅未发现关闭模块的阻断缺陷；父提供的137项假API及无GUI测试通过，仅作为离线证据，不替本轮现场。见[离线审阅索引](../.local-analysis/control-owned-close-live/offline-review.md)。

完整候选复制到`main-2/.local-analysis/control-owned-close/execution`，保留client/tools/isolated同级关系，`client/plan.json`未改。17客户端、13工具、77文件包及3监督器均纳入批准或监督器冻结。最初离线脚本创建已存在的空inbox目录报错；核对副本仍完全等于111文件清单且没有批准/状态后，只恢复离线准备，没有服务或截止重置。

父审阅消息`msg_fa696d8887f7`同时绑定两份新批准，仅将`message_id`和`permission_confirmed`更新为批准值。监督器方案SHA-256为`3f0893ee53369e6b6c0b8ef9175d4ba419bd165d1a61b59ce756488ca3f89595`，本轮Task/Dispatch及实际session写在批准/方案中。[原批准消息](../.local-analysis/control-owned-close-live/task-approval-messages.json)、[完整准备摘要](../.local-analysis/control-owned-close-live/prepared.json)、[离线预检](../.local-analysis/control-owned-close-live/preflight.json)保留。基础Python探针、`require_client_approval`及runner `preflight`均在启动前通过；审阅时没有服务、runner或等待代理放行的短握手进程。

## 唯一启动与失败边界

本机14:27:54（UTC+08:00）唯一启动证据侧recorder，连续原Popen链为recorder→owner→launcher→runner。runner由已核验基础Python直接启动冻结`control_supervisor_runner.py --root R`，每层立即持原查询句柄、记录实际映像和脚本摘要，再等待原Popen，没有额外消息闸门。父另独立持recorder/owner的精确句柄。见[本轮见证脚本](../.local-analysis/control-owned-close-live/launch-and-wait.py)和[runner原Popen持柄](../.local-analysis/control-owned-close-live/runner-popen-held.json)。

实际runner PID `25956` / birth `134377288749999125`。`WitnessLaunch.__init__`已创建握手子进程，但读取`witness-0599a2bea2be459b9f12ab1230865d4b/identity.json`时发生`PermissionError: [Errno 13] Permission denied`。错误点早于runner持监督器句柄及`launch.release()`；`runner-error.json`保存`held_identity=null`，握手目录没有release原件，目标监督器脚本未执行。见[runner原stderr](../.local-analysis/control-owned-close-live/runner-stderr.log)，主执行目录的`runner-error.json`、握手身份和stderr保持原件。

握手身份原件记录PID `50968`、正确基础Python映像和监督器脚本摘要。其原stderr显示10秒期限内未取得放行并抛出“目标脚本未执行”异常。构造器在该读取异常时没有把已经创建的Popen附到异常，runner局部`launch`仍为None，因此没有该child的原Popen等待或原查询句柄退出码；本轮将其退出证明记为**unverifiable**。事后进程查询未发现该PID只作观察，不能补成退出码0或1；权限错误的底层成因也未在本轮证明。

客户端/服务未启动，`runtime-limits.json`、`live-state.json`、`controller-trace.jsonl`、`actual-calls.jsonl`、监督器身份/子孙账本、窗口启动及回调原件均不存在。因此600/900秒服务预算没有起算，控制请求、创建窗口、原App、Snapshot、Click、Shortcut、ControlStatus均为0。没有真实控制拒绝或需要执行120秒零桌面退避的服务阶段；没有发stop/retire/WM_CLOSE或强杀，没有重连、第二组或重启。

## 分项结果与原退出证据

| 项目 | 本轮结论 | 证据与限制 |
| --- | --- | --- |
| GUI两图/双回调 | 未执行，未通过 | 实际read图片0，输入回调0，不能继承旧组通过 |
| close-owned完整无拒绝链 | 未执行，未通过 | 原Shortcut关闭调用0、未退役、未stop |
| 资源寿命/上传/零账本 | 未执行，未通过 | 没有服务trace或真实上传，不调用空输入伪造通过 |
| 本组健康采样 | 未执行，未通过 | 没有实际健康采样，不能继承旧组healthy |
| 监督器与全部已知退出链exit0 | 失败 | 目标监督器未执行；外层非0退出；握手child原退出码缺口 |
| 冻结及只读保护 | 通过 | 本轮两个111候选、执行源码、双方批准、旧证据/原包/产品逐文件摘要一致 |

冻结`audit_control_surfaces.py`及`replay_control_health.py`的原字节已独立核对；由于未产生trace，没有可重算的现场资源或健康样本，本轮不生成这两项通过报告。50ms枚举不能排除未知短命进程的限制保持；本次甚至未进入监督器枚举，不宣称全部子孙已退出0。

| 进程 | PID / birth | 原始退出证明 |
| --- | --- | --- |
| recorder | 26424 / 134377288747467761 | 父持原查询句柄退出1；由Start-Process创建，本轮没有recorder原Popen证明 |
| owner | 16608 / 134377288748492676 | recorder所持原Popen=1、原句柄=1；父独立原句柄=1 |
| launcher | 3504 / 134377288749245461 | owner所持原Popen=1、原句柄=1 |
| runner | 25956 / 134377288749999125 | launcher所持原Popen=1、原句柄=1 |
| 握手child | 50968 / birth未取得 | 身份JSON及原异常存在，原Popen/持柄退出码缺失，unverifiable |

对应原件：[owner](../.local-analysis/control-owned-close-live/owner-popen-exit.json)、[launcher](../.local-analysis/control-owned-close-live/launcher-popen-exit.json)、[runner](../.local-analysis/control-owned-close-live/runner-popen-exit.json)、[父owner](../.local-analysis/control-owned-close-live/parent-owner-exit.json)、[父recorder](../.local-analysis/control-owned-close-live/parent-recorder-exit.json)。`verified=true`仅表示该原Popen与句柄的退出码一致，并不表示退出0或任务成功。

## 结算与只读核对

[最终独立审计](../.local-analysis/control-owned-close-live/final-audit.json)核对本轮旧/新冻结各111文件、执行副本111源码、方案和双方批准均未变；[最终只读保护](../.local-analysis/control-owned-close-live/readonly-after.json)核对旧live172、旧candidate110、原包77、稳定/固定/实验22/23/22文件集合及摘要全同。旧截图、failed/token、原预算和批准原件保持。产品src、dist、原安装及其它工程未改，不重建或执行产品。

本工作树仅新增本报告与忽略目录中的审计脚本/证据。证据位于本工作树`.local-analysis/control-owned-close-live/`及主工作树`.local-analysis/control-owned-close/execution/`，不入Git。本任务按父消息`msg_08deae00144d`只读结算failed；后续见证器修复和重新验收另行冻结、批准及新Task，不在本组补验。137项既有离线测试保持其原结论，不能覆盖本次真实启动失败，也不能提升固定0.11.0、NET/铜竞争、长期稳定性或性能结论。
