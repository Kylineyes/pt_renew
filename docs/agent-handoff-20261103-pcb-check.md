# PT Renew 新 agent 统一交接：严格 PCB 核验命令之后

后续用户已要求继续并行推进并由父验收，最新结果见[原软件短观察和新增核心](native-evidence-wave.md)：核心无修复审查与82项定向验证通过；GLM配额失败；原软件仅新增离线短方案，现场目标未完成。产品源码、默认字段未知及能力门关闭状态保持。本文以下为交接时基线与完整入口，不再限制后续已获用户授权的工作。

本次用户要求整理当前进度与后续计划，由用户自行安排新 agent 接手。整理者只核对和编写交接，不启动开发、子代理或桌面现场，不重跑已通过的构建／测试。新 agent 先读 `AGENTS.md` 和本页，再按具体目标读取专题；Git 和原始证据优先于旧进度文字。

## 当前基线与用户可用能力

交接整理前 `dev=origin/dev=69711e572fe510e29d7addd31bdbd32f84d94863`，工作区干净。交接文档从该基线的独立分支提交，按规范 no-ff 合 dev 并推送；交接后最终 SHA 见本机 `.local-analysis/handoff-pcb-check-20261103/final-state.json`，不要把整理前 SHA 当作最终 HEAD。

产品源码、正式测试及新工具冻结提交为 `d2ee381161fdb444255f7db931aa1f1290aa5bd7`，之后只有 README、报告及合并，`src/`、`tests/`、`tools/InspectPcb.cpp`、根 CMake／预设无内容差异。main 保持 `3e13f69528cfc033718ef8352b8d3fb7bce915bd`；本轮未操作 main、tag、发布或既有 dist，已发布包不随源码自动更新。

| 范围 | 当前状态 | 限制 |
| --- | --- | --- |
| PCB／LIB／NET 查看 | 严格解析、分层预览、选择属性、定位、测量、端点捕捉及受限铜分析 | 文字和部分轮廓近似，不是完整 DRC |
| 已载入自由 FT 编辑 | 整数 mil 整线移动、删除、撤销重做、保存点、未保存保护 | 元件图元及其他类型只读；宽／层／附加字段不可改 |
| 普通另存为 | 已有合法 FT 修改可另存全新 PCB，保留原字节及未改字段 | 不覆盖原件或已有目标；Ctrl+S 覆盖保存未开放 |
| 内部新增路径 | 身份历史、布局、放置状态／controller、codec／planner／显式 writer、画布及 MainWindow 显式另存已完成 | 编码选项必须显式指定，普通入口仍关闭 |
| 新只读 CLI | `pt-pcb-check` 已接入正式构建与真实进程测试 | 解析成功不是原软件兼容证明，不选默认编码 |

**`trackPlacementUserEntryAvailable()` 仍 false；菜单／F3／旧式 P→T 未实现／禁用。默认 MainWindow／writer 保存拒绝 Created，有新增时 NETDEF 仍拒绝。** 原 AUTOTRAX 默认 FT 字段和真实单线保存重开样例仍缺，不能只翻门、删拒绝条件或根据合成文件猜默认值。

## 已完成的代码与入口

| 入口 | 主要职责 |
| --- | --- |
| `src/application/BoardEditSession.*`、`src/domain/TrackIdentity.h` | Loaded 按来源行，Created 单调非零序号；新增／移动／删除共用历史，分支不复用身份 |
| `src/io/LegacyPcbReader.*`、`LegacyPcbLayout.h` | 冻结完整输入；严格语法及顶层边界、ENDPCB／EOF／NETDEF／换行事实 |
| `src/application/TrackPlacementSession.*`、`TrackPlacementController.*` | 预览不 dirty、不分配身份；上下文失效取消，后端拒绝保留有效预览 |
| `src/io/LegacyFreeTrackCodec.*` | 六／七字段、LF／CRLF、附加整数显式选择，无默认值 |
| `src/io/LegacyTrackInsertionPlanner.*`、`LegacyPcbWriter.*` | 在已有移动／删除结果上确认插入位置、容量、语义及重载身份，发布全新文件 |
| `MainWindow::saveAsFileWithCreated(path, options, error)` | 内部显式另存；发布成功才标保存点，保留原输入身份及撤销历史 |
| `src/ui/MainWindow.*` | 已修复过期后台回调解锁后续读取、作废后 loading 不恢复、放弃确认重入丢修改 |
| `src/io/LegacyPcbWriter.cpp` | 已按分量精确核对点／矩形，拒绝被 Qt 模糊相等放过的小数篡改 |
| `tools/InspectPcb.cpp`、`tests/PcbCheckTests.cpp` | 新正式只读核验工具及 QProcess 过程测试 |

