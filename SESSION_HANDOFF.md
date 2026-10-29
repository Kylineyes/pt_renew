# PT Renew 当前进度与新会话交接

更新时间：2026-10-30。最新阶段为[产品客户端离线实现与冻结时限](docs/async-product-client-offline.md)，从已核对的`dev=origin/dev=f81576f83397900fd0c861765c57da928d313228`建立`feat/async-product-client-offline`。新增默认禁用的request/read/ack、NET/铜编排、产品Qt主窗/dirty模态及原Popen正常退出核心，30项新增测试和仓库234项Python测试全部通过。原22/23/22、旧事件/输入、最新控制及归档等10组参考按历史摘要口径全部匹配。产品启动/桌面请求0，没有新Task/Dispatch或批准；ready_for_live=false。

本阶段交接入口为[下一阶段](docs/control-next-stage.md)、[客户端约束](docs/async-product-client-contract.md)与本机`.local-analysis/async-product-client-offline/NEXT_AGENT_BRIEF.md`；原`.local-analysis/NEXT_AGENT_BRIEF.md`不改，按前阶段历史读取。下一步先以指定模型新上下文验证原read image记录兼容性及两图顺序时限，再补冻结的Win32/MCP现场适配器、文件框阶段和原Popen全链启动/见证接入。T1/T2/T3设计为触发前原时钟起算20/50/55秒，原60秒上限不变，尚无新的实际模型计时证明。必要控制授权持续；新现场先完成可审阅材料并说明具体时间/范围，不恢复旧failed/abandoned任务或执行其准备脚本。

以下保留2026-10-29及更早历史，旧结算和证据范围不变。前阶段[产品竞争离线预检](docs/async-race-offline-preflight.md)只增加事件/实际read时序审计工具及10项变异测试；此前71.019/88.949秒实际read区间及旧release缺少read关口的问题保持其历史结论。

此前[完整关闭现场](docs/control-close-journal-live.md)按限定succeeded结算：本会话两图0/0→1/1及双回调、一次原Shortcut Alt+F4严格回执→客户端原Popen退出0→退役→stop，全链无拒绝；7寿命3625上传零账本、2880健康全healthy，监督器及9已发现子孙和已知外层原链exit0。快照发生1次临时权限重试、0持续失败。先完整读本机`.local-analysis/NEXT_AGENT_BRIEF.md`、[AGENTS.md](AGENTS.md)、本文及[下一阶段](docs/control-next-stage.md)。

**当前控制限定缺口已取得本组证据，无已知遗留或后台控制。普通输入目标后验未删，旧failed/token/截止/退出码缺口保持。实际服务759.3414秒约12分39，超过预计5～10分钟但在原600/900预算内；50ms未知短命进程、长期稳定和性能倍率不因此通过。稳定产品/dist仍0.10.0，固定0.11.0及NET/铜完整竞争仍未过。下一步先离线准备独立产品竞争方案，本轮不启动产品。**

**此前acb9c87阶段新增实现默认禁用，绑定客户端创建时保存的原Popen；只在精确身份/门禁/前景核验后尝试一次原Shortcut Alt+F4，严格回执及原Popen退出0后退役。普通输入的目标后验保持。137项离线测试通过后按新Task/Dispatch唯一启动，但见证器身份文件读取PermissionError导致服务/桌面请求/窗口均0，现场failed；外层已知链exit1，握手child原退出码缺失保持unverifiable。随后仅离线修复见证器握手读取及构造失败原Popen所有权，140项测试全部通过，第三份111文件候选已冻结但未运行、无新任务/批准。本轮失败及所有旧证据不变，不追加连接补验。**

**稳定产品及dist仍为0.10.0，固定0.11.0候选和NET／铜完整竞争仍未通过。此前本机连续启动器限定任务succeeded：单组双图/双回调、7个正常资源寿命8887次真实上传/零账本，以及监督器和全部已知控制链的原始exit0证据通过；1898次健康采样全healthy，仅为本组结果。正常Alt+F4关闭后的目标前景守卫仍保守拒绝，失败token及120秒限制原件保留，完整无拒绝关闭流程尚未通过。未知短命进程覆盖、长期稳定性与性能倍率未获证明。该轮控制已正常退出；此前已结算验收会话按用户要求归档，目前累计5个闲置agent窗格关闭，历史JSONL/工作树/证据保留，无后台控制或自动续验。**

## 产品与冻结部署

