# PT 现状调查与 Windows 迁移建议

调查日期：2026-10-21。阶段：只做现状分析与兼容性探测，未开发替代应用。

> 后续决策：用户已选择 **C++ + Qt 6**。本报告保留首次调查时的框架比较，不再作为 WPF 选型决定；已安装并验证的 Qt 6.12.0 环境见 [Qt 开发环境](qt-development.md)。

## 1. 结论

1. 已安装的软件是 **Protel AUTOTRAX 1.57 / PCB Layout Program**，不是一般的表单程序。安装介质另外还包含 **Protel Schematic 3.31**。
2. `PT.EXE` 是 DOS MZ、16 位 x86 实模式程序。现代 64 位 Windows 不能直接执行这类程序，单纯设置“兼容模式”不能解决。
3. **DOSBox-X 路线已得到初步实测验证**：在隔离副本中启动成功，进入文件加载对话框，并打开 `PLACED.PCB` 看到了元件、焊盘及丝印。没有验证保存、输出、DRC、自动布线或长时间稳定性。
4. **REA 已安装，但其 Windows Ghidra 适配层不接受这个 DOS 目标**。本机 Ghidra 本身已成功导入该 MZ 文件；工具适配层限制不等于 Ghidra 不支持 DOS。
5. 如果目标是“仅在 Windows 上，开发相对简单、交互流畅”，优先考虑 **C# + WPF + 专用二维画布**。如果未来优先考虑跨平台及大型 CAD 内核，则考虑 **C++ + Qt 6**。
6. 不建议先完整反编译全部代码。应以原程序作行为参照，优先明确文件格式和操作规则，仅对无法由样例及界面验证的算法进行定向逆向。

## 2. 文件位置与 Git 保护

本次会话位于隔离 Git worktree。两个原始目录实际在主工作树 `D:\project\pt_renew` 下，而不在本次 worktree 中。所有命令仍从本次工作区执行，原始目录仅作为输入。

已做的保护：

- 新增项目 `.gitignore`：忽略 `pt/`、`pt_install/`，适用于匹配名称的目录及其内容。
- 同时在共享 Git `info/exclude` 加入这两个规则，让主工作树中的原始目录在本次 `.gitignore` 合并前也立即被忽略。
- 忽略 `.local-analysis/`，其中包含本次诊断脚本、运行副本、模拟器配置及截图；不会将软件副本或截图作为项目源代码提交。
- 用 `git check-ignore` 验证规则；`git ls-files -- pt pt_install` 无输出，原始软件未被跟踪。
- 启动前对已安装目录的 99 个文件建立 SHA-256 清单，运行使用逐文件校验过的副本，不直接运行或修改原始安装。

Git ignore 是普通 add/commit 的排除规则，不是安全权限控制；`git add -f` 仍可以绕过它。后续如引入远端仓库/CI，可另加服务端或 CI 禁止提交这些路径的检查。本次没有安装 Git 钩子、提交或推送。

## 3. 软件组成与证据

### 3.1 安装盘并非只包含一套产品

| 位置 | 观察到的内容 |
| --- | --- |
| `pt_install/DISK1/INSTALL.DAT` | `Schematic V3.31 (1.2M)`；Schedit、原理图库、Schplot、图形驱动 |
| `pt_install/DISK1/READ.ME` | `PROTEL SCHEMATIC Version 3.31`；1989/1990 版权信息 |
| `pt_install/DISK2/INSTALL.DAT` | `Autotrax Extended V1.57`；Traxedit、工具、Traxplot、图形驱动 |
| `pt/TRAXEDIT.MNU:4` | `AUTOTRAX 1.57` |
| `pt/TRAXEDIT.DFT:1` | `PROTEL DEFAULT 1.57` |
| 实际启动画面 | `AUTOTRAX - PCB Layout Program`、`Version 1.57` |

因此，不能用 DISK1 的说明推断 PCB 编辑器版本。当前已安装目录中没有发现 SCHEDIT 主程序；本报告的迁移建议以已安装 AUTOTRAX 为中心，不把原理图编辑器默认并入重建范围。

规模：`pt/` 为 99 个文件、1,981,680 字节；`pt_install/` 为 18 个文件、1,498,756 字节。

### 3.2 关键文件

