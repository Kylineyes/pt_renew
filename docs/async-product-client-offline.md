# 产品客户端离线实现与冻结时限

2026-10-30，从已核对的`dev=origin/dev=f81576f83397900fd0c861765c57da928d313228`建立`feat/async-product-client-offline`。本阶段实现[产品客户端约束](async-product-client-contract.md)中的可注入API核心，默认禁用；没有启动Qt产品、控制服务、输入钩子或新现场，没有恢复旧Task/Dispatch/批准，也未执行旧演练脚本。**ready_for_live=false，max_product_launches=0。**

## 实现与使用边界

新增`tools/async_product_client/`，仅依赖Python标准库，导入不访问桌面或创建进程。

| 模块 | 已实现行为 |
| --- | --- |
| `core.py` | 不可变Task/Dispatch/run/session身份；全客户端共享ID、token、busy/排队、原收尾截止与首次失败锁存；失败起完整120秒零桌面请求；本地事件等待每块至多1秒 |
| `review.py` | Snapshot原工具成功image、文件摘要、尺寸/倍率/物理rect；唯一request及图hash；绑定原会话JSONL的实际read/image/模型/session/时序；显式内容判断ack及一次消费 |
| `store.py` | 新目录独占创建request/ack，flush/fsync，不覆盖旧文件；写入未知不得重用机会 |
| `product.py` | 创建前核对完整22文件和新输入摘要、清理继承环境；创建后立即保存原Popen；核对原句柄创建身份，精确绑定主HWND；Qt主窗/模态关系与物理坐标；普通选择/Delete保持前景后验及canvas焦点保护 |
| `race.py` | NET/铜单次竞争的门闩图→实际read/ack→一次选择/Delete→编辑图→实际read/ack→唯一release→原回调淘汰→终图/read/ack；同应用时钟及外部保守截止分别检查 |
| `close.py` | 窄正常关闭：结算后一次原Shortcut Alt+F4；dirty时核实同PID/birth/image及owner模态并实际读图，再明确点击“放弃更改”或“取消”；原Popen有界wait、退出码及退役独立记录 |

`ProductOwner.launch()`的创建器、原句柄身份读取、native/工具/Snapshot及本地门闩API均注入。本阶段测试传入假API和假Popen，**没有交付可直接用于现场的Win32/MCP适配器或启动命令**。普通文本输入、Enter、通用快捷键、文件框自动操作不在该模块入口中；遇到原生文件框等owned窗口时拒绝主窗输入，不能借用主窗阶段发送按键。

主窗精确标题按冻结实验源码生成：`board.pcb · 工作副本 · 不支持保存 · PT Renew`及`board.pcb * 已修改 · 工作副本 · 不支持保存 · PT Renew`，不采用任意前缀。dirty模态精确标题为“放弃工作副本更改？”，必须属于同一主HWND，默认按钮必须为“取消”。主窗和模态同为`Qt6120QWindowIcon`时，仍按HWND及owner分别核对；不按Qt类计数识别主窗。

原Popen必须由持续存活的客户端直接创建并保留；创建后的身份核验失败也保留Popen引用及已消费启动机会，不重新按PID接管。正常退出只等待该对象，不重新查询句柄代替它。原句柄读取/持续owner及外层见证链仍须由以后冻结的现场适配器接入并实测。

## request/read/ack的证据链

request独占记录Task/Dispatch/run、应用request、PID/birth/image/主HWND、当前图HWND、图hash、工具call及起止、实际尺寸和物理倍率、应用原deadline与本地保守deadline。每张图单独request，不接受跨阶段或相同hash复用。

ack不能自行提供会话文件或用`observed=true`代替读图。`PiReadVerifier`只读构造时绑定的原JSONL：必须有唯一session header、实际assistant的`deng/gpt-6.1-sol/high`字段、request发布之后的`read`调用、同路径及唯一成功`toolResult` image；解码image必须与截图文件hash相同，并保存原JSONL快照hash、call/result记录ID及起止时间。会话时间必须有时区，request到ack出现超过1秒墙钟跳变则拒绝。

图像内容判断仍由指定会话明确提交，包括新修订、dirty、零走线、NET A来源；代码核对其与冻结判据相同，**不自动从日志或图片推断人工已经看过**。生产适配器须从可信原Snapshot回执构造`Snapshot`，从可信原会话文件提供read记录；不能将外部ack JSON当作可信原工具/会话记录。当前验证器对变换/缩放或删减image的会话记录保守拒绝，尚未用新的实际Pi上下文验证记录兼容性；如果需要适配，必须另行冻结可审计的变换链，不能放宽为只认文字成功。

消费ack与release尝试分开记录；release调用前先消费编辑ack和唯一机会。传输错误、取消或回执未知都锁存失败，不重发。release前重新读取本地门闩状态，核对未aborted/returned及剩余时间；不会额外调用ControlStatus。最后仍要核对同应用时钟的`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`及原淘汰决定。应用事件链只提供一部分证明，完整事件字段仍用`audit_async_race.py`独立审计，不能以`settled`属性替代最终GUI或事件验收。

## 冻结时限设计

