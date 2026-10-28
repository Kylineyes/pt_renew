# PT Renew 开发进度与会话交接

更新时间：2026-10-28。先完整读本机`.local-analysis/NEXT_AGENT_BRIEF.md`、[AGENTS.md](AGENTS.md)，再读本文。临时简报保存最终Git提交、进程和会话定位；出现差异以最新直接证据为准。本文已压缩历史追加内容，旧交接原文备份在本机忽略目录`handoff-archive/`。

**稳定产品保持0.10.0。本轮完成控制诊断工具开发和一次限定GUI诊断组验证；固定0.11.0候选及NET／铜层完整竞争验收仍未通过。** 产品代码、既有dist、固定候选、独立实验部署和原始安装未改，main未操作。用户最新要求是开发收尾并整理交接，当前没有后台诊断或自动续验计划。

## 当前产品与候选

| 对象 | 已完成 | 限制与状态 |
| --- | --- | --- |
| 稳定0.10.0 | PCB/LIB/NET只读查看、图层显隐、缩放平移、选择/定位、两点测量与几何端点捕捉、引脚映射、受限铜层分析 | 铜分析不是完整DRC，文字和部分轮廓有近似 |
| 固定0.11.0编辑候选 | 单条自由Track整数mil内存移动、删除、Undo/Redo、dirty/clean、关闭/换图保护、派生结果失效、外部NET保留并重新映射 | 独立分支，整体未通过，不合入稳定发行 |
| 独立异步实验候选 | 默认OFF的`PT_ENABLE_ASYNC_EXPERIMENT`，NET实际读取前和铜算法预算计时前的工作线程门闩、60秒看门狗、请求/线程/修订/回调事件 | 只作实验观察，不能替固定候选记通过 |
| 原字形研究 | 已有静态/受控执行及部分原程序现场证据 | `runtime_verified=false`；未接入Qt渲染、命中或铜分析 |

固定候选没有保存/另存为、新增图元、拖拽、元件移动、布线、完整DRC或生产输出。不要把后续开发计划写成已支持。

| 冻结部署 | EXE SHA-256 |
| --- | --- |
| 主工作区`dist/pt-renew.exe`，22文件 | `726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1` |
| 同级`feat-basic-editing/.local-analysis/basic-editing/release-candidate/pt-renew.exe`，23文件 | `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8` |
| 同级`experiment-async-result-barrier/.local-analysis/async-experiment/release-candidate/pt-renew.exe`，22文件 | `782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac` |

固定源码分支`Kylineyes/feat-basic-editing`在`b0e5ac7761f13690b5310bbc913ab7bfd2691d08`；实验分支`experiment/async-result-barrier`在`c4e3ec5e82bf1a022e523ec8844d0665d7b93234`，实验代码提交`98a4321`。主build可能仍有历史0.11.0构建，不能凭切分支判断EXE版本，固定部署不得重建覆盖。

## 本轮完成的工具开发

开发分支为`fix/control-snapshot-diagnostics`，从已推送dev基线`621afcd10478b0051d840765d26b3020aec93c84`建立，按AGENTS仅将允许范围合入dev并推送。最终合并提交见本机临时简报或`git rev-parse dev origin/dev`；main只由用户合并和推送。

| 文件 | 行为及验证边界 |
| --- | --- |
| `tools/control_diagnostics.py` | 对原控制方法附加只读阶段/原因日志和status诊断字段；保留原拒绝、接管、保持集合、心跳阈值与异常。日志有界、独立线程写入、结束记录丢失数量，不记录用户文字或键值 |
| `tools/run_control_diagnostics.py` | 复制已安装windows-mcp到独立副本并逐文件核验；启动复验任务批准、包清单及启动器摘要，调用原ControlToolGate和原工具 |
| `tools/control_app_refresh.py` | 新隔离进程显式批准才启用，在原App切换前刷新窗口列表；原查找、激活和前景后验保持，不改变原窗口过滤 |
| `tools/control_diagnostic_budget.py` | 目标恢复失败也终止诊断组，保留唯一只读诊断/观察供收尾；不自动重发输入 |
| `tools/control_geometry.py` | 临时线程DPI上下文读取物理桌面矩形并恢复原上下文；读取/恢复未知则拒绝，避免逻辑rect与物理点击坐标混比 |
| `tools/control_indicator_health.py` | 离线修正先取now再读并发heartbeat导致伪负年龄的顺序缺陷；保持原1秒阈值与故障拒绝。**尚未现场加载或部署到原安装** |

相关`tests/test_control_*.py`共27项通过，使用MCP现有解释器及假窗口/假输入API，未安装真实钩子或发送键鼠；不与工作者定向测试重复累加。测试命令及隔离启动方式见[工具说明](docs/control-diagnostics-tools.md)。源码提交包括`8049668`（隔离诊断/缓存/预算）及`4b3d75d`（物理矩形/健康读取顺序）。第三方安装和77文件隔离包原件前后摘要一致，第三方源码/截图/包副本不入Git。

