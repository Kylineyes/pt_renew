# 产品竞争客户端的实现约束

2026-10-31最新进展见[UIA对象生命周期修复与新单次核验](uia-object-lifecycle-review.md)：新增清理/最终回执失败收尾修复，仓库428项、独立候选234项通过；全新指定Pi任务单次对象严格COM三次初始化/三次释放、原Popen同PID/exit0及原5秒限定通过。旧failed及其结算不改，Qt/完整冷探针/文件框/全链和产品全动作仍未过，ready_for_live=false。下一步先准备真实Qt/完整冷探针新任务，NET31/铜22、32次和原全部时限保持。以下按历史阶段阅读。

最新[真实UIA对象核验](async-uia-object-compat.md)新Task仅一次创建对象，严格3次COM验收因记录2/2拒绝，原exit1、failed/token保持、120.091秒零请求收尾，Task failed已结算。父离线修复星号导出覆盖ctypes代理及停止被宽泛异常吞掉的路径，419项测试通过，没有重跑/改旧候选或把余额0补通过。真实Qt/整窗冷探针/产品全动作未过，ready_for_live=false；NET31/铜22、32次、5秒及原阶段/总截止不扩大。

最新[探针运行时](async-product-probe-runtime.md)将探针依赖固定为同原完整依赖中的156文件comtypes包，私有缓存及只读审计阻止生成字节变化，父独立重算COM原线程/API/HRESULT/余额。一次仅COM导入核验取得原Popen/exit0及平衡，两次初始化/释放，最终落盘2.867147秒；没有UIA对象/桌面查询或产品，真实冷探针/Qt/全动作仍未过。共享32次、NET31/铜22、5秒和20/50/55/60截止不变，`ready_for_live=false`。

最新[实际兼容性驱动与依赖](async-product-drivers.md)补单请求邮箱、实际客户端/监督器及全材料创建前核验；兼容性范围拒绝目标B打开、铜门闩、Delete和release。新原Popen身份实验确认虚拟环境重定向器产生不同执行PID，现要求基础解释器-I -S加完整冻结依赖，不用迟到查询句柄补证。原启动35秒截止已从父预检贯穿子依赖加载，不重计。真实控制服务/Qt/UIA/全动作时限未验证，`ready_for_live=false`、NET31/铜22和32次上限保持。

最新[阶段剩余时限与生产创建者](async-product-deadlines.md)已将原输入前时钟及20/50/55/60秒截止接到schema/哈希预检、工具/探针调用、原回执核验和最终落盘，保留35/5/40退出余量及600/900总预算。实际无GUI四身份原Popen/报告链、原服务stdio连接已验证，生产组件装配及服务入口默认禁用；真实服务/产品/COM/UIA及全动作时限仍未通过。失败收尾覆盖初始化、未绑定、文件框取消及未知探针，未知对象继续持有，迟到exit0不清失败。含发现NET31/铜22、32次上限及 `ready_for_live=false` 保持。

本文件配合[离线预检](async-race-offline-preflight.md)，描述产品客户端的接口和验证要求。最新[批量窗口观察](async-product-batch-observation.md)新增13项、仓库339项Python测试通过。单子进程执行同次完整native/UIA双轮核验，普通post_native和read关口保持；完整NET/铜含发现31/22次，未扩大32次上限。真实冷启动/工具/read总时限及生产原退出链仍缺，ready_for_live=false，产品/COM/桌面请求0。

此前[统一产品会话与创建者见证](async-product-session.md)新增15项、仓库326项Python测试通过。两条完整假会话和跨创建者报告已接通，修正实验主窗后缀；当前NET106/铜54次冷探针超过原32次上限，必须先批量优化观察并重算全动作预算，ready_for_live=false。没有产品/COM/桌面或新GUI证据，真实生产启动/原Popen链仍待接入。

此前[原生NET文件框与原Popen账本](async-product-file-dialog.md)新增16项测试，仓库311项Python测试通过。原生文件框独立read/路径Type/再read/明确选择及产品/探针原Popen账本默认禁用，尚无真实GUI/COM兼容性或完整原退出链；ready_for_live=false。

此前[有界UIA探针与主窗发现](async-product-bounded-probe.md)新增14项测试、仓库295项Python测试通过；父有界等待/协作停止和主HWND发现默认禁用，尚未进行真实Qt UIA/COM现场或产品启动，ready_for_live=false。仍缺原生文件框明确阶段和完整原Popen退出链；冷探针成本尚不能纳入已验证60秒预算。

此前[应用UUID与门闩接入](async-product-gate-binding.md)新增27项测试、仓库281项Python测试通过。独立应用UUID、原事件/release及native/UIA窄适配默认禁用；新归档任务两图实际read/ack取得36.22394秒完整观察区间，但没有产品动作/收尾或未来时限保证，ready_for_live=false。仍缺有界COM探针、初始主窗/文件框阶段及完整原Popen链。

以下保留前阶段范围：此前[原始回执与原Popen适配](async-product-evidence-adapters.md)新增20项测试、仓库254项Python测试通过；原MCP/region与原句柄窄适配默认禁用，仍缺native/UIA/文件框及完整全链接入。新指定模型图片任务在编码预检失败后已failed结算，实际read/ack0，时序未取得，ready_for_live=false。

