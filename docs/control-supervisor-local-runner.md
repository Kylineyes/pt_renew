# 本机连续启动监督器

本阶段修正[上一轮启动前300秒超时](control-supervisor-direct-live.md)的编排问题：新增[本机启动器](../tools/control_supervisor_runner.py)，把监督器创建、实际PID核对、持有原生句柄、放行及退出核验放在同一程序中连续执行。所有任务批准、文件摘要和基础解释器探针在创建监督器前完成，10秒子进程握手期间没有代理消息等待，也没有额外outer-driver/worker-holder或300秒外部闸门。

工作分支`fix/control-supervisor-local-runner`基于`dev=2cda5bd`。本轮只运行标准库命令行进程和原生进程查询，没有MCP控制服务、Win32窗口、截图、输入或新现场任务。上一轮failed、晚到放行文件和115项历史测试原件均保留。

## 启动与退出顺序

1. 读取本轮`supervisor-plan.json`和两份批准，核对任务、600/900秒预算、许可确认、方案摘要，以及17客户端和3个监督器模块。要求运行证据目录中的冻结启动器，已有runner/现场状态时拒绝再次启动。
2. 使用基础解释器探针，按监督器实际将使用的解释器核验MCP客户端环境独立性；控制客户端仍显式使用冻结venv解释器。该检查不修改`sys.executable`。
3. 独占创建`runner-start.json`后，通过`WitnessLaunch`直启监督器。子进程先写实际PID、解释器和脚本摘要，尚未运行监督器脚本。
4. 本机立即打开该实际进程查询句柄，核对仍存活并保存创建时间，然后调用release。放行文件先写临时文件再原子改名，子进程不会读到半写JSON。
5. 原Popen等待退出，随后核对同一精确句柄退出码；实际监督器身份、方案摘要、原Popen PID、握手PID、创建时间、链报告必须一致。独立检查子孙记录非空、无重复、每条退出码为0及无capture_errors后，才写`runner-result.json`。

这条流程不需要父代理在短期限内回复。父审阅与Pi任务身份绑定仍在启动之前完成；同一已授权范围无需向用户重复索权。原控制客户端600/900秒预算从其原t0计时，不因启动器增加、延长或重新起算。

## 失败边界

批准缺失、冻结文件变化、方案未绑定启动器或旧状态存在，均在监督器创建前拒绝。独占start文件使同一证据目录不能并发创建两次监督器。持柄失败不会放行子进程；未放行子进程按原10秒期限自行退出，父保留原Popen并等待，不kill、不重启。

非0客户端或监督器退出码写入`runner-error.json`并继续报错，不能只凭chain的verified标记宣称通过。原Popen已经wait完成后若最终审计失败，会复用已取得的退出结果，避免二次wait写覆盖原件。退出状态未知时仍保留pending_launch所有权，不以PID当前不存在替代原退出证明。已放行程序若未退出，只等待原正常生命周期，不通过终止进程来制造成功。

监督器仍以50ms间隔发现子孙，无法排除整个生命周期短于该间隔的未知进程；受控窗口/UIA子进程必须同时保留原Popen回执。该启动器解决已知根监督器的精确退出见证，不声称无限覆盖所有系统进程。

## 验证和冻结

新增[7项测试](../tests/test_control_supervisor_runner.py)，与原115项合计**122项全部通过**。真实但无GUI的集成测试覆盖：从MCP venv调用启动器、基础Python监督器、venv客户端/孙进程、持柄与自动放行、同一PID/创建时间及退出码核对；另覆盖未批准/文件变化拒绝、非0退出保真、持柄失败不放行、最终审计失败不覆盖证据、缺失/重复子孙及错误成功标记拒绝。持柄失败测试实际等待原10秒期限，没有伪造放行或强杀以加速测试。

[测试输出](../.local-analysis/control-supervisor-local-runner/tests-verified.log)保存最后122项通过记录；中间文案断言失败的原输出保留。测试中的所有客户端都是标准库假客户端，没有真实GUI/控制服务，因此不能补作旧现场通过证据。

新冻结候选为`.local-analysis/control-supervisor-local-runner/candidate/`，共110文件：原包77、包清单1、工具12、客户端17和监督器3。三个监督器文件为`control_process_supervisor.py`、`control_witness_launch.py`和`control_supervisor_runner.py`，摘要都绑定在新方案中。见[候选清单](../.local-analysis/control-supervisor-local-runner/candidate-manifest.json)、[方案模板](../.local-analysis/control-supervisor-local-runner/supervisor-plan-template.json)及[离线核验](../.local-analysis/control-supervisor-local-runner/validation.json)。模板尚无Task/Dispatch，不能直接运行。

本轮不再运行旧live。下一组须新建任务和证据目录，将候选client20文件原样复制到新目录，先填好新方案和两份批准、绑定方案SHA，再由指定Pi模型执行下面的单次命令；禁止临时再包一层等待代理回复的短闸门：

```powershell
& '<冻结MCP环境>/Scripts/python.exe' -X utf8 '<新证据目录>/control_supervisor_runner.py' --root '<新证据目录>'
```

命令会阻塞至监督器及子孙正常退出；验收worker须在自己的原Popen后台运行它并持有启动器本身的退出回执，同时用既定单步工具执行自建窗。实际runner若从venv调用仍可能有venv外壳，worker需记录其实际执行PID并持柄，不能只凭外壳退出码替代runner自身；更直接的方式是在启动前用已核验基础Python运行runner，并在同一本机启动操作中保留原Popen。不得把外层runner当成无须见证的隐含层。

用户已授权必要控制验收，下一组先说明15分钟、一个自建窗/连接/组、600秒诊断900秒收尾的范围，使用新Pi gpt-6.1-sol high及新任务批准后执行。真实GUI、资源、健康和全部已知进程退出分别判断；本轮122项通过只证明离线流程，资源适配器的长期稳定性、性能及产品竞争结论保持未通过。稳定产品/dist仍0.10.0，main不动。