以下是执行前必须满足的门槛，**不是实际模型耗时或未来上界的证明**。冻结实验看门狗保持60000ms，不热改EXE，不重置门闩时钟。

| 检查点 | 从目标请求触发前原本地单调时钟起算 | 超时行为 |
| --- | ---: | --- |
| T1：门闩图Snapshot、指定会话实际read及ack完成 | 严格小于20秒 | 停止后续选择/Delete/release |
| T2：唯一选择/Delete、文档发布、编辑图及实际read/ack完成 | 严格小于50秒 | 不release，不补写ack伪通过 |
| T3：release前最后本地只读检查与开始唯一调用 | 严格小于55秒，应用时钟也须余量大于5秒 | 不调用release |
| release回执 | 严格小于60秒，且应用released时间早于原deadline | 锁存未知/失败，不重发 |
| 本地门闩事件等待 | 每块至多1秒，总等待受原截止约束 | 不重建时钟或新增等待预算 |

本地起点必须来自**触发目标请求之前**的可信调用起点，不能取“观察到gate-ready”或“写request”时刻。以`trigger+60秒`给出的本地deadline只会更保守；应用QElapsedTimer纳秒顺序单独检查。Windows进程birth FILETIME仅比较身份，从不与应用纳秒时钟相减。更短看门狗按1/3与5/6比例收紧T1/T2，释放余量保持独立校验。

正常收尾保留35秒工具余量、5秒原Popen等待及40秒stop余量；每次输入前重新检查，dirty模态request的截止预留这80秒。原600/900秒总预算只作为未启用模板记录，离线冻结不开始计时、不生成批准。新现场不得通过重连或新组重置已开始的预算。

任一失败后，原failed ID/token、首次120秒截止和cleanup deadline保留。120秒内零native/截图/状态/输入请求；原Popen本地wait及本地门闩状态不属于桌面请求。冷却后只有在实验已结算，或确证aborted且原工作线程已经返回时，才允许显式窄正常收尾；成功退役也不改变失败组结果。dirty取消会做普通主窗后验且不等待退出，关闭机会仍已消费。任何错误输入之后即使原Popen后来退出0，也只记录生命周期结束。

## 测试与冻结交付

`tests/test_async_product_client.py`使用假时钟、假Popen/API和临时合成会话/图片字节；不冒称这些字节是产品截图或模型实际读图。覆盖两种实验完整调用链、阶段和唯一输入计数、错身份/owner/同类多窗、文本焦点、普通输入后验、忙/排队/旧token/冷却/原截止、错图/无image/错模型/session、预写/重复/过期ack、T1/T2/释放余量、时钟跳变、门闩取消/提前返回、应用状态倒退、release未知、dirty取消/放弃、Popen超时/非0/错误后退出。

`tests/test_freeze_async_product.py`使用合成22/23/22/77文件集合，核对新目录、完整复制和摘要、默认禁用、无Task/Dispatch/批准，以及来源或输入改变时不能发布最终manifest。`tools/freeze_async_product.py`只在新目录生成候选，复制本模块、测试、文档、3个已有标准库见证器、冻结实验部署、控制包和本轮新输入；固定/稳定产品和历史证据只引用只读摘要。见证器复制不等于已接入产品启动链。

`tests/test_async_product_client.py`的27项及`tests/test_freeze_async_product.py`的3项，共**30项新增测试全部通过**；仓库Python测试全集**234项全部通过，20.495秒**，见[最终日志](../.local-analysis/async-product-client-offline/tests-final-v2.log)。这是Python工具回归，不是Qt CTest或产品GUI验收。

本机证据写入新的`.local-analysis/async-product-client-offline/`。首轮20项测试有1项暴露本地wait误受桌面冷却限制，修复后20项通过；后续新增时限/并发/冻结等测试，早期失败日志保留。只读复核首次误将既有`__pycache__`计入，而历史清单明确排除字节码；查明缓存早于本会话，未删除或改写，按相同口径最终10组参考全部匹配，见[只读结果](../.local-analysis/async-product-client-offline/readonly-verification-final.json)。既有149项控制测试与10项离线审计保持独立范围，不将测试数量相加当产品验收。

## 下一步和现场条件

当前没有新Task/Dispatch、模型读图或现场批准；离线候选始终ready_for_live=false。下一步先在指定模型可用时另立**新上下文**，离线验证原会话image记录兼容性和顺序request→read→ack两图耗时，不恢复已failed/abandoned演练或执行其旧脚本。即使一次小于60秒，也不能自动认为未来可靠。

随后补冻结的产品现场适配器和原Popen全链启动/见证接入，先用假API回归，再冻结新客户端全部模块、控制包、EXE和输入。只有时限与收尾条件均可验证，才形成NET、铜各最多一次竞争的新Task/Dispatch/证据和具体可审阅顺序；现场前说明**实际开始时间、预计时长、桌面及进程范围**，在持续必要控制授权内完成最终审阅。该步骤不提前启动等待批准的短握手进程。

本阶段不安排产品现场，也不提供虚构的现场开始时间。稳定0.10.0、固定0.11.0和独立实验的证明边界保持；固定候选整体验收、完整竞争及原字形runtime均不因本次离线测试通过而升级。