| 对象 | 已实现/已有证据 | 当前边界 |
| --- | --- | --- |
| 稳定0.10.0 | PCB/LIB/NET只读查看、图层显隐、缩放平移、选择/定位、两点测量及端点捕捉、引脚映射、受限铜层分析 | 非完整DRC，文字/部分轮廓有近似 |
| 固定0.11.0候选 | 单条自由Track整数mil内存移动/删除、Undo/Redo、dirty/clean、关闭/换图保护、派生失效、外部NET保留重映射 | 整体验收未过；无保存/另存为、新增图元、拖拽、元件移动、布线或生产输出 |
| 独立异步实验 | 默认OFF的`PT_ENABLE_ASYNC_EXPERIMENT`、NET/铜工作线程门闩、看门狗与修订/回调事件 | 正向对照有GUI证据，完整竞争均未完成；不能替固定候选记通过 |
| 原字形 | 静态/受控执行及部分原程序现场研究 | `runtime_verified=false`，未接入Qt渲染/命中/铜分析 |

| 冻结部署（相对主工作区） | 文件数 / EXE SHA-256 |
| --- | --- |
| `dist/pt-renew.exe` | 22 / `726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1` |
| `../feat-basic-editing/.local-analysis/basic-editing/release-candidate/pt-renew.exe` | 23 / `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8` |
| `../experiment-async-result-barrier/.local-analysis/async-experiment/release-candidate/pt-renew.exe` | 22 / `782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac` |

固定源码`Kylineyes/feat-basic-editing=b0e5ac7761f13690b5310bbc913ab7bfd2691d08`；实验`experiment/async-result-barrier=c4e3ec5e82bf1a022e523ec8844d0665d7b93234`（实验代码`98a4321`）。主build可能是历史0.11.0构建，不凭分支猜EXE版本，不重建覆盖冻结部署。本轮未修改产品src、CMake版本、dist、候选或原安装，main仍由用户操作。

## 最新有效结果与限制

[产品竞争离线预检](docs/async-race-offline-preflight.md)没有启动产品或桌面。`tools/audit_async_race.py`只重算同应用时钟事件链，任何事件通过仍gui_verified=false；中止路径返回aborted不当有效竞争。10项变异测试通过。读图时序引用最近成功控制组原工具起止及实际read成功image回执，不将327.085/402.250秒完整检查点区间归因于纯模型推理。独立归档图演练Task `task_75f8102028b0` / Dispatch `ctx_1bed19e5ff05`在准备阶段因指定Pi连接错误/超时被父取消：Task failed、Dispatch failed、worker abandoned，processAction=none，资源保留、reclaimable0，无worker_done；request/read/ack均未开始、无时序结果，不换模型或新Task绕过。见[演练报告](docs/async-image-review-rehearsal.md)。

[完整关闭现场](docs/control-close-journal-live.md)：Run `run_5fe071294ef6` / Task `task_be586c71f149` / Dispatch `ctx_9bdfefbc4379`，唯一done `msg_b4ea15337528`限定succeeded父验收ack，报告`b87b3c8`已整合。批准`msg_584c9cfcd3b5`，实际Pi `deng/gpt-6.1-sol high` session `01a18648-535d-720b-998d-63e4e0d5c42b`，131条assistant及两次本轮read成功image回执核对。6937行trace closed/dropped0、7寿命3625上传/零账本、2880healthy/fail-open0；close-owned严格成功→原Popen0→退役→stop无拒绝。监督器69840/birth134377475074705323、9已发现子孙/runner51844/launcher41692/owner26088原退出0，父recorder61060/owner原句柄0；snapshot_retry1/failure0。所有旧482/381/182/172/110/77及产品22/23/22、worker42/204摘要全同。worker-release external_terminal retained/processAction=none、reclaimable0，任务已结算。

本轮[独立生命周期](docs/control-residual-lifecycle.md)通过，操作`lifecycle_e727f4cea876`仅处理残留窗，不创建控制连接或诊断组。冻结来源/工具/方案→只检查身份唯一→独占一次机会→复核完整身份→一次WM_CLOSE→同一新查询句柄exit0；没有键鼠/聚焦/强杀，没有原Task恢复或结果更改。149项测试和只读保护见报告。本次窗口原日志自然追加必须与旧归档区分，发送前完整备份保留。

