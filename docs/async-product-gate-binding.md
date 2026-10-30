# 应用UUID、原门闩与可信窗口的离线接入

2026-10-30，从已核对的`dev=origin/dev=42d7556b589232eceb803cbebdc5eace04015726`建立`feat/async-product-gate-binding`。继续[原回执与原Popen适配](async-product-evidence-adapters.md)，本阶段补应用随机UUID、原日志/清单到GateState、唯一release确认和可信窗口只读采集。另立全新任务取得了两张归档图的实际read/ack与计时证据。产品与桌面请求仍为0，**ready_for_live=false**。

## 两种运行身份与门闩前基线

冻结实验在启动后用`QUuid::createUuid()`生成应用run，不能预先使用Orca Run或客户端run代替。新增不可变`ApplicationRun`，保留原`Context`中的Task/Dispatch/客户端run/session，同时单独绑定应用UUID、原Popen PID/birth/image、持续客户端owner PID/birth、原事件目录和启动记录hash。绑定只能进行一次，后续request会记录两个run身份；本阶段没有修改冻结EXE或实验源码。

`ApplicationJournal`只读本客户端创建器保存的原Popen及该创建器的新事件目录。每次核对同一原句柄/PID/birth/image，以及当前持续客户端owner；原启动记录的owner、kind、skip和60000ms看门狗必须匹配。不能从旧PID或旧目录接管，也不能重新绑定清除失败。`OriginalHandleApi.current_identity()`从当前客户端原伪句柄读取创建时间，不创建临时PowerShell owner。

原NET请求只有修订、代次和A来源，没有clean/走线数。因此新增`baseline`审阅阶段：先对已载板/A来源的真实图像完成指定会话read/ack，明确修订、clean、单走线及A摘要；其应用UUID/精确产品身份必须匹配，ack必须早于目标请求的原触发时钟，随后一次消费。`GateJournal`从该已核验基线取得初始文档字段，不把配置默认值或旧日志伪装成当前GUI观察。产品初始载入和基线捕获的完整现场顺序仍需接入启动器。

## 原事件与唯一release

`tools/async_product_client/events.py`读取完整UTF-8 JSONL，校验非空对象、无重复JSON字段、同UUID/PID、连续序号、无损且严格递增的应用纳秒、线程与唯一启动/停止。已见原字节前缀只能追加，截断/改写或不完整末行保守拒绝；不重试抹平未知状态。

目标`request-N.json`必须保持原字节，核对应用UUID、request、kind、PID、creation FILETIME及精确`Local\\PtRenewAsync-<UUID>-<ID>-release/cancel`名称。只使用原应用已创建的事件，不创建/重置事件，不接受任意事件名称。

事件映射核对唯一门闩请求、NET或铜冻结入口、工作/GUI线程、门闩前A读取与正常接受、冻结A/B/板输入摘要、修订/代次、门闩内唯一document-published，以及原返回/回调淘汰决定。cancel后的discard映射为aborted，不能变为有效竞争。初始字段来自baseline，编辑字段来自原publication，并仍要求门闩图、编辑图和终图真实read/ack；**事件状态不授予GUI通过**。

`sampled_app_ns`明确取原文件最后一条事件的应用时间，不冒称是“应用现在”。外部时限继续使用目标请求触发前的原单调时钟；两个时钟分别核验，不把进程FILETIME与应用纳秒相减。原ready附近60秒看门狗保持，观察到ready、创建图像request或等待下一块都不能重启时钟。

`tools/async_product_client/release.py`默认禁用。只有竞争状态机已记录本次release尝试，且门闩图/编辑图已有同应用、同request的实际read/ack消费证明，才能进入该接口。打开现有release/cancel句柄后核对两者未置位、原Popen/owner与原日志仍有效、文档未变化并且原截止留有5秒余量，再尝试**一次**SetEvent(release)。cancel只读，不设置；传输未知或任何错误不重发。

SetEvent返回只记录“信号已返回”，不伪造应用纳秒。随后在原截止内以每块至多1秒的本地等待读取原日志；必须取得原`gate-released`且未aborted，才给核心返回原应用时间的有效回执。只有信号返回、应用中止、工作返回缺release、超时或句柄清理失败都不能成功。句柄在finally逐个清理，失败锁存、token和120秒截止保持。等待仅处理本地文件/原句柄，不调用桌面状态或续心跳。

## 可信原生窗口与只读UIA

新增`native.py`，默认禁用，构造/导入不加载user32或COM。`ReadOnlyWin32`只读取输入桌面、前景、目标PID可见窗口、原生owner/标题/类/启用状态和物理矩形；DPI采用已有`control_geometry.py`的PER_MONITOR_AWARE_V2临时线程上下文并验证恢复。所有Win32句柄函数明确声明指针宽度，不激活窗口、不发送消息或键鼠。

`ReadOnlyUia`只读调用方提供的冻结包模块，不接收外部JSON冒充结果；核对ControlFromHandle根PID/HWND/标题/类，读取WindowPattern.IsModal、有限深度/数量的dirty模态按钮子树、LegacyIAccessible默认状态以及实际焦点祖先关系。没有Invoke、Close、SetValue或自动选按钮入口。

