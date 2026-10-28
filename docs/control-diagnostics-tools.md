# 控制工具隔离诊断与App窗口缓存修复

PT Renew的真实GUI验收多次在编辑后的截图阶段遇到控制拒绝。新增工具用于在独立控制包副本中保留拒绝原因和真实调用轨迹；它不修改PT Renew或已安装控制工具，也不把日志替代有效GUI图像。稳定产品保持0.10.0，固定0.11.0候选验收状态不因工具测试改变。

`tools/run_control_diagnostics.py`先复制本机已安装的`windows_mcp`包，核验原包与隔离副本每个文件的SHA-256，生成清单。运行阶段复验清单、当前任务身份和启动器摘要，确认实际导入来源是独立副本后，调用原MCP服务及其ControlToolGate。复制包、诊断日志、截图和清单均放在Git忽略目录，第三方包源码不提交。

`tools/control_diagnostics.py`包装原控制器方法并继续调用原实现，只向状态附加`diagnostics`并记录阶段。原`state`、`generation`、`wait_seconds`、拒绝代码、异常及保持键集合不被清理或重置；1秒心跳阈值、接管、截图暂停和输入账本原语义不变。低层记录只有消息类别和injected标志，不保存键值、字符或输入文字。队列有界，磁盘由独立线程写入，正常关闭记录`trace-closed`及丢失数量；存在丢失或写入失败时不能声称有完整因果证据。

可观察字段包括截图暂停/恢复、调用开始/结束、控制状态变迁、物理事件处理类别、指针API阶段、fail-open调用点、控制/指示线程心跳年龄与状态。fail-open只记录看门狗已经求值的健康布尔，不额外触发健康检查。字段为非原子只读快照，诊断开销也可能改变调度时序；单次时序邻近或没有复现都不证明历史原因。

新增`tools/control_app_refresh.py`针对一个可离线复现的问题：原`Desktop.switch_app`只在窗口缓存为空时更新列表，已有非空旧列表会遗漏后来新建的窗口并返回not found。修复在原switch_app前调用get_state刷新，随后仍由原模糊查找、激活和前景后验决定成功；刷新失败、目标不存在或Windows拒绝激活都仍失败。该修复默认不加载，只有新进程的明确批准`app_refresh_fix=true`且摘要包含该文件才启用。它只解决缓存旧列表的问题；原`get_windows`还要求UIA窗口支持最小化和最大化，不支持最大化的窗口可能仍被过滤，刷新不会改变这一枚举规则。离线真实枚举方法的假控件复现已确认该边界，现场是否由此触发仍需对应UIA属性直接取证。不能热改正在拒绝操作的服务，不能以此跳过ControlToolGate，更不能称它修复了历史截图错误。

`tools/control_geometry.py`在临时线程`PER_MONITOR_AWARE_V2`上下文读取物理窗口矩形，最后恢复原线程上下文。它解决诊断客户端把DPI虚拟化的逻辑窗口矩形与Snapshot物理点击坐标直接比较的问题，未知上下文、无效矩形或恢复失败都拒绝结果，不移除边界检查、不激活或改变窗口。6项假Win32测试覆盖物理点、读取/上下文失败及恢复路径。

`tools/control_indicator_health.py`提供尚未默认加载的心跳读取修正。原表达式先取当前时间再读并发更新的heartbeat，可在两次读取之间产生伪负年龄；离线顺序复现已确认。修正先固定heartbeat再读当前时间，保持原1秒阈值、过期/未来心跳及停止/故障状态拒绝，5项测试通过。它不能解释全部真实心跳滞后或历史截图故障；没有现场加载证据时不得称可靠性修复已验收。

`tools/control_diagnostic_budget.py`用于诊断驱动的受限动作预算。驱动在专用目标恢复返回后须调用`restored(row)`；失败立即终止诊断组，保留一次只读诊断和观察用于收尾。它修复了基线中恢复失败未联动预算、导致diagnose在到达MCP前被本地断言拦下的缺口。失败后不会继续点击探测，已执行关闭也不会被自动重发。

隔离包准备示例，使用已有MCP环境的Python，避免系统Python的Pillow二进制版本不一致：

```powershell
& '<MCP环境>/Scripts/python.exe' -X utf8 tools/run_control_diagnostics.py prepare `
  --source '<MCP环境>/Lib/site-packages/windows_mcp' `
  --destination '.local-analysis/control-diagnostics/isolated'
```

现场前须先建立具体诊断任务和可审阅计划。服务启动批准JSON至少包含当前`task_id`、`dispatch_id`、`mode=diagnostics-only`、隔离清单摘要和`launcher_files`；如启用App刷新则额外声明`app_refresh_fix=true`并冻结修复文件。准备命令不会建立MCP、安装钩子或发送输入；serve命令将运行真实控制工具，应遵守用户键鼠授权、拒绝停链、120秒检查间隔、正常退出和进程句柄见证的既有流程。

离线验证使用MCP已有环境：

```powershell
& '<MCP环境>/Scripts/python.exe' -X utf8 -m unittest discover -s tests -p 'test_control_*.py' -v
```

27项测试覆盖原门禁语义和有界日志、缓存旧窗口复现及刷新后的查找/激活失败保护、预算恢复失败后的唯一诊断及禁止继续输入、物理矩形DPI上下文恢复，以及指示层健康读取顺序的并发假阴性。它们使用真实控制器/原Desktop方法及假窗口、假输入API，不安装实际钩子或发送键鼠，也不替代真实小窗口验证。

本机两阶段事实和实际调用结果分别见[诊断基线](control-snapshot-diagnostics.md)与[缓存及预算修复验证](control-snapshot-fix.md)。两次窗口和控制链均已正常退出，未进入Snapshot；其失败不能写成截图阶段已复现。收尾用精确身份的一次WM_CLOSE让自建Tk程序执行正常关闭回调，仅作生命周期清理，不作GUI输入或验收通过证据，不适用于产品候选或其他工程。
