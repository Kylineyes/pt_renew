# 原 AUTOTRAX 菜单选择校准

本轮先离线复核 2026-11-02 单线样例现场的原图、RPC、窗口矩形及输入通道。**File 点击坐标已经包含裁剪原点，不能将误入 BLOCK 简单归为漏加偏移；单字符 Shortcut 与 Shift 修饰的字母走不同输入通道，下一现场应优先复用已有成功记录的 Shift+I。** DOS 客体指针与菜单高亮的关系仍待实测，尚未据此核定 FT 默认字段。

本轮沿用 Pi `deng/gpt-6.1-sol high`，分支 `verify/native-menu-calibration`，fetch 后 `HEAD=origin/dev=fbda57f66abeb04e8aab574667e465b735405c9c`。模型／thinking 事件、实际 assistant 和成功工具回执见本工作树忽略目录 `.local-analysis/native-menu-calibration/session-audit.json`。随后附加监督 Task `task_5762f1bd719e`／Dispatch `ctx_001465cfe3a8`；范围仅限本报告、原软件单线保存重开报告及本地证据，不改 writer、UI、CMake，不自行合 dev 或推送。

## 原图、回执与实际观察

旧证据根为相邻工作树 `../feat-pcb-layout-boundaries/.local-analysis/native-ft-sample/`，只读。新证据索引为 `.local-analysis/native-menu-calibration/offline-evidence-index.json`，逐项保留绝对路径、完整 SHA-256、PNG 尺寸、capture-scope、原 RPC 请求／响应路径、旧 read-review、本会话 image 回执和目标 HWND／矩形。`audit_offline.py` 对全部 11 张旧图核对原 RPC image 解码 SHA，一致；本模型本次实际 read 其中 6 张原图。

| 原图 | SHA-256 前 8 位 | 本次实际观察 |
| --- | --- | --- |
| `step-003-focus-owned-post-00.png` | `eeb91275` | AUTOTRAX 1.57 启动页，VGA 640×480 提示 |
| `step-005-main-menu-post-00.png` | `5a0b27de` | AUTOTRAX 主菜单，Block 蓝底高亮，File 与 Information 可读 |
| `step-006-file-menu-post-00.png` | `b171c399` | f 后仍为主菜单，Block 高亮；没有 File 子菜单 |
| `step-007-click-file-menu-post-00.png` | `e00cd65a` | 全桌面图，目标实际显示 BLOCK，不能按 File 解释 |
| `step-008-leave-block-menu-post-00.png` | `eeeda9c1` | Esc 后子菜单消失，红外框及内部水平线仍在 |
| `step-009-information-key-post-00.png` | `8b1d7a10` | i 后无可辨 Information，不能据此读取文件名或计数 |

未在本次实际读取的其余 5 图，仅核对原字节及 RPC 回执，不冒称看过。原现场仍按[旧报告](native-ft-sample-verification.md)为 failed，不重写其结论。

## 坐标与 DPI

旧裁剪区域为 `[89,100,751,666]`，物理虚拟桌面为 `[0,0,3840,2160]`。裁剪图为 662×566，与区域宽高完全一致，换算式为 `桌面=(89,100)+图内坐标`。图中 File 行中心约为图内 `(31,170)`，故 `(120,270)` 是与图面相符的候选桌面点；原 Click RPC 确实为该点，服务回执为 `Single left clicked at (120,270)`。

全桌面 PNG 实际为 1920×1080，因此全桌面图内坐标须乘 2，再加虚拟桌面原点。两类图片不能共用一套比例；这项缩放来自 Snapshot 输出尺寸，与 Windows DPI 是不同层次。公开工具 `desktop/service.py` 明确按 max_image_size 缩图并记录比例。上述原始尺寸由 PNG IHDR 读取，未用聊天渲染尺寸猜测。

旧驱动显式调用 `SetProcessDpiAwarenessContext(-4)`，但未记录该调用返回值、`GetDpiForWindow` 或进程有效 DPI awareness。窗口观测工具自身也标注矩形受调用者 DPI 上下文影响。因此可确认旧脚本尝试使用每监视器 v2 上下文，不能宣称旧现场 DPI 交叉验证已经完整通过。新现场应记录有效上下文、目标窗口 DPI 和客户区物理位置；不直接把 DPI 百分比再乘到已验证的物理截图坐标上。

主机点击回执仅证明工具接受并执行主机点，不能证明 DOS 内部指针达到同点。旧截图未记录 INT 33h 位置、捕获状态、SDL 事件或菜单选择器读到的字符。Block 在点击前已高亮，点击后进入 BLOCK，与“点击被转换为确认当前选择”的解释相容，但不足以确认该解释。不能仅凭这些截图断言鼠标映射、原程序规则或 DPI 是根因。

## 字母输入与时序

只读核对当前安装 Windows-MCP 的 `desktop/service.py:988` 与 `uia/core.py`：单字符 `f`／`i` 直接拼入 SendKeys 字符串；没有修饰键时形成 UnicodeChar，Shift 保持状态下可匹配 CharacterCodes 并形成虚拟键按下／松开。工具文本 `Pressed f` 不等于客体收到普通物理 F 键。

[已有 verification-35 现场](legacy-menu-live-verification.md)曾在确认 ASCII 输入状态后观察到普通 i 无变化，而 `Shift+I` 实际进入 Information、`Shift+S` 实际进入 Status。该记录支持复用修饰键输入通道，不证明原程序只接受大写，也不能把本次全部无响应归于输入法。新现场若出现输入法候选条，先据图取消并单独切换当前目标输入状态，再观察。

