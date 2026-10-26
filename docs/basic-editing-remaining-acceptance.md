# 0.11.0 固定候选剩余验收

本轮已补齐严格文本焦点、旧式菜单与编辑历史、可视远移复位、五类只读图元、定向关闭/换图取消、选后文件消失读取失败及独立进程菜单退出的现场证据。NET和铜分析迟到竞态未取得完整时间线，系统会话结束保护仍待受控环境；因此不作0.11.0总体验收或发布放行结论。稳定产品保持0.10.0，上一轮Task的failed结论不变。

## 对象与证据

- Task：`task_d780e8e2eaad`；Dispatch：`ctx_eff89720518e`；Run：`run_361a6ad63310`。
- 工作区：`C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol`；分支：`verify/basic-editing-remaining`，从fetch后的`origin/dev`提交`9b8f1363680009974a85d7b0d09ac9727a9e2d2e`建立。
- 实际Pi会话：`01a1739a-82f6-76cf-9ffc-c63e95be56d4`，环境、会话JSONL最后模型/推理记录及assistant记录均为`deng/gpt-6.1-sol high`。同会话压缩后再核对，未换模型或新建Task。
- 固定候选：`b0e5ac7761f13690b5310bbc913ab7bfd2691d08`；EXE SHA-256：`dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8`。
- 证据根目录：`../.local-analysis/basic-editing-remaining-acceptance/`；下文现场图片均相对其`migration-01/`，实际截图分辨率3840×2160、返回1920×1080、比例2。

只提交本报告；截图、合成输入、工具及日志留在忽略目录。产品源码、候选、发布包和第三方控制包未修改，未合并或推送。原始输入仅用于生成有摘要的新隔离副本，新增竞态副本的预期删除单独记录，不混入固定7文件完整性比较。

## 驱动修复、审阅与现场边界

统一Guard在Click、Type、Shortcut、App、Launch、Snapshot及原生观察前核对ControlStatus、真正输入桌面、锁屏状态、前景稳定性、目标PID/HWND与映像。争用即失败锁存并保存单调时间/墙钟180秒截止；截止前禁止所有桌面请求，到期只读诊断，仍争用则再退让180秒。恢复必须显式引用失败ID和诊断ID，动作ID与parent token阻止重复输入、旧队列和并行请求。没有每步自动聚焦。

截图必须实际含image；`is_error=false`但文本报错、没有图像也停链。输入已执行后截图失败只允许另行观察，不重发输入。Type回执成功同样不能替代核对实际内容。

初版32项离线测试通过；专用恢复/迁移版共52项通过（包含原32项，不加总为84）。实际McpTransport/Controller与假时钟/假工具共用请求层，验证退让、失败锁存、截图空载荷、唯一请求、归属、进程见证及审阅门。材料为[offline-summary.json](../.local-analysis/basic-editing-remaining-acceptance/offline-summary.json)、[recovery-offline-summary.json](../.local-analysis/basic-editing-remaining-acceptance/recovery-offline-summary.json)及其日志/轨迹；这些是驱动测试，不是产品GUI测试。

父审阅批准`msg_d671d5b82a45`后开始阶段二。PowerShell5最初因包装脚本无UTF-8 BOM解析失败，脚本体未执行、桌面请求0；补BOM、AST核验和离线复验后重新获批。候选启动后前景是QQ，门禁阻止输入并完整退让；没有向QQ发送按键，也未重发Launch。父审阅专用`restore-target`后，批准一次客户端迁移：旧客户端树45596/9776/22864/42192/61044正面退出，新客户端53032完整继承failed、token、截止和全部请求ID，原候选27788/主HWND1183506/FILETIME134374552696214516保持不变。迁移批准以[migration-approval.json](../.local-analysis/basic-editing-remaining-acceptance/migration-approval.json)实文件为准，其`message_id`为`msg_8f16f130b1d0`（父最终预审确认按实文件引用）。之后压缩和全部剩余现场始终沿用该MCP连接。

专用恢复只在冷却到期、外部门禁允许、输入桌面未锁、全桌面PT Renew标题唯一且原PID/HWND/映像/创建时间一致时进行一次App切换并后验。原生文件框存在时不盲目切换。独立第二候选只在原进程持有句柄确认退出并显式retire后启动，同连接冷却和失败状态不清零。

