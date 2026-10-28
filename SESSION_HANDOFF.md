# PT Renew 开发进度与会话交接

更新时间：2026-10-28。先完整读本机`.local-analysis/NEXT_AGENT_BRIEF.md`、[AGENTS.md](AGENTS.md)，再读本文。临时简报保存最终Git提交、进程和会话定位；出现差异以最新直接证据为准。本文已压缩历史追加内容，旧交接原文备份在本机忽略目录`handoff-archive/`。

**稳定产品及dist保持0.10.0，固定0.11.0候选及NET／铜层完整竞争验收仍未通过。** 用户交接后要求“继续”，本次从`b085fe2`建立`fix/control-health-sampling`，完成测试窗日志修复、实际健康采样/阶段耗时工具及两个限定现场组。39项相关单元测试全部通过；日志组完整取证通过；健康组确认采样和先心跳后时间修复实际加载，但仍捕获3次真实过期心跳与2次fail-open，控制稳定性未修复。两组窗口、UIA探针和控制链均已正常exit0，两个Task已结算并验收，当前无后台诊断或自动续验计划。产品代码、部署、原始安装及main未修改；最终Git/Task结算见本机临时简报。

本轮继续工作仅为[日志离线重放](docs/control-offline-replay.md)，开发分支`feat/control-offline-replay`从`9ad19a9`建立；新增纯文本重放工具及8项定向测试，整合相关测试53项实际全部通过。3条过期采样归并为两段旧心跳区间，记录阶段墙钟并集覆盖90.61%/93.14%，两段内hook/input事件均0。静态源码显示心跳仅在整轮枚举/多层绘制/消息泵之后更新，累计耗时路径与日志一致；具体底层慢因仍unknown，不能用全场高频输入数量直接解释两段超时。默认关闭的位图细分计时模块和[30分钟方案](docs/control-bitmap-timing-plan.md)随后经用户“你先控制电脑”明确许可，在新隔离进程实际加载；首图前景拦截后原门禁持续user，限定恢复/诊断未允许，实际Snapshot/Click/Shortcut/上传均0，目标failed，计时未验证。窗口/探针/五控制链约14分6秒正常exit0，338863行trace closed dropped0，3209健康样本，2次ControlStatus；没有第二连接/组。新现场须另估时并获得明确许可；当前无后台桌面活动。

最新离线续作见[user门禁时间线](docs/control-user-timeline.md)：两次ControlStatus前10秒分别记录3953/4779条point/raw，原wait与最近输入年龄一致；服务曾三次ready（两次后续恢复维持约3.88/43.05秒），不是全程锁死。不能归因操作者或来源进程，也不改原门禁。已准备[15分钟有界方案](docs/control-bitmap-retry-plan.md)，随后用户明确“允许”，新15分钟Task `task_ab514403da21` / Dispatch `ctx_ab825328a37d` / Run `run_bdf0b619f1e3`执行唯一组：初始10.29秒日志观察通过、Launch前复查通过，窗口/UIA正常，但首图前稳定前景为Orca，未调用任何ControlStatus/App/Snapshot/Click/Shortcut，上传0。本组首拒绝即停，120秒后一次自建Popen WM_CLOSE正常生命周期退出；trace2136 closed dropped0、1925健康采样，服务507.072秒约8分27秒，窗口/探针/完整控制链全exit0，父持4链身份也exit0，无强杀。计时未验证；不是本轮再次user门禁拒绝。报告`f91ec98`已整合，任务已failed结算，done `msg_5589784859d9`已验收，现场已结束，无后台续验；新现场须另估时并获许可。

最新离线前景审查见[初始目标激活](docs/control-target-activation.md)：Popen与UIA可发现性不保证前景，原流程缺少首图前的一次明确激活。启动前/首图前已有记录均是相同Orca前景，不能直接归因UIA探针。新增`tools/control_target_activation.py`为未失败、已绑定/UIA核验、未开始组的唯一自建目标提供至多一次原App切换及精确前景后验，保留原门禁和120秒拒绝；8项假窗口/假工具测试通过，尚未现场接入。新client/step本地模板语法通过但身份未绑定，具体[15分钟方案](docs/control-target-activation-plan.md)等待用户明确许可。本轮没有GUI/控制服务/截图/输入，不能称修复通过。

## 当前产品与候选

