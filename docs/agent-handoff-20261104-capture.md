# PT Renew 新 agent 统一交接：输入核验与两槽现场之后

本次用户要求“先进行所需验证，然后整理当前进度和下一步计划，我让新 agent 接手”。本轮只完成交接核验与文档，不派发接手者、不启动新开发或桌面现场。新 agent 先读 `AGENTS.md` 和本页；Git、原始日志和证据优先于旧进度文字。

## 当前基线与完成范围

整理前 `dev=origin/dev=远端dev=acb983dbf2d5069f090f969ed526c2b828e35a6e`，工作区干净。本交接从该基线的 `docs/handoff-capture-20261104` 提交，按 no-ff 合 dev 并推送；最终 SHA 见本机 `.local-analysis/handoff-capture-20261104/final-state.json`，不要把整理前 SHA 当最终 HEAD。

产品源码、正式测试、仓库 tools 与根 CMake／预设仍与已测候选 `d2ee381161fdb444255f7db931aa1f1290aa5bd7` 相同。后续提交只有文档与合并，本轮未操作 main、tag、发布或 dist。当前本地 `main=3e13f69528cfc033718ef8352b8d3fb7bce915bd`，本地跟踪 `origin/main=cfb6a8893aaf8d8b5778a24c00fc97813c5f083d`；两者不能混称“main 保持同一 SHA”，本轮没有合并、推送或更新 main。

| 能力 | 已完成 | 仍有限制 |
| --- | --- | --- |
| PCB／LIB／NET 查看 | 严格解析、分层预览、选择属性、定位、测量、端点捕捉、引脚映射与受限铜分析 | 文字／部分轮廓近似，不是完整 DRC 或生产放行 |
| 载入自由 FT 编辑 | 整数 mil 整线移动、删除、撤销重做、保存点与未保存保护 | 元件内部图元及其他类型只读；宽／层／附加字段不可改 |
| 普通另存为 | 已有合法 FT 修改另存全新 PCB，未改字节保留 | 不覆盖原件或已有目标，Ctrl+S 覆盖保存未开放 |
| 内部显式新增闭环 | 身份历史、布局、placement session/controller、显式 codec/planner/writer、画布、MainWindow 显式另存 | 调用方必须明确编码，诊断路径不是正式产品新增开放 |
| 只读 `pt-pcb-check` | 正式构建、过程测试、UTF-8 JSON、冻结字节与有界自由 FT／布局核查 | 严格解析成功不证明原 AUTOTRAX 兼容，不选择默认编码 |
| 原软件取证工具 | 当前步骤／nonce／实际 host/guest 摘要审核、菜单两阶段、完整预检、截止和正常收尾路径 | 属于忽略目录隔离工具，现场连续客体捕获仍未完成 |

**`trackPlacementUserEntryAvailable()` 仍 false，菜单／F3／旧式 P→T 未实现／禁用；默认 MainWindow／writer 拒绝 Created，有新增时 NETDEF 仍拒绝。** 原 AUTOTRAX 自建单线保存重开、FT 默认六七字段／extra／换行／布局仍未知。不要翻门、删拒绝或从合成样例猜默认值。

## 已完成实现入口与验证

| 入口 | 职责 |
| --- | --- |
| `src/application/BoardEditSession.*`、`src/domain/TrackIdentity.h` | Loaded 按原标签行，Created 单调非零；新增／移动／删除共用历史、分支不复用身份 |
| `src/io/LegacyPcbReader.*`、`LegacyPcbLayout.h` | 冻结完整输入、严格语法、顶层边界、ENDPCB／EOF／NETDEF／换行事实 |
| `src/application/TrackPlacementSession.*`、`TrackPlacementController.*` | 预览不 dirty／不分配身份、上下文失效取消、后端拒绝保留有效预览 |
| `src/io/LegacyFreeTrackCodec.*`、`LegacyTrackInsertionPlanner.*`、`LegacyPcbWriter.*` | 显式六七字段与换行、插入预检、容量／语义复核、全新文件发布 |
| `MainWindow::saveAsFileWithCreated(path, options, error)` | 内部显式新增另存，成功才标保存点，保留原输入身份和历史 |
| `src/ui/MainWindow.*` | 已修复旧异步回调解锁后续 busy、作废载入 loading 恢复、放弃确认重入丢修改 |
| `src/io/LegacyPcbWriter.cpp` | 几何按分量精确比较，拒绝 Qt 模糊相等放过的小数修改 |
| `tools/InspectPcb.cpp`、`tests/PcbCheckTests.cpp` | 正式只读 CLI 与真实 QProcess 测试 |