旧五项输入的“动作回执到下一 Snapshot 请求”间隔依次为 5.358、7.484、6.481、6.116、5.836 毫秒，详见新索引。底层 SendKeys／Click 本身还有等待；这些时间既不是客体按键保持时间，也不是截图曝光时间。只能确认旧驱动无额外稳定等待，不能据一张即时图排除处理／绘制延迟。新驱动每步动作后应保留短等待，仍逐图决定下一动作，不预排菜单按键。

## 菜单资料与新现场最小目标

只读原 `TRAXEDIT.MNU`：主菜单 File 是第 5 项、Information 第 8 项；FILE 子菜单为 Clear／Dos／Files／Load／Path／Quit／Save；INFORMATION 为 Board Dimensions／Components／Highlighted Pins／Library Components／Nets／Pwr/Gnd Pins／Status。KEY 中 F3 的宏为 Esc、Esc、P、T、Enter，F4 为 Esc、Esc；这些是文件内容，不替代运行证明。

[既有静态路径](legacy-menu-keypath.md)说明菜单选择器处理首字母、方向键、Enter、Esc，主循环 Enter 唤出主菜单；[独立复核](legacy-menu-static-validation.md)说明 Status 按 Esc 返回可避开报告输出，而 Enter 会进入额外 SAVE FILE NAME 询问。本轮未新做二进制逆向，也未重试此前 quota 失败的 GLM。

新现场先以 Shift 修饰字母和单步方向键／Enter核对 File、Information 的可预测进入和 Esc 返回，取得当前文件名与图元计数，再确认空板。菜单可靠后才明确层、宽、起终点创建单线、以不存在的 8.3 文件名保存并由原软件重开。每步实际读取原图，保存新 RPC、完整文件摘要和原创建者 wait 退出回执；新桌面时段另行预告。未取得这些证据前，六／七字段及附加值仍未核定。

## 本轮现场准备的实际结果与暂停

截至 2026-11-02 北京时间 12:10，**两次均未启动 DOSBox，未发送 App／Click／Shortcut／Type，未创建 FTNEW.PCB**，不能称已实测 File／Information、空板或新建 FT。现场证据位于 `.local-analysis/native-ft-created-roundtrip/`，第二次位于其 `attempt02/`；汇总见 `checkpoint-ui-handoff.json`。

第一次预告时段为 11:25–11:40，实际新控制服务于 11:26 后启动并取得一张基线，指定模型实际 read。我的请求辅助脚本将 PowerShell 内联 JSON 直接传给 Python，引号在原生参数传递时丢失，且脚本先创建请求文件再解析；空文件被驱动读到，于 11:30:10.306881 本地 JSONDecodeError 停止。该错误不是公开控制门拒绝，没有启动目标。驱动完成 120 秒零桌面请求后，服务原创建者于 11:32:10.770128 真实 wait=0，runner 原创建者于 11:32:10.780373 真实 wait=0。完成标记不代替这两个 wait 回执。

修复只涉及本地请求发布：用 write 生成结构化暂存文件，先解析并验证，再原子改名到唯一收件箱；不再把 JSON 内联到 PowerShell 原生参数。离线检查确认损坏 JSON 不发布任何请求、有效请求原子发布，实际桌面调用为 0，回执为 `attempt02/request-offline-check.json`。新驱动每步动作后增加 0.6 秒稳定等待并记录 DPI 设置结果／窗口 DPI；这些代码尚未经目标窗口验证，不记作行为通过。

第二次预告为 12:07–12:22；定时 owner 于 12:06:59 启动，随后新服务仅取得一张基线。协调者此前于 UTC04:04:13 发出高优先级排程调整消息 `msg_3610cf6341e3`，我在再次启动前没有及时 check，直到收到紧急提示后的 12:07:48 才读取到；因此这次服务和基线是在尚未处理的停止排程之后发生，须明确保留这项不足。收到后没有启动 DOSBox或业务输入，实际 read 基线，原子提交 Stop，服务 PID44860 于 12:10:06.617968 真实 wait=0，runner PID63020 于 12:10:06.628963 真实 wait=0。两项创建 FILETIME、原 Popen identity／handle、原 RPC及 PNG SHA 均留在对应原 JSON，以 Python int／原文本保存，不经 JS Number 转换。

最终离线审计确认：原安装 99 项、两份各 99 项 runtime 及冻结输入完整路径集合／大小／SHA-256 前后一致；两次各一张新基线由本模型实际 read，本会话 image 解码 SHA 与原 PNG 及原 RPC image 一致。服务／runner 四项原 wait 均为 0，目标启动均为 0，输出不存在。当前桌面已结构化交还协调者供 UI 验收；同 Task／Pi 会话保持，**协调者再次明确移交前只做离线工作**。上述暂停不是原软件单线闭环完成，也未向当前 Task 发送 worker_done。

本次只改研究说明与忽略目录证据，不改产品，因此不重复 Qt 构建或 CTest；Debug／Release 各19/19仍为交接中的既有证据。本报告提交前执行 `git diff --check`，不合 dev、不推送、不操作 main。

后续正式移交的13:35–14:05现场已结束：新DOSBox实际运行，但稳定窗口图及目标物理屏幕均不可辨，未发送客体业务按键，原目标正常wait=0。未取得原生新建单线样例，完整事实、原图回执／摘要及未执行的单Return建议见[单线保存重开取证报告](native-ft-created-roundtrip.md)；本Task整体按failed结算，离线坐标与输入通道的确定事实仍保留上述范围。
