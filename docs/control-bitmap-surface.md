# 不可变图层资源复用：原生适配器与待许可现场候选

本阶段完成默认关闭的Win32适配器、原`_Layer`生命周期接入、独立资源审计及客户端批准检查。**离线验证通过，真实Win32上传、GUI表现和性能尚未验证，`runtime_verified=false`。** 稳定产品/dist保持0.10.0；控制稳定性、固定0.11.0和NET／铜完整竞争结论均保持未通过。

分支`feat/control-bitmap-surface`从`dev=705c239`建立。依据[上一阶段的局部成本边界](control-upload-offline-analysis.md)实施最小实验。本轮没有启动GUI、真实控制服务或钩子，没有截图、输入或恢复旧Pi会话，也没有创建新Task/Dispatch或生成有效桌面批准。

## 实现与失败边界

[适配器](../tools/control_bitmap_surface.py)通过原构造和`set_opacity`调用期间的线程局部上下文接管`flash_overlay._push_bitmap`。原图层构造、透明度去重、显示/隐藏、光标移动、显示器枚举、模式切换和消息泵继续执行；其他线程或上下文外的flash上传调用原路径。安装发生在健康阶段包装之前，使健康阶段可以观察新上传路径。安装拒绝已启动的指示层、重复安装及旧位图计时包装。

每个图层对象独占一个surface，由[寿命核心](../tools/control_bitmap_surface_model.py)管理。原始不可变bytes只复制一次，尺寸/像素对象/目标变化必须沿原代码关闭并重建；不按尺寸或HWND建立跨寿命缓存。已退役对象禁止重新初始化或上传，即使出现相同句柄值也不复用。每次上传保留GetDC→完整UpdateLayeredWindow→ReleaseDC；不在中途写心跳或显示确认。

原生后端使用私有`WinDLL(..., use_last_error=True)`函数对象，明确设置返回类型与参数，不改共享`ctypes.windll`或原模块函数的签名。失败返回在计时/下一次API前保存错误码；GDI错误码可能为0，仍按API失败处理，不把错误码0当成功。

| 路径 | 实现行为 |
| --- | --- |
| GetDC/CreateCompatibleDC/CreateDIBSection失败 | 检查空句柄，回收此前已取得的资源 |
| DIB句柄成功、bits为空 | 先把有效句柄交给寿命核心，再拒绝复制并退役，不丢弃部分结果 |
| SelectObject失败 | 拒绝0、-1及指针宽度的HGDI_ERROR；不把失败当成有效旧对象 |
| 正常上传 | 保留top-down 32位DIB、原BGRA、原位置/尺寸、整窗opacity和per-pixel alpha参数 |
| 恢复选择失败 | 报错并锁存；先删除DC解除选择，再删除位图，不删除仍被选中的位图 |
| 恢复选择和DeleteDC同时失败 | 保留选中关系及句柄，所属线程后续只做退役，不再上传 |
| 构造失败且清理失败 | 异常`pending_surface`及管理器强引用保留资源所有者，避免构造未返回就遗失句柄 |
| DeleteObject/DeleteDC/ReleaseDC失败 | 账本只在API成功后扣除；失败剩余句柄保持，不清零冒称释放 |
| 图层关闭 | 资源退役成功且窗口身份仍相同，才调用原窗口关闭；身份变化不销毁其他窗口 |
| 所属线程退出 | 独立遍历全部待退役图层，一层失败也继续处理其他层，保留原错误和失败锁存 |
| 服务退出 | 主线程只审计；资源余额非0或实验曾失败均拒绝声明通过，trace仍关闭 |

资源操作必须在创建线程执行。实验上限为64个surface、64MiB DIB像素估算；超过上限先拒绝新分配并锁存失败。该字节预算不等于进程总内存，也不包含已有Python像素、DC开销及合成器分配。资源账本覆盖屏幕DC、内存DC、DIB、选择关系及图层寿命；真实窗口与进程退出仍须精确句柄见证，不能由账本替代。

## 启动批准与诊断记录

[启动器](../tools/run_control_diagnostics.py)新增`indicator_bitmap_surface`，缺省为false。只有以下条件全部满足，才会在新隔离进程中安装实验：

- 选项为布尔true，同时批准实际健康采样和heartbeat-first读取修复；1秒阈值保持。
- 冻结启动器、诊断、健康、原生适配器和寿命核心模块摘要。
- 原`control_overlay.py`与`flash_overlay.py`恰为已核验版本；完整包文件集合及摘要匹配。
- 明确设置本轮`permission_confirmed=true`、许可文字、批准消息及600/900秒预算。有效Task/Dispatch仍为必需项。
- `indicator_bitmap_timing=false`，避免旧`_push_bitmap`计时把复用路径记录成空API集合。本轮资源操作自行记录完整分段。

资源日志使用`indicator-surface-installed`、`indicator-surface-operation`、`indicator-surface-owner-exit`和`indicator-surface-shutdown`。每项操作记录独立surface序号、尺寸/字节、真实started/finished、API次数/失败数/墙钟耗时及账本快照；不记录HWND、坐标、opacity、像素内容或用户文字。初始化、上传与退役分开记录，上传失败的清理仍归入该次失败操作。

[独立离线审计](../tools/audit_control_surfaces.py)逐寿命重算正常API集合和资源余额，拒绝缺失上传、复用身份、次数/时间矛盾、异常、非零账本、退出后操作和未正常closed/dropped0的输入。它只证明正常记录内部一致，不证明真实图像或性能。原健康日志仍可由`replay_control_health.py`重放；旧`analyze_control_uploads.py`专门解释旧位图schema 1，不能用于新surface日志。

