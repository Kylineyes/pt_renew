# 会话交接：控制恢复与独立异步实验验收

更新时间：2026-10-27。先读本机临时`.local-analysis/NEXT_AGENT_BRIEF.md`、[AGENTS.md](AGENTS.md)，临时文档最新事实优先于本文历史记录。稳定产品保持0.10.0，不合入0.11.0实现、不替换发布包、不操作main。

## 最新：原连接已恢复并正常退出

用户实际轻按松开反引号键后，同一原连接诊断`cr120-003-after-physical-key`成功；随后显式resume旧failed并正常stop。客户端50048、服务40648及其关联36396/20036/17396/31708共六个原精确身份均由停止前持有的查询句柄确认exit0，无强制终止。PID2020此前已按用户指令结束并退役，不能恢复。VK192残留曾有直接只读取证，本次恢复依据原Guard实际成功检查，没有重新读取键集合，也没有修改第三方安装或声称完整事件链已修复。详见[控制恢复报告](docs/desktop-control-recovery.md)。下文“原连接仍拒绝／候选仍存”为历史状态。

新Run `run_021d6c33debf`、Task `task_cc0acf5789a3`、Dispatch `ctx_2f2d4d1f3ae1`已向保留Pi会话`01a1739a-82f6-76cf-9ffc-c63e95be56d4`派发，沿用`deng/gpt-6.1-sol high`。新分支`verify/async-gui-recovered-120`、新证据`.local-analysis/async-gui-recovered-120/`；先在新副本适配120秒并定向验证、冻结和审阅后，才启动NET／铜层对照与竞争。旧180秒实例已经退出，不能冒称旧代码适配完成；三个旧已结算生命周期不复用。当前这里只记录派发与准备，尚无新GUI通过结论。

## 最新再次接管：原连接仍拒绝键鼠

用户再次明确“你操作电脑进行验收”。本次新Run `run_4b8adf1b5599`、Task `task_92f676d5e13d`、Dispatch `ctx_7072599ead1b`，仍使用原Pi会话及`deng/gpt-6.1-sol high`，分支`verify/async-experiment-resume`，新证据`.local-analysis/async-experiment-resume/`。用户键鼠授权充分，阻塞来自真实ControlStatus，不应要求重复授权。

已核对7个残留进程的创建时间、空inbox及busy=false、28冻结文件摘要和到期截止。父`msg_b2296d95525c`批准新任务接管原连接：旧空inbox归档，旧路径junction指向新目录inbox；新请求携本次Task/Dispatch及r-唯一步骤ID，原client50048/MCP、candidate2020、failed/token/seen/截止全部保留，没有热改源码或重连。连续运行追加事件属本轮明确接管，不覆盖原静态证据。

本次三次到期诊断均user（generation44）；第三次由隐藏pythonw静置15秒后提交，仍拒绝（wait约9.91秒），不能把活动归因用户或认定辅助终端是根因。没有发送键鼠/截图/原生窗口请求，没有启动新候选、没有正常清理。最后截止`691127.2648819`，原失败锁存仍为`a009-net-control-segment`；已停止本次后续自动桌面计划。未来恢复先核对当前新inbox通道及adoption记录，禁止向已结算任务续投、重连清门禁或用其他输入入口绕过。[接管续验报告](docs/async-experiment-resume.md)提交`76f8089744546ef3c3808da3e690f2367676eba5`，唯一worker_done failed=`msg_4d69effa69b4`已接受/ack，终端retain。本轮25项证据及10个报告本地链接核验通过；七个原身份仍存，没有清理成功记录。以下保留上轮现场及精确残留身份。

## 上轮现场：受控阻塞，存在未退出进程

用户已明确授权“进行下一步，键盘鼠标交给你”，本轮无需重复索取授权。已建立全新Run `run_de333c61159e`、Task `task_173ed3eebb79`、Dispatch `ctx_f4aea03b6bef`，沿用截图Pi会话`01a1739a-82f6-76cf-9ffc-c63e95be56d4`，实际环境/JSONL均为`deng/gpt-6.1-sol high`。截图工作区分支`verify/async-experiment-gui`，新证据`.local-analysis/async-experiment-gui/`；父证据为主工作区`.local-analysis/async-experiment-gui-parent/`。

