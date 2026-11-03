# 原 AUTOTRAX 短观察方案与本轮阻塞

本轮真实目标未通过：没有执行新现场，没有新增客体截图，没有核定工作文件名和图元计数，也没有取得原软件新建单线、另存及重开样例。父协调者在本轮模型多次连接失败、工具间隔已达十余分钟后明确不放行现场，要求交付离线短方案，避免活目标等待模型。没有把离线检查、历史图像或工具回执写成新 GUI 成功，产品能力门与默认字段均未修改。

基线 `origin/dev=3fd6e5fa2b241ef8c61bf6ecd7b46c4839b34be6`，新分支 `verify/native-short-observation`。切分支前工作树干净，只提交本报告；本树 `.local-analysis/native-short-observation/` 是全新忽略证据目录。沿用 Pi 会话 `01a19f6a-a52d-7333-95f3-2972829f4e9f`，实际环境和会话 assistant 事件为 `deng/gpt-6.1-sol high`，成功工具事件已存入 `session-audit.json`；没有切模型、派生代理、合并或推送。

已完整读取 `AGENTS.md`、[统一交接](agent-handoff-20261103-pcb-check.md)、[显示分离诊断](native-startup-diagnosis.md)、[上轮两槽报告](native-guest-save-sample.md)，以及旧 retry-01 driver／submit。切分支前旧树缺少两份新文档，切到指定基线后已成功读取；不将旧工作树缺失误记为材料不存在。

## 本轮确认的证据边界

旧 `retry-01` 的实际 Capture 菜单已确认 **Take screenshot 为 F11+P**，Raw 为 F11+Ctrl+P；Ctrl+F5 是复制。本轮父指定模型另行实际读取旧菜单和旧 `pt_000.png`，确认客体为 AUTOTRAX 1.57 启动页并显示 PRESS ANY KEY TO START，未包含文件名或计数。父回执在 `main-2/.local-analysis/native-evidence-wave/parent-image-review.json`。本 worker 本轮只读文档、脚本和摘要，不冒称重新看过历史原图或取得新图。

旧第二捕获的 `stopped-error.json` 明确为 **16:16:31 进入最后七分钟收尾范围**，在公开热键发送前被拒；没有第二 PNG。因此缺图不是已证明 F11+P 无效，也不是连续捕获通过。旧目标原创建者在父迟到正常关闭后于16:25:45真实 wait0；旧迟到事实保留，不改写为按时退出，不恢复旧进程或收件箱。

旧唯一动作名 submit 拒绝待消费请求、同名 consumed 和缺少原图 review；旧三轮离线消费和三拒绝结果可以复用为参考。旧 driver 将最后420秒限制为正常收尾，并保留原创建者 Popen／HANDLE。当前只记录其 SHA-256，不重建通用框架或再跑旧现场。

旧 `verification-35/step-012-information-key-event.json` 和 `step-013-status.json` 的实际公开请求分别为 `Shortcut shift+i`、`Shortcut shift+s`。这只是有依据的下一次输入路径，不能用主机 Pressed 回执代替客体菜单和状态验收。

## 最小新观察路径

可审阅的结构化方案为：

`C:/Users/rikideng/orca/workspaces/pt_renew/native-startup-diagnosis/.local-analysis/native-short-observation/short-plan.json`

方案 SHA-256：`72817fd675ef36fe5395296dd068b8fd304463d2ffaad2887479367d62232eb1`。

| 只读参考 | SHA-256 |
| --- | --- |
| 旧 retry-01 driver | `4470713e8bd6afcb2b2f687ba1894e0df8e04081994c24b1a70726f269095323` |
| 唯一动作名 submit | `c5f1dfad884fe69c8f0d60b58d2e797f2c2912f86bc1375e1d120f6ecced272d` |

以上是参考材料摘要，**不是本轮已准备并获批的可执行现场冻结**。本轮没有新副本、现场 driver、GO 文件、服务、目标、桌面请求或截图。未来父重新允许准备时，才复制新隔离运行目录和独立输入／输出目录，保存原安装99项与复制后完整摘要，适配新 driver 的仓库层级、新 Task／Dispatch／plan 绑定并冻结；原安装不挂载，旧目录只读。

建议未来单槽30分钟，其中最后7分钟仅正常收尾。当前没有有效起止时段；必须在模型可持续处理工具时，由父按实时时钟回复 GO 并向用户公告后才启动。动作顺序如下，每项只在上一项实际原图已读后决定：

1. 门禁、锁屏与唯一精确新 PID／创建时间／HWND／前景核对，新启动宿主原图实际读取；必要时公开 App 精确聚焦并读后图。
2. 单次公开 `Shortcut f11+p`。核对动作前后 capture 目录差异，确认新增非空 PNG，实际读取原640×480客体图并保存对应模型／工具事件和原字节摘要，不能只看宿主黑线或 synthetic 回执。
3. 只有第一图已读且可辨才单次第二次 F11+P，再确认另一个新文件和真实 image 回执；未生成新图立即停业务，不盲目补键。
4. 若两图均为启动页，按当前图单次 Enter，再读取宿主后图，单次捕获并读取新客体图。逐步进入主菜单、Shift+I 和 Shift+S，每个业务动作后都捕获并读取客体。确认实际工作文件名与计数，不能拿 SYN1 打开日志代替计数。
5. 状态证据先报父，父检查点确认后才能考虑空板、新段和保存。清板、选择层／宽／端点、全新8.3文件保存及重开均依据当前客体图逐步进行，不预排未知业务。真实样例出现立即报告，不等长文档。

正常退出优先使用现有公开 Close（Alt+F4）或当前图确认的宿主 X，原 owner 持有本轮 Popen／HANDLE 至真实 wait；控制服务也由原创建者 wait。关闭失败立即上报本轮精确身份，不强杀、不按历史 PID 或窗口消失推断退出，不换输入入口绕拒绝。连接延迟开始侵蚀收尾预算时提前停止业务；公开门拒绝继续执行既定120秒静默规则。不能靠未来截止时强杀保证时间。

## 本轮实际验证与未执行范围

`python .local-analysis/native-short-observation/prepare_offline.py` 退出0，提取本轮17个原会话事件，其中6个成功工具结果，保存旧关键材料路径／大小／SHA和短方案；后续工具另保留在原会话。脚本没有导入或调用旧 driver，没有调用桌面函数，没有修改其他树或旧证据。

首次本轮成功工具在北京时间20:32:56确认模型与会话，20:50:42切新分支并向父报告会话文件；20:58:14已处理并 ack 父“不放行现场”和历史图复核消息至空。工具间持续连接延迟使现场观察风险没有消除。21:02:48离线材料生成成功，随后通过协调问答提交方案，问题 ID `msg_77df0b3ac92a`；问答超时本身不代表 GO，继续遵守未授权现场边界。

本轮没有触及原安装、库和用户文件，也没有运行 Qt 构建、全轮测试或原软件。没有本轮目标／服务，故没有可声称的本轮目标 wait 或新的安装运行前后摘要；既有退出与99项摘要只属于历史证据。

未完成项明确为：连续两张新客体截图、F11+P实际成功发送、File／Information／Status文件名计数、空板、单线层／宽／端点、原软件新保存字节及重开。默认 FT 六／七字段、附加值、换行、布局与兼容性仍未知；`trackPlacementUserEntryAvailable()`保持关闭，不把离线阶段交付当作真实单线目标成功。
