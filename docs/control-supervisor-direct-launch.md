# 直启监督器接入与新候选

基于`dev=fb02245`，本阶段在独立分支`feat/control-supervisor-direct-launch`把[见证器直启工具](control-witness-launch.md)接入[标准库监督器](../tools/control_process_supervisor.py)，并冻结全新候选。上一轮[现场](control-bitmap-surface-live.md)的failed与缺失监督器退出码保留，不用新工具补造旧证据。

监督器自身由`WitnessLaunch`使用基础Python直启。目标脚本在原Popen PID、实际PID、基础解释器与脚本摘要握手一致后才运行；自身退出码由父原Popen.wait取得。监督器单独记录实际PID及创建时间，最终须与该Popen退出回执对应。启动控制客户端时，明确使用方案中的MCP venv解释器，不使用监督器自身sys.executable替代控制环境。

监督器在启动前核对本轮两份批准、新任务/派发、600/900秒预算及方案摘要，逐份核验17客户端文件和监督器/直启器源码。已有runtime-limits、live-state、监督器身份或退出原件会拒绝启动，不覆写或重置旧现场。子孙账本仅从仍有精确句柄的本链父进程发现子进程；开柄后核验创建时间，拒绝早于父进程的身份，退出码只由持柄查询取得。

任何已发现但未成功持柄的进程都会记录capture_errors并阻止完整通过。50ms轮询不能排除整个生命短于采样间隔的未知进程，因此窗口/UIA等受控短命进程还必须保留原Popen回执，不能宣称仅靠枚举覆盖所有进程。监督器不调用桌面、不结束进程、不重发输入或重启连接。到原客户端900秒截止后仅保留只读退出观察，不延长桌面许可。

新增[5项测试](../tests/test_control_process_supervisor.py)包含乱序子孙发现、非0退出保留、PID复用/查询失败拒绝、旧状态/错误批准拒绝，以及真实无GUI集成：基础Python直启监督器、显式venv启动客户端、实际孙进程、精确PID与原Popen一致、所有已记录退出码为0。该测试使用标准库假客户端，不创建Win32窗口、MCP服务、截图、输入或钩子。**相关仓库测试115项全部通过**，见[测试输出](../.local-analysis/control-bitmap-surface/tests-with-direct-supervisor.log)。

新候选位于`.local-analysis/control-supervisor-direct-launch/candidate/`，共109文件：原控制包77、包清单1、工具12、客户端及监督器19。候选与[清单](../.local-analysis/control-supervisor-direct-launch/candidate-manifest.json)独立于上一轮candidate-final/live，旧原件均不修改。[监督器方案模板](../.local-analysis/control-supervisor-direct-launch/supervisor-plan-template.json)尚无Task/Dispatch，不能直接运行。实际运行前将本轮新身份填入方案，再将方案SHA-256绑定客户端和服务批准。

用户已经授权必要控制验收。若安排下一组，范围仍限15分钟一个自建窗/一连接/一组双图和双回调，诊断600秒、收尾900秒，启动前说明范围并绑定新Task/Dispatch/Pi gpt-6.1-sol high实际模型证据；原1秒健康阈值、完整显示后心跳、真实拒绝后120秒零桌面请求均保持。不复用上一轮失败状态、许可文件、inbox或截止，不在失败后追加第二组。GUI、正常资源寿命、本组健康、监督器自身及客户端子孙的退出分项报告，单组成功仍不证明长期稳定性或性能倍率。
