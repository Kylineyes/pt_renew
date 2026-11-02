# PT Renew 新代理交接：2026-11-02 并行核心开发及原软件现场之后

用户要求整理进度和下一步计划，再自行安排新 agent。本阶段到交接收尾为止，**不再启动开发、子任务或桌面控制**。新 agent 先读本页和 `AGENTS.md`，再根据选定任务读取对应文件；工作区与真实文件优先于历史会话。

## 当前状态与接手起点

整理前 `dev=origin/dev=222acbaa8fedf687613d6e0e83c8f52b057f7bff`，工作区干净。最近产品实现集成为 `c1195dbab933fd8db8ea158ed218279cc7a1a739`，此后 `222acba` 只增加现场报告和进度文档；产品源码、CMake 和测试没有变化。本交接在独立 `docs/handoff-track-preflight-native` 分支整理，再按项目规范 no-ff 合并并推送 dev。最终 SHA 与清洁状态见本机 `.local-analysis/handoff-track-preflight-native/final-state.json`，避免把文档中的整理前 SHA 当成最新 HEAD。

本地 main 仍为 `3e13f69528cfc033718ef8352b8d3fb7bce915bd`，本次 fetch 观察到远端 main 为 `cfb6a8893aaf8d8b5778a24c00fc97813c5f083d`。代理没有提交、合并或推送 main，没有创建 tag 或发布；main 的变化由用户管理。已发布 alpha 包不因本阶段核心开发自动更新，不能仅凭版本字符串猜功能。

新工作从最新 dev 建独立分支，完成构建／相应验收后合 dev 并推送；保留中文 Conventional Commits 和有意义的合并记录。用户明确要求尽可能并行，但必须独立修改：各 worker 使用独立工作树／分支／构建／证据目录，预先分配不重叠文件；共享 CMake、跨模块测试和最终集成由协调者维护，合并前核对实际文件交集。

## 用户能用到的产品能力

| 范围 | 当前已实现 | 准确边界 |
| --- | --- | --- |
| PCB 查看 | 支持已记录格式的严格载入、分层预览、选择／属性、元件定位、测量和端点捕捉 | 格式并非完整，文字及部分轮廓近似 |
| LIB／NET／铜分析 | 只读库浏览、引脚映射、受限几何连通分析 | 不是完整 DRC，不放置元件或输出生产文件 |
| 已有自由 FT 编辑 | 整数 mil 整线移动、删除、撤销重做、保存点与未保存保护 | 元件内和其他图元只读，宽度／层／附加字段不可改 |
| 受限另存为 | 将合法已有 FT 移动／删除保留原字节写到全新 PCB | 不覆盖输入或已存在目标，Ctrl+S 覆盖保存未开放 |
| 新增走线 | 只有内部核心及测试具备新增、预检、编码与提交控制 | 菜单／F3、画布取点／预览／统一取消未接入，writer 仍拒绝新增 |

详细用户行为见[编辑与另存为](pcb-save-as.md)。冻结 `sourceBytes` 是载入时原字节，保存不重新读原件；移动只补四坐标，删除只去对应记录，其他内容保持。另存成功标记历史保存点，不改原输入身份、不清撤销历史，主窗可能仍显示 INPUT；重新打开新文件才绑定新来源。外部 NET 不写进 PCB，原内嵌 NETDEF 逐字保留。目标文件沿用同目录临时写入、flush、不覆盖的原子改名保护。

## 已完成的新增走线内部模块

| 模块与代码入口 | 实际行为 | 接入注意 |
| --- | --- | --- |
| `src/domain/TrackIdentity.h`、`src/application/BoardEditSession.*` | 区分 Loaded／Created；载入身份按原标签行，新建按非零单调序号；支持 addTrack 及统一新增／移动／删除历史 | `PrimitiveId` 仍须文档／修订约束；新建不伪造来源、不复用废弃序号；`source.byteOffset=-1` 不是已知偏移 |
| `src/io/LegacyPcbReader.*`、`LegacyPcbLayout.h` | `parseWithLayout` 在严格解析路径记录 ENDPCB、完整顶层记录、DOS EOF、尾部 NETDEF 和换行事实 | 失败不返回局部布局；交错 NETDEF 无插入候选；语法候选不等于原软件已接受 |
| `src/application/TrackPlacementSession.*` | Idle／WaitingForStart／WaitingForEnd，纯临时几何、参数及文档上下文 | 预览不改文档／dirty／历史、不分配身份；`confirm` 成功会清空，新增 `prepareRequest` 保留有效预览 |
| `src/application/TrackPlacementController.*` | 引用编辑会话，取点／预览／提交检查文档指针、真实修订和目标层可见性；成功 addTrack 后才清预览 | 后端拒绝原样返回错误且保留有效预览；undo／redo 先取消；目前没有 UI 调用方 |
| `src/io/LegacyFreeTrackCodec.*` | 明确六／七字段、LF／CRLF的单 FT 内存编码，几何整数 mil 校验 | 默认 Unspecified 拒绝；七字段须显式附加整数，六字段禁止附加值；不选择原软件默认值、不写文件 |
| `src/io/LegacyTrackInsertionPlanner.*` | 验证 Created 顺序／身份／来源／几何；剥离新增后复用现 writer 得 baseBytes，再严格解析实际偏移及容量 | 删除释放实际容量；有新增时拒绝尾部／交错 NETDEF；无新增保留受限路径；不编码／拼接新 FT，不发布文件 |
| `tests/TrackPreflightWorkflowTests.cpp` | 串联控制器→预检→显式编码→内存重解析及撤销重做 | 候选仅在测试内存，明确断言原 writer 仍拒绝新增；不是原软件兼容证明 |

