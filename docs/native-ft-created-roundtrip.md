# 原 AUTOTRAX 新建单线保存重开取证：未完成

本 Task 结果为 **failed：没有取得原软件新建、保存并重开的单线样例**。本轮 `live03` 的两张稳定窗口截图及一次目标物理屏幕截图均显示黑底白横线，没有可辨启动页或工作文件名；宿主 Capture → Take screenshot 请求后没有生成客体 PNG。目标正常关闭，原创建者真实 `wait=0`、`forced=false`；原安装、运行副本和冻结输入的完整集合／大小／SHA-256 前后一致。**六／七字段、附加值、换行、排序及新增走线默认值均未核定。**

本报告不覆盖[上一现场可辨启动页和菜单的事实](native-ft-sample-verification.md)，也不解释其菜单误选或历史黑屏根因。菜单坐标、输入通道及前两次无目标启动的准备结果见[菜单校准报告](native-menu-calibration.md)。

## 范围、模型与现场时段

沿用 Pi 会话 `01a19a20-d1f1-761b-8916-078f4c28b7ef`，实际环境、model／thinking 事件、assistant 及成功工具回执核对为 `deng/gpt-6.1-sol high`，审计为 `.local-analysis/native-menu-calibration/session-audit.json`。独立分支 `verify/native-menu-calibration`，监督 Run `run_98316b665261`、Task `task_5762f1bd719e`、Dispatch `ctx_001465cfe3a8`。仅修改授权的两份研究文档及忽略目录证据，不修改产品、writer、UI、CMake或其他 worker 工作树，不合 dev、不推送。

协调者在 UI 普通产品目标正常退出后，以 `msg_434c8f53bfa2` 正式移交唯一桌面权；现场为北京时间 **2026-11-02 13:35–14:05**（UTC05:35–06:05），14:00 起至少五分钟收尾。操作者已在 commentary 和结构化消息预告，未另问重复许可。真实目标于13:41:35启动，13:55:07正常退出，此后仅离线审计，没有重启。

此前两次准备未启动 DOSBox：第一次本地 JSON 请求发布错误后静默收尾，第二次因桌面排程调整停止；其服务／runner 四项原 wait 均为0，原安装及两份副本摘要一致。完整事实仍保存在菜单校准报告及 `.local-analysis/native-ft-created-roundtrip/checkpoint-ui-handoff.json`，没有将它们计为本轮菜单或保存验收。

## 新隔离输入及启动

本轮本地证据根 E 为：

```text
C:/Users/rikideng/orca/workspaces/pt_renew/verify-native-menu-calibration/.local-analysis/native-ft-created-roundtrip/live03/
```

复制原安装 `D:/project/pt_renew/pt` 的99文件到新 `E/runtime/pt`，先核对完整一致；仅在新副本移除 `TRAXEDIT.DFT`，加入冻结 `SYN1.PCB` 后仍为99文件。原安装不运行、不挂载。C／D 只挂载本轮 `E/runtime`，客体工作目录为8.3路径 `C:\PT`，配置依次执行 `pt SYN1.PCB`，预定新目标 `FTNEW.PCB` 从未存在。

`SYN1.PCB` 为180字节，SHA-256 `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`。它是已有合成五段输入，只用于启动及后续计划的状态确认，不是原软件新建样例，不能当作六／七字段或附加值的默认依据。

本轮直接复用已验证的 `orca computer` 轻量 RPC 包装，目标由独立 Python owner 保持原 Popen；未启动 Windows-MCP 服务或旧冻结驱动。RPC 按精确 `pid:9716` 操作并恢复目标焦点，点击为窗口局部坐标。owner 的截止强制 terminate 分支改为记录仍存活后继续持有等待，实际未触发截止分支。

启动准备存在一次本地参数失误：13:38:09创建 owner PID28144 时，复制脚本的 `argparse args nargs=*` 不能接收直接传入的 `-conf`，没有生成 held／目标证据；随后只读查询不见该 owner，没有其原创建者真实退出码，故不称已证明其 exit=2 或正常退出。最小修复为 `argparse.REMAINDER`；第二次owner启动保存stderr，正常创建下述唯一DOSBox。此处是本地参数失败，与原软件后续画面不可辨分开记录。

