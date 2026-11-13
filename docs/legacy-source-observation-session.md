# Shell32观测事件的纯数据session组装器

本组件接续[EX-005](exploration-backlog.md#ex-005)，将[现有begin／finish提取核心](legacy-source-call-capture.md#interfaces)输出按[冻结schema v2契约](legacy-source-capture-binding.md#shell32-capture-binding)组装，再实际调用[已有审计器](legacy-source-observation-audit.md#schema-v2-shell32-binding)。它不连接进程、读取本机时间／ACP／模块、调用Windows API或创建目标。**通过只表示合成事件在现有协议下自洽，source_attribution恒null、execution_ready恒false。**

<a id="observation-session-interface"></a>

## 显式输入与状态接口

[实现](../tools/legacy_source_observation_session.py)只提供库接口，无CLI、回放文件格式或新采集schema；[合成测试](../tests/test_legacy_source_observation_session.py)直接复用实际提取和审计函数。本节继续[EX-005](exploration-backlog.md#ex-005)。工具目录须在调用者的Python模块搜索路径中，与现有审计库的顶层导入惯例一致。

```python
ObservationSession(identity, *, start_at, coverage, lost_events, truncated_events, read_memory)
session.begin_api(registers, *, module_base, caller_rva, encoding, read_limit, phase, at)
session.return_api(call_id, registers, *, snapshot_at, return_at)
session.append(kind, data, *, at)
session.end(*, at, coverage, lost_events, truncated_events, complete)
session.report()
```

| 输入／返回 | 确切约束 |
| --- | --- |
| identity | 字典恰含run_id、pid、creation_filetime、image_sha256；类型和范围由原审计器检查。正FILETIME可为精确整数或无前导零十进制字符串，超过2^53不转float；后续事件固定使用保存身份 |
| at／start_at／snapshot_at／return_at | 字典恰含tid、utc_ns、monotonic_ns；TID为1..2^32-1精确整数，两个时点为0..2^64-1精确整数。拒绝布尔、浮点和额外身份字段；不调用本机时钟补值 |
| coverage／lost_events／truncated_events／complete | 调用者必须明确提供，既有覆盖字段、零丢失／截断门及结束布尔仍交原审计器检查。构造或结束时不提供零值默认，也不据本地seq推断外部零丢失 |
| begin_api参数 | registers及模块／站点／编码／读取上限按现有提取契约；phase显式提供。成功返回本地唯一call_id，不按返回地址去重，不要求调用者自行制作capture |
| return_api参数 | registers恰含原rax/rip/rsp。snapshot_at与return_at分别提供；其TID必须相同，调用ID须为该线程栈顶，两个单调时点不得倒退。成功返回独立capture副本 |
| append | 只接受原call_enter/call_return及file_open/read/close；call_enter仅operation=parse，call_return仅能结束已知栈顶parse。data的精确字段、句柄与parse关联、数量及生命周期交原审计器检查；禁止API进入／返回、api_snapshot、run_start/end和身份变更旁路 |
| end／report | end返回独立session报告；report随时只读返回当前前缀、诊断、未返回调用和现有审计结果。返回对象或输入对象的后续变更不会改内部事件或旧报告 |

所有输入字典、时点、原parse/file data和寄存器在本操作使用前独立复制。提取核心另保存不可变进入状态；编码和模块只取显式参数，不从本机猜。注入的read_memory是外部可调用对象，本库保存该引用但不复制其闭包或宣称其真实来源。缺少或未知Python关键字由函数签名拒绝，不生成事件；已进入session操作的字段错误会封存失败。

## 调用顺序与失败封存

每线程有独立调用栈，支持串行提交的两线程交错、同线程嵌套及同返回地址的不同调用。本库不创建线程，也不提供并发调用的锁或吞吐保证；同一实例应串行使用，回调重入修改会封存失败，即使回调吞掉该异常也不能恢复通过。

begin_api先通过已有审计器验证并保留call_enter，再登记待完成调用并实际调用begin_shell_folder_call。返回地址短读、异常或参数失败均不删除进入事件；pending_calls保留call_id、TID、operation及entry_ready，诊断保留阶段、异常类型、说明、前缀长度和可定位的本次调用／时点。

return_api首先核同线程栈顶ID、调用未返回及两个显式时点，之后才调用finish_shell_folder_call；finish自身先核RIP/RSP再读保存的进入RDX。错配／孤立／跨线程／非栈顶／重复返回不会读取缓冲。成功提取后，先组装api_snapshot，再用其原raw_bool组装call_return，两个事件使用各自提供的时点，不把一个本机时间复制成“自动捕获回执”。

| 结果 | session处理 |
| --- | --- |
| begin的栈读取失败 | 保留call_enter和entry_ready=false的未完成调用，不生成capture |
| finish回调异常或RIP/RSP错配 | 保留实际前缀及未返回调用，记录原异常类型／说明，不重试或补返回；KeyboardInterrupt等中断原样传播，同时封存session |
| finish产生read_complete=false或成功但unknown | 原capture作为api_snapshot保留，已有v2审计拒绝；不生成随后call_return，pending表示本组装器未发布经核验的返回记录，不代表断言目标从未返回 |
| 较短bytes但complete=true | 不擅改提供者声明；成功空串或其它结果按原v2与解码器规则决定 |
| parse/file非法、时点倒退或字段错误 | 保留可序列化的拒绝事件及审计诊断，封存失败；不可序列化输入只保留之前前缀和异常说明，不伪造有效事件 |
| end时未返回调用、非零丢失／截断、不完整或覆盖不符 | 保留实际提交的结束声明及原前缀，返回失败报告；不删除失败call、补成功返回、重开session或凑出完整结果 |
| 失败后继续、二次结束或结束后追加 | 拒绝并记录session_sealed；没有重置接口，不读取更多内存、不改旧事件或已返回给调用者的报告 |

每次追加均实际调用audit_events检查完整候选前缀。未结束时仅允许missing_end、unreturned_call、unclosed_file作为暂时未闭环状态；其它问题立即封存。结束时要求原审计完整通过，report再对保留的前缀实际审计。继承原4MiB／64KiB单行／10000事件限制，不承诺长时高吞吐；重复前缀审计有额外开销，没有复制另一套字段、解码或文件生命周期算法。

报告顶层integrity_passed要求state=ended、无session诊断且子audit.integrity_passed为true。二次结束等操作可能使原事件前缀仍自洽、子audit仍为true，但顶层state=failed且integrity_passed=false；调用者必须检查顶层，不能只取子审计结果。之前已返回的独立报告保持其当时内容，不事后覆写。

<a id="synthetic-session-example"></a>

## 可直接运行的合成示例

以下从仓库根目录运行，只使用自造整数和bytes；身份、时间、模块与覆盖均为夹具声明，不是本机或目标取样：

```python
import sys
sys.path.insert(0, 'tools')
from legacy_source_observation_session import ObservationSession

identity = {'run_id': 'synthetic', 'pid': 123,
            'creation_filetime': '134390106270047430', 'image_sha256': 'a' * 64}
coverage = {'from': 'before_first_target_instruction', 'until': 'process_exit',
            'domains': ['directory_api', 'parse', 'file_io']}
def at(n):
    return {'tid': 11, 'utc_ns': 1794573455000000000 + n,
            'monotonic_ns': 9007199254740993 + n}
returned = 0x140000123
memory = {0x1000: {'data': returned.to_bytes(8, 'little'), 'complete': True},
          0x4000: {'data': b'X:\\synthetic\0\xfftail', 'complete': True}}
def read_memory(address, size):
    return memory[address]

session = ObservationSession(identity, start_at=at(0), coverage=coverage,
    lost_events=0, truncated_events=0, read_memory=read_memory)
call_id = session.begin_api(
    {'rcx': 0, 'rdx': 0x4000, 'r8': 0x1c, 'r9': 0, 'rsp': 0x1000},
    module_base=0x140000000, caller_rva=0xa56bbe, encoding='ascii',
    read_limit=260, phase='synthetic', at=at(1))
session.return_api(call_id, {'rax': 0xffffffff, 'rip': returned, 'rsp': 0x1008},
    snapshot_at=at(2), return_at=at(3))
report = session.end(at=at(4), coverage=coverage,
    lost_events=0, truncated_events=0, complete=True)
assert report['integrity_passed']
assert report['audit']['api_snapshots'][call_id]['capture']['raw_bool'] == -1
assert report['source_attribution'] is None
assert report['execution_ready'] is False
```

events为按原v2组装的独立事件列表，seq和API call_id是本地生成值，原parse/file调用ID保留不改；身份／时间／原缓冲仍按显式输入保存。子audit.input摘要是**组装事件的canonical_jsonl摘要**，digest_scope另明确它不是外部原始采集文件；不冒称保留了未提供的原日志字节、真实时序或外部丢失计数。没有文件读写／CLI或现场conf、plan、GO输出接口。

<a id="validation-and-open-items"></a>

## 验证、身份与剩余缺口

本轮Task task_22cc9edd4046／Dispatch ctx_70ed4bb6d117，沿实际Pi会话01a1d4e9-ce67-756e-8b4e-17d0dd926e95、deng/gpt-6.1-sol/high。环境／最新model与thinking事件、干净Git及首工具exit0已核，先发status msg_8d77d9443cd6；providerRejected／ECONNRESET通知后保留原任务和失败，随后只读git命令实际exit0并回报msg_1d2f99d6cd67，未重建／换模型／重计时间。fetch后确认基线含733b977及本轮登记，从98d8f0de37bfe0730b2da569e72e4041f5239f12建立feat/ex005-observation-session，只新增指定三个文件，不改提取／解码／审计核心、共用协议或共享入口。

验证命令：

```powershell
python -B -m unittest discover -s tests -p test_legacy_source_observation_session.py -v
python tools/check_exploration_docs.py
git diff --check
```

首轮22项合成测试全部通过，exit0，原回执本树.local-analysis/ex005-observation-session/tests-first.json保留；补失败调用定位及精确整数FILETIME／原parse输入独立保存后23项通过，回执tests-final.json；再补回调中断封存验证后最终24项全过，exit0，回执tests-interrupt-final.json。文档中的完整合成示例亦实际执行通过，exit0，回执example-check.json及example-result.json。当前没有测试失败，不将原网络通知冒称为测试失败或删除其历史。测试实际调用begin／finish／audit，无手造capture替代；覆盖两线程／嵌套／同返回地址、同路径多次打开、BOOL低32有符号及尾部、短读／抛异常／错配先于内存读、错误后不可恢复、输入和报告独立、结束与覆盖／丢失声明、原parse/file拒绝及无需本机时钟。所有磁盘fixture仅在本树任务忽略目录内创建并清理，诊断回执不覆写旧记录。

完整文档检查实际exit1：166份Markdown／1365链接／41开放事项／139来源细节／150索引报告，唯一错误为本文尚未在完整资料索引中恰好出现一次，原document-check.json保留，由协调统一入链；没有修改共享索引或忽略其它错误。差异检查与精确提交状态在本轮交付回执中保留。

真实进程读取后端、权限与ABI／模块／编码来源、用户根隔离、实际丢失检测、Property、windir、完整Host IO、GET输出及原创建者退出见证仍缺。另一个worker的读取适配未在本树调用或修改，协调将以其真实组件输出进行后续**合成**互通验收。本轮没有任何真实Windows API、进程枚举／连接／调试／启动、用户配置、窗口或桌面动作；如后续需要控制电脑，先说明并等待用户确认，不以组件测试作现场批准，也不结EX-003／005。
