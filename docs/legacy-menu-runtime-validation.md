# 原菜单运行核验与桌面观测诊断

verification-33 已解释此前截图中窗口元数据为空的原因，并用新截图、Win32 HWND、PID 和会话归属交叉核对桌面观测。随后在全新无 `TRAXEDIT.DFT` 副本中只启动了一次 DOSBox；可验证的目标窗口出现，但客户区只有黑底与白横线，未取得可辨 AUTOTRAX 启动页，因此停止交互。**Enter 主菜单、Information、Status 的 Work File Name、图元计数和文字对象属性均未完成运行核验，`runtime_verified=false`，产品仍为 0.9.0。**

本轮基于 `origin/dev=050c713d134a983729ef83092a655790485c788d`，分支为 `Kylineyes/research-menu-runtime-validation`，只新增本页和 [只读桌面观测工具](../tools/inspect_legacy_desktop.py)。既有 [菜单静态路径](legacy-menu-keypath.md) 与 [文字运行记录](legacy-text-runtime.md) 仅作为只读参考；未修改它们。没有合并或推送 `dev`、`main`。

## 证据位置与输入保护

本轮证据根目录为：

```text
C:/Users/rikideng/orca/workspaces/pt_renew/research-menu-runtime-validation/.local-analysis/verification-33/
```

下文相对证据路径均以该目录为根。旧证据只读来源为 `C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/`，没有执行原安装或既有运行副本。原安装 `D:/project/pt_renew/pt` 的 99 个文件与 `source-sha256.json` 相符；既有 `verification-20/runtime-without-dft/pt` 的 103 个文件与 `verification-20/inputs-without-dft-before.json` 相符，才复制出本轮 `runtime-without-dft/pt`。这里“无 DFT”特指没有 `TRAXEDIT.DFT`，不表示删除其他程序的 DFT 文件。

运行结束后再次计算完整文件集合与 SHA-256：原安装 99 项、既有副本 103 项、新副本 103 项全部相符，前后均为 0 项差异。完整清单保存在 `source-before/after.json`、`existing-inputs-before/after.json`、`fresh-inputs-before/after.json`，摘要结论在 `verification-before.json`、`verification-after.json`；只读复核脚本为 `check-inputs.py`。

| 新副本输入 | SHA-256 |
| --- | --- |
| `PT.EXE` | `abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968` |
| `TRAXEDIT.OVR` | `cab0fc0571c5a295c396bd6479a57f060bb18a01d2c2ffc5b438cc1b65f8a0d8` |
| `GRAPH.DRV` | `46dcf6903de901ed403b14b627591a2b628b6d144a43b95c5272ed66e801e76f` |
| `C21.PCB` | `09f16e0c4fb7e0380e15285b8d610f6963e73ad349c9168cb28626f34c0a3f85` |

原字节、截图、完整工具清单和第三方源码摘要只留在忽略的本地证据目录，不提交。

## 空窗口元数据的原因

本机 Windows-MCP 版本为 0.8.8。只读核对其 `windows_mcp/desktop/service.py` 第 138 至 153 行发现：`use_ui_tree=false` 的快速截图路径主动跳过窗口枚举，设置 `windows=[]`、`active_window=None`。因此 verification-29/32 中的 `No active window found`、`No windows found` 不能单独证明 Windows 实际没有窗口、目标失去焦点或原菜单未载入。

该文件本轮 SHA-256 为 `c116adc0d221c993a89596a14f0ac66bf924e250672cb2691a8914b0e788231e`。这解释的是当前实现与已记录调用参数的关系；没有倒推出历史每个按键实际送达的窗口，也没有解释 verification-28 第二个 Esc 后前景变化。

新工具调用只读 Win32 API，记录前景 HWND、窗口标题、类名、所属 PID/映像路径、会话、可见状态、矩形、窗口站与线程桌面；不发送输入、不切换窗口、不结束进程。`native-initial.json` 显示观察进程和 Orca 都在 session 3，窗口站 `WinSta0`、线程桌面 `Default`，前景 Orca 为 HWND 67484、PID 55276。可见顶层窗口枚举成功，前景 HWND 在枚举前后稳定。工具显式提示：窗口矩形受进程 DPI 上下文影响，不可直接作为截图物理像素输入坐标。

随后唯一 MCP 连接的完整 `Snapshot(use_ui_tree=true)` 在约 15.49 秒返回窗口列表与截图。其前景 HWND 656982，与 `step-001-initial-native-after.json` 的 Windows Terminal HWND 相符；截图确实显示本轮 Python 客户端控制台。该窗口归属 Windows Terminal PID 51644，不归属 DOSBox；本轮没有清理该终端宿主。由此本轮的桌面观测可以交叉验证，不能再把快速截图的空列表作为焦点判断依据。

## 单连接动作与停止位置

客户端 `desktop-client.py` 使用一个 stdio Windows-MCP 连接。请求逐个写入全新 inbox，未预排多个输入动作；每次桌面调用前查询 `ControlStatus`，变更动作后先再次查询状态再截图，调用超时上限为 30 秒。实际所有控制查询均为 `ready` 或 `ai`，未发生 `user` 等待或 `CONTROL_PREEMPTED`；本轮没有修改第三方包、门禁、阈值或 hooks。