离线驱动最终82/82项通过（含既有61项），父独立复验相同82项并冻结28个源码/配置文件，PowerShell包装解析通过。已绑定新批准`msg_d8e9399a8547`，未复用旧批准或旧任务。实验候选仍为SHA `782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`。

现场实际只启动NET对照：初次非目标前景被阻止，完整退让后专用恢复成功；取得三张有效截图，确认实验标记、合成board/NET_A、1条走线及未修改修订2，再打开原生NET框并读图确认本轮隔离`b.net`路径。关键段提交前`ControlStatus=user`，触发点击`executed=false`，没有B读取请求或门闩。该次中止并消费机会，NET竞争未进入；后续三次到期只读复查仍user，铜层未启动。没有新增迟到结果通过项，也未发现产品淘汰缺陷。

**存在残留：候选PID2020、创建FILETIME134374989405547867；持有者/client PID50048、创建134374989304233763，以及本链其余PID17396/20036/36396/40648仍存，正常关闭未完成。** 失败锁存`a009-net-control-segment`，最后截止`not_before_monotonic=686259.8917363`，busy=false。已明确停止所有后续桌面计划，客户端仅本地inbox空闲，不预排GUI；未强关、未换入口、未重连。不得写成已清理或退出码0。未来恢复须新任务并先核对这些身份/控制状态和生命周期归属，不向已结算旧inbox续投，也不删除live-state清门禁。

父独立核验实验部署22/来源输入3/原固定部署23/原来源输入7/稳定dist22文件集合、大小、SHA前后不变；Guard已持久化90事件/35请求没有提前越过180秒，3张PNG文件头有效；应用仅1运行、无gated请求，未记录run-stopped。[现场报告](docs/async-experiment-gui-acceptance.md)提交`dc77c16334cdc120fe287272f37585e13f7c3e56`；唯一`worker_done failed`回执`msg_3b99780f753e`已接受，终端已明确retain，交付已ack，无待回收工作者终端。父独立审计239项索引文件/3张PNG/12个本地链接有效；额外启动包装进程31708的存活/创建时间也单独记录。稳定源码和dist保持0.10.0，实验源码仍独立，main未操作。

## 上一阶段开发：独立异步实验构建

用户要求进行开发，并在操控鼠标键盘前先告知。已在新隔离工作区`C:/Users/rikideng/orca/workspaces/pt_renew/experiment-async-result-barrier`、分支`experiment/async-result-barrier`完成门闩与时间线实现；代码提交`98a4321`，报告提交`c4e3ec5`，实验分支已推送。该分支从固定编辑候选`b0e5ac7`建立，**不得整体合入稳定dev**。本次dev只集成[实验开发报告](docs/async-experiment-development.md)及进度说明。

开关`PT_ENABLE_ASYNC_EXPERIMENT`默认关闭；开启后只为显式配置的新运行提供单次后台门闩、请求/修订/线程/结果事件、60秒看门狗与持有者退出/取消处理。NET在成功打开副本后读取前等待，铜层在算法预算计时前等待；原代次和身份淘汰条件保留。Python控制器按PID与创建时间核对专用命名事件，不发送桌面输入。

Debug/Release实验各12/12组CTest通过，新实验QtTest每配置12 passed（包含初始化/清理，已含于CTest）；普通开关OFF的Release编辑/NET/铜层3/3组通过。两个配置共8条自动对照/竞争时间线确认工作线程进入后，程序接口编辑先发布新修订，再释放、返回旧结果并由原条件丢弃。测试仅offscreen，不是实际鼠标键盘或固定候选现场证据。

独立Release部署`.local-analysis/async-experiment/release-candidate/pt-renew.exe`共22文件，EXE SHA`782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`。新证据在实验工作区`.local-analysis/async-experiment/`，含逐例事件、输入、副本摘要、构建/测试日志和交付核验。原固定部署23、源输入7、既有隔离输入7、稳定dist22文件集合/大小/SHA与前轮基线一致。

没有派发子代理或创建/复用旧Task/Dispatch，没有鼠标键盘或真实GUI请求。尚未实际验收窗口标识、原生文件框、选线/Delete、最终截图及正常GUI关闭；进行这些操作前须先告知用户并协调桌面。固定候选NET/铜层现场仍未覆盖，0.11.0整体验收仍未通过；稳定产品0.10.0、固定候选和dist不变，main未操作。

