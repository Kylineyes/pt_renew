# 控制恢复后的独立异步GUI验收（120秒版）

本轮完成四次独立实验运行及正常清理：**NET与铜层正向对照通过，两项竞争均中止，Task整体failed。** NET竞争没有实际编辑发布；铜竞争实际删除并观察到旧结果丢弃，但门闩内截图失败且通过cancel中止，不能补作有效竞争通过。稳定产品保持0.10.0，实验结果不替原固定0.11.0候选记通过，不改变总体验收未通过结论。

## 对象、恢复与新驱动

- Task：`task_cc0acf5789a3`；Dispatch：`ctx_2f2d4d1f3ae1`；Run：`run_021d6c33debf`。
- 工作分支：`verify/async-gui-recovered-120`，基于本地`origin/dev=cc46e4c2ed90d2c819015d6a5f3aeb804a752c6e`建立；只提交本报告，不合并、不推送。
- 原Pi会话`01a1739a-82f6-76cf-9ffc-c63e95be56d4`，环境、JSONL最后模型/推理及实际assistant均为`deng/gpt-6.1-sol high`，见[model.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/model.json)。
- 新证据目录：[async-gui-recovered-120](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/)；实验源码HEAD为`c4e3ec5e82bf1a022e523ec8844d0665d7b93234`，代码`98a4321`，实验EXE SHA-256为`782a769f6a1a00f60f184bda32c0a9b8bab9edafdc5a45218b9e697b3d00b4ac`。

用户实际轻按松开反引号后，原连接诊断成功并显式恢复，原控制链六个身份由持有句柄确认正常exit0；旧目标2020此前已结束退役，本轮不恢复该PID。原始退出、恢复状态与全部旧请求记录复制到新目录provenance，旧180秒档案保持原样。新连接建立在旧链真实恢复并正常退出之后，不把重连当作解决拒绝或实验通过。

新驱动在独立副本适配本轮身份、路径、120秒检查间隔和普通动作不额外ControlStatus预检的用户偏好；原生目标归属、PID/HWND/映像/创建时间、工具真实拒绝、image必需、失败锁存、唯一动作ID、不排队和已执行输入不重发均保留。争用后完整120秒无桌面请求，到期一次只读诊断并显式恢复；正常点击不增加120秒等待。运行仍保留已恢复token、旧截止和历史请求ID，新四机会不继承旧实验消费。

[4项变化路径定向测试](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/targeted-summary.json)通过，父另[8项独立检查](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/parent-audits/parent-targeted-review.json)通过；没有无变化重跑旧82项或产品全矩阵。父批准回复`msg_dd1c244eb8b1`，新[phase-two-approval.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/phase-two-approval.json)绑定本Task/Dispatch、候选SHA、根目录和21项文件摘要，获批后才启动MCP。实际Guard SHA为`7dc8831cba2616ff8f1ef1360f7a2c286777f46f623b5e66aa9f2dce62e995f2`；现场结束后21项冻结文件仍匹配，没有热改运行源码或第三方安装。

持续client/owner为PID33200，launcher31080；四运行共用同一MCP连接，owner为持续存活的控制客户端，不使用短命PowerShell PID。NET采用kind=net/skip=1，A完成后GUI打开B；铜采用kind=copper/skip=0，A完成后用共享命令快捷键Ctrl+Alt+C触发分析。各运行均仅一次目标请求、60秒门闩，旧失败不改写。

## 四次现场结果

| 运行 | PID | 实际结果 | 正常退出 |
| --- | --- | --- | --- |
| NET正向对照 | 37300 | B读取成功、accepted；最终NET_B/B摘要、clean修订2、3图元/1走线保持。通过 | Popen exit0 |
| NET竞争 | 59728 | B门闩实际进入，但关键段点击后无选中，Delete未发布文档；断言失败cancel中止，随后B读取成功并accepted。未通过，不补试 | Popen exit0 |
| 铜正向对照 | 39768 | 算法入口等待后释放，旧修订2报告accepted；最终支持模型内连接1/分离0、未超限。通过 | Popen exit0 |
| 铜竞争 | 29708 | 真实Delete发布修订3/dirty/0走线，后置截图控制不可用，立即cancel；旧修订2返回并discarded，experiment_aborted=true。未通过，不补试 | 放弃确认后Popen exit0 |

总预算4、实际独立候选4，两个有效对照、零个满足完整判据的竞争；没有追加运行、重新分析或重发Delete。所有关键截图均由指定截图会话实际查看，实际屏幕3840×2160、返回1920×1080，坐标比例2。

### NET正向对照

初始图0002确认实验标记、隔离board/a.net、NET_A、A摘要、3图元/1走线、clean修订2。图0007实际核对B路径后才提交关键段。原生框关闭，工作线程在成功打开B后进入读取门闩；[0009图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/0009-Snapshot-00.png)显示后台读取中，释放后[0010图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/0010-Snapshot-00.png)显示NET_B及B摘要`fc8cc17bc6cb8d0e584cf6f7489130326adccc621f6d4f6fffb68bf7363ca77b`，clean修订2/几何数量不变。

同应用单调纳秒：`worker-entered 588875307300 < gate-ready 588875325900 < gate-released 589580807400 < worker-returned 589581530300 < callback-accepted 589581625800`。门闩等待705.4815ms，无document-published或aborted。B成功摘要与隔离输入匹配，工作线程与GUI回调线程不同；这是实际工作函数等待及完成，不是只观察回调排队。

