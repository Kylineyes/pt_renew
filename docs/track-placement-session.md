# TrackPlacementSession 放置状态模型

`TrackPlacementSession` 位于应用核心层，为后续画布提供一段自由走线的临时放置状态。本阶段不接入窗口、菜单、键盘分发或写出器；确认结果仍需由调用方显式交给 `BoardEditSession::addTrack`。

## API

- `begin(document, revision, width, layer, targetLayerVisible)` 捕获不可变文档指针、修订、整数 mil 宽度和铜层。合法铜层为 1 或 6，宽度范围为 1..1000000，铜层必须可见，文档指针必须有效且 `sourceContext` 为空，修订须非零并与 `document->workingRevision` 一致。
- `setStart(point)` 在等待起点或等待终点时设置整数 mil 起点；重新设置起点会清除旧终点预览。
- `previewEnd(point)` 在等待终点时保存临时终点。端点必须是有限整数，坐标范围为 ±1000000 mil，且不能与起点相同。
- `checkContext(currentDocument, currentRevision, targetLayerVisible)` 检查捕获的文档指针、修订及目标层可见性。放置活动期间任一项失效就自动取消并返回 `false`；空闲状态返回 `true`。
- `confirm(currentDocument, currentRevision, targetLayerVisible)` 再次执行同样的上下文核对，并在起终点完整有效时返回一次 `TrackPlacementRequest`，随后回到 `Idle`。请求只有起点、终点、宽度、铜层、修订和文档指针，不含 `TrackIdentity`、`PrimitiveSource` 或 `extra`。
- `cancel()` 清除全部临时状态且可重复调用。

状态只有 `Idle`、`WaitingForStart` 和 `WaitingForEnd`。预览只保存在会话对象中，不调用 `BoardEditSession`，不修改 `BoardDocument`、dirty、历史、工作修订、recordCounts 或网表，也不分配新增走线身份。

## 边界行为

非法 `begin` 在所有参数写入前返回错误，因此不会打断原活动会话。非法起点或终点会保留当前状态和已有预览；零长度终点不进入预览。确认缺少起点或终点、几何越界、非整数、非有限值或非法参数时不提交，调用方仍可修改或取消。

文档换入、工作文档修订变化或目标层隐藏会使上下文失效；检查会丢弃旧预览并回到 `Idle`，防止旧板坐标用于新板。确认成功后重复确认无效。取消不触碰编辑会话，也不消耗 `BoardEditSession` 的新增身份序号。

## 实际验证

专项测试文件为 `tests/TrackPlacementTests.cpp`，覆盖状态流转、非法输入、非法 `begin` 保留活动预览、文档／修订／图层失效、两阶段取消、预览不改变编辑会话、单次确认、请求交给 `addTrack` 后的撤销重做、旧修订拒绝以及取消不消耗身份序号。

本机使用 Qt 6.12.0、MSVC 14.51.36231 x64，在被忽略目录 `.local-analysis/track-placement/` 配置独立 CMake 工程，设置 `BUILD_TESTING=OFF` 后引入本仓库，单独编译新增实现及专项测试并链接 `pt_core`／`Qt6::Test`。最终 Debug 构建退出码为 0，CTest 1/1 组通过，Qt Test 11 项通过（含初始化／清理）、零失败、零跳过；专项包含已有保存点和重做分支在预览／取消后的保留验证。

配置、构建、测试命令及退出码记录在 `session-evidence.txt`，最终日志为 `build-final.log`、`ctest-final.log` 和 `build/track-placement-test-results.txt`。首次从 Bash 调用时因当前 PATH 无 `cmake` 返回 127，随后通过项目既有 `scripts/Enter-QtEnv.ps1` 启用 Qt／MSVC，配置和测试均正常；未安装新依赖。Pi 实际会话已核对 `deng/gpt-6.1-sol`、`high`，原始会话的模型及推理强度事件摘录在 `model-session-excerpt.jsonl`。

未启动 GUI、未截图；根 CMake 注册和后续 UI 整合由父任务负责，不能据此宣称产品已经支持画线或新增写出。