| 文件 | 字节数 | 作用/观察 |
| --- | ---: | --- |
| `PT.EXE` | 210,016 | MZ 主程序，包含 TRAXEDIT 相关字符串；程序启动画面确认 AUTOTRAX 1.57 |
| `TRAXEDIT.OVR` | 274,574 | 外置覆盖模块，开头为 `TPOV`，包含编辑器与版本等字符串 |
| `TRAXPLOT.EXE` | 230,048 | 绘图/输出程序，MZ |
| `TRAXPLOT.OVR` | 75,941 | 绘图覆盖模块，开头为 `TPOV` |
| `GVIEW.EXE` | 208,064 | 配套查看程序，MZ；本次未验证具体运行功能 |
| `GRAPHSET.EXE` | 19,792 | 图形驱动选择工具，MZ |
| `GRAPH.DRV` | 4,096 | 与 `VGA640.DRV` 的 SHA-256 完全一致；字符串为 VGA 640×480 |
| `TRAXSTD.LIB` | 151,328 | 二进制封装库，包含 `PCB 4 LIBRARY` 标识 |
| `TRAXEDIT.MNU` / `.KEY` / `.DFT` | — | 菜单、快捷键宏、默认配置，均可读 |

`PT.EXE` SHA-256：

```text
abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968
```

MZ 头声明长度恰好为 210,016 字节、重定位项 3,950 个、文件头 990 段落，入口文件偏移 17,312；没有主 EXE 末尾附加的覆盖区。**这不代表没有覆盖代码**，因为 `.OVR` 是独立文件。

`TPOV`、运行时错误字符串和覆盖模块组织方式是 Turbo/Borland Pascal 工具链的强线索，但尚未恢复原始编译器版本或源代码。后续仅分析 EXE 会遗漏外部覆盖模块中的逻辑。

### 3.3 数据兼容性比预期有利

- 两个 `.PCB` 样例均以 `PCB FILE 4` 开头，是可读文本，而非需要先破解的加密数据库。
- `PLACED.PCB` 为 24,922 字节，有 36 个 `COMP` 标记、422 个 `CP` 标记、203 个 `CT` 标记、15 个 `CA` 标记。
- `660A.PCB` 为 6,533 字节，有 170 个 `FT` 标记、35 个 `FF` 标记、2 个 `FV` 标记等。
- 上述是按独立标记行作的初步统计，不是经过完整格式解析器验证的语义计数。
- `.LIB` 不是同样的纯文本 PCB 格式，需要单独研究库目录、名称编码、图元记录及偏移结构。
- `TRAXEDIT.KEY` 已明确给出 F1 放焊盘、F3 放走线、F5/F6 缩放等宏，是保留旧操作习惯的直接证据。
- `PCBTODXF.DOC` 描述现成 DXF 转换器及图层映射；`PADS2PCB.DOC` 描述导入转换限制。它们虽以 `.DOC` 命名，实际可按文本读取，不是现代 Word 文档。

本次只识别结构，尚未证明坐标精度、全部记录类型、旋转/镜像语义、兼容文件读写或库格式已完全掌握。不能因文本可读就直接按空格切分后宣称完成格式兼容。

## 4. 工具现状

| 工具 | 本机状态 | 本次验证结果 |
| --- | --- | --- |
| REA | `rea-agents@6.7.0`，已有全局 CLI | 版本、帮助、doctor、artifact inspection 均实际调用 |
| Node.js | 24.22.0 | 满足当前 REA 文档要求 |
| Ghidra | 12.1.4 | 原生 headless 成功按 DOS MZ / 16 位实模式导入 PT.EXE |
| JDK | OpenJDK 21.0.2，64 位完整 JDK | 显式进程级 JAVA_HOME 后，REA Java 检测通过 |
| DOSBox-X | 2026.10.01 | 启动 AUTOTRAX 并打开 PCB 样例成功 |
| .NET SDK | 已安装 10.0.402 | 仅确认已安装，未创建项目或验证发布包 |
| WSL | 不可用，提示需安装组件 | 未安装，初步调查不需要此系统级变更 |

没有重复安装、升级或下载上述工具。官方文档通过 HTTPS 查询；遇到网络错误时使用本地 `http://127.0.0.1:10808` 代理。

### 4.1 REA 的两个不同问题

**问题一：Java 路径。** 初始 doctor 以相对命令 `java.exe` 启动时，Windows owned-process 校验拒绝，报“requires an absolute executable path”。在当前命令进程内设置：

```powershell
$env:JAVA_HOME = 'C:\Users\rikideng\scoop\apps\openjdk21\current'
```

之后 Java、Ghidra 安装和 Windows native authority 检查均通过。未修改持久环境变量或全局客户端设置。

**问题二：目标支持边界。** 即使 doctor 通过，实际执行 `rea inspect ... --provider ghidra` 仍返回：

```text
target_format_unsupported
Windows Ghidra P0 accepts native PE and explicitly selected raw 6502 targets only.
```

报错同时识别出目标为 `dos-mz`、`x86`。这与 REA 官方 DOS 和 Windows P0 文档一致。因此不能用 REA 的 Windows 后端直接完成这个 DOS 程序的深度分析。

另一个静态接口 `inspect-artifact` 对 `PT.EXE` 返回了正确大小和摘要，但格式是 `unknown`；不能把这当成“文件不是 DOS EXE”。针对完整目标的 `inspect` 分类和 Ghidra 原生导入都确认了 DOS MZ。

