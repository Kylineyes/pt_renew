# PT Renew 唯一交接：当前进度与下一步

本文件是新 agent 的唯一交接文档。能力概览见 [PROGRESS](PROGRESS.md)，软件主题见[文档导航](docs/README.md)，具体未知及领取状态见[探索待办](docs/exploration-backlog.md)。用户在完成交接整理后明确要求继续处理剩下的工作项；当前已启动 EX-001 接续，具体范围与新会话见下文。

<a id="baseline"></a>

## 接手基线和最短步骤

唯一交接整理已合入并推送 `dev=9374e66cc3141596fd252543f3730204924e910a`，当时工作区干净，最终记录为 `.local-analysis/handoff-maintenance/final-state.json`。用户随后要求继续剩余事项，EX-001 新领取已 no-ff 合入并推送 `7fbcc47203a23ab4c97eb2367b26d17b318f5ffe`；实时 HEAD 仍以 Git 与远端查询为准。直连 GitHub DNS 和代理 SSH 22 曾失败，当前已验证经 `127.0.0.1:10808` 代理连接 `ssh.github.com:443` 可 fetch／push；仅使用进程级 SSH 参数，未修改全局配置。

1. 完整阅读 [AGENTS](AGENTS.md)、本文件、[探索工作规则](docs/exploration-workflow.md)，再选相关主题及报告。旧提示词、旧 GO 和历史“下一步”不再作为接手指令。
2. 核对 `git status --short --branch`、`git log -5 --oneline`，fetch 后核对远端 dev；从最新 dev 建独立分支。main 的合并、提交和推送由用户处理。
3. 先消费下面四项已经沉淀的研究结论，再领取一个具体剩余问题；如接续受阻事项，更新同一事项的实际负责人、分支、会话和证据，经协调同步共享领取，不再建同义编号。
4. 旧子 agent 和子终端已全部收尾；EX-001 接续使用下述新会话。已结算 Dispatch 不续投；复用资料和工具，不重建已完成模块或复制整套现场。

<a id="capabilities"></a>

## 当前产品能力与严格边界

已发布 **v0.11.0-alpha 是只读包**；当前 dev 另外实现自由 FT 编辑与受限另存，未发布新的编辑安装包。版本字符串可能相同，使用源码／EXE 摘要和具体入口判断能力，不用版本号推定功能。

| 部分 | 当前已有 | 继续保持的限制 |
| --- | --- | --- |
| PCB／视图 | 严格载入已覆盖记录、图层、选择属性、元件定位、测量及端点捕捉；正式 `pt-pcb-check` | 文字和部分轮廓近似，代码页／历史格式不全，CLI 解析成功不证明原软件兼容 |
| LIB／NET／铜 | 只读库浏览、NET／受限 NETDEF、引脚映射与保守几何分析 | 未实现元件放置／替换、库写入、完整 DRC、交互／自动布线、生产输出 |
| 已载入自由 FT | 整数 mil 整线移动／删除、Undo／Redo、保存点和未保存保护 | 元件内与其他类型只读；宽、层、extra 不可改 |
| 普通另存 | 冻结原字节，只补四坐标词或删除原 FT；全新目标、临时文件后不覆盖发布 | 不覆盖原件或已有目标；Ctrl+S 覆盖保存未开放；成功仅标保存点，不重绑原输入或清历史 |
| 内部 Created | 身份／历史、预览／提交、显式编码／预检／writer、画布及 MainWindow 显式另存闭环已完成 | 参数必须显式给出；`trackPlacementUserEntryAvailable()` 仍 false，正式菜单／F3／P→T 禁用，默认 MainWindow／writer 拒绝 Created；新增遇 NETDEF 继续拒绝 |

新增内部约束为整数 mil：端点 ±1000000、宽 1..1000000、层 1／6、零长拒绝，不隐含取整或网格吸附。总文件 64 MiB，语法记录（含 COMP／ENDCOMP／内部记录／ENDPCB）最多 200000。这些是当前工程规则，不是已恢复的全部原格式限制。

原 AUTOTRAX 自建单线保存重开及实际默认编码／布局仍缺。最新 extra 静态规则不能替代该样例，也不能据此打开新增门或解除铜覆盖保守策略。

<a id="validation"></a>

## 已有验证与适用范围

