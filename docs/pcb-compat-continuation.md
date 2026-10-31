# 原软件最小兼容闭环继续核验

2026-10-31，本轮结果为 **failed：首次 Snapshot 无图片，按约停止，原软件输出兼容闭环未完成**。已核对上轮残留 DOSBox 和原创建者身份，但目标窗口实际处于最小化状态，区域截图请求使用其屏外矩形，被公共工具拒绝且没有 image；未发送聚焦、关闭或任何键鼠输入，没有启动新 SYN1 目标。此结果不证明原软件黑屏或输出格式不兼容。

本轮为新的 Task `task_bc20d796d7cf`、Dispatch `ctx_a0f59ee4a9c2`，沿用指定 Pi 会话 `01a19107-f43e-75fd-9e8c-0925f8c21dac`，环境、原 JSONL 模型／推理等级和实际 assistant 记录均核对为 `deng/gpt-6.1-sol high`。准备期间连接错误后由同一模型自行恢复，没有替换模型。工作树从干净的 `origin/dev=a8da1a8c4cad5bd4ab3677ca48612b5ee5dd4c26` 建立独立分支 `verify/pcb-compat-continuation-worker`；仅提交本报告，不合并、不推送、不创建 tag，不修改旧报告、旧脚本或冻结。

本树新忽略证据目录为 `.local-analysis/pcb-compat-continuation/`，下述文件名均相对该目录。原资料已在前轮完整阅读，本轮只核对交接差异，复用既有核心输出和独立字节证据，没有重建生成器、产品或重复全部 CTest。

## 准备与现场边界

新建 `runtime/pt`，从只读原安装 `D:/project/pt_renew/pt` 复制 99 项，只在新副本移除 `TRAXEDIT.DFT`、加入 `SYN1.PCB`，仍为 99 项；原安装不挂载。新 `inputs/` 保存前轮源／输出的完整副本，摘要如下。

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `SYN0.PCB` | 212 | `a87c265b5e8b53c36e49c0b8677767920fee3d903945e2c43de75b2a6976759c` |
| `SYN1.PCB` | 180 | `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228` |

前轮产品核心生成及独立字节比较结论保持：首水平线从 y=1800 移至 y=2200，第二条内部短竖线删除，四条外框原字节保留，FT 总数 6→5。该结论来自[前轮报告](pcb-legacy-native-verification.md)与其原字节证据；本轮没有把它当作 AUTOTRAX 新输出重开通过。

父审阅计划 SHA-256 `e1015a5604ecd676f700e1cb11afa9a5caddf4cd059ea0d7a0728f80cbca5516` 和最终脚本 SHA-256 `4e864b04a7af8cd5685bf02aa4b3042b4d9b89da5f2760a636bda41e5f5b47ef`，明确允许自 **18:01（UTC+8）起、最多 1500 秒**开始，收窄为先正常关闭旧残留并取原创建者退出证据，再仅一次新 SYN1 重开。最终开始指令为 `msg_fe56948e76c1`，在本会话原 JSONL 的 `check` 回执中保存；旧 ask 的“先修正”答复与后续最终允许开始指令分别保留，不混用。

实际 runner 于 **18:11:36.6187391** 启动，PID **16512**，仅创建一个新公开 Windows-MCP `serve` stdio 服务。复用成熟公共 RPC，不修改第三方控制包、门禁或钩子，不恢复旧服务／停止脚本。正常关闭后截图范围在启动前已审阅修正；现场未热改脚本。

计划中的唯一新目标 argv 为本机 `dosbox-x/2026.10.01/dosbox-x.exe -conf <本轮证据>/SYN1.conf`，cwd 为 `<本轮证据>/runtime/pt`，仅挂载新 runtime，保留 opengl／vgaonly／固定 10000 cycles；**该启动未执行**。真实板与独立产品原生另存流程不在本轮收窄现场范围。

## 首次接管与停止事实

`step-001-adopt-old-binding.json`、`step-001-adopt-old-cim.json` 核对以下身份：

| 对象 | 已核对身份 |
| --- | --- |
| 上轮 DOSBox | PID **11096**，birth FILETIME `134379091157937368`，映像为原 DOSBox-X，CIM 父 PID **40336**，命令行仍指向上轮 `pcb-legacy-native/SYN0.conf`，窗口 HWND **21301300**、类 `SDL_app`、标题 `DOSBox-X 2026.10.01: PT - 10000 cycles/ms`。 |
| 原创建者 runner | PID **40336**，birth FILETIME `134379090238890945`，映像 Python，命令行仍为上轮 `pcb-legacy-native/desktop_session.py`。 |
| 本轮查询句柄 | 目标 **692**、原 runner **712**；均为新开只读查询句柄，绝非原 Popen 句柄。原目标 Popen 句柄 **612** 仍属于旧创建者，不重建、不冒称持有。 |

