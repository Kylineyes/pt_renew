# 测试窗日志修复与完整回调取证

本轮限定目标 **succeeded**：一个新连接、一个自建窗口、一个诊断组完成首图0/0→真实Click一次→真实Ctrl+Shift+F8一次→最终图1/1，首终图均已实际读取；两条Tk输入回调记录完整落在对应原工具调用区间，计数1/0→1/1，窗口stderr为空，正常关闭终态一致。窗口、UIA探针与完整控制链均正常exit0。健康采样和健康修复两个开关均关闭，本组不代表历史截图故障、长期可靠性或产品竞争已通过。

- Task `task_d88863b795f8`，Dispatch `ctx_e09b30cefbe7`，Run `run_e136aa13bab5`，协调终端`term_bb347931-d545-42c6-9ff1-ca2ebbd65fda`。
- 原Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`；实际环境、JSONL模型/推理记录及assistant记录核对`deng/gpt-6.1-sol high`，没有用终端复用或空model字段代替模型证据。
- 分支`verify/control-window-logging`基于fetch后`origin/dev=b085fe220b5a072cef7edd635a8b85ecb1b69f6b`，证据`../.local-analysis/control-window-logging/`。旧四任务已结算、旧链exit0前置核验，原目录和报告保持。

可复用实现为[control_test_window.py](../tools/control_test_window.py)，对应[test_control_test_window.py](../tests/test_control_test_window.py)。旧第四阶段把`record(kind, **fields)`与输入`kind=`重名，界面先更新但逐输入日志失败。本次将事件名改为event_name，保留输入kind字段，每条记录含pid、monotonic、wall及counts，并逐行flush。Tk按钮command和快捷键绑定分别调用记录逻辑，没有程序接口更新界面来冒充现场键鼠。

窗口不再在导入时创建日志或GUI，可复用类独立测试；显式`--evidence-root`指定新任务目录。`launch_window`为本client创建的窗口明确重定向window-stdout.log/window-stderr.log，Tk异常处理同时标记callback-error并保留原stderr traceback，不吞异常或把异常当成功。离线3项新增测试覆盖两回调记录/单调计数、异常原堆栈输出、真实短子进程stdout/stderr捕获；最后一项只运行命令行异常脚本，无GUI/钩子/控制调用。3项通过，没有重跑产品矩阵或旧回归全集。

新驱动仅复制旧已验证UIA、可缩放窗口、App缓存刷新、物理矩形、失败预算和原120秒Guard，适配新身份/批准路径及子窗输出保存。18项新驱动摘要、2项可复用代码摘要、父3启动器和几何工具摘要/77包清单均先交父审阅，父在本次question `msg_82a0eeb981e4`明确批准并生成双批准后才启动。父自有健康tools/tests未被工作者修改；批准`indicator_health_sampling=false,indicator_health_fix=false`，客户端再次断言false。实际server仍用父启动器、隔离77文件包、原ControlToolGate及原Snapshot/Click/Shortcut。

| 步骤 | 实际结果 |
| --- | --- |
| l001/l002 | 新窗口PID69684、birth`134376651309508180`、HWND17043394；UIA CanMinimize/CanMaximize=true，原Desktop.get_windows枚举同一窗口，探针只读无激活/输入并exit0 |
| l003/l004 | 唯一组建立，首Snapshot直接成功，无需额外ControlStatus或App恢复；`0002`图已读计数0/0 |
| 图像/边界 | 原图3840×2160、返回1920×1080、倍率2；按钮图坐标约(1093,628)换算物理(2186,1256)，在物理rect `[1500,825,2874,1634]`内 |
| l005/l006 | 同Guard实际Click一次、Ctrl+Shift+F8一次成功，两Tk回调完整记录 |
| l007 | `0005`原Snapshot成功，实际读图按钮1/快捷键1，唯一组结束，未追加测试 |
| l008 | 原工具Alt+F4关闭成功执行，窗口正常退出后post_native前景失配，CLI报告错误并锁存120秒；保留原错误，不能称关闭CLI无错误 |
| l009/l010/l011 | 一次多余生命周期请求在已退出Popen断言拒绝，未发WM_CLOSE；原Popen exit0退役后，持有五链句柄正常stop，全部exit0 |

两次真实回调与原MCP调用均使用同主机monotonic秒，可直接核对：

| 输入 | 原call_tool起点/结束 | Tk回调时刻 | 回调后计数 |
| --- | --- | --- | --- |
| Click | 849064.2867774→849064.8594876 | 849064.3579264 | click1/shortcut0 |
| Ctrl+Shift+F8 | 849065.1195900→849065.6869584 | 849065.1496763 | click1/shortcut1 |
| Alt+F4正常关闭 | 849347.8222044→849348.3824849 | normal-close 849347.8518785 | click1/shortcut1 |

窗口记录依次为window-ready、input-callback(click)、input-callback(shortcut)、normal-close、mainloop-returned，时间严格递增，终态1/1与最终图相同，无callback-error。窗口stdout/stderr均0字节，显式输出重定向路径和原文件保留；本次不再存在第四阶段的逐回调缺口，也不改写旧轮日志缺失。父独立审计确认两个回调分别落在对应工具起止内，stderr0、终态一致；图像内容由指定验收会话实际读图确认。

实际原工具调用为Snapshot2、Click1、Shortcut2，其中一个Shortcut是诊断快捷键，一个是正常关闭，不能合写成两次测试输入。两张Snapshot参数保持use_vision=true/use_ui_tree=false/use_annotation=false，均有image并读图，未用Screenshot、OS截屏或其他输入入口。真实call_tool-start/end记录位于本地pacer等待后，原is_error/text/structured/images及完整raw保留。两Snapshot起止分别`848712.2900409→848712.8788310`、`849065.9537913→849066.2182031`，没有短间隔重试；诊断序列未遭真实工具拒绝，没有失败后补试本组。

控制器trace486行，trace-closed/dropped0，包含两次capture pause/resume/screenshot-return、一次cursor API对、14条低层hook，fail-open0。没有安装健康采样/修复事件，父新健康模块即使已在另一分支开发，本组也未加载。此样本不证明历史CONTROL_UNAVAILABLE根因已确定或修复，旧三failed及第四阶段限定通过保持原结论，小窗口不替NET/铜竞争通过。

收尾有一项代理操作失误如实保留：l008已执行Alt+F4后，我把它误作仍活窗口场景，多余提交l009 lifecycle-close。该请求在客户端`child.poll()`已退出的断言处拒绝，lifecycle-close-attempt/result均不存在，WM_CLOSE发送0；未再次发送键鼠或关闭消息。该断言错误不是现场新控制拒绝，也不作为成功证据。随后仅Popen exit0 retire，不再恢复已死窗口。退出后前景失配的原failed=`l008-close`、token=`l007-final`、截止`849468.4012629`和budget保留；120秒内没有桌面/原生请求，`early_requests=[]`。

五链38420/50932/60924/62752/70168停止前均持有创建时间匹配查询句柄，正常stop后全exit0，termination_calls0。父独立见证另持有50932/38420/60924/70168及窗口69684共五身份，也确认exit0；不凭进程列表缺失代替退出证据。窗口Popen及UIA探针均exit0，无残留/后台桌面动作。

最终18驱动、2workspace代码、父3启动器及几何摘要均与批准一致；第三方原安装和隔离包各77文件、稳定22/固定23/实验22部署文件名集合/字节/SHA前后不变。未改产品、dist/main或原材料，未启动固定/实验候选，稳定保持0.10.0。只提交本报告、可复用窗口和3项测试，不合并推送；健康验证须另Task/新批准，不在本轮继续。

本地证据入口（Git忽略目录）：

- [模型会话](../.local-analysis/control-window-logging/model.json)、[18+2摘要/3测试](../.local-analysis/control-window-logging/checkpoint-offline.json)、[测试日志](../.local-analysis/control-window-logging/targeted-tests.log)、[客户端批准](../.local-analysis/control-window-logging/phase-two-approval.json)、[父批准](../.local-analysis/control-window-logging/parent-audits/window-logging-approval.json)。
- [UIA前置](../.local-analysis/control-window-logging/uia-preflight.json)、[首图0/0](../.local-analysis/control-window-logging/0002-Snapshot-00.png)、[最终图1/1](../.local-analysis/control-window-logging/0005-Snapshot-00.png)、[完整窗口回调](../.local-analysis/control-window-logging/window-events.jsonl)、[窗口stderr](../.local-analysis/control-window-logging/window-stderr.log)、[窗口stdout](../.local-analysis/control-window-logging/window-stdout.log)、[回调时序审计](../.local-analysis/control-window-logging/callback-audit.json)。
- [原工具调用时刻](../.local-analysis/control-window-logging/actual-calls.jsonl)、[controller trace](../.local-analysis/control-window-logging/controller-trace.jsonl)、[trace汇总](../.local-analysis/control-window-logging/trace-summary.json)、[父独立审计](../.local-analysis/control-window-logging/parent-audits/logging-independent-audit.json)。
- [关闭后验原回执](../.local-analysis/control-window-logging/l008-close-complete.json)、[多余收尾请求事实](../.local-analysis/control-window-logging/cleanup-extra-request.json)、[Popen exit0](../.local-analysis/control-window-logging/window-exit.json)、[五链句柄exit0](../.local-analysis/control-window-logging/chain-exit.json)、[父句柄见证](../.local-analysis/control-window-logging/parent-audits/logging-chain-witness-state.json)、[门禁审计](../.local-analysis/control-window-logging/control-audit.json)、[完整性](../.local-analysis/control-window-logging/integrity-result.json)、[结果](../.local-analysis/control-window-logging/verification-summary.json)、[索引](../.local-analysis/control-window-logging/evidence-index.json)。
