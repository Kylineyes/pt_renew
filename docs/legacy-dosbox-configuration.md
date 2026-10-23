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

**尚未证实的加载规则**：本机范围内没有足够说明或源码，无法精确确认显式 `-conf` 成功/失败时对当前目录、程序目录、用户目录默认配置的搜索与继承条件，也不能确认多个文件的属性覆盖和 `[autoexec]` 是替换还是追加。未指定的键不能简单认为继承 I 或 U；F/R 中的参考值也不能直接视为本次有效值。这些未知应由下一轮实际启动的配置来源记录、可用的有效配置查询或后续获准的对应版本源码核对来收敛，不扩大本任务搜索范围。

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