新增约束：有限整数 mil 坐标 ±1000000，宽 1..1000000，层 1／6，零长拒绝；无隐含取整／网格捕捉。整体 64 MiB、语法记录含 COMP／ENDCOMP／内部记录／ENDPCB 不超过 200000。原记录仅改四坐标词或删除；Created 放在严格确认的无 NETDEF 顶层 ENDPCB 前，extra 为显式输出投影，不反写内存。

固定候选 `d2ee381` 的 Debug／Release 配置、构建及 CTest 各 **24/24**，原创建者退出 0，CTest 日志 125.23／19.08 秒；CLI 独立 QProcess 15 项。近期核心审查无修复，Debug 定向及消费者 offscreen 合计 **82 passed**（含初始化／清理），不等于新完整矩阵或 GUI 通过。详见[核心审查](track-core-boundary-review.md)、[上一轮综合](native-evidence-wave.md)。

Qt 核心已有独立真实验收：固定 `374b1d7` 的异步读取生命周期、失败保留、旧 watcher 隔离、关闭取消、真实另存、Undo dirty／Redo clean、输出重开，18 原图与回执匹配，原 owner 正常 wait0；详见[核心现场](parallel-save-hardening-live.md)。更早显式 Created 的整数新增、取消、原生另存及输出新进程重开已通过诊断闭环，见[显式新增现场](mainwindow-created-save-live.md)。这些结论保持原范围，不补作正式菜单或原软件兼容通过。

CLI：先 `& ./scripts/Enter-QtEnv.ps1`，再 `& ./build/release/pt-pcb-check.exe --track-limit 100 <隔离PCB路径>`。本机 Release SHA-256 仍为 `e0cc7fd9c64e7e332461b093ab2849aaedf978c0a247573c3c520c39331a0d8d`；重建后须重新记摘要。核退出码和 `succeeded`，兼容标记恒 false。Qt 6.12.0／MSVC x64／Ninja 已有，SDK `C:/Users/rikideng/Qt/6.12.0/msvc2022_64`，不安装无关依赖。完整[CLI说明](pcb-check.md)、[环境说明](qt-development.md)。

## 最新输入事实与两槽失败

先读[父验收报告](native-capture-checkpoint.md)和[驱动审查及冻结](native-capture-driver-review.md)，不要直接执行历史 [短观察方案](native-short-observation.md) 的 F11+p 建议。

父只读实际安装的 Python 函数，以原 AST／枚举、假输入 API 实跑四例：公开 `Shortcut f11+p` 生成 `{f11}p`，事件是 **F11 down → F11 up → Unicode p**，不能保持 F11；Shift+i、Alt+F4、Enter 的解析顺序符合预期。该结论只证明安装函数解析，不证明目标应用响应，不等于“DOSBox 截图热键失效”。旧 Capture 菜单显示 Take screenshot=F11+P 的原图仍有效；菜单标注与工具能否发送对应组合分开。

旧驱动 12 项缺口已子复现、父新目录独立复跑；最终工具包修复实际文件摘要／当前步骤与 nonce 审核、菜单 open→select、生命周期不读取业务 state、门后输入前截止、RPC 余量、完整 runtime/inputs/frozen_files 预检和失败后静默只收尾。最终 36 项假 fixture、原 main 假环境八步两轮、完整 preflight 退出 0；第二槽准备另有 13 项。它们不是 GUI 成功。最终仍不能自动保证目标有界正常退出：截止未退时原 owner 记录 unproven 并持 Popen 等父正常关闭，不能强杀或把服务退出当目标退出。

| 2026-11-03 北京时间 | 实际现场 | 退出结论 |
| --- | --- | --- |
| 首槽 23:17–23:37，23:30 起仅收尾 | 新目标启动，公开 App 精确聚焦后取得清晰 AUTOTRAX 1.57 启动页；23:22:38 菜单 Click 前 guard 发现 Windows PowerShell 前景，**Click 未发送**。完整 120 秒零新桌面请求后只收尾 | 父核本轮精确身份一次正常 WM_CLOSE；目标 23:25:43.951809 wait0、服务 23:25:44.279924 wait0、driver 23:25:44.288379 wait0 |
| 第二槽 23:31–23:51，23:44 起仅收尾 | 驱动三模块不变，全新副本；App 后父仅 read/write，不插 shell。23:33:23 Click(545,160) 已发送并回成功，但后图无 Capture 菜单且终端前景；不以 purpose／文字回执认定菜单打开，不重发、不猜选择，停止业务 | 父精确身份正常 WM_CLOSE；目标 23:37:40.518503 wait0、服务 23:38:13.709774 wait0、driver 23:38:13.761237 wait0 |

