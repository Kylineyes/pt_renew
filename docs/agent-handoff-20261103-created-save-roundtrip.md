# PT Renew 新会话交接：2026-11-03 主窗显式新增另存闭环之后

本次只整理进度与计划，由用户自行安排新会话接手；整理者不启动新开发、子任务或桌面现场。接手者先读 `AGENTS.md` 和本页，再按目标读取对应材料。工作区、Git 和原始证据优先于历史会话中的进度陈述。

## 基线与用户实际能用的能力

整理前已推送基线为 `dev=origin/dev=远端dev=2f77ca113c6fec5fa3e462d1f5932d1a859fd90e`，工作区干净。本交接在 `docs/handoff-created-save-20261103` 独立分支编写，再按项目规范 no-ff 合 dev 并推送。交接后的最终 SHA 见本机 `.local-analysis/handoff-created-save-20261103/final-state.json`，不要把整理前 SHA 当作最终 HEAD。

最近产品源码及正式测试冻结提交为 `64e36d8e634f517fa86cb4b0266ace52911c5b56`，后续到本交接只有报告、说明和合并，`src/`、`tests/`、根 CMake 与预设无 Git 内容差异。当前本地 main 仍为 `3e13f69528cfc033718ef8352b8d3fb7bce915bd`；代理未提交、合并或推送 main，没有新 tag 或发布。已发布安装包不能因本次源码进展自动视为更新。

| 范围 | 当前结果 | 边界 |
| --- | --- | --- |
| PCB／LIB／NET 查看 | 已有严格载入、分层预览、选择属性、定位、测量和受限铜连通分析 | 格式未完整；文字和部分轮廓近似；不是完整 DRC |
| 已有自由 FT 编辑 | 整数 mil 整线移动、删除、撤销重做、保存点和未保存保护 | 元件内图元及其他类型只读，宽／层／附加字段不可改 |
| 普通产品另存 | 合法已有 FT 移动／删除可保留原字节另存全新 PCB | 不覆盖输入或已有目标；Ctrl+S 覆盖保存未开放 |
| 新增走线内部路径 | 身份历史、布局、状态、控制器、编码、插入预检、显式 writer、画布及主窗显式保存均已接通并测试 | 编码必须由内部调用者明确指定，尚无原软件默认值 |
| 普通用户新增入口 | `trackPlacementUserEntryAvailable()` 仍返回 `false` | 菜单／F3／旧式 P→T 继续未实现／禁用；默认主窗／writer 保存仍拒绝 Created |

**当前最重要的区别是：诊断宿主中的内部显式新增保存闭环已通过；普通产品新增命令及原 AUTOTRAX 兼容仍未开放／未证明。** 不要重新派发已完成核心，也不要仅删除 writer 拒绝条件或翻转能力门。

## 代码入口与已完成设计

| 入口 | 接手时需要知道的职责 |
| --- | --- |
| `src/domain/TrackIdentity.h`、`src/application/BoardEditSession.*` | Loaded 按来源标签行，Created 按非零单调序号；新增／移动／删除共用历史；撤销分支不复用废弃身份 |
| `src/io/LegacyPcbReader.*`、`LegacyPcbLayout.h` | `parseWithLayout` 严格记录顶层记录、ENDPCB、DOS EOF 和 NETDEF 布局，失败不返回局部候选 |
| `src/application/TrackPlacementSession.*`、`TrackPlacementController.*` | 临时预览不 dirty、不分配身份；检查文档指针／修订／层可见性；后端失败保留有效预览，成功后才清空 |
| `src/io/LegacyFreeTrackCodec.*` | 六／七字段、LF／CRLF 和可选附加整数须显式指定，不选择默认参数 |
| `src/io/LegacyTrackInsertionPlanner.*` | 剥离新增后调用默认 writer 复核旧编辑，在编辑后的真实字节上获取语法位置和容量；新增仍拒绝尾部／交错 NETDEF |
| `src/io/LegacyPcbWriter.*` | `prepareWithCreated`／`saveAsWithCreated` 组合预检、编码、整体大小／语义／重载身份复核及新文件发布；默认 `prepare`／`saveAs` 仍拒绝 Created |
| `src/ui/BoardCanvas.*`、`MainWindow.*` | 主窗实际消费放置控制器；画布只绘临时覆盖层；整数面板明确坐标再提交；共享取消并保留旧交互语义 |
| `MainWindow::saveAsFileWithCreated(path, options, error)` | 本轮完成的内部显式入口；与默认 `saveAsFile` 共用 `saveAsFileImpl`，只有真实发布成功才 `markSaved()` 并更新最近输出 |
| `src/application/CommandCatalog.*` | 单一能力门继续 false；菜单／快捷键共用命令模型，不通过隐蔽命令行或配置开关开放 |

