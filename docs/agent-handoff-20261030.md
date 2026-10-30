# PT Renew 新代理交接：2026-10-30

本次用户要求整理进度与计划、交由新代理继续，因此停止扩展实现，不再启动产品、控制服务、探针或图片任务。**产品方案仍ready_for_live=false。**

## 接手入口与版本

先完整读取：

1. [AGENTS.md](../AGENTS.md)。
2. 本文件。
3. [SESSION_HANDOFF.md](../SESSION_HANDOFF.md)及[下一阶段计划](control-next-stage.md)：顶部为最新状态，后续各段是历史，旧数字不能覆盖最新结论。
4. [产品客户端约束](async-product-client-contract.md)及[最新批量观察报告](async-product-batch-observation.md)。
5. 本机`.local-analysis/CURRENT_AGENT_HANDOFF.md`、`.local-analysis/async-product-batch-observation/NEXT_AGENT_BRIEF.md`：完整本机路径、证据与已结算任务身份。

实现基线为`dev=origin/dev=53922ab39dda1a0c07739f557ea9d5cbc5dd0c01`，已推送、工作区干净。最后实现分支`feat/async-product-batch-observation`，提交`68b5bdef6c38a711786aadb0841d75e9fd2351ec`，no-ff合dev。此次交接文档从该基线独立分支`docs/agent-handoff-20261030`提交合并；最终Git状态另存本机`.local-analysis/agent-handoff-20261030/final-git-state.json`。

`main`仍`3e13f69528cfc033718ef8352b8d3fb7bce915bd`，代理未操作main。后续从最新dev建立新开发分支，不在dev/main直接实现，完成验证后no-ff合dev并推送。原`.local-analysis/NEXT_AGENT_BRIEF.md`是2026-10-29旧接手记录，保持只读，其f81576f不是当前HEAD；不要照旧计划重做已完成模块。

## 产品与验收边界

| 对象 | 当前结果 | 尚未通过/实现 |
| --- | --- | --- |
| 稳定0.10.0 | PCB/LIB/NET只读、选择/定位/测量/捕捉、引脚映射、受限铜分析 | 完整DRC、生产输出 |
| 固定0.11.0候选 | 单条自由Track整数mil内存移动/删除、Undo/Redo和保护，已有部分GUI证据 | 整体验收仍未过；无保存/另存为、新增图元、元件放置/移动、布线 |
| 独立异步实验 | 历史NET/铜正向对照有效；冻结实验默认OFF | 完整竞争仍未通过；旧两竞争保持aborted，不能用cancel后discard补通过 |
| 原字形 | 独立研究结果保持 | runtime_verified=false |
| 控制工具 | 历史完整关闭单组限定succeeded，原输入后验/资源/健康/已知退出链证据保持 | 未知短命子孙、长期稳定与性能倍率未证明 |

本会话完成的是离线控制客户端及证据关口，未发布新产品版本，未把实验整体合入稳定产品。产品启动和桌面请求均0；真实Qt/UIA/COM适配及完整产品时限仍未现场验证。

## 已完成实现

主目录`tools/async_product_client/`均为可注入API、默认禁用的标准库模块：

| 文件 | 作用 |
| --- | --- |
| `core.py`、`review.py`、`store.py` | Task/Dispatch/客户端run/session/应用UUID身份、原时限与失败账本；唯一Snapshot/request/read/ack及不可复用消费；绑定原Pi成功image记录 |
| `product.py`、`process.py`、`close.py` | 原Popen创建和原句柄核验、精确Qt主HWND/dirty模态、一次Alt+F4及read后明确放弃、原Popen退出与退役 |
| `events.py`、`release.py`、`race.py` | 原JSONL/request清单到GateState、基线/原A接受/修订/代次/线程/淘汰；唯一SetEvent后等待原gate-released才确认有效release |
| `native.py`、`batch.py` | 同次完整原生/UIA观察的双轮核验，单个子探针承载；父原Popen与子查询身份句柄分别证明，不混淆退出来源 |
| `probe.py`、`probe_worker.py`、`discovery.py` | 受限STA/DPI只读子探针、原Popen有界等待/协作停止/本地reap、一次精确主窗发现 |
| `file_dialog.py`、`commands.py` | 可见NET/铜按钮read后单次Click；原生文件框read→唯一冻结路径Type→Value/焦点后验/read→明确打开/取消 |
| `session.py`、`budget.py` | 同一原身份/时钟下的NET、铜完整显式会话和实际调用计数 |
| `lifecycle.py`、`witness.py` | 创建时保存的原Popen账本；跨创建者报告递归审计与根原Popen退出证明 |