两槽均 **failed**，guest PNG 均 0，NEWFT 未生成。7 张宿主原图父实际 read，字节与原会话 image 回执 7/7 匹配；原安装 99 项、runtime 各 99 项、inputs 各 1 项完整集合／大小／SHA 不变；目标、服务、driver 共六组原 PID／Popen／HANDLE／FILETIME 创建退出一致，均在各槽截止前退出，无强杀。

首槽父曾考虑 shell 插入影响前景，第二槽无 shell 仍出现终端，故单因假设不成立。窗口裁剪原点 (89,100)、图 662×566；全屏 3840×2160 缩到 1920×1080，比例 2；第二槽 Click 后 Snapshot 记录光标 (545,160)。尚未解释菜单为何未出现，不归因用户、DPI 或某 API。父辅助参数／编码错误和过早读缺文件事实保留，未据此重发输入。

更早 15:35–16:20 现场只取得单张菜单选择产生的客体启动页，未连续捕获，父迟到 16:25 收尾事实继续保留，见[native-guest-save-sample](native-guest-save-sample.md)。新槽按时退出不改写旧迟到。

**本轮所有原软件目标／控制服务／driver 已原创建者正常退出，桌面已释放。PID 均是历史证据，不按旧 PID 操作。** Pi external_terminal／retained／processAction none 不代表 Pi OS 已退出。

## 本次交接补验

2026-11-04 在全新 `.local-analysis/handoff-capture-20261104/` 保存核验，不覆盖旧材料：

- fetch 后 dev／origin/dev／远端 dev 基线一致，源码及 tools/CMake 与 `d2ee381` 无差异，CLI EXE SHA 一致，能力门仍 false。
- 重新读取两槽原创建／退出，六组身份与 wait0 一致；重新算原安装、副本、输入及冻结文件摘要，仍相符，输出与 guest PNG 不存在。
- 从原父 JSONL 重新提取 image 回执，7 张原图全部匹配；没有重新截图或冒称本次新 GUI。
- 在本次全新目录复跑快捷键原 AST／假 API 四例和旧驱动 12 项复现，均通过；最终 36 项与假 main 的结果／候选摘要保持对应。
- 最新 Run 的 Task 均已结算、收件箱 0、reclaimable 0；进程盘点未发现匹配本轮实验命令行的 Python／DOSBox／产品残留。进程不存在仅是现场状态复核，不能替代已有原创建者 wait 证据。

没有源码变化，不重跑完整构建／24 组、不启动新子任务或桌面。核验日志与最终 Git 见本机专题 `verification.json`、`final-state.json`。

## 下一步顺序与并行边界

1. **先做菜单点击的离线时序／坐标核对。** 对第二槽 `step-003-focus-owned-post`、`step-004-menu-one-*` 的原图、capture-scope、Snapshot 文本元数据、native-before/after、请求响应和原 JSONL 时间线逐项对齐。检查 Click 实际 screen-space 发送、窗口物理／逻辑矩形、DPI 上下文和目标前景在调用中的变化；提出能由证据区分的假设。不要只凭回执宣称“菜单已开”，不要重做长通用控制框架或无差别开第三槽。
2. **据明确依据再安排新短现场。** 用新隔离副本／slot／上下文／冻结，原槽只读；先两轮 Capture 菜单打开→当前菜单原图→选 Take screenshot→新 640×480 PNG 实际 read。每步最新宿主／客体审核与 nonce，成功消费后才下一步。先解决一次可靠动作的后验和前景，再扩展菜单，不回到 `Shortcut f11+p`。
3. **取得文件状态和真实样例。** 连续观察可靠后按已有实际 Shift+i／Shift+s 路径确认 Information／Status 文件名与图元计数；按图确认空板、明确层／宽／端点，新建一段、另存全新 8.3 文件、原软件重开。保存字节、图、参数、日志和前后摘要共同核定字段。一个层样例不推广全部层或 NETDEF 排序。
4. **用正式 CLI 核结构，再接普通产品。** 默认字段依据充分后复用已有显式 MainWindow／writer 路径接默认策略与单一门，新增 NETDEF 暂继续拒绝。完成菜单／F3／旧式 P→T、文本焦点、取点、取消、模态／换图／隐藏层、历史、原生另存、产品输出交原 AUTOTRAX 重开的独立验收。