此前[第三候选现场](docs/control-owned-close-v3-live.md)：Run `run_dc31bcdf4756` / Task `task_2978396a0432` / Dispatch `ctx_f2162fee7cf9`，唯一done `msg_bf13a30cf0e2`为failed并父验收ack，报告提交`e1259d6`。两批准绑定`msg_6dcabc521474`，实际沿用Pi `deng/gpt-6.1-sol high` session `01a18648-535d-720b-998d-63e4e0d5c42b`，96条assistant记录及两次read图片核对。双图0/0→1/1、双Tk回调在原工具start/end、11563行closed/dropped0、7寿命7663上传零账本、3420健康全healthy成立；close-owned在前景为WindowsTerminal时preflight拒绝，AltF4调用0，120秒及后续零桌面请求直到900秒原硬截止。监督器66892账本替换PermissionError后exit1，runner/launcher/owner原Popen及句柄均1，父recorder/owner原句柄均1，子孙完整原退出证明缺失；精确窗66968仍live。旧172/110/77和产品22/23/22、上一阶段482文件及旧worker42文件集合/摘要全同。worker-release仍为external_terminal retained/processAction=none，任务已结算，reclaimable为空。

此前[专用关闭启动现场](docs/control-owned-close-live.md)：Run `run_0ca568a11b7b` / Task `task_304e9df22f4d` / Dispatch `ctx_818a32eb5b79`，done `msg_a7125e2d3539`按failed结算并验收ack，worker报告`8d41db3`已整合。Pi `deng/gpt-6.1-sol high`、session `01a18648-535d-720b-998d-63e4e0d5c42b`，两批准绑定`msg_fa696d8887f7`。启动前PermissionError早于监督器放行；GUI/关闭/资源/健康均未执行，不能继承旧现场通过。runner25956、launcher3504、owner16608原Popen/句柄exit1，父recorder26424/owner原句柄exit1；握手child50968缺原退出码保持unverifiable。父独立审计核对旧172/110/77、产品22/23/22和本轮两个111候选/执行源码/批准全同。第三份待验候选和140项离线结果独立保存，不改本轮失败。worker-release回执为external_terminal/retained/processAction=none，验收Pi终端仍闲置保留，任务已结算且无reclaimable资源。

以下为此前有效现场与历史结果，结论保持原范围。

[本机连续启动器现场](docs/control-supervisor-local-live.md)：Run `run_2ca10ef14e2f` / Task `task_f45a13630a8b` / Dispatch `ctx_d0c7d529aa48`，唯一done `msg_e0448797f2ae`按限定succeeded验收ack。实际Pi `deng/gpt-6.1-sol high`、session `01a185da-259e-7031-a404-17572feabd0a`，两批准绑定`msg_d1dc0cf65510`。冻结candidate110/live20/包77/旧隔离77/部署22/23/22摘要均不变。原App1、Snapshot2、Click1、Shortcut2、ControlStatus0；指定worker实际read两图0/0→1/1，父核对原JSONL读图调用与双回调区间，不冒称父读图。

真实trace11113行closed/dropped0；7寿命8887上传，DIB/兼容DC/复制/释放各7，SelectObject14，GetDC/ReleaseDC各8894，最终账本0。1898健康全healthy/fail-open0。上传墙钟4.2648431秒、最慢0.1085396秒，包含诊断与50ms进程枚举开销，不与旧不等长样本直接推导提速。

本机runner在短期限内连续持柄/放行，监督器58784/birth134377212257949452的握手/Popen/原生句柄/自身身份/子孙报告一致exit0；9个已发现子孙全exit0、capture_errors空；runner62600、launcher30772的原Popen和句柄均0，owner29084由父原句柄证实exit0。50ms枚举不能排除未知短命子进程，窗口/UIA另有原Popen回执。服务501.2558秒、约8分21，诊断/收尾都在原600/900预算内。s09-close AltF4已实际正常关闭，随后post_native拒绝，原failed/token/120秒限制保留，冷却后只retire/stop，不重发或重连。

以下为更早阶段的历史，失败与证据缺口不由本组追溯改写：

基于`dev=a189389`安排的新监督器现场在服务启动前超时，详见[本轮记录](docs/control-supervisor-direct-live.md)：Run `run_6c0b4be9202f` / Task `task_e972187b97ac` / Dispatch `ctx_3a7ad6cbe5f7`，done `msg_e35383efeaef`按failed结算。driver66860在300秒外部门截止先于父放行退出1，holder72056退出0，均有父精确持柄及driver原Popen/句柄证明。监督器、客户端、服务、窗口均未启动，桌面请求0，不能形成新资源/健康/GUI结论；晚到放行、旧源码和状态原件保留，不重启。worker报告4e9fa90已整合，验收Pi窗格按用户要求关闭归档，目前累计4个闲置窗格已关闭，历史JSONL/工作树保留。115项离线测试保持有效，109候选及19客户端/原包/部署摘要不变。