## 离线验证与冻结候选

仓库`test_control_*.py`共**106项通过**（上一阶段79项加本轮27项：原生/原循环17、启动器6、客户端批准4）。冻结客户端另有**6项定向离线检查通过**，单独记录，不相加冒称产品覆盖。测试使用假API、假窗口及从摘要匹配的原源码提取的类/循环，没有运行真实原生窗口。

覆盖包括原生0/空返回/HGDI_ERROR、DIB部分成功、恢复/释放失败、所有权保留、预算、关闭后句柄复用、错误窗口拒绝、像素/alpha/位置参数、逐次完整上传，以及原显示循环的几何变化/模式切换/停止。假循环验证上传期间heartbeat/applied不提前推进，失败时不补确认、不重发。启动测试验证缺省关闭、导入前拒绝、安装顺序、服务退出审计与trace收尾；定向客户端检查缺许可前置、35秒请求余量、900秒空闲截止、关闭机会消费及被动日志条件。

本机候选目录为`.local-analysis/control-bitmap-surface/candidate-final/`，冻结107文件：隔离包77、包清单1、工具12、客户端17。客户端绑定10个运行工具，另外两个离线审计工具也在候选清单中。旧`candidate/`和`candidate-v2/`是中间版，保留原件，后续仅使用v2及其清单。主工作区Git切换不会修改这些已复制的冻结工具。

| 本机证据 | 内容 |
| --- | --- |
| [候选清单](../.local-analysis/control-bitmap-surface/candidate-final-manifest.json) | 107文件摘要，尚无许可或Task/Dispatch绑定 |
| [候选计划](../.local-analysis/control-bitmap-surface/candidate-final/client/plan.json) | 唯一窗口/连接/组、操作顺序、截止和失败收尾 |
| [仓库测试](../.local-analysis/control-bitmap-surface/tests-verified.log) | 106项 |
| [冻结客户端测试](../.local-analysis/control-bitmap-surface/frozen-client-tests-final.log) | 独立6项 |
| [假API独立审计](../.local-analysis/control-bitmap-surface/fake-api-audit-final.json) | 明确标记fixture_only，5寿命/10上传，不是现场证据 |
| [完整性核对](../.local-analysis/control-bitmap-surface/validation-final.json) | 测试源码与冻结副本一致；原控制包77/旧隔离77、部署22/23/22集合及摘要不变 |
| [服务批准模板](../.local-analysis/control-bitmap-surface/server-approval-template-final.json)、[客户端批准模板](../.local-analysis/control-bitmap-surface/client-approval-template-final.json) | ID/消息/许可为空，permission_confirmed=false，不能直接运行 |

原安装、隔离副本、截图/日志/模型材料和部署均不提交Git；没有改写已安装第三方包或冻结产品。复制/摘要验证是离线准备，不是新现场通过。

## 待许可的单组现场方案

预计控制范围为**15分钟**：自服务启动计时，诊断最多600秒，正常退出余量至900秒。所有新请求预留至少35秒；初始化、工具RPC及UIA探针的等待上限35秒。客户端900秒空闲截止会停止请求并明确报告尚未退出的自建窗口，不伪造退役，不自动延期、重连或强杀。

收到用户对时间和范围的新明确许可之后，才创建新Task/Dispatch、独立验收分支和证据目录，由Pi的`gpt-6.1-sol high`执行；实际PI环境、JSONL及工具记录必须核对。本机候选已预分配未来验收目录`.local-analysis/control-bitmap-surface/live/`，当前仅有空inbox，无批准/状态。获得许可并绑定新身份后复制冻结客户端的17文件至该目录；候选源目录保持不变。`server-approval.json`与`phase-two-approval.json`只放live目录。[批准检查](../tools/control_surface_approval.py)要求新会话、实际环境匹配、目录内无live-state/runtime-limits/client-fatal旧状态，不能使用旧任务、旧PID或旧15分钟许可。

单组顺序为：

1. 只读新链日志观察10至60秒，核对原ready、健康、保持集合及唯一资源安装记录；资源曾失败则终止，不创建窗口。
2. 启动一个自建诊断窗，UIA核对后，原App初始激活最多一次并验证精确前景。
3. 首Snapshot实际读图0/0；按钮Click一次，Ctrl+Shift+F8一次；终Snapshot实际读图1/1并核对双真实回调。正常两图，总截图上限4，不重发输入。
4. 正常Alt+F4最多一次，凭原Popen退出证明退役，再停止服务；独立审计资源/健康/回调及全部精确控制链exit0。

正常动作不加ControlStatus。首次真实拒绝终止诊断组，完整120秒内不发输入、截图、状态或原生桌面请求；之后最多一次诊断只用于收尾，预算不足可省略。本候选禁止restore-target/resume，不恢复旧诊断组。Alt+F4已执行或结果未知时不再关闭；只有从未尝试关闭或明确证明工具未发送，才允许冷却后对精确自建Popen一次WM_CLOSE生命周期关闭，不计GUI通过，不用于产品或其他工程。失败token、截止和保持集合均保留。

验收分别记录：GUI双图/双回调；正常资源寿命与余额0；实际健康过期/故障；完整进程退出。任一项未完成都如实报告。单组无过期只能说明该组未观测到过期，不能宣布稳定性已修或产品竞争通过；即使API次数减少，也不直接推导性能倍率。
