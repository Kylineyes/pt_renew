# 异步竞争续验：按运行中截图自适应选线

本轮使用独立实验候选，只执行NET和铜各一次新竞争，引用上一轮已通过对照作前置，不重跑对照、不改写旧failed。稳定产品保持0.10.0，实验结果不能替固定0.11.0候选通过。

- Task：`task_5877c051c786`；Dispatch：`ctx_b449da0e783c`；Run：`run_77f70610bac1`。
- 分支：`verify/async-races-adaptive`，从本地`origin/dev=ef1af656ccb3ecccf508773a9c07c11ea36f7ef7`建立。
- 原Pi session：`01a1739a-82f6-76cf-9ffc-c63e95be56d4`，环境、JSONL及实际assistant记录均为`deng/gpt-6.1-sol high`。
- 证据目录：`../.local-analysis/async-races-adaptive/`；实验EXE SHA-256：`782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`。

旧驱动复制到新目录并保留provenance。新关键段只从门闩当前有效Snapshot图定位合成连线：实际尺寸1920×1080、桌面3840×2160、比例2必须一致；ROI中唯一大橙色连通簇的中段逐行区间和线宽满足条件才产生点击坐标。缺线、多目标、未知比例/尺寸均拒绝输入。实际图中dock宽度变化时选点随之移动，不再复用触发前canvas_loc，不把同线点击错误描述成toggle取消。选点只决定GUI Click位置，不代替实际截图判断，不调用产品编辑接口。

Snapshot仍使用原工具参数use_vision=true/use_ui_tree=false/use_annotation=false。新运行只在相邻Snapshot完成后安排至少4秒本地间隔，已过间隔不额外等待；真实工具错误直接返回Guard停链，不自动重试、换入口或修改第三方包。4秒节奏没有宣称修复控制工具。

12项定向测试通过，包含5张不同布局旧图、缺线/多目标/未知大小/错误比例拒绝、两race预算和历史前置、节奏及实际适配器不掩盖拒绝。增加历史对照source-plan候选/输入上下文绑定后，仅复验3项预算测试通过，不将重复复验累加覆盖数。系统Python的NumPy/Pillow扩展不兼容只作环境记录，实际测试与运行统一使用原MCP解释器已有Pillow，没有安装或修复依赖。

历史NET对照PID37300和铜对照39768的原始日志、最终图、launch/exit0复制controls并冻结；与本轮候选SHA和输入摘要一致，代码验证有效release→returned→accepted和无编辑/aborted。它们属于历史前置，不虚写成本轮新对照。父明确批准`msg_f2e1a6c17afd`并生成新phase-two-approval后才启动单MCP连接，运行源码此后不改。

本轮总体结论为 **failed**：两次竞争都从当前门闩图正确定位并实际删除走线，应用发布修订3/dirty/零走线/A来源；但Delete后截图分别遭遇`USER_CONTROL`和`CONTROL_UNAVAILABLE`，两次都立即cancel中止，没有有效`gate-released`。它们只能证明中止路径上的旧结果丢弃，不能建立完整竞争验收，后来补图不能补正门闩内缺图；两次预算全部消费，没有重发Delete、补试或第三个候选。

| 项目 | NET竞争 | 铜竞争 |
| --- | --- | --- |
| 本轮唯一候选 | PID66732，kind net/skip1 | PID54752，kind copper/skip0 |
| 已读触发前图 | `0007`线属性和A；`0010`完整B路径 | `0028`线属性和A |
| 已读门闩运行图 | `0012`显示正在读取NET、修订2、3图元/1线 | `0030`显示正在后台铜分析、修订2、3图元/1线 |
| 当前图自适应桌面点击坐标 | `(2002,1060)`，来自`0012` | `(2051,1060)`，来自`0030` |
| Delete后截图 | `0015`：USER_CONTROL，images空 | `0033`：CONTROL_UNAVAILABLE，images空 |
| 后续已读有效图 | `0017`：dirty修订3、2图元/0线、A，旧B丢弃提示 | `0035`：dirty修订3、2图元/0线、A，旧铜结论已清除 |
| 有效release / 判定 | 无 / failed | 无 / failed |
| 正常退出 | `an017-retire` Popen exit0 | `ac024-retire` Popen exit0 |

两次桌面点击坐标随dock布局变化而改变，实际Click及Delete均走相同Guard和真实工具，不从应用内部直接编辑。NET的B返回摘要仍为`fc8cc17b…ca77b`，旧generation4对当前5发生discard，最终图保留NET_A及A摘要`130e3b1e…baa974`；铜返回的是旧revision2/3铜元素，当前revision3、generation/board不匹配、NET仍匹配，最终没有把旧铜报告恢复。两者回调都有`experiment_aborted=true`，不将discard单独包装成有效竞争通过。

