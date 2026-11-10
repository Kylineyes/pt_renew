# PCB 严格语法布局元数据

本阶段以 `dev=6a29de0db7ba8f4d0dcc2d6822f0ed1f3a08499c` 为基线，在独立分支 `feat/pcb-layout-boundaries` 实现读取布局元数据。它为未来新增走线写出提供语法边界；新增写出仍未开放，原软件兼容性仍未验收。相关设计见[新增自由走线与工具取消设计](free-track-creation-design.md)和[身份与编辑历史核心](free-track-history-core.md)。

## API 与解析路径

```cpp
const auto result = pt::LegacyPcbReader::parseWithLayout(bytes, source);
if (result.succeeded()) {
    const auto& board = result.document;
    const auto& layout = result.layout;
    // layout.insertion.isValid() 仅表示存在语法候选，不能据此放开写出。
}
```

`LegacyPcbLayoutReadResult` 提供 `document`、`layout`、`error` 和 `succeeded()`。元数据定义在 `src/io/LegacyPcbLayout.h`，不附加到 `BoardDocument`。原 `parse` 调用 `parseWithLayout` 后取回文档和错误；`readFile` 继续经过 `parse`，大小限制、错误消息、载入身份、字段、警告、摘要及冻结输入的行为共用同一路径。

所有布局只在严格解析完整成功后返回。文件头、数值、范围、COMP 配对、NETDEF、结束标签或 DOS EOF 校验失败时，不返回局部文档，也不暴露先前已遇到的顶层边界或候选；`insertion.unavailableReason` 解释失败原因。

## 偏移及记录区间

所有偏移为相对 `document->sourceBytes` 的零起始原字节位置，未出现的边界用 `-1` 表示；行号沿用原读取器的一起始行号。高位字节在显示文字中仍按既有规则产生替代字符，但偏移不依赖解码后的字符数。

| 字段 | 含义 |
| --- | --- |
| `sourceByteSize` | 完整冻结原输入的字节数，包含 DOS EOF 及其后空白 |
| `textEndOffset` | DOS EOF 的位置；没有 DOS EOF 时为输入字节数 |
| `dosEofOffset` | 实际单个合法 DOS EOF 字节的位置；不存在时为 `-1` |
| `endPcbOffset` | 解析器确认的顶层 ENDPCB 标签行起点，包含该行前导空白 |
| `trailingNetdefsOffset` | 所有 NETDEF 都处于几何之后时，第一条 NETDEF 标签行起点；无 NETDEF 或交错布局时为 `-1` |
| `topLevelRecords` | 按原顺序记录顶层自由图元、完整 COMP、NETDEF、ENDPCB 的标签、行号和半开字节区间 |

`topLevelRecords` 的区间为 `[beginOffset, endOffset)`，包含标签行及其字段和实际行终止字节，不包含后续记录前的空白行。COMP 区间从 COMP 标签行开始，到配对 ENDCOMP 行结束；内部图元及 ENDCOMP 不另列为顶层记录。文件头和独立空白行不列为记录。

ENDPCB 边界由原 `Reader::run` 的顶层语法分支产生。文字内容、焊盘名和元件字段可整行等于 `ENDPCB`，NETDEF 名称、节点及元数据也可能含这些字样；它们在各自字段解析路径中消费，不触发结束边界。没有增加独立搜索 ENDPCB 字符串的路径，也没有放宽原 NETDEF 对结构分隔符和名称的校验。

## 插入候选及能力边界

| 已解析布局 | `insertion.kind` | `insertion.byteOffset` |
| --- | --- | --- |
| 无 NETDEF | `BeforeEndPcb` | 真正顶层 ENDPCB 标签行之前 |
| 所有 NETDEF 均在几何／COMP 后，允许多条及节间空白 | `BeforeTrailingNetdefs` | 第一条尾部 NETDEF 标签行之前 |
| NETDEF 后又出现任意自由图元或 COMP，包括空元件和多段交错 | `None` | `-1` |
| 严格解析失败 | `None` | `-1` |

交错输入仍可通过原 `parse` 正常读取；`geometryAfterNetdef=true`，`unavailableReason` 明确说明不能提供新增插入候选。即使后面另有尾部 NETDEF，也不会恢复候选或错误报告一个完整尾部区。

<a id="explore-ex-010"></a>

