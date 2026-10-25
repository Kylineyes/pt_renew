# 原文字形截图现场验收

2026-10-25，北京时间。基线为 `origin/dev=acf22bb2b3044e05ad0358aa2b53c94fb73de532`，独立分支为 `Kylineyes/verify-text-screen-sol`。实际运行器为 Pi；启动环境确认 `PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`。沿用当前会话，没有启动子代理。产品保持 **0.10.0**，**`runtime_verified=false`**。

本轮完成新隔离场景、配置实际加载与 PT 执行核对，但**现场验收因目标前景无法确认而阻塞**。三张工具截图均包含遮挡目标的其他应用，不能作为 AUTOTRAX 启动页、PCB 工作画面或客体像素证据。没有发送 Enter、菜单键、保存或编辑命令，没有新增字形测量结论。

## 范围与逐项结果

完整阅读本工作区 `AGENTS.md`、`HANDOFF.md`、机器码验证、边界补验及 PCB 文字字段路径文档；另只读核对 DOSBox 配置、启动日志报告和历史准备脚本。历史 verification-40 的错误脚本未执行；没有重复函数仿真，没有修改产品代码、根交接文档或其他工作区。

| 验收项 | 状态 | 本轮事实与限制 |
| --- | --- | --- |
| 实际模型、推理强度、独立分支和基线 | 通过 | Pi 的实际环境值匹配指定模型；HEAD 与 origin/dev 同为 acf22bb |
| 首次原生前景、锁屏与残留进程检查 | 通过 | 23:10:46 前景为 QQ，输入桌面为 Default；无 DOSBox、pt-renew 残留；LockApp 进程存在但不是前景 |
| 全新隔离副本、挂载和无 BOM 配置 | 通过 | 13 个独立场景；每份配置挂载本场景 runtime，断言 pt/PT.EXE 与 SCREEN.PCB 存在；UTF-8 无 BOM |
| A240 配置实际加载与 PT 执行 | 通过 | 本轮 stderr 明确记录加载本轮 dosbox.conf；独立日志记录两次 mount 及执行 pt.EXE |
| 可辨 AUTOTRAX 启动页、可靠目标前景 | 阻塞 | PID/HWND 身份可确认；实际前景未确认属于目标，截图被其他应用遮挡 |
| 实际工作文件名 SCREEN.PCB | 未验证 | 没有进入 Status；启动参数不充当实际载入证据 |
| Strings=1、Tracks=4 | 未验证 | 为输入结构的预期值，未从原程序状态页观察 |
| A/F 文字属性、方向0、层和线宽 | 未验证 | 只实际启动 A240；没有进入文字属性框；F240 未启动 |
| 同层独立尺标及图层显隐 | 未验证 | 文件已生成；未取得可接受工作画面，不能宣称尺标可见 |
| 视图缩放及完整/简化绘制路径 | 未验证 | 没有现场缩放值或路径观测；不能从输入高度推断实际绘制分支 |
| 客体原生截图、板坐标比例和端点像素 | 未验证 | 没有 DOSBox 客体原生捕获；宿主截图尺寸不作客体分辨率；未进行拟合或残差计算 |
| 高度240/251/252、AA/A A | 未验证 | 隔离输入已准备，未运行比较 |
| 非对称 F 旋转和镜像 | 未验证 | 已准备方向1–3、16–19，未运行；文件到内部方向的映射仍未确认 |
| Y镜像和双镜像组合 | 未验证 | 没有从解释器支持推断实际文件接受范围，本轮未准备或运行32/48组合 |
| 唯一原件、历史副本及本轮输入保护 | 通过 | 15组前后文件集合和SHA-256全部相同 |
| 本轮进程清理 | 通过 | 只终止核对命令行属于本轮的DOSBox PID7484；结束查询无DOSBox或pt-renew残留 |

## 本轮实际执行路径

证据根目录仅在本机，记为 E：

```text
C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-acceptance/
```

23:10:01 启动环境核对后首先创建 `E/worker-status.json`。23:10:46 只读 Win32 观察取得前景 HWND `133028`（`0x207A4`）、PID `36428`、QQ.exe、session 3，`OpenInputDesktop` 成功并读到 `Default`。历史 LockApp PID12708 仍存在，但这不能证明当前锁屏。此观察文件中的 `input_desktop_open_error=203` 是成功调用之后未清除的线程错误值，不能解释为打开失败；本轮判断依据为非空句柄及成功取得的桌面名称。没有尝试解锁或持续轮询。

