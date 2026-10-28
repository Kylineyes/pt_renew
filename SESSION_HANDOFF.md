# PT Renew 当前进度与新会话交接

更新时间：2026-10-29。先读本机`.local-analysis/NEXT_AGENT_BRIEF.md`、[AGENTS.md](AGENTS.md)，再读本文。最新开发成果已合入推送`dev`基线`eb270f8`；本次仅整理交接，最终文档提交见本机简报或`git rev-parse dev origin/dev`。旧版交接备份在`.local-analysis/handoff-archive/`，不删除失败原件。

**稳定产品及dist仍为0.10.0。固定0.11.0候选和NET／铜层完整竞争验收仍未通过。最新完成的是控制诊断工具与限定自建窗口取证：一次原App初始化、单组GUI和4081条位图上传记录通过；真实心跳滞后仍存在，控制稳定性尚未修复。所有现场窗口、探针与控制链已正常退出，Task均结算，无后台诊断或自动续验。**

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

[最新现场报告](docs/control-initial-activation.md)对应原Pi验收会话实际读图；父侧独立审计工具调用/回调时序、API次数/分段、健康判定及精确进程退出，不把父日志审计冒称父读图。

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

最后实际相关单元测试为**61项全部通过**，输出主`.local-analysis/control-target-activation/tests.log`。未与本地截止/被动观察测试重复累加，也未因纯文档交接重跑无变化代码。单元测试使用假窗口/API，不安装真实钩子或发送输入，测试窗子进程测试仅命令行异常脚本。纯本机驱动额外有截止4项、被动观察5项定向测试，不能作为新增产品覆盖。产品既有CTest固定Debug/Release各11组、实验各12组及OFF相关3组历史结果不变。

## 已结算现场阶段

| 阶段 / 报告 | 结果与有效边界 |
| --- | --- |
| [基线](docs/control-snapshot-diagnostics.md)、[缓存/预算](docs/control-snapshot-fix.md) | failed，App未找到，未进入有效截图/输入 |
| [窗口兼容](docs/control-window-compat.md) | failed，UIA/枚举/App/首图通过，Click本地混合DPI坐标拒绝；有健康失败轨迹 |
| [物理矩形](docs/control-physical-geometry.md) | 限定通过，图0/0→1/1；旧逐输入日志有重名参数缺口，原件保留 |
| [日志修复](docs/control-window-logging.md) | 限定通过，完整双回调/空stderr，486trace/丢失0 |
| [健康采样](docs/control-health-validation.md) | 取证通过、稳定未过，5444样本3stale/2fail-open，247057trace/丢失0 |
| [位图首次](docs/control-bitmap-timing.md) | failed，原门禁user，实际图/输入/上传0，14分06正常退出 |
| [15分钟重试](docs/control-bitmap-retry.md) | failed，初始ready但首图前景Orca，实际call/上传0，约8分28正常退出 |
| [原App初始激活](docs/control-initial-activation.md) | 限定通过，原App/前景后验、两图/双回调/4081上传有效，健康2stale/1fail-open，约12分45全exit0 |

全部Task均已结算，原Pi终端retain不代表任务仍活。新工作必须新Task/Dispatch/分支/批准/证据，不续投旧inbox、不重复worker_done、不重连清状态。精确ID和最终Git见本机简报。最新Run `run_b750f95c36e5`、Task `task_47e20595fdcb`、Dispatch `ctx_343756e91911`、done `msg_eea4f2c348a1`已验收ack，报告提交`37e9805`；无reclaimable资源。此前Run `run_bdf0b619f1e3`（前景failed）、`run_3da0a4eb0ac6`（user受阻failed）、`run_e136aa13bab5`（日志/健康）、`run_22b5092f9df3`（早四阶段）也全部结算。

## 下一会话的执行计划

1. **先离线、先定位范围。** 完整读本机简报、AGENTS、本文及最新现场报告，核对Git与部署摘要。读取最新`independent-audit.json`和`callback-and-cost-audit.json`，以最后一次健康失败的旧心跳区间重建完整枚举/上传/消息泵时间线。复用现有重放工具，检查嵌套区间不重复计时；不要仅按全场API占比选优化，也不要把墙钟时间等同CPU或直接归因memmove。
2. **评估最小性能实验，不先改健康规则。** 可评估图层寿命内复用兼容DC/DIB、避免重复像素复制的收益与风险，或证明这些假设不值得实施。先明确资源所有线程、SelectObject恢复、部分初始化失败、关闭/重建/显示器变化/异常释放路径；用假API和离线模型验证结果与资源平衡。此为待评估方向，尚无资源复用实现、性能改善或采样调度修复完成。
3. **满足可审阅条件才安排新现场。** 先完成独立分支代码/必要测试/风险边界、冻结摘要与新方案；向用户说明预计控制用时和具体范围，得到明确许可后，再沿原指定Pi模型执行一组有界验证。原App初始化可以引用最新通过流程，仍须原门禁/精确身份及前景后验；失败消费机会，不新增连接碰运气。开始计时、第N分钟停止新增诊断、正常退出余量均写入冻结客户端。
4. **控制条件可靠后再另定产品竞争。** 不自动启动NET/铜产品实验。新范围须冻结候选与输入，引用不变对照；有效竞争要求同应用时钟`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`，真实GUI编辑、门闩内新修订/几何/dirty/NET来源图与最终图共同成立。cancel后的discarded不能补作有效release或完整竞争通过，实验通过也不自动让固定候选通过。
5. **产品后续另立阶段。** 固定候选900000mil极端位置属性、受控系统会话结束（共享宿主不注销/关机）仍缺。新增图元→工具取消→另存为新文件→未知字段保留或明确拒绝→往返/原程序重开另行开发；元件放置、布线、完整DRC、生产输出、Windows部署/性能分别规划。原字形继续独立研究，完整runtime兼容未过前保持false。

