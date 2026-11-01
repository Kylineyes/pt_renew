# 原 AUTOTRAX 单线样例现场核验

本轮结论为 **failed：未取得原软件新建并保存的单线样例**。新的隔离 DOSBox-X 已显示可辨的 AUTOTRAX 1.57 启动页、红色板图外框／内部水平线及主菜单，并获得实际启动日志和标准流；但没有确认空板、工作文件名、图元计数或新增单线，未生成 `NEWFT.PCB`。原 FT 默认字段、附加值、换行编码及新增写出兼容性仍未核定，不能由现有 `SYN1.PCB` 的七字段或项目解析往返推断默认值。

本任务以 `dev=c1195dbab933fd8db8ea158ed218279cc7a1a739` 为基线，在独立分支 `verify/native-ft-sample-worker` 执行；仅新增本报告，没有修改产品源码、根 CMake、控制工具、第三方门禁／钩子或旧现场。实施范围依据[单线样例控制方案](native-ft-sample-control-plan.md)，配置及既有失败边界分别见[日志配置证据](legacy-dosbox-configuration.md)和[原软件键鼠报告](pcb-mouse-keyboard-verification.md)。

## 本轮身份、授权与隔离

本轮 Run 为 `run_bcac7af517bf`，Task 为 `task_3f5dcfa2d53c`，Dispatch 为 `ctx_63390a1027f7`。沿用当前 Pi 会话 `01a1986f-2198-700e-9abd-4b9af7a122c6`，环境、会话模型切换记录和实际 assistant 消息均核对为 **`deng/gpt-6.1-sol`、`high`**，没有切换模型、派生子代理或恢复其他 provider 会话。

用户本轮明确允许操作电脑。父协调者完成离线冻结审查后，指定北京时间 **2026-11-02 04:09:30–04:24:30**（UTC 2026-11-01 20:09:30–20:24:30）为唯一现场窗口，04:22:30 起仅收尾；GO 记录为 `go-start.json`。实际仅启动一个新控制服务和一个新 DOSBox-X，不复用旧目标，不切换输出后端，不重连、强杀或热改驱动。

本报告以下相对路径均位于本工作树忽略目录 `.local-analysis/native-ft-sample/`，截图、原软件文件和副本均不提交。

