# 原软件单线重试：Return 启动转换及软件输出对照

本 Task 结果为 **failed：未取得原 AUTOTRAX 新建单线、全新保存及重开样例**。本轮已在两个新隔离实例各实际发送一次 `Return --restore-window`；OpenGL 槽仍为黑底白横线，`surface` 单变量槽显示 DOSBox 启动说明／挂载文本，两槽 Return 前后及各自物理屏幕图均无变化，日志均未见 `SYN1.PCB` 打开记录。两个原目标均正常 `wait=0`、`forced=false`；没有执行菜单编辑、创建线段或保存，六／七字段、附加值、换行、排序和默认参数仍未知。

沿用 Pi `deng/gpt-6.1-sol high`，会话 `01a19a20-d1f1-761b-8916-078f4c28b7ef`；环境、model／thinking 事件、实际 assistant 和成功工具回执保存于本树 `.local-analysis/native-created-retry/session-audit.json`。本 Task 为 `task_c97906c5400d`／Dispatch `ctx_db8126806671`，独立分支 `verify/native-created-retry` 基于 `origin/dev=fbbc572a46463f617481618f214c49d0b2549829`。只新增本文和忽略目录证据，不修改旧报告、产品或测试，不合 dev／推送。

## 新副本与两槽现场

证据根 E 为本工作树 `.local-analysis/native-created-retry/`。原安装 `D:/project/pt_renew/pt` 只读，每槽从原件新建隔离副本；核对原安装99项复制一致后，仅在副本移除 `TRAXEDIT.DFT`、加入冻结 `SYN1.PCB`，运行目录仍99项。C／D仅挂载各自新 `runtime`，客体目录 `C:\PT`，预定新目标 `FTNEW.PCB` 不存在。冻结输入180字节，SHA-256 `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`；这是合成启动输入，不是原软件新建字段证据。

复用既有轻量 `orca computer` RPC 和修正 `argparse.REMAINDER` 的原 Popen owner；未恢复旧PID／driver／服务，也未启动 Windows-MCP。RPC逐次核对精确PID及birth，命令指定HWND并恢复目标窗口。每个动作后实际read原PNG，再决定下一动作。

| 项目 | OpenGL 槽 | surface 槽 |
| --- | --- | --- |
| 预告时段，北京时间 | 16:10–16:55，16:48起留7分钟收尾 | 父追加授权17:00–17:30，17:23起留7分钟收尾 |
| 证据目录 | E | E/surface |
| 原owner／目标PID | 20532／13692 | 17080／16008 |
| birth FILETIME字符串 | `134380815283758810` | `134380836060811697` |
| HWND | 7866396 | 13372498 |
| 实际启动，UTC | 08:25:28.393967 | 09:00:06.098550 |
| 单次Return请求开始，UTC | 08:38:24.901604 | 09:05:41.530402 |
| 正常原wait，UTC | 08:41:53.432817 | 09:09:24.034806 |
| 原waitReturn／forced | 0／false | 0／false |

第一槽准备及读图耗时未形成完整业务进展，仍在预定边界前正常关闭。随后协调者明确授权第二槽，开始前再次预告、核对收件箱；前一实例退出后才启动新实例。原owner记录保留Popen identity、handle、完整argv及映像SHA，FILETIME使用原JSON／Python int或字符串，不经JS Number。

软件输出的选择依据本机 `dosbox-x.reference.conf` 第17行：`surface = software (SDL_Surface)`。`surface/single-variable.json`核对新副本与首槽before一致，配置除隔离根路径外仅将 `output=opengl` 改为 `output=surface`；未改变CPU、周期、机器、输入或同时组合其他选项。日志实际出现 `surface consider=640x480 final=640x480`。只做这一次单变量对照，没有第三种组合。

## 实际 Return 结果与图像证据