| 项目 | 本轮原始证据 |
| --- | --- |
| DOSBox-X | 2026.10.01，映像SHA-256 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832` |
| 原创建者 | owner PID63316，`runtime/native3-held.json` |
| 唯一实际目标 | PID9716，birth FILETIME字符串 `134380716956894590` |
| 原 Popen | identity字符串 `2707447052480`，handle字符串 `532` |
| 窗口 | HWND7735714，`DOSBox-X 2026.10.01: PT - 10000 cycles/ms` |
| 目标开始 | UTC05:41:35.717993，完整argv、exe摘要及owner记录在held中 |

FILETIME、Popen identity／handle用原JSON／Python int或字符串保存，不经JS Number丢失精度。复制时的owner实际记录还有Qt scale环境字段；该变量不构成DOSBox渲染参数或根因证明。运行使用的脚本及其摘要以本轮实文件为准。

## 实际截图与动作

E下 `rpc/` 保存每次原CLI JSON、请求命令、退出码、耗时、原图副本及SHA。所有五张本轮PNG均由指定模型实际read，`audit-final.json`逐张保存本会话原image回执ID／toolCallId／时间及解码SHA匹配；同SHA的不同截图路径分别保留。局部图为662×566，不用聊天渲染缩放猜坐标。

| 步骤，UTC | 实际动作及观察 | 证据，SHA-256前8位 |
| --- | --- | --- |
| 05:43:23 | 精确目标get-app-state并restore；原图为黑底白横线，未发送启动页Return | `001-startup-0.png`，`306baaca` |
| 05:45:36 | 再取稳定目标图，与首图逐字节相同，仍不可辨 | `002-stable-0.png`，`306baaca` |
| 05:47:55 | 仅点可辨宿主Capture菜单，局部坐标(445,60)，菜单实际出现Take screenshot等项 | `003-capture-menu-0.png`，`da6ab169` |
| 05:50:08 | 按协调者建议取一次物理屏幕；背景仍黑底白横线，宿主Capture菜单可读，与同时窗口图SHA相同 | `004-physical-screen.png`，`da6ab169` |
| 05:52:33 | 仅点宿主Take screenshot，局部(533,94)；菜单消失，窗口图恢复黑底白线；captures未生成客体PNG | `005-native-capture-0.png`，`306baaca` |
| 05:55:05 | 仅点看图确认的宿主X，局部(616,22)，正常关闭；CLI没有返回新image，不将缺图称为成功截图 | `006-host-normal-close-raw.json`及receipt |

物理截取使用已有 .NET `System.Drawing.CopyFromScreen`，仅截自有目标矩形：先核对PID及birth、目标为前景、线程每监视器v2 DPI上下文，再读 `GetWindowRect=[89,100,751,666]`。方法、时间、矩形、HWND及完整SHA在 `004-physical-screen.json`。这项结果缩小了“仅Orca窗口捕获遗漏OpenGL内容”的猜测，但不能凭一次对照证明OpenGL、配置继承、原软件或特定系统设置的根因。

本轮公开RPC合计5次：2次get-app-state、3次宿主click；另有1次只读物理屏幕截图。**0次客体Return／字母／F3／文本输入，0次编辑或保存。** 局部点击回执均为 synthetic／verification unverified，菜单出现及关闭分别由实际原图及原Popen wait补足观察，不把工具回执本身当成业务证明。

协调者UTC05:54:42发出的单Return启动状态转换建议在目标关闭后才被本模型读取；随后又收到“已见wait0，不为建议重启”的明确指令。因此该最小诊断**未执行**，未取得其是否能显示启动页／读入SYN1的结论；不把未执行描述成无效。

## 日志、文件及退出审计

stderr明确记录加载本轮绝对 `SYN1.conf` 和本轮 `runtime/pt` cwd；startup.log记录OpenGL 4.6 NVIDIA617.42、桌面3840×2160、144DPI报告、PT、GRAPH.DRV、MNU、KEY及PAD访问和640×480模式。日志没有本轮 `SYN1.PCB` 打开记录；文件访问请求本身也不证明完整载入。未观察到工作文件名／Status计数，不能确认当前板图或空板。

将上次可辨现场的配置与本轮配置各自把隔离根替换为同一占位符后，文本一致。这只能说明这两份配置文本除隔离路径外一致；没有验证全部继承配置、启动环境或渲染状态，不能据此解释本轮与旧轮画面差异。

目标原创建者于UTC **05:55:07.267381** 在 `runtime/native3-exit.json` 保存同一PID／birth／Popen identity／handle的真实 `waitReturn=0`、`forcedDeadlineTermination=false`。这证明本次宿主正常退出，不证明原软件业务完成。后续CIM查询目标9716、owner63316及首次owner28144均不见，时间与空数组在 `processes-final.txt`；owner自身没有额外原父wait回执，不能把目标wait误称为owner操作系统退出码。

`audit_final.py` 首次因空PowerShell管线没有创建进程结果文件而失败；改为结构化时间／PID列表／空数组后重新完整运行退出0，原失败回执保留在本会话。最终 `audit-final.json` 及三份after清单确认：

- 原安装99文件，运行目录99文件，冻结输入的完整路径集合、大小、SHA-256与各自before一致。
- `FTNEW.PCB`不存在；`captures-after.json`为空集合。没有原生客体PNG，故不能说客体原生截图也是黑图。
- 五张原图都有本会话实际image回执，摘要与原图匹配；RPC保存的原图摘要也全部匹配。
- 原目标wait=0、forced=false；完整argv、原文件／日志／配置／脚本摘要在最终索引中。

<a id="explore-ex-007"></a>

未新增用户线段，没有可记录的用户所选层、宽、端点或经原软件确认的默认值；六／七字段、附加整数、换行及记录布局不能从未生成文件推断。新增写出与原AUTOTRAX兼容阻塞仍在，由协调者统一决定后续最小试验和产品开放范围。

[探索 EX-007](exploration-backlog.md#ex-007)。

本次只提交文档，不改产品；不重复Qt构建／CTest，既有Debug／Release各19/19不算本次新验证。最终检查为新审计脚本成功、图像回执及文件摘要核对、`git diff --check`；文档提交后将按真实failed向协调者结算，不再启动现场或子代理。