| 输入或准备证据 | 本轮事实 |
| --- | --- |
| `original-before.json`／`original-after.json` | 只读原安装 `D:/project/pt_renew/pt` 共 99 个文件，完整相对路径集合、大小、SHA-256 前后一致 |
| `runtime-copied-original.json` | 全部原安装文件复制到新 `runtime/pt` 后，先核对与原件完整一致 |
| `runtime-before.json`／`runtime-after.json` | 仅在新副本去掉 `TRAXEDIT.DFT`，再加入冻结输入；现场前后均为 99 个文件，逐字节摘要及完整集合无变化 |
| `inputs-before.json`／`inputs-after.json` | 单独冻结 `inputs/SYN1.PCB`，原件及运行副本均为 180 字节，SHA-256 `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`，前后一致 |
| DOSBox-X 映像 | `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.exe`，实际读取核对 SHA-256 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832` |
| 输出目标 | 新隔离目录的 `runtime/pt/NEWFT.PCB`，现场前后均不存在，没有覆盖输出 |

## 冻结驱动与配置

离线准备没有启动服务、GUI、截图或键鼠。`prepare.py` 退出码 0，完成新驱动 `py_compile`、10 项截图区域检查、11 项精确窗口／前景守卫检查、4 项公开控制门等待检查及 4 项 GO 时间边界检查，详细结果见 `preflight.json`。驱动基于已有 `desktop_session_v2.py` 最小适配，保留原 Popen、单请求收件箱、公开 ControlStatus、实际截图和拒绝后的静默收尾；没有改动第三方输入实现。

| 冻结文件 | SHA-256 |
| --- | --- |
| `desktop_session.py` | `1f3796cd1595e3711c2904e8bdfa99f5592ca616aabe9f153a38afc3e26c3bfa` |
| `live-plan.json` | `ff2d84472a935b609171129cba5ecd1b9b547601226c0cc88f7a2101b060cecf` |

现场和最终审计确认驱动、计划、配置摘要均未改变。配置 `SYN1.conf` 保留 `output=opengl`、`machine=vgaonly`、`core=normal`、`cycles=fixed 10000`，只挂载本轮 `runtime` 到 C／D，依次执行 `c:`、`cd \pt`、`pt SYN1.PCB`。原安装没有挂载。日志使用 `[log] logfile` 及 `files/exec/gui/misc=normal`，目标 stdout／stderr 单独保存，没有同时尝试其他图形后端或周期设置。

每步先检查公开门，仅 `ready/ai` 才请求动作；`user` 最多等待 30 秒。本轮没有公开工具错误或门拒绝。App 只允许唯一精确标题，普通输入须满足本轮 PID、原进程创建 FILETIME、固定 HWND 和稳定前景；Click／Type 坐标须在该窗口矩形内。窗口缺失、最小化、屏外、前景变化或被遮挡时使用全桌面图，缺失 image 则停止。每个变更后的原 PNG 都实际读取后才决定下一步，没有预排连续菜单操作。

## 实际看图与操作结果

本轮 11 张 PNG 均由指定 Pi 通过原 `tools.read` 实际读取，成功回执含 image。`audit_after.py` 沿用既有审计方法，逐张计算回执 image 解码 SHA-256，与原 PNG 相等，并核对读取早于下一次键鼠输入。`audit-after.json` 保存完整 SHA、原 tool call ID、读取时间和对应观察；`session-prefix.jsonl` 保留本轮审计所依据的当前会话只读前缀。

| 原图 | SHA-256 前 8 位 | 本模型实际观察 |
| --- | --- | --- |
| `step-001-baseline-00.png` | `59f3ca2e` | 全桌面为 Orca，尚无本轮 DOSBox |
| `step-002-launch-isolated-post-00.png` | `fe78c071` | 启动后目标被 Orca 遮挡，使用全桌面；不据此判黑屏 |
| `step-003-focus-owned-post-00.png` | `eeb91275` | 唯一精确 App 聚焦后，可辨 AUTOTRAX PCB Layout Program Version 1.57、Protel 标志及 VGA 640×480 提示 |
| `step-004-enter-startup-post-00.png` | `54fcccdb` | 单次 Enter 后显示红色外框与内部水平线；未显示工作文件名或计数 |
| `step-005-main-menu-post-00.png` | `5a0b27de` | 再单次 Enter 后出现 AUTOTRAX 1.57 主菜单，可辨 File／Information／Place 等项 |
| `step-006-file-menu-post-00.png` | `b171c399` | 单次 `f` 后主菜单未出现可辨变化，不能称已进入 File |
| `step-007-click-file-menu-post-00.png` | `e00cd65a` | 按预期 File 位置提交 Click `(120,270)`，实际出现 **BLOCK** 子菜单，未执行其条目；不把其他菜单当 File |
| `step-008-leave-block-menu-post-00.png` | `eeeda9c1` | 单次 Esc 退出 BLOCK 菜单，原几何仍可见 |
| `step-009-information-key-post-00.png` | `8b1d7a10` | 单次 `i` 后没有可辨 Information／文件名／计数，没有继续菜单探索 |
| `step-010-focus-for-cleanup-post-00.png` | `9edb1773` | 精确 App 聚焦并取得全桌面收尾图，确认本轮宿主窗口右上 X |
| `step-011-host-x-normal-close-post-00.png` | `1562efa3` | Click `(716,122)` 后窗口消失；随后仅由原持有者 WaitExit，不据消失本身推定退出码 |

实际公开输入请求为 **2 次 App 切换、2 次 Click、5 次 Shortcut、0 次 Type**。五次 Shortcut 为 Enter、Enter、`f`、Esc、`i`，两次 Click 分别是上述预期 File 操作和宿主 X 关闭。没有放置、删除、保存或另存命令，也没有选择新段的宽度、铜层或端点。Click 进入 BLOCK 而非 File 的原因未定位；本轮没有足够证据将其归因于坐标换算、鼠标映射、键盘实现或原软件菜单规则。

红色外框及内部水平线与冻结输入的预期几何相符，但没有取得原软件 Work File Name 或 Status 计数。因此不宣称 `SYN1.PCB` 的文件名／五条走线计数已通过 GUI 验收，更不能称空板、新段或 `NEWFT.PCB` 重开已通过。

## 原创建者退出与截止

目标由 runner **48916** 创建并持续持有原 Popen：PID **26968**、创建 FILETIME **134380374573781027**、HWND **396742**、原 Popen 对象身份 **2138986497680**、原句柄 **592**。北京时间 **04:22:28.002816** 发送宿主 X 点击，最后公开请求为关闭后截图 **04:22:28.579574**；没有发送 Alt+F4 或强杀。**04:23:26.781083** 的 `step-012-wait-original-exit-exit.json` 核对同一 PID／创建时间／对象身份／句柄，真实 `wait_return=0`。这证明宿主正常关闭及原目标退出，不证明客体单线保存业务完成。

收尾存在一项明确不足：Stop 请求文件实际于 **04:24:46** 写入，晚于 **04:24:30** 硬截止，因而未被消费。冻结驱动已在 **04:24:30.007689** 记录 `本执行分段现场截止`，按照既定路径完成 **120 秒零桌面请求**，于 **04:26:30.008875** 写出 `quiet-period-ended.json`。该记录是现场截止，不是公开控制门拒绝；不把迟到的 Stop 改写为成功执行。

随后控制服务原 Popen **PID 5064**、创建 FILETIME **134380374260787376**、原对象身份 **2138985622096**、原句柄 **532**，于 **04:26:30.351991** 真实 `wait_return=0`；runner 于 **04:26:30.352741** 写出 `runner-finished.json` 完成标记，仅证明脚本收尾完成，不等同于 runner 自身的操作系统退出码。截止后没有任何桌面、控制状态或截图请求，没有重连／热改／强杀。父已获通知桌面控制结束；此后只做文件和当前会话的只读审计。

## 本轮日志新增证据

| 文件 | 字节数 | SHA-256 |
| --- | --- | --- |
| `dosbox-startup.log` | 8918 | `4316b39a44bb707d83cd54bc72a6d163264b3781b6a7eed444e0a18dfe4d7d59` |
| `step-002-launch-isolated.stdout.bin` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `step-002-launch-isolated.stderr.bin` | 10033 | `981a7395852ca41153b7dbdca10b9bad987dc03459363f032b982c1a8aece4f8` |

stderr 明确记录本轮绝对路径 `SYN1.conf` 被加载，以及工作目录为新 `runtime/pt`；独立日志确认日志文件成功打开、DOSBox-X 2026.10.01／SDL 2.32.10、Windows 桌面 3840×2160、`OpenGL Version : 4.6.0 NVIDIA 617.42`，并记录 `pt.EXE` 执行、`GRAPH.DRV`／`TRAXEDIT.MNU` 等文件访问、640×480 图形比例及 `SYN1.PCB` 的打开请求。打开请求不等于所有字段已正确解释或 GUI 文件状态已核对；日志也不能证明没有额外配置继承。

日志含 MEM_SlowPath、代码页转换及退出时中断向量警告，本轮未定位其影响。当前可辨启动页并不证明此前黑底白线的根因已修复，也不能把新增日志选项认定为解决原因。没有进行第二后端或第二启动对照。

## 核对结果与剩余边界

`python .local-analysis/native-ft-sample/prepare.py` 及最终只读 `python .local-analysis/native-ft-sample/audit_after.py` 均退出 0；证据见 `prepare-output.txt`／`prepare-exit.txt`、`audit-output.txt`／`audit-exit.txt`。最终审计确认 11 图原 image 回执、冻结文件未变、原安装和输入完整集合未变、运行副本零变化、一个目标／一个服务、双原 Popen 退出 0，以及截止后零桌面请求。仅文档收尾，不涉及产品构建或测试变更。

本轮已获得启动页、可辨几何和主菜单、实际配置加载／日志／标准流及正常退出证据；空板、新建 FT、用户选择参数、新文件保存、原软件重开及默认编码仍未完成。后续必须在新的明确任务和现场范围内解决可预测菜单交互，再取新建／保存样例；本轮不开放新增写出、GUI 入口或 NETDEF 插入兼容能力，不修改旧 failed／runtime 未验证结论，也不创建发布、标签或合并推送 dev／main。
