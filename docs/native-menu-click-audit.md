# 第二槽菜单点击离线审计

已完成第二槽 `step-003-focus-owned-post` 与 `step-004-menu-one-*` 的原图、裁剪、公开请求响应、原生窗口状态及父 Pi 会话时序核对。**没有发现 Click 自动应用截图比例的路径，也没有找到足以确定前景为何转为终端的证据。** 本次不启动新现场，原软件连续客体截图、文件状态、单线保存重开及默认字段继续未完成。

从 `dev=66955ba` 建立 `verify/native-menu-click-audit`。当前 Pi 会话 `01a1a2ac-682d-754e-b2da-87798ba11eb3` 的环境、model_change、thinking_level_change 和 assistant 记录一致为 `deng/gpt-6.1-sol high`；本会话实际读取两张旧原图，SHA 与 image 回执均匹配。没有派发子任务、恢复旧槽或操作原安装。

## 坐标与图像

第二槽原件位于 `review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate/slot-retry-01/`，始终只读。

- 聚焦后图为未缩小的 662×566 PNG，裁剪区域 `(89,100,751,666)`，Capture 标签约在图内 `(455,60)`。请求 `(545,160)` 对应图内 `(456,60)`，位于标签文字附近；一像素差不构成整倍缩放证据。
- 输入前原生 DOSBox 矩形仍为 `(89,100,751,666)`，PID 43792、HWND 6751790，且在原生枚举前后均为稳定前景。该点在窗口内；驱动检查的是窗口矩形，没有单独验证菜单标签或最终鼠标接收者。
- 点击后因目标已非前景，驱动改取全屏。3840×2160 图缩到 1920×1080，公开元数据明确要求调用方对**这张全屏图的图内点**乘二；这条说明不应反用于上一张未缩小裁剪图。
- 全屏 Snapshot 的光标元数据为 `(545,160)`；安装实现直接读取 `GetCursorPos()`，没有按图像缩放该字段。它与公开请求相符，但不是鼠标按下瞬间的轨迹或接收窗口证明。

读图确认：前图可见 AUTOTRAX 1.57 启动页和宿主 Capture 标签；后图 Windows PowerShell 遮挡目标，未见 Capture 菜单。菜单是否曾短暂出现，现有两张图无法判定。

## 时间线

以下为 2026-11-03 UTC，转换北京时间加八小时。文件中的 `at` 是驱动本机记录请求发送／响应保存的时间，不能等同于 Windows 事件实际送达时间。

| 时间 | 原始证据 | 能证明的事实 |
| --- | --- | --- |
| 15:32:31.445125–15:32:46.200572 | App 请求／响应 | 精确标题聚焦调用约 14.76 秒后返回 |
| 15:32:46.206487–15:32:46.294005 | focus-post native-before/after、Snapshot | DOSBox 前景稳定，裁剪图实际取得；公开 Snapshot 文本却为 `No active window found`，不能用此文字推翻原生状态和图像 |
| 15:33:02.768Z | 父原 JSONL codemode | 读取当前状态与真实聚焦后图 |
| 15:33:23.044Z | 父原 JSONL codemode | 只写读图审核与唯一菜单请求，没有调用 shell |
| 15:33:23.183836 | Click 前 ControlStatus 响应 | `ready`，generation 7 |
| 15:33:23.186360 | menu-one-native-before | DOSBox 为稳定前景，矩形与身份未变 |
| 15:33:23.187509–15:33:23.754738 | Click 请求／响应 | `(545,160)` 一次请求，耗时 0.567229 秒，返回单击成功文字 |
| 15:33:23.760351 | menu-one-post-native-before | 前景已是终端 HWND 9636356，矩形 `(255,266,2007,1202)` |
| 15:33:23.762233–15:33:23.940452 | 后图 Snapshot 请求／响应 | 全屏图、光标元数据 `(545,160)`；没有 Capture 菜单后验 |
| 15:33:23.946841 | menu-one-post-native-after | 前景是同一终端进程的另一 HWND 44766346，矩形 `(293,304,2045,1240)` |

输入前枚举与首次终端枚举相隔 **0.573991 秒**。前景变化发生在这两个采样之间；Click 响应、后图控制门及枚举也占用其中部分时间，不能进一步断言变化发生在按下、释放或等待的哪一刻。后图前后终端 HWND 不同，需保留这一事实，不能将整个后图区间称为同一精确窗口稳定。

父原 JSONL 在聚焦请求到菜单后图之间只有 codemode 内的 read/write/image；第二槽没有父 shell 插入这一点得到原记录支持。没有观察到 shell 调用不等于证明所有外部前景变化来源都已排除。

