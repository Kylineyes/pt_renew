# PCB 严格只读核验命令

`pt-pcb-check` 将已有 PCB reader／layout 的结构核验作为正式控制台命令提供，供原软件隔离样例和产品输出检查使用。成功只表示本项目严格解析通过，**不代表原 AUTOTRAX 接受该文件**；观察到的 FT 字段数量、附加值及换行也不能当成新增写出的默认策略。

## 调用与退出码

```powershell
pt-pcb-check.exe 'C:/本地样例/板图.PCB'
pt-pcb-check.exe --track-limit 0 'C:/本地样例/板图.PCB'
pt-pcb-check.exe 'C:/本地样例/板图.PCB' --track-limit 1000
pt-pcb-check.exe --help
```

仅接受一个路径；Unicode 路径由 `QCoreApplication::arguments()` 处理。`--track-limit` 可在路径前后指定一次，必须是 `0..1000` 的十进制整数，默认 `100`；`0` 只输出完整摘要及布局，不列自由 FT 明细。可用 `--` 结束选项识别，后面只接受路径。`--help` 单独使用时输出说明 JSON，不读取文件；它与其他参数组合时视为参数错误。

标准输出统一为 UTF-8 JSON，正常情况下标准错误为空。退出码为：

| 退出码 | 含义 |
| --- | --- |
| `0` | 严格解析并生成完整报告；或单独请求帮助 |
| `1` | 无法读取、严格解析失败，或无法确认模型与原 FT 布局对应关系 |
| `2` | 参数错误 |
| `3` | 标准输出写入失败 |

调用者必须先检查进程退出码和 JSON 的 `succeeded`。解析／参数失败仅返回 `succeeded: false`、`error`、`path` 及兼容性提示；不返回局部几何、记录计数、摘要或布局。帮助 JSON 只有用法及兼容性提示，不含 `succeeded`。

## 冻结输入与报告范围

命令只调用一次 `LegacyPcbReader::readFile`，继承其完整原字节冻结、64 MiB 上限、未知记录拒绝、ENDPCB／DOS EOF 完整性等规则；再将该次冻结的 `sourceBytes` 交给 `parseWithLayout`，不重新打开输入，也不写输入或旁路文件。

自由 FT 只从严格解析给出的 `layout.topLevelRecords` 中枚举，并逐条核对模型来源行、Loaded 身份和自由归属。每条记录只在其已确认的 `[beginOffset, endOffset)` 内观察标签／数值两行和字段数量；无法对应时整体拒绝。不会搜索正文中的 `ENDPCB` 猜插入点，也不会把 FS 文字、元件名或元件内 CT 当成自由 FT。即使明细上限为零，也完成严格解析及 FT 区间对应检查。

仅输出受限的自由 FT 几何；不导出完整原字节、文字内容、焊盘、库或其他私有几何。摘要计数包含全部已解析对象，明细上限只影响 `freeTracks` 数组。布局输出是语法事实；例如 `BeforeTrailingNetdefs` 不表示 writer 允许新增到 NETDEF 前，本命令不改变 writer 或能力门。

## JSON 字段

字段采用英文 camelCase；端点单位为整数 mil，偏移单位为字节，来源行从 `1` 开始。不存在的偏移保留 reader 的 `-1`，不伪造字节来源。

| 字段 | 内容 |
| --- | --- |
| `succeeded` | 严格解析及报告构造成功 |
| `path`、`sha256`、`byteSize` | reader 返回的输入绝对路径、完整冻结字节 SHA-256 与字节数 |
| `recordCounts` | reader 的全部记录分类计数，包含元件内部记录和 ENDCOMP，不含 ENDPCB |
| `syntaxRecordCount` | `recordCounts` 总和加 ENDPCB 一条；字段行及 COMP 隐式文字不另计记录 |
| `primitiveCount` | 模型全部图元总数，含元件内图元和可见的元件隐式文字，不等同于语法记录数 |
| `freeTrackCount` | 全部顶层自由 FT 数量，排除元件 CT |
| `trackLimit`、`freeTracksOmitted` | 本次明细上限与实际省略条数 |
| `freeTracks` | 最多上限数量的自由 FT 明细，保持文件顺序 |
| `originalSoftwareCompatibilityVerified` | 永久为 `false`，包括错误和帮助输出 |
| `notice` | 中文兼容性和默认编码未核定提示 |

每条 `freeTracks` 包含：

- `start`、`end`：`[x, y]` 整数端点；`width`、`layer`：严格 reader 解释出的宽和层。载入可见层范围遵从 reader，不收窄为新增编码层。
- `extra`：只有原记录为七字段时出现，包括合法零值和负值；不解释电气属性。
- `identity`：`{"kind":"Loaded","value":来源标签行}`。
- `sourceLine`、`sourceByteOffset`、`sourceComponent`：模型来源；当前 reader 的字节来源为 `-1`，自由 FT 元件归属为 `-1`。
- `sourceRecord`：`fieldCount` 为实际六／七字段观测；`beginOffset`／`endOffset` 是严格顶层区间；`tagLineEnding`／`valuesLineEnding` 是两行实际终止字符串。

