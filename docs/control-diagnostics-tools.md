# 控制工具隔离诊断与App窗口缓存修复

PT Renew的真实GUI验收多次在编辑后的截图阶段遇到控制拒绝。新增工具用于在独立控制包副本中保留拒绝原因和真实调用轨迹；它不修改PT Renew或已安装控制工具，也不把日志替代有效GUI图像。稳定产品保持0.10.0，固定0.11.0候选验收状态不因工具测试改变。

`tools/run_control_diagnostics.py`先复制本机已安装的`windows_mcp`包，核验原包与隔离副本每个文件的SHA-256，生成清单。运行阶段复验清单、当前任务身份和启动器摘要，确认实际导入来源是独立副本后，调用原MCP服务及其ControlToolGate。复制包、诊断日志、截图和清单均放在Git忽略目录，第三方包源码不提交。

`tools/control_diagnostics.py`包装原控制器方法并继续调用原实现，只向状态附加`diagnostics`并记录阶段。原`state`、`generation`、`wait_seconds`、拒绝代码、异常及保持键集合不被清理或重置；1秒心跳阈值、接管、截图暂停和输入账本原语义不变。低层记录只有消息类别和injected标志，不保存键值、字符或输入文字。队列有界，磁盘由独立线程写入，正常关闭记录`trace-closed`及丢失数量；存在丢失或写入失败时不能声称有完整因果证据。

可观察字段包括截图暂停/恢复、调用开始/结束、控制状态变迁、物理事件处理类别、指针API阶段、fail-open调用点、控制/指示线程心跳年龄与状态。fail-open只记录看门狗已经求值的健康布尔，不额外触发健康检查。字段为非原子只读快照，诊断开销也可能改变调度时序；单次时序邻近或没有复现都不证明历史原因。

新增`tools/control_app_refresh.py`针对一个可离线复现的问题：原`Desktop.switch_app`只在窗口缓存为空时更新列表，已有非空旧列表会遗漏后来新建的窗口并返回not found。修复在原switch_app前调用get_state刷新，随后仍由原模糊查找、激活和前景后验决定成功；刷新失败、目标不存在或Windows拒绝激活都仍失败。该修复默认不加载，只有新进程的明确批准`app_refresh_fix=true`且摘要包含该文件才启用。它只解决缓存旧列表的问题；原`get_windows`还要求UIA窗口支持最小化和最大化，不支持最大化的窗口可能仍被过滤，刷新不会改变这一枚举规则。离线真实枚举方法的假控件复现已确认该边界，现场是否由此触发仍需对应UIA属性直接取证。不能热改正在拒绝操作的服务，不能以此跳过ControlToolGate，更不能称它修复了历史截图错误。

`tools/control_geometry.py`在临时线程`PER_MONITOR_AWARE_V2`上下文读取物理窗口矩形，最后恢复原线程上下文。它解决诊断客户端把DPI虚拟化的逻辑窗口矩形与Snapshot物理点击坐标直接比较的问题，未知上下文、无效矩形或恢复失败都拒绝结果，不移除边界检查、不激活或改变窗口。6项假Win32测试覆盖物理点、读取/上下文失败及恢复路径。

`tools/control_indicator_health.py`现在提供新隔离进程可选的健康判定采样。每条`indicator-health-sample`记录该次判定实际使用的线程/停止/错误状态、`now`、`heartbeat`、年龄、读取顺序和返回值；原短路未执行的读取保留空值，避免把事后快照当作原判定证据。默认启动器仍不加载它。批准`indicator_health_sampling=true`且冻结该模块摘要后，保持原先取当前时间再取心跳的顺序；额外明确`indicator_health_fix=true`才启用先心跳后时间的修复，修复必须同时采样。两种模式都保留原1秒阈值及过期/未来心跳、停止、故障、线程死亡拒绝。

采样同时附加指示层阶段观察：显示器枚举、图层建立、透明度更新、显示/隐藏/移动/关闭、消息泵和状态确认。健康行记录当时观察到的阶段与开始时间，完成阶段仅在耗时至少50毫秒或异常时写入`indicator-phase`。阶段读取不构成原子线程快照，阶段为空不能归因具体渲染或调度；包装和日志也会影响时序。离线测试确认原读取顺序的伪负年龄可复现、修复顺序有效，以及实际判定字段、短路、阶段异常传播和清理。本轮已在新隔离进程实际加载并完成限定组观察：5444条原采样判定全部可复核，其中3条真实年龄超过1秒，最大约1.0781844秒，并触发两次看门狗fail-open。两次有效Snapshot和诊断输入完成不代表控制稳定性已修复；详见[健康验证](control-health-validation.md)。

`tools/control_diagnostic_budget.py`用于诊断驱动的受限动作预算。驱动在专用目标恢复返回后须调用`restored(row)`；失败立即终止诊断组，保留一次只读诊断和观察用于收尾。它修复了基线中恢复失败未联动预算、导致diagnose在到达MCP前被本地断言拦下的缺口。失败后不会继续点击探测，已执行关闭也不会被自动重发。