已有移动只替换四坐标词，删除只移除对应原记录，其他字节、旧附加属性、混合换行、非 ASCII 文字、ENDPCB 尾部和 DOS EOF 保留。冻结 `sourceBytes` 不重读可能外部变化的原路径。新增按创建顺序插入严格确认的无 NETDEF 顶层 ENDPCB 前；记录总量不超过 200000（含 COMP／ENDCOMP／内部记录／ENDPCB），整体输出不超过 64 MiB。端点为 ±1000000 mil 内有限整数，宽 1..1000000，新增层目前限 1／6，零长拒绝；网格不隐含捕捉或取整。

显式七字段附加值属于输出投影，不反写 `Created.extra`，不解释电气语义。重开输出后按新文件行建立 Loaded 身份。另存成功只标记当前位置保存点，不改原输入身份、不清历史；撤销离开保存点 dirty、重做回保存点 clean。主窗文件框现在还核对 document／original 指针、revision、loadGeneration 及 loading，防止失败载入不改变修订时旧文件框仍发布。

详见[本轮集成](parallel-mainwindow-created-save.md)、[主窗显式保存](mainwindow-created-save.md)、[显式输出](track-explicit-output.md)、[界面接入](track-placement-ui.md)与[新增设计](free-track-creation-design.md)。旧说明中的“待父验收”属于其实现提交当时状态，最新结果以本页及现场最终报告为准。

## 构建与自动化证据

最近正式 Debug／Release 的配置、全量构建、CTest 均由原创建者记录真实 wait=0，CTest 各 **23/23 组通过**。Debug CTest 原进程耗时 **227.75 秒**，Release **25.96 秒**；此后文档交接不重新跑或冒称新跑。

| 专项 | QtTest 通过项，含初始化／清理 |
| --- | ---: |
| `MainWindowCreatedSaveTests` | 31 |
| 更新后的 `TrackCreatedWorkflowTests` | 5 |
| `TrackCreatedWritingTests` | 67 |
| `TrackPlacementUiTests` | 13 |

本轮跨模块测试真正经过主窗显式保存，覆盖新增→取消下一段→发布后 clean→撤销 dirty／重做 clean→已有目标拒绝不改变保存点→重开 Loaded 身份与输入字节保持；没有用直接 writer 加手动 `markSaved()` 冒充主窗。旧 Writing、Library、Editing 等全量回归通过。worker 独立 harness 首轮 Library 漏部署相邻检查工具，失败 wait1 记录保留；只修忽略目录部署，未改旧测试掩盖。

环境仍是 Qt 6.12.0／MSVC x64／Ninja，SDK `C:/Users/rikideng/Qt/6.12.0/msvc2022_64`，详见[开发环境](qt-development.md)。常用命令：

```powershell
& './scripts/Enter-QtEnv.ps1'
cmake --preset debug
cmake --build --preset debug --parallel 3
$env:QT_QPA_PLATFORM='offscreen'
ctest --preset debug --parallel 2
```