此前已执行GUI的[资源复用现场](docs/control-bitmap-surface-live.md)：Run `run_3cd747640832` / Task `task_142ea7a86a8d` / Dispatch `ctx_af9c3c5211fd`，唯一done `msg_893d1c0c6eee`按failed结算。实际Pi `deng/gpt-6.1-sol high`、session `01a18478-da17-72cd-a114-3faf5c2359f1`。服务316.4527秒，原App1、Snapshot2、Click1、Shortcut2、ControlStatus0；两图实际0/0→1/1，双回调均落工具起止内，窗口stdout/stderr空。Alt+F4执行后目标消失保守锁存a009，原Popen exit0退役，完整120秒零桌面请求后原stop；无WM_CLOSE、重发或第二组。

真实trace9958行closed/dropped0；7寿命、8509上传、创建DC/DIB/复制各7、SelectObject14、GetDC/ReleaseDC各8516，退役后账本0。1188健康样本全healthy/fail-open0；上传墙钟约4.25547秒、最慢0.108514秒，不与历史不等长样本直接推导提速。原包/隔离77/77、部署22/23/22与candidate107集合及摘要不变。

8个持柄子进程、父持11208/29836以及监督器启动器28300原Popen exit0有证明；实际监督器66568没有原持柄退出码，当前不存在不补作exit0。父早期审计保留，最终以`.local-analysis/control-bitmap-surface/parent-independent-live-audit-corrected.json`更正结论为准。后续`control_witness_launch.py`以基础Python直启、实际PID握手和原Popen等待修正此缺口，4项无GUI子进程测试通过，其后完成本机连续启动器及本组新现场验证；旧66568退出缺口仍保留。

以下为此前[初始激活/旧位图计时现场](docs/control-initial-activation.md)的独立历史结果，对应原Pi验收会话实际读图；父侧仅审计日志，不冒称父读图：

- 一次原App初始化及精确PID/birth/HWND/映像/标题/物理矩形前景后验成功。首图实际0/0，真实Click和Ctrl+Shift+F8各一次，终图实际1/1，两条Tk回调分别落原工具调用起止内，stdout/stderr空。
- 原调用App1、Snapshot2、Click1、Shortcut2（诊断快捷键及Alt+F4关闭各一次），ControlStatus0；没有第二组/连接。服务约764.531秒（12分45秒），全部诊断动作600秒内，正常退出900秒内。
- 4081次真实位图上传，尺寸/字节匹配；每上传SelectObject2，其余8个资源/API阶段各1，正常路径清理完整、上传异常0。总上传墙钟5.187942秒、最慢0.3109134秒；memmove占总上传墙钟约26.01%，UpdateLayeredWindow约18.31%。这些值含调度和诊断成本，不是CPU成本，不证明某API是唯一根因或无诊断环境性能。
- 2883条实际健康采样逐行一致，其中2stale（watch约1.0200467秒、恢复输入线程约1.1905275秒，同旧heartbeat），1次watch fail-open，`indicator_ok=false,desktop_ok=true`。此前先读心跳修复已加载，真实滞后仍发生；不声称健康稳定、全部历史截图根因或产品竞争已通过。
- 7384行trace正常closed/dropped0，209项本机证据/17链接；父整合交付56链接通过。Alt+F4已正常关闭，之后post_native目标消失保守锁存原件保留；只凭Popen exit0退役，无再次关闭、WM_CLOSE或强杀。窗口/探针及完整五链全exit0，原77/隔离77和稳定22/固定23/实验22前后文件集合及摘要相同。

**三个问题应分别判断。** 旧`user`回执有最近输入事件持续刷新10秒空闲的直接证据，服务也曾正常ready，不能归因操作者；两次位图尝试因门禁/非目标前景未进入上传路径；最新一次原App初始化越过前景阻碍，才取得有效上传与真实滞后样本。这些结果互不替代。

## 工具与验证状态

工具行为、开关及使用限制见[工具说明](docs/control-diagnostics-tools.md)。所有可选运行时包装只在冻结且明确批准的新隔离进程加载；已安装第三方包未改，不在活服务热改。

