# 初始原App激活与位图成本取证

本轮限定 **succeeded**：一次组前原App激活及精确前景后验成功，首图0/0→一次真实Click/一次Ctrl+Shift+F8→终图1/1，首终图由指定验收会话实际读取；取得真实位图上传成本。**健康稳定性仍未通过**，不称历史故障修复或产品竞争通过。

Task `task_47e20595fdcb` / Dispatch `ctx_343756e91911` / Run `run_b750f95c36e5`；原Pi session `01a1739a-82f6-76cf-9ffc-c63e95be56d4`的环境/JSONL/assistant核对`deng/gpt-6.1-sol high`。分支`verify/control-initial-activation`基于`origin/dev=86714d8a3401f2bb0ee4e631c99a287330d4d8f3`，父source-ready后核对19驱动/5启动器/几何及激活模块与77清单，新批准`msg_f6d332380fea`绑定用户本次“允许”，未复用旧任务或重跑61测试。

t0=`869863.8226699`，诊断/收尾硬截止600/900秒；初始10.387秒纯日志观察ready通过，创建窗口前复核通过。唯一窗口PID40400/birth`134376865231274087`/HWND8259734的UIA原枚举通过；`initial-activate`仅调用原App一次，无额外ControlStatus、直接原生激活或改状态，返回后PID/birth/HWND/映像/标题与物理rect前景后验通过，才开始组。

原工具调用App1、Snapshot2、Click1、Shortcut2（诊断与Alt+F4关闭各一），无重复测试；图原3840×2160/返回1920×1080/倍率2，物理按钮点(2186,1256)在物理rect内。两输入回调分别落对应call_tool起止内，计数1/0→1/1，窗口stderr/stdout空，关闭终态1/1。原Snapshot/门禁及1秒健康阈值保持，未热改或制造故障。

trace7384行正常closed/dropped0；位图installed scope=`windows-mcp-control-indicator`。4081次上传均尺寸/字节匹配BGRA，正常API次数及清理精确符合预期：SelectObject8162，其余GetDC/CreateCompatibleDC/CreateDIBSection/memmove/UpdateLayeredWindow/DeleteObject/DeleteDC/ReleaseDC各4081；上传异常0，仅验证本次正常路径，不外推未执行异常路径。

总上传墙钟5.187942秒，测得API累计5.085509秒，API外约0.102433秒。各API占总上传墙钟：memmove26.01%、UpdateLayeredWindow18.31%、DeleteObject12.45%、GetDC10.33%、SelectObject9.11%、CreateDIBSection8.12%、CreateCompatibleDC7.07%、ReleaseDC4.79%、DeleteDC1.85%。均含调度/诊断开销，不是CPU成本，不能把剩余时间减法当CPU结论。

最慢上传0.3109134秒，56×2048/458752字节：memmove约0.1086793秒、CreateCompatibleDC0.0625340秒、SelectObject两次合0.0615804秒、GetDC0.0303925秒、UpdateLayeredWindow0.0156880秒，其余和清理详见top慢上传原记录。本样本有可见慢上传，但单个API占比不证明心跳间隙的唯一原因。

2883条健康实际判定逐行一致，其中2stale年龄1.0200467/1.1905275秒，均在layer.set_opacity阶段被观测；一次同watch线程fail-open保存`indicator_ok=false,desktop_ok=true`。这仍是真实滞后，不是伪负年龄；阶段关联/多层累积与调度因果未唯一确定，不能推广到无诊断环境或历史全部拒绝。

a009 Alt+F4已实际正常关闭后post_native因目标消失返回错误并锁存，原件保留；仅Popen exit0退役，不重发关闭或WM_CLOSE。窗口及UIA探针exit0，五链39876/41220/43336/68072/72760停止前持有精确创建时间匹配句柄，正常stop全exit0，termination_calls0。trace关闭t0+764.531秒（约12分45），诊断动作均600秒内、收尾900秒内；早期见证仍活记录另存，最终退出用重新持有句柄证明。

父独立API/回调/退出审计与本地一致；19驱动、5启动器、几何/激活摘要、原安装77/隔离77及稳定22/固定23/实验22部署前后不变。稳定/dist仍0.10.0，main和产品竞争结论不动；仅提交本报告、不改父tools/tests、不合并推送，截图/第三方/日志不入Git。

- [模型/批准](../.local-analysis/control-initial-activation/phase-two-approval.json)、[原App激活结果](../.local-analysis/control-initial-activation/a003-activate-complete.json)、[首图0/0](../.local-analysis/control-initial-activation/0003-Snapshot-00.png)、[终图1/1](../.local-analysis/control-initial-activation/0006-Snapshot-00.png)、[回调原件](../.local-analysis/control-initial-activation/window-events.jsonl)、[stderr](../.local-analysis/control-initial-activation/window-stderr.log)。
- [原调用时刻](../.local-analysis/control-initial-activation/actual-calls.jsonl)、[完整trace](../.local-analysis/control-initial-activation/controller-trace.jsonl)、[API百分比/尺寸/字节/top慢上传/健康](../.local-analysis/control-initial-activation/bitmap-audit.json)、[父独立审计](../.local-analysis/control-initial-activation/parent-audits/independent-audit.json)、[回调审计](../.local-analysis/control-initial-activation/callback-audit.json)。
- [五链句柄exit0](../.local-analysis/control-initial-activation/chain-exit.json)、[Popen exit0](../.local-analysis/control-initial-activation/window-exit.json)、[时限/门禁](../.local-analysis/control-initial-activation/runtime-audit.json)、[完整性](../.local-analysis/control-initial-activation/integrity-result.json)、[限定结果](../.local-analysis/control-initial-activation/verification-summary.json)、[证据索引](../.local-analysis/control-initial-activation/evidence-index.json)。