已测约束：新增坐标为 ±1000000 mil 内有限整数，宽1..1000000，层1／6，零长拒绝；无隐含取整或网格捕捉。总语法记录含COMP／ENDCOMP／内部记录／ENDPCB不超过200000，整体64 MiB。新增放在严格确认的无 NETDEF 顶层 ENDPCB 前，Created附加值只作显式输出投影、不反写内存。已有编辑只替换四坐标词或删除原记录，保留混合换行、非ASCII、未解释字段与DOS EOF。

不要重复实现这些模块或再增加无消费者的框架。详见[内部闭环交接](agent-handoff-20261103-created-save-roundtrip.md)、[并行修复与验收](parallel-save-hardening.md)、[主窗修复](mainwindow-load-lifecycle.md)、[写出精确校验](pcb-writer-boundaries.md)。

## 最新构建、测试与工具

正式固定候选 `d2ee381` 已完成 Debug／Release 配置、构建和 CTest，原创建者逐进程真实 wait 均0，两配置各 **24/24 组**。Debug CTest原日志125.23秒、Release19.08秒；原创建者计时125.295／19.142秒。测试前后核对127个源码／测试／CMake文件摘要，后续文档合并不冒称新跑。

新 CLI 的独立 QProcess 测试15项通过，覆盖Unicode路径、六七字段／混合换行、正文伪标签／CT排除、明细截断、参数和损坏文件整体拒绝、NETDEF及64 MiB上限。CLI只调用一次readFile，再用该冻结sourceBytes作parseWithLayout，默认最多100条自由FT（可0..1000），输出UTF-8 JSON及永久false的兼容验证标记。

```powershell
& './scripts/Enter-QtEnv.ps1'
& './build/release/pt-pcb-check.exe' --track-limit 100 'C:/隔离目录/样例.PCB'
```

先核进程退出码和 `succeeded`；帮助不含 `succeeded`。退出0为严格解析或帮助，1为读／解析失败，2参数错误，3输出失败。详细schema见[CLI说明](pcb-check.md)。该次Release EXE SHA-256：`e0cc7fd9c64e7e332461b093ab2849aaedf978c0a247573c3c520c39331a0d8d`；重新构建后重新记摘要，不直接套用。

父正式CLI实跑两份前轮74字节合成输入，均exit0、前后输入不变：INPUT首段(100,100)→(400,500)，HARDENED-SAVED为(175,190)→(475,590)，两FT分别七字段extra42／CRLF与六字段／LF，ENDPCB偏移65、EOF73。它们不是原 AUTOTRAX 自建保存样例。

环境仍是Qt6.12.0、MSVC x64、Ninja，SDK `C:/Users/rikideng/Qt/6.12.0/msvc2022_64`，先运行 `scripts/Enter-QtEnv.ps1`，再用debug／release预设构建测试。容量测试Debug较慢，writer正式超时300秒／planner180秒；保留原创建者wait和独立日志，不因短工具等待杀掉测试。不需新装Vulkan／WebEngine／Creator。完整环境见[Qt开发](qt-development.md)。

## 真实 Qt 验收：已有核心通过，范围分开保留

主窗生命周期和writer修复固定源码 `374b1d7` 已由独立指定Pi实际窗口验证：排队读取期间编辑／UndoRedo、失败保留、同步失败inspect恢复、双门闸证明旧watcher销毁不解锁后续busy、关闭取消、真实主窗另存、Undo dirty／Redo clean、输出实际重开为Loaded且无历史。18张原图与实际image回执匹配，原owner13:12:53正常wait0、未强杀。报告[独立核心现场](parallel-save-hardening-live.md)。

其中第二次移动是旧控件索引误点，三次实际移动累计75,90；原图和误点记录保留。输出74字节SHA `51dbf589b06cc7b6fdd1d24b20f2c2b8b4a84fe4e95508b51466ee6474e786d3`，仅四坐标替换，其余字节不变。确认框API重入、同步成功替换、F3／文本焦点、本次Created／原生框未重演，不冒称本次全验。

更早主窗显式新增诊断闭环已实际验证整数新增、取消下一段、原生另存、保存点、隐藏层与菜单Esc取消、90字节输出新进程重开；六字段／LF为显式合成选项，不是产品新增开放。见[新增闭环现场](mainwindow-created-save-live.md)。新CLI不改GUI，本轮没有重复Qt现场。

## 原 AUTOTRAX：已知事实、最新失败与当前进程

先读[显示分离诊断](native-startup-diagnosis.md)和[最新两槽失败](native-guest-save-sample.md)。旧可辨启动页／主菜单事实有效；旧成功与后续黑图的归一OpenGL配置、99项runtime一致。已证一个旧槽公开Shortcut Enter后实际日志打开SYN1.PCB，DOSBox客体640×480图可辨而同期宿主黑线，说明不能用宿主黑线判断客体未推进，但不证明全部黑图同因或文件计数正确。

