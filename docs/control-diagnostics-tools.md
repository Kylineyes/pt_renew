# 控制诊断工具：当前能力、验证与使用限制

当前稳定产品/dist为0.10.0。[本机连续启动器](control-supervisor-local-runner.md)已实现预检、持柄与自动放行，离线122项通过，新候选110文件，尚无新桌面验证。本轮[直启监督器接入](control-supervisor-direct-launch.md)离线115项通过，但[启动前尝试](control-supervisor-direct-live.md)因300秒外部门超时failed，服务/GUI均未启动，没有新现场样本。工具在独立控制包副本中提供取证；[资源复用实验](control-bitmap-surface.md)默认关闭，后续[真实现场](control-bitmap-surface-live.md)完成双图/双回调、7寿命8509上传及零账本，但整体Task因监督器66568缺独立精确退出记录而failed。1188健康样本全healthy仅为本组结果；[退出见证修正](control-witness-launch.md)已离线完成，尚未追加现场。产品和已安装第三方包未修改。最新[限定现场](control-initial-activation.md)的一次原App初始化/精确前景后验、单组图0/0→1/1/双回调/空stderr及4081上传取证通过；2883健康样本仍含2次真实过期、1次fail-open，控制稳定性及历史全部截图根因未解决，固定0.11.0/NET铜竞争未通过。

## 工具和开关

| 文件 | 行为 | 验证边界 |
| --- | --- | --- |
| `tools/run_control_diagnostics.py` | `prepare`复制windows_mcp并逐文件验SHA生成manifest；`serve`复验包、Task/Dispatch/mode、manifest和launcher摘要后调用原MCP/ControlToolGate | prepare不创建控制链/钩子；serve会启动真实控制服务。资源实验还要求新许可确认/消息/600与900秒预算、健康条件和已核验源码版本 |
| `tools/control_diagnostics.py` | 原方法包装追加阶段/原因/status diagnostics，保留原拒绝/异常/输入账本/接管/保持集合，队列有界、独立线程写日志，closed记录dropped | 非原子快照、日志开销影响调度；不记录用户字符或按键值，丢失/写错不能宣称完整因果 |
| `tools/control_app_refresh.py` | 原switch_app前刷新窗口缓存，继续原窗口过滤/查找/激活/前景后验 | `app_refresh_fix=true`且冻结模块才加载；不改变CanMinimize/CanMaximize枚举要求，不解释全部历史not found |
| `tools/control_diagnostic_budget.py` | 恢复失败联动refused，停止组，保留冻结一次只读诊断/观察供收尾 | 客户端须调用restored(row)；不能自动重发输入，也不能替已拒绝的组记通过 |
| `tools/control_geometry.py` | 临时PER_MONITOR_AWARE_V2读取物理rect并finally恢复原线程DPI上下文 | 未知/无效/恢复失败拒绝，无激活或窗口移动；不能直接将逻辑rect与物理点比较 |
| `tools/control_indicator_health.py` | 每次记录判定实际alive/stopping/error、now/heartbeat/age、顺序与返回值；记录当时可见阶段和完成的慢阶段/异常 | `indicator_health_sampling=true`默认保持clock-first；另`indicator_health_fix=true`才heartbeat-first，必须同时采样；保留原1秒及故障拒绝 |
| `tools/control_test_window.py` | 真实Tk按钮/快捷键回调计数及逐行pid/monotonic/counts；显式stdout/stderr，异常原堆栈 | 修正旧event参数与输入kind冲突；仅测试窗，不用程序接口更新图冒充现场键鼠 |
| `tools/replay_control_health.py` | 纯JSONL离线重放，按相同旧heartbeat归并过期区间，裁剪阶段并集，分开事后完整/当时可见覆盖 | 不导入控制包，拒绝未正常closed、丢失、矛盾/拼接日志；区间墙钟不是CPU归因 |
| `tools/control_bitmap_timing.py` | flash模块局部API代理，仅指示层线程上传范围每次汇总尺寸/字节、API次数/墙钟耗时/异常 | `indicator_bitmap_timing=true`需同时批准健康采样、冻结模块摘要；共享ctypes/WinDLL对象不改，不记录像素/坐标/HWND |
| `tools/control_target_activation.py` | 未失败、已绑定/UIA核验目标、组前最多一次原App switch；激活前精确身份/桌面检查，后调用原前景后验 | 客户端独立批准并冻结模块摘要；不直接原生激活、不额外ControlStatus、不清锁存/集合，不在旧失败组补激活或重试 |
| `tools/analyze_control_uploads.py` | 纯JSONL分析上传发出延迟、采样点裁剪与API集合占时边界；复用健康重放 | 正常schema 1上传专用，需核验同线程/同一时钟/心跳写入路径；上下界不是CPU或预计提速 |
| `tools/control_bitmap_surface_model.py` | 后端注入的不可变图层寿命核心，验证一次创建/复制、逐次完整上传与失败退役 | 模块本身不加载Win32；原生适配器在单独模块，部分失败实例保持可退役 |
| `tools/control_bitmap_surface.py` | 私有WinDLL、图层线程上下文接管、DC/DIB账本和所属线程退役，64图层/64MiB预算 | `indicator_bitmap_surface=true`且冻结核心/适配器才安装；需健康采样/修复，和旧bitmap计时互斥；runtime_verified=false |
| `tools/control_surface_approval.py` | 纯离线核对新客户端/服务批准、真实Pi模型、新目录和冻结文件/包集合；附加资源日志前置检查 | 不是许可来源；旧Task/会话/状态拒绝，不启动桌面 |
| `tools/audit_control_surfaces.py` | 正常surface JSONL独立寿命/API/账本审计，拒绝矛盾/异常/缺失退役 | 本次7寿命8509上传内部证据通过；不替完整进程退出或性能/健康 |
| `tools/control_witness_launch.py` | 基础Python直启标准库见证脚本、实际PID/摘要/解释器握手后显式放行、原Popen等待 | 修复venv外壳与实际进程身份缺口的离线工具；4项命令行测试 |
| `tools/control_process_supervisor.py` | 显式MCP环境启动客户端、核验冻结方案与新批准、精确子孙账本 | 5项无GUI测试；本次现场在其启动前超时，尚无实际监督器现场退出验收 |
| `tools/control_supervisor_runner.py` | 本机连续完成全部批准预检、实际PID持柄、原子放行及原退出码审计，不等待代理回复 | 7项无GUI测试；新候选110文件，真实GUI仍待验证 |