**18:14:39.613092** 的首次原生记录明确显示 `minimized=true`，矩形为 `[-32000,-32000,-31763,-31961]`。脚本在完成身份绑定后、发送聚焦动作之前，把这个矩形用于目标区域 Snapshot；工具在 **18:14:40.454053** 返回文本错误：

```text
Error capturing desktop state: region [-32000, -32000, -31763, -31961]
does not overlap the virtual screen bounds (0,0,3840,2160).
```

该回复 `isError=false` 但只有 text，无 image。脚本独立检查图片缺失，于 **18:14:40.455053** 记录 `Snapshot缺少image；停止输入`，立即停止。本轮此前两次 ControlStatus 均为可用状态；实际停止原因是区域截图无图片，不能改称公共门返回 user，也不能从无图推断黑屏。

到 **18:16:40.456414** 的完整静默区间为 **120.001361 秒**，拒绝后输入、截图、状态和原生桌面请求均为 0。没有重连、聚焦、恢复窗口、关闭或重新截图；没有强杀。父收到 escalation 后明确接受停止，禁止扩大本轮尝试。

本轮统计为 **零键鼠动作、零新 DOSBox 目标、零成功图片／实际 read 图片**。`image-read-receipts.json` 依据当前新 Task 起点后的原 JSONL 保存这一零值与会话前缀摘要；`session-initial.jsonl`、`session-final.jsonl` 保存原字节。没有 PNG 文件，未捏造或复用前轮六图的读图回执作本轮成功证据。

## 退出与后审计

本轮控制服务 PID **36780**，birth FILETIME `134379150967439682`，原 Popen 身份 `2330476719008`、句柄 **520**。静默结束后关闭 stdio，创建者持原 `Popen.wait()` 于 **18:16:40.869532** 返回 **0**，见 `control-created.json`、`control-exit.json`。

本轮 runner 在 **18:16:40.870303** 写出 `runner-finished.json`，证明脚本完成收尾；本工作者没有该 runner 自身的原 Popen wait 回执，不把完成标记扩大为其操作系统退出码 0。旧 DOSBox 与旧 runner 的正常退出仍未证明：上轮目录中 `target-late-normal-exit.json`、`runner-finished.json` 均未产生，本轮仅记录 `old-target-exit-unproven.json` 并释放新查询句柄，原创建者仍承担原 Popen 的等待责任。未用 PID 消失、窗口状态或截图代替原退出证明。

`collect_final.py` 与 `final-audit.json` 实际完成以下只读后审计：

- 原安装 **99 项**、旧 runtime **102 项**、新 runtime **99 项**及两个输入的完整集合、大小和 SHA-256 均与本轮现场前相同。
- 公共控制包 **77 个 Python 源文件**前后相同；计划和最终执行脚本摘要保持父审阅值。
- 既有 v3 manifest 仍为 `d79ce9923630ddd68a57471f2be0cf2f3020db6db88f4521ed3662395090f9e6`，**57 个源码及 18 个二进制／依赖**逐项相符，产品未启动。
- 首次无 image 后桌面请求 **0**，新目标启动 **0**，输入动作 **0**，成功图片读取 **0**。

完整后摘要分别为 `original-after.json`、`old-runtime-after.json`、`runtime-after.json`、`inputs-after.json`、`control-source-after.json`，与对应 before 文件一起留在忽略目录。原安装、截图、运行副本、产品依赖均未提交。

## 未完成范围

本轮通过身份核验、隔离输入保护与按约停止；原目标正常关闭、旧创建者退出证明、SYN1 的工作文件名／Tracks=5／移动横线／删除短竖线／四外框对照及新目标正常退出均未完成。原软件输出兼容性仍未验收，前轮 failed 与原字形 runtime=false 等历史结论保持。

协调者另行报告自由走线新增设计提交 `a179c07`，以及并行静态任务因指定 GLM 模型 quota hard fail、零工具调用而 failed／abandon，未替换模型；这些由父独立记录，不是本轮 GUI 停止原因，也未用于替代本轮验收。后续若安排新现场，应先在启动前静态覆盖“最小化窗口必须先取得可读全桌面基线或正常恢复”的边界，再在新上下文处理残留，不恢复本轮已停止连接追通过。