坐标限 ±1000000 mil，宽度为 1..1000000，新增铜层只接受 1／6，零长／小数／非有限值拒绝；显示网格不能隐含捕捉或取整。预检总记录数上限 200000，包括 COMP、ENDCOMP、元件内部图元和 ENDPCB，不能只看 tracks 数。显式编码器测试出现的附加整数只是合成参数，禁止当作原 FT 缺省值。

完整设计及模块接口分别见[新增走线设计](free-track-creation-design.md)、[身份历史](free-track-history-core.md)、[布局元数据](pcb-layout-analysis.md)、[放置状态](track-placement-session.md)、[提交控制器](track-placement-controller.md)、[显式编码器](free-track-explicit-codec.md)、[插入预检](track-insertion-plan.md)。两轮并行记录见[第一轮](parallel-track-foundations.md)、[第二轮](parallel-track-preflight.md)。这些基础已完成，不应重新派发同一实现。

## 构建与测试证据

最近产品源码 `c1195db`：Debug／Release 全量配置及构建均退出 0，CTest 各 **19/19**，QtTest 零失败零跳过。Debug 总计 **67.49 秒**，Release **8.97 秒**；原创建者持有 CTest 子进程，真实 wait 均为 0。之后现场和本交接只有文档变化，不重复构建或把旧测试说成新跑。

| 专项 | 每配置通过数，含初始化／清理 |
| --- | --- |
| 显式编码 `FreeTrackCodecTests` | 72 |
| 插入预检 `TrackInsertionPlanTests` | 72 |
| 提交控制 `TrackPlacementControllerTests` | 25 |
| 跨模块 `TrackPreflightWorkflowTests` | 8 |
| 布局／放置状态／新增历史 | 40／11／28 |
| 原写出／原编辑 | 40／23 |

新增模块为 Qt Core／Qt Test；现有 UI 回归用 `QT_QPA_PLATFORM=offscreen`，不能代替真实产品交互。插入预检覆盖真实大板记录边界，CTest 预算 180 秒，其他新专项 30 秒；不要用 60 秒工具超时中断整个 CTest 再据半截日志报告通过。

现有环境 Qt 6.12.0／MSVC x64／Ninja，SDK 在 `C:/Users/rikideng/Qt/6.12.0/msvc2022_64`，详见[环境文档](qt-development.md)。可用 PowerShell：

```powershell
& './scripts/Enter-QtEnv.ps1'
cmake --preset debug
cmake --build --preset debug --parallel 3
$env:QT_QPA_PLATFORM='offscreen'
ctest --preset debug --parallel 2
```

Release 使用对应预设。并行构建使用不同目录，限制并发编译；长测试可参考父 `.local-analysis/track-preflight-wave/run_ctest.py` 的独立运行器及 `ctest-*-exit.json`。不需安装 Vulkan、WebEngine 或其他无关依赖。GUI 变更须实际启动交互并由指定模型截图验收。

## 原生文件流程与旧缺口

[原生另存重开报告](native-save-roundtrip-verification.md)已通过独立产品 Windows 原生另存框、新文件重开和正常退出：5 条 FT、180 字节，输出与既有输入逐字相同。输入是产品核心此前生成的样例，当轮没有新编辑，所以**不能替代 dirty 编辑→原生保存→精确重开完整闭环，也不能证明原 AUTOTRAX 兼容**。