同一候选应用的纳秒时序如下，原始日志保留全部字段；`gate-released`均缺失。

| 事件 | NET PID66732 | 铜 PID54752 |
| --- | ---: | ---: |
| worker-entered | 1555015949500 | 1157422441900 |
| gate-ready | 1555015972600 | 1157422472400 |
| document-published | 1556741122000 | 1159427164100 |
| aborted | 1559905115700 | 1162480015200 |
| worker-returned | 1559905943800 | 1162483543500 |
| callback-discarded | 1559906095800 | 1162483647100 |

NET启动和铜启动各一次前景不符均先完整120秒、专用restore及显式resume；真实截图拒绝也完整120秒后同连接diagnose/resume，只补状态观察，未重发已执行Delete。NET的放弃退出输入已执行后post_native因目标消失而锁存，随后只用Popen退役，不重发放弃。

铜收尾`0037`真实dirty放弃框已读；`ac016-discard`前检看到WindowsTerminal前景，executed=false，输入未发送。到期`ac017-restore`保存的原生快照已显示目标modal在前景，但主窗口和Qt modal都使用`Qt6120QWindowIcon`，专用恢复的all_main唯一性判断拒绝。该边界如实保留：再次完整120秒后原有普通diagnose确认同PID/映像/创建时间/实验主HWND，显式resume后取得`0040`当前对话框并实际读图，再以全新ID`ac023-discard`正常放弃，Popen证明exit0；运行源码没有修改、没有备用入口或新连接。主窗口和modal所属进程的实际创建时间均为`134376332629868809`，不能用CIM或JSON数字精度损失后的近似数代替。

两候选正常关闭后先持有控制链38152/39460/44420/67180/68860/72748的查询句柄，再`az001-stop`正常停止持有者；六个精确创建时间匹配句柄均确认退出码0，`termination_calls=0`。没有当前候选或控制链残留，保留Pi终端；父的独立句柄见证也证明所持身份exit0。停止后没有再发任何桌面请求。

最终审计：8次真实120秒退避，`early_requests=[]`；真实Snapshot回执完成间隔最短4.200545秒。Guard的tool_request日志位于pacer等待前，未单独记录实际MCP调用起点，因此回执完成间隔只按其真实含义报告；冻结适配器和定向测试验证“完成后至少4秒再调用”，不伪造逐调用起点实测。4秒节奏仍出现真实拒绝，不能声称工具已修复。父批准冻结30项全部摘要相符，实验22/固定23/稳定22/来源3/新输入3的文件名集合、字节数和SHA-256均与前置一致。仅新增本报告入Git，证据、驱动、图像不提交，未改产品或实验源码、未重建、合并或推送。

本轮没有重新构建或重跑产品测试：产品字节未变，离线定向测试与两次真实GUI竞争及退出验证按本轮范围完成。稳定仍为0.10.0，固定候选总验收状态不改变，900000mil、系统会话保护及原字形runtime不在本轮范围。

本地证据入口（均位于Git忽略目录）：

- [模型与原会话核对](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/model.json)、[12项定向测试](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/targeted-summary.json)、[批准及30项冻结](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/phase-two-approval.json)。
- [历史对照上下文](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/controls/source-plan.json)、[NET历史对照原日志](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/controls/net-control/events.jsonl)、[铜历史对照原日志](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/controls/copper-control/events.jsonl)。
- [NET运行图0012](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/0012-Snapshot-00.png)、[NET缺图回执0015](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/0015-Snapshot.json)、[NET事后图0017](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/0017-Snapshot-00.png)、[NET应用日志](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/runs/net-race/events/events.jsonl)。
- [铜运行图0030](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/0030-Snapshot-00.png)、[铜缺图回执0033](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/0033-Snapshot.json)、[铜事后图0035](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/0035-Snapshot-00.png)、[铜应用日志](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/runs/copper-race/events/events.jsonl)、[当前放弃框0040](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/0040-Snapshot-00.png)。
- [完整120秒审计](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/control-audit.json)、[Snapshot节奏证据及限制](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/snapshot-pacing-audit.json)、[六链持有句柄退出](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/chain-exit.json)、[完整性](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/integrity-result.json)、[结果汇总](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/verification-summary.json)、[证据索引](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-races-adaptive/evidence-index.json)。