| 文件 | 用途及完成范围 |
| --- | --- |
| `tools/audit_async_race.py` | 纯离线重算应用事件链/真实read先后及时间条件；10项测试通过，事件通过仍不授予GUI通过 |
| `tools/control_diagnostics.py` | 原方法只读阶段/状态/原因日志，有界队列、独立写线程、丢失计数，不记录用户文字或键值 |
| `tools/run_control_diagnostics.py` | 复制/核验77文件控制包；启动校验Task/Dispatch/manifest/launcher摘要，继续原ControlToolGate |
| `tools/control_app_refresh.py` | 原App切换前刷新旧窗口缓存，原枚举过滤、查找、激活和后验保持 |
| `tools/control_diagnostic_budget.py` | 恢复失败终止诊断组，只保留冻结的一次诊断/观察供收尾，不重发输入 |
| `tools/control_geometry.py` | 临时DPI线程上下文取物理rect并恢复，未知/失败拒绝，不激活窗口 |
| `tools/control_indicator_health.py` | 判定实际采样/阶段耗时，额外批准先heartbeat后now；1秒阈值及故障拒绝保持 |
| `tools/control_test_window.py` | 事件名与输入kind不冲突；真实Tk回调日志、stdout/stderr和原异常堆栈，完整取证已过 |
| `tools/replay_control_health.py` | 纯JSONL离线重放，合并同旧心跳区间并计算阶段并集，拒绝缺失/矛盾记录 |
| `tools/control_bitmap_timing.py` | 指示层每次上传API次数/墙钟成本汇总，模块局部代理不改共享WinDLL对象；最新4081次正常路径已现场验证 |
| `tools/control_target_activation.py` | 只在未失败、UIA核验后/组前，至多一次原App激活与精确前景后验；离线8项/现场单组通过 |
| `tools/analyze_control_uploads.py` | 复用健康重放，约束旧上传时间戳延迟及API裁剪上下界；最新4081上传离线核对通过，不等于CPU或预计提速 |
| `tools/control_bitmap_surface_model.py` | 每不可变图层独有的内存DC/DIB/像素寿命核心，保留部分结果与待退役实例；模块本身不加载Win32 |
| `tools/control_bitmap_surface.py` | 私有WinDLL适配器及原图层寿命接入，默认关闭；本组7寿命8887上传正常路径取证通过，异常路径仍为离线测试范围 |
| `tools/control_surface_approval.py` | 新客户端批准/实际模型/冻结文件及包集合核验，检查被动日志资源前置条件；不访问桌面 |
| `tools/audit_control_surfaces.py` | 纯JSONL独立重算正常资源寿命/API/零账本；本组7寿命8887真实上传审计通过，进程退出另行核验 |
| `tools/control_owned_close.py`、`tools/control_close_client/` | 默认禁用的一次精确自建Popen正常关闭；普通输入后验保持，最新单组原Popen0→退役→stop无拒绝通过 |
| `tools/freeze_control_close.py` | 离线冻结17客户端/13工具/3监督器/77包，生成111文件候选，不创建任务或许可 |
| `tools/control_witness_launch.py` | 基础Python直启标准库见证器、核对实际PID后显式放行、原Popen等待；新增原截止内身份读取与构造异常所有权，7项定向测试 |
| `tools/control_process_supervisor.py` | 标准库监督器显式启动MCP环境客户端、精确子孙账本；本组实际监督器和9已发现子孙exit0 |
| `tools/control_supervisor_runner.py` | 同一本机程序预检/持柄/放行与退出重算；7项无GUI测试及本组实际已知链退出取证通过 |

新增异步离线证据审计测试为**10项全部通过**，日志`.local-analysis/async-race-offline-preflight/tests-audit-final.log`，不启动Qt/Win32/门闩/产品，覆盖事件身份、时序、摘要、代次、原拒绝决定、中止伪通过与真实read成功/先后计时。和149项控制测试分属不同工具范围，不简单相加，不重跑无变化产品矩阵。

此前实际控制测试为**149项全部通过**，输出`.local-analysis/control-residual-lifecycle/tests-offline.log`，16.796秒；新增7项独立生命周期契约测试，用假API核对来源/权限/时限/身份/唯一性/一次机会和未知及退出失败，没有发送真实关闭消息。真实生命周期另有持柄及自然回调证明。此前142项结果不叠加计数。