## 前一轮：任务A审查与实验设计

已完整读取临时接手计划，并从fetch后的`origin/dev`提交`6256b7bc1b26cd410a8c3d0abfa3d79c656cd000`建立`verify/async-result-boundaries`。新交付为[异步迟到结果实验协议](docs/async-result-boundaries.md)：逐项审查固定`b0e5ac7`的NET代次淘汰、铜层代次/文档/网表身份淘汰，以及现有EditingTests实际证明的边界。

现有测试证明请求后编辑、处理完成回调时拒绝旧结果，但没有同步证明编辑时工作线程仍在执行。原生文件框中的oplock、禁用按钮和缺少完成信号不能补作该证据。因此本轮完成三项各一次的只读可行性审查后，固定候选GUI尝试为0；协议已列出T0—T4时间线、独立实验构建的实际工作线程门闩、NET不同指纹对照、每类两次上限和争用停止条件。实验构建尚未实现或执行，结果不得计作固定候选通过。

新证据在主工作区`.local-analysis/async-result-boundaries/`。实际当前Pi为`deng/gpt-6.1-sol high`，已核对环境和会话JSONL；保留截图终端仅只读核对。没有派发子代理，没有创建或复用Run/Task/Dispatch，未投递旧inbox。固定部署23文件、源输入7文件、上一轮隔离输入7文件及稳定dist22文件均保存集合/大小/SHA前后核验；本轮没有启动产品或控制客户端，不能记新增正常退出码。源码匹配按Git换行过滤后对象核验，保留首次直接比较CRLF与LF导致的预检失败原件。

稳定产品保持0.10.0，0.11.0整体验收仍未通过。下一步若实施门闩实验，应从固定候选另建实验分支和部署，按报告冻结新摘要及新执行身份；固定候选现场通过、产品集成与发布仍需独立依据。不重复常规A—F，不操作main。以下保留上一轮现场结论、证据和已结算生命周期。

## 上一轮现场结论

稳定`dev`产品源码和既有`dist/`保持**0.10.0**。固定0.11.0候选的常规编辑和主要保护已有上一轮证据；本轮补齐严格文本焦点、旧式菜单与编辑历史、10000mil远移后的显式reset、五类其他图元只读保护、关闭/换图取消的直接历史截图、选中文件后消失的实际读取失败，以及独立进程菜单退出确认放弃。

**0.11.0整体验收仍未通过。** 铜层迟到结果两次、NET迟到结果一次有界现场尝试没有取得完整竞争时间线；900000mil极端跨度下未直接确认远处属性；系统会话结束仍待受控环境。不能以驱动离线测试或已有产品自动测试替代这些现场边界。上一轮Task因退让不足和截图失败漏停链结算failed，原结论不改写。

本轮产品GUI已经结束。原候选PID27788及独立候选PID31072均由持有的进程句柄确认退出码0；本任务控制客户端正常停止，源输入、隔离输入和候选23/7/7文件集合、字节数及SHA-256前后不变。父代理独立核验迁移前后客户端树及候选共13个原进程身份均已退出。本轮Pi终端保留供接手，不再有后台桌面验收动作。

新报告为[剩余验收](docs/basic-editing-remaining-acceptance.md)，截图工作者提交`4b418d8653eda539c3c11eb35f39740d8ecdb999`，本Task/Dispatch已收到唯一一次`worker_done failed`并明确保留终端。父交付审计核对**3446项索引文件、76张PNG文件头、12个本地报告链接**均有效。父随后只集成四份验收/进度文档并修正主工作区的证据链接，不集成产品；最终dev提交以Git实际输出为准，不预写文档自身提交号。上一轮完整报告为[实际编辑验收](docs/basic-editing-actual-edit-acceptance.md)。

## 本轮新增现场结果

