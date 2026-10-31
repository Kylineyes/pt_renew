# PT Renew：当前进度与新 Agent 交接

2026-10-31最新状态与接手顺序见[编辑与另存为统一交接](docs/agent-handoff-20261031-save-as.md)。开发主线已支持自由走线编辑和另存为新PCB，Debug/Release各12组及本机真实Qt核验通过；原件和已有目标不覆盖，原软件重开/原生文件框等边界待验。已发布alpha仍只读，本轮不发新版本；用户要求完成本轮后交给新agent，以下保留历史。

**最新会话的统一交接请先读 [SESSION_HANDOFF.md](SESSION_HANDOFF.md)。** 本文保留历史环境、研究证据与复现细节。后续实际编辑已取得主要流程现场通过证据，但整体验收因未覆盖细项及部分未按用户要求退让满180秒而failed；稳定产品仍0.10.0、编辑源码仍是独立0.11.0候选。当前下一步以新交接文档为准，不沿用本文旧“数值输入前阻塞”断点。

交接基线日期：2026-10-24；进度入口更新：2026-10-26。最新综合进度、后续提交及子代理恢复情况见 [PROGRESS.md](PROGRESS.md)。本文保留原交接证据和复现步骤；先读 [AGENTS.md](AGENTS.md)，再按本文的“接手顺序”继续。

## 1. 当前结论

稳定 `dev` 产品为 **第十阶段 0.10.0**，采用 C++ / Qt 6，目标是 Windows 桌面的 DOS AUTOTRAX 重建。已经具备 PCB/LIB/NET 只读查看、选择定位、测量、引脚映射、受限铜层分析，以及可选的测量端点捕捉。

**0.11.0 自由走线内存移动/删除、撤销重做、修改状态及分析失效已完成源码和自动验证；真实GUI重试已显示部署窗口、原始属性和移动对话框，但首次有效数值输入前门禁持续 `user`，仍是独立候选，未合入稳定 `dev` 或覆盖 `dist/`。** 候选提交 `b0e5ac7` 在已推送的 `Kylineyes/feat-basic-editing` 分支，状态与路径见 [PROGRESS.md](PROGRESS.md)。保存/另存为、新增图元、元件放置、布线、完整 DRC 和生产输出尚未实现。

原文字形已新增32字符对象创建受控验证、无遮挡A240与层显隐现场证据，但完整原程序的缩放、方向和像素验收仍未完成，`runtime_verified=false`。Qt文字仍是系统字体近似，铜层文字仍为覆盖缺口。

最新用户目标是继续开发并分配子 agent。所有子 agent 使用 Pi：纯逆向 `glm/glm-5.3 high`，截图及截图验收 `deng/gpt-6.1-sol high`。用户已授权直接控制电脑，不反复询问；实际输入仍须先确认锁屏、目标前景及控制门禁，门禁拒绝后停止，不换入口绕过。

## 2. 仓库与分支状态

| 项目 | 交接基线 |
| --- | --- |
| 当前实际工作区 | `C:/Users/rikideng/orca/workspaces/pt_renew/main-2` |
| 原软件安装 | `D:/project/pt_renew/pt`，99 个文件，只读保护 |
| 远端 | `git@github.com:Kylineyes/pt_renew.git` |
| 本文编写前 dev / origin/dev | `951b296e3e899acf75def39a0910f36ebafe3870` |
| 最近产品功能合并 | `291feba`：0.10.0 测量端点捕捉 |
| 最近研究合并 | `951b296`：文字机器码矩阵与锁屏诊断 |
| origin/main | `e5f1822`；在本文编写前比 dev 少 22 个提交 |
| 发布程序 | 本地 `dist/pt-renew.exe`，0.10.0 |

本文通过独立文档分支提交后按项目流程合并、推送 dev；接手时以 `git log` 和 `git status` 的实际输出为准，本文不预写自身提交哈希。

不要根据另一工作区中的旧本地 main 判断产品进度。所有开发都从最新 dev 建独立分支，完成构建、测试、必要的 GUI 交互后，保留合并记录并推送 dev。**main 的合并、提交和推送由用户执行。**