所有可选运行时包装默认不启用，只在冻结并明确批准的新隔离进程中加载；服务启动后不热改。客户端Task批准与桌面许可是不同证据，批准文件不能替代用户对操作时间/范围的许可。

健康短路未执行的时间/heartbeat读取字段为空，不能用事后controller_fields快照代替原判定字段。`indicator-phase`在完成耗时至少50毫秒或异常时写入；健康行中的phase是当时线程可见关联，非原子，空值不说明线程没有工作。先heartbeat后now仅修伪负年龄，不能消除真实停更。

位图记录汇总GetDC、CreateCompatibleDC、CreateDIBSection、memmove、SelectObject、UpdateLayeredWindow、DeleteObject、DeleteDC、ReleaseDC。最新4081正常路径每上传SelectObject2次、其余各1，尺寸/字节/总成本一致且异常0；未执行的异常路径不能称为现场覆盖。分段耗时含调度/诊断开销，API外差值不能解释为CPU时间，不能按全场百分比直接确定超时根因。

初始激活客户端已现场验证顺序：Launch→UIA→initial-activate（原App一次及精确前景后验）→begin-group→首Snapshot→Click→诊断Shortcut→终Snapshot。Popen/窗口显示/UIA枚举都不保证前景，初始ready日志观察也不保证目标前景；目标检查不能删除，失败不自动激活救活旧链。实际最新client/step位于本机验收证据目录，未提交的旧模板含身份占位，不能直接运行。

## 离线验证与隔离准备

最后实际`tests/test_control_*.py`为**122项全部通过**，证据主`.local-analysis/control-supervisor-local-runner/tests-verified.log`（115项加本机启动器7项）。此前115项证据主`.local-analysis/control-bitmap-surface/tests-with-direct-supervisor.log`保留，此前110项在`tests-with-witness-fix.log`保留，原106项证据保留在`tests-verified.log`，其新增27项为原生/原循环17、启动器6、客户端批准4。冻结客户端另6项定向离线检查在同目录`frozen-client-tests-final.log`，不混入仓库覆盖。上一阶段79项证据`.local-analysis/control-upload-offline-analysis/tests-verified.log`、原61项证据`.local-analysis/control-target-activation/tests.log`保留。它们使用真实控制器/原Desktop方法加假窗口/输入API，覆盖原拒绝账本、日志、缓存、预算、几何、健康、启动开关、测试窗、重放、位图计时及初始激活。测试不安装真实钩子或发送输入；测试窗stderr测试仅运行命令行异常子进程。与工作者本机截止/初始观察定向测试不重复累加，不替产品CTest/GUI。