此前控制测试为**142项全部通过**，输出`.local-analysis/control-owned-close-v3/tests-supervisor-journal.log`，16.848秒；新增2项监督器快照重试/持续失败持原Popen回归，含真实无GUI客户端。此前一次定向子进程测试非0但stderr空，后续补诊断后定向7项及全体142项通过，该次未定位失败如实保留。离线修复`a37ed03`未写回活服务或冻结execution。此前140项结果如下，不叠加计数。

此前控制测试为**140项全部通过**，输出`.local-analysis/control-owned-close/tests-handshake-fixed.log`，覆盖原122项、14项关闭/客户端、1项批准和3项握手读取/所有权回归；不与137或122项历史结果相加。未运行GUI测试窗/输入钩子，既有监督器测试使用无GUI标准库子进程。现场因启动失败未验证专用关闭，不能用离线结果补记GUI通过。

此前实际相关仓库测试为**122项全部通过**，输出主`.local-analysis/control-supervisor-local-runner/tests-verified.log`。这些测试使用假窗口/API和无GUI标准库子进程，覆盖控制拒绝、诊断、健康、资源生命周期、批准、启动与精确退出，不安装真实输入钩子。冻结客户端另6项历史定向检查在`.local-analysis/control-bitmap-surface/frozen-client-tests-final.log`，不与仓库测试或产品覆盖相加。其余61/79/106/110/115项为历史测试阶段，原件保留，不重复累加。产品既有CTest固定Debug/Release各11组、实验各12组及OFF相关3组历史结果保持；本次纯文档交接不重跑无变化代码。

## 已结算现场阶段

| 阶段 / 报告 | 结果与有效边界 |
| --- | --- |
| [完整关闭现场](docs/control-close-journal-live.md) | 限定succeeded，专用关闭一次成功无拒绝、两图/回调、7寿命3625上传零账本、2880healthy及全部已知链原exit0 |
| [第三候选现场](docs/control-owned-close-v3-live.md) | failed，双图/回调及资源健康分项通过；关闭preflight拒绝未发送、监督器exit1/子孙缺口、窗口仍live |
| [专用关闭启动](docs/control-owned-close-live.md) | failed，身份文件PermissionError早于监督器放行；服务/桌面请求0，已知外层exit1，握手child原退出码缺失 |
| [基线](docs/control-snapshot-diagnostics.md)、[缓存/预算](docs/control-snapshot-fix.md) | failed，App未找到，未进入有效截图/输入 |
| [窗口兼容](docs/control-window-compat.md) | failed，UIA/枚举/App/首图通过，Click本地混合DPI坐标拒绝；有健康失败轨迹 |
| [物理矩形](docs/control-physical-geometry.md) | 限定通过，图0/0→1/1；旧逐输入日志有重名参数缺口，原件保留 |
| [日志修复](docs/control-window-logging.md) | 限定通过，完整双回调/空stderr，486trace/丢失0 |
| [健康采样](docs/control-health-validation.md) | 取证通过、稳定未过，5444样本3stale/2fail-open，247057trace/丢失0 |
| [位图首次](docs/control-bitmap-timing.md) | failed，原门禁user，实际图/输入/上传0，14分06正常退出 |
| [15分钟重试](docs/control-bitmap-retry.md) | failed，初始ready但首图前景Orca，实际call/上传0，约8分28正常退出 |
| [原App初始激活](docs/control-initial-activation.md) | 限定通过，原App/前景后验、两图/双回调/4081上传有效，健康2stale/1fail-open，约12分45全exit0 |
| [本机连续启动器现场](docs/control-supervisor-local-live.md) | 限定succeeded，双图/回调、8887上传零账本、1898健康及全部已知链exit0；正常关闭后验仍拒绝 |
| [资源复用现场](docs/control-bitmap-surface-live.md) | 整体failed，双图/双回调/7寿命8509上传/零账本及本组健康通过；66568精确退出码缺失，当前无该活进程不当exit0证明 |

全部Task均已结算，原Pi终端retain不代表任务仍活。新工作必须新Task/Dispatch/分支/批准/证据，不续投旧inbox、不重复worker_done、不重连清状态。精确ID和最终Git见本机简报。上一有效初始激活Run `run_b750f95c36e5`、Task `task_47e20595fdcb`、Dispatch `ctx_343756e91911`、done `msg_eea4f2c348a1`已验收ack，报告提交`37e9805`；无reclaimable资源。此前Run `run_bdf0b619f1e3`（前景failed）、`run_3da0a4eb0ac6`（user受阻failed）、`run_e136aa13bab5`（日志/健康）、`run_22b5092f9df3`（早四阶段）也全部结算。