关键提交：

- `0550367` / 合并 `f5e6eb9`：恢复文字属性证据，修正 Tracks 误读。
- `1dd6df1` / 合并 `291feba`：测量端点捕捉与取点来源，版本 0.10.0。
- `d70de85` / 合并 `951b296`：原文字解释器机器码及对象路径交叉核验。

## 3. 已完成功能与限制

| 模块 | 已实现 | 仍需注意 |
| --- | --- | --- |
| 应用与命令 | 17 个一级菜单，统一命令目录，现代快捷键及画布内旧式字母入口 | 未实现业务明确标注并禁用；文本输入不被单字母快捷键抢占 |
| PCB 查看 | `PCB FILE 4` 后台解析、图元预览、图层显隐、缩放平移、输入摘要 | 64 MiB / 200000 结构记录限制；未知记录整体拒绝；非 ASCII 代码页未确认 |
| 选择定位 | 重叠图元切换、只读属性、源行与元件归属、元件检索 | 文字与部分焊盘轮廓为近似几何 |
| 测量 | 两点距离、ΔX/ΔY、角度；自由取点或可选几何端点捕捉 | 不捕捉网格、文字、推测交点；不是 DRC 或制造尺寸验收 |
| LIB | 二进制目录/图元解析、独立只读浏览与筛选 | 本地四个真实库共 318 条有效条目、8026 个图元完成结构核对；未确认所有变体 |
| NET / NETDEF | 外部/内嵌来源、引脚映射、冲突诊断、焊盘高亮与定位 | NETDEF 主要依靠公开结构与合成测试；引脚映射不等于铜线连通 |
| 铜层分析 | 走线、焊盘、过孔、矩形填充、受限圆弧模型与覆盖诊断 | 不是完整 DRC；不完整覆盖时所有网络保持“无法确定” |
| 原程序研究 | OVR 描述符/重定位映射、字形表与解释路径、菜单/宏路径 | 原字形没有接入产品；原软件数据和字体不能随仓库直接分发 |

真实样例 `PLACED.PCB + DEMO.NET` 的既有诊断结果为 430 个铜模型对象、5211 次比较、88 个网络无法确定、21 组跨网接触候选。五处铜文字仍是覆盖缺口；这些候选不是已确认短路，也不能为生产放行。

## 4. 0.10.0 最近产品交付

端点捕捉入口：“信息 → 测量时捕捉几何端点”，画布快捷键 `Ctrl+Shift+M`；两点测量为 `Ctrl+M`。默认关闭捕捉，靠近候选时显示黄色方框。支持可见走线端点、焊盘/过孔中心、圆弧连续弧段的真实端点、矩形填充四角。

捕捉半径固定为 **10 个 Qt 逻辑像素**，按视图换算成板坐标。取点时重新查询，不使用过期的悬停结果；换图清空设置与来源。测量面板分别保留两端的真实来源，不能把开关开启当成所有取点都已捕捉。完整圆没有端点，相邻启用象限之间的连接处也不作为端点。

主要实现入口：

- `src/geometry/EndpointSnapIndex.*`：按 X 排序的模型候选查询，独立于 Widgets。
- `src/ui/BoardCanvas.*`：坐标换算、取点、悬停标记、图层和测量状态清理。
- `src/domain/Measurement.h`：两端坐标与各自图元来源。
- `src/application/CommandCatalog.cpp`、`src/ui/MainWindow.cpp`：共享菜单/快捷键和结果展示。
- `tests/EndpointSnapTests.cpp`：新增几何、画布、生命周期和命令入口测试。

已完成验证：

- Debug 与 Release 均 **10/10 组 CTest 通过**；八组 QtTest 各 **246 项通过、0 失败、0 跳过**（含初始化/清理）。另外两组是 Python 研究工具测试。
- 新增端点捕捉组 14 项通过；含 12000 个候选的替换查询、隐藏层、圆弧组合、混合来源、屏幕半径及文本焦点保护。
- 部署程序在排除 Qt SDK / Visual Studio PATH 的子进程环境中实际启动，菜单操作和捕捉标记已经截图核对。
- 合成走线 `(100,100) → (400,500)` 得到 **500.00 mil / 12.7000 mm**、53.13°；隐藏顶层后同处取点为自由来源，约 499.93 mil；恢复图层后再次得到 500.00 mil。
- 部署与 Release EXE 的 SHA-256 均为 `726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1`。

