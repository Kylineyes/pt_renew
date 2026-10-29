# 精确自建诊断窗的专用正常关闭

2026-10-29，从`dev=5c9c611`建立`feat/control-owned-window-close`。专用关闭实现与离线验证已完成，现场启动前失败，结果见[独立验收报告](control-owned-close-live.md)。旧现场、批准、failed/token、截止和原证据均只读；本轮失败也不重启补验。

旧路径在唯一Alt+F4已正常关闭诊断窗后，继续执行普通输入的前景后验并拒绝。新`tools/control_owned_close.py`提供默认禁用的`OwnedDiagnosticClose`，仅由创建自建窗的客户端登记原始Popen；请求不接受PID或窗口参数。关闭前沿用Guard门禁、物理矩形与前景检查，并核对唯一标题、PID、创建时间、映像、HWND、类及原Popen仍活。工具调用尝试即消费机会；只允许一次原Shortcut Alt+F4。

原工具成功返回后，最多5秒等待原Popen的退出码0，再退役原绑定并推进token。该路径不对已消失窗口请求前景后验。普通Guard及DiagnosticGuard源码与旧现场逐字节相同，Click/普通Shortcut继续执行原后验。工具拒绝、传输未知、取消、未退出、非0退出或不一致证据均失败；后来的退出只证明生命周期结束，不改写工具失败。failed/token与既有120秒截止保持，未设置截止的新失败沿用120秒退避。

`tools/control_close_client/`保存可审阅客户端模板，包含原门禁、精确检查和持柄辅助程序；接入`close-owned`、批准、预算、单步入口与stop条件。正常Alt+F4不能再通过普通key入口提交，关闭只在唯一完整诊断组后允许。即使组外直接提交或关闭机会重复也拒绝。单步关闭等待45秒、隐藏驱动等待50秒，覆盖35秒工具上限和5秒退出等待；不增加服务原900秒预算。运行时仍为600秒诊断、900秒收尾，关闭前至少留35秒工具、5秒退出、40秒停止余量；不通过WM_CLOSE或强杀补发。

`tools/freeze_control_close.py`只离线复制17客户端文件、3监督器文件、13工具文件和77文件控制包，生成111文件候选与摘要，默认没有任务、批准或有效关闭许可。模板通过实际路径找到同级冻结tools/isolated；使用时应保留该目录关系。新客户端必须通过双方`owned_diagnostic_close=true`及`owned_close_sha256`显式批准，并验证完整客户端/模块/包集合。旧客户端调用批准核验的缺省行为兼容。

关闭实现提交`69bdc82`，严格回执补强`81ae57b`；该版137项控制测试全部通过，包括14项新关闭/客户端测试和1项新批准测试。测试使用假时钟、假Popen及假桌面API；既有监督器测试使用无GUI标准库子进程。原始日志见本机[测试输出](../.local-analysis/control-owned-close/tests-verified.log)。首次误用全局Python产生依赖/解释器隔离错误，原输出保留为`tests-offline.log`；随后改用已验证MCP解释器，没有修改全局环境。没有改动产品源码或重建冻结产品。

离线冻结位于`.local-analysis/control-owned-close/frozen-v2/candidate/`，清单SHA-256为`cfca1f09dbc38ce905c0edb33d2b97120588775065598f4dad849c9341922103`。见[摘要索引](../.local-analysis/control-owned-close/offline-review.json)及[候选清单](../.local-analysis/control-owned-close/frozen-v2/candidate-manifest.json)。初稿111文件候选保留在`frozen/`，未启动；离线复核补充了冻结Shortcut成功回执的精确校验，空、畸形或不符回执均按结果未知失败，不因随后原Popen退出而成功。旧live172、旧候选110、原包77和稳定/固定/实验22/23/22文件集合及摘要已保存只读基线，现场后逐项比较。

后续现场按下述冻结顺序设计；本轮新Task/Dispatch已经启动前失败并结算，不再执行本组。需要再次验收时必须另立Task/Dispatch、独立验收分支和证据目录，Pi明确`deng/gpt-6.1-sol high`并核对实际环境、会话JSONL的模型/推理记录及read图片调用。先离线审阅和准备全部批准，再启动连续runner；基础Python原Popen直持runner、核对外层实际PID与原查询句柄，禁止等待代理消息的短放行闸门。

现场预计从服务启动起8～12分钟，硬上限15分钟：最多一个自建窗、一个连接、一组诊断；被动初始日志最多60秒，Launch→UIA→原App激活一次→首图实际读图→Click一次→Ctrl+Shift+F8一次→终图实际读图→close-owned一次→退役→stop。正常动作不额外ControlStatus。首次真实拒绝立即停止组，完整120秒不请求桌面；到期只按冻结方案观察原Popen、退役与停止，不恢复、不重发、不新连或追加第二组。没有退出则按原硬截止报告遗留身份，不能冒称关闭成功。

验收分别判断双图/双回调、专用关闭一次无拒绝、资源正常寿命与零账本、本组健康采样，以及监督器/已发现子孙/runner/launcher/owner的原退出证明。50ms子孙枚举仍不排除未知短命进程。本组通过也不证明长期稳定、性能倍率或产品固定0.11.0及NET/铜竞争通过。

本轮唯一启动在14:27:54（UTC+08:00）发生，Run `run_0ca568a11b7b` / Task `task_304e9df22f4d` / Dispatch `ctx_818a32eb5b79`，两批准绑定`msg_fa696d8887f7`。runner读取见证器身份JSON遭遇PermissionError，未写release、未执行监督器，服务/桌面请求/窗口均0，GUI、专用关闭、资源和健康均未执行。外层runner/launcher/owner原Popen和句柄均exit1，父recorder/owner原句柄均exit1；握手child50968没有原Popen或原句柄退出码，保持unverifiable。独立报告`8d41db3`及父[失败审计](../.local-analysis/control-owned-close/parent-independent-failure-audit.json)结论一致。旧live172、旧候选110、原包77及产品22/23/22全量摘要不变。

本轮失败后只在独立`fix/control-witness-handshake-read`分支离线修复见证器，提交`837baf8`、合入`33f4673`：身份文件的FileNotFoundError/PermissionError只在原握手截止内重读，不启动新进程或放行目标；构造器创建进程后任何读取/解析/校验异常均附带原pending_launch供调用方等待。底层权限错误原因仍未证实，修复不改写本组失败及child退出缺口。新增3项实质回归后[140项离线测试全部通过](../.local-analysis/control-owned-close/tests-handshake-fixed.log)，不与137项历史结果叠加。

第三候选已经由新任务唯一执行，见[第三候选现场](control-owned-close-v3-live.md)：GUI两图/双回调、7寿命7663上传零账本及3420健康分项通过；关闭preflight拒绝且Alt+F4未发送，监督器账本替换失败、子孙原退出码不完整，整组failed。诊断窗66968/birth134377322138115927/HWND15010430在晚到精确句柄查询时仍live；服务按原900秒截止退出，不补关或恢复。

本轮另在独立分支离线修复监督器周期快照写入失败时提前丢弃原进程的问题，142项控制测试通过。最新111文件候选、限制和下一步见[监督器快照修复](control-supervisor-snapshot-journal.md)及[下一阶段](control-next-stage.md)，尚未运行。旧第三份冻结和本轮失败execution均保留原样，不能追溯改写failed。下一现场之前先处理已知残留自建窗的生命周期归属。