以前产品实际键鼠完成选线、位移、保存取消与关闭取消，但该 dirty 会话没有保存；已有目标 GUI 测试停在原生文件名无效，不等于后端已有目标拒绝经过真实 GUI 验收。详见[产品键鼠报告](product-mouse-keyboard-verification.md)。原字形 runtime、异步实验 ready_for_live、NET／铜竞争、极端坐标和干净机器运行等旧边界照旧，不能被本阶段新增核心或现场观察覆盖。

## 最新桌面现场：有进展但任务 failed

[单线现场报告](native-ft-sample-verification.md)为目前权威结果。用户已明确允许电脑操作；本次单一 worker 的现场时段为北京时间 **04:09:30–04:24:30**，后两分钟收尾。**现场已结束，用户已被告知可恢复使用电脑；不再有本轮待控制的窗口。**

已取得：指定 Pi `deng/gpt-6.1-sol high` 实际看清 AUTOTRAX 1.57 启动页、VGA640×480提示、红色外框／内部水平线及主菜单。stderr 明确记录本轮配置加载和隔离工作目录；独立日志记录 OpenGL 4.6 NVIDIA 617.42、pt.EXE、GRAPH.DRV／菜单等及 SYN1.PCB 打开请求。没有证明额外配置继承不存在，也没有定位旧黑底白线根因。本轮已有可辨画面，后续不要再把黑屏当成当前唯一阻塞。

未完成：`f` 无预期 File 变化，预期 File 点击 `(120,270)` 实际进入 **BLOCK**，Esc 退出；`i` 后未出现可辨 Information。未确认工作文件名、走线计数、空板，没有放置或保存，`NEWFT.PCB` 不存在。菜单选择问题的坐标、DOS 鼠标映射、键盘规则及输入时序原因尚未定位，不能凭一次误选断言根因。

实际 1 新服务／1 新 DOSBox、2 App／2 Click／5 Shortcut／0 Type、11 张原图；每张有该模型实际原 read 的成功 image 回执，解码 SHA 匹配，读取早于下一步输入。父只核对原回执和字节，不冒称父直接看图。原安装 99 项、冻结输入及运行副本 99 项完整集合／大小／SHA 前后一致。

目标 PID26968、birth **134380374573781027**、HWND396742、原 Popen identity2138986497680／handle592，于 **04:23:26.781083** 原创建者真实 wait 0；控制服务 PID5064、birth **134380374260787376**、identity2138985622096／handle532，于 **04:26:30.351991** 原 Popen wait 0。FILETIME 用原 JSON 文本／Python int 或字符串保存，JS Number 会丢精度。runner-finished 仅完成标记，不是 runner 自身 OS 退出码。

Stop 于04:24:46写入，晚于04:24:30硬截止，未消费；冻结驱动按截止路径完成120秒零桌面请求后关闭服务。不是公共门拒绝，不能把 Stop 改称成功。最终 task failed 已父接受，准确保留了样例未完成的结果及分项证据。

## 建议下一步顺序

1. **先解决可预测菜单选择。** 只读复核最新截图、capture-scope、窗口矩形、实际请求与原菜单／按键资料。截图交给指定模型看；纯二进制逆向交指定 GLM，模型不可用则保留阻塞。核对裁剪图原点到物理桌面坐标的换算、DPI、客体鼠标及菜单规则，区分有证据结论与假设。下次真实窗口先只确认 File／Information 的可靠进入和返回、工作文件名与计数；不要预排多步按键或再次把其他菜单当成 File。
2. **取得原软件生成的单线样例。** 在菜单可靠后，用全新隔离副本和经确认空板，明确层／宽／端点，新建一段，另存不存在的8.3文件名，再由原软件重开并核对。保留操作前后原字节、用户选择参数与默认属性，确认六／七字段、附加值、换行及实际记录布局。一个样例不能自动开放尾部 NETDEF 排序或全部层。
3. **依据已核定编码接入新增写出。** 复用现有预检／编码器，完成整体输出64MiB等大小限制、重新解析及新旧对象／NETDEF语义复核、明确的新建身份到重载身份比较、保存点及文件发布保护。首版有新增仍可拒绝 NETDEF，除非取得专门兼容证据。不得仅删除 writer 的新增拒绝条件。
4. **接入产品工具与实际验收。** 参数／画布起终点预览、明确整数 mil、选择／测量互斥、统一取消菜单与画布 Esc、Undo／Redo先取消、换图／模态框／隐藏目标层取消；菜单与 F3／旧式 P→T 共享模型且不抢文本输入。提交后用 `MainWindow::publishWorkingDocument` 失效旧选择／测量／铜结论，外部NET重映射及迟到回调继续受身份／代次约束。最后验证新增→取消下一段→撤销重做→Windows原生另存重开→原软件重开→正常退出。