```powershell
& '<MCP环境>/Scripts/python.exe' -X utf8 -m unittest discover -s tests -p 'test_control_*.py' -v
& '<MCP环境>/Scripts/python.exe' -X utf8 tools/run_control_diagnostics.py prepare `
  --source '<MCP环境>/Lib/site-packages/windows_mcp' `
  --destination '.local-analysis/<新任务>/isolated'
```

使用已有MCP解释器，避免全局Pillow/NumPy兼容问题，不修改原安装或重复安装依赖。副本/manifest/trace/截图/第三方源码都在Git忽略目录，不入Git。

serve批准至少含`task_id`、`dispatch_id`、`mode=diagnostics-only`、`package_manifest_sha256`、`launcher_files`。加载App刷新/健康/位图时显式声明上述开关并冻结对应模块。客户端还须冻结自身、几何/激活摘要、绑定精确目标、预算、截止与用户许可；在新的Task/Dispatch/目录运行，不复用旧inbox/失败状态/PID。

## 现场证据入口

| 报告 | 已验证范围与限制 |
| --- | --- |
| [基线](control-snapshot-diagnostics.md)、[缓存/预算](control-snapshot-fix.md) | 两次failed，未进有效截图/输入；保留原App/预算失败证据 |
| [窗口兼容](control-window-compat.md)、[物理矩形](control-physical-geometry.md) | 前者UIA/App/首图通过但本地DPI拒绝；后者图1/1限定通过，旧逐回调日志缺口保留 |
| [日志修复](control-window-logging.md) | 完整双回调/空stderr/终态/正常退出，486trace dropped0 |
| [健康采样](control-health-validation.md)、[离线重放](control-offline-replay.md) | 5444样本3stale/2fail-open；两旧心跳区间阶段并集覆盖90.61%/93.14%，不能直接归因全场hook/input |
| [位图首次](control-bitmap-timing.md)、[user时间线](control-user-timeline.md) | 实际图/输入/上传0，门禁user有最近事件续期证据，服务曾ready，来源未知 |
| [前景重试](control-bitmap-retry.md)、[初始激活设计](control-target-activation.md) | 前者首图前景Orca/实际call0；后者离线补齐组前激活，不能反推UIA或用户夺焦点 |
| [最新初始激活现场](control-initial-activation.md) | 原App1/两有效图/双回调/4081上传，7384trace dropped0，全exit0；健康2stale/1fail-open仍存在 |
| [最新上传离线分析](control-upload-offline-analysis.md) | 同旧心跳的局部上传/阶段并集与API占时边界、假API寿命模型完成；该阶段无新现场 |
| [原生资源实验](control-bitmap-surface.md) | 适配器/图层接入/独立审计及候选冻结完成；历史离线106+单独6项通过 |
| [资源复用现场](control-bitmap-surface-live.md) | 单组GUI/8509正常上传/零账本和本组健康有效；整体failed，66568缺精确退出码，不推导性能或稳定修复 |
| [退出见证直启修正](control-witness-launch.md) | 4项无GUI进程测试通过，已归档3个闲置agent窗格，旧原件保留，无追加现场 |

## 操作约束

控制电脑前说明预计用时及范围。用户本次已明确授权控制，并补充必要控制验收允许执行；已授权范围不重复索权，但已结算组的预算不重置，不自动追加轮次。正常键鼠不额外ControlStatus预检，所有动作仍经原ControlToolGate和精确目标归属。首次真实拒绝按冻结预算终止，120秒内零输入/截图/状态/原生桌面请求，到期只按计划收尾或有界恢复，不循环追逐ready。

Snapshot必须有image并实际读图；动作已执行但后图失败只能补观察，不重发。Alt+F4已执行后窗口消失的保守锁存保持，凭原Popen exit0退役，不再发关闭。精确自建Popen一次WM_CLOSE仅正常生命周期、不计GUI通过，不适用于产品/其他工程进程，无强杀。不得改活内存/清集合/放宽1秒阈值/关闭指示层/中途续心跳或换入口绕拒绝。
