# PT Renew 新代理交接：2026-10-31 编辑与另存为后

> 后续进展（2026-10-31，用户已明确要求继续）：从 `dev=82ef90e` 开展了新的隔离兼容性验证，详见[原软件与原生文件框后续核验](pcb-legacy-native-verification.md)。Release 构建及 CTest 再次 12/12 组通过；合成板及 `660A.PCB` 副本经当前产品核心移动、删除后，独立字节审计通过。唯一原 AUTOTRAX 场景在 Information 按键前遇到 `ControlStatus=user`，停止后完成 120 秒零桌面请求等待；仅确认启动页、源合成板图及主菜单，未确认工作文件名、计数和新输出兼容性。真实样例重开、独立产品与 Windows 原生文件框未执行，原 DOSBox 正常退出尚未证明，创建者保留原 `Popen` 等待。旧验收、失败及预算边界不变，未新增图元能力或发布。

用户要求本轮开发完成后总结进度和计划，由其安排新agent接手。**本轮完成后停止新功能和新现场任务；不创建新tag、不发布、不操作main。** 当前主线是开发产品编辑／文件往返，不要重新从控制基础设施开始。已发布alpha保持只读历史版本，当前dev已经有新的编辑另存功能。

## 接手顺序

1. 完整读本文件、本机 `.local-analysis/CURRENT_AGENT_HANDOFF.md`、`AGENTS.md`。
2. 读[编辑与受限另存为](pcb-save-as.md)、[本轮实际Qt核验](pcb-save-as-verification.md)，再看 `src/io/LegacyPcbWriter.*`、`src/application/BoardEditSession.*`、`src/ui/MainWindow.*`、`tests/WritingTests.cpp`。
3. 核对Git最终状态和本机 `.local-analysis/pcb-save-as/final-state.json`；fetch后从最新dev建立独立分支。不要在dev/main直接开发，不根据旧构建猜功能。
4. 若下一工作涉及原软件交叉核验，先读原安装保护及相关格式/GUI报告；若涉及后台竞争，再读 `docs/async-result-boundaries.md`、`docs/control-next-stage.md`和UIA交接，旧failed/次数/时限保持。

## 已完成及实现范围

本轮起点 `dev=origin/dev=ef86125ca0084f5aadecca3b84c637417f3c095c`，独立分支 `feat/pcb-save-as`。实现提交 `e92ebc1`，移植此前 `b0e5ac7` 的基础编辑代码并解决版本／关于文案冲突，保留已发布版本标识，不重新发布。最终合并dev及远端SHA见本机最终状态记录。

| 模块 | 当前能力 | 边界 |
| --- | --- | --- |
| PCB/LIB/NET查看 | 图层显隐、选择/属性、检索定位、测量/端点捕捉、封装库、引脚映射、受限铜分析 | 格式覆盖受限，文字/部分轮廓近似，非完整DRC |
| 工作副本编辑 | 可见自由Track整数mil整体移动/删除，菜单与画布快捷键，Undo/Redo | 不编辑元件内部走线、其他图元或库；不新增图元 |
| 另存为新PCB | 文件菜单/Ctrl+Shift+S，原字节打补丁，写前重解析及语义比较，同目录临时文件原子改名 | 必须新文件名，禁止覆盖原件及任何已有目标；Ctrl+S仍禁用 |
| 字节保留 | 空白/混合换行、DOS EOF、非ASCII原字节、附加字段、元件/隐藏标签、内嵌NETDEF原样保留 | 未知记录在载入阶段明确拒绝，不承诺完整格式重建 |
| 历史保存点 | 保存后clean，Undo离开保存点dirty，Redo回保存点clean，分支截断保存点失效 | 几何修订和来源文档不重置，后续仍另存到其他新文件 |
| 故障保护 | 取消/写失败保留文档与历史；路径/设备/NTFS备用流拒绝；文件框期间修订变化拒绝写出 | 网络盘/断电持久性、原程序重开尚未验证 |
| 派生状态 | 编辑时选择/测量/铜结论失效，已载外部NET重映射，旧回调代次/身份保护 | 完整真实后台竞争仍未验收；保存本身不改几何或修订 |

