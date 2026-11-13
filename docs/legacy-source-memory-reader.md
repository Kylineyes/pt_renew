# Win64 有界只读内存适配器

本组件接续 [EX-005](exploration-backlog.md#ex-005) 与[调用快照纯提取核心](legacy-source-call-capture.md#interfaces)，提供借用外部显式 HANDLE 的有界读取回调。[实现](../tools/legacy_source_memory_reader.py)已编写，注入函数的合成验证已进行；**Windows ABI 现场、真实 HANDLE／权限、真实进程内存读取及进程身份均未实测，不能称已完成采集后端。**

版本文件仅为该实现、[本次测试](../tests/test_legacy_source_memory_reader.py)与本文；不修改提取核心、解码器、审计器、共用 capture 契约或其它 worker 的事件组装模块。

<a id="injected-interface"></a>

## 注入接口与固定 ABI

```python
make_memory_reader(process_handle, *, read_process_memory, get_last_error)
```

返回对象可直接作为 `read_memory(address, size)` 使用，输出**恰为** `{'data': bytes, 'complete': bool}`。构造不执行读取、不加载 DLL；模块导入也不调用 `WinDLL`。仅使用标准库的 ctypes 类型与本地缓冲，不查询本机进程、环境、窗口或用户配置。

注入 RPM 必须接受以下参数约定，参数都由适配器显式构造，不把 Python 大整数交给缺省 ctypes 签名截断：

| 顺序 | 参数／结果 | 明确类型 |
| --- | --- | --- |
| 1 | 借用的进程 HANDLE | `ctypes.c_void_p`，宿主须为 64 位指针 |
| 2 | 被读地址 | `ctypes.c_void_p` |
| 3 | 本地输出缓冲地址 | `ctypes.c_void_p`，仅供 native／模拟 native 写入本地缓冲 |
| 4 | 请求字节数 SIZE_T | `ctypes.c_uint64` |
| 5 | 实际字节数输出指针 | `ctypes.POINTER(ctypes.c_uint64)` |
| 返回 | 原 BOOL | native `restype=ctypes.c_int32` 所产生的 Python 精确整数，范围 `-2**31..2**31-1`；不将非零改成 1 |

代码不使用宿主 `c_long` 表示 Windows LONG／BOOL。`get_last_error()` 的注入返回值须为 `0..2**32-1` 的精确整数，表示 DWORD；失败时的 0 也原样保留，不据它改称成功。注入 Python 函数须返回符合该约定的整数，`ctypes.c_int32(-1)` 对象、无符号 `0xffffffff`、bool、浮点、字符串或越界整数均拒绝，不靠隐式转换修补。

<a id="bounds-and-ownership"></a>

## 参数边界与句柄借用

`process_handle` 为外部显式给出的正无符号 64 位精确整数；拒绝 0、负数、bool、浮点、字符串及 ctypes 包装对象。另排除 -1 至 -6 的无符号 64 位伪句柄表示及其常见错误的 32 位零扩展表示。这是**数值格式及已知伪句柄门**，不能证明任意其它整数是真实有效句柄，更不能证明它关联指定进程或具有读取权限。

组件不接收 PID，不执行 OpenProcess、CloseHandle、启动、枚举、调试或提权。句柄始终由外部所有者负责生命周期，须在适配器使用期间保持有效；本组件不等待退出、不从句柄推断创建身份、模块或权限。不提供析构关闭行为，失效句柄只能由后续 native 回执反映，不能据数值检查当作已核身份。

每次调用要求地址为非零无符号 64 位精确整数，size 为 `1..260` 精确整数，且 `address+size<=2**64-1`；拒绝 bool／浮点／字符串／溢出后才允许调用 RPM。只检查上述边界，不猜真实地址映射、规范地址位或页面可读性。每次至多一次 RPM，不重试、不扩大范围、不写目标，不追加 NUL 或零字节。

对象按串行调用设计；`last_receipt` 是局部最近一次尝试的诊断，不是线程安全账本或不可伪造的进程见证。需要并发时，调用者须另行同步或使用独立对象，本轮没有实现调试线程调度器。

<a id="results-and-errors"></a>

## 读取结果、即时错误码与独立诊断

输出只取本地缓冲中 `transferred` 声明范围内的原前缀。分配缓冲的初始化字节及 native 写入但未声明传输的尾部都不发布。传输计数先设为 `UINT64_MAX` 哨兵；native 未写计数或计数超过 requested 时拒绝发布，不能把初始计数当作零读成功。组件仍需信任注入／native 对输出计数与内容的声明，无法仅凭 ctypes 证明每个被声明字节确实来自目标。

| native 回执 | 二字段读取结果 |
| --- | --- |
| BOOL 非零且 transferred 等于 requested | 发布精确前缀，`complete=True` |
| BOOL 非零但 transferred 小于 requested，包括 0 | 仅发布前缀，`complete=False`；不读取陈旧 last error |
| BOOL 为 0，transferred 在请求内，包括完整数量或 0 | 先立即取错误码，仅发布对应前缀，`complete=False`；失败不能被完整数量冲销 |
| transferred 超 requested／未写计数，或 BOOL／错误码非法 | 抛 `MemoryReaderError(ValueError)`，不返回伪造快照 |
| RPM 或错误码回调抛异常 | 原异常向上传递，不重试、不吞错或构造成功结果 |

native BOOL 为 0 时，紧接 RPM 返回即调用注入的 `get_last_error`，在读取和验证传输计数前完成；成功时不查询错误码。若回调本身异常，无法取得可靠回执，保持异常而非补 0。错误码函数必须与 RPM 同线程、对应同一 native 错误存储；注入者若返回旧错误，本组件无法证明其真实性。

`reader.last_receipt` 与二字段回调完全分离，返回以下事实的副本：

```text
requested, transferred, raw_bool, error
```

它保存的是 **ReadProcessMemory 的 BOOL**；[14 字段 capture](legacy-source-capture-binding.md#shell32-capture-binding)中的 `raw_bool` 则来自 **Shell32 返回 RAX**，二者不能混用。测试特意覆盖 RPM 失败而 Shell32 BOOL=-1 的组合，原 capture 仍保留 -1，读取完整性单独为 false。

每次尝试（包括参数拒绝）开始先清空旧诊断；参数失败、native 异常、BOOL／错误码格式不合法时保持 `None`，不会把上次成功诊断留作当前结果。有效四字段已取得后，超量计数异常可保留该次四字段供审查，但它**不是成功标志**，调用仍然抛错。`last_receipt` 不加入二字段回调或 capture，不改变共用协议；读取副本的调用者修改字典也不影响内部记录。

<a id="synthetic-use"></a>

## 纯合成接口示例

```python
import ctypes
from tools.legacy_source_memory_reader import make_memory_reader

calls = []
def fake_rpm(handle, address, destination, requested, transferred):
    calls.append((handle.value, address.value, requested.value))
    raw = b'A\0B!'
    assert requested.value == len(raw)
    ctypes.memmove(destination, raw, len(raw))  # 仅写调用者的本地合成缓冲
    transferred.contents.value = len(raw)
    return -1

reader = make_memory_reader(
    0x1234, read_process_memory=fake_rpm,
    get_last_error=lambda: (_ for _ in ()).throw(AssertionError('成功不能取错误码')),
)
result = reader(0x4000, 4)
assert result == {'data': b'A\0B!', 'complete': True}
assert reader.last_receipt['raw_bool'] == -1
```

此处整数 HANDLE／地址全部自造，ctypes.memmove 只覆盖本地分配缓冲，不访问对应远程地址。把 reader 传给现有 begin／finish 时，栈请求为 8 字节，缓冲请求为显式有界上限；适配器不解析返回地址、编码或目录，不推断调用阶段。

<a id="windows-factory"></a>

## 已编写但未调用的 Windows 工厂

`make_windows_memory_reader(handle)` 仅在调用者显式调用时才检查 `sys.platform=='win32'` 和 64 位指针，加载 `ctypes.WinDLL('kernel32', use_last_error=True)` 并绑定 ReadProcessMemory 的上述 argtypes／固定 32 位 restype。它借用同一个外部句柄，构造完成仍不执行读取；只有之后调用 reader 才可能触发真实 RPM。错误码使用与 use_last_error 配套的 `ctypes.get_last_error`。

本轮所有测试**不调用该工厂**，也不调用 native API；导入与注入构造在禁止 WinDLL 加载的测试下验证。工厂代码存在不代表 Windows 实机的调用约定、权限、真实句柄、进程身份或读取能力已经验证，后续使用需要另行审查授权和现场回执。

<a id="validation"></a>

## 本轮验证与剩余缺口

验证命令 `python -B tests/test_legacy_source_memory_reader.py`：最终 20 项合成测试通过，退出 0，原回执 `unit-final.json`。首轮在用包导入旧审计器时发生 `ModuleNotFoundError`，测试尚未进入；新测试改用既有 tools 搜索路径和模块导入惯例后通过，未改旧实现。原 `unit-first.json`（exit1）与 `unit-second.json`（exit0）保留在本树 `.local-analysis/ex005-memory-reader/`；随后补充 RPM 与 Shell32 两类 BOOL 不混用的断言，最终回执另存，不覆写失败记录。

测试核对固定类型宽度、BOOL -1／INT_MIN、完整／成功短读／失败部分／零读、即时错误码和成功不读旧错、超量及未写计数、溢出与非法／伪句柄、回调异常与旧状态污染、导入和注入不加载 DLL。实际以新 reader 接已有 begin／finish 的合成互通检查了 8 字节栈＋260 字节缓冲、NUL 后的原尾部，以及部分 RPM 导致现有 v2 的 `incomplete_snapshot` 拒绝；这仅证明组件数据链自洽，不是实际目标采集。

本轮分支 `feat/ex005-memory-reader` 基于含 `733b977` 和本轮领取登记的 `origin/dev`，精确基线 `98d8f0de37bfe0730b2da569e72e4041f5239f12`。实际 Pi `01a1d4e9-989e-71e2-b4f9-f52f961a53f7`，环境及最新会话 model／thinking 事件均为 `deng/gpt-6.1-sol/high`；首工具、干净 Git 与 startup 回执已核并以本次 Dispatch status 报协调。合成 fixture 仅放本任务忽略目录并自动清理；本轮未调用真实工厂、Windows API、进程枚举／连接／调试／启动或桌面控制。

`python -B tools/check_exploration_docs.py` 实际退出 1，检查 166 份 Markdown／1363 个本地链接／41 个事项／139 处来源／150 份报告，唯一错误为本文尚未在完整资料索引中恰好出现一次，原 `docs-first.json` 保留，由协调统一入链，没有修改共享索引。`git diff --check` 退出 0，提交前另以 `git diff --cached --check` 核对三份新增文件实际暂存内容，回执随交付保存。

真实后端运行、ABI 实机、权限／句柄生命周期和进程身份、模块／编码来源、隔离、完整阶段 Host I/O、Property／windir、GET 及原创建者退出见证仍缺；不签现场 GO、不结 EX-003／EX-005。用户如需后续控制电脑，应先说明具体操作并等待确认，不能据本轮开发授权直接执行。

<a id="parent-review"></a>

## 协调验收：注入读取与已有提取／审计互通

本节接续[EX-005](exploration-backlog.md#ex-005)。协调完整审阅107行工具、322行测试、本文及原delivery中的首轮导入失败、两轮成功与索引失败回执；在独立集成分支运行20项父树测试全部通过，原实现未修改。固定BOOL／SIZE_T、立即取失败错误码、单次读取、仅发布transferred前缀及旧诊断清理符合接口；导入和注入构造不加载DLL。

测试直接以reader调用既有begin／finish并送v2审计，保留RPM和Shell32两个BOOL、完整原尾部；部分缓冲读取由v2以incomplete_snapshot拒绝，栈短读由begin拒绝。父证为协调树`.local-analysis/ex005-backend-session-49f8/memory-reader-parent-review.json`。协调统一补主题、索引和待办链接，子代理原未索引exit1及测试导入exit1保持。

此验收仅接受有界读取适配代码及模拟native互通；Windows工厂从未调用，真实ABI／句柄／权限／内存／身份／隔离与退出未实测。这20项只核读取适配；后续协调已用实际读取适配与组装器补7项跨模块合成测试，完整回归151项通过，见[读取到组装的父验收](legacy-source-observation-session.md#reader-session-integration)。真实Windows工厂未调用，当前结论仍限离线链路。
