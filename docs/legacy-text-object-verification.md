# verification-36：文字属性、计数修正与中断恢复

AUTOTRAX 1.57 的文字属性框已实际显示 **内容 A、高度 240、线宽 1**，并用 Esc 取消返回。重新审阅 verification-35、36 的原始状态截图，`Tracks` 均应读为 **4**，与 C21 的四条 FT 记录一致；前版文档的 0 是画面误读。尚未完成独立字形几何对照，`runtime_verified=false`，产品保持 0.9.0。

开发分支为 `research/direct-object-verification`，基线 `559e3d7`。用户授权代理继续开发并直接控制桌面。原程序、截图、配置、摘要清单和字体数据仅留在忽略目录。

## 保留的运行证据

证据目录为 `.local-analysis/verification-36/`。场景复用已核验的无 DFT 输入和日志配置，没有调整图形后端或窗口尺寸。DOSBox PID 为 28524，客户端 PID 为 29532；关键动作前后的原生前景观测均指向本轮目标。

| 步骤 | 已观察的结果 | 本地证据 |
| --- | --- | --- |
| 1–4 | 新桌面基线、隔离目标启动、AUTOTRAX 启动页、进入文字画面 | `step-001` 至 `step-004` 的返回和截图 |
| 5–9 | 处理输入法状态后进入 Edit → String | `step-005` 至 `step-009` |
| 10–16 | 鼠标及方向键定位后，Enter 选中文字并显示 EDIT STRING 属性框 | `step-016-select-string-keyboard-post-00.png` |
| 17 | 单个 Esc 取消属性框，没有输入新字段值 | `step-017-cancel-string-properties.json`、对应截图 |
| 18–21 | 取消选择状态后进入 Information → Status | `step-021-status-post-00.png` |
| 22 | 操作前控制状态持续为 user，30 秒后停止，未发送返回 Status 的 Esc | `step-022-cancel-status-gate-00.json` 至 `-15.json`、`client-stderr.log` |

属性截图显示 Height=240、Line Width=1、Text=A，与 C21 的 `FS` 高度及笔宽字段一致。属性框未显示原点、方向或图层，因此不能据此宣布这些字段已经完成运行核验。

C21 的一条 FS 和四条 FT 对应 Status 的 Strings=1、Tracks=4，工作文件名为 C21.PCB。文件名、计数和文件访问日志互相支持，但不能替代全部字段、显示层或几何行为的验证。

## Tracks 读数的修正

本轮保留了两次状态页的最近邻派生裁剪：`status35-table-review.png`、`status36-table-review.png`。结合各自原始整屏截图，Tracks 的字形应读为 4，前版 verification-35 文档的 0 予以更正；旧截图不变，修正保留在版本历史中。

参考尺标没有明显显示仍是待验证事实，但不能继续以误读的零计数推断未载入。后续应检查板框层 11 的显示状态，或在新副本中只将参考走线移到已可见的图层，建立独立尺标。

## 清理、输入保护与会话中断

控制等待超时后，旧终端记录显示先核对 PID 28524、父 PID 29532、映像及包含本轮配置的命令行，再仅终止该目标。`owned-target-cleanup-before.json` 保存归属；恢复盘点时查询没有 DOSBox 进程残留。

`source-before/after.json`、`existing-inputs-before/after.json`、`fresh-inputs-before/after.json` 分别为原安装 99 项、新旧副本各 103 项，完整文件集合及 SHA-256 前后相同。`verification-after.json` 记录核验通过、无 TRAXEDIT.DFT。

pi 在准备汇总时反复报 `ENOENT`，指向旧会话 JSONL；恢复时该文件不存在。能够依据旧终端和本地材料还原工作断点，不能据此判断会话文件消失原因，也不能完整恢复历史对话。

恢复后新增本地 `summarize.py`，实际核对输入清单、Enter/Esc 返回、关键前景 PID、16 次 user 返回及第 22 步动作未执行，并生成 `verification-summary.json`。汇总为原截图等关键证据记录 SHA-256；内容、高度、线宽和计数明确标注为人工画面复核，不伪装成自动 OCR 断言。

## 后续独立显示与参考层对照

verification-37 创建全新无 DFT 副本，保留 C21 原文件，新增 V37，仅将四条参考走线从 11 层改为 1 层。配置仍为 opengl，实际启动日志到达 PT 与 GRAPH.DRV 装载、VGA 640×480 模式，但窗口和独立屏幕裁剪均显示黑底白横线，没有取得启动页或 V37 载入证据。

verification-38 使用同样输入，配置仅变更隔离路径及 `output=surface`。通过 Orca Computer Use 按目标 PID 取得窗口截图和操作返回，软件后端显示旧的 DOSBox 文本画面；一次 Enter、目标窗口聚焦及 Capture 菜单操作没有提供可靠的客体画面或原生截图文件。本轮未取得可用于字形拟合的运行证据，不能据此认定板框层就是参考线不可见原因，也不能解释历史黑屏的根因。

两个场景均已核对归属后只清理本轮目标，最终查询没有 DOSBox 残留；原安装 99 项及各实验副本 104 项的文件集合和摘要一致。返回、日志、截图与输入摘要分别保存在 `.local-analysis/verification-37/`、`verification-38/`。不再重复同类显示尝试，原字形几何验证继续保留未完成；可独立验证的 Qt 几何交互开发继续推进。

## 验证边界与后续

本轮盘点已重新完成 Debug 配置、构建及 9 组 CTest，全部通过；其中七组 QtTest 共 232 项。产品代码没有变化，未重复 Release 或手工 Qt GUI 验收。

原程序本轮确认内容、高度和线宽，未确认文字原点、旋转镜像、字符间距、整数缩放差异、笔画端点、线宽面积及低缩放替代路径。独立尺标和非对称字符对照完成前，不将静态工具结果标记为已运行验证，也不接入铜层判定。