## 安装函数原 AST 离线验证

复用父现有忽略证据目录，新增 `main-2/.local-analysis/native-capture-checkpoint/audit_menu_click.py` 和 `menu-click-audit.json`，不复制运行副本或原图。脚本只解析安装源码，提取原函数 AST，去掉装饰器后用假 controller、虚拟桌面和鼠标 API 执行；不 import 桌面包、不调用 COM/UIA、Win32 输入或第三方服务。

实跑路径为 `tools/input.py:click_tool` → `desktop/service.py:click` → `uia/core.py:Click` → `AbsoluteMouseEvent`。三项均通过：

1. 原请求直接传递到假 `SetCursorPos(545,160)`；鼠标按下／释放事件按 3840×2160 虚拟桌面归一化为 `(9304,4857)`，没有乘二、再加裁剪原点或使用最近 Snapshot 的隐含状态。
2. 假 `SetCursorPos` 返回 false 时，原函数仍发送后续事件并返回相同成功文字。实际 Win32 `mouse_event` 没有接收窗口确认；**这只复现回执不等于送达后验，不证明旧现场 API 返回 false**。
3. 越界 `(3840,160)` 在假鼠标 API 前被拒绝；未执行真实输入。

安装 `desktop/service.py` 与 `uia/core.py` 的 SHA 分别仍为 `c116adc0d221c993a89596a14f0ac66bf924e250672cb2691a8914b0e788231e`、`3638d7ba96d7b918783e6e95b95af9978ae7a0df5b200e0966e47e56921f170e`，与[前轮输入语义审计](native-capture-checkpoint.md)一致。完整五项安装源码、冻结 driver 和 33 项第二槽 JSON／PNG，共 39 项大小与 SHA 存在本机结果中，收集前后未变。两个旧原图均有本会话实际 image 回执。

该实验绕开装饰器、线程调度、真实控制门和 Windows，不验证实际工作线程 DPI、真实 API 返回值或目标菜单响应。`core.py` 存在进程 DPI 设置代码也不证明旧服务中该调用成功；旧现场没有对应返回值和线程上下文记录。

## 可区分的解释与下一步

| 解释 | 当前证据判断 | 仍需的最小观测 |
| --- | --- | --- |
| 把未缩小裁剪图当成半尺寸图，Click 自动乘二 | 安装原函数 AST 不支持自动乘二；旧请求也未乘二 | 不应为了匹配假设盲改坐标为两倍或一半 |
| 父在聚焦后运行 shell 抢前景 | 第二槽原 JSONL 不支持此解释 | 沿用单一操作者和文件读写投递 |
| 调用期间前景／鼠标命中对象变化 | 与现象相容，尚不能确定原因 | 对一次公开 Click 前后做短时间只读原生观测，记录单调时间、前景 HWND/PID、逻辑及物理光标、目标与终端矩形 |
| API／线程坐标上下文差异、失败或目标菜单短暂开启后消失 | 原日志缺少区分信息 | 记录可从外部读取的进程 DPI 与窗口 DPI、光标和窗口命中预测；接收窗口预测不能冒称实际送达确认，不能从外部进程查询值冒称知道服务输入线程上下文 |

<a id="explore-ex-001"></a>