加载 `orca-cli` 技能、当前安装版本的 `orca skills get orca-cli --json` 和实际 `computer` 帮助后，使用公开 CLI。能力报告称截图和按 PID/HWND 定位可用；这只是能力描述，仍逐步核对实际结果。

`E/prepare-scenes.py` 只读核验原安装与历史 verification-40 副本，从后者复制到各场景的全新 `runtime/pt`。保留历史无 TRAXEDIT.DFT 条件，没有修改安装或历史副本。每个新场景增加一个 `SCREEN.PCB`，各为104文件。四条尺标与文字都在1层，尺标宽10，文字宽1；这样后续可独立检查同层可见性，不沿用历史11层尺标的显示前提。

仅启动 `E/scenes/a240/plan.json` 指定的命令，工作目录为该场景的 `runtime/pt`，命令为：

```text
C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.exe -conf C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-acceptance/scenes/a240/dosbox.conf
```

实际目标为 PID **7484**、HWND **1510096**，标题为 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms`。`dosbox-stderr.log` 第2行明确记录本轮绝对配置路径；`dosbox-startup.log` 第60、63行记录 mount，第68行记录 `Execute pt.EXE 0`。这些日志证明本轮配置与执行阶段，不能证明 PCB 已载入、对象已创建或字体指针状态。

随后实际执行了以下步骤，每步保存公开工具返回：

1. `step-001-windows.json`：按 PID7484 枚举窗口，取得 HWND1510096。
2. `step-002-startup.json/png`：按 PID/HWND 截图，662×566；图中大部分为遮挡目标的 Orca，仅露出 DOSBox 边缘和不完整图形，不能识别完整启动页。同期原生前景为微信 HWND133702/PID9324。
3. `step-003-restore-startup.json/png`：一次公开 `get-app-state --restore-window`；返回成功且截图仍被 Orca 遮挡，没有目标已到前景的证据。没有借助系统 API 强制抢焦点。
4. `step-004-focus-title.json/png`：一次限定 PID7484/HWND1510096 的窗口坐标标题栏点击 `(75,20)`。工具返回 `action.path=synthetic`、`verification.state=unverified`、`reason=synthetic_input`。图中为 ZCode；随后的原生观察取得前景 HWND264538/PID36556/ZCode。没有据工具成功返回宣称点击或前景切换已生效，也没有认定窗口变化由该点击造成。
5. 因无法确认焦点停止输入，未发送 Enter、菜单字母、缩放键或截图快捷键。没有切换其他控制入口或修改控制门禁。本轮没有收到 `ControlStatus=user` 或自动审批拒绝；停止原因是已观察到的前景和截图不满足后续输入前提。
6. 重新检查 PID7484 的映像与完整命令行，确认指向本轮 a240 配置后，仅终止该进程。立即查询仍列出该PID，但映像和命令行已为空，保留为退出期间的中间观察；没有据此宣称进程已消失。随后运行后摘要核验，23:20:04的最终查询确认无DOSBox或pt-renew残留。历史PID34876本轮开始时已不存在，没有对其发送操作。

## 场景及后续测量判据

全部场景保存在 `E/scenes/<名称>/`，各有独立 `runtime/pt`、`captures/`、`dosbox.conf`、`plan.json` 和 `inputs-before/after.json`。`plan.json` 的“已准备，未启动”是准备时的快照；实际启动事实以 a240 的 `target.json` 和总汇为准，其他12个场景确实未启动。

| 名称 | 字符 | 高度 | 文件方向 | 本轮执行情况 |
| --- | --- | ---: | --- | --- |
| a240 | A | 240 | 0 | 已执行PT；启动页与文件载入未确认 |
| f240 | F | 240 | 0 | 未启动 |
| a251、a252 | A | 251、252 | 0 | 未启动 |
| aa240、aspa240 | AA、A A | 240 | 0 | 未启动 |
| fdir01、fdir02、fdir03 | F | 240 | 1、2、3 | 未启动 |
| fdir16、fdir17、fdir18、fdir19 | F | 240 | 16、17、18、19 | 未启动 |

文字原点为 `(2000,2000)`。同层独立参考线为 `(1920,2000)→(2080,2000)`、`(2000,1920)→(2000,2080)` 的原点十字，以及 `(2000,1600)→(2400,1600)` 的400单位横尺和 `(2000,1600)→(2000,1800)` 的200单位竖尺。尺标坐标来自明确合成输入，不由字符外形推算。

后续复验必须新建尝试目录和日志，不覆盖本轮，也不原样执行会拒绝覆盖的准备/启动脚本：

1. 重新只读核对前景、锁屏和目标进程；桌面可用后使用公开 Orca 命令限定本轮受控 PID/HWND。锁屏、门禁拒绝或失焦时停止，保留结果。
2. 在新的隔离副本生成同样的A240输入，核对无BOM、C/D挂载、cwd、PT.EXE和SCREEN.PCB存在及输入摘要。保存新的配置加载行和PT执行行。
3. 确认完整AUTOTRAX 1.57启动页与目标原生前景后才发送Enter；截图核对工作画面。按实际菜单逐步取得Status文件名、Strings/Tracks以及文字属性，每步单独截图核对，取消属性时不修改字段。
4. 按用户指定先检查同层尺标与显隐，再核对属性、缩放和方向。切换1层可见性时观察文字及四条尺标一起消失/恢复，取得实际层状态；用独立横竖尺建立轴向与板坐标比例。
5. 确认DOSBox本机客体原生截图入口后获取原生图；宿主窗口缩放和截图放大只作阅读辅助。记录客体尺寸、视图缩放、尺标端点、字符端点和残差。没有独立缩放值或运行路径观测时，将完整/简化分派保持未验证；原条件是高度除以视图缩放值小于4且边界模式为0时走简化路径。
6. 在同一可核对视图条件下先比较F240与A240，再比较240/251/252及AA/A A。静态预期的高度整除尺度20/20/21仅为待比较预测。最后逐项加载F方向样例，确认实际属性及非对称笔画关系；没有导入状态证据时不得声称已观察DS:d59a或普遍方向映射。

本轮所有像素长度、比例、端点和误差均为**未测量**。没有用截图的662×566外框尺寸拟合640×480客体，也没有用文字自身反求尺标。

## 证据路径与摘要

以下三张均为**未采纳的宿主窗口截图**；用于证明遮挡与停止条件，不用于DOS画面验收。绝对路径如下：

| 截图绝对路径 | SHA-256 |
| --- | --- |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-acceptance/step-002-startup.png` | `7dd7aaa6a7056cff86ad2af5d9c444905fe1515dd0db7ee5262d5dd485efbaa9` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-acceptance/step-003-restore-startup.png` | `f29383a864b5647157fecf1ce6cb3e78de8795933cbe8e2478c3e3d4ebcec2d6` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-acceptance/step-004-focus-title.png` | `09ba79ae44e030808b4a1855fd56db9db2a85324ba05b5777bc224dbdfd8b694` |

