# 联合观测记录的离线完整性审计 v1

[EX-005](exploration-backlog.md#ex-005)的[隔离与观测设计](legacy-source-observation-plan.md#observation-contract)需要将同一运行的进入、返回和文件访问分开绑定。[审计工具](../tools/audit_legacy_source_observation.py)现在只检查调用者显式提供的JSONL或内存事件：身份不变、序号与单调时点、覆盖声明、按线程的调用配对，以及解析范围内的文件生命周期。它不实现采集器、ETW、调试器或隔离器，不读取其它现场材料，不判断来源归因。

即使 `integrity_passed=true`，输出也始终包含 `source_attribution=null`、`execution_ready=false`。连续seq、零丢失声明、完整配对都只是输入内部自洽，不能证明真实采集没有漏报，也不能构成现场GO或EX-005闭环。

<a id="schema-v1"></a>

## 单运行schema v1

本节继续[EX-005](exploration-backlog.md#ex-005)，限定已提供事件的结构与配对。

一份输入只允许一个运行、一个进程身份；每个物理行是一个JSON对象。UTF-8严格解码，接受LF／CRLF及末行无换行；拒绝BOM、空行、重复JSON键（包括嵌套对象）、非有限数和任何浮点／指数数值。已知字段集合必须完全相符，不忽略扩展字段或未知kind。未来新增事件需先扩schema和消费者，不能把v1未检查的扩展内容装进现有字段冒称通过。

| 所有事件的必填顶层字段 | 类型与规则 |
| --- | --- |
| `schema_version` | 精确整数1 |
| `run_id` | 非空字符串；全运行不变 |
| `seq` | 从0开始逐条加1的精确整数，拒绝跳号、重排和重复 |
| `pid`、`tid` | 1至 `2^32-1` 的精确整数；PID全运行不变，允许多个TID交错 |
| `creation_filetime` | 1至 `2^64-1` 的JSON整数或无前导零的正十进制字符串；不转float。相同数值的整数与字符串视为同一身份，报告统一用十进制字符串输出 |
| `image_sha256` | 64位小写十六进制字符串，全运行不变；只检查声明，不读取或校验实际映像 |
| `utc_ns`、`monotonic_ns` | 0至 `2^64-1` 的精确JSON整数；分别声明UTC Unix纪元纳秒、单调时钟纳秒。后者按事件全序不得倒退，允许相等；UTC校时倒退不替代单调判断 |
| `kind`、`data` | 下表的枚举字符串及对应对象；不得缺项或加项 |

整数规则一律拒绝Python／JSON布尔冒充整数，也不把 `1.0`、`1e0`或浮点FILETIME四舍五入为整数。PID相同但创建FILETIME差1也拒绝，避免PID复用误绑定。普通字符串最长1024个字符，不能为空／全空白，不能含ASCII控制字符、DEL或转义后孤立代理项；路径只是原样文字，不解析、规范化或访问其指向的文件。

| `kind` | `data`的完整字段集合 | 额外规则 |
| --- | --- | --- |
| `run_start` | `coverage`、`lost_events`、`truncated_events` | 必须为seq0且只能出现一次；两个计数均须为0 |
| `run_end` | 同启动三项，加 `complete`、`event_count` | 必须为最后一条；complete必须是布尔true，event_count含本结束条且等于输入事件数；计数非零／范围不足拒绝 |
| `call_enter` | `call_id`、`operation`、`name`、`phase`、`path` | call_id、name、phase为普通字符串；operation为api或parse；parse的path是普通字符串，api的path必须为null。本版不解析目录API参数和缓冲 |
| `call_return` | `call_id`、`result` | call_id必须匹配该TID栈顶；result为 `-2^63` 至 `2^64-1` 精确整数，parse另限为原始AL的0／1，不据此推正常EOF或属性接受 |
| `file_open` | `open_id`、`parse_call_id`、`path`、`success`、`handle`、`error` | 每次尝试均分配全新open_id，成功与失败都不能复用；path是普通字符串；关联本线程仍活动的parse；成功handle是非空字符串、error为null；失败handle必须显式为null、error为非负整数 |
| `file_read` | `open_id`、`parse_call_id`、`offset`、`requested`、`transferred`、`success`、`error` | 关联仍打开的成功open_id，parse与打开一致；三项数量为无符号64位精确整数；transferred不超requested，offset加transferred不溢出 |
| `file_close` | `open_id`、`success`、`error` | 必须有活动的成功打开；成功后释放其句柄绑定，失败保留活动状态，可在同一parse内重试 |

`success`必须是JSON布尔。读取和关闭同样要求成功时error为null、失败时error为非负精确整数；失败读取仍可有不超过请求量的部分传输，零传输也不自动解释为EOF。文件handle在本版是调用者定义的**精确、不归一化的非空字符串**，例如原始句柄的十进制文本；应在采集端统一表示。v1不把同一OS句柄的不同字符串写法识别为别名。

`coverage`对象严格含 `from`、`until`、`domains`：from为 `before_first_target_instruction`，until为 `process_exit`，domains列表恰好含 `directory_api`、`parse`、`file_io`且无重复。启动与结束对象内容必须一致，包含列表次序；三个域只是必须声明的最小范围，不证明真的从首次指令采集到退出。`lost_events`、`truncated_events`为无符号64位整数，非零时报告拒绝；工具不能检测采集端隐瞒的丢失。

<a id="pairing-contract"></a>

## 调用配对与解析文件关联

每个TID维护独立栈，因此支持两线程任意交错、同线程嵌套API和嵌套parse。call_id在整个运行中唯一，返回后也不能复用；重复ID、孤立返回、跨线程返回、先返回外层或重复返回均拒绝。结束时所有调用均须已返回；完整结束声明不能冲销未返回调用。

文件操作按open_id和活动handle关联，绝不按路径去重；同路径可有多次失败、先后或同时成功打开，前提是每次open_id不同且同时活动的handle字符串不同。关闭成功后允许另一个全新open_id复用同一个handle字符串；已关闭／失败打开的ID不能再读或关。

v1明确只支持文件事件在**打开线程及所属parse仍活动时**发生。文件read的parse_call_id必须与open相同；close由open_id继承关联。parse返回前必须成功关闭它打开的所有文件；跨线程共享句柄、异步IO、返回后延迟关闭均属于本版不支持的记录形态，会拒绝而不是猜配。文件path与parse path可不同，本版不推相对路径或归属，也不把open／Read或AL=1等同于属性写入。

phase和name仅为必须保留的有界文字，v1不检查phase是否覆盖[既有全部解析阶段](legacy-source-observation-plan.md#observation-contract)，也不验证RVA、实际模块基址、目录返回、输入文件身份、F表、Property或GET副作用。当前[查询契约](legacy-config-query-contract.md#minimal-contract)区分属性值、输出送达和CONFIG环境更新；这些语义并未被本审计器实现，不能用call_return替代其验收。

另外两个已验收的离线接口分别提供[两键命令数据](legacy-config-query-consumer.md#offline-query-consumer)和[目录API原缓冲解释](legacy-source-api-buffers.md#result-contract)。前者不执行查询；后者的bytes、BOOL和解码结果不在本版事件字段集合中，不能直接追加到data或塞进name／phase绕过校验。未来采集器接入时须先扩展并验证事件契约，再把原缓冲与调用ID、线程及来源回执绑定；当前没有将三个组件接成运行器或完成联合运行验证。

<a id="usage-and-results"></a>

## 使用、输出与边界

CLI只打开给出的一个输入路径，不扫描目录、不自动追踪事件中的path或发现其它日志。默认向stdout写完整JSON报告；可选择排他创建的新文件：

```powershell
python -B tools/audit_legacy_source_observation.py .local-analysis/ex005-observation-audit/fixture/events.jsonl
python -B tools/audit_legacy_source_observation.py .local-analysis/ex005-observation-audit/fixture/events.jsonl --output .local-analysis/ex005-observation-audit/fixture/report.json
```

以上路径仅示意调用者自造夹具，工具不会生成它们。输出已存在（包括输入本身、已有报告或链接）时拒绝覆写；不会自动创建父目录。新文件发生中途写出错误时可能留下不完整新文件，必须按失败处理，不作为有效回执。

| 退出码／接口 | 行为 |
| --- | --- |
| CLI 0 | 所提供记录在v1检查范围内通过，仍无归因／GO |
| CLI 1 | 形成失败审计JSON，包括畸形JSON／精度拒绝、配对／生命周期错误、缺少结束、丢失／截断或范围不足 |
| CLI 2 | 参数、输入读取或输出写入错误；不将OS错误伪装为通过的完整性报告 |
| `audit_jsonl(path)` | 返回报告；输入读取失败抛OSError。JSONL结构错误保存在issues，保留输入摘要 |
| `audit_events(events)` | 接受单个JSON兼容事件列表，返回报告；非列表、超事件数、不能序列化或NaN等非法内存输入抛ValueError，不修改调用者对象。内存浮点经严格JSONL路径拒绝 |

文件输入最多读取4MiB加1字节；超限只摘要已读前缀并标 `sha256_scope=read_prefix`，不得当全文件摘要。未超限时报告 `full_input`及原始bytes_read／SHA-256，CRLF和末行差异也保留；输入不加锁，摘要仅对应本次读到的字节，不保证并发写入期间的文件快照一致。每行上限64KiB、事件上限10000。内存接口先确定性序列化（字段排序、UTF-8、紧凑格式）再按相同字节／行上限检查，其摘要标 `canonical_jsonl`；不将规范化摘要称为原始文件摘要，也不承诺任意巨大已分配内存对象的资源上界。

报告包含精确身份、首个违规位置与稳定代码、已检查计数、仍未返回的call_id／未关闭open_id列表及限制说明。语法解码错误时不能构造可靠事件列表，summary保持空；结构检查在首个错误处停止，不修复或续接后面的事件，pending只表示此前已接受前缀的状态。无有效结束摘要必定不通过。所有结果都固定保留source_attribution=null、execution_ready=false。

<a id="validation-and-limits"></a>

## 合成验证与交付

新Task `task_a3d54c493dd5`／Dispatch `ctx_33b88db36304`，沿实际Pi `01a1d4e9-ce67-756e-8b4e-17d0dd926e95`、`deng/gpt-6.1-sol/high`续作。环境、会话model／thinking事件和成功工具回执已核并以status `msg_7f1a01135154`交当前协调；从干净旧交付树fetch，确认origin/dev含 `4c0cfe8`，基 `cf637ee6823adbc0ccff86e395c9e93a4c8347b6`建立 `feat/ex005-observation-audit`。只新增本工具、[合成测试](../tests/test_legacy_source_observation_audit.py)和本文，不修改前置报告、共享入口或另外两项并行模块。

所有文件夹具由测试建立在本树忽略目录 `.local-analysis/ex005-observation-audit/fixture-*`，测试结束清理；仅使用标准库。核验命令为：

```powershell
python -B -m unittest discover -s tests -p test_legacy_source_observation_audit.py -v
python tools/check_exploration_docs.py
git diff --check
```

测试覆盖双线程交错／嵌套、相同PID不同FILETIME、超过 `2^53` 的精确值、布尔／浮点／指数拒绝、重复JSON键／畸形UTF-8、缺起止摘要、范围／丢失／截断、重复调用／错配返回、同路径多个open、失败open无handle、读数量与关闭失败、显式单文件读取、原始摘要和排他输出。普通文件与硬链接的拒绝实际验证；符号链接附测仅在当前权限允许创建时执行，不据此证明全机权限或路径隔离。

首轮30项测试中29通过、1失败：重复call_id夹具复制了旧单调时间，先触发clock_reversed，未到预期duplicate_call检查；修正夹具新事件的时点后通过。原 `tests-first.json`保留exit1，第二轮 `tests-second.json`为33项全过；其后增加内存非法值／输入不变和直接未返回API用例，最终35项全部通过、exit0，回执 `tests-final.json`。另一次精确文本编辑因缩进不匹配被工具拒绝，未改文件，原工具回执保留。

新证据仅在本树 `.local-analysis/ex005-observation-audit/`，含身份、测试和最终文档／diff回执；未读取旧现场补新运行回执，未运行目标、GUI、控制服务、调试API、目录隔离或身份／VM试验，未制作现场配置、plan、候选或GO。文档检查实际exit1：161份Markdown／1279链接／41开放事项／133来源细节／145索引报告，唯一错误为本文尚未在完整资料索引中恰好出现一次，原回执 `document-check.json`交协调统一入链；未将其它错误视为预期。`git diff --check`实际exit0，暂存新增文件另核。EX-003／005及旧Task均不因该组件通过而结算。

协调已完整审阅323行工具、455行测试、本文及原tests-first／tests-final／delivery-state回执，在独立集成分支运行35项父树测试全部通过。首轮失败确为重复ID夹具用了旧单调时间，现有修正使其到达预期拒绝分支，原exit1保留；原实现未由协调修改。已核精确整数、单运行身份、线程栈／调用唯一性、独立open_id及失败关闭保留活动状态，父验收见协调树`.local-analysis/ex005-offline-0174/observation-audit-parent-review.json`。协调补齐主题／索引／EX-005双向链接及与另两组件的接口限制；验收仅接受离线审计能力。