REA 的当前客户端注册在 doctor 中显示缺失，CLI 使用不依赖该注册。本次没有为了这一目标去改全局 MCP 配置。

### 4.2 可行的逆向工具路径

- **近期：直接用已安装的 Ghidra**。实测 Loader 为 `Old-style DOS Executable (MZ)`，Language/Compiler 为 `x86:LE:16:Real Mode:default`，导入成功。
- 本次 Ghidra 使用 `-noanalysis` 验证导入链路，没有声称已经完成函数反编译、调用关系恢复或 `.OVR` 装载。
- Ghidra 项目目录不能含以点开头的路径段，本次不能直接放在 `.local-analysis` 下；改用独立系统临时目录后成功，生成的探测项目由 `-deleteProject` 删除。
- **确实需要 REA 自动化时**，再考虑在 Linux/WSL 中部署其 DOS Ghidra 适配层。届时仍要单独解决 Pascal 覆盖模块与运行时地址映射；不是换主机就自动获得完整源代码。

## 5. DOSBox-X 初步运行结果

全部运行均保持原目录不变；成功的运行只挂载隔离副本。

| 探测 | 结果 |
| --- | --- |
| 原目录只读挂载，启动 PT | 报 `TRAXEDIT.MNU Not Found`，尽管文件存在 |
| 可写副本、保留旧 DFT、S3/12000 cycles、启动传 PCB 参数 | 进程进入 PT，但未观察到正常编辑界面 |
| 可写副本、停用旧 DFT、标准 VGA/3000 cycles、无启动参数 | 出现 AUTOTRAX 1.57 启动画面，进入加载对话框，打开 PLACED.PCB 成功 |

成功配置的关键项：

```ini
[sdl]
output=opengl
fullscreen=false
autolock=false

[dosbox]
machine=vgaonly
memsize=16

[cpu]
core=normal
cycles=fixed 3000
```

模拟 DOS 中采用 `C:\PT` 目录，并把隔离根目录同时挂载到 C:、D:。只在副本中将 `TRAXEDIT.DFT` 改名为 `TRAXEDIT.OLD`，保留原配置以便对照。

现有 DFT 包含 `D:\PT\TRAXEDIT.DMP`、`C:\WIN\WD1EL.PCB`、`C:\WIN\POWER3.PCB`、`C:\TRAXSTD.LIB` 等历史路径。这些不是当前安装目录结构，后续必须整理。

只读挂载错误符合旧 Pascal 程序以读写方式打开资源文件时失败的表现，但尚未跟踪其 DOS 文件打开模式，**具体原因仍是推测**。成功探测同时改变了驱动模拟、输出后端、CPU 速度、配置和启动参数，**没有隔离出前一次异常的唯一原因**。

截图保留在被忽略的 `.local-analysis/`：`pt-initial.png`、`pt-vga.png`、`pt-editor.png`、`pt-placed.png`。这些是本机诊断材料，不作为可发布的原软件资源提交。

这是启动与样例加载验证，非性能基准。未验证：保存/重新加载、库浏览、中文与非 ASCII 文件名、大型板、打印、Gerber/钻孔输出、DRC、自动布线、Windows 10 实机运行以及长时间稳定性。

## 6. 重建技术选型

假设目标包括 Windows 10/11 x64，而不要求跨平台；若“Windows 10 之后”仅指 Windows 11，可缩小验证矩阵。

| 路线 | 开发便利性 | 对本项目的适合程度 | 取舍 |
| --- | --- | --- | --- |
| **C# + WPF + 专用画布** | 高 | **当前首选** | Windows 文件、菜单、快捷键、打印集成成熟；需要正确设计图形层 |
| C++ + Qt 6 | 中 | CAD 长期路线很合适 | 原生性能与跨平台能力好，但 C++、打包和维护复杂度更高，需检查所用模块许可 |
| Python + PySide6 | 原型阶段很高 | 格式探索/内部工具适合 | 大量几何运算可能要移到原生库，交付体积和依赖管理也要考虑 |
| Avalonia + C# | 高 | 跨平台需求明确时可考虑 | 可保留 C# 业务层，但本次没有跨平台需求，不为此额外引入验证面 |
| Electron / Tauri + Web 图形画布 | Web 团队可很高 | 不作为当前默认 | 并非不能流畅，但需要 Canvas/WebGL 而非海量 DOM，且多一层桌面集成与部署工作 |

### 6.1 WPF 推荐的边界

WPF 负责窗口、菜单、属性面板、快捷键和文件操作；板图使用单独绘图层。起步可以采用 `DrawingVisual`/`DrawingContext`，经真实板图基准证明有必要再评估 SkiaSharp 或 Direct2D。