桌面工具初次组合键调用未稳定改变状态，现场验收使用实际菜单；快捷键由 Qt GUI 事件测试独立验证。不要把前面的无效桌面按键返回重复记为成功。

详细记录：[测量端点捕捉](docs/measurement-snap.md)。未做干净 Windows 10/11 机器验收，最大板图压力测试也尚未完成。

## 5. 原文字形验证推进到哪里

### 5.1 已有现场事实

verification-35/36 已实际显示 AUTOTRAX 1.57 启动页、主菜单、Information、Status，以及 Edit → String 属性框。C21 状态为工作文件 `C21.PCB`、Strings=1、**Tracks=4**；文字属性可读为 **A、高度 240、线宽 1**，随后用 Esc 取消，没有修改字段。

旧文档曾将 Tracks 误读为 0，已修正。不要继续以“文件有四条 FT、计数却为零”作为阻塞或未载入依据。参考尺标未明显显示仍需检查，但它与计数误读是不同问题。

### 5.2 受控机器码验证已通过

verification-41 使用本机已有 Unicorn 2.1.4，按 MZ 头及重定位加载已知 EXE，在独立 16 位仿真内存中执行原文字解释器、原栈检查和短字符串复制辅助函数；截获绘线调用参数，模拟该绘图调用返回。

- 解释器 **21792 个输入组合**、**105504 条中心线**，坐标、每字符起点、最终位置、请求线宽与 Python 研究工具无差异。
- 输入覆盖 127 个非零低 7 位字符索引、10 组高度、16 种旋转镜像，以及空串、相邻字符、空格、高位别名和32/80字节长字符串等。
- 对象绘制包装 512 例：256 次进完整解释器、256 次进简化绘制路径，参数和分支均符合预期。
- 方向函数 512 例：变换状态为零时的 256 个字节保持不变，另 256 个有效状态/方向组合符合查表顺序。

关键路径沿用 Ghidra 的 `0x1000` 装载基段：解释器 `2964:39a2`，对象包装 `2964:53a3`，方向函数 `22fe:38bf`；换算原 MZ 段值需减去 `0x1000`。

**重要前提：高度除以视图缩放值小于 4，且边界计算状态为零时，会改走简化绘制路径。** 后续实际画面对照必须记录视图缩放和走到哪条路径，不能仅凭文件字高判断。

### 5.3 仍未验证，不能提前宣称完成

- 完整 DOS 启动、FS 读取、对象创建与原字体指针状态的联合运行。
- 实际 PCB 导入时 `DS:d59a` 变换状态及文件方向到对象方向的映射。
- 变体的屏幕端点、VGA 像素、裁剪、笔宽面积、真实缩放和完整/简化分派；A240已有独立尺标与有限像素证据，见第5.6节。
- 长文字经过对象创建的32字符复制限制后的实际显示与保存往返。
- 16位溢出、非法方向、零索引等未支持输入的原行为。

研究工具仍输出 `evidence: static_instruction_derivation`、`runtime_verified: false`。函数级仿真提高了推导可信度，不能替代完整程序的独立画面对照。**不要据此直接把字形接入铜层、放宽文件方向范围或宣称 DRC 完整覆盖。**

详细记录：[机器码验证](docs/legacy-text-machine-verification.md)、[文字属性核验](docs/legacy-text-object-verification.md)、[PCB 文字字段路径](docs/legacy-pcb-text-path.md)。

### 5.4 接手后新增：边界计算模式补验

verification-42 新增 1458 例原包装/解释器调用：944 例边界计算、256 例正常绘制、256 例简化分派、2 例空对象指针，全部通过。边界状态为1时绕过低缩放简化分派、不调用绘线，并累计所有移动指令的终点，包括抬笔移动；不会额外加入最初原点。这种累计边界不能直接当作可见笔画、铜面积或像素包围盒。

