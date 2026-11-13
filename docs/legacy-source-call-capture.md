# Shell32 调用快照的纯提取核心

本组件接续 [EX-005](exploration-backlog.md#ex-005)，实现[冻结 Shell32 capture 契约](legacy-source-capture-binding.md#shell32-capture-binding)中的 `begin_shell_folder_call` 与 `finish_shell_folder_call`。它只接收模拟寄存器和调用者注入的 `read_memory`，将一次进入／返回拆成可审的纯数据步骤；**没有真实进程、调试或 Windows API 后端，也不能称为已完成真实采集器。**

独占实现为 [legacy_source_call_capture.py](../tools/legacy_source_call_capture.py)，仅使用标准库，并复用[缓冲解释组件](legacy-source-api-buffers.md#result-contract)。不修改已有解码器、审计器或共用契约。审计 v2 的跨模块验收由协调集成，不在本报告把本地合成测试当作已经接通真实事件链。

<a id="interfaces"></a>

## 模拟接口与调用顺序

本节继续[EX-005](exploration-backlog.md#ex-005)，说明仅用于显式合成输入的提取接口。

```python
begin_shell_folder_call(registers, *, module_base, caller_rva, encoding,
                        read_memory, read_limit=0x104)
finish_shell_folder_call(entry, registers, *, read_memory)
```

进入映射须恰含 `rcx/rdx/r8/r9/rsp`，返回映射须恰含 `rax/rip/rsp`。所有寄存器都是 `0..2**64-1` 的精确整数，拒绝 bool、浮点、数值字符串和缺失／额外字段。返回映射不接受额外 RDX，缓冲地址始终来自保存的进入参数。

begin 的顺序为：

1. 复制进入映射中的整数；验证模块基址、冻结 caller RVA、地址相加、hwnd、CSIDL、fCreate、读取上限和显式编码。`caller_rva=0xa56bbe` 对应 `R8D=0x1c`，`0xa56bec` 对应 `0x1a`；hwnd 和 R9D 只接受 0。
2. **仅调用一次 `read_memory(entry_rsp, 8)`**，要求 `complete=True` 且 data 恰为 8 字节；按小端取非零返回地址。不读缓冲、不额外读代码或指针目标。
3. 返回只含不可变标量的冻结状态对象。它不引用输入寄存器字典，也不保存内存回调；进入读取期间或之后调用者修改原字典，不改变保存值。状态的正常字段赋值会拒绝。

finish 重新验证局部状态和返回映射后，要求 `rip==return_address` 且 `rsp==entry_rsp+8`。任何错配都在缓冲回调前拒绝；匹配后才调用一次 `read_memory(saved_buffer_address, read_limit)`。返回 RAX 的低 32 位按有符号 BOOL 转换，保留 -1、INT_MIN 或任意其它非零值，不规范成 1。

`entry` 是局部值对象，不是可信进程身份或不可伪造令牌；finish 复核其字段以拒绝非法状态，但不能证明这些值来自真实现场。组件也不分配 call_id、不管理线程栈或保证每个 entry 仅使用一次，重复／孤立／跨线程事件由共同审计契约检查。

<a id="memory-boundaries"></a>

## 内存回调与失败边界

`read_memory(address, size)` 是唯一内存接口，结果须恰含 `data: bytes` 与 `complete: bool`，不能带其它字段。data 超过请求大小时拒绝，不自动切片；bytearray、文本、数组、隐式 complete=1 均拒绝。调用方提供的回调结果不被修改。

模块基址、RSP、缓冲和返回地址均须非零且符合各自无符号 64 位范围；模块基址加 caller RVA、RSP 加 8、缓冲地址加 read_limit 不得溢出。读取上限精确为整数 `1..0x104`。本轮不另行猜测地址的 Windows 映射、规范地址位或可访问性，实际读取由回调决定；非零数值不等于真实有效指针。

| 情况 | 核心处理 |
| --- | --- |
| 栈返回地址短读、未完成、超过请求或全零地址 | begin 拒绝，不生成 entry，不读取缓冲。 |
| 返回 RIP／RSP 不匹配 | finish 拒绝，不调用缓冲回调。 |
| 缓冲短读或 `complete=False` | 保留原 bytes 和原 complete 声明，不补 NUL／尾部，不伪造完整；后续审计器按 v2 规则拒绝不完整采集。 |
| 缓冲较短但 `complete=True` | 原样保留；共用契约允许读取计划在 NUL 后结束，不以 `len(data)<read_limit` 擅改完成声明。 |
| 回调异常 | 原异常向上传递，不重试、不吞错、不生成伪造 capture。失败记录由调用者保存。 |
| 字段、地址、回调结果格式错误 | 抛出带中文说明的 `CallCaptureError(ValueError)`；显式编码格式错误也可由复用组件抛出 `SnapshotFormatError(ValueError)`。 |

R8、R9 的高 32 位允许有其它值，但只取 R8D／R9D；RAX 同样仅解释低 32 位。寄存器本身仍须为完整无符号 64 位整数，不能把 -1 直接作为模拟 RAX 输入；例如 `0xffffffff` 或 `0xffffffffffffffff` 的 BOOL 都解释为 -1。

begin 使用已有 `decode_shell_folder` 对空的内部格式检查输入验证编码和读取声明，检查结果不会发布成观测记录；finish 对实际回调 bytes／BOOL 再调用同一公共解码器。不复制另一套编码规则，也不把解码状态插入 capture。BOOL 失败后的残留、成功但未知文本、无 NUL、严格解码错误都能保留为原快照，由审计器决定是否可接受。

<a id="capture-object"></a>

## 输出对象与编码来源

finish 成功返回的对象**恰含**以下 14 个字段，名称和类型与[共用字段表](legacy-source-capture-binding.md#shell32-capture-binding)一致：

```text
api, module_base, caller_rva, entry_rsp, return_address, hwnd,
buffer_address, csidl, f_create, raw_bool, raw_hex,
read_limit, read_complete, encoding
```

`raw_hex` 是实际读取 bytes 的小写十六进制，无前缀或空白；第一个 NUL 后的原尾部也保留。`read_complete` 完全来自回调，不从 NUL 推导。`encoding` 保留调用者原名，例如 `windows-1252`，不改成规范名；模块与编码来源必须由外部证据绑定，本轮**仍缺现场来源证明**。核心不读取本机 ACP、locale 或环境来补它，也不增加 `encoding_source` 等契约外字段。

输出没有路径解释、来源归因、执行准备、事件序列或 call_id 字段；这些由相应消费者按共同契约分别处理。返回地址只证明合成栈快照里有该整数，不依据它推测 CALL 指令长度，不宣称验证了目标机器码。

<a id="synthetic-example"></a>

## 合成调用示例

以下数值和 bytes 全部在内存中自造，回调不访问进程或本机目录：

```python
from tools.legacy_source_call_capture import (
    begin_shell_folder_call, finish_shell_folder_call,
)

return_address = 0x140000123
memory = {
    0x1000: {'data': return_address.to_bytes(8, 'little'), 'complete': True},
    0x4000: {'data': b'X:\\synthetic\0tail', 'complete': True},
}
requests = []
def read_memory(address, size):
    requests.append((address, size))
    return memory[address]

entry = begin_shell_folder_call(
    {'rcx': 0, 'rdx': 0x4000, 'r8': 0x1c, 'r9': 0, 'rsp': 0x1000},
    module_base=0x140000000, caller_rva=0xa56bbe,
    encoding='cp1252', read_memory=read_memory,
)
result = finish_shell_folder_call(
    entry, {'rax': 0xffffffff, 'rip': return_address, 'rsp': 0x1008},
    read_memory=read_memory,
)
assert requests == [(0x1000, 8), (0x4000, 260)]
assert result['raw_bool'] == -1
assert bytes.fromhex(result['raw_hex']) == b'X:\\synthetic\0tail'
```

这只演示提取顺序，不能把 requests 当真实内存读取回执。未来后端必须另行证明寄存器取样、返回配对、模块和编码来源、时间／进程身份及读取完整性；本轮没有实现或调用该后端。

<a id="validation"></a>

## 验证与交付限制

`python -B tests/test_legacy_source_call_capture.py` 首轮 20 项全过，退出 0；原回执保存为本树 `.local-analysis/ex005-call-capture/unit-first.json`。测试覆盖两个 caller 与 CSIDL、R8D／R9D 高位及 BOOL -1／INT_MIN、模块／栈／缓冲溢出及上界、零／非法字段、错配返回先于缓冲访问、栈短读拒绝、缓冲短读原声明、260 字节边界与尾部、输入不变／进入后改输入、回调异常和对公共解码器的实际复用。合成文件 fixture 只在本任务忽略目录创建并自动清理，没有读写旧现场或旧任务证据。

指定分支为 `feat/ex005-call-capture`，从已含 `22d479e` 和共同字段登记的最新 `origin/dev` 基线 `f355d7ba180db69128e91d4e7234e56fe2e842b3` 建立。实际 Pi `01a1d4e9-989e-71e2-b4f9-f52f961a53f7`，PI 变量和最新会话 model／thinking 事件为 `deng/gpt-6.1-sol/high`；初始 Git 干净、首工具和身份检查退出 0，startup 回执已通过本次新 Dispatch 发协调。

当前没有测试失败，首轮原成功回执保留。`python -B tools/check_exploration_docs.py` 实际退出 1，检查 165 份 Markdown／1335 个本地链接／41 个事项／137 处来源／149 份报告，唯一错误是本新报告尚未在完整资料索引中恰好出现一次，原回执 `docs-first.json` 保留，由协调统一入链，没有修改共享文件。`git diff --check` 退出 0；提交前另以 `git diff --cached --check` 检查三份新增文件实际暂存内容，回执随交付保存。

协调已完整审阅131行工具、299行测试、本文和原delivery.json，核对14字段、进入参数独立保存、返回RIP／RSP检查先于缓冲读取、BOOL低32有符号及R8D／R9D规则；在独立集成分支运行20项父树测试全部通过，未修改实现。父验收记录为协调树`.local-analysis/ex005-capture-binding-0174/call-capture-parent-review.json`，子代理未索引的原exit1保留，协调另补双向链接及索引。审计v2的实际接收及跨模块合成验证仍待后续交付，不把这20项测试算作已完成互通。

本轮不启动目标、接进程、调试、调用 Windows API、查询窗口、控制桌面或读取实时用户源，不制作配置／plan／GO；用户若需后续控制电脑须先说明并确认。本次完成的是纯提取核心的有界开发，实际采集、ABI 现场验证、隔离与阶段 Host I/O、Property／查询输出及原创建者退出见证仍缺，不结 EX-003／EX-005，也不追认历史运行。
