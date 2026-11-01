# 走线新增预检与提交控制：第二轮并行开发

> 后续现场：原软件单线样例已完成一次限时尝试，取得可辨启动／几何／菜单和日志及正常退出证据，但未取得新建保存文件，见[核验报告](native-ft-sample-verification.md)。下文保留本次离线开发及 19/19 组验证记录；原 FT 默认编码与产品新增写出仍未开放。

2026-11-02，按用户要求继续并行开发，基线为 `dev=2c0a60697c20ac565759d052229749583e89f839`。父分支 `integration/track-preflight-wave`，Run `run_983a7a1c8e88`。本轮完成显式编码、未编码插入预检和提交控制三项内部能力，并由父补跨模块内存流程测试；原 FT 默认编码、原软件兼容及产品新增写出仍未开放。

## 独立所有权与交付

| 子任务 | 工作树／分支 | 授权文件 | 提交与独立验收 |
| --- | --- | --- | --- |
| 显式 FT 编码器 | 复用 `../feat-pcb-layout-boundaries`，新分支 `feat/free-track-codec` | 新 `src/io/LegacyFreeTrackCodec.h/.cpp`、`tests/FreeTrackCodecTests.cpp`、`docs/free-track-explicit-codec.md` | `704a01d`，Debug 72 项通过 |
| 提交控制器 | 复用 `../feat-track-placement-state`，新分支 `feat/track-placement-controller` | `src/application/TrackPlacementSession.h/.cpp`；新 `TrackPlacementController.h/.cpp`、`tests/TrackPlacementControllerTests.cpp`、`docs/track-placement-controller.md` | `6d45800`，Debug 控制器 25 项和原状态 11 项通过 |
| 插入预检 | 新树 `../feat-track-insertion-plan`，分支 `feat/track-insertion-plan` | 新 `src/io/LegacyTrackInsertionPlanner.h/.cpp`、`tests/TrackInsertionPlanTests.cpp`、`docs/track-insertion-plan.md` | `2b3a81e`，Debug 72 项通过，73.48 秒 |

实际改动分别为 4、6、4 个文件，三方交集为空，均在授权范围；每个工作树和构建目录独立。父独占根 CMake、`tests/TrackPreflightWorkflowTests.cpp`、本集成记录、既有进度入口及[下一阶段桌面方案](native-ft-sample-control-plan.md)。子 agent 只提交自身分支，父审查后按 no-ff 逐项合入集成分支，不发生共享文件并发编辑。

三名子 agent 实际均为 Pi `deng/gpt-6.1-sol high`。编码器和控制器分别沿用 session `01a1986f-2198-700e-9abd-4b9af7a122c6`、`01a1986f-2612-7552-9ed6-755f83a3dcb7`，父在任务开始前核对闲置状态、干净工作树并切换至本轮新分支。预检新 session 为 `01a19892-370a-771e-a211-24198906e402`。本机只读审计按本轮 Dispatch 对应的新用户消息划定执行范围，确认实际模型、推理事件及工具返回，不把上一轮调用混成本轮证据。

| Task | Dispatch | 结果 |
| --- | --- | --- |
| `task_f5f4fdaf4c10` | `ctx_d0742653c9c4` | succeeded，父审阅接受 |
| `task_1e708421c93c` | `ctx_5033ae1a3eb8` | succeeded，父审阅接受 |
| `task_307a953209d4` | `ctx_4d135b058423` | succeeded，父审阅接受 |

三份 `worker_done` 的提交、文件、文档及真实测试结果经父核对后，各执行 `worker-release` 再确认消息。因绑定的是 external 终端，回执均为 `retained/external_terminal/processAction=none`，终端闲置，不把任务结束说成操作系统进程退出。最后 reclaimable 为 0、收件箱为空。此前 GLM 配额失败记录保持，本轮没有重派纯逆向任务或替换指定逆向模型。

## 最终行为