`isValid()` 只表达语法候选是否存在。`originalSoftwareInsertionVerified` 当前始终为 `false`；`unverifiedReasons` 记录原软件插入布局以及新增 FT 默认字段、附加属性和换行编码尚未核定。只有存在尾部候选时才附加尾部 NETDEF 的未验证说明，不把交错输入描述成仍有尾部候选。本阶段未改变 writer 的新增拒绝规则、编辑模型或产品界面。

[探索 EX-010](exploration-backlog.md#ex-010)。

## 换行观测与原字节保护

`newlines` 只观测 DOS EOF 前的文本，包括文件头、所有字段、NETDEF 内容、ENDPCB 及之后空白。DOS EOF 后的合法空白保留在冻结原字节中，不参与文本换行统计。

- `lfCount` 统计单独 LF，`crlfCount` 统计 CRLF，两者不重复计数；`mixed()` 表达两种形式同时出现。
- `firstLineEnding` 是首次实际出现的 LF 或 CRLF。`textEndsWithNewline` 只在 EOF 前文本以 LF 结束时为真。
- `bareCarriageReturnCount` 记录没有紧接 LF 的 CR。原解析器以 LF 划行，孤立 CR 不被推定为另一种行分隔方式。
- `insertion.anchorLineEnding` 描述候选锚点标签行本身的实际 LF／CRLF；该行无 LF 时为空。它不表示插入前一行的终止方式，也不提供新 FT 的默认编码。

普通行在原行消费时累计观测；NETDEF 由已有子解析器消费后，仅遍历它确认的字节区间补充换行统计，不再次解释标签。空白、混合换行、无末尾换行、高位字节、ENDPCB 原行及 DOS EOF 全部通过 `sourceBytes` 原样保留。没有任何归一化或写出操作。

## 实际验证

核对的 Pi 会话为 `01a1986f-2198-700e-9abd-4b9af7a122c6`，实际 provider/model 为 `deng/gpt-6.1-sol`，推理强度为 `high`。环境和会话 `model_change`、`thinking_level_change`、实际 assistant 消息记录保存在被忽略目录 `.local-analysis/pcb-layout/model-session.json` 及 `session-records.json`。

独立工程位于 `.local-analysis/pcb-layout/harness/CMakeLists.txt`，以 `BUILD_TESTING=OFF` 引入本仓库，再注册仅链接 `pt_core`／`Qt6::Test` 的 `PcbLayoutTests`；只构建 `pt-pcb-layout-tests` 目标。执行入口为 `.local-analysis/pcb-layout/verify.ps1`，使用现有 `scripts/Enter-QtEnv.ps1`，工具链为 Qt 6.12.0、MSVC 19.51 x64／Ninja。

| 配置 | 配置／构建／测试退出码 | CTest | QtTest 项数 |
| --- | --- | --- | --- |
| Debug | 0／0／0 | 1/1 通过，0.27 秒 | 40 通过，0 失败，0 跳过 |
| Release | 0／0／0 | 1/1 通过，0.15 秒 | 40 通过，0 失败，0 跳过 |

QtTest 项数包含初始化与清理。覆盖实际顶层原字节起点及记录区间、COMP 完整范围、字段内 ENDPCB、多条尾部 NETDEF、NETDEF 后几何／COMP／空 COMP 和多段交错、LF／CRLF／混合换行／无末尾换行／孤立 CR、NETDEF 内换行、带后缀空白的 DOS EOF、ENDPCB 紧贴 DOS EOF、高位字节、原 API 文档事实一致，以及嵌套 COMP、未结束结构、未知记录、非法字段、结束后数据、重复结束标签、非法 EOF、零字节、超长行和超大输入失败时无局部布局。

首次构建在测试中误写 `PrimitiveSource::componentIndex`，编译失败；修正为现有字段 `component` 后完成上述两配置验证。首次 PowerShell 日志因脚本缺少 UTF-8 BOM 导致中文乱码，已为本地验证脚本补 BOM；首次输出及最终明确的命令、退出码仍保存在 `verification-transcript.txt`。最终日志为 `configure-Debug.log`／`build-Debug.log`／`ctest-Debug.log` 及对应 Release 文件，详细断言结果位于 `build-Debug/pcb-layout-test-results.txt` 和 `build-Release/pcb-layout-test-results.txt`。

本任务没有运行 GUI、截图或原二进制，也未改根 CMake 和其他共享文件。根 CMake 的正式注册、集成回归及后续原软件兼容验收由协调者继续处理；本页结果不能证明新增写出或原 FT 默认编码已可用。