本轮先遭模型请求自动重试超时／连接错误、零工具；父压缩同一Pi后恢复成功工具，再做两槽：

| 槽 | 实际结果 | 退出／边界 |
| --- | --- | --- |
| initial：15:05–16:05 | 新submit固定request-next与既有consumed冲突，第二请求聚焦前FileExistsError；未Enter／Capture／业务 | 120秒静默后服务wait0；代理精确身份正常关闭目标，15:16:33原wait0 |
| retry-01：15:35–16:20，16:13只收尾 | 新目录／副本、唯一动作名投递；离线三轮消费及三拒绝验证通过。实际Capture菜单确认F11+P，菜单选择生成6350字节pt_000.png并实际read | 第二捕获请求16:16:31因只准收尾被拒，热键未发、无第二PNG；服务16:18:32原wait0，目标父16:25晚接手关闭 |

retry-01目录加深后新driver的REPO改parents[3]，导入／挂载／日志／捕获／输入输出与授权断言均通过，旧槽冻结和证据只读。此前第二后端只请求direct3d、未证实际生效，Capture未生成；本机CtrlF5为复制，不要按传统DOSBox猜截图键。F11+P这次已由实际菜单确认，但**快捷键本身尚未实际成功触发截图**，不能说连续热键捕获已通过。

第二槽模型连接延迟持续，未按16:20完成关闭。父 **16:25:44** 核PID31796／创建时间字符串134381656183249352／HWND14813192／映像后正常CloseMainWindow；原owner同Popen／HANDLE于 **16:25:45.236223** 记录wait0，无强杀。父迟到接手、缺失第二PNG的ENOENT、所有连接错误保留，不改成代理按时收尾。

两槽原安装99项、runtime各99项及冻结输入完整集合／大小／SHA未变；共8PNG均匹配指定模型image字节回执。两个NEWFT均不存在。没有验证连续截图、菜单Status文件名／计数、空板、单线新增、保存或重开，Task failed。代理最后自动重试以连接错误结束，没有worker_done或报告；父按原终止记录abandon，再明确Task failed，并编写事实报告，没有伪造代理回执。

**当前所有本轮原软件目标、控制服务和Qt验收目标均已退出，桌面已释放。** 所有PID均为历史证据，不恢复旧driver／inbox／服务或按历史PID关闭进程。Orca的external_terminal／retained／processAction none只表示未关闭Pi终端，不等于Pi OS退出。

## 下一步计划与并行安排

1. **先缩短原软件观察闭环。** 只读核对本机Capture菜单证据、已修复的唯一请求submit、缺失第二图的时段拒绝和连接延迟。新工作不再从归一配置对照、黑图截图、长控制框架或临时Inspect程序起步。先验证连续两张真实客体图，明确F11+P实际发送与落盘；模型连接不稳定时先停在可复核离线结果，不无限重派、重建副本或让活目标长期等待模型。
2. **取得文件状态与单线样例。** 连续捕获可靠后，通过已知公开键路径定向确认File／Information／Status、工作文件名和计数；核对旧Shift+I／Shift+S实际请求，普通f/i和误入Block不算成功。确认空板后选择有记录的层／宽／端点，新增单段，以全新8.3文件名保存，再由原软件重开。只有新保存字节、参数、截图、日志和前后摘要能证明默认字段；一个层的样例不能推广所有层或NETDEF排序。
3. **用正式CLI核定结构，再接产品。** 用固定摘要 `pt-pcb-check` 只读核对原软件样例和产品输出，核定六七字段／extra／换行／位置；严格解析通过本身不是兼容。依据充分后复用现有显式MainWindow路径接默认策略及单一能力门，不新增无消费者抽象，不单纯删拒绝。新增NETDEF首版继续拒绝，除非有专门证据。
4. **完成普通产品最终验收。** 菜单／F3／旧式P→T共享命令、文本输入不抢键、整数取点、预览取消、隐藏层／模态／换图、撤销重做、真正原生另存新文件和重开；将产品输出交原AUTOTRAX重开核对旧对象／新段／文件名计数，正常退出留原wait。复用已通过的核心证据，不重复整套模块。

适合两至三路：指定GPT独占原软件现场；指定GLM纯静态研究仅在模型可用且存在明确二进制问题时；源码开发者只在已确定编码证据基础上接产品，证据缺失时做具体源码审查／离线复现，避免为凑并行重复已有模块。独立分支／工作树／构建／证据，MainWindow与writer／core文件所有权不重叠，根CMake和跨模块测试由协调者掌握。原软件与Qt GUI验收串行移交桌面。