[显式编码器](free-track-explicit-codec.md)要求调用方明确选择六／七字段和 LF／CRLF；默认 `Unspecified`、矛盾附加值和非法参数均拒绝。它只返回一条 FT 的内存字节，不读写文件，不从原走线复制未知属性，也不授权生产入口。测试中的七字段值只是显式合成参数，不能用来选择原程序默认值。

[插入预检](track-insertion-plan.md)先剥离经验证的新建段，复用现有 writer 的冻结原件及旧记录保护，再重新解析应用移动／删除后的基础字节。偏移针对这些基础字节，容量按严格解析的全部语法记录加 ENDPCB 和新增段计算。父审查要求修正了保守按原输入计数的初稿，使删除旧段能够释放真实容量；最终专项验证了释放容量后合法新增和再次超限。存在新增时拒绝尾部或交错 NETDEF；没有新增时保留已有受限路径。计划不编码、不拼接新 FT，不估算未知编码的最终文件大小。

[提交控制器](track-placement-controller.md)使用非破坏性的 `prepareRequest`，同步调用已有 `addTrack`，只有成功后才清除预览；真实容量拒绝会原样返回错误并保留有效几何、文档、修订、保存点和重做分支。统一取消和撤销重做入口已在核心层实现，尚未接入画布或键盘分发。原 `TrackPlacementSession::confirm` 保留原有成功清空语义，原状态专项继续通过。

父的跨模块专项串联控制器、预检、显式编码器和读取器，覆盖六／七字段与两种换行的四种组合；先移动／删除旧记录，再新增两段，核对重算偏移、未修改前后缀、组件和附加字段、DOS EOF、四次撤销／重做及身份保留。另验证缺省编码不改变已提交几何、显式编码不能授权 NETDEF 插入，现有 writer 始终拒绝含新增段文档。合成候选只存在于测试内存，不写目标文件。

## 父集成验证

Debug／Release 已并行完成配置和全量构建，退出码均为 0。两套 CTest 各允许两个独立测试进程；现有界面回归使用 offscreen，新增模块与跨模块专项仅链接 Qt Core／Qt Test。插入预检的真实大板边界使用 180 秒专项预算，其他新专项维持 30 秒。

| 配置 | CTest | 编码器 | 插入预检 | 控制器 | 跨模块 |
| --- | --- | --- | --- | --- | --- |
| Debug | 19/19，67.49 秒 | 72 项通过 | 72 项通过 | 25 项通过 | 8 项通过 |
| Release | 19/19，8.97 秒 | 72 项通过 | 72 项通过 | 25 项通过 | 8 项通过 |

QtTest 项数含初始化／清理，两配置均零失败、零跳过，CTest 真实 `wait` 返回值均为 0。原读取、编辑、另存、网表、铜分析等专项一并纳入全量回归，其中原新增历史、状态、写出、编辑专项分别为 28、11、40、23 项通过。测试运行器持续持有各 CTest 子进程，不因单次工具等待上限打断长用例，完整日志和真实退出回执均已保存。通过后仅更新文档及 Git 集成记录，未再改产品源码，也不重复已通过测试。

本阶段没有 GUI 修改、真实桌面控制、截图、原软件启动或原件写入，没有新增依赖。测试通过不代替原 AUTOTRAX 的新建／保存样例或产品真实窗口验收。

## 下一步与证据

下一阶段需要操作原软件隔离副本，预计占用桌面约 15 分钟，先确认可辨菜单，再尝试产生单线保存样例，具体范围与停止条件见[桌面方案](native-ft-sample-control-plan.md)。本轮没有转入现场。原 FT 字段、附加值和记录顺序得到证据后，才能选择经过验证的编码参数、接入新增写出，再开放菜单／F3 和统一取消工具并进行指定模型截图验收。

父 `.local-analysis/track-preflight-wave/` 保存三份任务约束、会话只读审计、构建结果、独立 CTest 日志与真实退出回执及最终 Git／Task 状态；子证据在各工作树 `.local-analysis/free-track-codec/`、`.local-analysis/track-placement-controller/`、`.local-analysis/track-insertion-plan/`。原安装、运行副本、截图和构建不提交；原 provider 会话不修改。