## 四阶段真实诊断结果

所有阶段沿用原Pi会话`01a1739a-82f6-76cf-9ffc-c63e95be56d4`与实际核对的`deng/gpt-6.1-sol high`。每阶段独立分支、证据目录、Task/Dispatch和批准文件，运行后不热改。

| 阶段与报告 | 实际结果 | 收尾 |
| --- | --- | --- |
| [诊断基线](docs/control-snapshot-diagnostics.md) | failed。初始非前景后App not found；恢复错误未联动预算，唯一diagnose被本地断言拦截；Snapshot/Click/Shortcut均0 | 自建窗口及五控制链exit0；125索引、21链接、565行trace dropped0 |
| [缓存/预算修复验证](docs/control-snapshot-fix.md) | failed。缓存刷新已加载仍not found；预算修复允许唯一diagnose实际到达控制/原生检查；Snapshot/诊断输入仍0 | 窗口及五链exit0；143索引、21链接、320行trace dropped0 |
| [兼容窗口验证](docs/control-window-compat.md) | failed。可缩放Tk窗口的UIA/原枚举通过，App恢复和两张Snapshot成功；Click被诊断Guard的DPI混合坐标检查拦截，实际未发送 | 窗口、探针及五链exit0；207索引、23链接、488行trace dropped0 |
| [物理矩形验证](docs/control-physical-geometry.md) | **限定succeeded**。物理rect正确包含按钮点，真实Click及Ctrl+Shift+F8各一次，首图0/0、最终图1/1；未复现本组工具拒绝 | 窗口、探针及五链exit0；223索引、25链接、561行trace dropped0 |

第四阶段通过依据是指定会话和父侧实际读图、原工具调用及物理矩形证据。冻结测试窗逐输入日志存在`record(kind, **fields)`与`kind=`参数重名冲突，GUI先更新成功但输入日志缺行；未捕获stderr堆栈，不得称日志也证明完整逐输入时间线。正常关闭终态日志为1/1，不替代缺失的两条回调记录。旧源码和失败原件保留，未为补日志重跑。

第三阶段成功截图后两次看门狗直接记录`indicator_ok=false、desktop_ok=true`并fail-open；首条指示层心跳年龄约1.078秒。第二条非原子快照的瞬时心跳年龄较小，不能反推探测时的值。第四阶段未记录fail-open，health读取修复未加载；这些样本仍不足以确定历史所有截图拒绝的根因或证明长期可靠性。

所有诊断窗口和控制链均已正常退出，无强制终止或后台输入计划。受阻时精确身份的一次WM_CLOSE只用于自建程序的正常生命周期清理，不作GUI输入/验收通过证据，不适用于产品候选或其他工程进程。已退出运行的failed/token/budget/截止和live-state全部归档，不删除、不恢复旧PID、不重连清门禁。

## 产品验收仍缺什么

固定编辑候选既有常规编辑、严格文本焦点、旧式/现代菜单、10000mil远移/reset、五类只读图元、定向关闭保护、选后文件消失和独立菜单退出已有实际证据，无源码变化不重跑全套A—F。Debug/Release各11/11组CTest已通过。详见[实际编辑验收](docs/basic-editing-actual-edit-acceptance.md)和[剩余验收](docs/basic-editing-remaining-acceptance.md)。

独立实验Debug/Release各12/12组CTest和普通OFF Release相关3组通过，自动竞争只证明offscreen/程序接口场景；[实验设计](docs/async-result-boundaries.md)与[开发报告](docs/async-experiment-development.md)说明判据。此前NET与铜正向对照真实GUI通过；[恢复后四例](docs/async-gui-recovered-120.md)和[自适应续验](docs/async-races-adaptive.md)中竞争均中止，没有完整有效release及门闩内编辑截图。cancel后旧结果discarded不能补作通过，工具小窗口1/1也不替产品竞争通过。

未覆盖还包括900000mil极端位置的直接属性、受控系统会话结束、原字形完整runtime兼容。共享宿主不注销或关机。

## 下一阶段计划与验收标准

1. **先修诊断测试窗日志并补完整取证。** 在新副本修正回调记录参数冲突，显式重定向窗口stderr；复用已通过的可缩放UIA前置与物理矩形检查。仅测试新变化，不改旧报告或重跑产品矩阵。
2. **验证控制健康问题，而非继续碰产品候选。** 为指示层健康探测添加同次采样字段/阶段耗时，区分伪负心跳年龄与真实超过1秒滞后；在新任务和新批准下验证可选读取顺序修复，保留1秒阈值及真正故障拒绝。若记录丢失、图像失败或原因不唯一，结论仍unknown。不得关掉指示层、放宽阈值或切换输入/截图入口绕拒绝。
3. **条件具备后另定有界产品实验范围。** 新Task/Dispatch/批准/证据，冻结候选和输入；引用不变对照。要求同一应用时钟`worker-entered < gate-ready < document-published < gate-released < worker-returned < callback-discarded`，真实GUI编辑、门闩内新修订/几何/dirty/NET来源图和最终图共同成立。失败中止并消费机会，额外运行须另有明确范围；实验通过仍不自动让固定候选通过。
4. **固定候选边界与新产品功能分别安排。** 极端可见性和受控会话测试独立做。新增图元→工具取消→另存为新文件→未知字段保留或明确拒绝→往返及原程序重开另立阶段；元件放置、布线、完整DRC、生产输出、干净Windows部署、性能各自规划。
5. **原字形保持独立研究。** 缩放/完整与简化分派/F/251/252/旋转镜像/笔宽/导入联合状态/保存往返未完成前，继续保留`runtime_verified=false`。