换行使用 JSON 转义后的实际字节字符串：`"\n"`、`"\r\n"`、`"\r"` 或 `""`，不自行归一化或选择默认值。

`layout` 包含 `sourceByteSize`、`textEndOffset`、`dosEofOffset`、`endPcbOffset`、`trailingNetdefsOffset`、`netdefCount`、`geometryAfterNetdef`、`topLevelRecordCount`、`unverifiedReasons`，以及永久为假的 `originalSoftwareInsertionVerified`。其中：

- `newlines`：`lfCount`、`crlfCount`、`bareCarriageReturnCount`、`mixed`、`textEndsWithNewline`、`firstLineEnding`。统计范围是 DOS EOF 前文本，包含 ENDPCB 后合法空白，排除 DOS EOF 后空白。
- `insertion`：`kind` 为 `None`／`BeforeEndPcb`／`BeforeTrailingNetdefs`；另含 `valid`、`byteOffset`、`anchorLineEnding`、`unavailableReason`。交错 NETDEF 可严格解析，但没有可用插入候选；这不是解析失败。

## 构建与过程验证

正式目标 `pt-pcb-check` 由 `tools/InspectPcb.cpp` 构建，链接 `pt_core`。`pt-pcb-check-tests` 由 `tests/PcbCheckTests.cpp` 构建，链接 `Qt6::Core`／`Qt6::Test`，依赖 CLI；测试使用 `QTEST_GUILESS_MAIN`，无需桌面或 offscreen。根 CMake 由协调者集成，测试优先使用 `PT_PCB_CHECK_EXECUTABLE` 指定的程序路径，否则定位测试程序相邻的 CLI。

测试真实通过 `QProcess` 启动 CLI，并检查进程正常退出、退出码及标准输出 JSON。独立 Debug harness 的配置、构建与 CTest 均真实退出 `0`，QtTest **15 项通过、0 失败、0 跳过**，含初始化／清理；用例覆盖：

- Unicode 路径、输入 SHA 和字节数不变、混合 LF／CRLF、六／七字段、零／负附加值、逐行换行、无尾部换行及 DOS EOF。
- FS 正文含 `FT`／`ENDPCB`、元件字段含同名文字、元件 CT 排除、真实来源行与 Loaded 身份。
- 默认 100、0、1、最大 1000 条明细上限；1002 条输入计数保持完整并报告省略数。
- 帮助、错误参数、缺文件、未知标签、损坏 EOF、缺 ENDPCB、结束后数据、坏数值字段均不输出部分几何。
- 尾部及交错 NETDEF 布局报告，以及继承 reader 的 64 MiB 文件上限。

本机独立构建、真实退出和日志位于本树忽略目录 `.local-analysis/pcb-check-cli/`。`configure-debug-exit.json`、`build-debug-exit.json`、`test-debug-exit.json` 保留实际退出，完整 QtTest 日志在 `build-debug/pcb-check-test-results.txt`，CTest 1/1 通过耗时 3.18 秒；`env-locator-test.txt` 另确认父 CMake 使用的 `PT_PCB_CHECK_EXECUTABLE` 路径方式可用。`model-source-audit.json` 从原会话 `01a19f99-9252-74f7-9844-99633c12fe1f` 记录 `deng/gpt-6.1-sol`／`high` 原事件、成功工具和源码／exe 摘要。

## 前轮合成输入实跑

已只读调用本次 Debug CLI 核验以下两份既有合成输入，均来自 `verify-parallel-save-hardening/.local-analysis/parallel-save-hardening-live/runtime/`，两次真实进程退出均为 `0`，文件前后 SHA-256 完全一致：

| 合成文件 | 完整文件 SHA-256 | 首段端点 |
| --- | --- | --- |
| `INPUT.PCB` | `0d0bec3a1975a44182dbe8abf7071c6e1f3d2ce6a5859acaebdc28a4178c189e` | `(100,100) → (400,500)` |
| `HARDENED-SAVED.PCB` | `51dbf589b06cc7b6fdd1d24b20f2c2b8b4a84fe4e95508b51466ee6474e786d3` | `(175,190) → (475,590)` |

两份均为 74 字节、2 条自由 FT、3 条语法记录（含 ENDPCB）。第一段实际七字段、`extra=42`、标签与数值行均 CRLF；第二段实际六字段、两行均 LF。两份均报告混合换行、ENDPCB 偏移 `65`、DOS EOF 偏移 `73`，与实际冻结输入一致。完整 stdout、stderr、进程退出及前后摘要存于证据目录的 `INPUT.PCB.json`、`HARDENED-SAVED.PCB.json`、`synthetic-sample-results.json`、`sample-audit-exit.json`。

全量 Debug／Release 正式集成验收交协调者。本工具和测试只使用隔离合成输入，不涉及原软件现场或二进制逆向，不能把合成样例报告称为原软件样例验收。
