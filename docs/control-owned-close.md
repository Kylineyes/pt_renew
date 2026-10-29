# 精确自建诊断窗的专用正常关闭

2026-10-29，从`dev=5c9c611`建立`feat/control-owned-window-close`。本文件先记录可审阅实现与冻结方案，现场结果另记；旧现场、批准、failed/token、截止和原证据均只读。

旧路径在唯一Alt+F4已正常关闭诊断窗后，继续执行普通输入的前景后验并拒绝。新`tools/control_owned_close.py`提供默认禁用的`OwnedDiagnosticClose`，仅由创建自建窗的客户端登记原始Popen；请求不接受PID或窗口参数。关闭前沿用Guard门禁、物理矩形与前景检查，并核对唯一标题、PID、创建时间、映像、HWND、类及原Popen仍活。工具调用尝试即消费机会；只允许一次原Shortcut Alt+F4。

原工具成功返回后，最多5秒等待原Popen的退出码0，再退役原绑定并推进token。该路径不对已消失窗口请求前景后验。普通Guard及DiagnosticGuard源码与旧现场逐字节相同，Click/普通Shortcut继续执行原后验。工具拒绝、传输未知、取消、未退出、非0退出或不一致证据均失败；后来的退出只证明生命周期结束，不改写工具失败。failed/token与既有120秒截止保持，未设置截止的新失败沿用120秒退避。

`tools/control_close_client/`保存可审阅客户端模板，包含原门禁、精确检查和持柄辅助程序；接入`close-owned`、批准、预算、单步入口与stop条件。正常Alt+F4不能再通过普通key入口提交，关闭只在唯一完整诊断组后允许。即使组外直接提交或关闭机会重复也拒绝。单步关闭等待45秒、隐藏驱动等待50秒，覆盖35秒工具上限和5秒退出等待；不增加服务原900秒预算。运行时仍为600秒诊断、900秒收尾，关闭前至少留35秒工具、5秒退出、40秒停止余量；不通过WM_CLOSE或强杀补发。

`tools/freeze_control_close.py`只离线复制17客户端文件、3监督器文件、13工具文件和77文件控制包，生成111文件候选与摘要，默认没有任务、批准或有效关闭许可。模板通过实际路径找到同级冻结tools/isolated；使用时应保留该目录关系。新客户端必须通过双方`owned_diagnostic_close=true`及`owned_close_sha256`显式批准，并验证完整客户端/模块/包集合。旧客户端调用批准核验的缺省行为兼容。

本次136项控制测试全部通过，包括13项新关闭/客户端测试和1项新批准测试。测试使用假时钟、假Popen及假桌面API；既有监督器测试使用无GUI标准库子进程。原始日志见本机[测试输出](../.local-analysis/control-owned-close/tests-verified.log)。首次误用全局Python产生依赖/解释器隔离错误，原输出保留为`tests-offline.log`；随后改用已验证MCP解释器，没有修改全局环境。没有改动产品源码或重建冻结产品。

离线冻结位于`.local-analysis/control-owned-close/frozen/candidate/`，清单SHA-256为`31aea5b997c186a3361525db929d355d27a8e6b6d99a0c2dc1b71885cb1031a4`。见[摘要索引](../.local-analysis/control-owned-close/offline-review.json)及[候选清单](../.local-analysis/control-owned-close/frozen/candidate-manifest.json)。旧live172、旧候选110、原包77和稳定/固定/实验22/23/22文件集合及摘要已保存只读基线，现场后逐项比较。

后续仅安排一个全新Task/Dispatch、独立验收分支和证据目录，Pi明确`deng/gpt-6.1-sol high`并核对实际环境、会话JSONL的模型/推理记录及read图片调用。先离线审阅和准备全部批准，再启动连续runner；基础Python原Popen直持runner、核对外层实际PID与原查询句柄，禁止等待代理消息的短放行闸门。

现场预计从服务启动起8～12分钟，硬上限15分钟：最多一个自建窗、一个连接、一组诊断；被动初始日志最多60秒，Launch→UIA→原App激活一次→首图实际读图→Click一次→Ctrl+Shift+F8一次→终图实际读图→close-owned一次→退役→stop。正常动作不额外ControlStatus。首次真实拒绝立即停止组，完整120秒不请求桌面；到期只按冻结方案观察原Popen、退役与停止，不恢复、不重发、不新连或追加第二组。没有退出则按原硬截止报告遗留身份，不能冒称关闭成功。

验收分别判断双图/双回调、专用关闭一次无拒绝、资源正常寿命与零账本、本组健康采样，以及监督器/已发现子孙/runner/launcher/owner的原退出证明。50ms子孙枚举仍不排除未知短命进程。本组通过也不证明长期稳定、性能倍率或产品固定0.11.0及NET/铜竞争通过。
