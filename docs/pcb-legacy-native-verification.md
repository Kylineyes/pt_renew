# 受限另存为的原软件与原生流程后续核验

2026-10-31，本轮结论为 **failed：兼容性验收未完成**。当前产品核心成功生成合成及真实样例的新移动／删除输出，独立字节比较通过；原 AUTOTRAX 已显示合成源板及主菜单，但在进入 Information 前公共控制门返回 `user`，依约停止。未取得 Work File Name、Status 计数、新输出重开或独立产品原生另存流程，不能宣称输出兼容通过，也没有证据判定写出格式不兼容。

执行身份为 Task `task_19b0255b324e`、Dispatch `ctx_bc31cce1afcb`，独立分支 `verify/pcb-legacy-native-worker`，起点 `82ef90e028bb56e0466761f7a40be85c120e98e4`。环境及原 JSONL 的会话、模型变更、推理等级和实际 assistant 记录均核对为 Pi `deng/gpt-6.1-sol high`，session `01a19107-f43e-75fd-9e8c-0925f8c21dac`。本轮只提交本文；未修改产品源码、旧报告、旧冻结、原安装或发布物，不合并、不推送、不创建 tag。

本树忽略证据根目录为 `.local-analysis/pcb-legacy-native/`，下文相对证据路径均以此为根。已完整阅读 AGENTS、另存为交接与两份实现／验收文档、原软件隔离及菜单／文字属性 GUI 报告、公共控制恢复和下一阶段边界，并读取父树的 `CURRENT_AGENT_HANDOFF.md`、`WORKTREE_CLEANUP_NOTICE.md`；未恢复旧任务、失败预算或演练。

## 文件准备与独立字节验证

从只读 `D:/project/pt_renew/pt` 的 99 个文件创建全新 `runtime/pt` 副本，只在新副本去除 `TRAXEDIT.DFT`，保留其余文件。四份源／最终输出加入后运行集合为 102 项；原安装从未挂载。合成源为本轮新建的六条顶层 FT：四条外方框、一条内部水平线及一条内部短竖线；真实源为 `660A.PCB` 的完整副本。

父提供的本轮命令行生成器 `helper-build/pcb-compat-helper.exe`，SHA-256 为 `f7bbf008a19f691115aebea0eae8f16a82128813ba02b36abfab800a36babfd7`，直接链接当前产品核心，实际调用 `LegacyPcbReader`、`BoardEditSession` 和 `LegacyPcbWriter`。每组先从源板移动索引 0 写全新中间文件，再从中间文件删除索引 1 写全新最终文件；四个生成器原始 `Popen.wait()` 均返回 0，stdout、stderr、argv、原句柄及对象身份分别保存于 `helper-*`。

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `samples/SYN0.PCB` | 212 | `a87c265b5e8b53c36e49c0b8677767920fee3d903945e2c43de75b2a6976759c` |
| `samples/SYN1.PCB` | 180 | `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228` |
| `samples/REAL0.PCB` | 6533 | `c2c203680f8d1a6576caae9d9ef0da27c974972ed0fc451afbafec9c18a3ecda` |
| `samples/REAL1.PCB` | 6501 | `59b609172017d1871eb0e29cf1b366acbc6d0de186995dddc6b71529d6b20180` |

独立脚本按源文件的原行和数值词构造预期字节，并要求最终输出逐字节相等，未调用产品写出逻辑作比较。合成首线 `(1500,1800)→(2400,1800)` 平移到 `(1500,2200)→(2400,2200)`，删除 `(1800,1300)→(1800,1600)`，四条外框 FT 原字节保留，走线总数 6→5。真实首线 `(4837,5089)→(4856,5089)` 平移到 `(5237,5089)→(5256,5089)`，删除 `(4837,5095)→(4843,5095)`，走线总数 170→169，168 条未改 FT 及两圆弧、35 填充、一焊盘、两过孔等全部其他字节保持。两组宽度、图层和第七字段均保留。

证据为 `generate_outputs.py`、`independent-byte-audit.json`、`helper-processes.json` 和六份源／中间／最终样例。上述是核心写出与独立字节证据，不代替原 AUTOTRAX 重开。

## 现场与实际读图

协调者审阅 `live-plan.json`、`desktop_session.py`、输入摘要后，明确预告 **2026-10-31 16:29（UTC+8）起、最多 25 分钟**，允许开始；原回执为 `authorization-receipt.json`。计划 SHA-256 为 `40eb4a67d9f07fb47f4ca20fcaefe29ba95c67731a889c138255f852d2d0752c`。现场只启动一个未改公共 Windows-MCP `serve` stdio 连接与一个 DOSBox 目标，未热改脚本或重连。

