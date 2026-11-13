# DOSBox-X 本机日志与配置加载证据

最新有限实机结论见[第八Status与正常退出](#eighth-status-conclusion)：同一新槽已实际核 `SYN1.PCB` 与八项计数，Up／Esc路径及四原等待通过；完整配置来源／继承仍按[剩余离线核验方案](#remaining-configuration-plan)保留，不把旧Shift失败或第七预算停止改写为成功。

本次离线复核确认：DOSBox-X 的文件日志选项为 **`[log]` 下的 `logfile`**；类别日志开关也在 `[log]`，DOS 控制台输出开关则为 **`[dos]` 下的 `log console`**。现有 verification-33 证据不能证明安装配置或用户配置是否被额外加载，也不能把黑底白横线归因为 OpenGL、vsync 或原程序。下一轮应先保存启动日志和配置来源，再决定是否需要输出后端对照。

本次基线为 `origin/dev=a5c2bde201bec8f7b405553a8bc0c5f0d2abe35f`，独立分支为 `Kylineyes/research-dosbox-config-evidence`。只新增本文；未启动 DOSBox、GUI 或 Windows-MCP，未进行键鼠/窗口控制，未安装、下载依赖，也未改动共享场景或用户配置。未合并或推送 `dev`、`main`。

## 来源与版本边界

下表别名用于后续精确行号引用，全部是本机文件，未访问文中外部网址。

| 别名 | 本机绝对路径 |
| --- | --- |
| 安装目录 | `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/` |
| F（完整参考） | `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.reference.full.conf` |
| R（简版参考） | `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.reference.conf` |
| I（安装配置） | `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.conf` |
| U（用户配置） | `C:/Users/rikideng/AppData/Local/DOSBox-X/dosbox-x-2026.10.01.conf` |
| L（随包英文帮助文本） | `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/languages/en_US.lng` |
| C（随包变更记录） | `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/CHANGELOG.txt` |
| B（随包说明） | `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/README.txt` |
| S（既有场景） | `C:/Users/rikideng/orca/workspaces/pt_renew/research-menu-runtime-validation/.local-analysis/verification-33/` |

F、R、U 第 1 行和 C 第 1 行标注 `2026.10.01`，但 I 第 1 行标注 `2026.08.31`。I 是本机已有配置，不能因所在目录名称就视为该版出厂默认值。安装目录按 `*.c`、`*.cpp`、`*.h`、`*.hpp` 枚举未发现启动或配置解析源码；以下证明的是安装文档定义和文件内容，不是对当前二进制完整加载实现的审计。

原始快照和完整摘要仅保存在本工作区忽略目录 `.local-analysis/configuration-evidence/`，不提交第三方全文。`inputs-before.json`、`inputs-after.json` 覆盖 12 个输入，`verification.json` 记录前后差异为 0；安装配置、用户配置、场景配置摘要也分别与 S 的 `readonly-startup-diagnosis.json` 一致。

| 输入 | 字节数 | SHA-256 |
| --- | --- | --- |
| F | 293719 | `a33ddd908c7c58361985044b01e93b15f56e562d5485fa8baf17221ea6ebe14c` |
| I | 116956 | `733084f61ef2f4ec1710f5c3d7553d00e73e90650b9edd90056a7773d30d802c` |
| U | 124891 | `0d19342e41a9c73304a0923cfb10b0acd433cc57e6482eefec9932536c056d38` |
| S 的 `dosbox-c21-no-dft.conf` | 655 | `9d3b7532dc107773a2b98bf9e9767177b6fe87a1f42a3270421aeec46a3d4e19` |

模拟器映像摘要沿用 S 的既有记录：`a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832`；本次没有执行映像核验版本或重新读取其字节。

## 日志选项：可直接使用的片段

将片段写入后续独立场景的完整配置，路径改为该场景已经建立的绝对目录。此处给出语法示例，不代表本次创建或运行了该场景。

```ini
[log]
logfile=C:\独立证据目录\dosbox-startup.log
files=normal
exec=normal
gui=normal
misc=normal

[dos]
log console=true
```

若首轮只需最小变更，可以仅增加 `[log]` 与 `logfile`。上述片段使用 `normal`；需要更细日志时再单独改为 `debug`。加入类别开关和 `log console=true` 则用于增加文件访问、执行及控制台可观测性；这些类别名不能保证每个启动阶段都有记录。不要把 `logfile` 放在 `[dosbox]`，也不要为本任务自行增加未见本机定义的通用 `loglevel` 键。

| 选项或概念 | 本机定义与精确行 | 可以确认的边界 |
| --- | --- | --- |
| `[log] logfile` | F 第 109–110、163 行；R 第 107–108、115 行；U 第 111–112、119 行 | 日志保存文件；三个参考/用户文件中的值为空；I 第 107–108、115 行也为空 |
| `files` / `exec` | F 第 131–132、135–136 行；赋值第 174、176 行 | 类别开关可选 `true, false, debug, normal, warn, error, fatal, never`；文件中的值为 `false` |
| `gui` / `misc` | F 第 149–152 行；赋值第 183–184 行 | 同上，可显式使用 `debug`；没有本机源码证据解释 `true/false` 与各阈值的内部对应 |
| `vga` / `vgagfx` / `vgamisc` / `int10` | F 第 111–118、164–167 行 | 支持同一组类别值，参考值为 `false`；仅在确需视频细节时再启用，避免首轮同时扩大日志量 |
| `int21` / `fileio` | F 第 159–160、188–189 行 | 分别定义为记录所有 INT 21h 调用、经 INT 21h 的文件 I/O；参考值为 `false`，不能把它们当作等级字段 |
| `[dos] log console` | F 第 2450、2504–2505、2731 行；U 第 1257、1363 行 | 支持 `true, false, 1, 0, quiet`；`quiet` 仅留 DOS CON 输出并排除调试输出，首轮不宜使用；图形页不保证经过 CON |
| `debuggerrun` | F 第 161–162、190 行 | 定义的是调试器启动后的运行模式，不能当作打开普通文件日志的必要开关 |

日志文件即使创建成功，也不保证包含设置文件日志之前的早期输出；安装文档未给出初始化时序保证。下轮若需早期启动诊断，应同时保存目标进程 stdout/stderr，并把它与 DOSBox 独立日志分别命名。S 中目标标准流被丢弃的事实来自 [既有诊断](legacy-menu-runtime-validation.md)，本次未连接或修改其启动器。

## 配置加载与 autoexec：定义和实际必须分开

| 规则或入口 | 已安装来源与行号 | 可确认结论 |
| --- | --- | --- |
| `-conf configfile` | L 第 862–864 行 | 按指定配置中的选项启动；不等价于证明该文件在某次启动中成功解析 |
| `-userconf` 与 `-conf` | C 第 9752–9753 行 | 历史变更说明二者可以组合使用；未定义本版本精确加载先后 |
| 多配置能力 | C 第 9948–9949 行；L 第 297–308 行 | 历史变更说明支持多配置，帮助文本分别命名 primary、additional、global；文本没有证明当前加载列表 |
| 默认文件名 | C 第 6529–6532 行 | 历史说明 `dosbox-x.conf` 与 `dosbox.conf` 都可作为默认文件名；不构成当前搜索顺序的证明 |
| `-defaultconf` | C 第 5995–5996 行 | 定义为使用默认配置设置；未说明与 `-conf` 同用时的精确先后，本次不据此推荐混用 |
| `-defaultdir` | C 第 5997–6000 行 | 指定工作目录，并在其中查找 `dosbox-x.conf`；不证明 S 启动用了该参数 |
| 工作目录提示变化 | C 第 4–5 行 | 此版变更为使用 `-conf` 或 `-userconf` 时不提示选择工作目录；不等价于任何配置已加载的证据 |
| `-set` | L 第 894–896 行 | 指定选项覆盖配置文件，可以重复；首轮不宜同时改写图形相关选项 |
| `[autoexec]` | F 第 3120–3122 行；B 第 35 行 | 该节的行在启动时执行，可放 MOUNT 和程序启动命令 |
| `-noautoexec` | L 第 881–882 行 | 跳过已加载配置中的 `[autoexec]`；首轮复现场景不能无意加入，否则会改变程序启动序列 |
| `resolve config path` | F 第 235 行及第 481 行 | 文件注释定义为解析包含路径的配置选项，但明确排除 `[autoexec]`；参考值为 `true`，不能依赖它替 MOUNT 解析相对路径 |
| 后续只读查询入口 | L 第 354、359 行 | `config -axtype` 显示 autoexec，`config -get "section property"` 返回当前属性；本次未执行这些客体命令 |

<a id="explore-ex-005"></a>

**本段形成时尚未证实的加载规则**，已有后续有界结论：[默认根与三阶段守卫](dosbox-default-roots-static.md#final-explicit-and-eight)现列明显式 `-conf`、cwd、程序／用户目录和默认候选的条件；[parser／setter与autoexec](#fixed-config-parser-setter)核定文件登记、属性写入和同一对象的行文本追加；[初始化消费者](#autoexec-initial-consumer)进一步核定当前文本取样、自有复制与开关门，完整调度和执行仍缺。未指定键不能简单认为继承 I 或 U，F/R 参考值也不直接等于本次有效值；特殊词法、类型／回调效果和历史实际来源仍按 [EX-005](exploration-backlog.md#ex-005) 保留。

[探索 EX-005](exploration-backlog.md#ex-005)。

S 的 `processes-launch.json` 第 7 行记录 PID 46020 的命令行只有一个 `-conf`，参数指向 S 的 `dosbox-c21-no-dft.conf`，未出现 `-userconf`、`-defaultconf`、`-noautoexec` 或 `-set`。该配置第 1–3 行设置 `output=opengl`，第 8 行设置 `machine=vgaonly`，第 15 行设置 `cycles=fixed 10000`，第 18–24 行为 autoexec，依次挂载 C/D、切换 C、`cd \pt`、`pt C21.PCB`。这是磁盘内容和主机启动命令的证据；不能据此宣称所有命令已在客体内成功执行、PCB 已加载或菜单已进入。

## OpenGL、vsync 与白横线的证据限度

F 第 17–18 行把 `output` 定义为视频输出系统，并包含 `opengl`、`surface` 等可选值。S 明确请求 `output=opengl`，I 第 82 行为 `ttf`，U 第 85 行为 `default`，F 第 81 行也为 `default`；这说明磁盘配置存在差异，不证明 S 实际发生了覆盖、回退或后端故障。B 第 37 行关于默认 Direct3D 的概述也不能替代实际启动后端记录。

`[vsync]` 在 F 第 1138–1144 行定义：`vsyncmode` 同步宿主显示时序并要求校准，参考值为 `off`；`vsyncrate` 参考值为 `75`，`host` 模式下忽略该值。I 第 482–488 行和 U 第 509–515 行同样写成 `off/75`。S 配置没有 `[vsync]`，因此不能把上述文件内容直接表述为该次有效 vsync 状态，也没有证据表明 vsync 导致白横线。

F 第 912–915 行确实描述 `page flip debug line` 和 `vertical retrace poll debug line` 会产生调试线，参考赋值在第 1085–1086 行均为 `false`；S 未设置它们。这些文档只解释选项含义，既不证明白横线就是某种调试线，也不证明实际有效状态。C 第 7 行关于 OpenGL scaling 的修复记录同样不能指认本次原因。

既有运行记录确认窗口身份及黑底白横线，未取得可辨启动页；不存在该次 DOSBox 独立日志。**渲染、初始化、配置加载和原程序启动阶段仍未区分，根因未知，`runtime_verified=false`。**

## 下一轮首轮观察与最小对照

1. 由桌面独占 worker 在全新隔离场景保留同一输入、模拟器、`output=opengl`、CPU、挂载和 autoexec，仅增加日志设置；保存启动命令、主机工作目录及输入摘要。
2. 首先核对独立日志是否创建、绝对路径是否正确、有无无法打开日志或配置的错误；保存目标 stdout/stderr，寻找版本、配置路径、primary/additional/global 信息。日志没有某条信息，只能记为“未观察到”，不能当作没加载某文件。
3. 顺序观察实际输出后端/初始化错误、视频模式转换、MOUNT/目录/EXEC/文件访问是否有记录及其结果。CON 日志和窗口标题都不能代替 AUTOTRAX 启动页、菜单及 Work File Name 的实际核验；首次仍只有白横线时按既定停止边界停下。
4. 仅在首轮日志不足且后续任务允许时，安排第二个隔离场景只把 `output` 改为 `surface`（F 第 17–18 行）；其余参数及输入不变。若画面不同，只能说明输出路径与现象有关，尚不能定位驱动、vsync 或程序根因；不要首轮同时改输出、vsync、周期和机器类型。
5. 若疑点在配置继承，先取得有效配置值与来源，或单独做配置来源对照；不要把用户配置的内容直接复制为有效配置，也不要在日志首轮追加新的 autoexec 诊断命令而改变原有启动序列。

本任务没有发现值得提交的通用归一化工具需求，故仅留下本地标准库摘要收集脚本。验证命令为 `python .local-analysis/configuration-evidence/collect-evidence.py before`、整理后执行 `python .local-analysis/configuration-evidence/collect-evidence.py after`，以及 `git diff --check`；快照文件拒绝覆盖，重复研究应使用新证据目录。仅文档变更，不运行 Qt 构建或 GUI 验证。

## 新冻结场景：有效值与 Enter 后板图已取，状态核定受阻

<a id="effective-state-attempt"></a>

2026-11-11 接续 [EX-005](exploration-backlog.md#ex-005)，Task `task_215b58349614`／Dispatch `ctx_0c55cb76da25`，分支 `research/ex005-effective-state`，Pi `01a1cb98-e57e-75d0-9b06-c40a941eaaf0`。同一原 UTF-8 JSONL 的模型／thinking 事件、实际 assistant、环境和成功工具回执持续为 **`deng/gpt-6.1-sol / high`**。**本轮事项结果为受阻／failed：取得了配置关键有效值、启动与一次 Enter 后的板图，但未取得 Information／Status 的 Work File Name 和图元计数，不能删除事项。** 没有编辑 PCB、另存、保存重开或执行 EX-007。

父同步领取后才准备，审阅新工具／门／只读查询及假验证，首次写新槽 GO：UTC **19:25–19:50**，**19:43 起仅收尾**。唯一操作者为本 Pi，父不查询或输入桌面；已退出的 EX-001／004 及更早双槽、GO 和原失败只读。新槽位于本树 `.local-analysis/ex-005/candidate/slot/`；plan SHA-256 `a4b74ddeff87da84e69243d881ddd7210ac0d929861c6c04628b57f670faf300`，driver `b9dca0d1e17ccad199c2b7ae4c75c20e2c1bbfac1712ff43aedb3e1e8d53e2a2`，gate `cf31f884d82607545c45e9392daa55ff808e7790d10db5fb039faa52c27f8112`。24 冻结项／runtime99／input1 完整 preflight 后启动一个新目标和一个公开 windows_mcp 服务。

### 本次实际来源、查询和 autoexec

新目标 argv 只有固定 DOSBox-X EXE、`-conf`、本槽 `SYN1.conf`，cwd 为本槽 `runtime/pt`。本轮早期 stderr 实际记录 `CONFIG: Loaded config file: <本槽>/SYN1.conf`、对应工作目录，以及 **DOSBox-X 2026.10.01 Commit b6abbd5（Visual Studio SDL2 64-bit）**。EXE 25836544 字节，SHA-256 仍为 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832`。早期流在文件日志初始化前已开始保留，不能只查后半 `dosbox-startup.log` 就断言没有配置加载记录。

没有改输出后端或安装／用户配置。新 autoexec 顺序为 `@echo off` → 两次挂载本隔离 runtime 到 C／D → `c:` → 七条只读 CONFIG 查询并重定向到本槽 runtime 根 → `cd \\pt` → `pt SYN1.PCB`。查询只读取属性，**未用 `-set`、`-wc`／`-writeconf`、GUI 或全局配置写入**；输出文件不在被冻结的 `runtime/pt` 输入目录内。

| 当前客体命令 | 本轮隔离输出／实际结果 | 能证明的边界 |
| --- | --- | --- |
| `config` | `CFGINFO.TXT` 是命令用法帮助 | 本机该调用没有列出 primary/additional/global 来源，不能冒称得到完整来源列表 |
| `config -axtype` | `AUTOEXEC.TXT` 按顺序列出本场景的挂载、查询、目录切换和 PT 命令 | 该次当前 autoexec 内容与冻结文件一致，不外推任意多配置合并的追加／替换规则 |
| `config -get "sdl output"` | `OUTPUT.TXT`：`opengl` | 本次该属性实际值，不以 I 中 `ttf` 或 F/U 的参考值代替 |
| `config -get "dosbox machine"` | `MACHINE.TXT`：`vgaonly` | 当次实际机器类型 |
| `config -get "cpu cycles"` | `CYCLES.TXT`：`fixed 10000` | 当次有效周期设置 |
| `config -get "dosbox memsize"` | `MEMSIZE.TXT`：`16` | 当次有效内存值 |
| `config -get "dosbox captures"` | `CAPTURE.TXT`：本槽绝对 captures 路径 | 当次有效输出位置，并由后续两张新 PNG 实际落盘佐证 |

同次独立日志记录七个 `config.COM` 执行及输出文件创建，然后 `pt.EXE`、GRAPH／MNU／KEY／PAD 等访问。Early stderr 只报告本次显式文件；**这份观察不证明所有潜在来源都被完整枚举，也不回答任意多个 `-conf` 的覆盖优先级**。安装 I、用户 U、完整参考 F、英文帮助的原字节摘要前后未变；未指定属性和更广继承规则继续未知，不能把本次几个实测值泛化为全配置恢复。

### DFT、合成输入与单次 Enter 的真实后验

只在新隔离副本删除 `TRAXEDIT.DFT`，原安装 DFT 保留不变；runtime 99 项中该文件前后均不存在。输入 `SYN1.PCB` 为 **180 字节**，SHA-256 `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`，文本结构有 **5 FT、0 COMP／CP／FV／FF**，一条水平线加矩形四边。这是已知合成输入，不是原 AUTOTRAX 新建线段的默认字段证据。

兼容采样 33 样本无失败，最大单样本 **3.7111 ms**、最大启动间隔 **13.921 ms**，兼容线程真实 join。新目标 PID `45692`、FILETIME `134388987854713477`、HWND `1248646` 由原 Popen 绑定，精确聚焦后只按当前图逐步 Capture，并逐张实际 read：

| 新客体 | 字节数／SHA-256 | 指定模型实际观察 |
| --- | --- | --- |
| `captures/pt_000.png` | 6350；`eeb87e89693a12bdc2008113016e6cfc8fd29d36d037b3f9a337897066bfb628` | 640×480，AUTOTRAX 1.57 启动页，`PRESS ANY KEY TO START` 清晰可辨 |
| `captures/pt_001.png` | 2371；`d35bb9242f15c58478c39ac21e252bb613c9a45e1e8fc5ab7420ca1db8a24cf5` | 一次公开命名键 Enter 后，640×480 灰底板图、红色矩形四边加横线，底栏 `1:Top Layer / P:ROUND62 / T:12 / S:60 / G:25` 可辨；这些是底栏标签，不是 Information 文件名、图元计数或自建单线默认值 |

本轮 Enter 发前一次性 marker 记录 UTC `19:30:27.897834`，没有重发；日志在该输入后出现 `file SYN1.PCB` 打开请求，且新客体图形与五条 FT 结构相符。底栏原说明曾误读为 `Track:20 / RND:50`，父审阅后本模型重新实际 read 同一原 PNG，确认右半黄色底栏为 `P:ROUND62 / T:12 / S:60 / G:25`（约 x360..625、y456..469），本表已纠正。原错误核验、冻结审核及原会话保留，不把更正后的解释写回历史证据；底栏标签也不解释为新线默认策略。**仍没有 Work File Name 与实际统计对话框，不能只据图形和文件访问就宣布文件名／计数已经 GUI 核定。** 宿主对应图仍黑底白横线，两侧差异沿用 [EX-002](exploration-backlog.md#ex-002) 的现有限制，没有修改后端或推断统一根因。

四次 Capture 业务 Click 各有独立 trace，样本数 **190／189／188／190**；最大单样本 **2.3813／7.1966／1.5283／1.1083 ms**，最大启动间隔 **12.6610／17.5698／34.0944／11.6817 ms**，都在冻结拒绝线内，无失败且完整覆盖 RPC 与至少 100 ms 后段。每轮完整 captures 集合差分别为 0→1、1→2，旧 PNG 未改删，两个新增均非空且 IHDR640×480。后续没有补采第三张来绕过状态输入失败。

### Shift+I 后的可见输入法候选与停止边界

<a id="ime-state-boundary"></a>

本次经当前 Enter 后客体审核及既有 Information 通道证据，发送一次获批 `Shortcut shift+i`；发前一次性 marker 为 UTC `19:32:41.159088`，响应 `19:32:41.716053` 为 `Pressed shift+i`。该次实际宿主后图左上出现 Windows 输入法候选框，含 `I / i / lc / ID / Id` 等候选；没有可用的 Information 客体后验。收尾当前图候选框仍在，同目标线程的可见 ATL／Cicero 窗记录一并保留。

这些证据**不能证明 Shift+I 全部由谁消费、是否有部分事件到达 DOS 客体或为何走到候选框**；也不能把 DOSBox stderr 中 keyboard layout／mapper 为 US 当作 Windows 输入线程已经绕开 IME。没有为补图而继续鼠标 Capture，没有重发 Shift+I、改输入法、切控制接口、补 Status 或 Esc。此未解释通道问题补入已有[EX-003](exploration-backlog.md#ex-003)，不新建同义队列。后续[安装原AST／假API离线核验](native-menu-calibration.md#shortcut-offline-semantics)已确定该参数走VK而非普通字母Unicode通道，并限定Pressed及扫描码/IME证明范围；没有新输入或修复结论。有效配置／文件名计数的剩余条件仍在 [EX-005](exploration-backlog.md#ex-005)，不能通过删项弱化条件。

模型据真实图停止业务，原 driver 在 UTC **19:33:49.056230** 记录 `Refused`；`quiet-period-ended` 为 **19:35:49.057711**，完整 **120.001481 秒**零新增桌面请求，采样已 done。父确认维持停止和原正常收尾范围，不恢复业务或延写 GO。之后只有 CleanupSnapshot、当前图正常宿主 X 一次、原 WaitExit；无需额外聚焦、连接或 helper。

### 正常退出、原件和交付范围

静默后本模型真实 read 当前宿主 X，依据当下全屏缩放图点 `(352,62)` 得物理 `(704,124)`，原目标稳定前景；一次正常默认 Click 后由原 driver 原 Popen 真正 wait。所有 PID／FILETIME／映像／原 HANDLE 和 Popen identity（适用时）均与原创建记录精确匹配：

| 原创建者等待对象 | PID | 真实返回与 UTC |
| --- | --- | --- |
| 目标／driver 原 Popen | 45692 | wait0，19:39:34.471758 |
| 公开服务／driver 原 Popen | 49724 | wait0，19:39:34.734080 |
| driver／owner 原 Popen | 50188 | wait0，19:39:34.742290 |
| owner／原 .NET Process 与 HANDLE | 4464 | WaitForExit=0，19:39:34.7539260 |

线程真实 join；没有 Alt+F4、强杀、WM_CLOSE 或用服务退出替代目标退出。FILETIME 只经 Python／PowerShell 原整数，不经 JavaScript Number。外层隐藏 PowerShell 自身仍无原 Popen 退出证明，不由下层 wait0 外推。全部已知链在本分段业务截止前退出。

共 **10 张唯一宿主 PNG + 2 张新客体 PNG**，十二张原字节 SHA 均逐一匹配本 Pi 原 UTF-8 JSONL 的实际 image 回执。原安装99项、旧双槽包399项、EX-001证据584项、EX-004证据336项、本次runtime99／input1的完整集合／大小／SHA前后未变；安装／用户／参考配置及帮助原字节也不变。新增配置探针文件只在本槽runtime根；`NEWFT.PCB`不存在，PCB输入未写入。

新增工具 [prepare_legacy_state.py](../tools/prepare_legacy_state.py) 只最小扩展已验Capture／停止／正常X链。离线状态门 **15 项**、当前 driver **19 步**假状态流程、当前真实 AST **13 项**停止注错、24 项冻结 preflight 均通过，均不冒称真实状态验收；未重复无变化产品构建或采样模块测试。证据在本树 `.local-analysis/ex-005/` 的 `readonly-before.json`、配置探针、同次早期stderr／日志、`live-audit.json`、新原图／逐步审核／trace、原创建退出及停止原件，原软件、会话和截图均不提交。后续必须先在公开门和新审阅范围内解决输入通道及缺失的 Information／Status 证据；EX-007 仅有准备建议，本轮未启动。最终文档检查 **153 份 Markdown／1030 个本地链接／41 个开放事项／105 个来源细节／137 份索引报告，零错误**，`git diff --check` 通过。清理可重建假 fixture／本轮模块缓存 **196955 字节**，归档 **0**，净减少 **196955 字节**；保留现场证据约 **24.53 MB**，不删改输入、原图或停止失败记录。

<a id="named-status-plan"></a>

## 新8小时：基于Up首行环绕的命名Status方案与父集成验证

本节接续[EX-005](exploration-backlog.md#ex-005)与[EX-003](exploration-backlog.md#ex-003)。方案形成时，第六[Information／Esc有限导航](native-menu-calibration.md#sixth-navigation-conclusion)已实机取得，**当时尚无新Status现场／候选／GO**；后续第七实际结果见[预算停止记录](#seventh-status-budget-stop)。用户8小时总窗UTC2026-11-12 21:14:51.2986127至次日05:14:51.2986127，最后10分钟仅收尾；每段仍最多60分钟、至少7分钟正常收尾。沿原Pi／Task／当前Dispatch及指定模型high，新实现先交父代码审，不能沿用第六冻结或旧GO。

原逐Down方案约19–20轮，以第六实耗保守需57–65分钟，超出53分钟业务预算，已经排除；不省略read或延长单段。本次只沿既有常驻选择器定向检查，原 `PT.EXE` SHA `abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968`，MZ头 `0x3de0`，分析段324e对应原段224e，磁盘偏移为 `0x3de0 + 0x224e0 + 段内偏移`。只读Capstone5.0.7与已核MZ重定位、MNU／KEY交叉，没有加载／执行目标或新建反编译数据库。

| 原指令位置／原文件偏移 | 定向结论 |
| --- | --- |
| 324e:0650，尤其0670–0689 | 底层读取AL为0时，把AH扩展扫描码加0x80并返回低字节；Up扫描码0x48对应菜单码0xC8。真实宿主到DOS是否按此送达仍待新guest |
| 324e:16c9–16e2／17b0（0x27a70） | 从当前菜单表取结构指针到BP-1c，初始化当前行为1 |
| 324e:19a1（0x27c61） | 比较当前输入是否0xC8；不是就进入后续分支 |
| 324e:19ba／19be／19c2（0x27c7a／7e／82） | 当前行dec，比较0，非零跳19cd；不能按常见UI猜饱和或环绕 |
| 324e:19c4／19c7／19ca（0x27c84／87／8a） | 减至0时取BP-1c菜单结构首字总项数，赋回当前行，再19cd–19da重绘；早期排队路径17bd–17d6同样处理 |
| CS:169b的32字节字符集合／选择器至1a48返回 | End码0xCF／Home码0xC7不在首字符集合，选择器也没有它们的首末项分支；本方案不用End／Home。KEY的REDRAW／RECENTRE含END／HOME不能替代此菜单逻辑 |

原MNU的INFORMATION恰有7项，首Board Dimensions、末Status，与第六pt010实图吻合。因此静态支持**只在Information首行确认后，单独Up一次指向末项Status**；并非已经运行成功。远调用191f的段字1922在MZ重定位表中，不能把磁盘远调用段常数直接当运行段。父已逐字独立核同451行定向报告并落 `ex005-status-parent-static-review.json`。本树证据 `ex005-status-offline/selector-disassembly.json`、`positioning-static-review.json`保存原偏移／字节／断言；没有宽扫或重做已知菜单编号。

公开Shortcut的安装原AST＋假API回放8例（Up／End／Home及既有故障例）未导入windows_mcp／COM／UIA或加载user32，输入源码摘要不变。`up`转换为 `{up}`、VK_UP=0x26，假MapVirtualKey结果0x48，keybd_event按下／释放flags分别1／3；End=0x23、Home=0x24也走VK，但回放默认扫描fixture未定义二者，返回0不能拿来宣称真实扫描码。该报告只证包装传参，不证实际IME／Windows／SDL／DOS消费。

`prepare_legacy_state.py --named-status --budget-seconds 3600 --file-submitter-session <原Pi JSONL>`显式选择新方案，复用navigation／原driver／owner自有队列以及同七条CONFIG只读探针；未用此参数时历史Shift分支的配置／driver／gate逻辑沿用，已知失败不据此重跑。新门将主菜单Down7与Information专属 `status_position=up`各一次分开：startup Enter1→main Enter1→主菜单Down7逐图→Information确认Enter1→首Board Dimensions新guest→Up1→新guest必须Status高亮→status_confirm Enter1→Status新guest读文件名／八计数→status_return Esc1及新guest。只在返回后实际仍有菜单才允许menu_return Esc1，否则直接正常收尾。按静态Status输出门，**Status页禁止Enter或任何SAVE FILE NAME／报告输出**，未看清或Up未知即停120秒，不重发、不改为六Down、不切IME。

每个命名目的有发前used标记，门检查前置上下文、已结束阶段禁回放、预算上限和当前nonce／host／guest审核；driver原Shortcut分支消费标记并只调用公开工具。全部仍经原submit.validate／唯一未消费请求／排他x写，owner队列及原Pi JSONL身份、图片SHA、隔离／冻结／GO／生命周期／stop-join保持。必需14轮、含必要返回15轮，Capture硬上限16；按第六实耗估计45–50分钟业务、剩余至少7分钟段收尾，现场若耗时超预算仍须及时停，不能从估计推保证。

七CONFIG输出只在新槽runtime根，目标argv仍唯一显式-conf、输入及原安装不写；配置／源列表新增冻结state工具、安装配置／用户配置／英文帮助，真实候选预计28项（合成目标与Python同路径去重为27）。`config`只帮助文本、单次stderr只见本conf的原有边界保持，**完整潜在配置来源枚举／任意多conf覆盖仍未知**。Status文件名显示为去目录名称／扩展名且最多24字符，八计数按原静态路径为当前内存模型统计，不单凭5FT文本或底栏标签代GUI。

新命名状态8项、原隔离21项、预算3项共**32/32**通过，无skip／ResourceWarning：完整序列由原gate／原submit和真实driver Shortcut分支配假窗口／工具执行，覆盖上下文／重放／Shift与EndHome拒绝、七Down及新guest／review、16轮边界、七探针输出／旧路径／额外命令拒绝、派生最终门、无源／非法预算零准备以及公开Up原AST。它们都是合成／假创建，不是Status已验。首次6项setUp因合成JSONL被写成多行而JSONDecodeError，伴隐式清理ResourceWarning；修单行和addCleanup后，另一次仅1项冻结数量断言28!=27失败，修合成范围后8项通过，原JSONL回执不覆盖。只读核六个本轮失败临时目录已不存在，额外删除／归档／净释放均0。证据位于 `.local-analysis/ex-003-live/ex005-status-offline/validation.json`、`validation-tool-result.json`及回放／静态报告。协调者完整审查 `768dd07cdf73422007296b8dd22591f1ce42d802` 的工具／上下文门和测试，在 `main-2` 独立分支合入并完成相同32/32复测：新命名状态8、隔离21、预算3，无skip／ResourceWarning；交付源文本一致，测试后旧事故包400项和原安装99项完整集合／大小／SHA匹配。文档153／1061链／41事项／111来源／137报告零错，diff通过；父证据 `config-path-incident-20261112/named-status-parent-validation.json` 与三组parent日志。此为离线集成通过，下一步全新候选仍须父独立核配置／冻结／输入／原件后签新GO，不代表真实Up定位、Status文件名计数或完整来源已经验证。

EX-005完成条件未降低；旧六槽不重启或改写，真实现场另建独立候选。

<a id="seventh-status-budget-stop"></a>

## 第七实际场景：六轮到Edit，预算不足正常退出

2026-11-13，同一原Pi／模型high、Task `task_db06ca9d4229`／Dispatch `ctx_ed7b7e9ec944`，当前协调Pi `01a1d184-26bc-7092-be0b-362193a84c8c` 独立审查全新 `.local-analysis/ex-003-live/candidate-seventh-status/slot/` 后签本段GO：UTC **00:57:45.743166–01:57:45.743166，01:50:45.743166起仅收尾**。用户8小时总窗仍有效，但不能延长本段。plan SHA `40802469c4736bc14f6e94cc7dc936108db60215106c71b057b6cdf56d0e5ce2`，conf `02fa3a28cfd6b4ec0314c4f71b561a779f75fa5d94d15a697dff99520e1cd40f`，driver `c3fa2e1c16bb4ce489d77d5bf5b8466a3e528233fa384b1b59236f662be93f8f`，28冻结／99 runtime／1 input核验通过后唯一启动。

**本段结果为预算不足：六轮新客体图只到Edit高亮；未发Down4、Information确认、Up或Status输入，GUI工作文件名／八计数未取得。** 没有菜单失败、门拒绝或未知按键重发；协调者接受停止，只正常X一次、原WaitExit／Stop。不存在需要补造的120秒失败静默。[EX-005](exploration-backlog.md#ex-005)与[EX-003](exploration-backlog.md#ex-003)均保留，不能用第六的Information图填补本槽。

### 同次配置与逐键后验

七个CONFIG输出均已实际读取：`config`仅帮助，AXTYPE列本第七挂载／七查询／目录／PT命令，属性仍为 `opengl / vgaonly / fixed 10000 / 16 / 本第七captures绝对路径`。同次early stderr明确本第七 `SYN1.conf`、本第七cwd与 `DOSBox-X 2026.10.01 Commit b6abbd5`；独立日志记录七次config执行和PT／SYN1访问。这证明该次显式配置加载与几个有效值，**不枚举全部潜在来源，也不解决多conf覆盖规则**。Windows layout `0x0804` 与host／mapper `us`只是实际日志，不能宣称绕过IME；主机仍黑底白横线，客体Capture清晰，没有换后端或解释根因。

唯一目标PID2020、原HANDLE668、FILETIME `134390052357426303`、HWND1314662；33兼容样本无失败且原线程join。每键之后先读新host，再显式打开Capture并读新菜单host，看到Take screenshot才单击，再实际读新host和guest；不存在批量导航。六个640×480新PNG如下；底栏 `P:ROUND62 / T:12 / S:60 / G:25`只作标签。

| 客体文件 | 实际观察 | SHA-256 |
| --- | --- | --- |
| pt_000.png | AUTOTRAX 1.57启动页／PRESS ANY KEY TO START | `eeb87e89693a12bdc2008113016e6cfc8fd29d36d037b3f9a337897066bfb628` |
| pt_001.png | 唯一startup Enter后的红框／横线板图 | `d35bb9242f15c58478c39ac21e252bb613c9a45e1e8fc5ab7420ca1db8a24cf5` |
| pt_002.png | 唯一main Enter后的Block高亮 | `653a11a51c127f1534a5963c5ba4af5820d1f5946b0cf876e56fd20196ba5299` |
| pt_003.png | Down1后Current高亮 | `a7ab943f9db558b0bf8f7c0fc2597bc54666c044a5c020da5fad7b2e4317082a` |
| pt_004.png | Down2后Delete高亮 | `0704fdb2a1414db750c21c91efdbdf0071dbb8024465ff60c3c30698e69c02fb` |
| pt_005.png | Down3后Edit高亮 | `7024ef338770923e559d648fc3368ccf0e0e84e7471255be217353eb98fc51ac` |

20张唯一host＋6张guest共26张，都与本第七原Pi JSONL解码image的SHA匹配，当前nonce／模型／审核一致。owner自有队列22包均submitted：Launch1、App1、Shortcut5、Capture Click12、CloseX1、WaitExit1、Stop1；没有外部提交helper或第二控制连接。

### 实际轮耗：落盘时间与指定模型读图时间分开

原会话中每轮把 `send` 和 `readStep`分别作为codemode调用，形成每轮六次模型往返。下表UTC均为2026-11-13；落盘列来自原 `guest-after.json`，实际读回列来自原JSONL对应toolResult。落盘早于实际读图，不能把前者写成模型已验收。

| 客体 | guest-after记录 | 模型实际image回执 | 距前次实际读图／秒 | 六次文件工具合计／秒 |
| --- | --- | --- | --- | --- |
| 启动页 | 01:04:14.272826 | 01:04:43.414 | 首轮 | 启动准备不同，不作六次比较 |
| 板图 | 01:08:56.885496 | 01:09:34.348 | 290.934 | 1.208 |
| Block | 01:12:45.751825 | 01:13:16.876 | 222.528 | 1.206 |
| Current | 01:16:42.610169 | 01:17:16.301 | 239.425 | 1.215 |
| Delete | 01:20:51.304939 | 01:21:30.977 | 254.676 | 1.193 |
| Edit | 01:27:47.061235 | 01:27:53.577 | 382.600 | 1.203 |

正常三轮Block／Current／Delete对应可观测assistant生成区间合计221.115／237.995／253.261秒；每次readStep本身约0.25–0.33秒，两调用间经常约37–55秒。文件审核＋packet写回到owner提交0.016–0.108秒，提交到原driver complete 0.858–8.943秒，complete到实际图像回执6.510–51.713秒；这些阶段存在重叠，不能简单加和。可观测生成区间包含提供方、传输和调度，不能据时间戳拆成内部token计算。

原JSONL第2400行／记录 `ee89ba4d` 在 **01:23:15.022** 保留 `deng API error (413): Request payload is too large`；第2402行／`23be93bb`在 **01:26:55.785** 为compaction，二者相隔220.763秒。Down3后host在此前已实际读，本轮Capture打开在恢复后才发，没有重发Down3。此额外间隔解释Edit轮显著变长的一部分，**不是原程序消费慢或菜单失效的证据**。01:27完成第六轮后，按本槽实际耗时，余下至少八轮不能可靠在本段业务截止前做完，原Pi主动停止；原45–50分钟只是第六估计，不构成保证。

### 正常退出、保全与下一步边界

当前host已实际确认正常X坐标，原driver在发前再次核精确目标，唯一X在01:29:22.920187 complete。以下创建身份的PID／原HANDLE／FILETIME／映像以及适用的Popen identity逐项匹配，原等待均返回0：

| 原等待对象 | PID | UTC退出回执 |
| --- | --- | --- |
| 目标／driver原Popen | 2020 | 01:30:04.028500 |
| 控制服务／driver原Popen | 51344 | 01:30:25.384532 |
| driver／owner原Popen | 46828 | 01:30:25.394738 |
| owner／原.NET Process持柄WaitForExit | 43356 | 01:30:25.4071037 |

owner提交线程01:30:25.393135记录joined、五秒内完成、error null；observer join为真，无stopped-error。外层隐藏PowerShell自身不由这四个wait外推。原事故包400、原安装99、本槽runtime/pt99与input1、既有EX-001／004／005／003离线证据基线和六旧conf摘要均不变；无NEWFT.PCB、编辑、报告或保存输出。不宣称所有旧槽可变日志拥有完整前后基线，也不改旧事故或第五wait缺口。

本树 `.local-analysis/ex-003-live/seventh-live-audit.json`、`seventh-latency-audit.json`保留逐图原会话记录、原链身份、集合摘要及阶段时序；父独立证据在 `main-2/.local-analysis/config-path-incident-20261112/seventh-parent-final-audit.json`、`seventh-parent-latency-audit.json`。时序脚本首次终端汇总因初始只读步骤没有对应send、空值参加min而TypeError，完整报告已先排他写出；修汇总过滤后只读原报告复核，原失败回执保留，未覆盖报告或重做现场。一次rg命令引号错误也只影响离线搜索。

协调方要求先只读核“已看图审核＋唯一packet投递＋有界等原动作完成＋新图read”能否合为一次codemode，减少模型往返；**仍须每键三个显式观察决策，看到Capture菜单后才点，不能自动视觉替代或预排下一键**。当前codemode文档说明QuickJS没有timers／Node／文件系统，已暴露工具无独立纯文件wait；等待能力边界随后由父独立核本机Pi1.5.2安装二进制（SHA `40a062bedd75767e2c3c889265de7c83d64a0ba55c74b60243c2453d97cffd85`）内嵌共同工具执行层：明确 `windowsHide:true`／`detached:false`／stdio pipes，工具创建的原child由 `await waitForChildProcess(child)`等待；PowerShell适配直接委托该执行层。父完成同进程100ms纯等待／JSON输出烟测，无额外子进程或桌面API。证据 `main-2/.local-analysis/config-path-incident-20261112/pi-hidden-shell-implementation-audit.json`。据此只批准后续离线验证短时隐藏PowerShell只读等待适配，限制10–15秒／工具timeout不超过20秒，仅读本新槽精确packet结果／新step完成和nonce；pending不重发，不GUI／原目标调用／常驻helper／新连接，也不据隐藏标志宣称全机前景绝无其它干扰。父审下一方案前不生成候选／GO，不复用第七；GUI Up环绕、Status文件名和八计数、完整配置继承仍未知。

<a id="single-step-file-wait"></a>

## 单动作文件等待适配：25项与真实codemode无GUI烟测

原协调Pi沿原Task／Dispatch授权此最小离线实现，随后用户要求主Pi新对话交接；原worker会话、指定 `deng/gpt-6.1-sol / high` 和8小时总截止保持，**新协调审阅前没有新候选／GO／现场**。本节只验证当前图审核、单包队列、短时文件等待和新图读回能否在同一次codemode完成；不是Up／Status实际验收。

QuickJS自身没有定时器，不能假设 `setTimeout` 或无工具Promise会等待。实际本机 `C:/Users/rikideng/scoop/apps/pi-coding-agent/1.5.2/pi.exe` 为129055232字节，SHA `40a062bedd75767e2c3c889265de7c83d64a0ba55c74b60243c2453d97cffd85`，与父证据相同。本树又从原二进制精确偏移读取2802／456字节，逐SHA及UTF-8全文核父提取片段：`createLocalShellOperations`在126367285，显式 `detached:false / stdio:pipe / windowsHide:true`，持原child并 `await waitForChildProcess(child)`；`createLocalPowerShellOperations`在126487036，直接委托该执行层。**这是该安装实现和本次纯文件烟测的证据，不保证全机绝无其它前景干扰**。没有修改／安装Pi、换模型、另开worker或控制连接。

[legacy_file_step.js](../tools/legacy_file_step.js)提供 `createLegacyFileStep({tools,text,image})`，返回单次 `sendAndRead(options)`；[Wait-LegacyFileStep.ps1](../tools/Wait-LegacyFileStep.ps1)只通过本机内置 `tools.powershell` 被调用，命令不含窗口／桌面／进程API，也不启动额外子进程。其Stopwatch默认10000ms、上限15000ms，轮询间短sleep默认250ms，外工具timeout20秒；没有常驻helper、无限忙轮询或借桌面工具延迟。

在任何审核或packet写入前，JS先用纯read核：slot是等待脚本所在repo的 `.local-analysis` 后代，脚本只能是同树 `tools/Wait-LegacyFileStep.ps1`，拒绝点路径穿越；`live-plan.json.slot`、Task／Dispatch／session与当前state一致；该PS与同树 `tools/legacy_file_step.js`都在 `plan.frozen_files` 中唯一列出有效大小／SHA。**原包续等也先过此归属门**。新包再比当前state与原observation、要求模型提供已实际看过每种当前原图的观察，才写原格式review与唯一packet；不直接写inbox，owner／原submit的真实摘要、图片回执、隔离、GO、禁重放及排他x门保持。

等待端只核这个包的 `.json/.submitted/.rejected`、owner结果、预期序号和动作名的complete、精确新state及原observation；新nonce必须不同。读取包使用共享ReadWrite／Delete句柄，允许owner原rename，不能用读取锁阻塞提交线程。它遇现有停止／拒绝文件立即refused，完成后仍旧state／nonce或身份错则error。上限结束为pending；下次只核同一原包继续等，**不重写审核、不重发、不读取旧图**。同名不同包或多个仍存在的版本拒绝覆盖。

ready后JS再核未变化的新state与submitted结果，读该步原native文件必要字段及每张新host／guest PNG，并真正调用原 `image()`返回本Pi；这里只输出本目标PID的窗口摘要，不做桌面查询。**调用到此结束，不为新图生成审核或决定下一包**。模型必须先实际看本次返回图，下一次调用才给Capture打开／截图项／命名键之一。这样预期把每键六次分离往返减为三次，保持每键新host、Capture菜单新host、guest实际read的顺序；不能由25项合成测试推断实际场景耗时或成功率，仍按实际时刻和原截止停止。

真实PowerShell文件测试10项与JavaScript合成IO测试15项共**25/25**通过，无skip：ready且只读、延迟完成、300ms超时pending、拒绝、旧state、包／新state错误身份、旧nonce、同名重复、已停止；另覆盖新图不预排、续等不重发、无实际观察零写、等待工具错误、超限、树外slot／计划不符／未冻／错树脚本及续等归属门的零写。测试分别为 `python -B -m unittest discover -s tests -p test_legacy_file_step.py -v`、`node tests/test_legacy_file_step.js`；Node使用本机已有nodejs-lts，不安装依赖，未重复无关32／46项或Qt构建。

首次真实PS10项在解析源码前失败，原因是新文件没按仓库 `.editorconfig` 保存为UTF-8 BOM／CRLF；`validation-first.json`完整保留，JS当次10项通过。规范编码并为两个未来冻结适配器加 `.gitattributes -text` 后，PS10通过；补父指出的写前归属门及rename读取细节后，PS10＋JS15再次通过。原失败不覆盖，未把解析失败写成文件等待成功。

最后在**当前真实codemode／内置tools.powershell**中，用明确无GUI合成计划（含两个真实源码摘要）续等一个已经归档的假包：原工具return0／0.4秒，脚本 `ready / elapsed_ms=150`，新step／nonce通过后，原read和image实际返回71字节2×2 PNG，source SHA `77a06fb952117f359052f30f2c53d2f5f1a272ecd9e872db603158404e265399`；`packetWritten=false`，没有新packet、原程序、owner、GO或桌面控制进程。它验证真实适配工具可等待并读图，**不是原owner投递或真实按键消费证明**；初次补归属门前的独立烟测也保留。

本树证据 `.local-analysis/ex-003-live/file-step-adapter/`：`validation-first.json`、`validation-ps-bom.json`、`validation-plan-gate.json`、`source-review.json`、`codemode-smoke-result.json`、`codemode-plan-smoke-result.json`，以及唯一合成文件夹具；原Pi JSONL保留命令／exit／ready与实际2×2 image。当前PS源码6298字节／SHA `5d862ad11253dfd994abceefec3baa036eddf906b60aad6b89da3426fd1705cf`，JS10315字节／SHA `7c9fcc578e8f7dabf5ab8be9be8d98e1fd79f925235b49ae0fe339459fe67124`。下一真实候选还须把两个适配器列入真实冻结集合，沿原生成／隔离和新协调父审GO流程；本实现没有修改旧七槽、旧GO或完成条件。

新协调审阅25项后，授权准备全新第八候选。准备器新增显式 `--named-status --file-step-adapter`：仅此组合将同树JS／PS两项只读来源加入新计划；未选命名方案而打开适配器在生成前拒绝，默认方案不加入二者。新命名状态测试由8项扩为10项并全部通过，无skip；新增用例核两来源唯一列入、真实大小／SHA、原driver／gate／submit字节与未启用方案一致及最终语义门。真实冻结预计由28增至30项，合成目标与Python同路径去重为29项；实际以候选核验为准。此次只改准备器和测试，不修改已审控制工具、两个适配器或旧槽目录；旧计划引用的共享准备器源码会随新提交更新，不能声称旧完整冻结集合摘要仍全相同。准备器修正先独立交付，再由新协调核第八完整计划／原件和零现场状态，GO前不启动。

<a id="eighth-status-conclusion"></a>

## 第八有限实机结论：SYN1.PCB、八项计数与正常退出

2026-11-13，原Pi `01a1cb98-e57e-75d0-9b06-c40a941eaaf0`／`deng/gpt-6.1-sol / high`，Task `task_db06ca9d4229`／Dispatch `ctx_ed7b7e9ec944`，在准备器修正 `4dc19845e997f4e2241204aa72fda4a386bd4fc6` 上只生成一次 `candidate-eighth-status/slot`。审阅Pi `01a1d2a5-5798-745c-bb3b-fa3af5b3ac16`独立核完整plan／配置／30冻结／99runtime／1input／原件及七旧场景后，排他签GO **02:27:07.913678–03:27:07.913678，03:20:07.913678起仅收尾**。实际02:28:13核原会话、模型high和当前时刻，真实 `-File -Detach -PreflightOnly` 返回allowed后，从唯一入口Detach启动；没有refresh、第二目标、常驻helper或第二控制连接。

plan SHA `856a20de794a5d239689aee5c151d3d4038070a3741c84a7a27279c6883b730c`，conf SHA `dffab58083b64deacfdac608fbc901e7890b5b25c0073d4dccc80f6478a97507`。两个适配器及原owner／driver／gate／submit都在实际冻结集合，后者沿已审原字节。**本次完成固定新场景的GUI工作文件名／八计数、Information首行Up后的Status高亮、Status Esc返回及正常四链退出；不等于[EX-005](exploration-backlog.md#ex-005)完整配置继承或[EX-003](exploration-backlog.md#ex-003)的IME／队列／INT33条件闭环，两个事项与原Task保留。**

### 同槽日志、查询与真实GUI状态

七CONFIG实际输出仍为：`config`仅帮助，AXTYPE逐字列本第八C／D挂载和七查询／目录／PT命令，属性为 `opengl / vgaonly / fixed 10000 / 16 / 本第八captures绝对路径`。同次early stderr明确加载本第八SYN1.conf、cwd为本第八runtime/pt以及 `DOSBox-X 2026.10.01 Commit b6abbd5`。独立日志记录七次config执行，再PT、GRAPH／MNU／KEY／PAD与启动Enter后的 `file open command 2/0 file SYN1.PCB`。日志中的打开请求不能单独代替GUI验收；本次再由Status原图交叉确认。

隔离runtime没有TRAXEDIT.DFT，原安装DFT及输入保持不变。日志仍保留 `C:\PT\TRAXEDIT.DFT` 及后续拼接路径的打开尝试；没有据“尝试”宣称文件成功加载，底栏参数也不解释为默认FT编码。合成SYN1输入180字节、SHA `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`；五条FT只作输入结构对照，下面计数是原Pi直接读新Status PNG的独立记录。

| Status字段 | 本第八GUI实际值 |
| --- | --- |
| Work File Name | `SYN1.PCB` |
| Arcs | 0 |
| Components | 0 |
| Fills | 0 |
| Holes | 0 |
| Pads | 0 |
| Strings | 0 |
| Tracks | 5 |
| Vias | 0 |
| Library File／Current Path | `TRAXSTD.LIB`／`C:\PT` |

### 逐键观察、单Up和Esc边界

Launch的新host最初仍是DOSBOX-X初始化标题；文件等待返回ready只表示本次动作证据发布，**不能当作PT初始化完成**。原Pi没有猜后续标题，而经原owner队列／原submit额外Snapshot一次，实际读新host／native明确 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms`、PID37196／HWND526400后，App按当下完整唯一标题聚焦。App曾10秒pending；下一调用仅续等同一已submitted包，`packetWritten=false`，没有重写审核或再次投递。该Snapshot不在合一助手接受的业务动作内，沿原队列单独审核、投递、读回，未修改冻结工具。

33兼容样本无失败、原线程join真。首guest是640×480／6155字节／SHA `e473d5d1817063b927ca7493c3920f78b6282ccf4ed70f87badaf9161ad665e6`，实际可辨AUTOTRAX 1.57及LOADED GRAPHICS DRIVER VGA640x480，本帧确无PRESS ANY KEY字样；不补造提示或解释差异原因。唯一startup Enter后，新guest明确红框／短线板图；唯一main Enter后Block高亮，再七次独立Down，每次都实际读新host→新Capture菜单host→新guest，逐图为Current、Delete、Edit、File、Grid、Highlight、Information。

| 本第八关键guest | 原Pi实际image回执UTC | 观察与SHA-256 |
| --- | --- | --- |
| pt_009.png | 02:49:30.484 | 主菜单Information高亮；`21908e8bc31b2678932e0d97498bdc47bcb28a186d2dc74eff0e5f75a07ccd82` |
| pt_010.png | 02:51:21.479 | 确认Enter后INFORMATION／Board Dimensions首行高亮；`3292e5459c8c9aa078c59f2ee8dbd442a29938f400433938e0086ab2f00ce156` |
| pt_011.png | 02:53:18.419 | 唯一status_position Up后，末项Status明确高亮；`82a458eebe83ce57cdbe9d7fc2ecceb0ece37ac34639b829db27f94d1955cda8` |
| pt_012.png | 02:55:07.360 | 唯一确认Enter后STATUS，文件名／八计数如上；5397字节，`2292911137aa442cbc8daf623c43af7ac2f3d3204768cfbdf7e0c10ae03fbe8a` |
| pt_013.png | 02:58:37.496 | 唯一status_return Esc后无菜单板图；`d35bb9242f15c58478c39ac21e252bb613c9a45e1e8fc5ab7420ca1db8a24cf5` |

Status页没有再按Enter，没有报告或SAVE FILE NAME，返回图明确无菜单，所以没用可选menu_return Esc。主机guest区仍黑底白横线，而上述客体Capture清晰；不归因后端或宣称IME修复。共14轮、13个命名键、28个Capture业务Click；每次Capture完整集合差恰一张新640×480PNG，既有PNG不改删。28份采样共**5329样本**，序号连续、精确目标身份一致、API失败0，覆盖各自原RPC发送前至响应后至少100ms；这些观测不等于任意输入／鼠标语义恢复。

### 原始等待链、保全与证据

实际读当前最终host确认正常X坐标，原driver发前再次核精确目标，唯一X于 **02:59:43.313336** complete。以下原创建PID／FILETIME／映像／原HANDLE及适用Popen identity逐字段一致，FILETIME由原文件与Python整数核对，不用JavaScript Number作身份比较：

| 原等待对象 | PID | 原HANDLE | wait0 UTC |
| --- | --- | --- | --- |
| 目标／driver原Popen | 37196 | 672 | 03:00:20.443168 |
| 控制服务／driver原Popen | 3260 | 168 | 03:01:05.033490 |
| driver／owner原Popen | 32440 | 520 | 03:01:05.043388 |
| owner／原.NET Process持柄WaitForExit | 42596 | 2412 | 03:01:05.0555982 |

目标FILETIME为 `134390106270047430`。owner文件提交线程03:01:05.041885记录joined、五秒内完成、error null；observer于03:01:04.818403记录join真。没有stopped-error或门拒绝，不造120秒失败静默；外层隐藏PowerShell自身退出仍不由四个下层wait外推。全部现场链早于03:20:07业务截止结束，后续只离线审计和文档。

**45张唯一host＋14张guest共59PNG**，逐张匹配本第八原Pi JSONL相应步骤的解码image SHA／实际回执，59审核的绑定／nonce一致；重复内容的启动或板图也按本轮具体步骤核，不拿旧同SHA回执代新read。owner队列47包均submitted且只经原submit：Launch1、Snapshot1、App1、Shortcut13、Capture Click28、CloseX1、WaitExit1、Stop1。30冻结来源全部大小／SHA保持；runtime99／input1、原安装99、旧事故包400和七份历史conf保持。生成前后至本次退出，再核旧七个场景包分别739／113／253／206／534／1080／643项完整集合、大小和SHA无变化。此前共享准备器的授权更新只按[显式冻结修正](#single-step-file-wait)记录，不外推旧全部冻结引用从未改变。无NEWFT.PCB／编辑／保存／EX-007。

本树 `.local-analysis/ex-003-live/eighth-status-candidate-review.json`、`eighth-old-slots-before.json`、`eighth-live-audit.json`、`eighth-support-audit.json`及两份audit工具回执保留完整计划、源清单、原图／审核／队列、采样、原等待及GUI转录。既有第七审计工具只参数化扩展到第八，没有覆写第七报告。父独立 `main-2/.local-analysis/config-path-incident-20261112/eighth-parent-final-audit.json`另核全部59图／47包／四wait／线程与原件，父也实际read关键四张客体图；原PNG、日志、JSONL及历史失败均不提交或改写。

### 本次实际耗时与可推广范围

本第八七个Down轮从前一张客体实际image回执到后一张的间隔为 **65.533／84.149／90.880／81.238／89.089／95.112／109.397秒**，中位89.089秒；每轮三个合一业务调用的文件等待／读图合计约6.310–6.607秒。其余区间包含模型生成、调度、说明和消息处理；Status读取后转录／回报再Esc的返回轮为210.136秒，不归为DOS消费慢。本轮原会话没有该段提供方error记录，不改写第七已发生的413／压缩异常。

客体集合落盘与模型实际读图仍分开：Status的guest-after为 **02:55:07.068388**，原Piimage回执为 **02:55:07.360**；返回板图分别为 **02:58:37.222260／02:58:37.496**。全部14轮落盘到实际读图约0.243–0.358秒，体现本次合并调用避免再等一个模型回合的效果；文件ready／单次测得时延都不能推成未来性能或原程序就绪保证。完整双时标和调用区间在 `eighth-support-audit.json`，彼此重叠的原driver／模型／工具时间不简单加和。

<a id="remaining-configuration-plan"></a>

## EX-005剩余配置来源覆盖：最小离线核验方案

本段是第八退出后的**方案与已知来源清单**，没有新运行、配置改写、候选或GO；继续[EX-005](exploration-backlog.md#ex-005)，不另开同义事项。GUI文件名／八计数的缺口已由上节固定场景填补，仍须解释当前固定DOSBox版本的来源选择、默认搜索与多conf覆盖；原Shift+I／IME失败、历史只读挂载成因和DFT默认策略不因这次有限成功消失。

| 已知来源或上下文 | 本次能核定的范围 | 仍不能宣称 |
| --- | --- | --- |
| 固定DOSBox-X EXE／Commit b6abbd5 | argv中的真实映像，SHA `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832` | 版本字符串或几个导入／字符串不能代完整启动实现 |
| 本第八显式SYN1.conf／唯一-conf | 原argv、四路径、early loaded日志、AXTYPE和属性查询一致 | 日志只见一项不等于完整枚举所有来源 |
| 新cwd runtime/pt及隔离profile | 冻结清单及原Popen参数可复核 | cwd内容不能单独推出程序目录／用户目录搜索顺序 |
| 安装配置I、用户配置U、随包英文帮助L | 路径见本文来源表，三者列入本第八冻结且前后SHA不变；I首行2026.08.31、U／L按各原记录 | 冻结为只读输入不等于此次实际加载；参考值不等于有效值 |
| 完整／简版参考F／R | 已有12输入摘要与本机文档定义，复用原报告 | 参考文件本身不是本次加载来源，也不能视作出厂或生效默认 |
| 七CONFIG结果、early stderr和独立日志 | 当前几个有效值、autoexec及已观察的显式加载来源 | `config`只是帮助；`-l`说明为列参数，不能据帮助臆造来源枚举能力 |
| 无DFT隔离PT输入／真实Status | 当前合成板、文件名／计数与日志对应 | DFT尝试不证明成功，底栏不证明原新建FT默认值 |

源代码还显示，本第八原target Popen与控制服务都使用 [service_environment](../tools/legacy_runtime_config.py) 传入新槽 `service-profile` 下的USERPROFILE／APPDATA／LOCALAPPDATA／XDG_CONFIG_HOME及缓存／临时目录。该函数只改变子进程环境，未改系统持久配置。**不能直接把真实用户U路径当成本次目标读取路径；也不能仅凭环境变量断定Windows已知目录API一定使用重定向路径**。**后续静态进展：** 已定位固定PE的Shell32目录API和回退分支，见[路径静态结论](#fixed-config-path-static)；当次API的实际返回及瞬时I/O仍缺，这也是不能把“U已冻结”写成“U已加载／未加载”的原因。

上述离线方案现已有[三阶段默认根](dosbox-default-roots-static.md#final-explicit-and-eight)及[parser／setter／autoexec](#fixed-config-parser-setter)的有界静态结果，复用这些结论，不重做菜单或遍历同一批根。余下autoexec的[初始化消费者](#autoexec-initial-consumer)已核当前文本取样、条目自有复制及`-noautoexec`／`-securemode`本地门；构造入口的[普通启动条件顺序](#autoexec-main-conditional-order)及[聚合／登记边界](#autoexec-generated-vfile-data)已有后续结论；完整生命周期、后续打开对象和DOS实际执行仍缺。下一步先核已打开虚拟文件对象的数据／长度是否另复制或缓存，不展开完整shell。仅给已有静态入口，不补作旧现场的实际执行证明。特殊词法／类型／回调效果和历史实际来源仍保留，不下载新依赖、不运行目标或改conf。确需新材料或实机时先列具体缺口与最小方案，再按现行授权审核；完成条件不因阶段交付降低。

<a id="fixed-config-path-static"></a>

## 新5小时定向静态阶段：用户路径预读与最终回退不是同一阶段

用户新5小时UTC2026-11-13 **03:45:01.1736239–08:45:01.1736239**，08:35:01.1736239起总最后10分钟只收尾，覆盖旧8小时的执行安排而不恢复旧GO。沿原Pi／Task／Dispatch和指定模型high，03:47:24实际核身份、成功工具和干净Git后快进`ebc8a31`并读唯一HANDOFF。本阶段只推进[EX-005](exploration-backlog.md#ex-005)已有来源方案，未启动DOSBox／GUI／控制服务／探针目标，未改配置、旧八槽或原件，没有新候选／GO。

固定目标仍为25836544字节DOSBox-X，SHA `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832`、PE32+ AMD64、首选基址`0x140000000`。本机材料盘点限当前工作树与已知安装／工具目录，没有据未找到本地同版本源码或数据库声称全机不存在。REA实际session未开目标，Ghidra12.2／JDK21不满足当前REA的12.1.x／JDK25门，IDA／Kuna未配置，Hopper不支持Windows；诊断保留，没有升级、安装、下载、改注册或另派agent。转用已装r2／rabin2 6.2.6（commit06a7c9d）及Capstone做定向原字节分析，没有全库自动分析。

当前Python为3.15.2；**实际模块`capstone.__version__=5.0.7`，distribution metadata=5.0.9**，两个字段有差异，不能混称。原先两次状态文字沿旧记录／单字段更正均保留；现在同时绑定模块路径、模块SHA `94571d1314355e261aff0ddfc94985fe8761232ddff6874181fd21efa9fab47f`、native DLL7576576字节／SHA `76958e18380023a68fd1714fa2e01c594cc6db1955a07ad6937b66e66dc5d6c3`及API `(5,0,1280)`，未改依赖。

### 原PE锚点与正常入口守卫

rabin2实际提取完整692项导入并分类留为`E-triage-imports`，保留PE节、字符串、原失败和版本诊断；导入／字符串只作锚点，不代实际调用。初次分类未处理JSON顶层包装而失败，修后复用已成功解码缓存，未重跑四个产出；该次子命令stderr未单独留存，不宣称无警告。另一次截断JSON预览解析失败、一次Windows glob及状态命令智能引号解析错误也保留原回执，均为离线工具使用错误。

下表VA为首选镜像地址，RVA及原文件偏移另列；不能当作某次ASLR运行地址。`checkpoint-path-chain.json`核28点原bytes／映射，`entry-guards-and-clear.json`补23个入口／初始化点。已装r2只解11个关键小范围，28原字节点、14条直接call／条件跳转目标及Shell32 IAT地址交叉核过；r2的未应用重定位HINT保留，只核所列原文件点，不冒称全部引用已解析。

| 指令锚点 | VA／RVA | 原文件偏移 | 原字节 |
| --- | --- | --- | --- |
| 启动用户目录调用 | `0x140834a22`／`0x834a22` | `0x833e22` | `e829232200` |
| 启动首次用户路径解析 | `0x140834aa6`／`0x834aa6` | `0x833ea6` | `e8258d2500` |
| 首次未解析且路径非空后序列化入口 | `0x140834af0`／`0x834af0` | `0x833ef0` | `e8bb6c2500` |
| 随后才检查显式列表 | `0x140834b83`／`0x834b83` | `0x833f83` | `e87803b3ff` |
| 第二轮显式逐项解析 | `0x1408360ac`／`0x8360ac` | `0x8354ac` | `e81f772500` |
| 显式失败后目录前缀重试 | `0x1408360e4`／`0x8360e4` | `0x8354e4` | `e8e7762500` |
| 非空跳默认候选 | `0x1408365c3`／`0x8365c3` | `0x8359c3` | `7552` |
| 目录API调用一 | `0x140a56bbe`／`0xa56bbe` | `0xa55fbe` | `ff1554624400` |
| 目录API调用二 | `0x140a56bec`／`0xa56bec` | `0xa55fec` | `ff1526624400` |
| 赋零长度字符串 | `0x14081e74b`／`0x81e74b` | `0x81db4b` | `e840d992ff` |

入口`0x1408347ab`构造Control对象，`8347c8`保存同一全局指针，`8347e0`调用参数解析；`8347e7`仅在AL成功时转正常启动，失败清理返回。构造器先令RSI为0，向`+0x178/+0x180/+0x188`写零，覆盖defaultconf、userconf及若干前置特殊开关；单独conf分支只向`+0x108`追加32字节文件名元素。**结论限普通单conf正常继续、未走前置特殊开关分支／异常退出的控制流**：初始化及目录构造通到`834aa6`，其中没有因显式列表非空而跳过首次用户路径解析的分支。不能只按地址先后称所有组合／失败路径必经。

### 平台用户路径及两轮解析的已证部分

正常启动`834a22 → a56d50 → a56b70`：辅助范围通过原IAT `0x140e9ce18`调用 `SHELL32.SHGetSpecialFolderPathA`，先传目录常量`0x1c`，API失败或结果首字节为空时再传`0x1a`；二者无有效结果后传字符串windir给后续函数；`0x140a56c0f`测试返回指针，`cmovne`仅在非null时选该指针，否则使用原字面`c:\windows`，未见对非null空字符串另作回退判断；长度允许时拼`\Application Data`。这里记录固定代码的参数／分支，不把该次Windows API返回值补出来。`a56d50`以不创建模式调用该范围，然后拼`\DOSBox-X`及尾反斜线；`a56e30`给出`dosbox-x-2026.10.01.conf`。`a56e80`是传创建标志1的另一包装，不能把两个包装混为同一调用。

`834aa6`对上述目录与版本名组合调用解析器`a8d7d0`；若已打开／登记文件表为空且路径非空，`834af0`会进入序列化范围`a8b7b0`，其中已见配置头／版本输出、逐Section处理及创建父目录后打开输出的路径。**这说明固定代码存在显式conf列表检查前的用户路径预读／可达写出分支；不是第八当时每次IO的trace。** 第八profile的版本conf在本次迟后只读观察中为124891字节，SHA与真实用户U同为`0d19342e...d38`，创建时间与启动相近；这些相同字节或时间不证明复制、生成者、当时加载次序，旧场景不再运行补证。

随后还存在命令行／默认路径的预解析和工作目录处理，再清文本与解析文件表，才到`836011`最终显式列表循环。最终每个conf先用原名解析，失败后`8360e4`再试平台用户目录前缀；最终默认候选循环`8365b0`每次先查`+0x50`已打开／登记文件表，非空就跳剩余候选。因此，**最终显式成功后跳过默认候选，不等于启动从未读取用户配置**。这部分现由[已父审默认根报告](dosbox-default-roots-static.md#final-explicit-and-eight)列明条件与顺序；本文不重复，也不把静态条件表补成历史执行记录。

### 清文本不等于已经证明恢复全部Property默认

`81e6c0`需按CHAININFO展开三个范围，合计44条，而不是只读首8条就当完整函数。原RTTI字节分别为Section、Section_prop、Section_line；所见控制流遍历Section链，对prop的`+0x48`或line的`+0x38`字符串以长度0赋空。该范围没有直接遍历Property向量并恢复default_val的证据，**不能把它命名成已证恢复全部属性默认**。后续字段／写值／Line追加的有界结论见[parser与setter阶段](#fixed-config-parser-setter)；全部回调、极端词法及特殊类型组合仍未闭环，不把部分机制扩大为全输入／全模块保证。

证据统一本树 `.local-analysis/ex-005-config-source/`：`rea-session-initial.json`、`triage-evidence.json`及四个rabin2缓存、`xref-index.json`、所选`function-*.json`、`checkpoint-path-chain.json`、`entry-guards-and-clear.json`、`decoder-crosscheck.json`和原工具回执。每个关键指令保留原字节、VA／RVA／偏移及unwind范围；反汇编／推断不冒充对应C++源码或实机观测。完整来源／覆盖仍在[EX-005](exploration-backlog.md#ex-005)，[EX-003](exploration-backlog.md#ex-003)旧IME／队列／INT33未知不变。

<a id="fixed-config-parser-setter"></a>

## Parser返回、Property写入与autoexec合并：有界静态结论

本段接续同一固定SHA原PE研究，继续[EX-005](exploration-backlog.md#ex-005)，只读原字节及既有缓存，未执行目标、GUI、窗口查询或配置变更，没有候选／GO。用户授权已延长到UTC2026-11-13 **12:45:01.1736239**，12:35:01起总最后10分钟只收尾；没有恢复旧八槽GO。当前只交parser／setter／autoexec的已证机制；完整默认根／两轮守卫复用[已父审根报告](dosbox-default-roots-static.md#final-explicit-and-eight)，PT命令行／工作文件候选复用[DFT报告](pt-dft-load-static.md#working-name-and-cli)，不重复研究或把已证部分继续笼统列为未知。

### 文件打开登记与配置项接受分开

Control `+0x50`在旧检查点曾简称成功表，**准确含义为已打开／登记文件表F**。解析器 `0x140a8d7d0`先构造输入流；打开后的状态按mask `0x6`分流，非零边在 `a8d949`正常返回AL=0，未登记；通过边在 `a8d950..a8d9b4`已追加文件名，然后才逐行读取。AL=1或F非空不能推出所有节／属性值有效。

逐行调用后 `a8db0e/a8db13`也按mask `0x6`终止循环；该边经统一收尾，在 `a8e229`置AL=1。**此处没有把正常EOF与触发同一位掩码的后续读错误分别返回**；未实际注入I/O故障，不把1写成完整无差错解析保证。单行handler返回false不会作为文件false传播，可能另存extra文本，未使已登记文件移除；因此无效属性本身不触发主流程的原名打开失败／前缀重试，也不会使默认候选因该行继续搜索。抛异常／进程退出与上述正常返回边另列，未冒称全部错误集合。

```mermaid
flowchart TD
    A[打开配置输入流] --> B{打开后状态与0x6}
    B -->|非零| X[返回0：未登记]
    B -->|零| C[先登记文件名到F]
    C --> D[读取下一行]
    D --> E{读取后状态与0x6}
    E -->|非零| Y[共同收尾并返回1]
    E -->|零| F[节匹配和行handler]
    F --> G[接受、拒绝或extra文本]
    G --> D
```

### 已注册对象与写值层

Parser取节名后经 `a8d5f0`搜索已有Section对象，正常行调用其虚表 `+8`输入槽；不是每个文件／节头都重新构造默认对象。Section_prop输入在 `a8afd0`拆第一个等号，规范化键和值、处理配对外引号，再查已有Property名并调用其虚表首槽。辅助 `a92560`按原五字节集合 `20 0d 09 0c 0a`处理前后空白；未据此宣布所有INI词法、locale或非ASCII名称规则都已核完。

原MSVC TypeDescriptor／COL自指RVA／虚表把Section_prop槽 `+8`接到 `a8afd0`、Section_line槽接到 `a8b6f0`。另定位八个Prop类型；以下当前Value `+0x40`、回退／默认Value `+0x70`按所见用途命名，不冒充恢复了原C++成员名。Value赋值辅助 `a869a0/a86a30`核到类型及整数／布尔等字段复制、字符串另复制的路径。

| 路径及前提 | 本层已见写入与返回 | 不能统一解释成 |
| --- | --- | --- |
| Bool／Int文本转换正常返回false | 包装器在最终写值槽前返回false，本层没有经该槽写当前Value | 所有false都保留旧值 |
| Bool／Int输入为空 | 先从本Property回退槽生成文本，再走类型转换／校验 | 一律忽略、保持空或无条件重置成功 |
| 公共写值槽校验接受 | 将传入Value复制到当前槽并返回1 | 所有模块／回调最后一定无其它改变 |
| 公共写值槽允许值校验拒绝 | 将回退Value复制到当前槽，再返回0 | 返回false就没有状态变更 |
| Integer无建议列表且有有效上下界 | 转换后越界取近端边界写入，返回1；双界-1另有无界分支 | 所有越界值都保留旧值或都回默认 |
| String／Path包装 | String有空串／建议列表特判；Path先经公共写值，空输入又清独立路径字段 `+0xc0`并强制false | 所有Property共用一种空值规则 |
| Multival／remain | 首槽三指令叶片段转发 `+0x28`槽；父文本先处理，再逐子项，失败可调用从子回退槽拼文本再写父Value的辅助范围 | 整行原子回滚、父子状态始终一致 |

Setter返回true后，Section_prop还遍历 `+0x28`回调列表；false路径不进该成功回调边，但当前Value可能已被改成回退值。这里只核写值与派发，不穷尽回调效果。若后续没有另一写入或回调改变，未出现的新键不会自动清现有Property当前槽；上节清文本作用于Section字符串，不能拿来证明恢复所有Property默认。实际跨轮来源须与根报告的路径／清理条件组合，不能把单属性赋值层直接当历史最终运行值。

Bool局部转换比较中可见 `0/disabled/false/off`与 `1/enabled/true/on`分支；入口抽取、大小写／locale、尾随字符及数值溢出没有穷举，不套用其它程序常见拼写作承诺。Double／Hex专有边界、Path完整规范化及Multival缺项／余项／子值一致性仍是精确停点。

### autoexec在字符串层追加，阶段清理另计

初始化片段 `3c40d3/3c40e1`以autoexec名调用 `a8d080`；构造写入虚表 `0x14151dff8`，其输入槽是 `a8b6f0`。对同一已注册Section_line对象，已有文本长度非零时先追加原单字节LF `0a`，再追加本行；空对象首行不加该前置LF。辅助 `2f8170`快路径在旧尾写入并累加长度，扩容路径先保留旧内容再在旧长度处写输入，因此这里是追加而非替换。

普通文件读取循环及最终显式列表没有直接逐文件重建／清空Line的步骤；同一对象未经过清文本或其它改变时，后文件同节内容接到已有文本后。Parser行规范化与跳表仍影响哪些行送达：原表 `a8e26c..a8e2d8`单独按数据解析，不把ret后线性译出的乱码作指令；空行／#前缀与节头分支已列证据，异常前缀、未知节和畸形输入没有作完整健壮性结论。

**不能把同一对象追加推成整个启动从不清文本。** 已父审[工作目录及延后用户配置守卫](dosbox-default-roots-static.md#cwd-transition-and-userconf)分别列A3、B6、偏好保存、U2／U4的条件：某些边清Line数据和extra文本，延后用户解析登记后也有保留文本再进入最终E列表的路径。本文只给字符串层和已核直接控制流，不用最后会清一次覆盖所有分支。

### 原字节锚点、验证与剩余

以下VA沿用固定SHA及首选基址 `0x140000000`，不是某次ASLR现场地址；机器可读证据另列每点RVA、原文件偏移、原bytes及unwind／CHAININFO范围。Multival无unwind入口只读首jmp前3条，其后目标由原六槽虚表定位，不猜完整函数。

| 机制 | 首选VA及已见控制点 |
| --- | --- |
| 打开／行前登记 | `0x140a8d8a5`测试mask6；`0x140a8d9a2`推进F.end |
| 读取终止／文件返回 | `0x140a8db0e`测试mask6；`0x140a8e229`为`b001`，AL=1 |
| Property派发／回调 | `0x140a8b287`调用首槽；`0x140a8b2a3`调用成功回调 |
| 公共拒绝／接受写当前槽 | `0x140a850df`／`0x140a85153`调用Value复制辅助 |
| Integer边界写入 | `0x140a87f7e`写截断后的Value，`0x140a87f88`返回1 |
| Line追加 | `0x140a8b718`追加LF；`0x140a8b731`追加输入 |
| Multival顺序 | `0x140a898d8`先写父Value；`0x140a89c3b`后调子setter |
| Multival回退表示串 | `0x140a8923c`再经父对象写值槽，不是旧值快照恢复 |

本树 `.local-analysis/ex-005-config-source/parser-setter-proofs.json`于06:08:59核 **21份来源／3107缓存行、58关键点、12份虚表记录**的原PE字节／映射，工具返回0；缓存行含内嵌表，只作完整性计量，不等于3107条可达指令。材料含Section／Property／Multival虚表、输入handler／写值／Value复制／append／规范化及原注册片段，本文已展开关键条件，不要求远端读者仅凭忽略路径推断。

新增r2小窗口汇总在已产stdout／stderr解析后，因窗口未覆盖某关键地址报KeyError；保存 `parser-critical-stdout.json-stream`、stderr及 `parser-setter-decoder-tool-result.json`原失败，本提交**不声称58点已全部独立r2复核通过**，也没有为此重跑全程序。此前独立r2的28点／14直接目标仍只按前节范围成立。首个无unwind完整函数请求的拒绝、codemode语法／文档拼接失败且零工具调用也保留；未改目标、旧报告或原会话。

协调d38b独立重算PE节映射，复核上述21源／3107缓存行、58关键点、12组虚槽和27连续窗671条指令，另核Bool辅助217行及字符串原bytes、外引号和空白处理上下文。父只读解析原r2输出的27个数组，共671个地址，覆盖58点中的57点，唯一未覆盖为 `0x140a8dfab`；这与原KeyError相符，不把原汇总改成通过，也未重新执行r2。父证据为协调树 `.local-analysis/config-path-incident-20261112/parser-setter-d38b-parent-review.json` 和 `parser-setter-d38b-delivery-review.json`，原失败不覆盖。

本段有界交付完成，不结[EX-005](exploration-backlog.md#ex-005)或[EX-003](exploration-backlog.md#ex-003)。后续[初始化消费者阶段](#autoexec-initial-consumer)已补当前文本取样、自有复制及本地开关门；其[普通启动条件顺序](#autoexec-main-conditional-order)和[聚合登记边界](#autoexec-generated-vfile-data)已有后续结论；完整生命周期／DOS执行、实际Shell32返回／历史瞬时I/O来源、全部回调效果和上述特殊词法／类型边界仍保留。需要新材料或实机时另由协调界定方案与授权。

<a id="autoexec-initial-consumer"></a>

## autoexec初始化消费：当前文本、自有复制与noautoexec守卫

本段为[EX-005](exploration-backlog.md#ex-005)的有界离线接续：沿原Pi／Task／Dispatch，从06:55左右的检查点开始，复用前节固定DOSBox-X SHA与缓存，仅新增本树 `.local-analysis/ex-005-autoexec-consumer/` 材料。未运行DOSBox／PT／GUI或查询窗口，没有配置写入、候选／GO，也未重做根、DFT、菜单。**本段核到消费者内部采样／复制和本地开关门；完整调度上游尚未闭合，不能把字符串追加直接当作已经执行。**

### 注册常量不是已证的消费调用

既有注册片段 `0x1403c40cc..3c40e1`将R8置为 `0x1403a8cb0`，再按autoexec名调用Section_line构造入口。该R8目标原bytes为 `c2 00 00`，只有 `ret 0`：含义是返回时零额外栈清理，**不是设置布尔返回值0**。这里没有显式读取或复制Section文本，不能仅凭注册参数存在就把它命名为真实消费体。

本段另定位到带 `Allocating AUTOEXEC.BAT emulation`字面的范围 `0x140abe7c0..abe8f0`：其全局对象指针非空时跳过分配，否则按autoexec名取既有Section，调用 `abe210`构造范围并保存对象。另一路 `0x140833ab0..83411d`内也有 `8340a3`直接构造及 `8340a9`保存；因此前者不是已经证明的全部生命周期唯一入口。

### 构造时取样与本地跳过条件

命令行缓存的正常匹配分支明确给出：`83179a`比较noautoexec，`8317b1`写Control `+0x17e=1`；`8318ab`比较securemode，`8318c2`写 `+0x17f=1`。本段不扩securemode完整权限语义或所有参数组合。

在合法既有Section_line对象的构造路径上，`abe210`将Section指针存入对象，`abe2bb`先将securemode字段保存到R13；随后有 `+0x193`守卫的可选前置辅助调用，返回边会重取Control指针。本段只记这个先后，不推该辅助是否改变配置、也不展开全部prerun组合。

`abe2db..abe2e6`从传入Section的 `+0x38`字符串选内联或堆缓冲，然后才测试保存的securemode及 `abe302`处读取的noautoexec。通过前一项时R13为0，后一比较才等价于要求当前 `+0x17e=0`；不通过则 `abe309`等边跳到 `abe485`，绕过本次Section内容处理。**这个门位于对象分配和字符串元数据访问之后，只跳这段Section文本消费，不等于禁止解析Section或停止整个模拟对象。**

构造在正文复制前还存在文本前缀处理；剩余正文非空时，`abe461`复制成局部临时字符串，再于 `abe46f`传给接收对象 `+0x10`处条目的安装辅助 `ab2460`。取样是到达该构造分支时的文本，不是参数解析时冻结的一份配置；保存的17f与稍后读取的17e也不应混称同一时点。本文没有复原完整生成文件模板。

### 安装辅助确有自有字符串，后续执行仍分层

`ab2460`先检查接收条目的已创建标志，正常首次路径置位，再在 `ab2499`把输入复制到该条目 `+8`的自有字符串。当前调用的源是构造器局部临时串，接收存储位于另一对象；不是仅保存原Section数据指针。对象本身仍保存Section指针，后续刷新／重建路径未穷举，不能推出配置变化永远不会再次消费。

```mermaid
flowchart LR
    A[Section_line 当前字符串 +0x38] --> B[构造分支取缓冲与开关]
    B -->|通过Section门| C[局部临时字符串]
    C --> D[条目自有字符串 +8]
    D --> E[后续登记和生成辅助]
    E -. 未在本段闭合 .-> F[DOS读取及执行]
```

安装路径之后的 `a912e0/ab2620`已补[聚合与登记数据边界](#autoexec-generated-vfile-data)，实际DOS读取／执行仍未核。`abe485`起继续读取Control `+0x138`列表等其它来源，该范围不在17e的Section门之内；因此 **noautoexec门不能扩大为所有AUTOEXEC来源都被禁止**。

### 初始化日志、调度缺口与证据

主启动缓存 `8397d3`确有调用 `abe8f0`。但这个包含 `Initializing AUTOEXEC.BAT emulation`日志的51行范围，所见是把带 `AUTOEXEC_ShutDown`名的函数指针送入列表及数值1／12／14／16的注册接口；不能据日志名把它当作分配器已经触发，也未把接口数值套成完整事件枚举。

**后续[BOOT上游阶段](#autoexec-boot-upstream)已补833ab0的直接BOOT调用、动态槽安装与同表派发；[普通启动条件顺序](#autoexec-main-conditional-order)又接上最终解析、VM事件0构造与主桥。** `abe7c0`其它上游／完整生命周期、DOS shell实际读取／执行及原现场瞬时I/O仍未研究；`ab2620`到数据登记的局部结论见[聚合边界](#autoexec-generated-vfile-data)。定向引用结果只作候选，不以线性扫描未返回引用证明调用者不存在；不按函数地址先后推执行时间，不用本段补录第八真实字段或瞬时I/O。

| 本段关键锚点 | 首选VA／行为 |
| --- | --- |
| 注册参数空入口 | `0x1403a8cb0`，原 `c20000`／ret imm16=0 |
| noautoexec／securemode赋值 | `0x1408317b1`／`0x1408318c2`，写17e／17f |
| 构造读取Section字符串 | `0x140abe2db`，Section `+0x38` |
| securemode快照／稍后noautoexec门 | `0x140abe2bb`／`0x140abe302` |
| 临时复制／安装调用 | `0x140abe461`／`0x140abe46f` |
| 条目自有字符串复制 | `0x140ab2499` |
| 初始化注册范围调用 | `0x1408397d3 → 0x140abe8f0`，不代分配触发 |
| 另一构造入口 | `0x1408340a3 → 0x140abe210`，[条件上游](#autoexec-main-conditional-order)已接到VM事件／BOOT链 |

新目录 `consumer-proof.json`于 **07:35:15**逐原PE字节／映射核 **10份输入、912缓存行、35关键点**，13个直接相对call／条件跳转另从原bytes算目标一致，工具返回0；每点保留VA／RVA／原文件偏移、原bytes及unwind／CHAININFO范围。新目录只写本段派生材料，旧缓存只读。候选中与编辑器相关的范围没有作为初始化执行证据，也未深入GUI。

06:59原会话EPROTO TLS握手失败保留；其不完整codemode没有工具执行回执，不能算盘点已运行。实际盘点在07:02:46返回0；预算仍从原06:55检查点计，不因网络错误或换主重计。缓存注释出现空格裁切、反斜杠转义或UTF16显示差异时以原bytes为准，本段未据注释扩展shell命令语义。固定映像未改，未安装／下载／升级依赖。

协调d3c8独立父审复用先前9来源906行／252引用核验，并补核注册片段6行，合计10输入912缓存行、35关键点及13直接相对目标，原PE节映射／bytes／解码一致；另从PE异常目录核10个运行时函数范围，短字符串赋值辅助`14c090`的首范围原指令只作局部补核，不称全部扩容／异常路径已证。父证据为协调树 `.local-analysis/config-path-incident-20261112/autoexec-consumer-d3c8-parent-review.json`及`autoexec-consumer-d3c8-delivery-review.json`。父首轮字符串校验对缓存显示作了过强假设，先后在反斜杠、UTF16、`set `尾空格和转义LF处失败，核原bytes后修正派生校验，原失败和缓存均保留。前父检查点简称“ret0”仅指反汇编立即数，不代表已证明返回值为0。

本段按有证范围交付，继续保留[EX-005](exploration-backlog.md#ex-005)、[EX-003](exploration-backlog.md#ex-003)和原Task。后续已核[BOOT调用与槽派发](#autoexec-boot-upstream)，普通启动条件顺序见[主启动连接](#autoexec-main-conditional-order)，完整实际时序仍未核；当前不扩全DOS shell、视频模式、控制适配器、截图或新现场方案。

<a id="autoexec-boot-upstream"></a>

## BOOT路径中的消费上游与动态回调槽

本段接续[初始化消费](#autoexec-initial-consumer)，继续[EX-005](exploration-backlog.md#ex-005)，在原会话中新开约07:51至08:36的有界离线段，限定 `833ab0`上游、紧邻槽分配／安装及必要派发。新增文件均以 `.local-analysis/ex-005-autoexec-consumer/upstream-`等独立名称保存，前段交付和旧缓存只读。**已核定BOOT直接call、同表安装与间接派发之间的静态连接；与最终显式解析的完整启动相对顺序仍有具体缺口，不以地址大小补结论。**

### 直接BOOT调用及条件

原bytes `9e9044:e867aae4ff`直接调用 `833ab0`，位于异常表范围 `9e8ce0..9e90b6`，从该范围起点解码对齐。这个范围含 `BIOS boot SS:SP`及BOOT失败／protected-vm86拒绝字面；这里只据实际分支说明用途，不恢复完整BOOT源码名。

`9e8d20`可跳入拒绝支路，另有 `9e8fe8→9e9096`的异常支路；不能把进入该范围说成必达内核构造。到 `9e9044`返回后仍在 `9e9049/4b`检查AL，AL为0走 `9e907c`错误路径。即使成功调用 `833ab0`，是否真正新建autoexec对象还受前段所述全局对象空门及17e／17f内容门约束，不能说每次BOOT都会再复制Section。

### 动态槽的分配、保留与安装

BIOS构造范围 `9e91e0..9eafdb`在 `9ea81a`检查条目 `+0x70`的已安装标志；非零另走错误支路。首次正常路径置标志及类型值，再于 `9ea832`调用 `14dfc0`。返回AL经零扩展作为ECX，并保存到 `rsi+0x78`；`9ea84b`将 `9e8ce0`送入RDX，`9ea852`调用 `14ff20`，R9指向原 `BIOS BOOT`字面，R8D为1。本段不把这个类型立即量套成未经核验的源码枚举。

| 此链中的槽步骤 | 原字节所见行为 |
| --- | --- |
| `14dfc0`分配 | 从索引1开始，到127；比较表项是否等于 `14ddd0`哨兵，不能误写成寻找NULL空槽 |
| 成功预留 | `14e01a`先把所选表项置0，`14e026`返回索引；耗尽另走错误支路 |
| `14ff20`安装 | 先检查完整RCX小于128，否则AL=0返回；正常路径调用生成辅助后，在 `14ff98`写函数指针表 |
| 本次BOOT项 | 表基址 `0x141812970`，所选索引的项写入 `0x1409e8ce0`；索引取决于当时表状态，不是本段得到的固定常数 |

安装还会处理描述存储并有其余辅助动作，本段不展开全部回调生命周期或生成的来宾指令模板，也不将静态接口路径当第八现场安装结果。

### 必要派发与运行桥

`3a7e90..3a83db`范围中，`3a8077`明确将imagebase送入R15。`3a8339`先调用全局 `0x141813428`中保存的函数指针，再按返回值分流；正值支路在 `3a8351`比较**低32位EAX**与128，随后 `3a836f`使用**RAX**索引同一 `imagebase+0x1812970`表并间接调用。本段保留操作数宽度，不将它改写成对任意64位输入的范围承诺，也未复原前级函数的全部实现。

因此，当这次派发索引等于前述已安装BOOT索引，且表项未被其它路径改写时，同表调用可进入 `9e8ce0→833ab0`。动态索引和这些前提仍然存在；没有观测第八实际索引或触发时刻。另一处表内调用只作为定位候选保留，没有扩展为全部CPU／BOOT路径。

已有主启动缓存还给出 `83be9f→3a8850`。这个11行桥通过 `0x144d592c8`全局运行槽间接调用，返回0时继续调用。无异常表项的短叶 `3a8840`另以显式32字节上限、到ret为止解出三条／15字节：加载 `3a7e90`，写入该运行槽，返回。它证明了一个槽选择方式；其它选择者及具体调用时序未穷举。

### 最终解析顺序的当时断点与后续结论

[最终显式配置循环](dosbox-default-roots-static.md#final-explicit-and-eight)的 `836011`及 `8360ac/8360e4`原名／前缀重试仍沿既有结论。此BOOT段交付时尚缺最终解析到消费的连续启动连接；后续[普通启动条件顺序](#autoexec-main-conditional-order)已补VM事件登记、同步构造与主桥的模型内顺序，保留实际运行及异常／重入边界。

`9ebad4→9e91e0`的普通主启动连接现见下节。其余运行槽选择的实际状态、后续BOOT索引匹配及第八现场触发时刻仍未观测；缓存过滤未直接匹配已知目标不是不存在间接调用的证明。无需为此扩全部BOOT来源、`abe7c0`生命周期、`ab2620`到DOS shell或全部命令组合。

本段 `upstream-proof.json`于 **08:28:31**核6个新定向范围 **2273缓存行**、4个复用main点、3条有界短叶及 **32关键点／11直接相对目标**，原PE字节／映射和目标一致，工具返回0。缓存行不等于全部可达指令。参数化引用脚本曾把9e8ce0报告的scope文字遗留为833ab0；selected_entry与目标计算正确，原报告／回执保留，`upstream-scope-correction.json`另记更正，不覆写旧输出。

协调d3c8读完整43行增量，并独立重算六来源2273缓存行的PE节映射／原bytes／解码及657个直接或RIP引用；另核32关键点、11个含短跳的相对目标、3条15字节短叶和8个异常表范围。安装比较RCX、派发比较EAX却以RAX索引的宽度逐原指令保持，不补全64位范围保证。父证据为协调树 `.local-analysis/config-path-incident-20261112/autoexec-boot-d3c8-delivery-review.json`。父脚本初假设复用点都有rva而KeyError、随后漏计短跳导致计数断言失败，均修正派生校验后通过；原回执及已交证据不改。

研究树在修改本段文档前已干净快进共享 `ffdc15c`；只追加本专题，不改共享待办／HANDOFF／索引。全段零目标／GUI／窗口查询／配置写入／候选GO，无安装升级，原Pi／Task持续，[EX-005](exploration-backlog.md#ex-005)仍保留实际时序及下节所列边界。

<a id="autoexec-main-conditional-order"></a>

## 普通启动条件顺序：最终解析、VM事件0构造与主运行桥

本段从约08:40检查点继续原Pi／Task，继续[EX-005](exploration-backlog.md#ex-005)，新增材料均在本树 `ex-005-autoexec-consumer`内以 `connect-`等独立名称保存，旧交付只读。**固定PE的普通返回图支持 `836011 → 839717 → 83bcc6 → 83be9f`的先后；在已开标志为0且事件0迭代到相应节点等条件下，`9ebad4`的BIOS构造同步发生在该次主桥调用之前。** 这是有条件的静态连接，不是第八现场分支或时刻记录。

### 主登记与同表派发

主缓存 `839717`直接调用 `9ebdc0`。其 `9ec03f`加载 `9eb9f0`到RDX，`9ec046`将ECX清0，`9ec048`调用事件登记 `a8d2a0`，R8指向 `BIOS_OnPowerOn`名。此处是固定的VM事件值0，不是前节分配器取得的动态BOOT槽号。

`a8d2a0`把函数指针放入临时record首qword，以 `0x144caa360 + event*16`选链表记录并调用节点辅助 `a90e40`；后者在 `a90e87`把该qword复制到节点 `+0x10`并链接入表。派发 `a8d3b0`同样选择该表，迭代时在 `a8d45d`通过节点 `+0x10`间接调用。由此核的是同表、同记录偏移的连接，不能仅靠登记日志当作已经触发。

`9eb9f0..9ebb10`包装先检查全局 `0x14504d380`；旧对象非空时调用其首虚函数并传EDX=1，然后分配 `0xf0`字节，按原 `joystick`名查Section，将所得指针传入 `9ebad4→9e91e0`并保存新对象。本段只按原调用和参数记述，不从节名推其它功能，也不展开首虚函数的全部生命周期副作用。

### 事件0的同步入口与标志门

主缓存 `83bcc6`直接调用 `834120..834156`。该13行范围检查 `0x1447f923c`：非0时跳过事件调用；为0时先写1，再以ECX=0同步调用 `a8d3b0`，之后依次派发数值1和2。**两条正常返回路都在 `83414f`置AL=1，所以返回AL=1不能证明事件0实际发生。**

若该标志为0、事件0表中相应节点和函数指针仍在、此前handlers正常返回并迭代到此节点，则调用链为：`834136 → a8d3b0 → node+0x10 → 9eb9f0 → 9ebad4`。这条同步链在该次 `834120`正常返回前完成；后续1／2事件的全部handler行为不在本段穷举范围。

### 普通返回图中的相对顺序

本段用原主范围 `834730..83c881`的6779缓存行建图：指令连续原字节覆盖，550个直接跳转目标另从编码位移计算并与缓存一致；该范围未留未解析的间接jmp或缓存外直接跳转目标。条件分支两边均纳入，普通call抽象为正常返回边，已识别错误退出／抛出点作终止。C++异常重入、longjmp和外部跳入不在这个图中；间接call仍按正常返回假设，不称其实现已全部核验。

从普通入口 `834730`出发，独立按原分支位移重建图，再删除前点检查后点可达性，得到：

| 前点 | 后点 | 原图中后点可达 | 删除前点后仍可达 |
| --- | --- | --- | --- |
| `836011`最终显式循环入口 | `839717`BIOS登记调用 | 是 | 否 |
| `839717`登记调用 | `83bcc6`同步入口调用 | 是 | 否 |
| `83bcc6`同步入口调用 | `83be9f`主运行桥调用 | 是 | 否 |

这里的支配只指**图模型内到后点的路径均先经过前点**。它不依赖初次BFS选出的分支合取是否可满足；BFS的2201行候选及原回执仍保留，不当具体可执行或历史路径。E可以为空，`836011`入口先行也不等于每次实际读取了一个显式文件，更不等于所有Property被接受。

```mermaid
flowchart LR
    P[最终E循环入口 836011] --> R[BIOS登记 839717]
    R --> G[主同步入口 83bcc6]
    G -->|标志0并到达节点| C[VM事件0内 9ebad4构造]
    C -->|其余同步调用正常返回| B[该次主桥 83be9f]
    G -->|标志非0 跳过事件| B
```

合并前节时仍需保留主桥运行槽选择已核派发循环、后续索引匹配且表项未改、autoexec对象空门和17e／17f内容门等条件；满足时，才能把最终解析阶段与后续文本消费按这条静态链相接。中间其它模块、handlers及可选前置辅助的配置读改副作用未穷举，因此顺序结论不证明快照文本只来自最终一个文件或此后不再变化。完整异常／重入、其它生命周期及第八实际槽值／瞬时I/O仍未知。

协调d3c8独立核六新源389行及完整main6779行的原PE映射／bytes／Capstone解码，按原位移重建550直接跳转边，并复算三组删除前点检查；27关键点和12相对目标一致。另建更宽的“全部call均可返回”图，不依赖两个已识别错误函数为不返回，三组后点仍可达、删除前点后均不可达。该稳健性检查仍只属于普通入口图，不纳异常／longjmp／外部跳入或动态改码，也不证明BFS合取可满足。父证据 `.local-analysis/config-path-incident-20261112/autoexec-main-order-d3c8-delivery-review.json`；早期登记329行和事件0短函数／节点复制60行的初审证据保持各自边界。

`connect-proof.json`于 **09:00:56**核六个新范围 **389缓存行**、完整main **6779行／550跳转目标**及 **27关键点／12直接相对目标**，工具返回0；`connect-main-order.json`保留三组删除节点检查，先前候选另存不覆盖。修改文档前已干净快进共享 `6ba542f`，仅据新结论更新本专题旧断点链接，不改共享入口或已交本机证据。本段无目标／GUI／窗口查询／配置写／候选GO、下载升级或会话重启，[EX-005](exploration-backlog.md#ex-005)及原Task继续保留。

<a id="autoexec-generated-vfile-data"></a>

## AUTOEXEC聚合与虚拟文件登记的数据边界

本段从约09:16检查点沿原Pi／Task继续，继续[EX-005](exploration-backlog.md#ex-005)，只核 `ab2620`及紧邻字符串／数据登记接口。**条目和聚合层确有复制；发布的虚拟文件记录却直接借用全局聚合缓冲指针，不另持一份不可变数据快照。** 这里没有运行DOSBox／PT或合成实验，也未进入DOS shell读取／执行。

### 条目顺序与分隔

正常安装入口 `ab2460`把链表sentinel作为位置参数传给 `a912e0`；后者在指定position之前链接节点，因此这一入口是尾插。节点 `+0x10`的字符串由 `14bda0`复制：小串直接放入节点内，大串分配另一存储并传长度加1复制。生成器 `ab2620`从全局 `0x144d02030`的sentinel.next起，沿next向前迭代，随后再复制成局部临时字符串。**聚合顺序是当时的链序**；其它调用者可给不同插入位置，本文不把它扩大成全部来源都按配置文件或调用先后排列。

临时串非空时，长度／offset搜索辅助 `381df0`查找LF及CRLF：LF若已属于对应CRLF则保留，否则经 `4c3100`把该1字节LF替为2字节CRLF。原字面分别是 `0a00`和 `0d0a00`。之后每个节点都通过原格式 `25730d0a00`，即 `%s\r\n`，向聚合缓冲追加一份额外CRLF。

因此，已有末尾换行不会在本段被统一裁掉；空节点只跳过规范化循环，仍追加CRLF。空列表则不进逐项循环，缓冲首字节置0后仍会评估后续登记门。搜索使用std字符串长度，而格式 `%s`使用C字符串语义，不能把含NUL的std字符串全长都当作实际输出字节；此类特殊输入未做运行验证。

### 长度与登记门

每项追加前先求当前聚合C字符串长度 `p`，再取规范化后的临时std字符串长度 `n`，按64位指令计算 `p+n+3`；`ab27f1/7f8`做无符号比较，**大于 `0x1000`走 `SYSTEM:Autoexec.bat file overflow`错误分支，等号允许**。在加法不回绕且格式正常输出的普通对象条件下，3对应新增CRLF和终止NUL，聚合有效长度最多4095。本文记录的是所见门及宽度，不扩畸形对象或任意长度的通用安全证明。

格式包装 `19a320`本身向后端传容量值-1；4096门在生成器内，不是该包装获得了4096计数。包装可能归一化负返回值，但 `ab2620`在此没有据其返回再分流；异常、CRT全部失败行为及回滚不在本段闭合范围。

生成前在 `ab264b`读取 `0x144b55578`，非空时调用 `539630`尝试移除旧 `AUTOEXEC.BAT`记录；聚合后在 `ab2845`再次读取该门，非空时调用 `5379c0`登记。两次读取各管一个接口，本段不把它们当同一时点快照；门为空只跳过对应接口，不跳聚合。生成器未因为列表空或最终长度0而绕过后置门。实际启用状态未观测，生成不等于已经登记。

### 数据复制到哪里，登记又保存什么

| 层次 | 原指令支持的数据关系 |
| --- | --- |
| 安装条目到链表节点 | 节点字符串有独立存储，小串内置、大串另分配复制 |
| 节点到生成器临时串 | 再复制后作LF／CRLF规范化，不在这里改原节点字符串 |
| 临时串到全局聚合 | 追加到 `0x144b56580`；每次先置该地址首字节0，再重建有效C字符串 |
| 聚合到虚拟文件记录 | `537a07`保存原RDX，`539493/498`取回并原样写记录 `+0x10`；记录数据字段借用同一聚合地址 |

生成器以 `strlen`重算聚合长度传入R8，登记入口保存其低32位，并在 `5394a0`写记录 `+0x18`；普通4096门内的长度可落入该字段。原文件名bytes是 `AUTOEXEC.BAT\0`，目录实参指向首字节为0的窄字符串，均由原PE核定。记录在 `539507`链接入全局记录链，文件名／目录的其它处理不据此推成数据复制。

登记前调用方将 `0x143f1c88f`置1，记录 `+0x26`复制该byte，正常返回后调用方再置0；本段按偏移记录，不给该标志套未经核验的源码枚举或属性含义。异常边的标志恢复未核。

### 必要生命周期及成功边界

`539630`匹配并摘除记录后，只把记录本身以大小 `0x30`传给释放辅助；本范围没有把记录 `+0x10`的数据指针作为释放实参。这支持登记层的数据借用判断，不等于所有虚拟文件对象的生命周期均已恢复。全局缓冲地址被反复复用，内容会重建；已打开对象是否另外缓存指针／长度或复制数据，以及并发情况未追。

`5379c0`还存在全局计数不小于500、名称／目录指针等提前返回路径，本文只核到达数据发布尾部的字段关系。调用方不检查记录是否实际发布，所以不能把生成器正常返回当登记成功。移除接口内也未见显式回退该计数，不将摘除记录概括成恢复全部容量；其它重置、异常与目录分支未穷举。

协调d3c8完整审阅45增2删及两次门的补充说明，独立父审八来源2021行／296直接或RIP引用、44关键点／15相对目标、5组原字面，并从PE异常目录另核16个范围。两次门各控制一个接口，登记`+0x10`原指针／`+0x18`低32位长度及正常返回后清标志均按原字段保持。父证据为协调树 `.local-analysis/config-path-incident-20261112/autoexec-aggregate-d3c8-preliminary.json`及`autoexec-aggregate-d3c8-delivery-review.json`。补充读取命令一次因shell引号导致Python SyntaxError，改用独立脚本文本后完成只读核验，原失败保留；未改原proof及门更正说明。

本段 `aggregate-proof.json`于 **09:41:32**核八个新定向范围 **2021缓存行**、3个复用安装点、**44关键点／15直接相对目标**及5组字面原bytes，工具返回0。原 `aggregate-literals.json`另保留LF／CRLF／格式／目录／文件名的VA、RVA、偏移与bytes；所有 `aggregate-*`证据独立新建，旧交付只读。修改专题前已干净快进共享 `ab50467`，只更新本专题相关断点，不改共享待办／HANDOFF／索引；原Task及[EX-005](exploration-backlog.md#ex-005)仍保留历史实际、特殊输入及后续读取边界。全段无目标／GUI／窗口查询／配置写／候选GO或依赖变更。