隔离包准备示例，使用已有MCP环境的Python，避免系统Python的Pillow二进制版本不一致：

```powershell
& '<MCP环境>/Scripts/python.exe' -X utf8 tools/run_control_diagnostics.py prepare `
  --source '<MCP环境>/Lib/site-packages/windows_mcp' `
  --destination '.local-analysis/control-diagnostics/isolated'
```

后续新增[健康日志离线重放](control-offline-replay.md)及`tools/replay_control_health.py`，只读取已保存JSONL，不导入控制包或调用桌面。它按相同旧心跳归并过期采样，计算阶段区间并集，分别保留事后完整阶段与首次过期当时可见的阶段覆盖，并拒绝丢失/未关闭/矛盾输入。新增8项重放测试，合并相关控制测试共47项实际通过；本轮没有新的GUI样本。

后续另准备`tools/control_bitmap_timing.py`，按每次上传汇总DC/DIB准备、memmove、UpdateLayeredWindow及清理时间，不记录像素/坐标或HWND。仅flash模块引用使用代理，共享系统API对象不修改，其他线程继续原调用；`indicator_bitmap_timing=true`必须同时批准健康采样且冻结计时模块摘要，默认不加载。5项假API测试通过；用户明确许可后现场已加载，但在任何有效截图/输入/位图上传前被目标前景及原门禁拦下，故计时功能仍未现场验证。唯一控制链约14分6秒正常全exit0，trace338863行正常关闭dropped0；[本轮结果](control-bitmap-timing.md)记录failed范围，无自动重试。

现场前须先建立具体诊断任务和可审阅计划，并按用户最新要求先说明预计所需时间与操作范围、得到明确许可后再控制电脑。服务启动批准JSON至少包含当前`task_id`、`dispatch_id`、`mode=diagnostics-only`、隔离清单摘要和`launcher_files`；如启用App刷新则额外声明`app_refresh_fix=true`并冻结修复文件。准备命令不会建立MCP、安装钩子或发送输入；serve命令将运行真实控制工具，应遵守用户键鼠授权、拒绝停链、120秒检查间隔、正常退出和进程句柄见证的既有流程。

离线验证使用MCP已有环境：

```powershell
& '<MCP环境>/Scripts/python.exe' -X utf8 -m unittest discover -s tests -p 'test_control_*.py' -v
```

39项测试覆盖原门禁语义和有界日志、缓存旧窗口复现及刷新后的查找/激活失败保护、预算恢复失败后的唯一诊断及禁止继续输入、物理矩形DPI上下文恢复、健康读取顺序和实际采样/阶段日志，以及启动器在加载控制包前拒绝无采样修复、缺少冻结摘要和非布尔选项。另有测试窗三项测试覆盖真实回调记录逻辑、异常堆栈和子进程stdout/stderr捕获。它们使用真实控制器/原Desktop方法及假窗口、假输入API，不安装实际钩子或发送键鼠，也不替代真实小窗口验证。

本机此前四阶段事实见[诊断基线](control-snapshot-diagnostics.md)、[缓存及预算修复验证](control-snapshot-fix.md)、[窗口兼容前置](control-window-compat.md)和[物理矩形单组验证](control-physical-geometry.md)。前两次未进入Snapshot；第三次确认可发现性、App与首图成功，但被客户端DPI坐标检查拦下；第四次真实Click／快捷键后最终图从0/0变为1/1，限定单组通过。所有窗口与控制链均正常exit0，当前没有后台诊断计划。

第四阶段冻结测试窗的逐输入回调日志有重名参数冲突，最终图和原工具调用有效，窗口正常关闭终态也为1/1，但不能把缺失回调行宣称完整输入日志。后续[日志修复组](control-window-logging.md)已使用`tools/control_test_window.py`修复事件名参数并显式保存stdout/stderr，首终图0/0→1/1、两真实回调完整、stderr空，486行trace closed dropped0，所有进程exit0；旧轮缺失原件仍保留。

后续[健康组](control-health-validation.md)首次实际加载采样和先心跳后时间修复，保持原1秒阈值。相同限定GUI组完成、回调/stderr/退出证据完整，247057行trace closed dropped0；5444健康样本中5441健康、3过期，32条慢阶段/状态确认日志及两次fail-open。两次watch判定实际心跳年龄约1.0049和1.0193秒、desktop_ok=true，证明本隔离诊断配置存在真实滞后，未出现伪负年龄不等于长期可靠性已修复。诊断日志高频并有明显开销，不能据阶段时间邻近确定多图层累积、调度、绘制或历史截图根因。历史NET／铜层竞争仍未通过。

受阻时使用精确身份的一次WM_CLOSE让自建Tk程序执行正常关闭回调，仅作生命周期清理，不作GUI输入或验收通过证据，不适用于产品候选或其他工程。