现场必须保留以下驱动/环境问题，不能归为产品缺陷：

- m038回执`CONTROL_PREEMPTED`、`executed_steps=0`未被旧分类自动设为争用截止，但失败锁存有效，后续m039未执行。另行完整180秒零桌面请求后才诊断。原`preempted-retreat.json`因PowerShell5缺TickCount64把单调截止误写180，原件保留；[单调校正](../.local-analysis/basic-editing-remaining-acceptance/preempted-retreat-monotonic-correction.json)依据事件双时钟补正，未把错误元数据当有效截止。
- m025 Ctrl+0及m140 Delete已执行，后置Snapshot返回`CONTROL_UNAVAILABLE`；完整退让后只读恢复，没有重发动作。m133的user同样停链完整退让。
- m146请求supported路径，但0366图文件名框出现无关中文；来源未知。保留原请求和图像，另行完整180秒退让，压缩后只读诊断，再通过文件列表选择并截图0373核对`supported.pcb`，0385才确认载入。没有将Type成功当加载成功。
- m188菜单点击已执行，后置Snapshot返回“Previous screenshot flash did not close before capture”，无图像；本轮正确锁存失败，诊断/显式resume后0464单独补观察，没有重发菜单点击。
- 候选正常退出后，post_native因前景不再属于目标而保守停链。保留180秒截止，以进程句柄退出码确认，再显式retire；没有恢复已退出PID或重发放弃。

父另备通用`CONTROL_*`分类未来修复，必须在本轮GUI和客户端全部退出后才离线归档；它不能倒推为旧现场实例已支持PREEMPTED。最终归档状态见后文。

## 现场结果

| 项目 | 实际观察与判断 | 关键证据 |
| --- | --- | --- |
| 严格文本焦点 | 明确点击ΔX框，123→Delete空→Ctrl+Z恢复123→Ctrl+Y空；板图5图元/3走线、修订2及几何不变，取消后Undo/Redo禁用。通过。 | `checkpoint-1.json`；0024/0032/0036/0040/0048 |
| 旧式/现代入口与历史 | 画布M→T及现代移动菜单打开相同移动框；D→T实际删除，E→U/E→R实际撤销/重做。移动无独立现代快捷键，记N/A。 | `command-matrix.json`、`checkpoint-2-3.json` |
| 可视远移与reset | 单次ΔX/ΔY均10000，移出旧视野后显式reset可见可选，属性(10100,10100)→(10400,10500)、宽10mil/长500mil；Undo原几何clean、Redo远处dirty，底层隐藏保持。通过此范围。 | 0126/0130/0134/0147/0157 |
| 900000极端远移 | 提交dirty修订3、100%视图及底层隐藏保持；reset后亚像素，三次未命中远处属性。未验证该极端完整可见性/属性，不以10000结果外推。 | `checkpoint-3.json`；0075、0095 |
| 五类只读图元 | 自由焊盘FP、过孔FV、圆弧FA、填充FF、文字FS逐类选中后Delete不改6图元/1走线、clean修订19，移动自由线命令禁用，末尾Undo/Redo禁用。通过。 | `checkpoint-2-readonly.json`；0259/0271/0281/0291/0301/0307 |
| 定向取消与历史 | Ctrl+W取消、换empty.pcb取消、missing.pcb原生拒绝后取消、窗口关闭取消，均保留工作与历史；Undo原端点/长500/clean及Redo删除有直接图。missing只证明原生拒绝。通过各已测路径。 | `checkpoint-5.json`；0173/0181/0185/0197/0205/0209/0217/0227/0231/0235/0243 |
| 铜分析迟到 | 新合成板3905图元/3903走线，元素上界3915<4000；两次机会均未捕获后台运行中→编辑先完成→迟到结果未覆写的完整时间线。停止该类，未覆盖。 | `checkpoint-4-races.json`；0333/0337/0341/0347、m140回执 |
| NET迟到 | 一次oplock确实触发break，但m158前景仍为原生NET文件框HWND4395886；断言阻止后续画布输入，finally释放后NET正常载入。没有后台迟到时间线，未覆盖。 | `race-oplock/net-attempt-01/`及`factual-correction.json`；0396 |
| 选后文件消失 | 第一次delete-oplock只得到原生“文件正在使用”，不算产品读取失败；第二次WinEvent HIDE删除新副本，0427实际Qt状态显示找不到指定文件、当前工作与历史保留。Undo恢复(100,100)→(400,500)、宽10/长500、5图元/3走线clean，Redo恢复4/2 dirty。通过第二次路径。 | `race-file-vanish/attempt-02/result.json`；0414、0427、0433、0437 |
| 独立菜单退出 | 原候选窗口关闭放弃后退出0；同连接启动独立PID31072，实际删除dirty修订3，文件菜单退出显示放弃确认，确认后独立进程由持有句柄核验退出码0。通过该路径。 | 0441、m179；`target-2.json`、0464、0468、m193 |
| 系统会话结束 | 共享宿主不触发注销或关机。受控环境待验，未覆盖。 | `checkpoint-4-races.json` |

