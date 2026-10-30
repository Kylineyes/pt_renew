# PT Renew 新代理统一交接：2026-10-30 UIA阶段后

2026-10-31最新进展见[UIA对象生命周期修复与新单次核验](uia-object-lifecycle-review.md)：新增清理/最终回执失败收尾修复，仓库428项、独立候选234项通过；全新指定Pi任务单次对象严格COM三次初始化/三次释放、原Popen同PID/exit0及原5秒限定通过。旧failed及其结算不改，Qt/完整冷探针/文件框/全链和产品全动作仍未过，ready_for_live=false。下一步先准备真实Qt/完整冷探针新任务，NET31/铜22、32次和原全部时限保持。以下按历史阶段阅读。

用户要求整理当前进度和接下来计划，由其安排新agent接手。本次只整理交接文档，不继续开发，不创建Task/Dispatch，不启动产品、控制服务、探针、UIA对象、截图或输入。**产品方案仍 `ready_for_live=false`，新离线候选 `max_product_launches=0`。**

## 接手入口与Git

按顺序完整读取：

1. 本机 `.local-analysis/CURRENT_AGENT_HANDOFF.md` 和本文件。
2. [AGENTS.md](../AGENTS.md)。
3. [SESSION_HANDOFF.md](../SESSION_HANDOFF.md)、[下一阶段](control-next-stage.md)、[产品客户端约束](async-product-client-contract.md)：顶部为最新状态，后续是历史，不用旧数字或旧缺口覆盖最新结论。
4. [本轮UIA对象核验与离线修复](async-uia-object-compat.md)、[指定Pi工作者原报告](uia-object-compat-worker.md)，以及 `.local-analysis/async-product-uia-compat/NEXT_AGENT_BRIEF.md`。
5. 按具体工作继续读[探针运行时](async-product-probe-runtime.md)、[实际兼容性驱动](async-product-drivers.md)、[阶段时限与创建者链](async-product-deadlines.md)、[批量观察](async-product-batch-observation.md)。

实现基线已核对：`dev=origin/dev=远端dev=0506464d03cc40f28b2448305bfb46f962b0ff6f`，工作区干净已推送。最后开发分支 `feat/async-product-uia-compat`，实现 `303d148f1ad94dd37bb73dd5ea1105ffbb4b3eb0`，工作者报告cherry-pick为 `a660b2c`，经no-ff合dev。本交接从该实现基线建立独立分支 `docs/agent-handoff-20261030-uia`，交接提交后的最终HEAD见本机 `.local-analysis/agent-handoff-20261030-uia/final-git-state.json`；新agent应先fetch核对最新dev，再建立独立开发分支。

`main`仍 `3e13f69528cfc033718ef8352b8d3fb7bce915bd`，代理未操作main。按AGENTS：独立分支开发、验证后no-ff合dev并推送，main由用户处理，不强推、不跳钩子。

[早期统一交接](agent-handoff-20261030.md)及 `.local-analysis/NEXT_AGENT_BRIEF.md` 分别是afb22b7/f81576f阶段历史，保持只读，不代表最新实现。不要再按旧交接从零重做已完成模块。当前本机入口在本次交接更新，旧入口字节已备份到 `.local-analysis/agent-handoff-20261030-uia/previous-current-agent-handoff.md`；这是入口换代，不是更改任何旧冻结或Task证据。

## 产品状态与当前工作

| 对象 | 已实现或已有证据 | 当前边界 |
| --- | --- | --- |
| 稳定0.10.0及dist | PCB/LIB/NET只读查看、选择/定位/测量/捕捉、引脚映射、受限铜分析 | 非完整DRC或生产输出；没有本轮版本发布 |
| 固定0.11.0候选 | 单自由Track整数mil内存移动/删除、Undo/Redo、dirty与关闭保护；已有部分GUI证据 | 整体验收未过；无保存/另存为、新增图元、元件放置/移动、布线 |
| 独立异步实验 | NET/铜工作线程门闩、原事件日志、历史正向对照 | 完整竞争未过；旧aborted竞争不补通过，实验不替代固定候选 |
| 原字形研究 | 静态/受控研究结果保留 | `runtime_verified=false`，未接入产品运行时 |
| 控制工具 | 历史完整关闭组限定succeeded，原输入/资源/健康/已知退出链证据保持 | 未证明未知短命子孙、长期稳定或性能倍率 |
| 新产品客户端 | 默认禁用的标准库编排、原Popen链、实际read关口、阶段deadline、失败收尾、实际兼容性入口 | 真实服务/Qt/整窗UIA/文件框/全动作时限仍未通过 |