## 前阶段执行计划（2026-10-29历史）

当前入口见[下一阶段](docs/control-next-stage.md)和[产品竞争离线预检](docs/async-race-offline-preflight.md)。控制限定通过保持；产品竞争已完成不变对照/部署/输入/时序重算，当前尚不能在冻结60秒内可靠完成实际读图与release。先实现并验证产品专用客户端及read/ack/正常退出设计，不自动启动产品或旧控制组。

1. **最新现场离线重建已完成。** [上传分析报告](docs/control-upload-offline-analysis.md)核对父两个审计、原trace/源码与冻结部署；同旧心跳到最后过期采样1.1905275秒，原慢阶段并集覆盖85.96%，加入短上传后并集边界1.1167753～1.1169445秒。schema 1缺少API起止时间，上传记录还有发出延迟，均采用上下界；不将未来结束值记为当时证据。
2. **资源复用及已知退出链取得单组真实证据。** 最新[现场报告](docs/control-supervisor-local-live.md)及父独立审计完成，本组7寿命8887上传、零账本、1898健康全healthy、监督器/9子孙/runner/launcher/owner原exit0成立；不因此提升为长期稳定或性能通过。122项离线测试保持，文档整合未改源码不重跑。
3. **专用关闭已取得本组完整限定通过。** 原Shortcut一次、严格成功回执、原Popen0、退役、stop且无拒绝；普通输入后验保持。快照修复本组retry1/failure0、监督器及9已发现子孙和外层原链exit0，未知短命进程/长期稳定限制保持。有效111文件候选f5ebb7a8...和本组execution只读，不原地重跑。第三候选原failed及子孙缺口、独立生命周期非原Popen边界不改；当前可先离线准备独立产品竞争方案。
4. **产品竞争离线预检完成，先补执行条件。** 实验源码c4e3ec5/EXE782a769f...、历史NET/铜正向对照和A/B/板输入核对不变，旧竞争仍aborted。实际read时间超过60秒看门狗，旧关键段不等实际read便release不能复用；新方案ready_for_live=false、max_product_launches=0。需按产品客户端约束补主窗/dirty模态精确归属、原Popen正常退出、read/ack时限与冻结/批准，再另定必要新现场。新范围须冻结候选与输入，引用不变对照；有效竞争要求同应用时钟`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`，真实GUI编辑、门闩内新修订/几何/dirty/NET来源图与最终图共同成立。cancel后的discarded不能补作有效release或完整竞争通过，实验通过也不自动让固定候选通过。
5. **产品后续另立阶段。** 固定候选900000mil极端位置属性、受控系统会话结束（共享宿主不注销/关机）仍缺。新增图元→工具取消→另存为新文件→未知字段保留或明确拒绝→往返/原程序重开另行开发；元件放置、布线、完整DRC、生产输出、Windows部署/性能分别规划。原字形继续独立研究，完整runtime兼容未过前保持false。

固定候选已有编辑/严格文本焦点/菜单/10000mil远移reset/五类只读图元/关闭保护/选后文件消失等证据，无源码变化不重跑全矩阵，见[实际编辑](docs/basic-editing-actual-edit-acceptance.md)和[剩余验收](docs/basic-editing-remaining-acceptance.md)。产品实验边界见[异步设计](docs/async-result-boundaries.md)、[开发报告](docs/async-experiment-development.md)、[恢复四例](docs/async-gui-recovered-120.md)、[自适应续验](docs/async-races-adaptive.md)。

## 用户要求与不可改变的边界

- **控制电脑前先说明预计时间和范围。** 本次用户已明确“你控制电脑”，并补充“若有需要控制电脑验收的，允许控制，否则推进下一步开发”。该授权保持有效，不对已授权范围重复索权；不据此重置已结束现场的600/900秒预算，不在失败组追加轮次。新任务先完成可审阅材料并说明具体范围。
- 正常动作不额外ControlStatus预检。真实拒绝立停，完整120秒内无输入/截图/状态/原生桌面请求；到期只按冻结预算诊断/恢复/收尾，不自动归因user为用户正在操作。120秒最小退避与原服务最近输入后10秒空闲条件独立。
- Snapshot必须有image并实际读图；已执行输入后图失败只补观察，不重发输入。不关指示层、不放宽1秒阈值、不在中途续心跳掩盖未完成显示、不改活内存/清状态或保持集合、不换入口绕拒绝。
- 坐标用实际图像倍率和物理rect，不能与DPI逻辑rect混比。目标唯一PID/birth/image/HWND/title/class必须可核验。窗口关闭后消失的保守锁存由Popen exit0证明处理，不恢复已死目标，不重发关闭。
- 精确自建Popen的一次WM_CLOSE仅正常生命周期，不计GUI通过，不用于产品或其他工程进程，不强杀。failed/token/budget/截止和原日志归档不清。旧PID2020已退役，VK192早已原连接释放并正常退出，不再泛化要求用户按键。