| 对象 | 已完成 | 限制与状态 |
| --- | --- | --- |
| 稳定0.10.0 | PCB/LIB/NET只读查看、图层显隐、缩放平移、选择/定位、两点测量与几何端点捕捉、引脚映射、受限铜层分析 | 铜分析不是完整DRC，文字和部分轮廓有近似 |
| 固定0.11.0编辑候选 | 单条自由Track整数mil内存移动、删除、Undo/Redo、dirty/clean、关闭/换图保护、派生结果失效、外部NET保留并重新映射 | 独立分支，整体未通过，不合入稳定发行 |
| 独立异步实验候选 | 默认OFF的`PT_ENABLE_ASYNC_EXPERIMENT`，NET实际读取前和铜算法预算计时前的工作线程门闩、60秒看门狗、请求/线程/修订/回调事件 | 只作实验观察，不能替固定候选记通过 |
| 原字形研究 | 已有静态/受控执行及部分原程序现场证据 | `runtime_verified=false`；未接入Qt渲染、命中或铜分析 |

固定候选没有保存/另存为、新增图元、拖拽、元件移动、布线、完整DRC或生产输出。不要把后续开发计划写成已支持。

| 冻结部署 | EXE SHA-256 |
| --- | --- |
| 主工作区`dist/pt-renew.exe`，22文件 | `726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1` |
| 同级`feat-basic-editing/.local-analysis/basic-editing/release-candidate/pt-renew.exe`，23文件 | `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8` |
| 同级`experiment-async-result-barrier/.local-analysis/async-experiment/release-candidate/pt-renew.exe`，22文件 | `782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac` |

固定源码分支`Kylineyes/feat-basic-editing`在`b0e5ac7761f13690b5310bbc913ab7bfd2691d08`；实验分支`experiment/async-result-barrier`在`c4e3ec5e82bf1a022e523ec8844d0665d7b93234`，实验代码提交`98a4321`。主build可能仍有历史0.11.0构建，不能凭切分支判断EXE版本，固定部署不得重建覆盖。

## 控制诊断工具开发

此前`fix/control-snapshot-diagnostics`已合入推送dev=`b085fe2`。此次开发`fix/control-health-sampling`从该基线建立，源码提交`c20fdfd`（实际采样/启动开关）、`84947e0`（原健康函数差分测试）、`b239aba`（测试窗日志/三项测试及报告），完成后按AGENTS整合dev推送，main只由用户操作。

| 文件 | 行为及验证边界 |
| --- | --- |
| `tools/control_diagnostics.py` | 对原控制方法附加只读阶段/原因日志和status诊断字段；保留原拒绝、接管、保持集合、心跳阈值与异常。日志有界、独立线程写入、结束记录丢失数量，不记录用户文字或键值 |
| `tools/run_control_diagnostics.py` | 复制已安装windows-mcp到独立副本并逐文件核验；启动复验任务批准、包清单及启动器摘要，调用原ControlToolGate和原工具 |
| `tools/control_app_refresh.py` | 新隔离进程显式批准才启用，在原App切换前刷新窗口列表；原查找、激活和前景后验保持，不改变原窗口过滤 |
| `tools/control_diagnostic_budget.py` | 目标恢复失败也终止诊断组，保留唯一只读诊断/观察供收尾；不自动重发输入 |
| `tools/control_geometry.py` | 临时线程DPI上下文读取物理桌面矩形并恢复原上下文；读取/恢复未知则拒绝，避免逻辑rect与物理点击坐标混比 |
| `tools/control_indicator_health.py` | 记录原判定实际采样值、返回值和指示层慢阶段；采样保留原顺序，额外批准才先heartbeat后now。现场已在隔离新进程加载，仍观察真实滞后，原1秒阈值/故障拒绝保持，未部署原安装 |
| `tools/control_test_window.py` | 新副本修复日志事件名与输入kind冲突，逐行记录真实Tk回调；显式stdout/stderr、异常原堆栈。双回调与原工具时刻/图像/终态共同验证 |

相关`tests/test_control_*.py`共39项实际通过，整合输出在主`.local-analysis/control-health-sampling/integrated-tests.log`，不与工作者定向测试重复累加。覆盖原控制拒绝/输入账本、有界日志、缓存/预算、物理矩形、健康原顺序与修复差分、实际采样/阶段及启动选项、测试窗回调/stderr。无真实钩子或键鼠，测试窗子进程测试仅运行命令行异常脚本。命令及隔离方式见[工具说明](docs/control-diagnostics-tools.md)。第三方原安装/副本77文件、稳定22/固定23/实验22部署运行前后文件集合和摘要不变，主`before.json`/`after.json`可核对；忽略材料不入Git。

## 现场诊断结果