本会话从afb22b7后完成了四个阶段：剩余时限及创建者运行器→实际客户端驱动及基础Python依赖→专用探针依赖/缓存/COM计数→首次真实UIA对象失败取证及离线修复。最近真实执行只创建一个UIA对象进程；没有启动PT产品、真实控制服务，没有桌面查询、截图、键鼠输入或事件订阅。

## 已完成模块，不要重复实现

主目录为 `tools/async_product_client/`，生产入口默认禁用：

| 文件/模块 | 当前作用与验证范围 |
| --- | --- |
| `core/review/store/transport` | 共享Context/token/失败/绝对截止；原MCP/PNG到request/read/ack，绑定指定Pi原JSONL/image/hash；预检、回执和落盘都计时 |
| `product/process/discovery/native/batch` | 产品直接原Popen/句柄身份、精确主HWND及owned模态；主窗发现；同子进程完整双轮UIA/native核对；普通输入post_native保持 |
| `events/release/race/session` | 应用随机UUID、原JSONL/request/代次/修订/线程、唯一release与原gate-released；NET/铜假完整会话串到正常退出 |
| `commands/file_dialog/close/shutdown` | 可见按钮实际read后一次点击；冻结路径Type、后验/read、明确打开/取消；dirty模态read后明确放弃；门闩前/初始化/文件框失败收尾，未知对象保留 |
| `lifecycle/witness/runtime/runtime_worker` | 各创建者直接保存原Popen，身份先核验再放行，逐层报告/摘要及原退出见证；标准库无GUI四身份链已通过 |
| `connection/bootstrap/client_driver/supervisor_driver/launch/driver` | 原服务stdin/stdout MCP连接、同客户端产品装配、完整材料创建前核验、单请求邮箱；兼容性范围拒绝目标B打开/铜触发/Delete/release；真实全链尚未运行 |
| `python_environment/probe_environment/probe_workspace` | 基础Python `-I -S`加载冻结依赖；服务完整6267文件，探针完整156文件comtypes同源；每子进程私有依赖/缓存及只读审计 |
| `probe/probe_worker/com_apartment` | 原5秒/32次子探针、协作stop/保留原对象、分段时钟；模块局部COM计数及平衡；星号导出覆盖修复尚无实际再验 |
| `uia_object`及 `tools/probe_async_uia_object.py`、`tools/run_async_uia_object.py` | 单次对象兼容性入口：本轮批准/Pi前缀/原Popen/父5秒/严格3次COM/失败120秒，实际首组failed |

辅助工具：`tools/freeze_async_product.py`可冻结完整服务和独立探针依赖；`tools/async_product_command.py`只提交一条显式命令；`tools/measure_async_probe_import.py`只做依赖导入测量。工具存在不等于现场通过，旧测量、演练或实际入口不得直接复跑。

## 最新实际Task：failed已结算，禁止恢复

- Orca Run `run_0db66155091d`；Task `task_d3f457a86360`；Dispatch `ctx_d507e4b3f6a7`。
- 指定Pi `deng/gpt-6.1-sol high`，实际session `a8e82af0-6b64-4f65-bcce-51e8afec9ee2`；父核对68条assistant及原模型/推理记录、唯一执行工具回执。
- 工作树 `C:/Users/rikideng/orca/workspaces/pt_renew/verify-uia-object-compat`，分支 `Kylineyes/verify-uia-object-compat`；报告提交 `421c65166352698b3cb64cc7f27901f4f625e662`已整合。
- 批准 `msg_28824f39bc02`，最终材料回复 `msg_859144dcb8be`；唯一worker_done `msg_b1dbe0075c55`为failed，父已审计接收、ack `delivery_2496ec7e5835`。
- worker-release：`external_terminal retained / processAction=none`，reclaimable0。外部闲置Pi终端 `term_ebd28cfb-6b5c-49ee-8869-13f33d108618`不代表活Task或服务，不向旧Dispatch续投或重复worker_done。

实际工具时间为2026-10-30 **18:03:07.5576101～18:05:08.5841699（UTC+8）**。直接创建的基础Python原Popen PID72256/birth134378281877983799/handle200，原退出1。子记录 `object_created=true`，类型为POINTER(IUIAutomation)/POINTER(IUIAutomationTreeWalker)，但计数仅CoInitializeEx两次、CoUninitialize两次，缺原UIA的CoInitialize。