## 本机证据、环境与入口

| 位置 | 内容 |
| --- | --- |
| 主`.local-analysis/async-race-offline-preflight/` | 本轮新输入3、旧/新完整摘要、历史对照/aborted竞争重算、真实read时序、10项测试、非live方案、模型错误/结算和最终Git |
| 主`.local-analysis/async-image-review-rehearsal/`及worker同名目录 | 未开始演练的准备文件、环境/源图摘要；父快照和未执行审计仅主副本新增，Task failed/worker abandoned，无read/ack |
| 主`.local-analysis/control-supervisor-local-runner/` | candidate110/live20冻结、真实trace/两图/回调/runner退出与父独立审计；本组限定succeeded，122项离线测试 |
| `../verify-control-local-runner-live/.local-analysis/control-supervisor-local-live/` | 实际模型/原JSONL、before-after、owner/launcher/runner原Popen/持柄退出、worker审计 |
| 主`.local-analysis/control-bitmap-surface/` | candidate-final107冻结原件、live真实现场与父更正审计、110项仓库测试及原客户端6项；Task failed已结算，见证器修正仅离线，无后台进程 |
| 主`.local-analysis/agent-session-archive-20261029/` | 前3个闲置窗格的历史核验；后续direct/local验收窗格也已在各任务结算后关闭，累计5个，JSONL/分支/工作树保留 |
| 主`.local-analysis/control-upload-offline-analysis/` | 最新上传边界/成本分析、79项测试输出、原trace/源码与冻结包/部署摘要核对，全程desktop_requests0 |
| 主`.local-analysis/control-initial-activation/` | 最新双批准、before/after、独立API/健康/回调审计、精确句柄exit0见证、final-validation（56链接）、final-git-state |
| `../verify-text-screen-sol/.local-analysis/control-initial-activation/` | 最新209证据/17链接、原图0/0→1/1、实际call/窗口日志/stderr、4081上传和健康trace、退出身份 |
| 主`.local-analysis/control-target-activation/` | 离线模板/61项测试输出/旧证据SHA/verification，模板身份占位不得直接运行 |
| 主`.local-analysis/control-offline-replay/`、`control-user-timeline/` | 旧心跳阶段并集、user续期时间线、只读分析证据 |
| 主及验收工作区`.local-analysis/control-bitmap-timing/`、`control-bitmap-retry/` | 两失败组的原始批准/trace/前景/退避/退出及审计，禁止改写成通过 |
| 主`.local-analysis/control-health-sampling/`、`control-snapshot-diagnostics/` | 历史两组/早四阶段父侧批准、独立审计和材料；验收工作区同名及fix/compat/geometry目录保存现场原件 |

本机`.local-analysis/`、截图、安装副本、字体/库、反编译数据库、SDK/下载/构建不入Git，远端clone不带证据，不能强制add。原安装`D:/project/pt_renew/pt`只读，原板/库写入测试必须新副本。原软件和安装介质不得再分发。

Qt6.12.0/MSVC x64：`C:/Users/rikideng/Qt/6.12.0/msvc2022_64`；VS2026/MSVC14.51.36231、CMake/Ninja/Python已有，不安装无关依赖。已有控制解释器`C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Scripts/python.exe -X utf8`；全局Pillow/NumPy曾不兼容，不为任务修全局环境。

原验收Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`的旧终端`term_d544d0b2-a65f-4b5c-bea9-6257e802bd6d`与本次已结算Pi终端均按用户要求关闭归档，原JSONL保留，不恢复旧任务。所有子代理Pi；纯逆向`glm-5.3 high`，截图/GUI验收`gpt-6.1-sol high`，核对实际环境/JSONL/assistant；模型不可用如实报告不替换。开发从最新dev独立分支，验证后no-ff合dev推送，main合并/提交/推送只由用户执行，不强推不跳钩子。主工程`D:/project/pt_renew`及其他工程终端不是本任务，不抢占。