### NET竞争中止

图0027确认自由线属性`(100,100)→(400,500)`、宽10mil、长500mil及源行2；图0030确认B路径。实际请求2进入门闩，[0032图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/0032-Snapshot-00.png)显示后台读取及所选线；随后关键段再次点击预先给定坐标，选中变为空，[0035图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/0035-Snapshot-00.png)在Delete后仍为clean修订2、3图元/1走线，应用没有document-published。关键段断言失败、只本地cancel防遗留，无有效gate-released；应用随后记录aborted、B成功返回及accepted（experiment_aborted=true），补观察0037实际显示NET_B。

最初把原因描述为“同线重复点击取消选择”不准确，父核对BoardCanvas源码后已校正：同线点击不作toggle取消，空命中才清选。现有图像能确认点击未命中/未编辑，左dock宽度及画布走线位置在读取状态中变化，坐标偏差是可能原因；不宣称已确定全部根因，更不归为产品淘汰缺陷。该次机会已消费，未热改关键段或补试NET。

### 铜正向对照

A完成后单次Ctrl+Alt+C触发算法入口门闩。[0047图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/0047-Snapshot-00.png)显示后台受限铜层分析中；首次最终Snapshot返回CONTROL_UNAVAILABLE，无图像不作证据。完整120秒后同连接诊断/显式恢复，只补[0050图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/0050-Snapshot-00.png)，实际确认原板SHA、当前修订2、NET_A摘要、支持模型内连接1/分离0、完整支持模型/资源未触发/覆盖诊断0；clean和3图元/1走线保持。

单调纳秒：`worker-entered 654527390600 < gate-ready 654527418700 < gate-released 656282079500 < worker-returned 656285476700 < callback-accepted 656285917500`。等待1754.6608ms，无编辑或aborted；回调generation/board/net均匹配。门闩位于算法入口、预算计时前，表示工作任务已进入并受控暂停，不声称等待时持续做几何计算。

### 铜竞争中止与有限观察

图0059确认原自由线属性、A来源和clean修订2；[0061图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/0061-Snapshot-00.png)显示算法门闩中的分析状态。关键段真实选线/Delete一次，应用发布修订3、dirty=true、tracks=0且A摘要保持；紧接的新修订截图0064返回CONTROL_UNAVAILABLE、没有image，驱动立即失败锁存并本地cancel，没有有效release。

同应用纳秒：`worker-entered 962061188600 < gate-ready 962061212000 < document-published 964054500300 < aborted 965028184600 < worker-returned 965031504000 < callback-discarded 965031610300`。旧修订2结果返回时当前修订3，generation_matches=false、board_matches=false、net_matches=true，experiment_aborted=true。

完整120秒后仅补[0066图](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/0066-Snapshot-00.png)：实际2图元/0走线、dirty修订3、NET_A及A摘要`130e3b1e50c62762d72c57d73fc79955ec1d724c70cffad4ee0a9dd755baa974`保留，旧铜报告/诊断未恢复。该日志与事后UI支持“中止路径中的旧结果确实丢弃”，但缺门闩内编辑截图且没有gate-released，**不满足有效竞争验收**；不拿事后图修补失败时间线。未重发Delete或增加分析。

## 控制错误与正常清理

本轮真实USER_CONTROL（路径输入已执行后的截图）、CONTROL_UNAVAILABLE（铜对照最终截图/铜竞争Delete后截图）、新进程非目标前景和正常退出后的post_native失配均停止链，完整120秒后才恢复。输入已经执行时仅补观察，不重发Type、关闭、Delete或分析。新进程只在专用restore-target核对唯一标题、PID/HWND/映像/创建时间及实际门禁允许后恢复一次，没有每步自动抢焦点。

[本地时序审计](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/control-audit.json)核对10轮退让均为120秒，early_requests为空；父[独立现场审计](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/parent-audits/live-guard-audit.json)同样未发现提前请求。普通动作不额外ControlStatus前检；拒绝后的恢复检查才查询，旧180秒档案不冒称更新。本轮曾在remaining=0后多作一次45秒本地等待，只增加执行延迟，没有桌面请求或判据变化；父指出后未继续增加无必要等待。

四候选均正常关闭，由持有Popen确认exit0。最后dirty关闭实际查看0068放弃确认后点击放弃，没有强制终止。z001正常stop客户端，停止前持有六个查询句柄，确认6004/14012/31080/33200/38512/39152全部exit0，见[chain-exit.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/chain-exit.json)。没有操作其他工程进程，Pi终端保留；此后没有桌面请求。

## 完整性与交付边界

[完整性结果](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/integrity-result.json)核对实验部署22、固定候选23、稳定dist22、来源3、新隔离输入3的文件集合、大小及SHA前后全部一致。固定候选EXE仍为`dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8`，稳定EXE仍为`726a44aa5f1b976dcfbffa068c011b99038172a451eb0964cbc853ee3bf20fc1`。没有修改产品/实验源码、部署、第三方包或main。

[verification-summary.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/verification-summary.json)保存逐运行事件与机会消费，[证据索引](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/evidence-index.json)及[index-verification.json](C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/async-gui-recovered-120/index-verification.json)逐项核对字节数/SHA及本地报告链接；截图和本机材料均在忽略目录，不提交。两个对照通过是本轮新增的实验限定证据，两竞争未通过且不补试；旧failed结论保持。900000mil、系统会话及原字形不扩范围，原固定候选总体验收仍未通过。