辅助工具为`tools/probe_async_images.py`（只读归档图顺序测量）、`tools/freeze_async_product.py`（新离线冻结，无批准/启动入口）、`tools/audit_async_race.py`（纯事件审计，始终不授予GUI通过）。

已经修正的关键细节：冻结实验主窗所有业务标题末尾必须有`【独立异步实验构建】`；原`--netlist`可在载板后异步载入冻结A，B仍需独立文件框。打开前保存目标原触发时钟，应用UUID由Qt启动后生成，不能预先等同客户端run或Orca Run。SetEvent成功不是有效释放，必须取得原应用gate-released；辅助observed=true不是实际read证据。

## 最新测试与冻结

- 仓库Python全集339项通过，34.214秒；日志`.local-analysis/async-product-batch-observation/tests-all-final-v2.log`。
- 最新新增批量观察测试13项，不与各历史阶段测试数量重复相加。
- 最终152文件候选，独立145项通过，18.709秒；日志同目录`tests-frozen-final.log`。
- 冻结路径`.local-analysis/async-product-batch-observation/frozen-final/candidate/`；manifest SHA-256为`3c1a20112bbfd6d5adfa26f8176ea88673b9f89cf3c729851d9a9df9a9ba8287`。
- `final-verification.json`核对候选、源码、新副本3、原10组参考（实验22/固定23/稳定22、旧对照/竞争/输入、最新控制与归档、实验src/tests）及前6阶段证据和v2/v3 worker原件，摘要均保持。

以上是假API/Popen/native/UIA/事件/时钟和合成图片会话的离线验证；不等于产品GUI、真实COM或完整现场链通过。无变化C++产品没有重建，也没有重复产品CTest全矩阵。

测试限制必须保留：最新首次全回归有新增worker单测模块环境错误，已隔离测试环境；既有runner CLI还出现过两次子链未通过，后续两个新证据目录的独立诊断均exit0、最终339全过，但原失败原因尚未定位，未改控制源码或跳过测试。原日志及`runner-diagnostic/`、`runner-diagnostic-exact/`保留，不能改写为从未失败或长期稳定。

## 调用数量已解决，实际时间仍阻断

| 指标 | NET | 铜 |
| --- | ---: | ---: |
| 旧流程冷探针数 | 106 | 54 |
| 当前完整整窗观察/子进程数 | 30 | 21 |
| 加一次初始主窗发现 | 31 | 22 |
| T1门闩图整窗观察 | 2 | 2 |
| 门闩图至编辑图整窗观察 | 8 | 8 |

原32次上限不变；单窗与批量共享计数/原总截止，NET只余1次不能用于自动重试。当前精简路径若仍用旧逐窗适配，`budget.py`的`probe_queries`为NET84/铜48；真正批量含发现应看`batch_with_main_discovery_queries`的31/22，不要混读。

T1两次5秒配置等待合计10秒，至编辑图8次合计40秒，尚未包括解释器/模块/包摘要、真实Snapshot、指定模型read/ack、输入、release、落盘及调度。Snapshot当前35秒配置上限不能保证严格20秒T1。配置上限相加不是实际耗时或未来数学上界，不能因为调用次数合格就将ready_for_live改为true。

原门槛保持：触发前原单调时钟起算T1<20秒、T2<50秒、55秒前留5秒应用余量开始唯一release、原60秒内释放；35/5/40秒正常退出余量及600/900秒总预算不扩大、不重置。

## 下一代理执行顺序