`ProductNative`将两种来源与原Popen交叉核对。Delete只有焦点确认为同进程、目标子树内的`boardCanvas`/“板图工作区”/Pane时才允许；文本和未知焦点不升级为画布。dirty主窗必须已禁用，模态必须属于精确主HWND、两按钮归属和物理rect均明确，且“取消”为唯一默认按钮。主窗与模态同Qt类时仍由HWND/owner区分。采集结束前再次核对所有窗口、焦点、按钮、物理矩形、前景与桌面，捕获“检查其他窗时前一个窗已变化”的路径。

这些接口尚未经过本阶段真实产品native/UIA调用。Qt实际UIA树、Pane类型、自动化ID和默认按钮可读性不能从源码或假API测试推断通过；未知则拒绝，不能放宽成只按Qt类识别。独立且有界的COM探针启动/原Popen等待尚未接入，避免在主客户端留下不可回收的阻塞线程。原生文件框阶段与初始主窗发现也尚未完整实现，不能借主窗输入接口操作文件框。

## 本轮新归档图任务：限定成功

本轮按用户持续且再次明确的必要控制授权，使用[orchestration](C:/Users/rikideng/.pi/agent/skills/orchestration/SKILL.md)与[orca-cli](C:/Users/rikideng/.agents/skills/orca-cli/SKILL.md)，建立独立`Kylineyes/verify-async-image-probe-v3`，基线42d7556。新Run `run_2cca64780fb9`、Task `task_c257068934b4`、Dispatch `ctx_01d8d1a98c97`，显式Pi `deng/gpt-6.1-sol high --no-mcp --no-extensions`。父在执行前冻结17文件并运行冻结副本6项测试，向用户说明02:21 UTC+8起、预计5～10分钟、只读两张归档副本且无产品/桌面操作。

原session `01a188e4-680f-74d8-a046-d5e506d19612`的18条实际assistant身份均经父核对为指定模型/high；UTF-8 preflight通过17文件完整摘要。worker严格执行request1→一次实际内置read成功image→ack1→request2→一次实际read成功image→ack2。两图hash保持`cfc5b6d1...`及`d19a4958...`，父核对原会话各次确切read call/result ID、image字节hash及ack所引用的原JSONL完整前缀hash，未冒称父实际读图。

| 本次观察区间 | 耗时 |
| --- | ---: |
| 图一request→ack | 13.7759396秒 |
| 图二request→ack | 16.1056135秒 |
| request1→ack2完整区间 | 36.22394秒 |

本次T1小于20秒、两图完整区间小于50秒，说明**当前工具链取得一次实际归档图read证据和时序样本**。区间包含真实模型往返与工具调度，不是纯推理耗时；没有产品Snapshot、选择/Delete、应用发布或release成本，不是未来上界。第二张仍为历史取消后的事后图，不能称作门闩内编辑或新产品GUI通过。

唯一done `msg_825a2c42c45d`为succeeded，父在独立审计原会话、17冻结文件和32项worker证据后，仅按归档测量范围验收，ack `delivery_b349544d3d5a`。worker-release为external_terminal retained、processAction=none；不声称Pi进程退出，不复用已结算Task。此前编码预检failed及更早failed/abandoned任务保持原结论，不被本次成功改写。

## 验证、冻结与后续

新增门闩及窗口测试使用假事件/Popen/原生API/UIA/时钟及合成图片会话，验证两类完整假链、错run/PID/birth/owner、日志和清单改写、原A接受、入口/线程/代次、cancel伪通过、SetEvent单独返回无效、未知释放/超时/句柄清理，以及焦点/同类多窗/默认取消/窗口变化/DPI恢复等路径。actual read归档任务属于独立证据，不把测试数或协议settled当产品通过。

本阶段新增`test_async_product_gate.py` **16项**与`test_async_product_native.py` **11项**，合计**27项新增测试通过**；仓库Python全集**281项通过，24.505秒**，见[最终测试日志](../.local-analysis/async-product-gate-binding/tests-all-final.log)。此前10组旧参考及22/23/22部署按相同源码摘要口径全部不变，见[只读基线](../.local-analysis/async-product-gate-binding/readonly-before.json)。另保存前两阶段目录与旧编码失败worker原件的完整摘要用于冻结后复核；本轮新图片任务32文件原件已独立归档审计，不写回worker。

当前阻断项：独立有界COM探针及初始主窗发现、原生文件框明确阶段、产品/服务/客户端/监督器及已发现子孙的完整原Popen启动与退出见证链接入，以及包含实际产品截图/编辑/release和正常退出的冻结总预算设计。本次档案样本不能自行将ready_for_live改为true；先补这些接口并离线验证、冻结全模块/包/输入，再给NET、铜分别最多一次的新任务材料与具体时间范围。原20/50/55/60秒门槛、35/5/40秒正常退出余量与首次拒绝120秒零桌面请求保持，不重连、不重置旧预算。