严格两次CoInitializeEx+一次CoInitialize+三次CoUninitialize验收拒绝；`accepted=false`。记录余额0只说明已记录的四条调用平衡，不能说明全部实际COM平衡。子于原父起点后0.7160602秒结束、父0.7516047秒拒绝，这是计数/协议失败，**不是5秒超时**。failed_id=object-finish、token=object-start，首次失败后 **120.0914348秒零新请求**，runner累计120.8486028秒。原对象已经退出1，无需stop标记，没有已知在途UIA子进程。

实际候选、批准和170份worker证据前后摘要一致。完整运行时DLL清单没有记录，不补查桌面/native来完善历史，不声称额外DLL加载为0。父审计只是审计原创建者证据，不冒称父自己持有该子Popen。

## 离线修复及尚未验证之处

定位到原 `uia/core.py` 的 `from .enums import *`将真实ctypes导出，覆盖模块局部代理，导致原UIA的CoInitialize可能漏记。当前源码在core执行完、events类定义创建单例前重新绑定同一代理；假API测试模拟该星号覆盖并确认额外调用可记录。另外使用 `ApartmentStopped(BaseException)`，防止原初始化中的 `except Exception: pass`吞掉停止检查后继续创建。

严格3/3条件没有放宽。修复仅写入新源码及最终离线候选，没有修改实际候选/活进程，没有第二次真实UIA执行。**新修复的实际计数、COM释放及5秒全区间仍待验证**；首次对象曾创建不构成生命周期、Qt或GUI验收通过。

更早的无GUI观察也只在各自边界内成立：虚拟环境 `Scripts/python.exe`原PID与执行PID不同，生产入口已拒绝重定向器；基础Python同PID及完整依赖导入6.8892935秒样本通过。独立comtypes导入两次init/两次uninit、最终2.8671465秒通过，但未创建UIA对象，不能当当前严格三次路径的证明。不要重跑旧组追更快。

## 测试、冻结与证据位置

| 对象 | 文件数/测试 | Manifest SHA-256与用途 |
| --- | --- | --- |
| 本轮实际 `frozen-prelive/` | 6622文件；执行前仓库417项/43.338秒，候选223项/26.669秒 | `2d0775d17331c92cc386cbdd8064f2438ccaae5a6c14a4b8bc4c343483551543`；实际failed原件只读 |
| 本轮修复后 `frozen-final/` | 6623文件；仓库419项/43.476秒，候选225项/26.999秒；本阶段新增总10项 | `8464fceebaa09dd84533f3d38e15de6eba59b63a3e3bbe3afd553975e6d676a7`；未执行真实UIA，非现场批准 |
| 上一探针运行时候选 | 6617文件；仓库409项，候选215项 | `baeae55d1f630cc5d66d8cfba6368c90d24396d6c61331b64e67110349062734`；历史只读 |

本机主证据根为 `C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/async-product-uia-compat/`：

- `final-verification.json`、`post-merge-verification.json`：源码94、候选/输入3/服务6267依赖/探针156/原十组参考及前序阶段全摘要核对。
- `parent-live-audit.json`、`settled-evidence-snapshot.json`：原Pi记录、唯一调用、failed/原退出/120秒、worker170文件。
- `live-materials/`和 `frozen-prelive/`：实际批准/配置和失败冻结，只读，不直接执行。
- `frozen-final/`：修复后离线候选及manifest；`tests-all-fixed.log`和 `tests-frozen-final.log`为最新通过结果。
- worker原件：`../verify-uia-object-compat/.local-analysis/uia-object-compat/`；其中 `execution/`为原父账本/请求/子结果/失败/原退出/最终记录，`sessions/`为原Pi JSONL。

前序证据根依次为 `.local-analysis/async-product-probe-runtime/`、`async-product-drivers/`、`async-product-deadlines/`、`async-product-batch-observation/`及更早各阶段。Git clone不包含这些本机文件。旧runner偶发子链退出失败的原因仍未定位；后来全测通过不能消除旧失败。无变化C++产品未重建，未重跑产品CTest全矩阵。

## 新agent下一步执行顺序