该边界模式阶段未执行DOS启动、PCB读取、对象创建、保存或实际绘图，`runtime_verified=false`。其中32/80字节直接构造对象只用于边界路径，不能验证创建限制；**后续对象创建32字符边界补验已完成，见第5.6节**。原安装99项、隔离输入103项摘要不变，14项研究工具测试通过。详细矩阵、执行范围和复现命令见 [边界计算模式补验](docs/legacy-text-boundary-verification.md)。

### 5.5 截图重试：A240有限现场对照已取得

2026-10-25晚至26日凌晨，Pi `gpt-6.1-sol high` 在用户要求重试后完成A240阶段，专题提交 `d5931ea`，报告见 [A240现场重试](docs/legacy-text-screen-retry.md)。本轮取得11张640×480客体原生图，Status确认SCREEN.PCB、Strings=1、Tracks=4；文字属性为A、高度240、线宽1。独立尺标给出原点像素(240,186)、横向约0.5/纵向−0.5像素每mil；三个可辨文字端点的图像支持距离为0、0、1像素，包含端帽估计及栅格限制，不能视为绘线中心线误差。

该次完整验收未通过：原点处笔画被同色宽尺标遮挡，关闭当前顶层被“CURRENT LAYER MUST BE TURNED ON”拒绝，内部缩放与分派、导入变换状态、F/高度/间距/旋转镜像尚未验证，`runtime_verified=false`。15组输入摘要一致，该轮进程已清理。之后已解决A240尺标遮挡与层显隐，见下节；仍不能把旧环境当作当前状态。

### 5.6 最新补验：对象创建、无遮挡A240与层显隐

Pi `glm/glm-5.3 high` 完成对象创建 `22fe:06fc` 的16例受控机器码验证，最终提交 `3625f84`。最多保留32字符，处理顺序为限80、去尾空格、再限32，空串不建对象。原函数、实验设置与分配/后续处理截获范围均有记录；未执行GUI导入和保存，哨兵未变不能证明未读。原安装99文件、历史副本103文件摘要不变；研究工具全集45项通过。报告：[32字符对象创建边界](docs/legacy-text-copy-verification.md)。

Pi `deng/gpt-6.1-sol high` 后续取得无遮挡A240、独立双轴±0.5像素/mil、端点0或1像素对照。实际先切Current→Layer→Bottom Layer，再隐藏/恢复Top，红色像素3585→0→3585，恢复集合差0。提交 `2435a35`，报告：[后续现场验证](docs/legacy-text-screen-next.md)。Zoom菜单显示，但Keyboard缩放前ControlStatus持续user，K未发送、F未启动；完整验收仍为failed、`runtime_verified=false`。

门禁停止后同一预排shell曾错误继续两次宿主点击，相关图排除，原始记录保留；已离线修复停止标记、CLI失败停止和PowerShell退出码保护，没有实际桌面重试。父代理核验379项索引及12张原生图（11接受、1排除）的摘要/尺寸，视觉结论仍由指定截图模型作出。四组输入不变，目标与客户端已退出。

0.11.0候选的独立GUI首次任务只读检查16次/30秒仍为user，因此未启动产品。后续用户要求重试，Pi请求曾因超时和三次连接失败停在任务起点；父代理复用同一会话恢复，实际模型仍为gpt-6.1-sol high。门禁先返回ready，已在仅系统PATH启动真实部署窗口，确认原输入/未修改工作副本、自由走线原始属性(100,100)→(400,500)、500mil以及移动菜单/对话框。完整标题定位失败和Type缺loc两次错误属于工具使用，保留记录后修正；首张其他应用前景图排除。恢复输入连接时31次/60秒user，1.5请求未发送，实际编辑和后续交互未执行。候选部署包23文件、来源与副本输入各7文件不变，本轮目标和客户端已清理；稳定版本仍为0.10.0。详见 [首次阻塞](docs/basic-editing-acceptance.md) 和 [真实窗口重试](docs/basic-editing-acceptance-retry.md)。

## 6. 当前阻塞、进程与踩过的坑