源字节保存在 `BoardDocument::sourceBytes`，不是保存时重读原文件。`LegacyPcbWriter`只允许原FT记录的四坐标整体平移或该自由记录删除，其他结构修改、重排/伪造来源拒绝。第七附加字段未解释但保留，不因局部几何存在就认为电气属性通过。外部NET不写进PCB，原内嵌NETDEF则保留。

另存为成功保留原输入路径、摘要和撤销历史，信息面板另列实际写出路径、字节数与SHA。它当前是保留来源的工作副本流程，不会自动把新文件重绑定为原件；重开新文件则新建正常会话。不要擅自把保存点等同重新载入或清空历史。

## 验证结果与准确范围

Debug/Release配置、编译及**CTest各12/12组通过**。每配置QtTest共310项（含初始化/清理），其中新WritingTests **40项通过**、EditingTests23项；CTest中的两组Python格式研究测试独立保留，不与仓库控制工具428项等旧数字相加。最新完整日志为 `.local-analysis/pcb-save-as/{release,debug}-test.log`，源码最后仅校正原子改名说明注释并增量编译，功能逻辑不变。

首次回归失败为旧“另存为未实现”文案断言及新快捷键测试未等窗口激活，已修正测试并全回归通过；原 `release-test-first.log`、`writing-first.txt` 保留。冻结脚本一次输出日志已存在导致中止，新完整候选另建，不覆盖旧候选或伪称中止冻结通过。

本轮独立审阅与GUI：Run `run_78db3c10928b`，Task `task_7c4df24a2c54`，Dispatch `ctx_0bead893a9d1`；worker分支 `verify/pcb-save-as`，实际Pi `deng/gpt-6.1-sol high`，session `a456c840-52d0-4e61-a62b-df6e1c5c1974`。唯一done `msg_88bef1bb3c7a` 已父验收限定succeeded，ack `delivery_105bbcc94a67`；release为 `external_terminal retained/processAction=none`，reclaimable0。worker报告提交 `68e613b` 已cherry-pick为 `b2d9bc3`，原Pi终端 `term_47d39cb8-9be3-4d58-bda1-cfdd28d417e8`已闲置，不恢复其Task/Dispatch。父预告15:35（UTC+8），实际唯一测试进程 **2026-10-31 15:37:38.239300～15:37:39.426584**，PID21564、birth134379058582402521、原句柄496，创建者原Popen.wait返回0。

本次使用**链接真实产品UI的QtTest驱动**，Windows平台、20个隔离依赖文件、PATH限包/系统；不是offscreen。一次执行五个业务函数，含初始化/清理共7项通过：真实移动框→另存Qt文件框→写新PCB→新主窗重开、取消、失败保留、文件框期间修订变化、临时发布失败。四张PNG均由指定Pi原read成功image且实际看图；父独立核对原JSONL/模型/图片回执，父不冒称自己直接看图或持该Popen。

视觉结果：自由线 `(100,100)→(400,500)` 移动到 `(150,75)→(450,475)`，extra42保持；保存后clean；新窗重开新文件得到相同端点/字段。第三张图中最近保存路径/SHA在滚动区外，不能声称截图看见；写出摘要由结构化记录和文件字节证明。

原合成输入365字节 SHA256 `c633bb29e87b1f774950d3a188e583bd413a430de20c46747fcb5564ea1f2ff7`，新文件361字节 SHA256 `7699d0341a27bd82b526ca38a379b1c0179bac79dce8c9ae0262f78763358b46`。独立字节核验仅四坐标词改变，其余字节相同。冻结源码57文件、二进制/依赖20文件前后不变，manifest SHA256 `c002b01555ff752cce17d1b65e0365dbbf769902b7e7c6da88f56585a5d41aff`；测试EXE SHA256 `aa2ea9f7b6da2a9efd3e91515c4950bacf9e4b2cbef3f718526ca5fb8bab5768`。