不建议一开始同时接入多个渲染引擎，也不能把“用了 SkiaSharp”直接等同于“已启用 GPU”；具体控件和后端决定实际渲染路径。

流畅性的主要条件是：

- 不为每条走线、每个焊盘创建独立 WPF 控件和布局节点。
- 板图坐标与屏幕坐标分离，缩放/平移使用视图变换。
- 视口裁剪、分层绘制及适合实际规模的空间索引。
- 静态板图与动态光标/预览分离，避免每次鼠标移动重新构造全部数据。
- 几何、连通性、DRC、布线和文件解析不阻塞 UI 线程。
- 物理尺寸采用明确的内部精度与单位，旧格式单位验证后再定，不把屏幕像素当物理坐标。
- 以真实大板的缩放、拖动、选取、拖线延迟测量结果验收，不以框架名称保证 60 FPS。

推荐的数据与功能分层为：旧文件读写层、独立板图模型、编辑命令/撤销重做层、渲染与命中测试层、DRC/布线/输出服务。初期不需要为了单机文件编辑引入服务器或数据库。

### 6.2 Windows 版本和运行时要分开判断

当前已有 .NET 10 SDK，可以作为开发候选，但不能据此保证所有 Windows 10 版本都得到官方支持。Microsoft 的当前 .NET 10 支持列表按 Windows 具体版本与生命周期列出，普通 Windows 10 与 LTSC/IoT 版本的支持状态不同。

应在正式立项前确定最低 Windows 10 版本、架构、是否要求厂商支持，再选定运行时和部署模式。将“能够运行”和“官方仍提供支持”分开记录；自包含发布也不会消除操作系统支持边界。

Qt 同样要锁定版本和平台矩阵，不是选了 Qt 就能不加验证地覆盖任意旧 Windows。当前滚动 Qt 文档还提示后续版本将结束 Windows 10 支持。

## 7. 工作量与下一阶段建议

### 7.1 需要保留的实际功能

`TRAXEDIT.MNU` 不仅有基础画图功能，还列出了：

- 元件、焊盘、过孔、走线、圆弧、填充和文字；多层及电源/地平面。
- 网表载入、网络高亮、连通性相关操作、长度信息。
- 库管理、块复制/移动、快捷键宏、网格与捕捉。
- DRC、自动布局、自动布线；布线设置包含多种路径处理阶段与间距规则。
- 配套打印/绘图及格式转换工具。

因此“让原程序继续跑”“重做一个兼容编辑器”“完整复现所有算法”是三个不同规模的目标。需要先明确全部功能中哪些必须完全一致，不能在没有决定的情况下把完整编辑器悄悄缩成只读查看器。

### 7.2 建议顺序（本次未实施）

1. 固化可重复运行的 DOSBox 基线，进一步测试保存、库操作及输出，并逐项排查旧 DFT 与启动设置。
2. 建立功能与操作清单，收集真实使用的板图及库，确认是否还要包含 Schematic。
3. 用原程序生成单图元样例，逐字段对照 PCB 文本与 LIB 二进制，确定单位、层号、旋转、镜像、精度和未知记录处理规则。
4. 对 DRC、布线、库读写等不透明部分进行定向 Ghidra/运行时分析，保留对应输入输出证据。
5. 规格明确后才开发新程序；先验证读写兼容及画布交互，再逐步完成已确定范围内的编辑、检查、布线和输出功能。
6. 原程序和新版做双向文件交换与输出对照；保存必须使用副本、备份和安全写入策略，不能直接拿唯一用户板图试验。

模拟器可作为短期使用方案及长期回归参照，但不等于现代原生重建。没有依据初步启动结果给完整迁移作工期承诺。

## 8. 参考资料

- REA 官方项目及安装说明：https://github.com/morluto/rea
- REA DOS Ghidra 支持：https://github.com/morluto/rea/blob/main/docs/ghidra-dos.md
- REA Windows Ghidra 边界：https://github.com/morluto/rea/blob/main/docs/windows-ghidra-p0.md
- DOSBox-X：https://dosbox-x.com/
- DOSBox-X MOUNT 只读选项与帮助文本源码：https://github.com/joncampbell123/dosbox-x/blob/master/src/dos/dos_programs.cpp
- WPF 官方概述：https://learn.microsoft.com/en-us/dotnet/desktop/wpf/overview/
- .NET 10 操作系统支持矩阵：https://github.com/dotnet/core/blob/main/release-notes/10.0/supported-os.md
- Qt Windows 支持矩阵：https://doc.qt.io/qt-6/windows.html

本报告中本地文件与实际命令/界面观察优先于仅根据扩展名或工具宣传作出的推断。原软件、安装盘、库和用户板图的授权与项目自有代码许可应分别处理；仓库 LICENSE 不会自动赋予分发这些原始文件的权利。