## 用户偏好与执行约束

用户键鼠授权已明确，后续在已授权任务范围内不重复索权。最新要求是**两次拒绝后检查间隔120秒，正常键鼠直接执行，不增加额外ControlStatus预检**；目标归属核对和工具自身拒绝保持。不得把120秒解释成每次正常点击都等120秒。

真实拒绝立停、截止内零输入/截图/ControlStatus/原生桌面请求；到期有界检查并显式恢复，不能把user自动归因为用户正在操作。Snapshot必须有image；动作已执行但后图失败，只补观察，不重发。物理桌面坐标以实际图像原尺寸/倍率及物理rect为准，不能把DPI虚拟化rect直接作输入坐标。GUI关闭后窗口消失的保守锁存由Popen退出见证处理，不恢复已退出目标。

## 生命周期与证据定位

下列四Task均已结算，保留Pi终端不代表任务仍活；禁止复用或重复worker_done：

| Task / Dispatch | 结果 | 工作者报告提交 |
| --- | --- | --- |
| `task_bb8bca1bbfb9` / `ctx_5e11c1301247` | failed | `ef26ac5a223aee8d7bcf6eea0e8b460745f092f7` |
| `task_e389a3ccfaef` / `ctx_1f7869a00c74` | failed | `ac620056b2f43c7430ebc193582958e778bf51be` |
| `task_82d78df9e34c` / `ctx_1dbebe2effc3` | failed | `d44ae4e816b9ad6c7884ee5fe3cd28f2e1faafd1` |
| `task_30f766b66866` / `ctx_900f441db397` | succeeded（限定单组） | `a7110ad5013dd83a5853cf8587ce58c259d4695f` |

本Run为`run_22b5092f9df3`，最后唯一worker_done为`msg_921f9165317c`，父已验收/ack并明确retain原会话。此前固定候选、异步GUI、接管、恢复后四例及自适应续验的全部生命周期也已结算，不续投旧inbox。旧PT Renew PID2020已死亡退役，不再恢复；VK192残留已通过原连接物理释放恢复并正常退出，不再泛化要求用户按键。

| 位置 | 内容 |
| --- | --- |
| 主工作区`.local-analysis/control-snapshot-diagnostics/` | 四阶段任务/批准、77文件包副本、父离线复现、独立交付审计、新链退出见证 |
| 截图工作区`.local-analysis/control-snapshot-diagnostics/` | 基线125项证据 |
| 同工作区`.local-analysis/control-snapshot-fix/` | 修复验收143项证据 |
| 同工作区`.local-analysis/control-window-compat/` | UIA/坐标阶段207项证据与两次看门狗轨迹 |
| 同工作区`.local-analysis/control-physical-geometry/` | 单组223项证据、0/0→1/1图、日志缺口说明及退出证明 |
| 主工作区`.local-analysis/async-race-followup/` | 前轮两竞争中止、部署/安装摘要及591材料审计 |
| 主工作区`.local-analysis/control-investigation/` | 更早VK192内部残留直接只读取证 |

以上材料、截图、原字体/库、反编译数据库和构建产物不入Git，远端clone不带本机证据。原安装`D:/project/pt_renew/pt`只读，运行和写测试必须用新副本。

## 环境和接手步骤

Qt6.12.0 MSVC x64（`C:/Users/rikideng/Qt/6.12.0/msvc2022_64`）、VS2026/MSVC14.51.36231、CMake/Ninja已具备。已有Python/Unicorn/Capstone，不重复安装无关依赖。系统Python的NumPy/Pillow二进制导入存在兼容问题；本轮图像和控制测试使用已有`C:/Users/rikideng/scoop/persist/uv/tools/versions/windows-mcp/Scripts/python.exe -X utf8`，不为此修全局环境。

新会话先读临时简报确认最终Git与终端，再完整读AGENTS和本文；核对`git status`、`dev/origin/dev`、部署摘要和指定模型。保留验收终端`term_d544d0b2-a65f-4b5c-bea9-6257e802bd6d`属于当前Orca runtime，使用前先枚举确认，不能凭旧句柄推断仍存。所有子代理用Pi，纯逆向`glm-5.3 high`、截图/验收`gpt-6.1-sol high`并核对实际记录；同任务沿用会话。当前用户要求的是交接，**不要仅因读到下一阶段计划就自动启动新GUI或新竞争**。