Release 对应预设。writer 真实容量／64 MiB 专项 Debug 需较长预算，正式超时300秒，预检180秒。避免60秒工具超时中断整个测试；父 `.local-analysis/save-roundtrip-wave/run_checks.py` 可参考原创建者逐步 wait 与独立日志方式。不要安装无关 Vulkan、WebEngine 或 Creator。GUI 修改仍须真实交互，offscreen 不替代现场。

## 最新真实窗口：指定核心范围 succeeded

[主窗现场报告](mainwindow-created-save-live.md)是最新权威结果，报告提交 `94a4c8d`。使用 `64e36d8` 的精确源码快照构建诊断宿主，明确标注“六字段／LF合成编码；产品新增未开放”，调用真实 MainWindow API，没有修改产品入口。

已取得真实交互与实际看图：

1. 整数 `(200,250) → (800,550)`、宽17 mil、层6，新增后3图元 dirty，取消下一段不新增。
2. Windows 真正原生另存框发布90字节新 `DIAGNOSTIC-CREATED.PCB`，保存后3图元 clean；菜单 Undo 后2图元 dirty，Redo 后3图元 clean。
3. 未提交预览时隐藏目标层，预览取消且仍3图元 clean；恢复层后原已保存走线重现。
4. 追加新进程实际打开输出，标题和来源为输出文件、90字节、3图元 clean；Loaded 身份2／4／6，无撤销重做历史。
5. 等待起点时打开编辑菜单；前两次显式窗口ID Escape 定位失败，最终以精确 app PID 的 Escape 成功，读图为菜单关闭、Idle、无待提交预览、3图元 clean。

24张原PNG均匹配RPC并有指定模型成功image回执。父独立复核126个源码／测试／CMake文件与冻结内容一致；输出只比66字节合成输入在ENDPCB前多一条显式FT，其他字节保持。输入SHA `26424e685617887aa7573434c338d8b8ebc7c4cdb0131b1ad03b27583148a4a5`；输出SHA `57892d56b1698d7f0d28d340881e3be2e3ccd8350ccece819478e0e095da9224`。

失败及更正保留：首轮文件名输入受焦点／modal定位限制，最终使用原生框已确认不存在的默认新文件名；首轮因连接重试超过延长18:55截止，父核对PID31364／birth `134380865164826143`、dirty=false后19:02:38正常 `CloseMainWindow`，原owner wait0／forced=false，不能说worker按时自行关闭。父曾误称首轮已重开，已更正；`n31-start-cancel-test`不是重开，只有追加进程19508才是实际重开。追加进程20:45:18正常wait0／forced=false，早于20:53收尾。大图read会缩放；本轮小图可直接核对image字节，不能泛化历史缩图SHA相等。

F3、完整文本输入等旧现场缺口，以及普通产品正式新增菜单和原 AUTOTRAX 兼容，不在本次通过范围内。诊断宿主通过不能提升为产品新增已开放。

## 原软件与纯逆向：仍有阻塞

[最新原软件重试](native-created-retry.md)比上一轮前进之处是**两个实例均实际请求一次 Return**，不再是零客体输入的计划。OpenGL 首图与Return后仍黑底白横线；仅将输出改为surface的单变量对照显示DOSBox启动说明／挂载文本，Return前后和各自物理屏幕图均不变，日志均无SYN1打开记录。主机API返回pressKey成功／synthetic不等于DOS客体已处理物理键；两种输出不同表象不定位根因。

两个新隔离运行副本各99项、原安装99项及冻结输入集合／大小／SHA前后不变；六张662×566原图分别实际read并匹配回执。两个目标均原Popen正常wait0／forced=false，未进入可靠菜单、未确认空板、未新增或保存，FTNEW不存在，六／七字段、附加值、换行、排序及默认值仍未知。旧[可辨启动页与主菜单](native-ft-sample-verification.md)的事实仍有效，本轮不覆盖其历史，也不能宣称旧黑屏根因已修复。