以下保留前阶段实现状态：2026-10-30已实现[默认禁用的离线API核心与状态机](async-product-client-offline.md)，新增30项测试及仓库234项Python测试通过；尚无冻结现场适配器、实际模型新上下文时序或产品现场批准，ready_for_live=false。冻结实验、60秒门闩及真实GUI判据保持，不复用诊断Tk窗关闭接口。

一次产品运行必须只有一个创建所有者。新客户端启动冻结实验EXE并保存原Popen及创建时间，应用门闩owner指向持续存活的该客户端或已冻结的持有者；不使用短命PowerShell的PID。启动记录包含实验EXE/完整22文件、输入、副本路径、环境清理结果、原Popen PID和句柄、原生主HWND/类/实际标题。主标题随dirty/文件名变化，必须验证已冻结的允许状态及同一精确HWND，不允许任意前缀模糊匹配替代进程归属。

所有原native/工具路径沿用原120秒拒绝截止，普通输入仍执行目标前景后验。原生文件框、产品主窗和dirty模态是不同阶段，分别核验同一进程birth/image、窗口关系与当前输入归属。主窗和模态可能共用Qt类`Qt6120QWindowIcon`，不能仅按类计数“唯一主窗”；对话框须验证owner/主窗关系和精确“放弃工作副本更改？”标题。取消为默认按钮，不能预排Enter、Alt+F4或假定弹框消失即产品退出。

门闩内设计为明确的应用请求及观察状态：

| 状态 | 可接受的下一步 | 必须拒绝 |
| --- | --- | --- |
| 冻结/未启动 | 新副本/原Popen启动、组前精确身份与A来源核对 | 复用旧目录/批准/任务/时钟 |
| 目标请求已进入gate-ready | 当前门闩图Snapshot和成功image回执、同一请求的实际read确认 | 无图、旧图hash、模型/session不符、门闩已aborted/returned |
| 门闩图实际read完成 | 当前图物理坐标选择一次、真实Delete一次、编辑图Snapshot | 未read先点、重发Delete、应用内部编辑接口 |
| 编辑图实际read完成 | 新修订/dirty/零走线/A来源及同应用document-published核对，再唯一release | 先release后read、仅日志断言、以cancel替release |
| 有效release/工作返回/原回调discarded | 当前状态终图/NET来源/几何/旧报告未恢复核对 | 事后图补门闩内缺图、不同请求拼链 |
| 实验已结算/正常收尾 | Alt+F4一次，若dirty则实际读放弃框再一次明确点击，等待原Popen退出 | 未读模态先输入、消失窗口前景后验、仅PID不存在替退出码 |
| 任一失败/未知 | 保留失败ID/token/原截止，120秒零桌面请求；仅本地cancel/原owner失效或看门狗按实验aborted处理 | 自动恢复/新连接/重复输入/清状态/热改/强杀 |

GUI和本地release之间必须有新request/ack关联：request保存本轮Task/Dispatch、run/request ID、PID/birth/主HWND、图hash、工具起止/实际尺寸倍率、应用门闩原deadline；ack必须能追溯指定Pi实际read的成功image回执及图像内容判断。辅助文件里`observed=true`不独立构成read证据。ack消费即不可重用，release尝试消费机会，传输未知仍不重发；release前重新只读检查门闩未结束且剩余时限足够，不能用额外预检拖延到原截止之外。

所有应用顺序由同一应用纳秒时钟判定；操作工具/实际read墙钟只给区间，须核对不矛盾，不能把Windows进程创建FILETIME与QElapsedTimer直接比较。60秒看门狗从应用gate-ready附近起算；开始request的外部时钟不能重置门闩时钟。本地门闩wait默认每块不超过1秒，自动aborted只用于防止后台遗留，不构成有效release。

正常退出需独立窄命令实现于新产品模块：调用尝试、已返回、未知和未发送分开记录。关闭前核对绑定原Popen/精确主窗，Alt+F4最多一次；clean时以有界原Popen.wait=0证明，dirty时根据冻结模态关系核验及真实读图后才点击一次“放弃更改”。点击导致正常进程退出时走专用Popen等待后退役，不再要求已消失目标前景；普通Click/Shortcut后验保持。任何输入错误都不得因后来exit0重写为成功，retire只能证明生命周期结束。产品关闭模块没有实现/离线状态机测试/明确新批准前不能用于现场。

验收前离线测试必须包括错误PID/birth/image/HWND/owner、主模态同类多窗、普通文本焦点保护、乱序/重复ID/忙/排队、旧token/冷却/过期、缺图或错误图hash、read缺image、错session、门闩提前返回/取消/超时、release未知、工具错误、dirty取消/放弃、原Popen超时/非0、错误后退出及所有路径的输入计数/失败截止不变。测试使用假API、假Popen和假时钟，不启动真实输入钩子。已有控制149项和本阶段审计10项保持其独立范围，不凭测试数量替代产品验收。

实现先在最新dev独立分支，提交可审阅代码/测试/模块集合与新冻结方案；随后指定Pi `gpt-6.1-sol high`核验实际模型/JSONL，准备新Task/Dispatch/证据和时间范围后才做必要现场。每类NET/铜只给一次竞争机会，不因失败增加组或新连接追逐ready；没有合格读图时限设计时保持ready_for_live=false。固定0.11.0、异步实验及稳定发布的证明边界分开，实验代码不能整体合入稳定产品。