| 项目 | 结论 | 证据与边界 |
| --- | --- | --- |
| 严格文本焦点 | 通过 | 明确点击ΔX，123→Delete空→Ctrl+Z恢复123→Ctrl+Y空；板图几何、5图元/3走线及修订2不变，取消后Undo/Redo禁用；`checkpoint-1.json` |
| 旧式与现代入口 | 已测范围通过 | M→T与现代菜单打开相同移动框，D→T删除，E→U/E→R撤销重做；移动无独立现代快捷键，记N/A |
| 10000/10000远移与reset | 通过可视范围 | 移出旧视野后显式reset，可选到(10100,10100)→(10400,10500)、宽10mil/长500mil；Undo原端点clean、Redo远处dirty，底层隐藏保持；`checkpoint-2-3.json` |
| 900000/900000极端远移 | 部分观察，未完整验证 | 实际提交dirty修订3，100%及底层隐藏保持；reset后图元亚像素，三次未直接命中属性，不外推10000范围的结论 |
| 五类只读图元 | 通过 | FP自由焊盘、FV过孔、FA圆弧、FF填充、FS文字分别选中后Delete不改6图元/1走线、clean/修订19，移动自由线命令禁用，Undo/Redo禁用；`checkpoint-2-readonly.json` |
| 定向关闭与换图保护 | 通过已测路径 | Ctrl+W取消、empty换图取消、missing原生拒绝后取消、窗口关闭取消，均有Undo原端点/长500/clean与Redo删除直接图；补足上一轮缺图及受退让偏差影响的路径；`checkpoint-5.json` |
| 铜层迟到结果 | 未覆盖 | 两次有界尝试未取得运行中→编辑先完成→迟到结果未覆写的完整时间线，不再追加；普通编辑后NET保留、旧结论清空仍有观察 |
| NET迟到结果 | 未覆盖 | 一次oplock触发真实等待，但前景仍原生文件框，检查阻止画布输入，finally释放后NET正常加载；不是后台迟到时间线 |
| 选择后文件消失 | 通过第二次路径 | 第一次只触发原生文件框拒绝；第二次WinEvent HIDE删除新副本，Qt实际报找不到文件、当前工作和历史保留，Undo原端点宽10/长500clean、Redo删除dirty；`checkpoint-4-races.json` |
| 独立菜单退出放弃 | 通过 | 原进程窗口关闭放弃退出0；第二进程dirty后点击文件菜单退出、确认放弃，独立句柄退出0；不与窗口关闭混为同一项 |
| 系统会话结束 | 未覆盖 | 共享宿主不注销、不关机；需另安排受控环境 |

上一轮主要移动/删除/Undo/Redo、非法输入拒绝、元件内部图元与LIB隔离、测量清理/重新捕捉、NET映射保留及铜层清空/重算已有证据，无变化时不重跑整套A—F。0.11.0仍不支持新增图元、拖拽、元件移动、保存/另存为、布线、完整DRC或生产输出。

## 验收驱动与争用处理

用户已授权桌面控制；其他工程可能争用。检测user、非目标/不稳定前景、锁屏、控制不可用或执行中争用时，立即停链，记录明确的单调时间与墙钟截止，完整退让180秒。截止前不发送输入、截图、ControlStatus或原生桌面请求；单次本地等待不超过45秒以便沟通。到期只读复查允许后才恢复已知目标，仍拒绝则再次退让180秒。不能把user自动归因为人工操作，不能重连清门禁、换入口或修改第三方包绕过。

本轮统一Guard包含请求唯一ID、parent token、并发/排队拒绝、失败锁存和显式诊断/恢复。截图必须有image；即使`is_error=false`，无图或工具错误文字也停止当前链。输入已执行而后置截图失败时只补观察，不能重发移动/删除/关闭。原生对话框同样核对目标PID/HWND/映像；截图3840×2160返回1920×1080时倍率2，坐标以当时实际图像为准。Type需要loc或label，路径使用Windows反斜杠。

初版驱动32项离线通过；专用恢复与状态继承迁移版共52项通过，包含原32项。候选首次启动未前景时，外部门禁ready但本地Guard无法恢复已知目标，形成策略死锁。父审阅后增加专用`restore-target`：完整冷却后、实时外部门禁允许、输入桌面未锁、前景稳定、全桌面PT Renew标题唯一且PID/HWND/映像/创建时间一致，才允许一次App恢复并立即后验；普通输入仍要求目标前景，没有每步自动抢焦点。

运行时没有热更新入口，因此批准过一次正常迁移：旧客户端树正面退出后才建立新客户端，原候选PID/创建时间不变，原failed/token/not_before及全部历史步骤ID完整继承，新连接实际门禁再次核验。后续全部现场沿用该连接。Pi同会话内建压缩保留原session和`deng/gpt-6.1-sol high`，没有另建Task或替换模型。