以下为历史阻塞和PID，不能当作下一轮当前状态；最新控制门禁和清理结果见第5.6节。

2026-10-24 11:08（北京时间）的只读复核确认：Windows 原生前景仍为 session 3 的 `LockApp.exe`，标题“Windows 默认锁屏界面”，分辨率1024×768。锁屏时 Orca 的窗口截图可能取得壁纸，窗口列表仍可能列出 DOSBox；这不是 AUTOTRAX 的有效画面，也不是输入已送达的证据。接手时重新查状态，不假定仍锁定或已经解锁。verification-42 于同日11:15:50（北京时间）再次取得前景HWND 329562、PID 12708、标题“Windows 默认锁屏界面”；本轮未发送桌面输入、未启动DOSBox。

没有 DOSBox 残留。PID **34876** 的 `pt-renew.exe` 是上一轮部署验收窗口，命令行指向 `dist/pt-renew.exe` 和 `.local-analysis/verification-39/measurement.PCB`；它不是原 DOS 程序。若进程仍存在且需要关闭，先重新核对 PID、映像、命令行，避免终止复用同一 PID 的其他程序。

需要避免重复的实验问题：

- **verification-40 首次挂载错误**：副本在 `runtime/pt`，配置却挂载 `runtime-without-dft`，所以只进入 COMMAND。不是原软件异常。当前保留的 `prepare.py` 含这个历史错误，**不要原样重跑**；创建全新实验目录并修正、断言路径。
- 第二次用 PowerShell 写配置带 UTF-8 BOM，未取得新的完整日志；现存 startup 日志属于首次启动，不能用它判断第二次 PT 是否执行。
- 新配置用 Python `write_text(..., encoding='utf-8')` 无 BOM 写入；启动前检查挂载目录、PT.EXE、目标 PCB、日志输出路径，启动后核对实际配置加载记录。
- 不同尝试使用不同目录和独立日志，不能覆盖旧日志后把两次结果混为一轮。
- Windows-MCP 的普通字母 Shortcut 可能走 Unicode 输入，不能等同 DOS 的物理按键；既有现场通过 ASCII 状态下的 `Shift+I`、`Shift+S` 进入菜单。
- `use_ui_tree=false` 时 Windows-MCP 主动跳过窗口枚举；空窗口元数据不证明焦点丢失。焦点用 Win32 前景 HWND/PID 复核。
- 门禁持续返回 user 或报告失焦时，停止该动作并保存结果，不盲目重放；锁屏后不继续抢焦点或发全局键盘输入。
- DOSBox窗口外框放大未必放大客体分辨率，曾产生重绘残影。优先核实客体原生捕获，截图最近邻放大只能辅助阅读，不能增加测量精度。
- 本机 Unicorn 对全栈读取安装钩子时，远返回曾出现错误跳转。最终矩阵不对栈读安装读取钩子，保留写入及非栈读取检查，原解释器及辅助函数使用原生远返回；不要悄然改为辅助函数桩后仍称原路径已执行。

## 7. 本地证据在哪里

**本节路径只存在于原工作区，不在 Git 中。新 agent 如果在同一机器的新 worktree，需要从下面的绝对路径读取；远端 clone 不会包含这些文件。不要通过强制 git add 搬运它们。**

证据根目录：`C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/`。

| 相对证据目录 | 用途 |
| --- | --- |
| `source-sha256.json` | 原安装99文件基线摘要 |
| `verification-12/prepared-cases/` | 16个独立文字样例C00–C15及静态结果、manifest |
| `verification-35/` | 启动页、菜单、Status、实际配置与文件打开日志 |
| `verification-36/` | 文字属性截图、取消动作、计数修正和恢复汇总 |
| `verification-37/`、`verification-38/` | 同层参考线、显示后端对照，未取得可靠画面 |
| `verification-39/` | 0.10.0部署GUI验收；`verification-summary.json`索引截图和摘要 |
| `verification-40/` | 本轮C00隔离副本、挂载/BOM错误、锁屏、清理及输入不变汇总 |
| `verification-41/` | 机器码仿真脚本、矩阵、包装/方向结果及脚本摘要 |
| `verification-42/` | 边界状态为1的补验矩阵、只读锁屏观察、脚本及结果摘要 |