产品 `src/`、根 CMake／预设仍沿用已测 `d2ee381161fdb444255f7db931aa1f1290aa5bd7` 基线；之后新增了文档检查、研究工具及其测试，不能再说全部 tools／tests 与该基线相同。本次交接只改文档与文档维护规则，不重复完整产品构建或 GUI。

- 固定候选 Debug／Release 配置、构建、CTest 各 **24/24**，原日志与 wait 保留；正式 CLI QProcess 专项 15 项。核心定向审查另有 **82 passed**（含初始化／清理），范围见[核心审查](docs/track-core-boundary-review.md)、[综合记录](docs/native-sample-wave.md)和[离线集成](docs/native-evidence-wave.md)。不把不同候选数量累加为当前整体覆盖。
- [真实 Qt 核心现场](docs/parallel-save-hardening-live.md)：固定 `374b1d7` 的读取生命周期、失败保留、旧 watcher 隔离、关闭取消、主窗另存、保存点／历史、输出重开；18 图及原 owner 正常 wait0。未重演的模态重入等范围继续按报告保留。
- [内部显式新增现场](docs/mainwindow-created-save-live.md)：显式合成六字段／LF 新增、取消、原生另存、历史、隐藏层、输出新进程重开，24 图及正常退出。不是正式新增入口或原 AUTOTRAX 兼容通过。
- [独立产品原生文件流程](docs/native-save-roundtrip-verification.md)已有限通过，不等于所有 dirty／失败／覆盖情形均通过。
- 原字形已有静态、受控机器码矩阵、边界／复制实验及 A240 局部现场；整体 `runtime_verified=false`。真实 NET／铜迟到竞争、极端坐标、系统会话结束、干净 Windows 等缺口仍在队列，实验或诊断小窗通过不能替代产品验收。

<a id="research"></a>

## 首轮四项独立探索的交付与剩余未知

四个首轮独立 Pi 会话实际均为 **`deng/gpt-6.1-sol / high`**，当时只完成离线／静态阶段，完整 Task 均按 failed 结算。后续 EX-001 实机接续及 EX-004 两轮客体捕获 Task 均已 succeeded，完成条件闭环并删除待办；EX-006／008／017 仍受阻，队列当前共 41 项。