1. **先审阅失败与新修复。** fetch核对最终dev、完整读入口/约束/两个UIA报告和本机审计，确认新冻结字节与源码对应；核对星号覆盖修复时序、停止异常、原COM引用释放/回调和严格计数。针对新疑点做有意义的假API测试，不机械重跑无变化全矩阵，不从旧准备脚本启动。
2. **形成明确的新对象兼容性验证方案。** 本Task已failed并结算，不能恢复/复用其批准、Dispatch、输出根、token、时钟或120秒截止。只有审阅后的新修复、具体新范围和全部材料齐备，才安排单次新上下文核验。不得为追ready自动追加组/连接；仍需原Popen同PID/原退出0、严格3次计数及父5秒含预检/回执/落盘。先说明具体开始时间、预计时长和进程范围，失败按冻结方案收尾。
3. **对象关口通过后再做Qt/完整冷探针兼容性。** 先审阅产品启动到首次主窗发现的时序、前景/owner/精确标题、初始A接受和未绑定/unknown收尾，真实服务初始化/退出与全部原创建者链也要验证。使用同源新输入/EXE/包/依赖及指定Pi实际read，不以对象成功代替Qt控件、双轮整窗、DPI/焦点/文件框兼容。
4. **再验证实际客户端兼容性流程。** 单请求邮箱、基线/按钮实际read、冻结路径Type后验/read、明确取消、clean/dirty正常关闭、产品/探针→服务EOF→客户端/监督器/根原Popen报告链。兼容性驱动当前拒绝B打开/铜门闩/Delete/release，不可绕过或热改；缺功能先在独立分支实现、测试、冻结。
5. **最后重算完整竞争的真实全动作预算。** 正常批量流程含发现NET31/铜22，共享原32次；T1/T2/55/60秒从目标原输入前起算。含冷启动、hash、Snapshot、指定模型read/ack、输入、事件/release、校验和落盘全部计时，不能把旧归档样本或配置上限和当未来界。条件齐备后另拟NET/铜各最多一次新竞争，当前不启动、不放宽上限。

对象核验成功也不自动发布新产品。固定0.11.0极端属性/受控会话结束、新增图元→取消→另存为→未知字段往返、元件/布线/完整DRC/生产输出、字形runtime分别规划。

## 授权、时限及文件保护

用户反复明确“继续推进，允许控制键盘鼠标”，必要控制授权持续，**不重复索权**；现场前仍先完成可审阅代码/测试/冻结/具体范围及收尾顺序，说明实际开始时间、预计时长和桌面/进程范围。不先启动短握手进程等批准。

GUI/截图及其后验统一Pi `deng/gpt-6.1-sol high`，纯逆向Pi `glm-5.3 high`；显式模型、独立分支、证据路径，核对实际环境和原JSONL/工具/read，模型不可用如实报告不擅换。所有旧failed/abandoned/归档任务只读；本轮闲置Pi会话不等于活任务。

首次真实拒绝完整120秒零新输入/截图/状态/native/UIA，输入已经执行而观察失败只补观察不重发。不清failed/token/原截止，不重连/重置，不改指示层/门禁/1秒阈值/保持集合/活代码，不强杀。父有界等待不等在途COM已停止；保留原Popen/unknown/stop，迟到exit0只生命周期。

原5秒探针、32次共享上限、T1<20秒、T2<50秒、55秒前保留5秒开始唯一release、原60秒内完成、35/5/40关闭余量和600/900总预算均不扩大。有效release必须原gate-released，cancel后discard不当竞争通过，read/双轮UIA/普通输入post_native不删。

原安装 `D:/project/pt_renew/pt`及原板/库/用户文件只读；写测使用新副本，保留摘要。`.local-analysis/`、安装/介质、截图/库/字体/SDK/包/构建产物不提交，不强制add。主build可能旧版，不覆盖冻结部署。其他工程和终端不在范围。

测试解释器为 `C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Scripts/python.exe -B -X utf8`；生产直接创建基础Python为 `C:/Users/rikideng/scoop/persist/uv/python/versions/cpython-3.14.8-windows-x86_64-none/python.exe`，配合冻结依赖及 `-I -S -B -X utf8`。不修全局Pillow/NumPy、不新增无关依赖。Qt6.12.0/MSVC环境见 [Qt开发环境](qt-development.md)。

稳定22 EXE SHA `726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1`；固定23 SHA `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8`；实验22 SHA `782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`。完整部署路径/摘要见新本机manifest的references及[早期交接环境表](agent-handoff-20261030.md)。