NET辅助`completed`仅表示文件打开触发break，不能当产品通过。其原`reason`固定写“完成目标编辑后请求释放”，本次实际仅finally释放，没有编辑；父已保留原件并增加事实校正，报告采用实际动作和前景记录。文件消失共用两次机会，未扩大次数或重建候选以掩盖问题。

## 收尾与可复核结论

全部现场已结束，未再发送桌面请求。原候选27788和独立候选31072分别由m179、m194的持有句柄确认退出码0；两次放弃后的post_native失配均保留完整180秒冷却，未重发放弃。m195正常停止原MCP客户端，未新建第三候选。候选23文件、源输入7文件、隔离输入7文件的集合、大小与SHA-256全部不变，见[integrity-result.json](../.local-analysis/basic-editing-remaining-acceptance/integrity-result.json)。本任务完整客户端树与候选13个身份经父按创建时间核对已退出，见[退出审计](../.local-analysis/basic-editing-remaining-acceptance/parent-audits/remaining-process-exit-parent-audit.json)，工作者又以同一创建时间独立核验通过；没有终止其他工程或关闭Pi终端。

父确认所有现场进程退出后，备份实际运行的52项版Guard到`provenance/guard-runtime-52.py`，SHA-256为`972c6c008713b681879f5d9c23da16965c6f09043f29b865bdbc11d16bbc4375`，才归档通用`CONTROL_*`分类未来修复。归档后Guard SHA为`d9d65ce0f293a1ea0df50c1a95bba6050d3ee970e230c30abd0d435cfd9d4158`，新增分类器SHA为`bba9238181a2304b5702e812b96eb938260eb4efc182d75518da60396ed747a4`。实际归档路径61项全部通过，0失败/错误/跳过、0真实桌面请求；61为原52项加9项新协议场景，未载入已退出旧实例，也未作产品GUI重验。见[归档记录](../.local-analysis/basic-editing-remaining-acceptance/future-control-archive.json)及[实际回归摘要](../.local-analysis/basic-editing-remaining-acceptance/future-control/archived-summary.json)。

[现场时序审计](../.local-analysis/basic-editing-remaining-acceptance/parent-audits/remaining-live-parent-audit.json)核对已持久化请求、完整退让和输入归属；图像判断仍以本报告及checkpoint为准。[verification-summary.json](../.local-analysis/basic-editing-remaining-acceptance/verification-summary.json)、[证据索引](../.local-analysis/basic-editing-remaining-acceptance/evidence-index.json)和[index-verification.json](../.local-analysis/basic-editing-remaining-acceptance/index-verification.json)记录最终结论、逐项字节数/SHA与复核结果。索引排除自身、验证回执和最终结算回执，避免递归摘要；旧回执、校正、未来修复和父审计均保留。仅文档交付，运行`git diff --check`及本地链接/证据完整性检查后提交，不合并、不推送。

本轮只补剩余项目，没有重复旧A—F矩阵或重新运行未改动产品的全部Qt/CTest。NET/铜层异步迟到、900000极端可见性和系统会话结束保护仍未验证；离线驱动回归与原产品自动测试均不替代这些实际GUI边界。