截图子工作区 `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/` 保存 `text-screen-acceptance/`、`text-screen-retry-20261025/`、`text-screen-next/`、`basic-editing-acceptance/` 与 `basic-editing-acceptance-retry/`（含两次工具错误恢复子目录）。对象创建证据在同级 `research-text-copy-glm/.local-analysis/text-object-copy/`；开发候选、合成输入和构建记录在 `feat-basic-editing/.local-analysis/basic-editing/`。父工作区 `.local-analysis/agent-dispatch/` 保存派发与证据审计，`.local-analysis/development-wave/` 保存候选集成复验日志。这些目录均不入Git。

0.11.0固定候选为 `C:/Users/rikideng/orca/workspaces/pt_renew/feat-basic-editing/.local-analysis/basic-editing/release-candidate/pt-renew.exe`，SHA-256为 `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8`。只在对应独立候选分支运行编辑验收；稳定dev源码和既有dist仍为0.10.0。父工作区build目录曾编译0.11.0集成候选，不能因随后切换Git分支就把旧构建产物视为当前dev的构建；重新构建时遵循CMake预设。

原 EXE SHA-256：`abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968`。原 OVR SHA-256：`cab0fc0571c5a295c396bd6479a57f060bb18a01d2c2ffc5b438cc1b65f8a0d8`。固定偏移不能套用其他版本。

旧 pi 会话 JSONL 已缺失，完整历史不能恢复；旧终端留有 ENOENT 错误。现有 Git、正式文档、截图和本地汇总是继续工作的依据，不要为了恢复缺失聊天而长期停滞。

## 8. 开发环境与复现命令

已验证环境：Qt **6.12.0 MSVC x64**，SDK在 `C:/Users/rikideng/Qt/6.12.0/msvc2022_64`；Visual Studio Community 2026、MSVC工具集14.51.36231、CMake与Ninja。详细安装来源及限制见 [Qt 环境](docs/qt-development.md)。不需要另装 Qt Creator、Vulkan 或 WebEngine。

在工作区根目录的同一个 PowerShell 进程中启用环境再执行命令；工具多次启动新 shell 时不要假定上次环境变量仍存在：

```powershell
& ./scripts/Enter-QtEnv.ps1
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
cmake --preset release
cmake --build --preset release
ctest --preset release
```

发布目录更新：

```powershell
& ./scripts/Enter-QtEnv.ps1
cmake --install build/release --prefix dist
windeployqt --release --compiler-runtime --no-translations dist/pt-renew.exe
```

Python研究环境已有3.15.1、Unicorn2.1.4、Capstone5.0.7；它们不属于桌面程序依赖。不要重复安装。包含对象创建工具的研究测试全集45项已经通过：

```powershell
python -m unittest discover -s tests -p "test_legacy_*.py"
```

机器码矩阵从原工作区复现，详细边界先读报告，不要仅执行命令就声明完整运行验证：

```powershell
python .local-analysis/verification-41/compare_matrix.py .local-analysis/verification-40/runtime/pt/PT.EXE 12
python .local-analysis/verification-41/compare_matrix.py .local-analysis/verification-40/runtime/pt/PT.EXE 1 11 23 24 239 240 251 252 1200
python .local-analysis/verification-41/verify_object_paths.py .local-analysis/verification-40/runtime/pt/PT.EXE
python .local-analysis/verification-41/summarize.py
```

桌面控制已有可用的 Orca Computer Use 和 Windows-MCP 路径。涉及 Orca 工具先读 `orca-cli` 技能及本机 `orca skills get orca-cli`；使用公开命令，动作按目标PID/HWND限定，逐步保存返回和截图。不要修改控制门禁、第三方包或系统设置来掩盖失焦/锁屏问题。

## 9. 接手顺序与接下来计划

### 第一优先级：完成0.11.0候选独立GUI验收