当前已完成交接顺序的第一项离线审计，**根因仍阻塞第二项的可靠连续捕获**。后续[最小只读候选已完成离线核验](#readonly-observer-offline)，但没有实机兼容或动作后验。若继续诊断现场，目的应限定为一次公开菜单动作的时序和前景后验，使用当下原图和新冻结隔离槽；不修改第三方安装／控制门，不恢复旧 GO，不重复盲点。一次动作不能解释或菜单后验失败时停止业务；保留既有截止、拒绝后静默及原 owner 正常退出要求。取证成功后再扩展到两轮真实客体 PNG、文件状态和单线保存重开。

[探索 EX-001](exploration-backlog.md#ex-001)。

## EX-001 离线只读观测候选（2026-11-11）

<a id="readonly-observer-offline"></a>

本轮只完成离线阶段，**EX-001 未闭环，不能据假 API 删除事项或宣布根因已定位**。分支 `research/ex001-readonly-observer`，Task `task_3903c40083a3`／Dispatch `ctx_cdfee6b64af8`，Pi `01a1cb26-1411-7553-be7e-98cfa74d0e98`。环境、原会话 `model_change`／`thinking_level_change` 及成功工具回执均核对为 `deng/gpt-6.1-sol high`。领取状态由父同步到共享 dev 后才开始研究。

### 本轮独立核对及材料复用

完整阅读技术交接、本文、[两槽结果](native-capture-checkpoint.md)和[原软件主题](topics/legacy.md#explore-ex-001)。只读分析旧 `audit_menu_click.py`，没有运行其会写回旧结果的顶层代码。独立提取旧槽五份 JSON 和安装 `uia/core.py`，文件大小／SHA-256 在收集前后相同：重新得到 RPC 0.567229 秒、前景采样间隔 0.573991 秒，以及 `6751790 → 9636356 → 44766346` 三个不同精确 HWND。最后两个同属终端的窗口不能合并为一个稳定 HWND。

安装 AST 的 `Click` 顺序是 `SetCursorPos` → `AbsoluteMouseEvent(LeftDown)` → `sleep(0.05)` → `AbsoluteMouseEvent(LeftUp)` → `sleep(waitTime)`；默认 `OPERATION_WAIT_TIME=0.5`。绝对鼠标函数包含 MOVE、ABSOLUTE、VIRTUALDESK。因此旧 0.567229 秒 RPC **大部分与调用内等待相容，但不是“按下维持了 0.567229 秒”**，也不能把前景变化归在前 50 ms 或末尾 500 ms。函数忽略 `SetCursorPos` 的布尔结果，`mouse_event` 没有接收者回执；外部观测器不能事后恢复旧调用返回值。

原有 `tools/inspect_legacy_desktop.py` 已提供只读枚举，但无调用内连续光标／命中采样；直接反复全桌面枚举会增加扰动。`tools/control_geometry.py` 的物理矩形依赖临时改变观察线程 DPI 并恢复，已有假 API 回归；本候选不调用该函数，不改变任何 DPI 上下文，避免把自有线程设置成功误报为服务输入线程状态。没有新增依赖、下载、构建树或整套现场副本。

### 最小候选与证据字段

新增独立诊断工具 [observe_legacy_click.py](../tools/observe_legacy_click.py) 和 [假 API 测试](../tests/test_observe_legacy_click.py)，不改产品行为或第三方安装。模块导入无 DLL／桌面包加载，默认 CLI 拒绝查询；真实模式要求显式 `--observe-readonly`，此开关不是现场授权。本轮没有启用真实模式。

候选仅允许 1–3 个已核验 HWND、一个请求点、最多 3 秒、最短 5 ms 目标间隔；默认 2 秒／10 ms。仅新建 JSONL，已有输出在加载原生接口前拒绝覆盖。循环串行采样，不追赶漏采；记录每个 API 的单调开始／结束时间和序号。头部 UTC 与单调时钟的夹取区间只用于关联 RPC 本机时间，不能提升为输入事件送达时刻。

| 字段／只读 API | 能支持的观察 | 必须保留的限制 |
| --- | --- | --- |
| `GetForegroundWindow`，样本前后各一次 | 可见到的前景 HWND 变化及区间 | 前后相同不排除中间切换再返回；不是原子快照 |
| `GetCursorPos`／`GetPhysicalCursorPos` | 观察线程逻辑坐标、物理坐标，失败明确为空并留错误码 | 两次调用不同时；差值不能单独归因为 DPI 或外部输入 |
| `WindowFromPoint`／`WindowFromPhysicalPoint` | 观察者逻辑光标、物理光标、假设为物理坐标的请求点的窗口命中预测 | 不代表按下／释放实际接收者；捕获、线程输入队列、菜单和窗口销毁竞争均可能改变实际投递 |
| `GetWindowThreadProcessId`／`GetWindowRect` | 目标、前景及预测命中 HWND 的当次 TID/PID 和观察线程上下文矩形 | 无进程创建时间，不证明进程生命身份；矩形不冠以物理像素；窗口可能在查询间失效／复用 |
| `GetThreadDpiAwarenessContext`／`GetWindowDpiAwarenessContext`／`GetAwarenessFromDpiAwarenessContext`／`GetDpiForWindow` | 自有采样线程与当次窗口的 DPI 语义 | 不是远程服务输入线程的上下文；窗口 DPI 值不等于鼠标坐标换算比例，也不证明服务设置 DPI 成功 |
| 前景 TID 的 `GetGUIThreadInfo` | 当次 GUI flags、active/focus/capture/menu-owner HWND | 只观察前景线程，不覆盖所有输入队列；空／失败不等于“从未出现菜单”；不能跨进程获取真实 API 返回值 |

空 HWND 和失败返回不伪装成功。只在定义了错误码语义的失败 API 后读取 `GetLastError`，对空前景／空命中等不引用陈旧错误码。HWND 和 DPI context 使用指针宽度，POINT 按值传递，`GUITHREADINFO.cbSize` 明确设置。不开钩子、不附加线程输入、不发窗口消息、不读取窗口标题文本、不枚举全部进程／桌面、不设置焦点／光标／DPI、不截图或输入。动态 API 调用也受只读白名单约束。

### 离线验证及原始失败

运行 `python -m unittest discover -s tests -p test_observe_legacy_click.py -v`，10/10 通过：大 HWND／负坐标／不同逻辑与物理点、前景切换和菜单信息、光标／矩形／GUI 失败、空命中、DPI／身份未知、原生 ABI 签名与 Windows 结构大小、非白名单 API 先拒绝、慢采样不追赶、无效预算／句柄／坐标先拒绝、默认不读桌面及输出不覆盖、只读白名单。测试使用假 user32 和假时钟；其中 CLI 拒绝路径只启动自有 Python 进程，不加载 Win32。另跑现有 `test_control_geometry.py` 6/6，未执行真实几何查询。

本轮收集脚本最初把父目录层级多退一级，读取旧槽路径得到 `FileNotFoundError`；随后只修正本树脚本路径再收集成功，没有创建缺失源文件、重跑旧脚本或写入旧目录。首轮领取文档检查因历史忽略证据未分发而失败，原结果保留；父合入可移植检查修正后，本分支同步并复跑通过。以上不是 GUI 失败，也不掩盖本轮没有实机验证。

本机证据集中在本树 `.local-analysis/ex-001/`：`identity.json`、`claim-doc-check.json`、`collect_offline.py`、`offline-source-audit.json`、`fake-api-tests.log` 及最终验证记录。旧来源只读引用相邻 `main-2` 和 `review-track-core-boundaries`，不复制 PNG、安装或完整槽；本轮没有重新读取图片并冒称新读图／新捕获。

### 下一阶段最小假设、收敛条件与禁止推论

<a id="readonly-observer-next"></a>

待现场检验的最小假设是：**一次公开 Click 的前景切换，可能伴随物理光标／命中预测改变，也可能发生在坐标稳定时的等待阶段**。两者都与旧日志相容，当前无证据择一。不另立重复事项；这些未知仍属于 [EX-001](exploration-backlog.md#ex-001) 的完成条件。

父另行组织新隔离槽和唯一操作者；先在其已核验当下目标／终端 HWND 与请求点下，确认只读查询兼容性和样本耗时，再决定是否足以覆盖一次动作。观测器须在聚焦前预启动，由同一常驻驱动／文件信号触发短采样；不能为了点击期间采样再运行 shell 抢前景。与公开请求使用同机单调锚点关联，保留 gate 返回、发送、响应及前后截图的独立时间，不能拿不同进程的 UTC 差推事件因果。此交付没有修改冻结驱动，也没有提供可直接执行的旧槽命令或 GO。

首轮只做一次公开菜单打开动作及其当前原图后验，不预排菜单项，不重复 Click，不盲改坐标。如果出现样本缺口、查询失败、目标身份变化或看不到菜单，停止业务并按既有静默、截止和原 owner 正常退出规则收尾；不能以额外观测绕过控制门或拒绝后的零桌面请求期。采样循环截止不能中断正在阻塞的 Win32 查询，故 3 秒只是启动新采样的上界，不是硬退出保证；下轮必须测量实际查询耗时和关闭路径。

即使得到一致命中／DPI／GUI flags，**仍不能证明 Windows 实际鼠标接收者、服务的 SetCursorPos 返回值、服务输入线程 DPI 或外部前景来源进程**。若两次采样间菜单开启又消失，轮询可能完全漏过；没有菜单 flags 不构成否定。只有真实动作时序、采样完整性及指定模型实际读到的菜单后验共同成立，才能重新评估本项完成；可靠菜单之后才进入 [连续客体捕获 EX-004](exploration-backlog.md#ex-004)。

本轮只新增诊断工具／假 API 测试并更新文档，产品 `src/`、CMake 与既有测试不改；未重跑无变化的完整构建／CTest。最终文档检查 162 份 Markdown／1171 个本地链接、43 个开放事项／105 个来源细节、145 份索引报告，零错误；`git diff --check` 通过。收尾时证据目录仅约 43 KiB，无缓存目录、下载、归档或可删重复副本；删除字节／归档占用／净减少均为 0。测试子进程均由 `subprocess.run` 等待返回，没有启动常驻进程、GUI、DOSBox 或服务，也未为收尾查询活动桌面或全机进程。正式新增门、默认 Created 拒绝和 NETDEF 新增拒绝均沿用基线。没有新 GUI 通过结论、兼容性或默认字段结论。