如果用户优先要求产品进展，可并行推进不开放入口的输出复核或参数／预览内部模块，但先给出明确接口及不重叠文件所有权；不要增加又一层没有消费者的通用框架。当前最紧要的是原软件菜单交互与保存样例，不应重新从控制基础设施、布局解析或历史模型开始。

## 并发、模型与桌面操作约束

用户要求能并发就并发，并在需要控制电脑时告知。既有电脑操作授权已明确，但新现场仍应先通知目标窗口／进程、具体时间和预算，避免占用用户桌面不知情；这不是每次重复询问许可。本次只整理交接，不再开现场。实际桌面只能一个 worker 操作，其他 agent 不抢焦点。

按 `AGENTS.md` 全部子 agent 用 Pi，明确指定模型及 high，并核对实际原会话模型事件、assistant 和工具结果；纯逆向 `glm-5.3 high`，截图任务／验收 `gpt-6.1-sol high`。GLM 前次 quota hard fail、零工具调用，未换模型也未形成字段结论，不循环重试追结果。

本机 Orca 1.4.244 的 `worker-start --agent pi --model ...` 曾参数拒绝；可参考两轮已验证方式：Orca建立工作树和专用终端，显式 `pi --model deng/gpt-6.1-sol --thinking high`，再 `worker-start --terminal`。同一任务沿用现有Pi会话；旧 settled Dispatch 不能复用，新任务须新ID。先读实时技能及CLI帮助，不假设版本不变。不用 terminal send 代替结构化任务跟踪；结算须审阅真实结果、release／再派发后ack，保留 external 终端实际无进程动作的事实。

最新现场 Run `run_bcac7af517bf`／Task `task_3f5dcfa2d53c`／Dispatch `ctx_63390a1027f7` 已 failed结算；done `msg_bcd12821afcf` 已接受、ack `delivery_b3128695fd5b`，release `retained/external_terminal/processAction=none`，无 reclaimable、收件箱空。此前开发Run `run_983a7a1c8e88`三项均completed并结算。不要恢复已停止的driver／控制服务或向旧inbox补动作。

## 本机证据与工作树

| 位置，相对当前主工作树 | 用途 |
| --- | --- |
| `.local-analysis/track-preflight-wave/` | 第二轮三任务spec、原会话只读审计、Debug／Release构建日志、CTest日志和真实退出回执、final-state |
| `.local-analysis/parallel-track-wave/` | 第一轮布局／状态及GLM失败结算 |
| `.local-analysis/native-ft-sample-parent/` | 最新现场父spec／GO副本、精确原文件和image审计、final-state／结算回执；以 `parent-*-final-audit.json` 为终态 |
| `../feat-pcb-layout-boundaries/.local-analysis/native-ft-sample/` | 原创建者／服务、11图、原RPC、逐步read-review、原会话前缀、输入／runtime／日志、REPORT和audit-after |
| 同工作树 `.local-analysis/free-track-codec/`、`.local-analysis/pcb-layout/` | 编码器和布局独立专项证据 |
| `../feat-track-placement-state/.local-analysis/track-placement-controller/`、`track-placement/` | 提交控制器及状态专项证据 |
| `../feat-track-insertion-plan/.local-analysis/track-insertion-plan/` | 预检边界、失败／中断和最终72项完整通过记录 |
| `.local-analysis/handoff-track-preflight-native/` | 本交接快照、最终Git状态和 `NEW_AGENT_PROMPT.txt` |

当前有效 Git 工作树为本 `main-2`、原 `D:/project/pt_renew`，以及 `feat-pcb-layout-boundaries`（实际分支verify/native-ft-sample-worker）、`feat-track-placement-state`（feat/track-placement-controller）、`feat-track-insertion-plan`、`research-ft-static-wave`。目录名不等于当前分支，先核对状态和活会话；不要为整理交接清理这些目录。

先读 `.local-analysis/WORKTREE_CLEANUP_NOTICE.md`。旧 `verify-pcb-legacy-native`、`verify-product-mouse-keyboard` 等六个目录现为指向 `C:/Users/rikideng/orca/worktree-archives/pt_renew/20261102-cleanup/` 的目录联接，旧证据仍可读但没有 `.git`，不是可开发工作树。更早归档见同通知；不删除联接／归档或改写旧报告。

原安装 `D:/project/pt_renew/pt` 始终只读，运行／写盘用新隔离副本并留前后完整摘要。原安装、介质、库、用户板图、截图、SDK、构建和反编译数据库不提交，不用 `git add -f`。现场已取证并正常退出，接手无需关闭旧PID或清理目标。新增真实窗口前核对当前状态，不把历史PID当成仍存活的目标。
