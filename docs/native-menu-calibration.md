# 原 AUTOTRAX 菜单选择校准

本轮先离线复核 2026-11-02 单线样例现场的原图、RPC、窗口矩形及输入通道。**File 点击坐标已经包含裁剪原点，不能将误入 BLOCK 简单归为漏加偏移；单字符 Shortcut 与 Shift 修饰的字母走不同输入通道。** 当时依据既有成功记录建议优先复用 Shift+I；后续 EX-005 的相同公开参数却出现 IME 候选框，因此该建议不构成普遍保证，最新[原 AST／假 API 结论与消费者边界](#shortcut-offline-semantics)已限定其范围。DOS 客体指针与菜单高亮的关系仍待实测，尚未据此核定 FT 默认字段。

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

<a id="explore-ex-003"></a>

主机点击回执仅证明工具接受并执行主机点，不能证明 DOS 内部指针达到同点。旧截图未记录 INT 33h 位置、捕获状态、SDL 事件或菜单选择器读到的字符。Block 在点击前已高亮，点击后进入 BLOCK，与“点击被转换为确认当前选择”的解释相容，但不足以确认该解释。不能仅凭这些截图断言鼠标映射、原程序规则或 DPI 是根因。

[探索 EX-003](exploration-backlog.md#ex-003)。

## 字母输入与时序

只读核对当前安装 Windows-MCP 的 `desktop/service.py:988` 与 `uia/core.py`：单字符 `f`／`i` 直接拼入 SendKeys 字符串；没有修饰键时形成 UnicodeChar，Shift 保持状态下可匹配 CharacterCodes 并形成虚拟键按下／松开。工具文本 `Pressed f` 不等于客体收到普通物理 F 键。

[已有 verification-35 现场](legacy-menu-live-verification.md)曾在确认 ASCII 输入状态后观察到普通 i 无变化，而 `Shift+I` 实际进入 Information、`Shift+S` 实际进入 Status。该记录支持当时场景的修饰键通道，不证明原程序只接受大写，也不能把全部无响应归于输入法。后续同公开 Shift+I 的 IME 失败见[输入通道边界](#shortcut-offline-semantics)；遇候选框应按当前冻结方案停止及收尾，不能将本节历史切换建议当作取消、改 IME 或绕过拒绝的现时批准。

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

## Shortcut 原 AST 的离线通道核验

<a id="shortcut-offline-semantics"></a>

本节接续 [EX-003](exploration-backlog.md#ex-003)，Task `task_ca301710c5c6`／Dispatch `ctx_40040264e92f`，分支 `research/ex003-input-semantics`，证据 `.local-analysis/ex-003/`；沿用 Pi `01a1cb98-e57e-75d0-9b06-c40a941eaaf0`，原 UTF-8 JSONL 的模型／thinking、assistant、环境及成功工具回执均为 **`deng/gpt-6.1-sol / high`**。领取先由父同步共享 dev。**本轮严格纯离线，EX-003 完整条件仍未满足，保留受阻**；没有新桌面查询、COM/UIA、截图、原软件／控制服务、键鼠、IME 设置或 GO。控制总窗口于 UTC 20:02:12 结束，没有延续现场。

只读消费父原 `check_shortcut_semantics.py` 和 `audit_menu_click.py`，未执行会写回旧证据的顶层。前者已证明 F11+p 非保持组合及 Shift+I 的粗顺序；本轮补齐公开入口、真实扫描码函数、Unicode INPUT 构造、底层返回值和异常边界，不重写安装函数或控制框架。

### 来源、提取及支持范围

以下均相对已安装 `windows_mcp` 源码根 `C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Lib/site-packages/windows_mcp/`，不导入该包。选中节点保留原函数逻辑，移除装饰器，`ctypes.windll.user32` 指向仅记录调用的假对象；INPUT／KEYBDINPUT 结构只在内存构造。MapVirtualKeyA 和 SendInput 的返回值明确为测试值，没有查询实际 HKL、键态或接收者。

| 源文件／主要原定义 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `tools/input.py:418`，`shortcut_tool` | 19426 | `eb3bd88f950fcc76e8e9a11032363781c9c898eeb87aa9e8b74dd970361a2943` |
| `desktop/service.py:988`，`shortcut` 及第47行别名表 | 68704 | `c116adc0d221c993a89596a14f0ac66bf924e250672cb2691a8914b0e788231e` |
| `uia/core.py:246,1371,1390,1462,1485`，`keybd_event/SendInput/SendUnicodeChar/_VKtoSC/SendKeys` | 92107 | `3638d7ba96d7b918783e6e95b95af9978ae7a0df5b200e0966e47e56921f170e` |
| `uia/enums.py:1064,1216,1399,1551,1661`，事件 flags／VK／命名与字符表／INPUT 结构 | 78802 | `9da1086764fffe967186cdcc6f8afa7f164971e16d72e0c9aaa8eb3ac90607c1` |

四文件在回放前后逐字相同。另只读分析 `__main__.py`、`uia/__init__.py`、`infrastructure/analytics.py`、`desktop/control.py` 和 `tools/control_notifications.py` 的装饰器／线程／门禁范围；连同两个旧 AST 脚本及 EX-005 原请求／响应／窗口 JSON／PNG，共18个来源在收集期大小与 SHA 前后一致。逐定义源文件、行号及 AST SHA 见回放结果，辅助原始来源清单见 `source-evidence.json`，没有复制整套包或提交第三方源码。

工具 [replay_legacy_shortcut.py](../tools/replay_legacy_shortcut.py) 只执行已核选中定义及假 API，输出排他新建；拒绝选中 AST 中导入、动态执行、文件访问和反射入口，内建命名空间也不交给原函数任意访问。Python 3.15 的结构元类所需标准库内存布局仅列明放行，不加载真实 user32。本工具用于已核安装源码，假回放**不执行公开 MCP 门、analytics 装饰器、通用 worker 线程或 hook，也不把跳过这些层的成功当公开门通过**。

### 原函数实际分流和参数

公开 `shortcut_tool` 先调用 `get_desktop().shortcut(shortcut)`，无异常后直接返回 `Pressed {原参数}.`。service 按 `+` 分段并逐段 strip：单字符原样拼入 SendKeys 文本，多字符加 `{}`，少数别名先替换；`uia.SendKeys(..., interval=0.01)` 没有指定 charMode，沿默认 **True**，waitTime 沿常量 **0.5 秒**。命名键查表时 upper；普通字符保持大小写，只有 hold 状态才用 CharacterCodes 转成 VK。

| 公开参数 | service 交给 SendKeys 的文本 | 原解析所得底层通道 |
| --- | --- | --- |
| `shift+i`／`Shift+I`，含分隔符两侧空格亦同 | `{shift}i`／`{Shift}I` | Shift down → VK_I down → VK_I up → Shift up，走 `keybd_event`，没有 Unicode INPUT |
| `shift+s` | `{shift}s` | 同样保持 Shift，字母改为 VK_S（0x53） |
| `enter`／`return` | `{enter}`／`{return}` | VK_RETURN（0x0D）down／up |
| `esc`／`escape` | `{esc}`／`{escape}` | VK_ESCAPE（0x1B）down／up |
| `down`／`up` | `{down}`／`{up}` | 对应命名 VK_DOWN（0x28）／VK_UP（0x26）down／up；仍不能保证不经 IME 或客体必接收 |
| `i`／`I`／`s` | 原字符 | `SendUnicodeChar(char, True)`；wVk=0、wScan 为 U+0069／U+0049／U+0073，flags 4／6 的两次 SendInput，不会自动加 Shift |
| `f11+p` | `{f11}p` | F11 down／up 完毕后 Unicode p；F11 不是保持键，沿用既有否定结论 |

Shift+I 的原 API 参数可以写成 `keybd_event(0x10,s(0x10),1,0)` → `(0x49,s(0x49),1,0)` → `(0x49,s(0x49),3,0)` → `(0x10,s(0x10),3,0)`。这里 **1=KeyDown(0)\|ExtendedKey(1)**，**3=KeyUp(2)\|ExtendedKey(1)**；它是 VK 注入调用，**不是物理键盘事件证明，也不是以 flag8 的 scan-only 注入**。`s(vk)` 为原 `_VKtoSC`：generic Shift／I／S／Enter／Esc 调 `MapVirtualKeyA(vk,0)`，左右修饰键等可命中固定 `_SCKeys`；返回0时继续传scan=0，并不拒绝。回放使用的 Shift=0x2A、I=0x17 等扫描码是显式假返回，不是读取到了旧现场扫描码或服务线程布局。

Shift+I 四个键事件后各有名义10ms睡眠，再等0.5s，假时钟总 **0.54 秒**；Enter／Esc 两事件总 **0.52 秒**；单 Unicode 字符只有 INPUT 对之后10ms加0.5s，总 **0.51 秒**。这不是实际持键时长或 Windows 调度上界。普通 `I` 仍是大写 Unicode 码点，不能靠把参数 `i` 改成 `I` 宣称绕开 IME；`Shift+i` 与 `shift+I` 在该映射中是同一 VK 路径。

字符不在 CharacterCodes 时还有边界：假回放 `shift+中` 得到 Shift down／up 后才发 Unicode 中，不是把未知字符保持在 Shift 内；补充平面字符通过原函数拆成两个 UTF-16 单元、各 down／up（如 U+1F600 的 D83D、DE00），不是一个截断 WORD。字面参数 `+` 被 service 切成空段后形成 `{}{}`，本机原解析最终在 `ord()` 对双字符报 TypeError，未调用假输入 API；它不是可靠表达加号的已验证公开参数。

### 成功文字、失败与控制门的分层

1. **VK 层**：原 `keybd_event` 包装是 void 调用，没有接收窗口或客体确认；假返回0不构成真实 API 有布尔失败码的证据。MapVirtualKeyA 返回0仍可生成四个 VK 调用和相同成功文字。
2. **Unicode 层**：原 `SendInput(*inputs)` 每个 INPUT 各调用一次 `SendInput(1,...)`，只返回最后一次 ret，非总插入数；`SendUnicodeChar` 的值又被 SendKeys 忽略。假序列 `[0,1]`、`[1,0]`、`[0,0]` 都仍返回 `Pressed i.`。这证明返回传播缺少检查，**不证明旧现场 SendInput 曾返回0**，且插入数本身也不是目标消费回执。
3. **工具层**：service 在 SendKeys 前执行 `checkpoint_current`，完成后 `record_step_current` 一次；整个 Shortcut 是一个记录步，不能把计数1当四个 Win32 事件逐个已送达。假 checkpoint 拒绝时零 API、无成功文字；假第二个 keybd_event 抛异常时只留下 Shift down 和尝试的 I down，无后续 Shift up／record-step／Pressed，原 SendKeys 没有局部 finally 事务回滚。真实门、hook和其他清理是否处理相应状态未在此验证，不从假异常断言旧现场有卡住的修饰键。
4. **真实调度层**：安装的 Shortcut analytics 包装默认 `run_sync_in_thread=True`，静态定义会由 `asyncio.to_thread` 运行；不是在本轮证明了旧调用使用哪个线程 ID／HKL／输入队列。ControlToolGate 负责租约、context和异常映射，原服务 checkpoint 受 current-token 控制；该真实层本轮只读未运行，不能绕其拒绝或把假 controller 当控制授权。

### IME 与下一次状态核定可消费的边界

[EX-005 的原始失败](legacy-dosbox-configuration.md#ime-state-boundary)保留：一次 Enter 后板图可辨，随后相同公开 Shift+I 得到成功文字，但宿主出现 IME 候选框，没有 Information 后验；完整静默、正常退出及十二张原图的范围不改写。早期 C21／A240 曾在当时输入状态下通过同类公开通道进入 Information／Status，同样保留。**本次只证明 VK／Unicode 的源码分流，既不能以候选框证明所有事件被 IME 消费，也不能以旧成功或 `Pressed` 排除 IME／线程／队列差异。**

服务源码在该路径没有向目标 HWND 定向输入，也没有在这些函数中核实际字符、SDL／INT33h、客体菜单选择器或 IME 开关。generic worker、自有 mapper 的US记录、原生前景与同线程候选窗各有范围；它们都不恢复旧服务输入线程 HKL、实际接收窗口、低层 hook 完整处理或 DOS 侧键码。因此不能宣布“Shift+I 的全部根因已定位／IME已修复”，更不能切换到低层输入接口绕开公开门。

给未来新明确场景的最小建议是：先据当前客体图确认菜单上下文，再只改变一个公开参数或一个已声明观测条件，逐个输入后以新客体图验收。若选择命名 `enter/up/down/esc` 的菜单导航路径，本节可证明它使用对应 VK 而不是普通字母 Unicode；**是否更可靠仍要新现场证明**。大小写改写、盲目补发 Shift、清键态或改变全局输入法不由本节授权。没有新有效现场窗口时仅准备离线材料，不能写 GO；下一状态场景仍须遵守公开门、一次请求、失败静默及原创建者正常等待。

### 本轮验证与剩余事项

新增[回归测试](../tests/test_replay_legacy_shortcut.py)验证原 AST 的16项行为与提取边界，已分别在当前Python3.15及现有基础Python3.14.8执行，均16/16通过，未下载解释器；另有23个完整假回放案例。它们含 Shift 精确键序／flags／假扫描码、命名别名、大小写分流、Unicode UTF-16、SendInput 0 返回仍回成功、扫描码0、checkpoint零输入、半程异常不返回成功和输出不覆盖。测试不 import windows_mcp／COM/UIA，不加载真实 user32、不发送事件，来源四文件逐字未变。

原始失败也保留：最初受限命名空间执行 future-import 及 Python3.15 ctypes结构布局时因缺导入白名单停止，之后一次缺 enumerate 的 NameError 出现在报告内，未据生成文件宣称通过；补齐已加载标准库布局和内建枚举后，第一次测试又把 `+` 的真实 TypeError误预期为ValueError，修正测试解释后通过。未改第三方源码来迎合测试，旧失败输出与原会话记录保持。EX-003仍缺完整实际输入通道→客体响应及坐标／捕获／状态对照，保留[原事项](exploration-backlog.md#ex-003)及剩余条件，本轮不删项。最终文档检查 **153 份 Markdown／1045 个本地链接／41 个开放事项／106 个来源细节／137 份索引报告，零错误**，`git diff --check`通过。仅清理可重建成功中间输出／本轮模块缓存 **134608 字节**，归档占用 **0**，净减少 **134608 字节**；清理时证据约 **155 KB**，没有新运行副本、下载或构建树。所有自有短时诊断子进程均由原 `subprocess.run` 等待返回0，没有本轮原软件／控制服务可声称的新退出证明，也未为清理查询桌面或全机进程。

## 新窗口命名键导航：第一段至 Grid 的有限事实

<a id="named-navigation-live"></a>

本阶段接续 Task `task_db06ca9d4229`／Dispatch `ctx_e3ea7d528345`，Pi 仍为 `01a1cb98-e57e-75d0-9b06-c40a941eaaf0`、`deng/gpt-6.1-sol high`，分支 `research/ex003-live-navigation`。用户另开四小时、后来延长为同起点七小时的控制总窗口；本段仍只用父首次审批的 **UTC 2026-11-12 02:22–03:02，02:55 起仅收尾**，没有以总授权延长运行中 GO。[EX-003](exploration-backlog.md#ex-003)仍未完整闭环；下列是成功的有限命名键响应，不改写旧 Shift+I／IME 失败或宣称已到 Information。

新槽 `.local-analysis/ex-003-live/candidate/slot/`，plan SHA-256 `60e0824f4c6d7b22f15697fbe0ef3c6ea0010f74d00d65613abf99704beb40a2`，driver `193b148a6b08fc7cea90819bd89ef991c572b4dad67638f9e3a9cf516ce495c4`，gate `6ac935bb76a13e6d88bc4b66a1e4903a1cbd542c4a0e508009838120d34e3371`。23 冻结项／99runtime／1input预检通过，新目标 PID48992、创建FILETIME `134389238133484395`、HWND5575388 由原 Popen 绑定。兼容32样本无失败、最大单样本9.8639ms／启动间隔20.2243ms，线程真实join；没有输入法或系统设置改变。

| 本轮新客体原图 | 输入前后实际观察 | 允许支持的范围 |
| --- | --- | --- |
| `pt_000.png` | AUTOTRAX1.57、PRESS ANY KEY TO START | 只据当前启动页发送一次命名Enter |
| `pt_001.png` | 启动Enter后板图：矩形四边+横线 | 当次启动转换，底栏不当文件名或计数 |
| `pt_002.png` | 主循环再一次Enter后，主菜单出现，Block蓝底高亮 | 当次命名Enter打开主菜单成立 |
| `pt_003.png` | 第1个独立Down后Current高亮 | 与上一步相比向下一行 |
| `pt_004.png` | 第2个独立Down后Delete高亮 | 未确认Delete，不是执行删除 |
| `pt_005.png` | 第3个独立Down后Edit高亮 | 未确认Edit，不是进入编辑 |
| `pt_006.png` | 第4个独立Down后File高亮 | 未进入File或文件操作 |
| `pt_007.png` | 第5个独立Down后Grid高亮 | 未进入Grid或改变网格 |

每个命名键后都逐步实际 read 宿主、当下 Capture 菜单及新640×480客体，nonce／完整图片列表／原字节SHA绑定到当前步；不是把MNU的Information第8项当运行高亮证明。共 **27张唯一宿主PNG+8张新客体PNG=35张**，原字节均匹配本Pi原UTF-8 JSONL的实际image回执，各轮全目录集合差恰一新增且旧图未改删。宿主仍黑底白线，客体却能看到板图／菜单；没有候选框或未知键响应，不将这些有限成功泛化为IME已经修复。

逐步三类原图读取与模型往返实际占用了大部分40分钟分段。第5Down后已接近02:55业务截止，不足以安全完成其余两次Down、Information确认和逐图取证，因此**正常停止新业务**；未发送第6/7Down、Up、Information确认或Esc，没有进入Information子菜单。没有现场拒绝／`stopped-error`，也没有将正常预算结束伪造为需要120秒静默的失败。第一段的高亮和Grid只能描述该已退出目标，未来新槽必须从新当前图重建状态。

仅生命周期取新当前图、一次正常宿主X后，目标原Popen于 **02:58:58.180712 wait0**；服务PID6244于 **03:00:15.366146 wait0**；driver PID44092于 **03:00:15.374794 wait0**；owner PID56148由原.NET Process持柄WaitForExit=0于 **03:00:15.3876233**。四组PID／创建FILETIME／映像／原HANDLE及适用Popen identity均与创建记录匹配，观测线程join。全部在03:02原分段截止前结束，无Alt+F4／强杀／第二控制连接。外层隐藏PowerShell自身无原Popen退出证明，不从下层wait0外推。

本轮19项新门用例、当前driver40步纯AST假main（12张假客体）及13项停止阶段注错通过；假记录不证明实际菜单已到Information。原安装99、旧双槽包399、EX001证据584、EX004证据336、EX005证据387、前次EX003离线证据29以及本轮runtime99/input1完整集合／大小／SHA前后不变，`NEWFT.PCB`未产生。证据在 `.local-analysis/ex-003-live/live-audit.json` 及第一候选的原图／trace／请求／GO／退出原件；旧证据只读，不通过重启第一槽接续。下一段预算须在新冻结方案中明示，现有owner/driver的起止上限为3600秒，不能将65分钟直接套入旧入口；本Task保持未结，父先验收全新第二槽及新时段后才继续。

### 第二槽早发拒绝、入口防护及第三槽路径隔离事故

<a id="path-isolation-incident"></a>

**当前暂停全部新现场与归档精简，本Task未完成，不能用旧GO恢复业务。** [EX-003](exploration-backlog.md#ex-003)保留受阻，原Task/Dispatch未结。第一槽到Grid的逐键成功与正常退出仍保留；第二槽与第三槽分别是入口时刻错误和配置隔离失败，均不属于“命名键/IME已修复”证据。父用户随后要求新协调agent接手，本worker停在离线检查点，未另建交接文档，当前权威接手状态仍由[HANDOFF](../HANDOFF.md#plan)维护。

第二槽曾获批03:25–04:25，但操作者03:24:28提前约32秒调用入口。原owner21372由原.NET Process/HANDLE取得 **wait1于03:24:30.1868015**；其GO时段校验在driver／控制服务／目标创建前拒绝，零桌面请求。原GO撤销、该槽不重试。已提交 `f7f6dca` 的自有BOM入口在任何现场进程创建前增加plan摘要／身份／槽路径／实时时段校验及已启动marker拒重试，原owner/driver校验不取消；真实PowerShell `-File`／`PreflightOnly`／假创建3项和3600秒接受3900秒拒绝的3项边界测试通过。第三槽在03:45之后先PreflightOnly通过再唯一正式入口，没有再早发。

第三槽plan `b7a471bab84495cf12ec52c373c72454845bffd281ffe4eabcbe884baad0f21f` 经审批于03:45–04:45运行。新目标PID28820／HWND855124、兼容33样本／join及Capture菜单读取通过，默认选择截图项一次；公开Click响应成功、183个采样无失败。**本槽captures仍空**，完整集合差在 **03:52:37.330696** 拒绝“单次捕获必须恰一张新PNG且无其它新文件”。没有发本槽启动Enter、Down、Shift字母或IME设置，也没有重发截图。完整 **120.001448秒**零新增桌面请求，quiet-ended03:54:37.332144后仅当前图正常X／原WaitExit；目标28820、服务19000、driver45320、owner41048四组原创建／退出身份匹配且wait0，最晚 **04:01:50.4556775**。正常退出只证明生命周期，不证明隔离成立。

事后只读核查发现本槽日志缺失，实际 `SYN1.conf` 仍保留旧 `review-track-core-boundaries/.../final-candidate/slot-retry-01` 的 **logfile、captures及C/D双mount**；本槽conf SHA `e2931daeac67ece9c8f0b64012814ec334066c45f0b315580a3f54d7a57b9486` 恰与旧模板一致。早期stderr明确新conf文件被加载，却随后打开旧逻辑路径的日志；错位新PNG实际进入旧captures，不作为本槽捕获通过或新导航证据。

精确根因为：`prepare_legacy_click_observation.py`先对只读来源 `Path.resolve()`，而旧工作树已由父核验迁入归档、原路径成为目录联接；解析结果为 `C:/Users/rikideng/orca/worktree-archives/pt_renew/20261112-cleanup/review-track-core-boundaries/tree/...`。模板文本仍是旧workspaces逻辑路径，生成器用已resolve的物理根做无命中断言的字符串 `replace`，**匹配0次**后继续冻结。第一槽和第二槽在联接迁移前已正确重绑，第三槽未重绑；事后保全的三conf中前两份各含当前槽根4次／旧根0次，第三份当前槽根0次／旧根4次。摘要和输入集合预检只确认“这些字节与计划一致”，没有校验conf内部路径，操作者和父审阅均漏查；不能归因IME、原程序导航或第三方安装。

以本Task `readonly-before.json` 的旧399项基线逐项对比，父独立审计亦一致：

| 差异 | 本轮事故后实际内容 | 原记录及可恢复限度 |
| --- | --- | --- |
| 新增 `slot-retry-01/captures/pt_000.png` | 6155字节，SHA `e473d5d1817063b927ca7493c3920f78b6282ccf4ed70f87badaf9161ad665e6` | 原基线没有该文件；保留错位文件，不删或搬回新槽追通过 |
| 修改 `slot-retry-01/dosbox-startup.log` | 9038字节，SHA `d41cddaa69f8ab0fa24b592ded8d8c957073132dd4630684daeb6a98c08666bb` | 原8846字节，SHA `fc4680bc51d3c8c0e17672cbc5f8d3d14956c7d3f39acdab8d36058e7ab8ab34`；清单不能恢复原字节 |
| 其余旧来源 | 无缺失，其余原文件大小／SHA一致；旧runtime/inputs未变 | 原安装99项及EX001/004/005/离线EX003清单仍一致；这不证明没有瞬时写入同字节 |

旧包当前400项清单、改写日志／新增PNG的事故后字节及三conf已保全在本树 `.local-analysis/ex-003-live/path-incident-preservation.json`、`path-incident-current-bytes/`、`third-path-boundary-audit.json`；父另有 `main-2/.local-analysis/config-path-incident-20261112/` 独立保全。没有覆盖恢复旧日志、删除新增PNG、改旧manifest／冻结审核或原JSONL。此前“旧399项未变”仅适用于第三槽污染前；第一段当时的核验仍成立，**不能把其前后未变结论延续到事故后**。

旧日志副本搜索限定范围：父在现有归档根／main-2忽略目录／活动树普通文件中未找到任何8846字节副本；本worker只读检查6个现有项目ZIP的8846字节条目和相关三个工作树Pi完整toolResult日志文本／换行变体，也无目标SHA精确匹配。未扫所有外部备份、任意7z或拼接部分回执；准确结论是**此范围未找到完整旧副本，恢复可行性尚未知**，Git bundle通常不含被忽略日志，不能当可恢复备份。事故后文件另存仅用于证明污染后状态。

截至UTC04:30暂停检查点，根因／保全／精确差分／窄搜索已完成；当时新 `tools/legacy_runtime_config.py` 只有配置解析、语义重绑和逻辑／物理路径检查的**未完成草稿**，尚未接入、无语义测试，仅AST语法检查。该历史状态保留；后续离线修复和验证见[下一节](#isolation-offline-repair)，不把文件存在当作修复或现场已获批。原Task保持未结，事故暂停解除前不写GO或运行新候选，EX-003/005/007均未因此闭环。

### 恢复原Pi后的离线隔离修复与可审边界

<a id="isolation-offline-repair"></a>

本轮按最新用户和协调者的明确范围，**仅完成离线实现、合成回归和文档，不启动第四槽或新现场**。[EX-003](exploration-backlog.md#ex-003)保持受阻和原完整条件。原Pi `01a1cb98-e57e-75d0-9b06-c40a941eaaf0` 在执行期异常退出，旧 Dispatch `ctx_e3ea7d528345` 的 failed／process_exited／退出码1073807364及连接ECONNRESET保留；恢复同一原Pi后核环境和原记录仍是 `deng/gpt-6.1-sol high`，由当前协调者以同Task重新绑定 `ctx_ed7b7e9ec944`／终端 `term_cb09ddcf-d398-4302-b953-639d97951adf`。没有冒用失效旧Dispatch、换模型、新建同义agent或恢复旧GO。旧七小时窗口已到期，事故与归档精简暂停继续，[EX-003](exploration-backlog.md#ex-003)整体受阻。

新增 [legacy_runtime_config.py](../tools/legacy_runtime_config.py) 是针对当前已审DOSBox小配置的严格解析器和语义预检。生成器从模板计划声明的**逻辑slot**校对唯一 `[log] logfile`、`[dosbox] captures`、autoexec中的C/D两个挂载和启动输入，随后重建为新slot，不再对resolve后的源根做字符串替换。缺失、重复、额外章节／属性／命令、旧根残留、不在白名单的重定向或启动参数均拒绝。只读来源可由归档联接访问，但**可写候选在resolve之前保留原始逻辑路径**；逻辑路径与物理路径不等、联接、文件／目录符号链接、重解析点或多硬链接文件都不能进入可写树。模板校验失败发生在复制运行输入和新候选写入之前；四种准备器完成各自修改后还分别执行最终语义门，不用基类已过替代派生结果。

| 执行层 | 实际接入的隔离检查顺序 | 拒绝时离线已证明的范围 |
| --- | --- | --- |
| BOM PowerShell外层／子层入口 | 保留原GO摘要／身份／实时时段门和已有marker拒重试；正式创建owner前以 `python -B` 执行只读语义预检；`OfflineCheck`／时段 `PreflightOnly` 保持创建前退出 | 非法路径计划不创建owner／driver或其输出；最外层保留逻辑slot，不先Resolve-Path丢别名 |
| 原Popen owner | 逻辑slot读取计划后先完整隔离预检，再保留原GO／冻结验证，最后才打开driver日志和Popen | 无效计划零driver创建，零driver stdout/stderr文件 |
| 生成driver模块顶层／main | ROOT由原命令行取逻辑绝对路径；桌面模块导入、DPI调用及首次runner日志前校验；main再次校验后才构造Rpc／采样器 | 无效计划零桌面导入／DLL查询、Rpc.start、自动baseline或采样 |
| `Rpc.start(plan)` | 先检查再开控制流；创建局部profile后、服务Popen前再检查；失败关闭已开的流 | 非法计划零服务Popen；服务创建异常不泄漏stderr／raw句柄 |
| 目标Launch | 原preflight保留并调用语义门；开目标流前及Popen前再次核路径／完整输入 | 初始错误或预检后计划变化都零目标Popen／后图；Popen／校验异常均关闭父stdout/stderr |

语义门核 `slot`、实际ROOT、实际driver路径、`launch_argv` 的Python／`-B`／driver／slot、目标cwd／唯一 `-conf`／PCB输入／新输出，以及公开MCP入口的固定AST／参数。配置与driver、门、submit、目标映像、验证模块的冻结字段还须互相一致；输入完整集合／大小／SHA和去DFT策略也在启动入口重新核，摘要正确不能替代路径归属。目标和控制服务的用户／临时／缓存环境只作子进程局部映射，不修改系统持久设置。控制服务原有 `-I` 会忽略Python环境禁写字节码值，因此显式增加 **`-B`**，driver及owner同样显式禁写pyc，不能仅凭 `PYTHONDONTWRITEBYTECODE` 声称只读源码无缓存写入。

| 可写类别 | 允许范围 | 只读来源与限制 |
| --- | --- | --- |
| 框架JSON／JSONL／PNG／BIN／LOG、inbox和原创建／退出证据 | 当前slot根及slot/inbox | 候选driver、gate、submit／SYN1.conf、仓库工具不作为框架输出目标 |
| DOS日志和原生客体PNG | `slot/dosbox-startup.log`、`slot/captures` | 旧逻辑工作树／物理归档根均不是写入目标 |
| DOS挂载、启动输入及允许的新板输出 | C/D都仅 `slot/runtime`；cwd `slot/runtime/pt`，输入SYN1.PCB，新输出NEWFT.PCB | 原安装、介质、用户库板图与旧冻结runtime只能作读取来源；运行文件必须独立复制且单硬链接 |
| 已审CONFIG只读探针的重定向文件 | 固定命令分别到 `slot/runtime/CFGINFO.TXT` 等7个已知TXT名 | 不接收D盘变体、附加命令、额外文件或任意重定向 |
| 子进程profile／临时／缓存 | `slot/service-profile`下的user／roaming／local／temp／config／uv-cache／pycache子目录 | USERPROFILE／APPDATA／LOCALAPPDATA／TEMP／TMP／XDG_CONFIG_HOME／UV_CACHE_DIR等仅子进程局部值；新环境的真实DOSBox／MCP兼容性尚未实机验证 |
| 可执行和模块读取 | 原base Python、目标EXE、公开windows_mcp入口／相关源码、仓库验证与owner工具、旧已审自有模板 | 清单按计划冻结并单列；本轮只读取来源，不导入控制包或启动目标 |

合成夹具实际建立“逻辑来源目录联接≠物理归档路径”，精确复现旧replace零次的前提，click／capture／state／navigation四种生成器均正向生成正确逻辑/物理归属的**假数据包**；没有生成第四现场槽／GO。派生阶段被注入旧/未审路径后最终门拒绝。覆盖旧logfile／captures／C/D挂载、启动输入输出、额外-conf／控制脚本参数、CONFIG额外重定向、目标目录别名、目录联接、文件symlink和5类真实硬链接共享写风险；硬链接例和symlink权限例已经分开，不能因后者权限跳过掩盖前者。本机此次文件symlink实际可建并拒绝，最终未跳过。

最终隔离回归 **21/21** 在现有Python3.15和基础3.14.8各自通过，启用ResourceWarning错误检查；另保留真实PowerShell5.1文件加载／提前起跑 **3/3**、60分钟／65分钟预算边界 **3/3**。有效配置正向例包含原owner main及当前driver真实Rpc.start／Launch分支，Popen、线程、identity和后续观察全部为假对象；错误计划分别执行实际PowerShell入口、owner main、driver顶层前缀、main、Rpc.start和Launch，明确证明未越过driver／服务／目标／baseline／键鼠创建点。测试不只调用独立路径函数，也没有用“全部拒绝”冒充修复。

原失败保留：中断前隔离14项中1 error，为Launch后二次门测试的流句柄未关导致tearDown WinError32，伴ResourceWarning；当时owner3项虽过，整体隔离不能写通过。修复以 `with` 管理目标父流、服务异常关闭其流，补Popen异常正反回归后不再出现句柄警告或残留句柄；恢复前最后两次edit已核落盘，连接异常和旧测试结果不覆盖。最终日志保存在本Task `.local-analysis/ex-003-live/offline-repair/`，原异常见原JSONL，本轮不改其历史内容。

测试前后再次核事故后旧包 **400项**与本Task保全清单完全相同，原安装 **99项**不变，三conf仍为各自历史SHA；没有回滚9038日志、删除错位PNG、修改旧manifest／冻结审核／原JSONL，也没有重复扩大旧日志副本搜索。修复的证明范围是**当前小配置和受控合成文件／假创建边界**：不提供操作系统级文件沙箱，不保证敌对进程在检查与open/Popen间并发换链的TOCTOU消除，不验证所有DOSBox语法、未知第三方写入口或新profile真实兼容。新的语义检查不使三个旧槽合法，也不恢复旧日志字节；后续若需现场，必须另获明确范围／全新冻结和GO，本轮不执行。最终文档检查 **153 份Markdown／1057个本地链接／41个开放事项／108个来源细节／137份索引报告，零错误**，`git diff --check`通过；首次索引因同专题两个链接计为重复，已合并单入口后复跑。只清理本Task可重建失败夹具和模块缓存 **122708字节**，归档占用0、净减少122708字节；先记录夹具集合/摘要，原WinError32和中断失败回执保留。所有旧输入/PNG/日志/三槽和事故保全不清理，不以同盘移动或假Popen算真实退出/空间收益。

父集成到另一工作树后真实复测发现测试根 `.local-analysis/ex-003-live` 尚不存在，21例都在setUp的TemporaryDirectory阶段报FileNotFoundError，隔离断言没有执行；原研究树通过只按原范围有效。后续小修正在setUp先对证据根及其祖先做 `confined` 校验，再 `mkdir(parents=True, exist_ok=True)`，不复制忽略证据或写父私有现场；冷目录初始化和已有根联接的零外部写入拒绝另经实际setUp前三句验证。另补正式入口的两条创建边界：语义预检返回后、Start-Process和owner Process.Start之前再核当前时段，假时钟证明预检前合法但结束已到deadline-420时两条路径均零创建，合法结束时正向保持。原owner/driver二道门和60分钟上限不取消。后续隔离21/21、PowerShell/时段4/4（新增上述1项）复测通过，无跳过；父跨树原失败及一次本地检查脚本目录层级错误的ModuleNotFoundError原回执均保留，未因修正改旧现场或生成新GO。

协调者审查`b14245c`及后续`955d476`后，在`main-2`独立集成分支处理专题／待办冲突并保留共享HANDOFF，于实际缺少测试根的工作树完成**28/28**复测：隔离21、真实PowerShell文件／时段4、预算3，均无跳过；隔离组启用ResourceWarning错误检查。父测试后再独立核旧包400项、原安装99项及三历史conf，均与事故保全一致，文档及差异检查通过。父本机证据为`.local-analysis/config-path-incident-20261112/integration-review.json`及同目录`integration-*.log`，不为复测复制旧现场。此次交付只改变诊断工具、测试和文档，产品`src/`与根CMake／预设不变；原七小时控制窗口已结束，EX-003整体与新profile实机兼容等剩余条件继续受阻。

<a id="fourth-request-refusal"></a>

## 新一小时第四槽：协议拒绝与正常退出

用户新授权UTC2026-11-12 **16:49:39.443894–17:49:39.443894**仅EX-003，17:39:39起最后10分钟只收尾；沿原Pi/同Task和当前Dispatch，FF同步共享dev `483d6e2`，未新建会话。此次授权覆盖前述历史离线暂停；归档精简仍暂停，旧三个槽与GO不复用。新建 `.local-analysis/ex-003-live/candidate-fourth/slot`，通过本树冻结校验器validate_plan_file，实际read conf的logfile/captures/C-D挂载四路径都归本新slot。父独立审核后签新GO：16:59:56.003749生效，硬截止17:46:39.443894，固有7分钟业务门恰为17:39:39.443894，不延长总窗口。

| 冻结项 | SHA-256 |
| --- | --- |
| plan | 4e48be5fd4a2d2678fd81f1647730466ddc78c00836e8905be6a7385584efbe7 |
| driver | c3fa2e1c16bb4ce489d77d5bf5b8466a3e528233fa384b1b59236f662be93f8f |
| gate | 6ac935bb76a13e6d88bc4b66a1e4903a1cbd542c4a0e508009838120d34e3371 |

17:01:53真实PowerShell-File PreflightOnly通过后，唯一Detach入口启动。新目标绑定PID36096、FILETIME134389766755393000、HWND3149268，兼容33样本无失败且join；Launch后新host真实read仍是Orca前景。**操作者误用未定义tool=FocusOwned投递聚焦，冻结gate只允许App，17:08:02.153865在创建桌面请求前以“两轮捕获禁止其它业务”拒绝。** 这是请求协议错误，不是新profile/IME/客体响应失败；没有App/业务聚焦、Capture或Enter/Down/Up/Esc。错误请求原文和rejected、stopped-error及原JSONL保留，未修改冻结驱动、绕门或重发恢复业务。

严格120.001374秒静默，17:10:02.155239结束；期间零新增桌面请求。随后仅CleanupFocus精确原窗口一次并取收尾当前图，模型实际read为662×566 AUTOTRAX启动页；依据新native rect [89,100,751,666]及图内正常X定位全局[705,122]，17:10:53只发正常宿主X一次。原WaitExit和另外三层原创建者持柄记录如下，不从下层外推外层隐藏PowerShell宿主退出。

| 原创建链 | PID | 原wait_return | UTC退出记录 |
| --- | --- | --- | --- |
| 目标 | 36096 | 0 | 17:11:03.818510 |
| 控制服务 | 14104 | 0 | 17:11:04.090199 |
| driver | 46760 | 0 | 17:11:04.097968 |
| owner | 41924 | 0 | 17:11:04.1097841 |

只读收尾审计 `fourth-live-audit.json`核3张host原图与原Pi JSONL image.data解码SHA回执一致，无guest/导航used标记/新Capture/NEWFT.PCB；四层退出身份均与原创建记录一致，采样线程join通过。原安装99、事故后旧包400、既有EX001/004/005与离线EX003证据、新runtime99/inputs1完整集合与大小/SHA均不变。候选预检见`fourth-candidate-review.json`，父独立审核见协调树`config-path-incident-20261112/fourth-parent-review.json`。本次只证明新profile入口可启动到启动页、兼容采样和正常收尾，不证明全部环境写隔离/客体截图/导航或Information到达；[EX-003](exploration-backlog.md#ex-003)总体仍受阻，不由此次请求错误自动生成第五候选或新GO。

离线协议复核直接载入第四槽冻结gate，并以临时合成PNG/计划/state/review调用原submit.py，App、6个命名Shortcut目的、Capture开菜单和选择客体截图共9组均validate通过、实际submit返回0且排他投递一致；旧FocusOwned及14轮已满后的Capture继续拒绝。正确App结构为 `{"name":"focus-owned","tool":"App","arguments":{"mode":"switch","name":"DOSBox-X 2026.10.01: PT - 10000 cycles/ms"}}`，实际新现场仍须从当下精确绑定原窗口取标题；外层packet为本Task/session/dispatch和当下previous/nonce。错误来自操作者跳过submit的本地协议预验，直接把意图当tool写inbox；后续流程须先完成当前host/guest真实read和审核，由原submit先validate后排他写唯一请求，不直接投递业务、不预排、不改gate放行。此合成成功不证明新现场动作消费。

最坏初始客体图1＋startup Enter1＋main Enter1＋Down7＋Up1＋Information确认1＋Esc1合计13轮，在14轮预算内；每轮仍需Capture打开与选择各自的新host后验及guest实际read。原第一段35图约30分钟，完整最坏约70–80次图read/步骤，保守35–45分钟，17:15距17:39:39业务截止不足25分钟，因此父接受保守预算并决定本小时不再开第五现场，不生成新候选/GO/进程，不延长总授权，不以省略读图/多键预排赶时；当前停在未结Task的离线可审点，由父统一HANDOFF及集成，EX003/005/007均不删项。离线检查首次9组成功后，尾部合成步骤重名导致publish FileExistsError，未完成预算断言和report；修正临时编号后17:15:19完整复跑通过，原失败和文档追加脚本一次SyntaxError回执均保留。最终只读协议报告为同Task `fourth-protocol-review.json`，不改第四槽冻结与失败原件。