必须保留的执行边界：

- `CONTROL_PREEMPTED`未被运行版自动设为争用截止，但失败锁存立即阻断后续动作；额外完整180秒静默后才诊断。原PowerShell5缺TickCount64把单调字段误写180，原墙钟有效；原件保留，父从事件双时钟映射生成`manual-control-retreat-m038.json`校正，审计零提前请求。
- Ctrl+0/Delete后Snapshot的`CONTROL_UNAVAILABLE`、菜单点击后闪烁层未关闭等均正确停链；恢复只补观察，不重复已执行动作。
- Type请求与实际文件名文字不符，来源未知，按争用完整180秒退让；随后从文件列表选supported并先核对实际文件名，再确认真正载入，不把成功回执当内容正确。
- NET辅助的原`result.reason`固定写“完成目标编辑后释放”，本次其实只是finally释放，没有画布编辑。保留原件及`factual-correction.json`，该回执不能证明产品竞态通过。
- 正常退出后的post_native失配也保守停链并完整退让，实际退出用持有句柄核验，退役保留失败与截止，不恢复已退出PID或重发放弃。

GUI及所有控制客户端退出后，父才替换本地验收Guard的通用`CONTROL_*`协议分类。实际运行版备份为`provenance/guard-runtime-52.py`，SHA`972c6c008713b681879f5d9c23da16965c6f09043f29b865bdbc11d16bbc4375`。未来修复在实际归档路径61项离线回归全过（原52项加9项新控制协议场景，不能再加总113），见`future-control/archived-summary.json`及日志。**未来修复未在旧现场实例加载，不构成新GUI验收。** 新运行须核对当前源码与新的审批摘要，不能直接沿用旧批准文件。

## 分支、候选与会话

| 项目 | 定位 |
| --- | --- |
| 主工作区 | `C:/Users/rikideng/orca/workspaces/pt_renew/main-2` |
| 本轮父文档分支 | `docs/basic-editing-remaining-acceptance` |
| 本轮截图分支 | `verify/basic-editing-remaining`，同级工作区`verify-text-screen-sol` |
| 产品功能分支 | `Kylineyes/feat-basic-editing`，已推送`b0e5ac7761f13690b5310bbc913ab7bfd2691d08` |
| 产品开发工作区 | 同级`feat-basic-editing` |
| 曾验证集成分支 | `integration/basic-editing-wave`，`1422a8d4ab3f7ee804f2224b2e4dd25d17979f2c`，不表示合入dev |
| 固定0.11.0候选 | 开发工作区`.local-analysis/basic-editing/release-candidate/pt-renew.exe` |
| 候选EXE SHA-256 | `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8` |
| 0.10.0发布EXE SHA-256 | `726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1` |
| 本轮Run/Task/Dispatch（已结算failed） | `run_361a6ad63310` / `task_d780e8e2eaad` / `ctx_eff89720518e`，不要复用其生命周期ID |
| 截图Pi终端 | `term_d544d0b2-a65f-4b5c-bea9-6257e802bd6d` |
| 截图实际Pi会话 | `01a1739a-82f6-76cf-9ffc-c63e95be56d4`，`deng/gpt-6.1-sol high` |
| 开发Pi终端 | `term_dd341315-769e-48e2-8939-736aa685a21b` |
| GLM研究Pi终端 | `term_e4974120-7dc9-4ffe-90f5-76c23497ba97` |

所有子代理使用Pi。纯逆向`glm/glm-5.3 high`，截图及验收`deng/gpt-6.1-sol high`，同任务沿用会话，核对实际JSONL、环境和工具结果。终端句柄属runtime`f95c7627-6971-4200-96a1-284003c521c6`，失效先枚举，不能推断进程已死；模型不可用如实报告，不替换。

## 本机证据与原材料

证据在Git忽略目录，远端clone不会带入，禁止强制add。

