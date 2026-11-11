# 原软件连续客体捕获：输入语义、两槽历史与两轮新图

后续[同一新目标中的两轮真实客体捕获](#continuous-capture-conclusion)已完成：每轮各新增一张非空 640×480 PNG、逐张真实 read，正常宿主 X 及四组原创建链均 wait0。两张图都是 AUTOTRAX 1.57 启动页；不据此宣称板名／计数、PCB 编辑或保存重开已完成。下文两槽失败是此前阶段的原事实，仍保留。

本轮从 `dev=672351eb89734c0b508fadfefc577af09928a550` 继续，父分支 `verify/native-capture-checkpoint`，Run `run_c9bab9d00b23`。原软件操作者与离线审查者沿用各自原 Pi 会话，实际模型为 `deng/gpt-6.1-sol high`，独立工作树和证据目录。父负责独立复现、交叉验收与集成；普通产品新增入口仍关闭。

## 已确认：公开 Shortcut 的 F11+p 不保持 F11

本机安装的 `windows_mcp/desktop/service.py` 中，`shortcut` 将用 `+` 分割的多字符键包成花括号，单字符保持原文，再调用 `uia.SendKeys`。本机 `uia/core.py` 的 `SendKeys` 仅把 Win、Shift、Ctrl、Alt 等列为保持键，未把 F11 列为保持键。

父没有导入或执行桌面模块。离线实验用 Python AST 提取实际安装的 `shortcut`、`SendKeys` 与所需原枚举／映射，以假 `keybd_event`、`SendUnicodeChar` 和睡眠记录调用。四例均完成，事件顺序如下：

| 公开请求 | 实际 SendKeys 文本 | 假 API 记录顺序 |
| --- | --- | --- |
| `f11+p` | `{f11}p` | F11 按下、F11 释放、Unicode 字符 p |
| `shift+i` | `{shift}i` | Shift 按下、I 按下、I 释放、Shift 释放 |
| `alt+f4` | `{alt}{f4}` | Alt 按下、F4 按下、F4 释放、Alt 释放 |
| `enter` | `{enter}` | Enter 按下、Enter 释放 |

这证明本机安装函数的解析及调用顺序，未证明目标应用响应。它足以否定“传入 `f11+p` 字符串便已发送保持 F11 的组合键”这一假设；并不证明原软件截图热键本身无效。

因此，[上轮短观察方案](native-short-observation.md)建议的 `Shortcut f11+p` 首序列不应直接执行。已有 Capture 菜单上显示 F11+P 的旧图仍有效，但菜单标注与公开工具能否送出对应事件是两个事实。本轮计划改用已取得过成功客体 PNG 的公开菜单路径：按当下原图打开 Capture，再选择 Take screenshot；连续两次各确认新 PNG 并实际读取。没有改已安装第三方包或切换输入接口。

输入实验脚本为父忽略目录 `main-2/.local-analysis/native-capture-checkpoint/check_shortcut_semantics.py`，结果 `parent-shortcut-semantics.json`。首次实验断言将生成文本预期写成大写 `{F11}`，而实际是小写 `{f11}`；改为忽略键名大小写后通过，没有改原函数或安装。三份受审安装文件的 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `desktop/service.py` | `c116adc0d221c993a89596a14f0ac66bf924e250672cb2691a8914b0e788231e` |
| `uia/core.py` | `3638d7ba96d7b918783e6e95b95af9978ae7a0df5b200e0966e47e56921f170e` |
| `uia/enums.py` | `9da1086764fffe967186cdcc6f8afa7f164971e16d72e0c9aaa8eb3ac90607c1` |

## 已复现：旧驱动的读图与收尾缺口

独立审查者对旧 retry-01 的 `desktop_session.py`、`submit.py` 进行 12 项离线复现。父阅读脚本后，将单脚本复制到自己全新目录独立运行，12 项均符合预期，未修改子证据。测试只执行 submit 副本和 driver 原 AST 中的纯请求、授权及 finally 片段；假目标记录 wait 参数，没有真实窗口、输入、COM/UIA/MCP 或原软件。

具体事实：

- F11+p 后只有宿主 `last_capture` 读图约束，没有新客体 PNG 的读取要求。
- 审核与清单只比摘要字符串，实际图片字节改变后仍可通过；错误 Task／Dispatch／步骤和旧时间字段也未检查。
- submit 可以接受其他 `previous` 的旧审核，driver 依当前步骤再拒绝时，请求已经改名消费。
- 缺少业务读图审核会同时挡住 Close、WaitExit、Stop，影响正常收尾。
- 6 分钟 GO 会被接受，但原最后 7 分钟规则使业务截止早于启动。
- 异常静默 120 秒后，旧 finally 先关闭 RPC，再调用无超时的原目标 `wait()`；这保留原 Popen，但不能保证模型失联时按时正常退出。

这些是实验辅助驱动的问题，不是产品源码缺陷，也不追溯修改旧现场结论。原有唯一动作名和禁止多请求预排的拒绝路径在复现中仍有效。

## 新槽待验边界

操作者仅在新 `.local-analysis/native-capture-checkpoint/` 修改复制驱动、submit 与审核函数；原槽和原安装只读。业务请求要求绑定当前 Task／Dispatch／会话／步骤 nonce，并重算宿主及客体图片摘要。捕获要求动作前后文件集合差、恰一张新 640×480 PNG、保留旧图摘要及真实读图审核。Capture 菜单打开与截图菜单项选择是两个明确宿主动作，不能因首张 guest 尚未存在而被业务约束互相锁住。

生命周期请求须在加载业务状态或审核前分类，但正常 Close 仍须走公开控制门、当前精确 Popen／窗口／前景核验；不以任意 `purpose=cleanup` 放宽输入，不引入强杀或绕门关闭。运行前还须核对冻结代码及完整输入／运行副本摘要，并在 gate 返回后、实际输入发送前再次核对截止。

本轮最终工具包已修订并冻结，36 项假 fixture、原 driver main 的八步假环境两轮菜单捕获和完整 preflight 均退出 0，外层计时分别 1.0740446／0.2155946／0.3404806 秒。父独立执行原函数 AST 的纯 preflight 并核对全部摘要后接手现场。第二槽离线准备另有 13 项检查、0.3222774 秒退出 0。详见[独立驱动报告](native-capture-driver-review.md)。这些都是工具逻辑和材料核验，不是 GUI 通过。

## 父现场验收：两槽未完成连续客体捕获

父实际 Pi 会话 `01a1a15a-5307-7312-a21c-9c61e64983f5`，环境及原 JSONL 为 `deng/gpt-6.1-sol high`。两槽均预告具体时段，单一操作者，未修改已冻结驱动；原安装没有挂载。现场结果均为 **failed**，没有新 guest PNG，没有文件名／计数或单线保存重开证据。

| 槽与冻结计划 | 实际动作与失败边界 | 正常退出 |
| --- | --- | --- |
| 首槽：23:17–23:37，23:30 起仅收尾；plan `d6bf6e57…` | 基线图后启动单一隔离目标；第一次后图前景是 Orca，公开 App 精确聚焦后取得可辨 AUTOTRAX 1.57 启动页。菜单 Click 前 driver 再核前景，发现 Windows PowerShell，23:22:38.935947 拒绝；**Click 未发**。完整 120 秒零新桌面请求后只正常收尾。 | 父核对 PID／创建时间／映像／HWND 后一次 WM_CLOSE，仅处理自建目标生命周期，不恢复业务；原 owner 23:25:43.951809 记录目标 wait0，服务 23:25:44.279924 wait0，原启动入口 23:25:44.288379 记录 driver wait0。 |
| 第二槽：23:31–23:51，23:44 起仅收尾；plan `86048dfa…` | 新副本与独立计划，驱动三模块不变。聚焦后仅 `read`／`write` 保存实际读图审核及投递单一请求，driver 仍完整 validate；不在期间启动 shell。菜单 Click 一次真实发送并返回成功，但 23:33:23 后图没有 Capture 菜单，前景为终端。**不以 purpose 或成功文字判菜单已打开**，不猜菜单项／不重发，停止业务。 | 父精确核对后一次正常 WM_CLOSE；原 owner 23:37:40.518503 目标 wait0，服务 23:38:13.709774 wait0，父持原 Popen 的启动器 23:38:13.761237 记录 driver wait0。 |

首槽曾将聚焦后插入父 shell 调用视为可能影响前景的因素；第二槽移除这类调用仍出现终端，因此该单因解释不成立。本轮只确认前后原图、实际请求和精确前景事实，尚未解释为何菜单动作没有产生预期菜单。第二槽公开 Snapshot 元数据记录点击后光标为 `(545,160)`、全屏缩放系数为 2.0；当前窗口裁剪图采用物理原点 `(89,100)`，Click 依据该未缩小的窗口图计算。缺少进一步证据时，不把现象笼统归因为用户操作、DPI 或某个 API。

首次父辅助 submit 调用遇到子进程默认编码导致 stdout 解码错误，但原 submit 返回 0，启动请求已接受，未重发。随后一次内联 JSON 参数解析在投递前失败，改为文件参数后仅发送一次 App。第二槽有一次本地读取尚未生成的 focus 后图路径得到 ENOENT，随后读取真实新步骤完成，未据缺图重发输入。原错误均保留，不改写成 GUI 故障。

父两槽均未强杀、未恢复旧服务或按历史 PID 关闭。7 张唯一宿主 PNG 全部由父实际读取，父脚本把每张原字节 SHA-256 与当前会话 image 回执逐项匹配，7/7 相同；没有新客体图。两槽原安装 99 项、运行副本各 99 项及输入各 1 项完整集合／大小／摘要均保持不变。目标／服务／driver 的创建和退出 PID、原 Popen 身份、HANDLE、FILETIME 一一相同且 wait0，全部在各自预告截止前结束。

## 任务结算与后续

原操作者 Task `task_f8c94a979620`／Dispatch `ctx_ae9b1854c946` 交付首版槽及 28 项首版离线结果，按真实连续捕获未执行 failed 结算。其后编辑过的菜单版三文件没有重新冻结，旧 plan 与当前字节不一致，不能运行或将首版 28 项结果套在后版；该槽保留只读。prepare／check 曾通过 runpy 在独立 Python 进程导入 driver 顶层并设置该进程 DPI，未调用 inspect／main／桌面 RPC，不能声称完全没有 DPI 副作用。

审查与最终工具包 Task `task_46be31be3ba2`／`ctx_c38cc667f1c9` succeeded，报告提交 `fa938a95de8cb19a58c0dee49649a9b91d2f6d28`；第二槽准备 Task `task_1e5b34acc232`／`ctx_2d207d616347` succeeded，补记提交 `a97f6c123fc4609b1ea99f78f7da87262af04667`。两者 success 只指离线工具包与准备，不包含父 GUI；父处理三个唯一 worker_done 后 release 并 ack，external_terminal／retained／processAction none 不等于 Pi OS 已退出。

<a id="explore-ex-004"></a>

后续离线核对已完成，见[第二槽菜单点击审计](native-menu-click-audit.md)：原图／请求／原生窗口／父会话时序已对齐，安装原 AST 假鼠标验证没有自动截图比例换算；约 0.574 秒采样间隔内的前景变化仍缺少调用内部观测，根因未定。后续[实机短时观测及一次菜单后验](native-menu-click-audit.md#live-menu-conclusion)已取得：新槽189样本无失败、前景稳定、光标到达请求点、指定模型真实读到Capture菜单，原目标及服务链最后正常wait0；旧前景触发者仍不可恢复，不把新成功覆盖两槽失败。下一步按该结论的消费者边界准备两轮新客体捕获，不复用已退出槽或旧GO。旧 `Shortcut f11+p` 假设已排除，菜单路径仍需要真实连续验证。旧现场两槽失败及本文原有证据范围保持。原软件单线保存重开、FT 默认字段及兼容性继续未通过；普通新增门和默认 writer 的 Created 拒绝、NETDEF 新增拒绝保持。产品源码没有改变，不重跑无变化的完整 Debug／Release 矩阵。

以上是旧两槽未闭环时的记录。后续[两轮独立新 PNG、文件集合差及真实读图结论](#continuous-capture-conclusion)已补齐原事项；旧失败、快捷键解析事实和适用限制保持。

父证据在 `main-2/.local-analysis/native-capture-checkpoint/`：快捷键原 AST 假 API 结果、旧缺口父复现、最终包 preflight、两槽原身份退出／摘要审计、7 图字节回执匹配和最终状态。子冻结包及两槽原件在相邻 `review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate/`。这些忽略材料、截图与原软件副本均不提交；报告按独立分支 no-ff 集成到 dev，最终 SHA 与任务／收件箱核对见父 `final-state.json`。

## 同一新目标中的两轮真实客体捕获

<a id="continuous-capture-conclusion"></a>

曾对应 EX-004 的完成条件已经满足：同一个全新隔离目标内，连续两轮均按当下图打开 Capture、实际读取菜单、选择已确认的 `Take screenshot`，每轮取得完整集合差证明的唯一新增非空 **640×480** PNG，并由指定模型逐张真实 `read`。**两张内容相同是当前启动页未改变的事实，不影响两个独立新路径／两次动作成立；它不能证明打开过编辑器、当前工作文件名／计数或默认 FT 编码。** 本次没有 `Enter`、Information／Status、PCB 新增／另存或重开动作。

### 当前身份、冻结与动作顺序

Task `task_57c256b62a70`／Dispatch `ctx_9bb156265144`，独立分支 `research/ex004-continuous-capture`，沿用 Pi `01a1cb98-e57e-75d0-9b06-c40a941eaaf0`。环境、原 UTF-8 JSONL 的 model／thinking 事件、所有 assistant 和成功工具回执持续为 **`deng/gpt-6.1-sol / high`**，没有恢复已结算 Dispatch 或切模型。领取提交先由父推共享 dev 后才准备；父审阅当前工具、真实 AST 假结果、完整冻结项并首次写新 GO。

新槽为本工作树 `.local-analysis/ex-004/candidate/slot/`，plan SHA-256 `8e6f88674ef65c512b154127219d4b0ab18ea257d988da9624d9051486b95a96`；driver `e9e639e791dbc3b11283de82a83c4bf461b19b7eeb89eccd96b26e5330c6aa81`，gate `a1c70a9a71c00aef7c60ccdc6f26cff26ff72ba707d70badd0aeb2081ad6e94a`。20 项冻结项、runtime 99 项、inputs 1 项均预检；只复制约 1.98 MB 必要运行文件，不用硬链接或新下载。UTC **18:48–19:13**，**19:06 起仅收尾**；本 Pi 是唯一操作者，父不发桌面请求。更大的用户控制窗口不改写这份 GO。旧双槽及前次菜单观测／失败证据只读。

新原目标 PID `10772`、FILETIME `134388965400999898`、HWND `2822238`，均由本 driver 原 Popen/HANDLE 绑定；这些是历史证据，不是后续可用 PID。启动后的真实兼容采样 **33 样本**，最大单样本 **4.9051 ms**、最大启动间隔 **15.2851 ms**，无失败；兼容线程真实 join 后再建立聚焦前常驻线程。一次公开精确标题 App 后，每个业务步骤只通过 read/write 逐步审核与投递，不插入 shell。

当前图为 1920×1080 全屏缩放图时，依据当下 3840×2160 虚拟桌面及 region=null 将图点乘二；未把同一规则套到后来的 662×566 裁剪图。两轮 Open 分别由各自当下图定位 Capture，截图项也分别实际 read 菜单后定位。四次默认 Click 坐标恰好重合为 Open `(548,160)`、截图项 `(620,194)`，属于各轮新图确认结果，不能作为未来固定坐标；没有使用已否定的公开 `Shortcut f11+p`。

| 轮次 | 公开选择截图项的请求／响应 UTC | 捕获前后完整文件集合 | 新客体原图 |
| --- | --- | --- | --- |
| 第一轮 | 18:52:13.825821 → 18:52:14.391995；单调 RPC 0.5655154 秒 | 18:52:13.764494 空集 → 18:52:15.774659 恰一文件 | `captures/pt_000.png`，6155 字节，640×480 |
| 第二轮 | 18:55:15.606982 → 18:55:16.172957；单调 RPC 0.5653332 秒 | 18:55:15.545947 仅第一张 → 18:55:17.556426 恰两文件，第一张大小／SHA 不变 | `captures/pt_001.png`，6155 字节，640×480 |

两个新 PNG 的 SHA-256 均为 `e473d5d1817063b927ca7493c3920f78b6282ccf4ed70f87badaf9161ad665e6`。两次完整目录快照分别保存 UTC、同机 `perf_counter_ns`、所有文件的路径／大小／SHA；单调锚点满足 before < 发送 < 响应 < after。两轮各只有一张新 PNG，旧文件没有改写或删除，没有额外非 PNG。真实 image 回执中有两次独立客体图读取，不能只用相同 SHA 的第一次回执冒充第二次 read。

四次业务 Click 各 **190 样本**、独立 JSONL／请求／响应／摘要；最大单样本分别 **1.3205／2.0554／2.7151／3.5639 ms**，最大启动间隔分别 **11.5128／12.4190／13.3457／13.9871 ms**，均无失败、取消或超限。发送前覆盖 **53.8087–54.6187 ms**，响应后覆盖 **1372.7684–1375.5989 ms**；本候选的完整 RPC 与至少 100 ms 后段要求均通过。时间只标公开请求与外部采样，不冒称 Windows 按下送达时刻或实际接收者。

### 宿主与客体的本次不同呈现

<a id="host-guest-difference"></a>

两轮宿主图都呈黑底白横线；对应新客体 PNG 却清楚显示灰底 Protel 图案、`AUTOTRAX - PCB Layout Program / Version 1.57`、版权和 `LOADED GRAPHICS DRIVER: VGA 640x480`。本指定模型实际读到两张菜单、两张新客体及相应宿主；共 **8 张唯一宿主 PNG + 2 张客体 PNG**，十张原字节 SHA 全部逐一匹配本 Pi 原 JSONL 的真实 image 工具回执。菜单可读只证明宿主菜单状态，客体启动页只证明当时客体呈现，二者不能替代板名／计数或编辑状态。

这给[EX-002](exploration-backlog.md#ex-002)已有宿主／客体呈现差异补充了新版本、冻结配置及并行证据，**没有确定 OpenGL／SDL／刷新哪一个是原因，也没有排除其他历史黑屏成因**。本轮未改变渲染后端或为黑线盲目重发输入。下一步只可据当前客体状态设计 [EX-005](exploration-backlog.md#ex-005) 的有效配置和工作文件核定，不能把命令行 `SYN1.PCB` 或宿主 `PT` 标题当成已经进入 SYN1 编辑器。

### 正常退出与原创建者证据

第二张客体与宿主真实 read 后，立即投生命周期 `CleanupSnapshot`，在新的 662×566 未缩小裁剪图内实际确认宿主 X；当下裁剪原点 `(89,100)`、X 图内约 `(616,22)`，所以一次正常默认 `Click(705,122)`。当前原目标稳定前景，无需额外 CleanupFocus；没有 Alt+F4、第二控制连接、外部 helper、WM_CLOSE、强杀或业务重发。随后由原 driver 对原目标显式 `WaitExit`，再 Stop 正常关闭服务，原 owner 链逐级真实等待。

| 原创建者实际等待对象 | PID | 原创建／退出身份匹配及真实返回 |
| --- | --- | --- |
| DOSBox-X 目标／driver 原 Popen | 10772 | wait0，UTC 18:58:21.588855 |
| 公开控制服务／driver 原 Popen | 46588 | wait0，18:58:48.302805 |
| driver／owner 原 Popen | 29120 | wait0，18:58:48.311145 |
| owner／上层原 .NET Process 与 HANDLE | 64876 | WaitForExit=0，18:58:48.3230726 |

四组分别精确比较 PID、创建 FILETIME、映像、原 HANDLE；有 Popen 的还比较原对象身份，均一致。FILETIME 用原 JSON 的 Python／PowerShell 整数，未经过 JavaScript Number。观测线程也真实 join。本轮没有现场拒绝或 `stopped-error`，没有需要执行静默的现场失败；120 秒零新增请求规则持续存在于冻结驱动中，不能把未触发写成执行过。全部已知原持柄链在业务截止之前完成，隐藏外层 PowerShell 自身无原 Popen 退出证明，仍不外推为其原退出码。

### 工具验证、原件保护和后续消费者

新增 [prepare_legacy_capture.py](../tools/prepare_legacy_capture.py) 复用已有准备器、审核门、常驻采样与 BOM owner；仅把单菜单限制扩展为严格两轮，并在同 driver 预先声明看图 CloseX。门核 nonce／session／Task／Dispatch、当前原 PNG 字节重算及已有 guest 实际审核；缺第一张客体审核不能第二轮，第二轮之后拒第三轮。captures 检查覆盖递归完整文件集合，既有文件变化、零／多文件、额外非 PNG 或错误尺寸都拒绝。正常 CloseX 仍必须当前图审核、精确身份／稳定前景／标题栏范围，显式原 WaitExit 后才允许 Stop。

离线验证为当前 gate／集合差 **21 项**、当前 driver AST **9 步**两轮假主循环、当前真实动作／Rpc 定义的 **13 项**停止阶段注错，均通过；原 BOM 启动器的真实 PowerShell 5.1 `-File` **1 项含 2 子例**亦通过，未因此创建现场进程。源码与 product src/CMake 无关，不重复无变化的产品构建或旧采样模块测试。初次 gate 测试只捕获 RuntimeError，预期缺 review 的 FileNotFoundError 使测试提前结束；补入预期 OSError 后通过，门没有因测试改为允许缺审核。一次进程级 SSH 参数引号错误后修正并成功 fetch；这两次失败均未启动现场，原回执保留。

收尾独立审计：原安装 **99 项**、旧含双槽包 **399 项**、前次 EX-001 全组证据 **584 项**、本次 runtime **99 项**及 inputs **1 项**的完整集合／大小／SHA 前后一致；`NEWFT.PCB` 未产生。captures 恰两张新 PNG。证据集中于本树 `.local-analysis/ex-004/` 的 `live-audit.json`、`readonly-before.json`、冻结包、逐步审核／trace、模型身份、原创建及退出记录，均不提交。已退出槽不作为下一阶段活现场，旧坐标、PID 或 GO 不复用。

这份有限通过允许后续消费[有效配置与工作状态 EX-005](exploration-backlog.md#ex-005)，再进入[单线保存重开 EX-007](exploration-backlog.md#ex-007)；后续须新 Task／分支／方案／GO，并保持逐图实际 read 和正常原 wait。本次没有核定默认 FT、NETDEF 新增、铜覆盖或正式新增门，产品保守规则不变。最终文档检查 **153 份 Markdown／1017 个本地链接／41 个开放事项／103 个来源细节／137 份索引报告，零错误**，`git diff --check` 通过。只清理可重建假 fixture 和本轮模块缓存 **175075 字节**，归档占用 **0**，净减少 **175075 字节**；收尾证据目录约 **19.07 MB**，输入／原图／冻结包／失败原件保留。
