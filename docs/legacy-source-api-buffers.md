# 目录 API 返回缓冲的纯数据解码组件

[EX-005](exploration-backlog.md#ex-005) 的[来源观测前置设计](legacy-source-observation-plan.md#observation-contract)需要保留原返回值和缓冲，不能只保存“看起来像目录”的文本。[本组件](../tools/legacy_source_api_buffers.py)提供两个只接收显式数据的库函数，解释单次 `SHGetSpecialFolderPathA` 或 `windir` 查询快照；没有真实 API、进程内存读取、断点、环境查询或路径访问。合成测试通过不代表实际采集、隔离或来源归因已经通过。

<a id="input-contract"></a>

## 输入和编码契约

`decode_shell_folder` 的所有参数均为必填关键字参数：

| 字段 | 输入约束 |
| --- | --- |
| `raw_bool` | 原 Windows BOOL 的有符号 32 位整数，范围 `-2**31..2**31-1`，0 表示失败，任何非零值走成功门；保留原整数。不接受 Python `bool`、浮点、文本或无符号 `0xffffffff` 的隐式转换。采集者须先按 ABI 保存正确有符号值。 |
| `raw_bytes` | 原 `bytes`，不接受文本、bytearray、memoryview 或数组的隐式转换。原字节及首 NUL 后的全部尾部逐字节保留。 |
| `read_limit` | 严格整数，`1..0x104`，单位为字节；`len(raw_bytes)` 不得超过它。超界直接拒绝，不截掉输入尾部再声称成功。 |
| `read_complete` | 严格 `bool`，表示采集者声明本次计划的有界读取已完整完成；可以在取得终止 NUL 后结束，不要求填满上限。不完整即保留 `unknown`，即使已经看到 NUL 也不接受为完整成功快照。 |
| `encoding` | 显式非空编码名；无默认、自动检测、本机 locale／ACP 推断或替换字符。编码别名按标准库查表解析，同时保留原名称和规范名称。 |

支持的规范编码为 `ascii`、`utf-8`、`cp874`、`cp932`、`gbk`、`cp949`、`cp950`、`johab` 及 `cp1250..cp1258`，涵盖这里允许的常见 ASCII 兼容 Windows ANSI 代码页和 UTF-8 代码页；例如 `cp936` 可规范为 `gbk`、`cp65001` 可规范为 `utf-8`。未列出的编码明确拒绝；`mbcs`／`oem` 等本机相关名称、UTF-16、带 BOM 处理的 `utf-8-sig` 和非文本 codec 不作自动降级。传入 `cp1252` 并不能证明目标当次就使用该代码页，编码来源仍由采集者提供证据。

`decode_windir` 要求同样显式传入 `encoding`，另带严格布尔字段 `pointer_is_null`。非 null 时使用上述缓冲契约；null 时 `raw_bytes`、`read_limit`、`read_complete` 必须全部为 `None`，不虚构一次空缓冲读取，也不接受 null 指针同时附带残留 bytes 的矛盾记录。

字段类型、BOOL 范围、读取长度、编码名称或 null 声明矛盾时抛出 `SnapshotFormatError(ValueError)`，错误文字为中文；缺少必填参数由 Python 抛 `TypeError`。错误输入保持原样，由调用者连同异常保存；组件不修改调用者输入来生成一个“修复后”结果。

<a id="result-contract"></a>

## 结果与拒绝含义

本节继续[EX-005](exploration-backlog.md#ex-005)，仅说明原快照的数据消费规则。

返回字典保留 `raw_bytes`、原 BOOL／指针门、读取声明、原／规范编码，以及：

- `first_nul`：原字节中首个 `00` 的从 0 计位置；不存在则为 `None`。
- `text`：仅首 NUL 前缀严格解码所得文本；没有 NUL 或解码失败则为 `None`。失败 BOOL 后的可解码残留仍可放在此字段，**不能直接把 text 当路径使用**。
- `tail_bytes`：首 NUL 后所有原字节，包括其它 NUL 和非法编码 bytes；无 NUL 时为 `None`，完整原缓冲仍在 `raw_bytes`。
- `buffer_status`：无读取／终止／解码问题才为 `complete`，否则为 `unknown`；windir null 为 `not_applicable`。
- `possible_truncation`：读取未完成或未找到 NUL 时为 true，只说明快照可能截断，不能断言目标原字符串一定超长；不带 NUL 的 260 字节不会被补 NUL。
- `decode_error`：严格解码失败时保留前缀内字节偏移 `start`／`end` 和标准库原因 `reason`；不输出替换文本。
- `issues`：按读取、终止、解码次序保留 `incomplete_read`、`missing_nul`、`decode_error`，可同时存在。

| Shell32 `status` | 判定及消费者字段 |
| --- | --- |
| `api_failed` | `raw_bool==0`，即使缓冲残留非空也不接受路径；`path_text=None`、`fallback_required=True`。缓冲本身仍可能是 unknown，两个层次分别保留。 |
| `success_empty` | BOOL 非零且缓冲完整、首字节 NUL；`text=''`、`path_text=None`、`fallback_required=True`。它与失败 BOOL 是不同结果。 |
| `success_nonempty` | BOOL 非零且缓冲完整、严格解码为非空；`path_text=text`、`fallback_required=False`。这仅是该返回文本可以消费，不证明目录存在、绝对路径、身份或隔离。 |
| `unknown` | BOOL 非零但快照不完整、无 NUL 或解码错误；`path_text=None`、`fallback_required=None`，不猜分支。 |

`fallback_required` 只描述[已核默认根局部分支](dosbox-default-roots-static.md#roots-and-fields)的返回条件。组件不知道这次是 CSIDL `0x1c` 还是 `0x1a`，不伪造第二次调用，不把局部后备条件变成最终路径或调用已发生的证据。

| windir `status` | 判定及消费者字段 |
| --- | --- |
| `null_pointer` | 没有可读字符串，`literal_fallback_required=True`、`value_text=None`；只标记 null 门，不构造常量目录。 |
| `nonnull_empty` | 完整快照首字节 NUL，`value_text=''`、`literal_fallback_required=False`。不能套 Shell32 的空串后备规则。 |
| `nonnull_nonempty` | 完整非空文本保存在 `value_text`，`literal_fallback_required=False`。 |
| `unknown` | 非 null 但缓冲信息不足／解码失败，`value_text=None`；指针门已知，故 `literal_fallback_required=False`，不以未知内容改选 null 字面后备。 |

固定默认根链只对 windir 返回指针做 null 判断；非 null 空串没有额外常量回退，后面的长度门与字符串拼接也不是本组件职责。读取上限是组件的保守输入边界，不声称这是所有 CRT 字符串读取的原生容量约定。

<a id="consumer-example"></a>

## 未来采集者与审计器如何调用

以下 bytes 全为合成数据，不访问本机 API：

```python
from tools.legacy_source_api_buffers import decode_shell_folder, decode_windir

folder = decode_shell_folder(
    raw_bool=0, raw_bytes=b'X:\\residue\0tail',
    read_limit=0x104, read_complete=True, encoding='cp1252',
)
assert folder['text'] == 'X:\\residue'
assert folder['path_text'] is None
assert folder['status'] == 'api_failed'

empty = decode_windir(
    pointer_is_null=False, raw_bytes=b'\0old',
    read_limit=0x104, read_complete=True, encoding='cp1252',
)
assert empty['value_text'] == ''
assert empty['literal_fallback_required'] is False
```

未来采集者须按[观测记录契约](legacy-source-observation-plan.md#observation-contract)保存该次调用 ID、进入／返回对应关系、进程创建身份、模块／调用站点、CSIDL、buffer 地址、读取长度和编码来源，然后将自己取得的原 BOOL 与 bytes 传入本库。`read_complete=True` 是外部证据声明，库无法验证它是否真实、是否来自同一时点，不能替代实际读取回执或完整性审计。

未来审计器保留原记录，并分别审查格式异常、`buffer_status` 和 API `status`，只在相应状态下消费 `path_text`／`value_text`；单看 `text` 会误收失败残留。原 bytes 在 Python 返回值中仍为 bytes，若需要写 JSON，由调用者使用明确的十六进制／base64 字段进行无损序列化，不用路径文本覆盖它。本轮不增加 JSON CLI 或事件框架。

本库不调用 `SHGetKnownFolderPath` 或任何辅助 API，不从它们推断目标实际调用；不读环境、locale、磁盘目录或旧现场，不 resolve、trim、补终止符或规范化路径。它既不证明配置来源已加载，也不补[GET 输出／环境更新回执](legacy-config-query-contract.md#local-results)，不生成运行配置、候选或 GO。

<a id="validation"></a>

## 验证、交付与剩余缺口

验证命令为 `python -B tests/test_legacy_source_api_buffers.py`，20 项合成测试退出 0，原回执在本树 `.local-analysis/ex005-api-buffer-decoder/unit-first.json`。测试覆盖失败后非空残留、成功空串、windir null／非 null 空串、259+NUL 的 260 字节边界、260 字节无 NUL、嵌入 NUL 和尾部 bytes、部分读取、严格解码／多字节代码页、非法字段／编码／长度，并用禁用环境／locale／路径查询的检查核对纯数据接口。全部文件 fixture 都在本任务忽略目录内创建并自动清理；没有真实 API、目标运行、用户配置、目录隔离或调试验证。

开发分支 `feat/ex005-api-buffer-decoder` 从最新 `origin/dev` 的 `ff7f23e267172f46e326e360c03b0b0f0a9fae4c` 建立；唯一版本文件为本组件、[测试](../tests/test_legacy_source_api_buffers.py)和本文。实际 Pi `01a1d4e9-989e-71e2-b4f9-f52f961a53f7`，环境及会话模型事件均为 `deng/gpt-6.1-sol/high`，成功核验回执 `startup.json` 已发协调。本轮原测试失败如有须原样保留；当前首轮 20 项全过，未产生测试失败。

文档检查 `python -B tools/check_exploration_docs.py` 实际退出 1，检查 161 份 Markdown、1281 个本地链接、41 个事项、133 处来源及 145 份报告，唯一错误为本文尚未在完整资料索引中恰好出现一次；原回执 `docs-first.json` 保留，由协调统一入链，不修改共享索引。`git diff --check` 退出 0，提交前另以 `git diff --cached --check` 检查新增三文件的实际暂存内容，回执随交付保存。

协调已完整审阅119行工具、237行测试、本文和原delivery.json，在独立集成分支运行20项父树测试全部通过。已核失败BOOL不会将残留text发布为path_text、成功空串与失败分开、windir非null空串不选字面后备、260字节及严格编码／截断规则；实现未作修改。父验收记录为协调树`.local-analysis/ex005-offline-0174/api-buffers-parent-review.json`；子代理未索引的原exit1保留，协调另行统一入链。该验收只接受纯数据组件。

实际 API 参数／返回采集、原 BOOL 的 ABI 绑定、编码证据、读取完整性、调用配对、隔离能力及来源／阶段 I/O 仍缺实现和真实回执；上述设计继续受[观测能力前置](legacy-source-observation-plan.md#capability-gates)约束。组件完成不结 EX-003／EX-005，也不追认任何历史运行。