纯静态逆向指定 `glm/glm-5.3 high` 再次 quota hard fail，自动重试后结束，**零工具、零逆向结论**。协调者依据原会话最终错误记录将该attempt abandon、Task failed，processAction=none；没有换模型、循环重派或生成伪造报告。后续模型仍不可用时如实保留静态研究阻塞，不能让截图模型代做纯逆向。

原安装 `D:/project/pt_renew/pt` 始终只读；运行只使用新副本，原件不挂载。相关文件与截图不可提交或重新分发。

## 接下来建议顺序与并行安排

1. **先定向解释原软件启动与输入阻塞。** 复用旧可辨现场和最新两槽日志，列出已证事实与单一假设；检查启动配置继承、图形驱动初始化、客体输入送达及PT进入文件载入之前的状态。Return已试、surface已试，不重复同一无结果组合；不要继续仅截图黑图后停止，也不盲目预排编辑／保存。纯二进制分析只由指定GLM；若不可用，将其报告为依赖阻塞。看图与必要新现场交指定GPT，针对具体假设做最小试验。
2. **完成真实原软件样例。** 可辨后先可靠进入／退出File、Information／Status，确认工作文件名和计数；再确认空板，明确层／宽／端点，新建一段，以不存在8.3文件名保存并由原软件重开。保留原字节、参数、截图、日志与前后摘要，核定六／七字段、附加值、换行和布局；一个层的样例不证明全部层或NETDEF排序。
3. **依据字段证据开放产品。** 复用已完成codec／planner／writer／主窗显式路径，选择有证据的默认输出策略，再连接普通产品保存和单一能力门。不要新增又一层无消费者抽象，不只翻转门或删除拒绝条件。新增NETDEF首版继续拒绝，除非有专门证据。
4. **普通产品最终验收。** 真正菜单／F3／旧式P→T进入同一命令；文本框不抢按键、整数取点、预览取消、隐藏层／模态／换图取消、撤销重做、原生另存新文件与重开，并将产品输出交原AUTOTRAX重开核对旧对象／新段／计数，最后正常退出。现有诊断已证项目可复用证据，不必从零重复。

适合两至三路：一名GPT独占原软件现场；一名GLM纯静态定向研究（可用时）；一名源码开发者根据已确定接口补具体产品接入，尚无格式证据时可做代码审查和离线准备但不开放入口。独立分支／工作树／构建／证据，文件所有权不重叠；共享CMake、跨模块测试与最终合并由协调者掌握。不要为凑并行重复现有模块。现场与产品验收串行交桌面，不同时抢焦点。

## 模型、桌面与生命周期

按 `AGENTS.md`：所有子代理用Pi，启动明确模型与high，核对实际model／thinking、assistant和成功工具；纯逆向`glm-5.3 high`，看图和截图验收`gpt-6.1-sol high`，不可用不擅自替换。同一未完任务沿用Pi会话，已结算Task不能复用旧Dispatch。用户要求能并行则独立推进并由协调者验收。

用户已多次明确允许直接键鼠；授权持续有效，**新现场先通知目标窗口、当前具体时段与预算，无需重复问同一许可**。时间必须基于当前时钟，不能继续历史时段。只一名操作者，业务检查点先处理／ack所有父消息；有新延时指令保留原GO，记录新授权。不要依赖固定截止强杀，至少提前留7分钟收尾，保留原创建者Popen/HANDLE及真实wait。连接超时会消耗预算，安全无活目标时可压缩同会话减少延迟。现有控制脚本已够用，不再从通用框架起步。

Orca 1.4.244曾拒绝Pi启动时`--model`，已验证流程是Orca工作树／专用终端显式 `pi --model deng/gpt-6.1-sol --thinking high`，然后`worker-start --terminal`；GLM实际provider为glm。接手先读实时orchestration／orca-cli技能和CLI help，不假定版本不变。`set-value`可避免部分键盘焦点问题，菜单popup HWND会变化，避免复用过期索引；F3在旧Orca控制接口Unsupported不是产品失败，不循环同参重试。

