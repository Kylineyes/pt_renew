# 遗留自建诊断窗的独立生命周期收尾

2026-10-29，从`dev=2ad0c9a`建立独立分支`fix/control-residual-diagnostic-lifecycle`。本工作只处理第三候选任务遗留的自建诊断窗；第三候选Task `task_2978396a0432`仍为failed，其关闭工具调用0和子孙原退出码缺口不变。新操作`lifecycle_e727f4cea876`不投递旧inbox、不建立控制连接或诊断组。

`tools/control_residual_lifecycle.py`默认只检查，要求本工具摘要、来源原件摘要和未过期独立方案一致。来源必须是本库的`control_test_window.py`、明确非产品候选、原启动/UIA/绑定一致、关闭未发送、120秒冷却已满、原硬截止保留窗口且trace正常closed/dropped0。目标固定本次原记录PID66968/birth134377322138115927/映像基础pythonw.exe/HWND15010430/标题“PT Renew 控制诊断试验”/类TkTopLevel，不从命令行接收PID。

执行前重新持有只读查询句柄并核对当前完整身份及同名窗口唯一性；独占写入一次机会后再次核验，最多一次定向WM_CLOSE，最多10秒等待同一新查询句柄退出码0。错误、未知、非0或超时均失败，不补发或强杀。工具不激活窗口、不发送键鼠，未要求消失窗口仍保持前景。本工具只适用于已结束且从未发出关闭输入的自建诊断窗，不能用于产品或替代正常`close-owned`验收。

新增7项实质契约测试及原控制回归共149项全部通过，16.796秒，见[测试输出](../.local-analysis/control-residual-lifecycle/tests-offline.log)。假API覆盖默认只检查、一次成功、重复请求、权限/期限、身份变化、唯一性、已经退出、临近发送变化、拒绝/未知/取消/超时/非0、冻结来源与产品/服务/冷却约束。测试没有访问桌面或发送WM_CLOSE，既有进程链测试只启动无GUI子进程。

已完整复制实际旧执行目录157文件到本次`source-before`，核对摘要一致；冻结本工具/ProcessApi/诊断窗源码到新目录。见[独立方案](../.local-analysis/control-residual-lifecycle/plan.json)、[全部只读基线](../.local-analysis/control-residual-lifecycle/readonly-before.json)和[只检查回执](../.local-analysis/control-residual-lifecycle/inspect-result.json)。冻结主模块SHA-256 `7a293f7fdd6e25b007e289d9a29c472178275ae8d938d1cb3a9705a1777c1bc2`。只检查已确认精确身份仍活、同名窗唯一，发送计数0。

实际于18:14:27（UTC+08:00）执行，工具进程返回0；只向上述精确自建窗发送一次正常关闭消息，并在10秒上限内由同一新查询句柄取得退出码0。用户已持续明确授权必要控制电脑，本次继续指令涵盖此前报告中的遗留收尾，无需重复索权。原failed/token与旧验收结论未改；窗口自身在原已打开日志自然追加normal-close/mainloop-returned，原日志已先完整备份。

本次退出证明明确标为晚到精确查询句柄，不是原Popen，不恢复已结算Task或监督器。[独立审计](../.local-analysis/control-residual-lifecycle/independent-audit.json)核对唯一WM_CLOSE、同句柄exit0及原窗口两条自然回调顺序，计数保持1/1；旧窗口日志原476字节前缀逐字节不变，原执行目录157文件中仅window-events.jsonl追加，其余文件及全部冻结/旧验收归档/产品摘要不变。新增来源备份保留全部发送前原件。只读进程查询当前未发现该PID只是辅助观察，退出结论来自本次持柄回执。[执行回执](../.local-analysis/control-residual-lifecycle/execute-result.json)和[事件日志](../.local-analysis/control-residual-lifecycle/execute-events.jsonl)保持原件。

本次独立生命周期通过，遗留自建窗已退。第三候选failed、专用Alt+F4关闭未验证、原子孙退出码缺口、长期稳定性及固定0.11.0/NET/铜竞争边界保持。下一步可以使用此前监督器快照修复后的111文件候选另立全新有界验收，先准备可审阅材料和具体时间范围，不能复用旧Task/inbox/批准/预算。