**这些不证明**：直接操作独立发行EXE、Windows原生文件框、原AUTOTRAX重开、干净系统兼容、完整NET/铜竞争、900000mil极端现场或系统会话结束。旧失败/归档/批准/时限不改。原字形runtime仍未过。

## 下一步建议

1. **优先补文件写出的独立兼容性证据。** 从当前dev独立分支，用隔离合成副本及受限真实样例检查输出；使用原AUTOTRAX打开新副本，核对移动/删除与未修改对象。原安装/库/用户文件只读，不复用旧Task或准备脚本。原程序不能接受时先定位字段差异，不盲目扩大写出范围。
2. **补独立产品EXE与原生另存框的真实操作。** 验证用户从打开→选线→移动/删除→原生文件框输入新目标→另存→重开、取消/已有目标/关闭保护。不要把本轮QtTest/Qt文件框当原生Windows验收。先备新代码/冻结/具体范围，再由指定Pi执行。
3. **逐步扩展编辑闭环。** 可以选新增自由走线与工具取消，但先设计稳定记录身份、原字节插入位置、Undo/Redo与写出规则；当前writer明确拒绝新增，不应简单放宽校验。元件编辑和布线随后规划。
4. **异步验收按需并行，避免抢占产品主线。** UIA对象关口已限定通过，但真实Qt完整冷探针、原生文件框自动化及客户端正常关闭/原Popen全链仍缺。NET/铜含发现31/22、共享32次、原5秒及20/50/55/60、35/5/40和600/900预算不扩大，ready_for_live=false。若推进该路线先读对应完整交接，不重复实现已有模块。

用户本次只要求完成开发后交接，不安排新tag或发布；下一agent接手前本轮不再启动上述下一阶段任务。

## 本机材料与工程保护

- 父 `.local-analysis/pcb-save-as/`：两个配置构建/测试、失败原日志、`frozen-gui-verified/`、`parent-gui-audit.json`及 `final-state.json`。
- worker `../verify-pcb-save-as/.local-analysis/pcb-save-as/`：身份/静态审阅/Qt改名原源码、原Pi JSONL、`gui/`原Popen/输出/四图/源目标副本/roundtrip及字节审计。原字节路径与摘要见报告，不提交。
- 发布alpha固定tag `v0.11.0-alpha`→`3705e56cf12739fc27691cc8d80fda591bf5b73d`，下载仍只读；旧 `dist` EXE SHA `726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1`未改。本轮不覆盖任何历史部署或已发布资产，不操作main。开发构建沿用原版本标识，不凭`--version`区分新旧功能，应核对源码/EXE摘要；`scripts/package-release.py`属于旧alpha发布准备，当前不直接用它重包新dev冒充原只读发行。
- 新dev已改变主窗标题、菜单和能力；旧异步客户端绑定的冻结EXE/标题策略不自动适用于新dev。后续若用自动化测试新产品，应制定新策略并验证，不能放宽旧白名单或更改旧冻结来适配。
- 历史11工作区已被另一个agent归档，原路径可能是指向 `C:/Users/rikideng/orca/worktree-archives/pt_renew/20261030-cleanup/` 的目录联接，不应把归档副本当活Git工作树；先读 `.local-analysis/WORKTREE_CLEANUP_NOTICE.md`。
- Qt/MSVC/Python环境沿用 `docs/qt-development.md`；不修全局依赖。所有写测使用新副本并留摘要；`.local-analysis`、截图、包、SDK、原安装与用户板库不入Git。

必要键鼠授权持续；新现场先说明具体开始时间、预计时长及窗口/进程范围。子代理统一Pi，截图/GUI验收 `deng/gpt-6.1-sol high`，纯逆向 `glm-5.3 high`，核对实际原JSONL，不擅换模型。工作者闲置终端不代表活Task，完成结算后不恢复旧Dispatch；新任务按范围独立安排。
