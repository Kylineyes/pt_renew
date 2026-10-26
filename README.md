# PT Renew

最新接手入口：[本轮会话交接：已完成与接下来任务](SESSION_HANDOFF.md)。

使用 **C++ + Qt 6** 重建 DOS 版 Protel AUTOTRAX 的 Windows 桌面工程。

稳定 `dev` 为第十阶段（0.10.0）：支持 PCB/LIB/NET 只读查看、引脚映射，以及**受限铜层几何分析（非完整 DRC）**，本阶段增加两点测量的可选几何端点捕捉及取点来源。铜层分析只对已支持几何建立保守接触图；**只要整个板图几何覆盖不完整，所有网络均显示“无法确定”，不因局部路径看似相连而报通过。** 没有实现完整 DRC、断短路确认、布线、封装放置、编辑保存或生产输出。

另有 **0.11.0 基础编辑候选**：已有自由走线可在内存中移动、删除及撤销重做，原输入只读，不支持保存。源码已推送至 `Kylineyes/feat-basic-editing`，Debug/Release 自动验证及父工作区集成复验各11/11组通过。此前真实GUI已取得主要编辑、测量/分析更新和关闭保护证据；本轮又补齐严格文本焦点、10000mil远移后的显式复位与旧式撤销重做、五类其他图元只读保护、关闭/换图取消后的直接历史截图、选后文件消失的实际读取失败，以及独立进程菜单退出确认放弃。NET/铜层迟到结果竞态、900000mil极端可见性和系统会话结束仍未覆盖，**整体验收尚未通过**。两个候选和本任务控制客户端已正常退出，固定候选及输入23/7/7集合与摘要前后不变。用户要求稳定产品保持 **0.10.0**，本轮不合入实现、不替换 `dist/`。详见[剩余验收报告](docs/basic-editing-remaining-acceptance.md)和[此前实际编辑报告](docs/basic-editing-actual-edit-acceptance.md)，实现见[候选开发报告](https://github.com/Kylineyes/pt_renew/blob/b0e5ac7761f13690b5310bbc913ab7bfd2691d08/docs/basic-editing.md)；原任务的退让执行偏差和截图失败漏停链记录继续保留。

## 开发环境

已验证 Qt **6.12.0 MSVC x64**、Visual Studio 2026、CMake 和 Ninja；不需要 Qt Creator。

```powershell
& .\scripts\Enter-QtEnv.ps1
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
& .\build\debug\pt-renew.exe
```

其他 SDK 安装路径：

```powershell
& .\scripts\Enter-QtEnv.ps1 -QtPrefix 'D:\Qt\6.12.0\msvc2022_64'
```

可通过命令行只读打开一个旧 PCB 文件：

```powershell
& .\build\debug\pt-renew.exe 'D:\板图\样例.PCB'
```

载入在后台解析，显示走线、焊盘、过孔、圆弧、矩形填充、文字与元件标签，同时展示 SHA-256、图元数量和限制说明。当前仅支持已覆盖的 `PCB FILE 4` 记录；未知记录或畸形字段整体拒绝，不静默丢弃。上限为 64 MiB、200000 条结构记录，非 ASCII 代码页尚未确认。格式覆盖与显示限制见 [PCB 只读预览](docs/pcb-readonly.md)。

## 菜单与键盘

- 顶部菜单保留原程序 17 个一级入口及字母，窗口较窄时通过菜单溢出入口访问。
- **鼠标**：点击顶部菜单。
- **现代键盘**：Alt+F 等访问菜单，Ctrl+O 打开只读板图，Ctrl+W 关闭板图，Ctrl+G 切换网格。
- **旧式入口**：点击画布使其获得焦点，按 F 打开文件菜单，再按 L 打开同一个文件对话框；P、N 等字母可打开对应菜单。
- 单字母兼容只在画布焦点内生效，不抢占文本框中的文字。
- F5/F6 缩小/放大，F9 重绘，F10 居中；滚轮缩放，中键拖动视图。
- 左侧复选框控制 13 层显隐；面板关闭后，可从“设置 → 图层显隐面板”恢复。
- 单击图元查看只读属性，同位置再次单击或画布内 **Ctrl+Tab** 切换重叠候选；画布内 **Esc** 或单击空白清除选择。
- **Ctrl+I** 或“信息 → 图元属性面板”恢复属性面板；显示尺寸、源文件行和所属元件，不修改原板图。
- **Ctrl+F** 或“跳转 → 检索并定位元件”（画布 J→C）：按标号、封装或注释筛选，Enter 定位，不移动元件；画布 **Ctrl+Home** 跳转板坐标原点。
- 画布 **Ctrl+M** 或“信息 → 两点只读测量”：依次单击两点读取距离、ΔX/ΔY 和方向角；画布 **Esc** 退出模式并保留已完成结果。“清除测量”移除结果。
- 测量默认自由取点；画布 **Ctrl+Shift+M** 或“信息 → 测量时捕捉几何端点”开启捕捉。靠近可见走线端点、焊盘/过孔中心、圆弧端点或填充角点时显示黄色方框，点击使用该模型坐标；超出范围仍为自由取点。
- 测量面板分别显示两点的实际来源；不捕捉文字、网格或推测的交点，不是 DRC 或生产尺寸校验。详见 [测量端点捕捉](docs/measurement-snap.md)。
- 未实现的业务明确标注并禁用，不提供伪保存或伪布线。

## 封装库只读浏览

主窗口 **Ctrl+L** 或“封装库 → 封装库只读浏览”（画布 L→B）打开独立窗口；**Ctrl+Shift+L** 选择 LIB。也可直接运行：

```powershell
& .\dist\pt-renew.exe --library 'D:\库\示例.LIB'
```

库窗口内 Ctrl+F 筛选名称、Ctrl+O 打开 LIB，可缩放、平移、选择图元并查看二进制字节偏移。库预览不会替换主板图、放置元件或启用保存。

已对四个本地真实库的 318 个有效指针条目、8026 个图元完成当前结构检查；尚未完成原程序导出和逐像素对照，不宣称所有历史库变体完全兼容。未知/损坏条目明确拒绝部分预览，详见 [LIB 分析](docs/library-analysis.md)。

本地结构诊断工具（需要先启用开发环境）：

```powershell
& .\build\release\pt-library-check.exe 'D:\库\示例.LIB'
```

## 网表与引脚映射（不是铜线连通检查）

- **Ctrl+Shift+N** 或“网络 → 只读载入外部 NET”（画布 N→G）。
- **Ctrl+Alt+N** 或“网络 → 网络与引脚映射”（画布 N→N）打开面板并聚焦筛选。
- 选中网络可高亮唯一匹配且无冲突的焊盘；激活节点（如按 Enter）定位到焊盘。
- 内嵌 NETDEF 与外部 NET 使用来源下拉框切换，**不自动合并**；更换/关闭板图会清除外部网表及高亮。
- 重复网络名/元件声明、缺失/歧义/跨网冲突会明确报告，不自动猜测或替换封装。

```powershell
& .\dist\pt-renew.exe 'D:\project\pt_renew\pt\PLACED.PCB' --netlist 'D:\project\pt_renew\pt\DEMO.NET'
```

当前样例的 36 个声明元件、88 个网络、370 个节点均能唯一映射到焊盘，**不代表这些焊盘之间的铜线已经连通**。本地没有原始 NETDEF 样例，该部分仅由公开结构描述和合成测试验证；元数据保留但未解释。详细语法、EOF 兼容、限制见 [网表兼容说明](docs/netlist-compatibility.md)。

命令行只读诊断（先运行 `Enter-QtEnv.ps1`）：

```powershell
& .\build\release\pt-netlist-check.exe 'D:\project\pt_renew\pt\DEMO.NET' 'D:\project\pt_renew\pt\PLACED.PCB'
```

退出码 0 不等于 DRC 通过；必须结合 `board_loaded` 和完整诊断信息判断。工具不会修改输入。

可选运行受限铜层接触分析：网络面板按钮、“网络 → 受限铜层几何分析”（画布 **N→A**）、**Ctrl+Alt+C** 共用同一入口。命令行：

```powershell
& .\build\release\pt-copper-check.exe 'D:\project\pt_renew\pt\PLACED.PCB' 'D:\project\pt_renew\pt\DEMO.NET'
```

分析完成后，面板会列出未覆盖图元、图层和源文件行号；双击条目或按 Enter 可定位并查看属性，隐藏图层保持关闭。详细条目最多保留 200 条，同时显示总数及省略数；CLI 的 `coverage_issues` 提供同样的来源信息。说明见 [覆盖诊断与文字研究](docs/copper-coverage.md)。

此分析**不是 DRC**。退出码 0 也不代表生产通过；`3` 表示存在未覆盖几何或无法判定内容，须以完整 JSON 限制/分网说明为准。铜层模型和样例结果见 [铜层分析说明](docs/copper-analysis.md)。

## 覆盖模块研究工具

原程序的外置 OVR 已建立受限只读映射工具，可核对 MZ 描述符、覆盖入口及段重定位，并输出 JSON 摘要：

```powershell
python tools/inspect_legacy_overlays.py 'D:/软件/PT.EXE' 'D:/软件/TRAXEDIT.OVR'
```

默认只输出结构摘要，`--detail full` 增加入口和调用候选；不执行或修补原软件。Python 仅用于研究工具，桌面程序不依赖它。格式边界及已验证计数见 [覆盖模块映射](docs/legacy-overlays.md)。

后续已定位默认文字笔画表及静态解释路径，可只读核对已知 EXE：

```powershell
python tools/inspect_legacy_text.py 'D:/软件/PT.EXE'
```

可选 `--text`、`--height`、`--orientation` 输出供本地对照的静态中心线。[受控机器码验证](docs/legacy-text-machine-verification.md) 已比较 21,792 个组合与 105,504 条中心线，未发现差异；后续 [边界计算模式补验](docs/legacy-text-boundary-verification.md) 的 1,458 例也全部通过，确认累计边界包含抬笔移动端点，不能等同可见笔画或铜面积。完整原程序的独立画面与像素对照仍待完成，尚未将字形接入桌面程序或铜层分析，详见 [原文字形静态证据](docs/legacy-text.md)。

后续 [32字符对象创建补验](docs/legacy-text-copy-verification.md) 的16个受控用例通过，确认限80、去尾空格、再限32及空串不建对象；[A240后续现场](docs/legacy-text-screen-next.md) 已取得无遮挡笔画和切换当前层后的隐藏/恢复。真实缩放、其他高度/方向变体、导入联合状态及保存仍未完成，`runtime_verified=false`。

## 发布目录

在已启用 Qt 开发环境的终端运行：

```powershell
cmake --preset release
cmake --build --preset release
ctest --preset release
cmake --install build/release --prefix dist
windeployqt --release --compiler-runtime --no-translations dist/pt-renew.exe
```

`dist/` 是本地部署目录，不应提交。正式发布仍须在干净 Windows 10/11 上验证运行库、安装包及许可义务；本机运行成功不替代目标系统验收。

## 文档与协作

- [当前综合进度](PROGRESS.md)：0.10.0稳定交付、0.11.0候选剩余GUI结果和未覆盖项、原字形研究及子代理状态。
- [新 Agent 交接](HANDOFF.md)：当前进度、验证边界、环境与本地证据路径、接手顺序和后续计划。
- [协作规范](AGENTS.md)：简体中文、约定式提交、独立分支 → dev → 用户合并 main。
- [Qt 开发环境](docs/qt-development.md)：安装组件、验证结果和平台限制。
- [首次调查](docs/initial-assessment.md)：软件身份、DOSBox 与文件现状。
- [逆向结构与架构](docs/reverse-architecture.md)：证据、分层、快捷键设计和后续步骤。
- [PCB 只读预览](docs/pcb-readonly.md)：第二阶段字段布局、扩展属性、渲染与失败策略。
- [选择与属性查看](docs/selection-inspector.md)：第三阶段命中规则、重叠切换、属性来源和操作验证。
- [测量端点捕捉](docs/measurement-snap.md)：第十阶段的几何候选、可见层、屏幕半径与取点来源。
- [元件检索与测量](docs/navigation-measure.md)：第四阶段筛选定位、自由取点、快捷键与近似读数限制。
- [LIB 分析与浏览](docs/library-analysis.md)：第五阶段二进制目录/图元布局、只读窗口、结构诊断及未验证语义。
- [网表兼容说明](docs/netlist-compatibility.md)：第六阶段 NET/NETDEF、引脚映射、差异/冲突检查与真实验证。
- [铜层分析说明](docs/copper-analysis.md)：三态几何接触模型、运行限制和“非 DRC”验收边界。
- [覆盖模块映射](docs/legacy-overlays.md)：MZ/TPOV 入口、重定位检查、研究工具与字形恢复的证据边界。
- [原文字形静态证据](docs/legacy-text.md)：默认笔画表、字符指令与旋转镜像、只读检查工具及运行对照限制。
- [覆盖诊断与文字研究](docs/copper-coverage.md)：第九阶段的未覆盖图元定位、JSON 字段和原文字体研究边界。
- [铜层圆弧分析](docs/copper-arcs.md)：第八阶段的象限拆分、内外包络、端点假设与验证范围。

`pt/`、`pt_install/` 和 `.local-analysis/` 永远不应提交。原软件及用户文件不属于本项目自行授权分发的内容。测试使用合成小样例，不提交原软件数据或反编译数据库。
