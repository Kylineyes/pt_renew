# 原生NET文件框与原Popen账本离线接入

2026-10-30，从核对的`dev=origin/dev=9b13adaec08a936aff4bd2c1f3bc5e8cea9d7218`建立`feat/async-product-file-dialog`。继续[有界UIA探针与主窗发现](async-product-bounded-probe.md)，补独立原生NET文件框阶段、受限一次性Type凭据，以及接入产品/探针创建器的原Popen账本。生产模块默认禁用，**ready_for_live=false、max_product_launches=0**；本阶段没有产品启动、实际COM/UIA、控制服务、桌面请求或新图片任务。

## 原生文件框的独立状态机

`file_dialog.py`的`NetFileDialog`不借用主窗的普通文本输入接口。它接收已经由产品命令打开的文件框，按当前原Popen的PID/birth/image、主HWND和精确owner关系验证：主窗精确标题保持且已禁用，文件框为唯一owned窗口、类`#32770`、标题“只读载入 Protel 网表”、启用、模态且为当前稳定前景。出现其他窗口、错误owner或未知状态立即拒绝，不聚焦、不试探Enter或Alt+F4。

主窗和文件框都必须来自可信`ProductNative`采集，并在每一步再次核对原身份和物理矩形。只读UIA桥接新增对该精确类/标题的有限子树读取：文件名Edit automation ID `1148`、打开按钮 `1`、取消按钮 `2`，交叉核对PID、后代关系、启用/可见状态及物理rect；文件名ValuePattern只读取得Value/IsReadOnly，绝不通过SetValue或Invoke操作。打开按钮冻结名称“打开(O)”、取消为“取消”。

以上控件ID、按钮名称及原生owner关系是当前严格候选协议，**未在真实Qt/Windows现场确认**。不同系统语言、Qt原生框封装或UIA字段若不同，应先记录并冻结适配，不能放宽到模糊标题、任意Edit/按钮或坐标猜测。文件框控件归属证据不能由调用者提交JSON代替可信探针。

状态顺序为：

1. 当前文件框Snapshot→指定Pi实际read成功image→ack，确认文件框及目标副本。
2. 消费本张ack→仅一次Type输入冻结A/B网表绝对路径，`clear=true`、`press_enter=false`、`caret_position=idle`。
3. 原生前景/归属后验、文件名Value与焦点后验→当前路径图Snapshot→指定Pi实际read→ack。
4. 消费路径图ack，再核对原文件摘要、文件名Value和窗口→按实际图像倍率明确点击打开按钮一次；取消可在初次或路径图read后明确点击，不能靠Enter默认动作。
5. 点击后仍通过普通主窗前景后验。打开仅记`submitted/load_verified=false`，应用后续request、读取成功和A/B接受/丢弃须由原事件链及实际图像另行核对。文件框消失不等于网表载入成功。

冻结路径只允许本轮隔离副本`a.net`或`b.net`，绝对路径、无换行/NUL/引号、摘要必须匹配，每一步重新核对。不打开用户原文件、不接受任意文本或网络路径列表。路径图和初次文件框图仍绑定本轮身份、唯一hash、原request/read回执及外部原截止，不伪造应用门闩时间。

## 普通输入边界与真实触发时钟

`McpProductTransport.__call__`继续拒绝通用Type。唯一专用`file_dialog_type`入口要求进程内的`FileTypePermit`，绑定同一Ledger、当前成功token、冻结NetFileSpec及精确参数，并在调用前消费；旧token、跨客户端、收尾阶段、已消费或摘要改变均拒绝。凭据不是外部可反序列化请求协议，也不是操作系统安全沙箱，调用方仍须按冻结状态机提供可信对象。

原MCP回执仍先保存原序列化结果，再规范化字段；Type必须有冻结参数和严格原文本回执。输入未知、错误回执、后验失败或已经出现新的文件框都锁存原failed ID/token/120秒截止，不重发Type/Click。之后产品退出0不能改写先前输入失败。

明确点击打开按钮前保存`trigger_mono_ns`，供门闩客户端从实际目标请求触发之前计算20/50/55/60秒门槛。这个时间不会在观察到gate-ready、写request或读图时重置。文件框读图和填路径发生在目标请求触发之前，但它们仍消耗原600/900秒总预算；不能通过独立阶段或新探针重新起算总运行时间。

当前进入文件框的产品命令/菜单按钮、初始A和后续B分别如何串接、打开后主窗UIA焦点的真实兼容性及全动作成本尚待启动器集成。接口存在不代表可直接运行产品竞争。

## 同客户端原Popen账本

`lifecycle.py`的`ProcessRegistry`保存创建者返回的原Popen对象，在任何身份回调之前记录；身份未知也不丢引用。核对原PID/birth/image/创建句柄后标识，再仅以同对象的原returncode记录退出，不按PID重开句柄代替。重复对象、键、身份回写、改变PID或冲突退出码拒绝。

`OwnedProductProcess`与`BoundedUiaProbe`新增可选同账本接入。产品创建后立即登记，身份读取后补原身份；探针创建后登记为产品子角色，正常退出或失败后的本地reap均写回原对象退出证据。创建后身份失败、非0退出、超时unknown都阻断完整生命周期结论。

账本区分`lifecycle_complete`与`action_succeeded`。所有必需角色正常退出0且无身份/子孙缺口才可完成生命周期；原动作若已有failed ID，即使后来各进程exit0，动作仍失败且token/冷却截止不改。GUI字段始终false，未知短命子孙覆盖始终不宣称通过。

默认必需角色为product/service/client/supervisor。当前只接入产品和探针；客户端自身、外层监督器及MCP服务的创建所有者跨进程原句柄回执尚未集成，缺失角色会明确列出，不能把局部账本当全链完成。发现没有原Popen的子孙只能登记不可消除的gap，不能用进程后来不存在、迟到查询句柄或重新登记PID修补。封存后的账本禁止新增身份，不删除原缺口。

## 验证与下一步

本阶段测试仅使用假文件框/native/UIA、合成图像与Pi会话、假MCP/Popen/API和时钟，无真实产品或输入钩子。覆盖实际read严格顺序、冻结路径唯一输入/后验、明确打开/取消、错图/坐标/身份/owner/Value/焦点、未知输入及不重试、通用Type仍被拒绝、UIA只读ValuePattern，以及账本缺角色/非0/身份未知/已发现子孙gap、迟到退出不覆盖失败和产品/探针创建器同对象接入。

本阶段新增`tests/test_async_product_file_dialog.py` **16项测试通过**（12项文件框/专用输入/创建器接入、4项账本契约），仓库Python全集**311项通过，27.607秒**，见[最终日志](../.local-analysis/async-product-file-dialog/tests-all-final.log)。全程假API验证，无新增实际读图或产品GUI验收。

下一步先接通初始A/B打开命令与上述阶段，完成服务/客户端/监督器的跨进程原Popen见证交换及全部已发现子孙审计，再形成可审阅的完整启动/失败收尾顺序和冻结预算。原归档双图36.22394秒仍只是不变观察样本，不含产品Snapshot、冷探针、输入或release成本，不自动授予live-ready。必要控制授权持续，现场前仍先完成代码/测试/冻结材料并说明实际开始时间、预计时长与范围；旧Task/Dispatch/批准和failed/abandoned证据保持只读，不执行旧演练或追加组追逐ready。
