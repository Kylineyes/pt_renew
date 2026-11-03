# 原软件连续捕获：输入语义与新槽核验

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

后续先离线对齐实际 Snapshot 坐标元数据、Click 发送和前后窗口身份／时序，找到能解释菜单未出现的具体依据，再安排新现场；不继续无差别重开槽。旧 `Shortcut f11+p` 假设已排除，菜单路径仍需要真实连续验证。原软件单线保存重开、FT 默认字段及兼容性继续未通过；普通新增门和默认 writer 的 Created 拒绝、NETDEF 新增拒绝保持。产品源码没有改变，不重跑无变化的完整 Debug／Release 矩阵。

父证据在 `main-2/.local-analysis/native-capture-checkpoint/`：快捷键原 AST 假 API 结果、旧缺口父复现、最终包 preflight、两槽原身份退出／摘要审计、7 图字节回执匹配和最终状态。子冻结包及两槽原件在相邻 `review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate/`。这些忽略材料、截图与原软件副本均不提交；报告按独立分支 no-ff 集成到 dev，最终 SHA 与任务／收件箱核对见父 `final-state.json`。
