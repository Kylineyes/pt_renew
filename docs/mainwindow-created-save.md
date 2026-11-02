# 主窗显式新增另存闭环

`MainWindow::saveAsFileWithCreated(path, options, error)` 已把主窗中真实提交的 Created 走线接到显式 writer 发布流程。成功后工作副本进入保存点，撤销变 dirty、重做回到保存点变 clean；写出失败保留文档、身份、历史、dirty 和最近成功输出元信息。普通 `saveAsFile`／文件菜单继续使用默认 writer，仍拒绝 Created，`trackPlacementUserEntryAvailable()` 仍为 `false`。

这是**内部显式验收 API**，没有增加用户菜单、命令行开关或 FT 默认值，不代表原 AUTOTRAX 兼容，也不代表普通产品新增功能已开放。

## 调用与职责

```cpp
pt::LegacyFreeTrackCodec::Options options;
// 以下仅为合成验收参数，不是原软件默认值。
options.fields = pt::LegacyFreeTrackCodec::FieldLayout::SevenFields;
options.lineEnding = pt::LegacyFreeTrackCodec::LineEnding::CrLf;
options.extra = 19;
QString error;
const bool saved = window.saveAsFileWithCreated(newPath, options, &error);
```

选项参数没有默认值。六／七字段、换行、七字段附加整数都由调用方提供，编码器和 writer 负责校验；无 Created 时沿用 writer 的已有规则，不消费新增编码选项。七字段输出仅投影附加值到文件，不反写 Created 内存对象。

主窗没有重写 writer、控制器、历史或发布算法。两个公开保存方法共用私有 `saveAsFileImpl`：

1. 取消临时放置但不提交预览；保留已有选择、测量模式和测量结果。
2. 沿用主窗载入中、未载入、活动库窗口保护，再分别调用真实 `LegacyPcbWriter::saveAs` 或 `saveAsWithCreated`。库来源、无效选项、已有目标、同输入、路径和 NETDEF 等保护由现有 writer 继续执行。
3. 失败返回错误并显示保留历史的状态提示；不调用 `markSaved()`，也不修改最近成功输出记录。
4. 只有 writer 确认全新文件发布成功后才 `markSaved()`，更新输出路径／SHA-256／字节数，并刷新标题、动作和文件信息。两条路径共享这一成功收尾，没有复制两套发布实现。

另存不会重绑来源：`original()`、当前文档指针、来源 `filePath`、`sourceBytes`、来源摘要、内存 Created 身份及修订保持不变。重开输出是独立载入，会按输出行建立 Loaded 身份，并以输出作为新来源。

## 取消和陈旧文件框

直接 public 保存与菜单文件框都只取消临时走线。菜单原有命令分派也保留相同规则，不再依赖必须先经过 QAction 才能正确取消。取消路径不扩大为清除全部选择或测量。

默认文件框打开前保存修订、当前文档、原始文档和载入代次；用户选定路径后，只要这些信息变化或仍在后台载入，就拒绝陈旧写出。即使后台载入失败、当前文档和修订没变，载入代次改变仍让旧文件框失效。现有“文件框期间移动旧走线”的回归继续通过，原选择没有被取消操作清掉。

显式 API 接收调用方已选择的路径，不自行弹文件框。诊断宿主若提供原生路径选择，应在打开文件框前取消预览并记录文档／修订，在文件框返回后复核；真实桌面验收须另行排程，不能把 offscreen 测试当作原生文件框验收。

## 专项与回归结果

新增 `tests/MainWindowCreatedSaveTests.cpp` 全部通过真实 MainWindow API 建立保存点，没有直接 writer 调用加手动 `markSaved()` 冒充主窗测试。所有文件均为 `QTemporaryDir` 中的独立合成输入，逐项比较输入字节；不使用原软件或用户原件。专项覆盖：

- 六字段 LF／七字段 CRLF 发布、输出精确字节、元信息更新、内存附加字段不变、重开 Loaded 行身份及产品能力门保持关闭。
- 已有走线移动／删除与 Created 混合保存、保存后撤销 dirty／重做 clean、保存点之前和之后截断分支、Created 身份不复用。
- 缺编码选项、七字段缺附加值、已有目标、同输入、空路径、缺目录、错误扩展名、尾部／交错 NETDEF、默认保存拒绝 Created；失败保留文档指针、身份、修订、历史、保存点和最近输出信息。
- 已保存 Created 的失败重存保持 clean；默认路径仍不能借助此前显式保存绕过新增拒绝。
- 默认／显式保存取消未提交预览，不向输出添加预览；已有选择和测量结果保留。
- 未载入、后台读取中、失败读取、活动库窗口和库来源保护；菜单文件框取消不写出，以及失败载入完成后陈旧文件框拒绝。

本 worker 在独立忽略目录 harness 中进行 Debug 构建，编译并行度为 2，配置和构建退出均为 0。offscreen 实际创建者 wait 和 QtTest 结果如下，计数含初始化／清理：

| 专项 | 通过项 | 失败／跳过 | 创建者 wait |
| --- | --- | --- | --- |
| `MainWindowCreatedSaveTests` | 31 | 0／0 | 0 |
| 既有 `WritingTests` | 40 | 0／0 | 0 |
| 既有 `TrackPlacementUiTests` | 13 | 0／0 | 0 |
| 既有 `LibraryTests` | 26 | 0／0 | 0 |
| 既有 `TrackCreatedWorkflowTests` | 5 | 0／0 | 0 |

首轮 Library 为 25 通过、1 失败，真实 wait1：本地 harness 的诊断工具在 `product/` 子目录，测试按自身目录查找 `pt-library-check` 失败。仅在忽略目录 harness 增加相邻工具复制后，26 项全部通过，旧测试和产品库代码没有修改；原失败日志保留。新主窗专项首轮 29 项通过，后续增加混合编辑与活动库窗口用例、加强载入完成后的陈旧文件框校验后为 31 项。完整 Debug／Release 正式注册与全量验收由父协调者负责，本 worker 未修改根 CMake 或跨模块测试。

## 证据与待验收边界

实现分支 `feat/mainwindow-explicit-save` 从 `origin/dev` 的 `fbbc572a46463f617481618f214c49d0b2549829` 建立。只有 `src/ui/MainWindow.h/.cpp`、本专项及本说明纳入本次 Git 修改；所有构建、harness、原会话与日志留在 `.local-analysis/mainwindow-explicit-save/`。

本地证据包括 `session-audit.json`（同一 Pi `deng/gpt-6.1-sol high` 的实际 model／thinking／assistant／成功工具原事件）、`build-exit.json`、`build-attempt2-exit.json`、`tests-exit.json`、首轮失败回执及各测试文本日志。没有改变 `CommandCatalog` 能力门、选择默认编码、合并 dev、推送或派生代理。

当前结果为**实现及局部 offscreen 验证通过**。本轮未操作桌面，Windows 原生文件框中显式另存、保存后的真实窗口 clean／Undo／Redo，以及真实重开输出仍待父明确排程；原 AUTOTRAX 生成与重开兼容仍无证明。这些边界不因专项通过而改变。