1. **优先接阶段剩余时限。** 从最新dev新分支，对探针/工具调用实行原阶段绝对deadline及剩余时间收紧；把调用前hash/源码检查、实际调用、回执校验和持久化都计入。保留批量观察、输入post_native、read/ack、DPI/owner/焦点及唯一机会，假时钟测试覆盖慢预检、慢落盘、未知调用、跨T1/T2/55/60秒、失败120秒及原总预算不变。
2. **接生产启动器和原Popen报告链。** 当前ProductSession从已创建/发现的产品接续，CreatorRelay有协议/假链，但真实监督器→客户端→MCP服务/产品/探针的原创建对象、报告发布交换、服务正常退出、客户端自身由上层见证、全部已发现子孙仍需实际构造和冻结。报告JSON或后来打开的查询句柄不能替代创建时保存的原Popen。
3. **补所有阶段失败正常收尾。** 门闩前初始化异常、文件框取消、主窗尚未绑定、探针unknown等路径尚无完整统一收尾；不能只靠门闩绑定后的ProductClose宣称任何阶段都能正常exit0。
4. **再安排必要现场。** 代码、离线测试、全模块/包/EXE/输入冻结、时限与正常收尾材料可审阅后，说明实际开始时间、预计时长与桌面/进程范围。先按具体兼容性任务核对真实Qt/UIA/文件框和冷成本，再决定NET/铜各最多一次新竞争；不先启动短握手进程等待批准，不续投旧任务，不额外组/连接追逐ready。

探针关键限制：父端等待有界不等于在途COM已停止。父失败stop-requested阻止后续检查点查询，卡住的原调用可能不返回；保留原Popen/unknown，不强杀、不重试。迟到exit0只补生命周期，不采纳迟到结果、不清失败。这是现场收尾的真实限制。

## 已结算图片任务，仅引用不恢复

最新归档v3：Run`run_2cca64780fb9` / Task`task_c257068934b4` / Dispatch`ctx_01d8d1a98c97`，限定succeeded，唯一done`msg_825a2c42c45d`父验收ack。实际Pi`deng/gpt-6.1-sol high` session`01a188e4-680f-74d8-a046-d5e506d19612`，18条assistant、17冻结文件、两次实际read成功image/hash/原会话前缀及32文件worker证据经父审计。

图一request→ack13.7759396秒、图二16.1056135秒、完整36.22394秒。仅归档观察样本，不含产品动作、冷探针或收尾，不是未来上界；第二图是历史cancel后事后图，不作门闩内GUI。父仅审计未显示图。原件`../verify-async-image-probe-v3/.local-analysis/async-image-probe-v3/`，父归档及审计在主`.local-analysis/async-product-gate-binding/`。不盲重跑追更快结果。

v2编码预检Task`task_70c8976c2e7e`/Dispatch`ctx_1e46f88cbaf6`为failed、read0；更早`task_75f8102028b0`/`ctx_1bed19e5ff05`为failed/abandoned、无worker_done，全部原结论不改。外部Pi终端保留/processAction=none不等于活控制服务，不借用旧身份或句柄。

## 授权、环境与保护

用户多次明确“继续推进，允许控制电脑”，必要授权持续，不重复索权；实际控制前仍先完成具体可审阅材料并说明时间/范围。截图/GUI子代理统一Pi`deng/gpt-6.1-sol high`，纯逆向Pi`glm-5.3 high`，核对实际环境/session/原工具回执，模型不可用不擅自替换。

首次真实拒绝完整120秒零新输入/截图/状态/native请求，输入已执行后观察失败只补观察不重发；不清failed/token/截止，不改指示层/门禁/1秒阈值/保持集合/活代码，不强杀。旧critical_segment/rehearsal脚本不得直接执行，不把cancel后的discard记为有效release。

现有控制测试Python为`C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Scripts/python.exe -B -X utf8`；基础Python为`C:/Users/rikideng/scoop/persist/uv/python/versions/cpython-3.14.8-windows-x86_64-none/python.exe`。Qt6.12.0/MSVC/CMake/Ninja已安装，不修全局Pillow/NumPy或新增无关依赖。

稳定22 EXE SHA`726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1`；固定23 SHA`dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8`；实验22 SHA`782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`。不重建覆盖，主build可能旧版。原安装`D:/project/pt_renew/pt`只读，写测必须新副本；`.local-analysis`、图/字体/库/安装/产物/SDK不提交。其他工程终端不在任务范围。