所有阶段沿用原Pi会话`01a1739a-82f6-76cf-9ffc-c63e95be56d4`与实际核对的`deng/gpt-6.1-sol high`。每阶段独立分支、证据目录、Task/Dispatch和批准文件，运行后不热改。

| 阶段与报告 | 实际结果 | 收尾 |
| --- | --- | --- |
| [诊断基线](docs/control-snapshot-diagnostics.md) | failed。初始非前景后App not found；恢复错误未联动预算，唯一diagnose被本地断言拦截；Snapshot/Click/Shortcut均0 | 自建窗口及五控制链exit0；125索引、21链接、565行trace dropped0 |
| [缓存/预算修复验证](docs/control-snapshot-fix.md) | failed。缓存刷新已加载仍not found；预算修复允许唯一diagnose实际到达控制/原生检查；Snapshot/诊断输入仍0 | 窗口及五链exit0；143索引、21链接、320行trace dropped0 |
| [兼容窗口验证](docs/control-window-compat.md) | failed。可缩放Tk窗口的UIA/原枚举通过，App恢复和两张Snapshot成功；Click被诊断Guard的DPI混合坐标检查拦截，实际未发送 | 窗口、探针及五链exit0；207索引、23链接、488行trace dropped0 |
| [物理矩形验证](docs/control-physical-geometry.md) | **限定succeeded**。物理rect正确包含按钮点，真实Click及Ctrl+Shift+F8各一次，首图0/0、最终图1/1；未复现本组工具拒绝 | 窗口、探针及五链exit0；223索引、25链接、561行trace dropped0 |

第四阶段通过依据是指定会话和父侧实际读图、原工具调用及物理矩形证据。冻结测试窗逐输入日志存在`record(kind, **fields)`与`kind=`参数重名冲突，GUI先更新成功但输入日志缺行；未捕获stderr堆栈，不得称日志也证明完整逐输入时间线。正常关闭终态日志为1/1，不替代缺失的两条回调记录。旧源码和失败原件保留，未为补日志重跑。

第三阶段成功截图后两次看门狗直接记录`indicator_ok=false、desktop_ok=true`并fail-open；首条指示层心跳年龄约1.078秒。第二条非原子快照的瞬时心跳年龄较小，不能反推探测时的值。第四阶段未记录fail-open，health读取修复未加载；这些样本仍不足以确定历史所有截图拒绝的根因或证明长期可靠性。

本次[日志修复组](docs/control-window-logging.md)关闭健康开关，在新副本实际读图0/0→1/1、Click和诊断快捷键各一次、两回调时间各落对应原调用区间，stderr空、486行trace closed dropped0/fail-open0。AltF4已正常关闭后目标消失导致本地后验锁存，多余生命周期请求被子进程已退出断言拒绝，WM_CLOSE实际0，失误原件保留。窗口、探针、五链均exit0，父时间线/句柄审计通过。

本次[健康组](docs/control-health-validation.md)明确批准采样和修复，实际installed事件`heartbeat_first=true/phases=true/threshold_seconds=1.0`。首图前本地非目标拦截，完整120秒后恢复成功，同一连接/组实际两张有效图0/0→1/1、两回调完整、stderr空；5444健康样本逐行核对（5441健康、3真实过期，最大约1.0781844秒），32条慢阶段/状态确认，247057行trace closed dropped0。两次watch实测过期约1.0049/1.0193秒、desktop_ok=true并fail-open，恢复另见1.078秒；未出现伪负年龄不能证明长期稳定。phase观察非原子，高频事件/诊断开销显著，不能确定绘制/多图层累计/调度或历史截图因果。关闭前本地拦截未发送AltF4，120秒后精确自建Popen的一次WM_CLOSE仅生命周期，窗口/探针/五链exit0，父样本及退出审计通过。此组只证明采样有效和限定GUI完成，控制健康稳定性未通过。

所有诊断窗口和控制链均已正常退出，无强制终止或后台输入计划。受阻时精确身份的一次WM_CLOSE只用于自建程序的正常生命周期清理，不作GUI输入/验收通过证据，不适用于产品候选或其他工程进程。已退出运行的failed/token/budget/截止和live-state全部归档，不删除、不恢复旧PID、不重连清门禁。

本次位图现场Run `run_3da0a4eb0ac6` / Task `task_371c96f46645` / Dispatch `ctx_1aa4e6fd282a`已failed结算，唯一done `msg_b47f7956ea27`已由父验收ack，提交`4a18527`已整合；终端明确retain，无reclaimable。实际服务t0=859112.2685206，trace关闭859958.0270714，约845.7586秒；本地截止检查保留1500秒诊断/1800秒收尾限制，4项离线边界测试通过。父独立句柄5身份和工作者完整五链均exit0，无强杀。原门禁user不直接归因用户，上传0不代表计时模块异常或性能通过。证据主`.local-analysis/control-bitmap-timing/`及验收工作区同名目录，报告[位图取证](docs/control-bitmap-timing.md)；既有53项测试未为这次现场重复累加。