固定候选已有编辑/严格文本焦点/菜单/10000mil远移reset/五类只读图元/关闭保护/选后文件消失等证据，无源码变化不重跑全矩阵，见[实际编辑](docs/basic-editing-actual-edit-acceptance.md)和[剩余验收](docs/basic-editing-remaining-acceptance.md)。产品实验边界见[异步设计](docs/async-result-boundaries.md)、[开发报告](docs/async-experiment-development.md)、[恢复四例](docs/async-gui-recovered-120.md)、[自适应续验](docs/async-races-adaptive.md)。

## 用户要求与不可改变的边界

- **控制电脑前先说明预计时间和范围，取得明确许可。** “继续”只授权离线推进；已结束15/30分钟窗口不能复用。已获同一范围许可不重复索权，但不能扩大轮次/目标或自动延期。当前用户仅要求整理交接，无新桌面许可或自动续验。
- 正常动作不额外ControlStatus预检。真实拒绝立停，完整120秒内无输入/截图/状态/原生桌面请求；到期只按冻结预算诊断/恢复/收尾，不自动归因user为用户正在操作。120秒最小退避与原服务最近输入后10秒空闲条件独立。
- Snapshot必须有image并实际读图；已执行输入后图失败只补观察，不重发输入。不关指示层、不放宽1秒阈值、不在中途续心跳掩盖未完成显示、不改活内存/清状态或保持集合、不换入口绕拒绝。
- 坐标用实际图像倍率和物理rect，不能与DPI逻辑rect混比。目标唯一PID/birth/image/HWND/title/class必须可核验。窗口关闭后消失的保守锁存由Popen exit0证明处理，不恢复已死目标，不重发关闭。
- 精确自建Popen的一次WM_CLOSE仅正常生命周期，不计GUI通过，不用于产品或其他工程进程，不强杀。failed/token/budget/截止和原日志归档不清。旧PID2020已退役，VK192早已原连接释放并正常退出，不再泛化要求用户按键。

## 本机证据、环境与入口

| 位置 | 内容 |
| --- | --- |
| 主`.local-analysis/control-initial-activation/` | 最新双批准、before/after、独立API/健康/回调审计、精确句柄exit0见证、final-validation（56链接）、final-git-state |
| `../verify-text-screen-sol/.local-analysis/control-initial-activation/` | 最新209证据/17链接、原图0/0→1/1、实际call/窗口日志/stderr、4081上传和健康trace、退出身份 |
| 主`.local-analysis/control-target-activation/` | 离线模板/61项测试输出/旧证据SHA/verification，模板身份占位不得直接运行 |
| 主`.local-analysis/control-offline-replay/`、`control-user-timeline/` | 旧心跳阶段并集、user续期时间线、只读分析证据 |
| 主及验收工作区`.local-analysis/control-bitmap-timing/`、`control-bitmap-retry/` | 两失败组的原始批准/trace/前景/退避/退出及审计，禁止改写成通过 |
| 主`.local-analysis/control-health-sampling/`、`control-snapshot-diagnostics/` | 历史两组/早四阶段父侧批准、独立审计和材料；验收工作区同名及fix/compat/geometry目录保存现场原件 |

本机`.local-analysis/`、截图、安装副本、字体/库、反编译数据库、SDK/下载/构建不入Git，远端clone不带证据，不能强制add。原安装`D:/project/pt_renew/pt`只读，原板/库写入测试必须新副本。原软件和安装介质不得再分发。

Qt6.12.0/MSVC x64：`C:/Users/rikideng/Qt/6.12.0/msvc2022_64`；VS2026/MSVC14.51.36231、CMake/Ninja/Python已有，不安装无关依赖。已有控制解释器`C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Scripts/python.exe -X utf8`；全局Pillow/NumPy曾不兼容，不为任务修全局环境。

原验收Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`，终端`term_d544d0b2-a65f-4b5c-bea9-6257e802bd6d`保留，使用前Orca枚举确认当前runtime，不能凭旧句柄判断。所有子代理Pi；纯逆向`glm-5.3 high`，截图/GUI验收`gpt-6.1-sol high`，核对实际环境/JSONL/assistant；模型不可用如实报告不替换。开发从最新dev独立分支，验证后no-ff合dev推送，main合并/提交/推送只由用户执行，不强推不跳钩子。主工程`D:/project/pt_renew`及其他工程终端不是本任务，不抢占。