唯一 DOSBox 命令为本机 `dosbox-x/2026.10.01/dosbox-x.exe -conf <本树证据>/SYN0.conf`，cwd 为 `<本树证据>/runtime/pt`。配置仅挂载本轮 `runtime`，执行 `pt SYN0.PCB`，沿用 `opengl`、`vgaonly`、`core=normal`、固定 10000 cycles。DOSBox 映像 SHA-256 为 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832`；配置、argv、stdout／stderr 及程序日志均保留。没有将日志中打开请求作为载入或兼容通过。

以下六张 PNG 均由本 Pi 使用原 `read` 实际打开并判断。`image-read-receipts.json` 索引原会话中的调用 ID、结果记录 ID、时间、成功 image 及解码 SHA；六次成功 image 的字节摘要均与对应原 PNG 相同，完整原会话前缀另存为 `session-evidence-final.jsonl`。

| 图片 | 原 JSONL 结果记录 | 实际可见内容与判断 |
| --- | --- | --- |
| `step-001-baseline-00.png` | `9ce8dee2` | Orca 桌面基线，无原软件业务结果。 |
| `step-002-launch-syn0-post-00.png` | `ee4489aa` | DOSBox 在 Orca 后方，仅部分边缘可见；不能辨识客体启动页，未据此判为黑屏或载入成功。 |
| `step-003-syn0-settled-00.png` | `7e3ebc57` | DOSBox 仍被其他窗口遮挡；结合该次原生归属记录确认本轮 PID 的标题为 PT，尚无完整可读客体画面。未向遮挡它的其他进程发送输入。 |
| `step-004-focus-syn0-post-00.png` | `91bdde08` | 聚焦已确认本轮唯一窗口后，实际显示 AUTOTRAX 1.57 启动页、VGA 640×480 与按键启动提示。 |
| `step-005-dismiss-startup-post-00.png` | `28f5d93e` | 单个 Enter 后显示红色外方框、内部水平线及内部短竖线，与合成源图形布局相符；没有可见工作文件名、状态计数或对象坐标属性。 |
| `step-006-syn0-main-menu-post-00.png` | `1eec762a` | 再单个 Enter 后，原 AUTOTRAX 主菜单实际出现，源板布局仍可见；尚未进入 Information／Status。 |

第 7 步请求原本准备发送 `Shift+I`，但其前置 `ControlStatus` 在 **16:45:38.108806** 返回 `state=user`、`generation=14`、`wait_seconds=1.0532800999935716`，随后脚本锁定停止。**Information 按键未发送**，没有第 7 步 post 图片；本 Pi 对预期图片的一次磁盘 `read` 收到 ENOENT，明确计为失败读图，没有当成成功截图。

拒绝记录为 `step-007-syn0-information-gate-response.json` 和 `stopped-error.json`。到 `quiet-period-ended.json` 的实际间隔为 **120.000573 秒**，期间及之后桌面请求为 0；未发送关闭输入、截图、控制状态或新的原生桌面观察。协调者明确接受该停止和退出未证明范围，禁止恢复现场。

## 进程、原件与冻结后审计

| 进程 | 原始身份与实际结果 |
| --- | --- |
| 公共控制服务 | PID **23712**，创建 FILETIME `134379090239930507`，原 Popen 身份 `2210178199104`、句柄 **472**。16:30:23.996819 创建；关闭 stdio 后原 `wait()` 于 **16:47:39.355155** 返回 **0**，见 `control-created.json`、`control-exit.json`。 |
| 唯一 DOSBox | PID **11096**，创建 FILETIME `134379091157937368`，原 Popen 身份 `2210178406736`、句柄 **612**，窗口 HWND **21301300**。16:31:56.627834 记录创建；**正常退出未证明**，16:47:39.119918 的 `target-exit-unproven.json` 记录仍由原创建者持有 Popen 等待。 |
| 本轮创建者 | runner PID **40336**，见 `runner-started.json`，仍按冻结脚本保留目标 Popen 等待正常退出；runner 自身退出也未证明。未强杀、未通过 PID 消失推断退出，也未将服务退出 0 扩大成全链清理完成。 |

最终只读后审计为 `collect_final.py`、`final-audit.json`：原安装 **99 项完整集合／大小／SHA 与运行前相同**；本轮运行副本 **102 项** 与现场前相同；六份源／中间／最终样例均保持；公共控制包 **77 个 Python 源文件**前后相同。完整清单分别为 `original-before/after.json`、`runtime-before-live.json`、`runtime-after.json`、`samples-after.json`、`control-source-before/after.json`，不提交原软件内容。

本轮候选只使用父新建 `product-candidate-v3`：manifest SHA-256 `d79ce9923630ddd68a57471f2be0cf2f3020db6db88f4521ed3662395090f9e6`，独立产品 `pt-renew.exe` SHA-256 `8730f39af09be8290e278d09ebb186c630e44d988a204237cc5f8bb5395d57df`。前后逐项核对 **57 个源码、18 个二进制／依赖**，与当前父／本树源码及清单一致，见 `product-before/after.json`；**该产品 EXE 本轮没有启动**。父报告 Release 构建及 CTest 12/12 通过，本工作者未重复构建或把该结果视为 GUI 通过，旧 alpha 未用于本轮流程。

## 通过与未完成范围

通过的是本轮隔离准备、当前产品核心生成、独立字节比较、指定模型六图实际读取、AUTOTRAX 合成源板可见布局／主菜单及拒绝后的按约停止与服务正常退出。GUI 目标总体未完成，受限另存为的原软件兼容性仍未验收。

未执行或未取得证据的范围为：Work File Name 和 Information／Status 计数、修改／未改对象的原软件属性、`SYN1.PCB` 新输出重开、真实源／输出对照，以及独立产品打开→选择→移动／删除→Windows 原生另存框→新目标→重开、取消、已有目标和关闭保护。未修改原字形 `runtime_verified=false`、异步竞争 `ready_for_live=false`、旧次数／时限或其他历史结论。

后续应在新的明确现场上下文中先处理本轮尚未证明退出的目标归属，再安排剩余最小源／输出对照；不得直接恢复本次控制连接、已停止脚本或旧 Dispatch，也不得由本轮源板显示或 Qt 自重开推定原程序输出兼容。