## 模型、键鼠与生命周期约束

所有子代理使用Pi，显式模型和high并核对实际model／thinking／assistant／成功工具：纯二进制逆向仅 `glm/glm-5.3 high`；截图及截图验收仅 `deng/gpt-6.1-sol high`，不可用不擅自替换。GLM前次quota硬失败零工具记录保持，本轮未重派。未完成同任务沿用原Pi，已结算Task／Dispatch不复用；需要新Task，失败恢复用明确retry-of而非重复开工。

Orca1.4.245拒绝Pi launch-time模型选择，已验证方式是专用终端 `pi --model deng/gpt-6.1-sol --thinking high` 后 `worker-start --terminal`；接手先读实时orchestration／orca-cli技能和help，不假定版本未变。结构化send仅证明消息入队，操作者每业务检查点必须check／ack直到空，未ack会挡住后续GO或收尾消息。

用户键鼠授权持续有效，新现场先预告当前具体起止／目标／预算，无需重复问同一许可；检查锁屏、公开控制门与精确前景，拒绝即停该动作，不换接口绕过。只一名操作者，至少留7分钟正常收尾，原创建者Popen／HANDLE真实wait，不依赖强杀截止。模型连接重试也消耗预算；没有活目标时才可考虑同会话压缩。不要展开含image.data的RPC全文，原JSON落盘保留，文本过滤字段，实际看图仍需read/image回执。

本次用户说“我让新agent接手”，由用户自己安排新会话；整理者不派发接手者。

## 本机证据与任务结算

父根：`C:/Users/rikideng/orca/workspaces/pt_renew/main-2`。这些忽略文件不在Git，跨工作树需按绝对路径读，不能因clone没有而否认完成。

| 证据目录 | 内容 |
| --- | --- |
| `main-2/.local-analysis/native-sample-wave/` | 最新spec／派发重试、双配置原日志wait、parent-cli-audit、两槽parent-native-audit、父正常关闭、final-state |
| `main-2/.local-analysis/parallel-development-20261103/` | 主窗／writer修复双配置23/23、冻结、18图／字节／进程父审计 |
| `../fix-pcb-writer-boundaries/.local-analysis/pcb-check-cli/` | 工具15项、两样例、原model／thinking及真实过程日志 |
| `../native-startup-diagnosis/.local-analysis/native-guest-save-sample/`及`retry-01/` | 两槽原始配置、运行副本、宿主／客体图、模型回执、submit修复及原Popen退出 |
| `../verify-parallel-save-hardening/.local-analysis/parallel-save-hardening-live/` | Qt固定快照、18图、两输入／输出、原GO和正常退出 |
| `../feat-track-placement-ui/.local-analysis/mainwindow-created-save-live/` | 前轮显式新增原生另存、取消及输出重开 |
| `main-2/.local-analysis/handoff-pcb-check-20261103/` | 本交接提示词、旧本机入口备份和最终核对 |

最近Run `run_0194a0579d38` 全部结算，收件箱0、reclaimable0：

| Task／Dispatch | 结果 |
| --- | --- |
| `task_2aa7abe3fe06`／`ctx_7564b49d7d1c` | CLI succeeded，3d21969，父正式验收通过 |
| `task_05ba117e9541`／`ctx_a63d2c848a4b` | 模型超时重试终止零工具，abandoned |
| 同Task／`ctx_c72daea3c24e` | 两槽取证后连接重试终止，abandoned；父明确Task failed |

主窗Pi会话 `01a19f99-6515-720c-9e03-ee00ab05152e`，writer／CLI `01a19f99-9252-74f7-9844-99633c12fe1f`，native `01a19f6a-a52d-7333-95f3-2972829f4e9f`，Qt QA `01a19fa1-5219-7342-9ee0-3e6eb23772b4`。核对实时空闲／工具状态，不改provider原记录，不向旧inbox追加业务。

目录名不等于分支：`fix-pcb-writer-boundaries`目前`feat/pcb-check-cli`，`native-startup-diagnosis`为`verify/native-guest-save-sample`，`verify-parallel-save-hardening`为同名verify分支。旧工作树先读 `.local-analysis/WORKTREE_CLEANUP_NOTICE.md`：部分旧verify目录是归档联接、无.git，仅只读证据，不能当开发树或删除。

新开发从最新dev独立分支，中文代码说明、界面、日志、文档及Conventional Commits；适当构建测试／GUI后no-ff合dev推送。main由用户处理，不强推、不跳钩子。原安装、库和用户板图只读，新隔离副本运行留摘要；pt／pt_install／.local-analysis／截图／SDK／build／数据库／会话均不提交，不git add-f。