| 输入或配置 | SHA-256 |
| --- | --- |
| 原PT.EXE及本轮副本 | `abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968` |
| 原TRAXEDIT.OVR及本轮副本 | `cab0fc0571c5a295c396bd6479a57f060bb18a01d2c2ffc5b438cc1b65f8a0d8` |
| 原GRAPH.DRV | `46dcf6903de901ed403b14b627591a2b628b6d144a43b95c5272ed66e801e76f` |
| DOSBox-X映像 | `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832` |
| a240/SCREEN.PCB | `6707495bf8567f055d79235d6dfe1a71c8f2779d77ab7cf614871006f8055834` |
| a240/dosbox.conf | `8bdc4da265331a57bbe0c9bd5b4bd3112a107afe0076674515f3ec8198ca772b` |

其余配置、日志、逐步返回及原生观察的绝对路径和SHA-256见 `E/evidence-index.json`。总汇为 `E/verification-summary.json`；首次观察为 `E/desktop-observation.json`；原生后续观察为 `E/native-after-launch.json`、`E/native-after-focus.json`、`E/native-final.json`；清理归属证据为 `E/process-before-cleanup.json`，退出期间的中间观察为 `E/processes-after-cleanup.json`，确认无残留的最终记录为 `E/processes-final.json`。所有原图、配置、脚本、日志及完整摘要均只在本工作区忽略目录，不提交。

`E/finalize-evidence.py` 实际核对15组输入：原安装99文件、历史副本103文件、13个各104文件的新隔离副本，集合及每文件SHA-256全部无变化。13份配置摘要也与准备时相同且无BOM。`git diff --check` 通过。此次只有专题报告，无产品或研究工具修改，不重复Qt构建、CTest或既有机器码矩阵。

本轮仅在自己的工作分支提交此报告，由父工作区集成；没有合并或推送dev/main。完整DOS加载、字形、像素、缩放和旋转镜像验收继续保持未完成。