## 产品验收仍缺什么

固定编辑候选既有常规编辑、严格文本焦点、旧式/现代菜单、10000mil远移/reset、五类只读图元、定向关闭保护、选后文件消失和独立菜单退出已有实际证据，无源码变化不重跑全套A—F。Debug/Release各11/11组CTest已通过。详见[实际编辑验收](docs/basic-editing-actual-edit-acceptance.md)和[剩余验收](docs/basic-editing-remaining-acceptance.md)。

独立实验Debug/Release各12/12组CTest和普通OFF Release相关3组通过，自动竞争只证明offscreen/程序接口场景；[实验设计](docs/async-result-boundaries.md)与[开发报告](docs/async-experiment-development.md)说明判据。此前NET与铜正向对照真实GUI通过；[恢复后四例](docs/async-gui-recovered-120.md)和[自适应续验](docs/async-races-adaptive.md)中竞争均中止，没有完整有效release及门闩内编辑截图。cancel后旧结果discarded不能补作通过，工具小窗口1/1也不替产品竞争通过。

未覆盖还包括900000mil极端位置的直接属性、受控系统会话结束、原字形完整runtime兼容。共享宿主不注销或关机。

## 下一阶段计划与验收标准

1. **初始激活辅助模块离线准备已完成，现场待许可。** 代码确认窗口启动/UIA不保证前景，旧流程缺少首图前激活。新步骤只在未失败、已核验目标且组前执行一次原App，随后原精确前景后验通过才开始组；不直接原生激活、不加ControlStatus、不清锁存/保持集合、拒绝后不重试。8项离线测试和client模板语法通过，尚未现场验证。新15分钟范围含一次App切换，先说明时间/范围并获明确许可再启动。
2. **控制稳定性仍需独立开发和新有界验证。** 先心跳后时间只修伪负年龄，不能消除本组实测约1.005/1.019秒过期；第三个恢复采样约1.078秒。不能通过续写心跳、关指示层、放宽1秒阈值、清状态或切入口规避真正故障拒绝。若要新现场，另Task/批准/冻结/证据，失败不加新连接。无有效图、日志丢失、原因不唯一仍unknown，不把限定GUI成功当长期稳定。
3. **条件具备后另定有界产品实验范围。** 新Task/Dispatch/批准/证据，冻结候选和输入；引用不变对照。要求同一应用时钟`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`，真实GUI编辑、门闩内新修订/几何/dirty/NET来源图和最终图共同成立。失败中止并消费机会，额外运行须另有明确范围；实验通过仍不自动让固定候选通过。
4. **固定候选边界与新产品功能分别安排。** 极端可见性和受控会话测试独立做。新增图元→工具取消→另存为新文件→未知字段保留或明确拒绝→往返及原程序重开另立阶段；元件放置、布线、完整DRC、生产输出、干净Windows部署、性能各自规划。
5. **原字形保持独立研究。** 缩放/完整与简化分派/F/251/252/旋转镜像/笔宽/导入联合状态/保存往返未完成前，继续保留`runtime_verified=false`。

## 用户偏好与执行约束

用户本轮最新要求：**如需控制电脑，先告知预计所需时间及操作范围，得到明确许可后再操作。** 此要求覆盖此前通用键鼠授权及无需重复索权偏好；“继续”只授权离线工作，不授权启动控制链、GUI交互或截图。先完成代码、离线验证和具体现场计划，再估时请求许可，未获许可不得自动续验。正常动作不增加额外ControlStatus预检，拒绝后检查间隔120秒及原工具自身保护仍保持。

真实拒绝立停、截止内零输入/截图/ControlStatus/原生桌面请求；到期有界检查并显式恢复，不能把user自动归因为用户正在操作。Snapshot必须有image；动作已执行但后图失败，只补观察，不重发。物理桌面坐标以实际图像原尺寸/倍率及物理rect为准，不能把DPI虚拟化rect直接作输入坐标。GUI关闭后窗口消失的保守锁存由Popen退出见证处理，不恢复已退出目标。

## 生命周期与证据定位

下列四Task均已结算，保留Pi终端不代表任务仍活；禁止复用或重复worker_done：

