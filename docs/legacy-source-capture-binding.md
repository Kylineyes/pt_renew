# EX-005 Shell32 调用快照与审计 v2 的字段绑定

<a id="shell32-capture-binding"></a>

本契约接续[EX-005](exploration-backlog.md#ex-005)及[观测前置设计](legacy-source-observation-plan.md#observation-contract)，供本轮两个离线实现共同使用。目标是将原参数、返回值和缓冲接入[已有审计器](legacy-source-observation-audit.md#schema-v1)与[缓冲解释组件](legacy-source-api-buffers.md#result-contract)。本文固定数据边界，不证明采集器、实际隔离或运行能力；本轮没有目标启动、真实进程连接或桌面控制。

## 本轮分工与版本边界

- 审计 worker 独占现有审计工具、测试及报告，新增 schema v2 的显式分流；v1 的字段和接受规则继续按既有契约验证，拒绝单输入混用版本。
- 快照 worker 独占新提取核心、测试及报告，只用模拟寄存器与注入的只读内存回调；不实现 Win32 进程／调试后端。
- 两项各从最新 dev 的独立工作树和分支开发，不互改文件。协调在交付后验收共同字段，再安排离线回放集成。

v2 的顶层公共字段与 v1 相同，`schema_version` 改为精确整数 2。已有事件仍执行身份、顺序、时间、覆盖、调用栈及文件生命周期检查。v2 的 `operation=api` 本轮仅接受名称精确为 `SHGetSpecialFolderPathA` 的调用，不接受其它 API 名称；parse 事件仍按已有规则。Property、windir、查询输出和完整 Host I/O 尚不属于本版扩展，不能藏入扩展字段绕过检查。

## api_snapshot 事件

v2 新增 `kind=api_snapshot`，其 `data` 必须恰含 `call_id` 与 `capture`。快照必须在同一 TID 的相应 API 调用处于栈顶时出现，位于 call_enter 与 call_return 之间，每次调用恰好一次；返回事件的原 result 必须等于快照的 raw_bool。重复、孤立、跨线程、错误顺序或返回前缺快照均拒绝。快照和相应 call_return 分开记录，不改写或隐藏原事件。

`capture` 必须恰含下表字段，库生产者也返回这个对象，不额外添加推断结果。地址和整数均使用 Python／JSON 精确整数，拒绝 bool 与 float；不接收数值字符串。本契约没有任意扩展字典。

| 字段 | 固定约束及来源 |
| --- | --- |
| `api` | 精确字符串 `SHGetSpecialFolderPathA` |
| `module_base` | 正的无符号 64 位整数；由外部显式传入，不在本轮查询真实模块 |
| `caller_rva` | 仅 `0xa56bbe` 或 `0xa56bec`；分别对应 CSIDL `0x1c`、`0x1a`，来源为[既有调用点](legacy-source-observation-plan.md#observation-contract)；module_base 加 RVA 不得溢出 |
| `entry_rsp` | 进入函数时非零的无符号 64 位 RSP，entry_rsp 加 8 不得溢出 |
| `return_address` | 从 entry_rsp 处完整读取的 8 字节小端返回地址，必须非零；不凭它推测调用指令长度或宣称已验证原机器码 |
| `hwnd` | RCX 原指针值，本已核调用只接受 0 |
| `buffer_address` | RDX 原指针值，必须非零且加 read_limit 不溢出 |
| `csidl` | R8 的低 32 位，必须与 caller_rva 对应 |
| `f_create` | R9 的低 32 位，本已核调用只接受 0 |
| `raw_bool` | 返回 RAX 低 32 位按有符号 BOOL 解释，范围 `-2**31..2**31-1`，不把非零规范成 1 |
| `raw_hex` | 此次读取所得原 bytes 的小写十六进制文本，无空格或前缀；最长 520 个字符、长度必须为偶数，解码字节数不得大于 read_limit；不补 NUL 或清理尾部 |
| `read_limit` | 精确整数 1..0x104，是计划读取上限，不表示原 API 的任意通用容量契约 |
| `read_complete` | 严格 bool，是读取回调对本次有界读取的声明，不由文本中有没有 NUL 推导 |
| `encoding` | 调用者明确提供、由现有缓冲组件支持的非空编码名，保留原名；不读取本机 ACP／locale 来猜 |

审计器须实际调用 `decode_shell_folder`，不能复制一套解码规则。报告以 call_id 和事件位置绑定解码结果；原事件摘要仍对应完整原输入，解码 bytes 若输出 JSON 使用明确的十六进制表示。v1 的报告不宣称检查这些新字段。

`read_complete=false` 必须导致该次 v2 完整性检查不通过，即使已经读到 NUL。BOOL 非零时若解码器给出 unknown，也不能通过此扩展的快照检查。BOOL 为 0 且读取已完整时，可以保留无 NUL 或解码失败的残留缓冲并通过结构检查，但不得消费为路径；API 调用失败、缓冲文本不可用与采集不完整必须分别保留。所有结果继续 `source_attribution=null`、`execution_ready=false`，结构通过不是来源或执行批准。

## Win64 纯提取核心接口

约定新模块 `tools/legacy_source_call_capture.py` 提供：

```python
begin_shell_folder_call(registers, *, module_base, caller_rva, encoding,
                        read_memory, read_limit=0x104)
finish_shell_folder_call(entry, registers, *, read_memory)
```

进入寄存器映射须恰含 `rcx`、`rdx`、`r8`、`r9`、`rsp`；返回映射须恰含 `rax`、`rip`、`rsp`。所有值是无符号 64 位精确整数。begin 只通过回调读取 entry_rsp 处 8 字节返回地址，保留调用状态；finish 验证 RIP 等于保存的 return_address、RSP 等于 entry_rsp+8 后，才读取保存的 buffer_address。它不能改用返回时的 RDX，因为 Win64 ABI 将 RDX 作为易失寄存器，返回时不保证仍保存该参数。返回值为上表唯一 capture 对象。

`read_memory(address, size)` 的回调结果必须恰含 `data`（原 bytes）和 `complete`（严格 bool）。请求不超过上述明确范围，回调短读／失败不能被补齐或重新解释为成功。返回地址读取要求 complete=true 且恰为 8 字节，否则 begin 拒绝并保留调用者的失败记录。缓冲读取允许 complete=false 或较短数据进入 capture，随后由审计器拒绝不完整回执；`complete=true` 是回调声明，不要求填满 read_limit，但不能超请求。回调异常保持失败，不生成伪造快照。

提取核心不导入或调用 ctypes、OpenProcess、ReadProcessMemory、调试事件或任何真实 API；不查进程／窗口／环境，不启动目标。合成测试应核符号 BOOL、R8D／R9D 位宽、地址溢出、返回 RIP／RSP 错配先于缓冲读取、进入后调用者改写输入不影响保存参数、失败与短读、260 字节边界。真实采集后端、ABI 现场验证及模块／编码来源仍缺。

## 验收与后续

协调验收两个独立提交的代码、拒绝边界和有意义的合成测试，统一补主题与索引，再用提取核心实际输出构造 v2 事件送入审计器，核对原字节和解码结果的对应关系。跨模块验证属于离线集成，不能写成目标运行或联合采集通过。

纯提取核心已交付并经协调审源及20项父树测试，见[接口与失败边界](legacy-source-call-capture.md#interfaces)；实际实现按本协议输出14字段，不读取真实进程。后续审计v2已交付并经父审，协调以提取核心实际输出增加6项跨模块测试，完整集成回归100项全过，见[离线互通验收](legacy-source-observation-audit.md#capture-v2-integration)。本协议和合成测试不替代真实采集回执。后续[有界读取到session组装](legacy-source-observation-session.md#reader-session-integration)已通过7项实际组件合成互通，完整回归151项通过；真实工厂、身份／隔离及运行观测仍未实测。

用户最新要求“如果有需要控制电脑跟我说先”。需要桌面控制时必须先说明具体操作并等待用户确认，本轮不进行这些动作；真实目标启动、调试连接和隔离试验亦不在本轮执行范围。EX-003／EX-005 与原完成条件继续保留。