| 根目录（均为上述工作区相对路径） | 内容 |
| --- | --- |
| 截图工作区`.local-analysis/basic-editing-remaining-acceptance/` | 本轮全部截图/事件/checkpoint、原32/52项驱动、未来61项、输入摘要、迁移与清理、最终索引 |
| 同目录`migration-01/` | 主要现场单连接记录；该客户端已经退出，不续发inbox |
| 同目录`parent-audits/` | 父现场时序、13进程身份退出、离线轨迹、进程见证及同会话压缩审计 |
| 同目录`race-oplock/`、`race-file-vanish/` | 新副本的文件等待/删除实验，预期删除与固定7输入分开核对 |
| 截图工作区`.local-analysis/basic-editing-actual-edit-acceptance/` | 上一任务1309项完整证据及4处退让偏差、缺图原件，不覆盖 |
| 同工作区`.local-analysis/basic-editing-acceptance-retry/`、`basic-editing-acceptance/` | 更早真实窗口重试和启动前阻塞历史 |
| 编辑工作区`.local-analysis/basic-editing/` | 开发构建/测试、23文件固定候选与7文件来源输入 |
| 主工作区`.local-analysis/agent-dispatch/` | 自包含任务、父离线/现场/交付审计、归档脚本、协调检查点 |
| 主工作区`.local-analysis/development-wave/` | 先前父集成Debug/Release复验 |
| 研究工作区`.local-analysis/text-object-copy/` | 原文字对象16例受控执行与32字符边界 |
| 截图工作区`.local-analysis/text-screen-next/` | A240/层显隐379项证据与12张原生图 |

原安装`D:/project/pt_renew/pt`共99文件只读；`pt/`、`pt_install/`、`.local-analysis/`、截图、字体/库、反编译数据库及构建产物永不提交。PT.EXE SHA`abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968`，OVR SHA`cab0fc0571c5a295c396bd6479a57f060bb18a01d2c2ffc5b438cc1b65f8a0d8`；偏移不能用于其他版本。运行和写入实验只用新副本。

## 仍待完成与下一步

1. **补未覆盖的受控验收。** NET/铜层后台迟到需要可重复的实际竞争时间线；900000极端总览的直接属性仍缺；系统会话结束另在受控环境验证，共享宿主不注销/关机。已通过常规组无源码变化时不重跑。新任务使用新Task/Dispatch，不复用本轮已结算生命周期；保留原Pi会话和明确候选摘要。
2. **稳定线继续0.10.0。** 本轮只集成验收文档到dev并推送。未来产品集成须另有任务和验证，不能把报告合并当0.11.0实现或发行更新。main仅用户操作。
3. **原字形现场兼容。** `runtime_verified=false`；32字符对象创建16例、21792组合/105504中心线、1458边界例、无遮挡A240及Top隐藏恢复已有证据。真实缩放、完整/简化分派、F、251/252高度、旋转镜像、笔宽栅格、实际导入联合状态、长文字显示及保存往返仍缺；原字形未接入Qt渲染/命中/铜层。
4. **新增图元及另存为另立阶段。** 设计可撤销工具和取消状态；保存只写新文件，验证未知字段保留或明确拒绝、往返及原程序重开。元件放置、布线、完整DRC与生产输出各立阶段。
5. **发行与压力测试。** 干净Windows10/11运行库/部署、最大板图性能、安装包及许可义务仍待完成。

## 环境与验证

Qt6.12.0 MSVC x64，SDK`C:/Users/rikideng/Qt/6.12.0/msvc2022_64`，Visual Studio2026/MSVC14.51.36231、CMake/Ninja。已有Python、Unicorn2.1.4、Capstone5.0.7，不重复安装。

功能分支及父集成的Debug/Release各11/11组CTest已经通过；每配置QtTest270项，Python两组30项，研究工具全集45项有重复包含，不能简单累加。产品源码未改，本轮没有无变化重跑全部产品测试；驱动61项离线不替代产品GUI。

```powershell
& ./scripts/Enter-QtEnv.ps1
cmake --preset debug
cmake --build --preset debug
$env:QT_QPA_PLATFORM='offscreen'
ctest --preset debug --output-on-failure
cmake --preset release
cmake --build --preset release
ctest --preset release --output-on-failure
```

主工作区build目录可能仍是先前0.11.0集成构建，切dev不会自动将二进制降为0.10.0；运行前核对源码和重新构建，固定候选目录不得覆写。真实GUI必须移除offscreen和SDK插件变量，使用部署包自身qwindows；不拿offscreen代替真实窗口。

Git提交/合并和开发结果使用简体中文Conventional Commits，独立分支验证后合并推送dev，不强推、不跳钩子。**main仅用户合并、提交和推送。**