| 事项／研究提交 | 已沉淀结论与验证 | 接续时的具体缺口 |
| --- | --- | --- |
| [一次菜单观测结论](docs/native-menu-click-audit.md#live-menu-conclusion)／`4266c52` | 实机兼容 33 样本及真实线程 join；一次菜单 Click 的 189 样本完整覆盖与真实菜单后图；七组原创建／退出身份匹配且 wait0；28 项定向测试及 13 项阶段注错通过 | 原 EX-001 已闭环；旧前景来源不可追溯边界留 EX-038，菜单活动时 Alt+F4 响应边界留 EX-003；连续客体捕获仍待 EX-004 |
| [EX-006](docs/exploration-backlog.md#ex-006)／`6281f84` | [宏、Repeat、Un-Delete](docs/legacy-command-dispatch-static.md)：队列／录制／递归状态、模板累计放置、删除类型栈／对象链；96 项静态断言及 18 区域核验 | 实际 KEY 状态、宿主键码、录制上下文、Repeat 和 Un-Delete 运行响应；不能直接映射成 Qt 重复／通用撤销 |
| [EX-008](docs/exploration-backlog.md#ex-008)／`bb3b540` | [FT extra](docs/ft-extra-static-semantics.md)：缺失→0、仅整数 1 置对象标志真、所核定保存路径输出显式 0／1；预布走线平滑消费者；178 记录及 30 指令核对 | 全部电气／间接消费者、非规范文本边界及原软件对照。继续保留原值和存在性，含 extra 铜走线继续覆盖不完整，不用静态归一化重写原件 |
| [EX-017](docs/exploration-backlog.md#ex-017)／`3ff4a3d` | [LIB 目录](docs/library-directory-state.md)：查名排除 FFFF、删除只改指针保留名称／计数、双 FFFF 初始化、首空槽复用、压缩按同名去重；四库盘点、6 测试、25 根 CFG 核对 | 合法别名、非零保留字段、其他版本和中断失败状态；不按残留名称或未引用数据猜测恢复 |

四项事实和失败记录已经在版本控制内专题中，无需从旧会话重新整理。新结论继续补现有专题；发现独立未知先去重、追加双向事项。达到完整完成条件后替换全部事项入链为结论，再删正文与索引，编号不复用。agent 退出不等于事项完成。

<a id="plan"></a>

## 下一步计划：按依赖推进

EX-001 接续 Task `task_0dbd022cdd62`／Dispatch `ctx_93fb7c0c4213` 已 succeeded，交付 `4266c5294d644893639a8c7c13fff72779b6cc6d`。同一 Pi `01a1cb98-e57e-75d0-9b06-c40a941eaaf0` 随后完成 EX-004 Task `task_57c256b62a70`／Dispatch `ctx_9bb156265144`，交付 `ceee461eb2dd7e20c1e290612a28833b6ebe1765`；实际模型始终 `deng/gpt-6.1-sol / high`。两轮各一张新客体 PNG，路径／动作独立、均为 640×480／6155 字节，图像同为可辨 AUTOTRAX 1.57 启动页，字节相同符合原条件。四次各 190 样本覆盖完整，十张原图匹配实际 read 回执，target／service／driver／owner 四组身份匹配且 wait0，最晚 UTC 18:58:48 退出。父另实际读两张客体原图并核集合差、单调锚点和四组原 wait；没有板名／计数或编辑通过结论。

工作树 `explore-ex001-observer`、分支 `research/ex001-live-observation`／`research/ex004-continuous-capture`、证据 `.local-analysis/ex-001-continuation/`／`.local-analysis/ex-004/` 保留。父协调 Pi 为 `01a1cb92-9f30-71d5-a89b-dca34f1b90e1`。下一主线 EX-005 继续复用实际 Pi／工作树，以新 Task、独立分支和新槽接续，不给已结算 Dispatch 追加业务。

首候选因停止信号缺口未放行；v2 因 PowerShell 5.1 加载无 BOM UTF-8 脚本解析失败而零现场，原 GO 撤销。修后 v3 一次菜单后验通过，但公开 Alt+F4 后原目标 wait5 秒超时；完整 120.001889 秒零新增桌面请求后，经父另审正常退出 helper，依据新图一次正常宿主 X 收尾。七组已知原创建／退出链均精确匹配且真实 wait0，最晚 UTC 18:16:09 退出。父已独立核原件及采样覆盖。v3、独立收尾槽、旧 GO 和失败证据全部只读，不能续跑；完整事实见[实机结论](docs/native-menu-click-audit.md#live-menu-conclusion)。

用户明确“现在开放两个小时给你的控制时间，你调节子agent的控制顺序”。父于同机 UTC `2026-11-11T18:02:12.1522606Z` 登记总窗口至 `20:02:12Z`（北京时间 11 月 12 日 02:02:12–04:02:12）。授权覆盖后续必要键鼠和子 agent 控制顺序，由父自主调度，不重复索同一许可；全部子 agent 继续 Pi、`deng/gpt-6.1-sol / high`。EX-001／004 现场已经正常收尾，后续 EX-005 接续仍由同一实际 Pi 操作者独占桌面，其他 agent 仅可离线工作；切换操作者必须核实前一现场正常收尾及原持柄等待结果。新的总授权不解除冻结方案、控制门或拒绝静默约束。

剩余总窗口按实际交付进度顺延 EX-004 → EX-005 → EX-007；各阶段先登记共享领取、准备具体方案及新冻结 GO，不直接执行原临时预算中的时刻或输入。UTC 19:55:12 起至少保留最后 7 分钟整体收尾，所有输入不得超过 UTC 20:02:12。父审查、闭环判断及授权记录在 `.local-analysis/ex-001-continuation/`，含 `completion-decision.json`、`cleanup-scene-review.json`、`control-window.json`。

1. **消费一次菜单观测结论。** 读[实机时序与支持范围](docs/native-menu-click-audit.md#live-menu-conclusion)，复用已有观测／驱动／真实等待工具；不重做最小观测器，不把有限通过外推为旧因果恢复。
2. **消费已完成的两轮客体捕获。** 读[两轮客体捕获结论](docs/native-capture-checkpoint.md#continuous-capture-conclusion)，复用逐步菜单实际 read、全目录集合差、新图摘要与客体 read、同驱动正常 X／原 wait 流程。已退出槽和坐标不复用，启动页不能替代实际工作状态。
3. **可靠观察后取得状态和单线样例。** [EX-005](docs/exploration-backlog.md#ex-005) 核有效配置、Information／Status 工作文件名和计数；[EX-007](docs/exploration-backlog.md#ex-007) 在确认空板、层／宽／端点后新建一段，以全新 8.3 文件另存并由原 AUTOTRAX 重开。字节、参数、图像、日志和前后摘要共同核定默认策略。静态保存函数、内部合成参数或某一层样例不能替代完整证据。
4. **最后接正式产品入口。** 用 `pt-pcb-check` 核结构，再复用现有显式 MainWindow／writer 路径接默认策略与唯一能力门；新增 NETDEF 仍需专门证据。按 [EX-029](docs/exploration-backlog.md#ex-029) 验证菜单／F3／P→T、文本焦点、整数取点、取消、隐藏层／模态／换图、历史、Windows 原生另存及原软件重开，不重做已有核心。

可并行做 EX-006／008／017 的具体剩余静态问题，阅读和证据独立，父统一验收、共享文件及取号协调。GUI／原软件桌面始终只有一名操作者；不能为凑并行重复实现、抢焦点或把其它 agent 的推测当证据。异步产品竞争仍按 [EX-035](docs/exploration-backlog.md#ex-035) 的真实 Qt／UIA、冷探针和预算前置推进，不挤占本次原软件取证主线。

<a id="scene"></a>

## 原软件现场事实与继续时的约束

最新[两轮新客体捕获](docs/native-capture-checkpoint.md#continuous-capture-conclusion)已通过并正常收尾，仍未产生 NEWFT 或确认板名／计数；客体可辨而宿主黑底白线的边界留 EX-002。此前[一次菜单观测](docs/native-menu-click-audit.md#live-menu-conclusion)同样通过。更早两槽的历史结果见 [native-capture-checkpoint](docs/native-capture-checkpoint.md)及[驱动审查](docs/native-capture-driver-review.md)：两槽均 failed，guest PNG 均 0，NEWFT 未产生，原退出和完整摘要证据保留。旧 PID 全是历史证据，不操作它们。

已排除公开 `Shortcut f11+p` 会保持 F11 的假设：安装函数先释放 F11，再发送 Unicode p。菜单标注 F11+P 不证明该接口已送达等价组合。第二槽 Click(545,160) 已发送，但约 0.574 秒前后采样只见终端前景，没有菜单后验；Click 不自动乘二、父聚焦后无 shell 插入都已核对，根因仍未定。更早已有单张可辨客体图、C21／A240 局部状态及宿主黑线而客体可辨的证据，不能覆盖最近失败或推广全部黑屏同因。

- 用户既有必要键鼠授权持续有效；新现场先完成具体可审阅材料，说明**当前实际时段、目标、范围和预算**，不重复索取已授予的同一许可。旧 GO／旧截止不沿用。
- 公开门、锁屏、精确 PID／创建时间／映像／HWND／owner、当下前景和实际图片后验保持。首次拒绝后按冻结约定完整 120 秒零新增桌面请求，输入已执行后的观察失败不重发输入，不换接口绕过拒绝。
- 正常收尾余量至少 7 分钟（具体新场景须写入预算），由原创建者持有 Popen／HANDLE 直到真实 wait；不使用强杀制造通过，不把服务退出或 runner-finished 当成目标／owner 的原退出码。FILETIME 用原 JSON／Python 整数或字符串，不经 JavaScript Number 丢精度。
- 观测预测、工具成功文字、日志事件与截图各有范围；指定模型必须实际读取图片。不要展开含 image.data 的完整 RPC，大输出落盘后筛字段。
- 异步竞争另守原 5 秒／32 次、20／50／55／60 秒及 600／900 秒预算。单 UIA 对象严格生命周期已有限通过，不等于真实 Qt／整窗／原生框或有效 NET／铜竞争通过；cancel 后 discarded 仍不通过，`ready_for_live=false`。

<a id="agents"></a>

## 模型、派发与历史 agent 收尾

用户最新明确指定：**本次工作及接续的子 agent 全部使用 Pi、`deng/gpt-6.1-sol / high`**。该显式授权优先于 AGENTS 和旧报告中的纯逆向 GLM 默认分工；新 agent 不应再以旧 GLM 配额问题停止这轮已授权的模型路线。保持独立工作树／分支／证据和父级验收，不重复启动同一任务。

本轮 Orca 结构化 Pi 启动忽略了工作树默认模型，`worker-start --agent pi --model ...` 又拒绝参数。实际可靠方式是：先通过 Orca 建立／复用专用终端，用 Pi 的 `--provider deng --model gpt-6.1-sol --thinking high` 显式启动，再用 `worker-start --terminal` 绑定任务。先读实时 orchestration／orca-cli 技能和 CLI help；启动界面或配置不等于模型证明，必须核对 PI 环境、原 JSONL model／thinking 事件、实际 assistant 和成功工具回执。旧错误模型尝试及 GLM 429 配额失败均保留原记录，不冒认成果。

最近探索 Run 为 `run_2809cae6026b`。下表 Task 已结算，不能恢复旧 Dispatch／inbox 追加业务；原会话可只读复查，后续同事项应登记新实际归属。

| 事项 | Task／最终 Dispatch | Pi 原会话 | 独立分支 |
| --- | --- | --- | --- |
| EX-001 | `task_3903c40083a3`／`ctx_cdfee6b64af8` | `01a1cb26-1411-7553-be7e-98cfa74d0e98` | `research/ex001-readonly-observer` |
| EX-006 | `task_97a62f2a4660`／`ctx_54f4486b50d7` | `01a1cb42-030b-7113-982d-8f6a4bd79ba1` | `research/ex006-command-dispatch` |
| EX-008 | `task_d913518e29a3`／`ctx_abb7c92f8325` | `01a1cb42-06ef-7017-9f48-3ada4f0d4276` | `research/ex008-ft-extra` |
| EX-017 | `task_b61ab7998498`／`ctx_897a4a52cf7d` | `01a1cb42-0ab9-77f9-a99c-99f1ca944f37` | `research/ex017-lib-directory` |

用户已授权全权处理此前派发的本工程 agent。已盘点 91 条历史派发；本轮 3 个驻留 Pi 用 `/quit` 正常退出，EX-001 已释放；随后 7 个空闲 shell 全部关闭。最终本机本工程子 agent、活子终端及不可核验子终端均为 **0**，主协调会话保留。29 个失效旧终端引用只是历史记录，不是 29 个活进程；原退出码不补造，不重置跨项目数据库。EX-006 关闭一处孤立页曾返回 tab_not_found，后验确认 connected=false、writable=false、exitCause=operator_close、工作树终端列表为空，不盲重试。

工作树卡片的历史 in-review 标记表示阶段交付已收尾、完整事项仍受阻，不等于正在运行或研究完成。分支、会话、工作树、原软件和失败证据均保留；清理详情见 `.local-analysis/agent-cleanup/REPORT.md` 和 `authorized-final-state.json`。当前不再有可继续操作的旧子 agent 终端；新接续 EX-001 使用 `term_896ab8d5-51f6-4082-b741-6eec0625269e`，通过其新 Dispatch 协调，不向终端追加业务提示。

<a id="evidence"></a>

## 本机证据、归档与可复用环境

当前协调根为 `C:/Users/rikideng/orca/workspaces/pt_renew/main-2`。下表相对 `C:/Users/rikideng/orca/workspaces/pt_renew/`；忽略材料不随 Git clone 分发，跨机器不能以缺少这些文件否定报告结论，也不能为接手重复复制整套材料。

| 位置 | 用途 |
| --- | --- |
| `main-2/.local-analysis/exploration-wave-01/` | 四项 spec、模型路由／配额失败、实际模型与领取、两阶段父集成及 final-state；旧 spec 的 GLM 文本已由用户新授权覆盖 |
| `explore-ex001-observer/.local-analysis/ex-001/` | 只读候选、旧 JSON／AST 独立核对、假 API 与失败原件 |
| `explore-ex006-command-dispatch/.local-analysis/ex-006/` | 宏／Repeat／Un-Delete 地址、可达解码、96 核验、103 输入摘要与清单 |
| `explore-ex008-ft-extra/.local-analysis/ex-008/` | extra 原字节／调用、178 记录与 30 指令核对、候选消费者及 cleanup |
| `explore-ex017-lib-directory/.local-analysis/ex-017/` | 七原件摘要、四库目录、25 根 CFG、工具／CLI 对照及 cleanup |
| `main-2/.local-analysis/native-capture-checkpoint/` | 快捷键 AST、点击审计、父驱动复现、两槽退出／摘要、7 图回执 |
| `review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate/` | 正式冻结 driver／gate／submit、`slot` 与 `slot-retry-01`、原图／配置／GO／原 Popen 退出；全部只读，不直接续跑 |
| `native-startup-diagnosis/.local-analysis/native-capture-checkpoint/` | 首版准备；后版模块曾改变而 plan 未重冻，不能套用旧摘要或直接运行 |
| `main-2/.local-analysis/native-sample-wave/`、`parallel-development-20261103/` | 原产品 24/24 与前轮 23/23、CLI、主窗／writer 固定来源及真实现场父审计 |
| `verify-parallel-save-hardening/.local-analysis/parallel-save-hardening-live/` | Qt 核心 18 图、输出和原 owner 退出 |
| `feat-track-placement-ui/.local-analysis/mainwindow-created-save-live/` | 内部显式新增／原生另存／输出重开原证据 |
| `main-2/.local-analysis/agent-cleanup/` | 历史派发盘点、正常退出和 7 shell 关闭原回执 |
| `main-2/.local-analysis/temp-maintenance/` | 唯一旧会话盘点 ZIP 和完整清理清单，不重复解压或执行历史删除脚本 |
| `main-2/.local-analysis/handoff-maintenance/` | 本次淘汰交接原文的一份 ZIP、逐文件大小／SHA-256 核验、维护脚本和最终 Git 状态；仅供历史追溯 |

原安装 `D:/project/pt_renew/pt/` 与 `pt_install/`、原库和用户板图只读；任何运行／写入试验使用独立副本并保留完整输入摘要。`pt/`、`pt_install/`、`.local-analysis/`、截图、字体、SDK、构建、会话及反编译数据库不提交，不 `git add -f`。

部分旧验证路径是指向 `C:/Users/rikideng/orca/worktree-archives/pt_renew/` 的目录联接，无 `.git`，仅供只读证据访问。先读 `.local-analysis/WORKTREE_CLEANUP_NOTICE.md`，不当成活开发工作树，不删除或跟随联接清理。目录名不保证等于分支，任何接续先核实时状态。

既有 Qt 6.12.0／MSVC x64／Ninja，SDK 为 `C:/Users/rikideng/Qt/6.12.0/msvc2022_64`。桌面产品无需 Python，研究工具用已有 Python／Capstone；先盘点工具、依赖、归档和 build，不下载无关依赖。复现入口：

```powershell
& ./scripts/Enter-QtEnv.ps1
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
# Release 使用 release 预设；长测试保持原创建者等待及独立日志。
& ./build/release/pt-pcb-check.exe --track-limit 100 <隔离PCB路径>
python tools/check_exploration_docs.py
```

CLI 帮助及 schema 见[专门说明](docs/pcb-check.md)。`e0cc7fd9c64e7e332461b093ab2849aaedf978c0a247573c3c520c39331a0d8d` 是历史已验 CLI 的摘要，重建后重新记录，不能当新文件的自动身份。writer／planner 的大容量 Debug 用例需要原预算，不让短工具超时中断测试。GUI 修改仍须真实交互。

<a id="history"></a>

## 唯一入口维护与旧文档追溯

以后只更新本文件承载当前进度、接手约束和下一步；PROGRESS 只做能力概览，主题／专题负责软件知识，探索待办负责未闭环问题。不要另建 SESSION_HANDOFF、按日期命名的 agent-handoff、CURRENT_AGENT_HANDOFF、NEXT_AGENT_BRIEF 或另一个“当前接手摘要”。用户明确要求唯一交接，不再保留这些兼容入口。

本次从工作树移除 12 份受版本控制的旧交接／历史根文档，以及 4 份本机活跃旧接手摘要；删除前完整归档并逐文件校验大小与 SHA-256。旧全文在 `c05baff` 及更早 Git 历史中仍可追溯，例如 `git show c05baff:docs/agent-handoff-20261104-capture.md`。本机核验归档见上表；子任务冻结目录内的旧说明和失败证据保持原样，只作历史，不是额外交接入口。

旧交接里的阶段测试、失败、迟到、PID、GO 和批准不升级为当前状态。需要某一历史事实时优先查[完整专题索引](docs/reference-index.md)中的原报告；没有原证据不能补成功或删除探索事项。