最近Run `run_ba2b6ac49c4a` 已全部结算：

| Task／Dispatch | 结果 |
| --- | --- |
| `task_4d5aa9b763e6`／`ctx_4ed6d5bf848e` | 主窗实现 succeeded，提交8a4c390 |
| `task_c97906c5400d`／`ctx_db8126806671` | 原软件样例 failed，报告e607ad8 |
| `task_b84d052d1e94`／`ctx_92006b122453` | 静态quota失败，failed／abandoned，零工具 |
| `task_ecdc9a63dfe3`／`ctx_a91aa16f3171` | 指定GUI核心范围 succeeded，报告94a4c8d |

收件箱空，reclaimable为空；worker-release实际为retained／external_terminal／processAction none，**不表示Pi OS退出**。全部现场目标已结束，用户已被告知可正常用电脑；不要关闭历史PID、恢复旧driver／service或向旧inbox追加业务。新工作用新Task，先观察实时会话是否空闲。

## 本机证据与工作树

父当前工作树为 `C:/Users/rikideng/orca/workspaces/pt_renew/main-2`，下列未跟踪材料只在本机，跨机器接手需另行取得，不能因Git里没有就断言未完成。

| 路径 | 内容 |
| --- | --- |
| `.local-analysis/save-roundtrip-wave/` | 本轮spec、模型原事件、Debug／Release构建／CTest日志与真实wait、父原软件／源码／输出／image审计、父正常关闭回执、原最终Git／结算状态 |
| `../feat-track-placement-ui/.local-analysis/mainwindow-explicit-save/` | 主窗实现专项、harness、初次部署失败和最终通过原日志 |
| 同树 `.local-analysis/mainwindow-created-save-live/` | 341文件冻结快照、诊断源码／exe、24图原RPC／image回执、两进程原Popen退出、66字节输入及90字节输出、最终审计 |
| `../verify-native-menu-calibration/.local-analysis/native-created-retry/` 及 `surface/` | 两槽Return、软件输出对照、六图、日志、原安装／运行副本／输入前后完整摘要与wait |
| `.local-analysis/track-native-wave/` | 上阶段22/22和显式writer／UI首次集成及失败／修复记录 |
| `.local-analysis/handoff-created-save-20261103/` | 本次交接提示词、旧本机入口备份、最终状态 |

原Pi会话：UI `01a19a2e-36c1-7793-8cc2-3f7677a76600`；native `01a19a20-d1f1-761b-8916-078f4c28b7ef`；GLM `01a1986f-2a58-7787-a72a-1993d6d10356`。会话只读审计，勿改写原provider文件或制造回执。

实际有效工作树仍包括 main-2、D:/project/pt_renew、feat-pcb-layout-boundaries、feat-track-explicit-output、feat-track-insertion-plan、feat-track-placement-state、feat-track-placement-ui、research-ft-static-wave、verify-native-menu-calibration。其中目录名不等于分支：UI目前`feat/mainwindow-explicit-save`、native为`verify/native-created-retry`、静态为`research/startup-ft-save-path`。先核对实时状态，不为交接清理。

先读 `.local-analysis/WORKTREE_CLEANUP_NOTICE.md`：verify-pcb-legacy-native等旧目录已是指向 `C:/Users/rikideng/orca/worktree-archives/pt_renew/` 的归档联接，无.git，只读证据，不能当开发工作树；勿删除联接／归档。原安装pt／介质pt_install、库／用户文件、截图、SDK、构建及反编译数据库不得提交，不用git add -f。

新开发从最新dev建独立分支，中文Conventional Commits，通过相应构建／验收后no-ff合dev并推送；main合并由用户执行。接手者应保留所有未验证边界，阶段性说明应从本页最新事实出发，而不是把早期failed或“待验收”误作当前结论。