1. 阅读AGENTS、当前PROGRESS和基础编辑验收报告，核对候选 `b0e5ac7`、部署EXE摘要及合成输入。实现分支已推送；Debug/Release自动验证和父工作区集成复验各11/11通过，不能替代真实窗口。
2. 复用Pi `deng/gpt-6.1-sol high` 截图会话，使用新Task/Dispatch和证据目录。先只读核对ControlStatus、锁屏及前景；只有明确恢复允许状态后才启动部署包和发送输入。持续user则停止该任务，不重连或换入口绕过，也不用offscreen替代截图。
3. 按验收报告完成部署启动、移动/取消/零位移、删除/撤销/重做、元件/隐藏层/库只读、文本焦点、测量/捕捉/分析失效、关闭/换图/退出取消与失败载入保留。发现缺陷回派开发会话；修复须新提交和新部署摘要。
4. GUI通过后合入dev、更新交付与发布目录。系统会话结束保护在受控环境另验收，不主动注销共享桌面。

### 并行兼容性研究

对象创建32字符边界与边界模式已经完成，无变化时不重复矩阵。继续现场时使用新隔离副本、正确挂载和无BOM配置，先核对加载、属性、计数与原生640×480捕获。A240笔画遮挡和切换当前层后的显隐已经解决，下一步确认真实缩放及完整/简化分派，再做F、高度251/252、AA/A A、旋转镜像与笔宽像素；实际导入变换和字体指针仍需证据。

只有真实加载、对象状态、独立坐标尺标、指定绘制路径和变体对照补齐后，再决定原字形接入。先解决本地原字体使用/分发方案，渲染、命中与铜层分别验收，不能因函数级无差异就改为`runtime_verified=true`或放宽铜层覆盖结论。

### 后续产品阶段：新增图元与另存为

0.11.0候选已实现自由走线移动/删除及撤销历史、修改状态、取消保护和派生分析失效，尚未通过真实GUI，不能当作正式交付。先完成上述验收，再扩展：

1. 为新增自由图元设计明确的工具与取消状态，保留来源和可撤销命令；元件整体与内部图元关系另行设计。
2. 先做“另存为新文件”，禁止覆盖唯一原板图；验证未知/未解释字段的保留或明确拒绝、读写往返、原程序重新打开和失败后输入不变。
3. 通过构建、测试和真实GUI后，再扩展网格/约束捕捉、元件放置、布线及网络维护；完整DRC和生产输出各立阶段。

## 10. 不要忘记的协作约束

- 代码说明、界面、日志、文档和提交说明使用简体中文；Git遵循中文Conventional Commits。
- `pt/`、`pt_install/`、`.local-analysis/`、SDK、构建产物、原截图、字形数据和反编译数据库永远不提交。
- 原始安装、库与板图只读；运行及写入实验使用独立副本，记录摘要或备份。
- 图形模型、几何、命令状态与渲染分层，不为每个图元建立QWidget。
- GUI修改必须实际交互验证；测试通过不替代现场验收，仿真通过也不替代完整程序行为对照。
- 工作分支完成后合并并推送dev；main留给用户。失败、阻塞和未验证项如实记录。

## 11. 可直接交给新 Agent 的启动提示

> 请继续PT Renew开发。完整阅读AGENTS、PROGRESS和HANDOFF并核对实际分支。稳定dev/发布包仍为0.10.0；0.11.0候选b0e5ac7在已推送的Kylineyes/feat-basic-editing，实现和Debug/Release各11/11自动验证完成。真实GUI重试已确认部署启动、原始走线属性、移动菜单/对话框，但数值输入前ControlStatus持续user，实际移动和后续交互未验收，尚未合入dev或覆盖dist。复用Pi gpt-6.1-sol high，用新Task只读核对门禁，允许后从固定摘要候选的数值输入与实际编辑继续；工具Type须提供loc或label，动作均受门禁与PID/HWND核对保护。拒绝后停止，不换入口绕过。纯逆向只用Pi glm-5.3 high；32字符创建边界和A240/层显隐已完成，缩放和变体仍缺，runtime_verified=false。用户已授权直接控制，无需反复询问；保护原安装和忽略材料，验证后合并推送dev，不操作main。
