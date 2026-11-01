# 自由走线放置提交控制器

`TrackPlacementController` 在核心层连接临时放置状态与 `BoardEditSession`，解决先清除预览、后调用新增后端时可能丢失有效预览的问题。本轮从 `dev=2c0a60697c20ac565759d052229749583e89f839` 的独立 `feat/track-placement-controller` 分支实现，没有接入产品窗口、菜单、F3 或新增写出。

## API 与生命周期

控制器构造接收 `BoardEditSession&`，拥有自己的 `TrackPlacementSession`，不拥有编辑会话。编辑会话必须比控制器活得更久，所有访问须在同一线程串行进行；控制器不可复制。`placement()` 返回放置会话的常量引用，供未来界面读取状态、文档身份、修订、参数及临时端点，不暴露可写状态或编辑会话。

| 入口 | 行为 |
| --- | --- |
| `begin(width, layer, targetLayerVisible, error)` | 从当前编辑会话捕获文档指针和修订，沿用状态类参数校验；非法入口保留已有活动状态。 |
| `setStart(point, targetLayerVisible, error)` | 核对当前编辑上下文后设置明确起点，重新指定起点清除旧终点。 |
| `previewEnd(point, targetLayerVisible, error)` | 核对上下文后保存临时终点，沿用整数 mil 与零长度保护。 |
| `checkContext(targetLayerVisible)` | 依据编辑会话的实际文档、修订及目标层可见性检查失效；活动上下文失效时取消并返回 `false`。 |
| `commit(targetLayerVisible, error)` | 准备请求并同步调用已有 `addTrack`，成功后取消临时放置并返回 `true`。 |
| `cancel()` | 幂等清除全部临时状态，不触碰文档或历史。 |
| `undo()`／`redo()` | 无条件先取消临时放置，再调用编辑会话对应历史入口；没有历史时也会取消。 |

每个显隐参数都指已捕获目标铜层的当前可见性。后续调用方需在换图、关闭文档、其他编辑或目标层显隐事件发生时调用 `checkContext`，取点、预览和提交入口也会再次检查实际上下文。换入独立文档时即使修订号相同，文档指针不一致仍会拒绝；编辑会话正常编辑或 reset 后的旧预览也会取消。库预览与无文档状态不能进入。

## 提交与失败保留

状态类新增 `prepareRequest(currentDocument, currentRevision, targetLayerVisible, error)`：复用原确认校验，返回不含身份、来源或 `extra` 的请求，保留有效预览；上下文失效仍会取消。原 `confirm` API 复用该方法，并继续保持成功后回到 `Idle` 的原行为。

控制器在一次同步 `commit` 中准备请求并调用 `BoardEditSession::addTrack`。确认请求仍绑定相同文档指针和工作修订。新增后端成功时产生一次历史，随后临时状态回到 `Idle`，重复提交无效；后端拒绝时保持几何、参数和活动状态，并通过 `error` 原样返回后端的实际错误，用户可继续修改端点或取消。容量、来源身份和新增身份序列等保护由既有后端执行，控制器不复制这些校验，也不维护第二份历史。

预览和取消不改 dirty、保存点、历史、工作修订、recordCounts 或网表。文件保存和新增写出由后续独立流程处理；本轮验证的失败保留是新增后端拒绝后的预览保留，没有文件写入行为。

## 实际验证

沿用 Pi `deng/gpt-6.1-sol`、`high` 的实际会话，核对环境及原始会话模型事件后，在被忽略目录 `.local-analysis/track-placement-controller/` 建立临时独立 CMake 工程。使用既有 `scripts/Enter-QtEnv.ps1` 启用 Qt 6.12.0、MSVC 14.51.36231 x64，设置根工程 `BUILD_TESTING=OFF`，独立编译控制器专项及原状态专项；状态类实现通过基线 `pt_core` 链接，没有重复编译。

最终 Debug 配置、构建及 CTest 命令退出码均为 0。CTest 2/2 组通过，共 0.44 秒；`TrackPlacementControllerTests` 25 项通过、`TrackPlacementTests` 11 项通过（均含初始化／清理），零失败、零跳过。

专项使用纯内存合成文档，覆盖正常一次提交及身份／来源保护、真实 200000 条走线容量拒绝后的几何保留、保存点和重做分支保留、两阶段取消、无历史撤销重做仍取消、四种上下文变化在取点／预览／提交／显式检查处失效、非法输入、库预览拒绝，以及准备请求与旧 `confirm` 的兼容行为。原状态专项原样编译运行，没有修改已有测试。

实际命令、退出码、分支和模型核对在 `session-evidence.txt`，日志在 `configure.log`、`build.log`、`ctest.log`、`build/track-placement-controller-results.txt` 和 `build/track-placement-session-results.txt`。本轮未运行 GUI、截图或二进制逆向，未触碰原安装与原文件，不能据此宣称用户界面已支持画线；根 CMake 注册及全量 Debug／Release 回归由父任务整合。