两槽均执行精确 `pid`、`--window-id`、`--key Return`、`--restore-window` 的公开 `press-key`。原RPC退出码为0，actionName为pressKey，verification为synthetic_input／unverified。因此可确认请求实际执行，不能凭工具回执单独宣称DOS客体收到等价物理按键；也不能把本轮重新描述成“Return未执行”或“零输入诊断”。

| 原图，相对各槽目录 | OpenGL SHA-256前8位及实际观察 | surface SHA-256前8位及实际观察 |
| --- | --- | --- |
| `rpc/001-startup-0.png` | `03a26461`，黑底白横线，无可辨AUTOTRAX启动页 | `4ae2321f`，DOSBox启动说明及C／D挂载文本，无AUTOTRAX界面 |
| `rpc/002-return-startup-0.png` | 同首图摘要，Return后无可辨变化 | 同首图摘要，Return后无可辨变化 |
| `rpc/003-after-return-screen.png` | 同首图摘要，目标物理屏幕亦同 | 同首图摘要，目标物理屏幕亦同 |

六张原PNG均为 **662×566**，本模型分别实际read，成功image回执解码SHA与对应原图一致；本轮没有大图缩放，不把其他历史缩图的摘要当原图摘要。每槽 `audit-final.json` 保存原路径、SHA、尺寸、本会话entryId／toolCallId／读取时间，及原RPC命令／退出码／PNG提取摘要。相同SHA的不同文件仍分别保留。

物理屏幕截图为 `System.Drawing.CopyFromScreen`，核对目标进程birth、前景HWND，使用每监视器v2线程上下文读取物理矩形 `[89,100,751,666]`。每槽 `003-after-return-screen.json`保存方法、时刻、矩形与SHA。窗口图与物理屏幕一致，不能仅归为Orca窗口捕获；两种输出的不同表象也不足以证明根因或某个后端普遍可用。

两槽各有3次公开RPC：首图get-app-state、单次Return、看图确认宿主X后正常关闭；另各有1次只读物理屏幕截图。关闭RPC未返回image，准确保留为空，不宣称关闭后截图成功。日志确认本轮配置／cwd、PT／GRAPH／MNU／KEY／PAD访问，但均无SYN1打开；窗口标题PT和文件访问请求不能替代文件名、图元计数或空板的GUI确认。

## 退出、摘要和剩余边界

两个目标的 `runtime/native3-held.json` 与 `native3-exit.json`逐项核对PID／birth／Popen identity／handle相同，原owner真实waitReturn均0、forcedDeadlineTermination均false。各槽 `processes-final.json`记录目标及owner查询空集合；目标wait不冒称为owner自身OS退出码。两个实例均在各自收尾边界前正常关闭，此后没有桌面请求。

两槽 `audit_final.py`均退出0，完整核对原安装99项、各运行副本99项及冻结输入1项的路径集合／大小／SHA-256前后一致；六图原image回执及RPC原图摘要全部匹配。两槽captures为空，`FTNEW.PCB`均不存在。证据入口：

- `E/audit-final.json`：OpenGL槽完整图像／RPC／文件／日志／原wait索引。
- `E/surface/audit-final.json`：软件输出槽相同完整索引。
- `E/surface/single-variable.json`：配置及输入单变量核对。
- 两槽 `original-before/after.json`、`runtime-before/after.json`、`inputs-before/after.json`：完整文件集合摘要。

<a id="explore-ex-005"></a>

工作文件名、计数、空板、可靠File／Information、用户所选层／宽／端点、原生新线保存／重开均未完成。没有字段证据可供开放默认写出或UI能力门，一个未生成的文件不能推断默认值，也不证明全层或NETDEF兼容。上一轮可辨菜单事实仍见既有报告，本轮不覆盖或解释其根因。

[探索 EX-005](exploration-backlog.md#ex-005)。

本次仅新增研究文档，不改产品，故不重复Qt构建／CTest；验证为两槽实际Return请求、原图读取、原创建者正常wait及完整文件摘要审计，并在提交前执行 `git diff --check`。本Task按真实failed结算，后续由协调者统一决定最小试验与产品范围。