可并行：一人只读做现场时序／坐标审计，一人离线核对公开输入实现与最小复现，各自报告与证据目录独立；现场只一名指定 GPT 操作者，Qt 与原软件串行移交。纯二进制逆向只有明确问题且 `glm/glm-5.3 high` 实际可用才派，最近 quota／concurrency 硬失败零工具，不能换模型或无限重派。没有字段证据时不安排源码开发者为凑并行重复已有模块。

## 本机材料、会话与任务结算

父根 `C:/Users/rikideng/orca/workspaces/pt_renew/main-2`；忽略材料不在 Git，跨工作树须按绝对路径读。

| 路径（相对 workspaces/pt_renew） | 用途 |
| --- | --- |
| `main-2/.local-analysis/handoff-capture-20261104/` | 本交接核验、新提示词、旧入口备份、最终 Git／Task 状态 |
| `main-2/.local-analysis/native-capture-checkpoint/` | 原 AST 输入复现、父旧驱动复现、冻结包核验、两槽身份退出／完整摘要审计、7 图回执匹配 |
| `review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate/` | 正式冻结 driver/gate/submit、首 `slot` 和 `slot-retry-01` 原件、配置、日志、图片、GO、Popen退出 |
| `review-track-core-boundaries/.local-analysis/native-capture-driver-review/` | 12／16／36 项假 fixture、main假环境、冻结与第二槽准备证据 |
| `native-startup-diagnosis/.local-analysis/native-capture-checkpoint/` | 原操作者首版准备；后来模块改过但 plan 未重冻，**不可运行当前后版或套首28项** |
| `main-2/.local-analysis/native-sample-wave/`、`parallel-development-20261103/` | 24/24 原日志／wait、CLI核验、主窗与writer固定来源／现场父审计 |
| `verify-parallel-save-hardening/.local-analysis/parallel-save-hardening-live/` | Qt 18 图、输出、原owner退出 |
| `feat-track-placement-ui/.local-analysis/mainwindow-created-save-live/` | 更早内部显式新增／原生另存／输出重开 |

最近 Run `run_c9bab9d00b23`：`task_f8c94a979620/ctx_ae9b1854c946` failed（准备有产物，连续捕获未执行）；`task_46be31be3ba2/ctx_c38cc667f1c9` succeeded（离线修订包）；`task_1e5b34acc232/ctx_2d207d616347` succeeded（第二槽准备）。后两 success 不包含父 failed GUI。三份唯一 worker_done 已验收 release／ack，reclaimable 0。

会话：native `01a19f6a-a52d-7333-95f3-2972829f4e9f`；工具审查 `01a1a161-c684-75ff-8e81-5918e22bf0ce`；父现场 `01a1a15a-5307-7312-a21c-9c61e64983f5`；主窗 `01a19f99-6515-720c-9e03-ee00ab05152e`；CLI `01a19f99-9252-74f7-9844-99633c12fe1f`；Qt QA `01a19fa1-5219-7342-9ee0-3e6eb23772b4`。目录名不等于分支，接手查实时状态。已结算 Task／Dispatch 不复用、不向旧 inbox 追加业务；同一未完成工作沿用已有 Pi，会话空闲／工具状态核实后再继续，不改原 provider 记录。

## 协作约束

所有子 agent 用 Pi，启动明确模型／high／独立分支／范围／证据，并核原 model/thinking/assistant/成功工具。截图与后续截图验收只 `deng/gpt-6.1-sol high`，纯逆向只 `glm/glm-5.3 high`。Orca 1.4.245 下已验证方式是显式 `pi --model ... --thinking high` 终端再 `worker-start --terminal`；先读实时 orchestration／orca-cli 技能与 help。send 入队不等于已读；自然检查点 check／ack 到空，ask 超时 resume 原消息取 reply。

用户既有键鼠授权继续有效，现场前公告实时时段／目标／预算，不重复索权；公开门、锁屏／精确前景、单操作者、拒绝后原 120 秒零新桌面请求、至少 7 分钟只正常收尾和原 Popen/HANDLE 真实 wait 保持。无强杀、无换接口绕拒绝；正常自建目标生命周期与业务成功分开。别展开含 image.data 的 RPC 全文，图像需实际 read/image 回执。

中文说明／界面／日志／文档与 Conventional Commits；从最新 dev 独立分支，验证后 no-ff 合 dev 推送，main 仅用户处理。原安装／库／用户板只读，写入只用隔离副本留摘要。pt／pt_install／.local-analysis／截图／SDK／build／会话／数据库不提交，不 add-f。旧工作树先读 `.local-analysis/WORKTREE_CLEANUP_NOTICE.md`，归档联接无 .git 仅供只读，不清理旧证据。