| Task / Dispatch | 结果 | 工作者报告提交 |
| --- | --- | --- |
| `task_bb8bca1bbfb9` / `ctx_5e11c1301247` | failed | `ef26ac5a223aee8d7bcf6eea0e8b460745f092f7` |
| `task_e389a3ccfaef` / `ctx_1f7869a00c74` | failed | `ac620056b2f43c7430ebc193582958e778bf51be` |
| `task_82d78df9e34c` / `ctx_1dbebe2effc3` | failed | `d44ae4e816b9ad6c7884ee5fe3cd28f2e1faafd1` |
| `task_30f766b66866` / `ctx_900f441db397` | succeeded（限定单组） | `a7110ad5013dd83a5853cf8587ce58c259d4695f` |

此前Run为`run_22b5092f9df3`，唯一worker_done为`msg_921f9165317c`，已结算。本次Run `run_e136aa13bab5`：日志Task `task_d88863b795f8` / `ctx_e09b30cefbe7`已succeeded（限定日志取证），done `msg_a81bde98ca69`已验收ack，提交`b239aba`；健康Task `task_2e0cc599ee61` / `ctx_95024c79b018`已succeeded结算（仅采样及有界GUI取证，健康稳定性未过），done `msg_22d186aef34c`已验收ack，提交`85c3f7f`。两个已结算验收终端所有权均明确retain，无reclaimable资源。初次`ctx_2b320b2960a1`仅agent_readiness超时、无提示/GUI/MCP，失败归档，原会话空闲后显式retry成功，不是额外现场轮次。图像由指定工作者实际读图；父独立核对回调/原工具时序、stderr、采样判定和进程退出。旧PT Renew PID2020及历史VK192处置保持已结算，不重启旧连接、不恢复旧PID、不泛化要求用户按键。

| 位置 | 内容 |
| --- | --- |
| 主工作区`.local-analysis/control-snapshot-diagnostics/` | 四阶段任务/批准、77文件包副本、父离线复现、独立交付审计、新链退出见证 |
| 截图工作区`.local-analysis/control-snapshot-diagnostics/` | 基线125项证据 |
| 同工作区`.local-analysis/control-snapshot-fix/` | 修复验收143项证据 |
| 同工作区`.local-analysis/control-window-compat/` | UIA/坐标阶段207项证据与两次看门狗轨迹 |
| 同工作区`.local-analysis/control-physical-geometry/` | 单组223项证据、0/0→1/1图、日志缺口说明及退出证明 |
| 主工作区`.local-analysis/control-health-sampling/` | 两新组批准、39项测试输出、运行前后材料、父日志/健康/回调审计与两组精确进程句柄exit0见证 |
| 截图工作区`.local-analysis/control-window-logging/` | 日志组200索引/25链接、两图0/0→1/1、双回调及空stderr、486行trace dropped0 |
| 截图工作区`.local-analysis/control-health-validation/` | 228索引/22链接；真实加载采样/修复组，两图/双回调/空stderr、5444采样/32阶段/两fail-open、247057行trace dropped0，退出及根因限制 |
| 主工作区`.local-analysis/async-race-followup/` | 前轮两竞争中止、部署/安装摘要及591材料审计 |
| 主工作区`.local-analysis/control-investigation/` | 更早VK192内部残留直接只读取证 |

以上材料、截图、原字体/库、反编译数据库和构建产物不入Git，远端clone不带本机证据。原安装`D:/project/pt_renew/pt`只读，运行和写测试必须用新副本。

## 环境和接手步骤

Qt6.12.0 MSVC x64（`C:/Users/rikideng/Qt/6.12.0/msvc2022_64`）、VS2026/MSVC14.51.36231、CMake/Ninja已具备。已有Python/Unicorn/Capstone，不重复安装无关依赖。系统Python的NumPy/Pillow二进制导入存在兼容问题；本轮图像和控制测试使用已有`C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Scripts/python.exe -X utf8`，不为此修全局环境。

新会话先读临时简报确认最终Git与终端，再完整读AGENTS和本文；核对`git status`、`dev/origin/dev`、部署摘要和指定模型。保留验收终端`term_d544d0b2-a65f-4b5c-bea9-6257e802bd6d`属于当前Orca runtime，使用前先枚举确认，不能凭旧句柄推断仍存。所有子代理用Pi，纯逆向`glm-5.3 high`、截图/验收`gpt-6.1-sol high`并核对实际记录；同任务沿用会话。用户交接后明确要求的日志和健康诊断已完成并结算；新会话按下一阶段计划先做离线研究，不仅因读到计划就自动启动新GUI或产品竞争。
