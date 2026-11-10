# 主窗载入生命周期与写出保留：独立现场验收

<a id="explore-ex-030"></a>

最终固定候选 `374b1d7fdf0e06fd0a7b31890348cc243f7306ca` 的本轮核心范围通过真实 Qt 界面验收：读取排队期间编辑和 Undo/Redo、失败保留、同步失败 inspect 使旧读取过期、双闸门下旧回调不能解除后续 busy、关闭确认取消、真实主窗另存保存点与输出重开。未发现上述已执行路径的产品缺陷；模态重入、同步成功替换、Created 新增及默认拒绝没有在本次现场重演，不纳入本次独立现场通过结论。

[探索 EX-030](exploration-backlog.md#ex-030)。

本工作在 `verify/parallel-save-hardening` 独立分支，只修改本报告和自有 `.local-analysis/parallel-save-hardening-live/`，未修改根 CMake、`src/`、`tests/` 或其他工作树。父代理完成产品集成与正式全量测试，本报告不把父测试当作本代理新跑。

## 固定候选与模型证据

父冻结 manifest 为 `main-2/.local-analysis/parallel-development-20261103/candidate-freeze.json`。通过 `git archive` 导出指定提交后，355 项大小与 SHA-256 全部匹配；29 个历史 Python/文档文件的归档为 CRLF、父 manifest 为 LF，仅转换换行后匹配，逐项转换记录保留，`src/` 与 CMake 无此差异。实际宿主链接该快照真实 `pt_ui`，本树早期 `0655a00` 未作为候选。

Release 配置和编译由原 Python owner 逐步记录真实 `wait=0`，耗时分别为 4.19 秒、30.01 秒，回执 `build-exit.json`。宿主 SHA-256 为 `72777cc666cbdfe93452b34cf61f9279636ff44318b2b3120b2e309993776181`。首次冻结 assert 失败后误启动的 build owner 仅因快照清单缺失而退出，未执行 CMake；最终候选实际配置/编译一次通过，该准备失败原记录保留。

Pi 会话 `01a19fa1-5219-7342-9ee0-3e6eb23772b4` 的原始 model/thinking 事件为 `deng/gpt-6.1-sol`、`high`，具有相同模型 assistant 和 `isError=false` 成功工具记录。18 张原 PNG 均由本会话实际 read；最终审计逐张核对 RPC SHA、磁盘 PNG SHA、成功工具 image 块解码字节 SHA 完全一致，零缺失或摘要不符。截图主窗为 1722×1306，小于图像缩放阈值；菜单截图 225×213，不用缩图推定原图摘要。

## 真实现场结果

诊断宿主明确显示“产品新增未开放”，复用旧 `freeze_source.py`、`rpc.py`、`launch_owner.py` 和严格 reader 检查工具。全局线程池设为一个线程，两道 `QSemaphore` 控制真实读取顺序；按钮仅调用公开 `MainWindow` API 和产品 QAction，不触碰私有字段、不直接标记 dirty 或保存点。状态只读文档、修订、dirty、历史、动作以及真实 watcher/`boardLoadFinished`。

| 实际检查 | 可观察结果及原图 | 结论 |
| --- | --- | --- |
| 载入 INPUT、已有 FT 移动 | `s01` 两条 FT、clean；实际移动后标题带星号、dirty、Undo 可用 | 通过 |
| 读取排队期间继续编辑及历史 | `s03` A 阻塞、打开/另存禁用；`s04` 再移动；`s05` Undo 后 Redo 可用；`s06` Redo 回已编辑几何 | 通过 |
| 后台读取失败保留 | `s07` 真实失败状态，watcher finished/destroyed=1、载入回调=1；INPUT、dirty 和 Undo 保留，打开/另存恢复 | 通过 |
| 同步失败 inspect 使旧读取过期 | `s08` A 仍阻塞时同步 inspect MISSING 返回 false，原文档及历史保留，打开/另存立即恢复 | 通过 |
| 旧回调不能解锁后续 busy | 固定顺序 A→旧 OTHER→B→后续 MISSING；`s09` A 已结束、B 阻塞、旧 watcher finished/destroyed=2，但业务回调仍1，打开/另存仍禁用；当前 INPUT 不变 | 通过 |
| 后续读取正常结束 | `s10` 释放 B 后 finished/destroyed=3、回调=2，失败保留 dirty/历史，动作恢复 | 通过 |
| 关闭取消及旧读取丢弃 | `s11` 真实放弃确认框；`s13` 点击取消后 INPUT dirty/历史保留，动作恢复；`s14` 释放旧读取，destroyed=4而业务回调仍2，当前文档不替换 | 通过 |
| 真实主窗另存新文件 | `s15` 实际点击显式 API 按钮，发布全新 HARDENED-SAVED，clean、Undo 保留，来源仍 INPUT、最近输出单独记录 | 通过 |
| 保存点 Undo/Redo | 菜单 Undo 已实际调用，`s18` 菜单关闭后读图 dirty=1、Redo=1；`s19` 通过诊断按钮触发真实产品 Redo QAction 后 clean、Undo=1 | 通过 |
| 真实重开输出 | `s20` 点击重开，标题及来源 HARDENED-SAVED，clean、Undo=0/Redo=0，两条 FT；严格 reader 独立复核 Loaded 身份2/4及几何 | 通过 |

本次起点为 `(100,100)→(400,500)` 的首条 FT，三次实际移动累计 `(75,90)`，最终为 `(175,190)→(475,590)`；第二条 FT 保持 `(600,100)→(900,100)`。原件未写回，工作历史在失败/取消路径保留，只有真实重开成功才建立新的 clean、无历史文档。

## 文件字节与摘要

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| INPUT.PCB | 74 | `0d0bec3a1975a44182dbe8abf7071c6e1f3d2ce6a5859acaebdc28a4178c189e` |
| OTHER.PCB | 39 | `f0a55abedfdc2e250a1136cc169d2d1f8a0189626e029622bd84a72b77676eab` |
| HARDENED-SAVED.PCB | 74 | `51dbf589b06cc7b6fdd1d24b20f2c2b8b4a84fe4e95508b51466ee6474e786d3` |

两份输入前后摘要不变。输出逐字节精确等于 INPUT 只将首 FT 的四坐标词替换为 `175 190 475 590`，第七字段 `42`、第二条 FT、混合 CRLF/LF、ENDPCB 及 DOS EOF 全部保留；没有新增记录。本次调用 `saveAsFileWithCreated` 时无 Created，真实 writer 回落既有图元写出路径，不宣称验证了新段编码。

## 时段、正常退出与控制限制

父消息 `msg_c75ebfdb31c1` 明确移交唯一桌面后，原申报时段为北京时间 12:33–13:18、13:11 起只正常收尾。输入桌面只读核对为 Default，未切换桌面；12:34:02 启动固定宿主，原 owner PID52952、目标 PID53680、birth FILETIME `134381540423538516`、原 HANDLE528、Popen identity `2930871613296`、HWND19270334。

父在消息 `msg_379c94a27944`（05:10:55Z）追加有限 GO：只允许已生成输出重开、实际读图和正常关闭，13:14 起收尾、最终13:21，禁止其他新业务。该消息在13:12:52收件检查返回，13:13:54 ack，单独保存为 `GO-continuation.json`，未覆盖 owner 原 schedule。重开发生于13:10:51、未跨原13:11业务截止；重开原图 read 与正常关闭属于随后收尾，未重复重开或再启动。

13:12:53 点击主窗 X 正常关闭后，原 owner 保存 `waitReturn=0`、`forcedDeadlineTermination=false`，早于原13:18和新增13:21最终截止。关闭 RPC 的后快照返回 `app_not_found`，该错误与原进程正常退出一致；不据错误重复点击、不强杀。父随后独立核对同一 Popen/HANDLE/birth/exe 摘要及 wait，桌面正式结束，之后无新窗口、截图或键鼠。

控制异常均保留：`s02-pending` 因控件树重排后使用旧索引，实际第二次命中移动，不是排队证据；真正排队证据从 `s03` 开始。`s12` 取消索引过期报 `element_not_found`，按工具提示刷新后 `s13` 成功取消。菜单 Undo 后截图 `s16` 仍为 popup，不能单凭该图判 dirty；指定主 HWND 的 `s17` 返回 windowNotFound，先核对 capabilities/最新窗口后对同一 owned PID 发送 Escape，`s18` 才是主窗 dirty 实图，期间无权限/锁屏/失焦拒绝或换入口绕过门禁。

## 未重演范围及证据位置

按父 `msg_6e8211e37b4b` 和新增有限 GO，后半段优先当前实际编辑的保存点及重开，不重置为“一次移动”，不重跑旧 Created 闭环。以下明确不作为本次现场通过项：同步 inspect 成功替换、确认框内重入、关闭后清空再开、Created 新增/默认 writer 拒绝、Windows 原生另存框。相关正式自动化由父固定候选双配置各23/23通过；旧 Created/原生框现场见 [mainwindow-created-save-live.md](mainwindow-created-save-live.md)，不能说本代理这次重新执行。

普通产品单一新增能力门在本候选运行状态始终为 false，源码审查也确认未开放；默认 writer 拒绝 Created 的既有边界由正式测试和旧证据覆盖，本次仅看到 DEFAULT-REJECT 目标不存在，未点击其诊断按钮，不以“不存在”冒充本次拒绝测试。没有原 AUTOTRAX 兼容结论。

本机证据根 `.local-analysis/parallel-save-hardening-live/` 包括固定快照和逐文件清单、父manifest、诊断源码/构建回执/exe摘要、原模型事件、所有 RPC/18原PNG及实际 image 回执审计、输入输出前后摘要、状态/事件历史、原Popen退出、原GO及追加GO。`final-audit.json` 记录355源码项零不符、18图零不符、两输入未变、输出精确匹配、原owner wait0；`output-inspected.json` 为真实严格 reader 输出。以上忽略目录、图像、软件及构建均不提交。
