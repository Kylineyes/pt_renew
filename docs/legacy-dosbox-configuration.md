# DOSBox-X 本机日志与配置加载证据

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

**尚未证实的加载规则**：本机范围内没有足够说明或源码，无法精确确认显式 `-conf` 成功/失败时对当前目录、程序目录、用户目录默认配置的搜索与继承条件，也不能确认多个文件的属性覆盖和 `[autoexec]` 是替换还是追加。未指定的键不能简单认为继承 I 或 U；F/R 中的参考值也不能直接视为本次有效值。这些未知应由下一轮实际启动的配置来源记录、可用的有效配置查询或后续获准的对应版本源码核对来收敛，不扩大本任务搜索范围。

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

这些证据**不能证明 Shift+I 全部由谁消费、是否有部分事件到达 DOS 客体或为何走到候选框**；也不能把 DOSBox stderr 中 keyboard layout／mapper 为 US 当作 Windows 输入线程已经绕开 IME。没有为补图而继续鼠标 Capture，没有重发 Shift+I、改输入法、切控制接口、补 Status 或 Esc。此未解释通道问题补入已有[EX-003](exploration-backlog.md#ex-003)，不新建同义队列；有效配置／文件名计数的剩余条件仍在 [EX-005](exploration-backlog.md#ex-005)，不能通过删项弱化条件。

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