| 顺序 | 调用与现场结论 | 本地证据 |
| --- | --- | --- |
| 1 | `ControlStatus=ready`、generation 1；完整 UI 截图及原生前景核对通过 | `step-001-initial-gate-00.json`、`step-001-initial.json`、`step-001-initial-00.png`、对应 `native-before/after.json` |
| 2 | 状态为 `ai`，`App(launch_executable)` 仅启动本轮 DOSBox；返回 PID 46020，约 0.83 秒 | `step-002-launch-gate-00.json`、`step-002-launch.json`、`processes-launch.json` |
| 2 后 | 再次查询状态并立即截图，约 0.19 秒；此时截图仍是客户端控制台，原生前景也仍是该控制台，尚未观测到目标窗口 | `step-002-launch-post-gate-00.json`、`step-002-launch-post.json`、`step-002-launch-post-00.png`、`step-002-launch-native-after.json` |
| 3 | 后续只读核对发现目标窗口已出现；请求一次新的快速截图，约 0.25 秒。截图可见 DOSBox 黑色客户区和白横线，没有可辨 AUTOTRAX 启动页，停止交互 | `native-after-launch-review.json`、`step-003-launch-settled-gate-00.json`、`step-003-launch-settled.json`、`step-003-launch-settled-00.png`、对应 `native-before/after.json` |
| 4 | 发送客户端 stop 请求，连接正常结束，随后只读复核进程与输入 | `step-004-stop.json`、`processes-after-client-stop.json`、`processes-final.json`、`native-final.json` |

目标窗口完整标题为 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms`，类名 `SDL_app`、HWND 2295234、PID 46020、session 3；CIM 记录的父 PID 为本轮 MCP 服务进程 24920，命令行包含本轮配置绝对路径。原生前景与截图中窗口一致，足以确认本轮窗口和进程归属。标题中的 `PT`、启动命令中的 `C21.PCB` 均不能代替程序实际文件名与对象状态。

本轮没有发送 Enter、Esc、菜单字母、宏或鼠标输入，没有为了黑屏再切换焦点或重复启动。未观察到启动页，故没有执行“启动确认 → Enter 主菜单 → Information → Status”的后续序列，也未到达文字属性观察入口。静态复核提示 Status 观察后应优先单个 Esc 退出，避免进入输出分支；本轮未运行到该分支。

## 配置和启动日志的只读复核

`dosbox-c21-no-dft.conf` 与 verification-29 已取得启动页的配置逐行比较，只有 `captures` 和 C/D 挂载目录改为本轮绝对路径，其他参数与启动序列完全一致：`output=opengl`、`machine=vgaonly`、`cycles=fixed 10000`、`c:`、`cd \pt`、`pt C21.PCB`。verification-32 只有控制/截图探测，没有 DOSBox 启动配置可用于比较。配置差异保存在 `configuration.diff`，程序化归一化比较通过；本轮配置摘要为 `9d3b7532dc107773a2b98bf9e9767177b6fe87a1f42a3270421aeec46a3d4e19`。

C/D 两个盘符均只挂载本轮 `verification-33/runtime-without-dft`，运行工作目录为其 `pt` 子目录，主机路径及 `PT.EXE` 的存在均已核对。DOSBox-X 2026.10.01 可执行文件 SHA-256 为 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832`。挂载配置和文件存在不证明客体内加载成功。

`client-stdout.log` 为 0 字节，`client-stderr.log` 仅含 MCP 服务启动消息和一条弃用警告，没有 DOSBox 启动错误。只读核对 `windows_mcp/tools/app.py` 第 50 至 57 行确认 `App(launch_executable)` 将目标 stdout/stderr 都重定向至 `subprocess.DEVNULL`；这部分输出本轮没有保存，不能从空客户端日志推断目标没有错误。该文件 SHA-256 为 `92707067638d86fe259d41c7a017c35ceba696811a53ce14e3101f8d933395e0`。

新实验目录没有 DOSBox 独立日志，本轮配置未启用日志；本机安装/用户配置的 `logfile` 为空。安装与用户配置的路径、大小和摘要保存在 `readonly-startup-diagnosis.json`，没有断言它们在本次启动中是否被额外加载。只读复核脚本为 `readonly-diagnosis.py`，没有再次启动目标。

因此，已解释的是快速截图空元数据；新阻塞是具有可验证归属的 DOSBox 窗口没有可辨启动页。现有证据不能区分 DOSBox 图形输出、初始化、配置继承或原程序启动阶段的问题，不能据黑屏断定菜单解析、PCB 格式或图元计数。最小下一步候选是在后续独立场景中，保留同一输入与模拟器参数，仅把 DOSBox 自身日志启用到新证据目录，并记录启动配置来源；仍需单连接、动作前状态、动作后截图及 30 秒停止边界。本轮不执行该候选。

## 进程归属与验证

| PID | 归属与父进程 | 清理结果 |
| --- | --- | --- |
| 57980 | 本轮 Python 启动器；父 PID 33404 | stop 后已退出 |
| 62172 | 本轮客户端 Python；父 PID 57980 | stop 后已退出 |
| 19232 | 唯一 Windows-MCP shim；父 PID 62172 | 连接结束后已退出 |
| 43944 | MCP Python 启动器；父 PID 19232 | 连接结束后已退出 |
| 24920 | MCP Python 服务；父 PID 43944 | 连接结束后已退出 |
| 46020 | 本轮 DOSBox-X；父 PID 24920 | 连接结束后已退出 |

`processes-client.json`、`processes-launch.json`、`processes-stop-check.json` 保存 PID、父进程、会话、映像与命令行；`processes-after-client-stop.json`、`processes-final.json` 的查询无匹配行。没有调用 `Stop-Process` 或清理其他进程，没有关闭其他人的窗口。进程退出事实通过 CIM 核对，不只依据窗口消失。

工具已在本机实际运行并生成前景/可见窗口记录，Python 语法检查通过，已有输出路径拒绝覆盖的行为已验证；输入核对与配置归一化比较通过，`git diff --check` 通过。未修改产品代码、Qt 字形、方向缩放或铜层判断，没有运行 Qt 构建或 CTest。本轮交付是有界诊断与未完成运行目标的可复核记录，不是菜单、载入文件或文字对象参数已验证的声明。
