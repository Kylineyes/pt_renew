# 初始目标激活：补齐窗口启动到首图之间的前景步骤

本轮仅离线读取代码与既有JSON/日志、开发流程辅助模块并使用假窗口/假工具测试，没有启动控制服务、GUI、原生桌面检查、截图或输入。新增[control_target_activation.py](../tools/control_target_activation.py)及[8项定向测试](../tests/test_control_target_activation.py)。模块尚未现场接入，不能声称前景问题已修复或取得位图样本。

上一[15分钟尝试](control-bitmap-retry.md)的两份原生记录显示：Launch前`864520.0220823`前景为PID23024/HWND333150的Orca，此时无目标；首图前`864523.5246169`前景仍为同一Orca，目标PID20332/HWND7276816已在窗口列表。二者都记录前景稳定、Default输入桌面。记录没有覆盖所有中间前景变化，不能证明目标从未短暂前景或是哪一步夺焦点，更不能归因用户。

离线代码审查发现可操作的流程缺口：

- `control_test_window.launch_window`只调用Popen创建进程；Tk显示窗口没有承诺目标成为前景。
- 独立UIA探针只核验身份、可缩放属性及原工具枚举，明确activation_calls=0/input_calls=0。
- `Step.ps1`把单步驱动交给pythonw，但UIA探针是另一个Python控制台程序。其是否造成现场焦点变化没有直接证明。
- 原Guard在Launch前检查输入桌面，Launch后只绑定目标；首Snapshot才要求目标已在前景。旧失败后restore_target有App激活，但先要ControlStatus允许；此前一组在该门禁处受阻，最新一组按范围首拒绝即停，均没有原App调用。

因此当前流程把“窗口已经创建/可枚举”误当作“首图时已在前景”的前置假设。修正应在首次失败之前明确做一次初始化激活，仍由原工具决定是否允许。它不降低Snapshot/键鼠原有目标归属检查。

新辅助模块执行顺序：未失败且无并发的已绑定目标→UIA前置完成、组数0、当前token和唯一ID→原native只读检查Default桌面/稳定前景/唯一标题及PID、创建时间、HWND、映像、类→原`guard.raw('App', mode='switch', name=指定自建标题)`→原`guard.observe_native()`精确前景后验→推进token。激活前当前前景可以是其他窗口，这是App切换的用途；随后原Snapshot检查保持不变。原App内部仍走原ControlToolGate及Windows前景校验，不直接调用SetForegroundWindow、不输入辅助按键、不修改第三方安装。

每个辅助实例至多一次尝试。门禁/工具传输结果不确定记executed=unknown，不重发；App成功返回但精确前景后验失败记动作已执行、组未完成。失败锁存当前ID、清本次诊断token并保持已有退避截止，原层尚未设置退避时按原guard.retreat设置120秒；不清旧failed、集合或心跳，不自动resume。失败的前置调用不会发送App，仍消费本次初始激活机会。8项测试涵盖非目标前景初始化、后验不通过、PID/birth/HWND/映像/类/唯一性、锁屏/不稳定、原门禁及传输异常、旧token/重复/并发/已开始组、120秒截止和保持集合不改。

客户端下一次接入应增加独立`initial-activate`请求，只能在Launch与UIA后、begin-group前由新批准显式启用；导入并校验本模块摘要，结果失败即停止。不得把新入口用于旧失败Task/Dispatch、旧PID或一般产品窗口。原预算和控制服务不改，不能在拒绝后调用该入口救活已失败组。未获用户新桌面许可前，不启动任何现场来验证它。

[待许可15分钟方案](control-target-activation-plan.md)已明确一次App初始化及其前后身份检查。本次没有运行GUI验证，也没有产品代码/版本/dist改动；稳定0.10.0、固定0.11.0和NET/铜竞争未通过状态保持。
