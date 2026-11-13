# 联合观测记录的离线完整性审计 v1／v2

[EX-005](exploration-backlog.md#ex-005)的[隔离与观测设计](legacy-source-observation-plan.md#observation-contract)需要将同一运行的进入、返回和文件访问分开绑定。[审计工具](../tools/audit_legacy_source_observation.py)现在只检查调用者显式提供的JSONL或内存事件：身份不变、序号与单调时点、覆盖声明、按线程的调用配对，以及解析范围内的文件生命周期。它不实现采集器、ETW、调试器或隔离器，不读取其它现场材料，不判断来源归因。

即使 `integrity_passed=true`，输出也始终包含 `source_attribution=null`、`execution_ready=false`。连续seq、零丢失声明、完整配对都只是输入内部自洽，不能证明真实采集没有漏报，也不能构成现场GO或EX-005闭环。后续新增的[v2 Shell32快照绑定](#schema-v2-shell32-binding)按[冻结共同字段契约](legacy-source-capture-binding.md#shell32-capture-binding)显式分流，下面v1章节保留其独立边界。

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

另外两个已验收的离线接口分别提供[两键命令数据](legacy-config-query-consumer.md#offline-query-consumer)和[目录API原缓冲解释](legacy-source-api-buffers.md#result-contract)。前者不执行查询；后者的bytes、BOOL和解码结果不在v1事件字段集合中，不能直接追加到data或塞进name／phase绕过校验。下方v2已增加显式快照绑定，v1仍拒绝这些新字段；子代理交付时仅用手造快照验证消费端；随后协调已用[提取核心](legacy-source-call-capture.md#interfaces)的实际输出完成下方6项离线互通验收，尚未接成真实运行器或完成联合采集验证。

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
| CLI 0 | 所提供记录在选定的v1／v2检查范围内通过，仍无归因／GO |
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

<a id="schema-v2-shell32-binding"></a>

## v2结论：Shell32原快照、调用配对与原输入摘要

本节接续[EX-005](exploration-backlog.md#ex-005)，实现[冻结Shell32绑定契约](legacy-source-capture-binding.md#shell32-capture-binding)的消费端。本轮不修改该共用协议，不复制解码器，不实现真实采集。原v1测试文件保持不变，其35项接受／拒绝回归继续通过；v1仍拒绝api_snapshot，且仍接受原有不带快照的通用api记录。

输入首个可检查事件选择精确整数schema_version 1或2，后续每条必须相同；单输入混用版本拒绝，不尝试拆分、丢弃快照、重排事件或按v1重新摘要。v2沿用原公共字段、身份／顺序／时点／覆盖声明、线程调用栈及parse文件生命周期，仅增加api_snapshot，并限制operation=api的name精确为SHGetSpecialFolderPathA。parse不要求也不接受API快照。

api_snapshot的data必须恰含call_id和capture。该call_id必须已进入、未返回，位于同一TID栈顶且operation为api，每次调用恰好出现一次；孤立／跨线程／非栈顶／重复／返回后快照均拒绝。call_return须在快照后出现，原result必须逐值等于capture.raw_bool；不能把-1等非零BOOL先规范为1再比较。未返回调用、API返回前缺快照、原配对错误均不通过。

capture完整字段集合为：api、module_base、caller_rva、entry_rsp、return_address、hwnd、buffer_address、csidl、f_create、raw_bool、raw_hex、read_limit、read_complete、encoding；缺项或扩展字段都拒绝。具体类型和来源以冻结契约为准，消费端核验如下：

| 约束 | 实现范围 |
| --- | --- |
| 站点／CSIDL | caller_rva仅0xa56bbe／0xa56bec，分别对应0x1c／0x1a；api精确匹配，hwnd／f_create均为整数0 |
| 地址 | module_base、entry_rsp、return_address、buffer_address均为非零无符号64位精确整数；module_base加RVA、entry_rsp加8、buffer_address加read_limit不得溢出；不凭返回地址猜调用指令长度，也不证明内存实际可读 |
| BOOL／字节 | raw_bool保留有符号32位原值；raw_hex为最长520字符、偶数长度的小写十六进制，无空格／前缀，字节数不超read_limit；read_limit为1..260精确整数，数值字段拒绝布尔／浮点／数值字符串 |
| 有界读取 | read_complete为严格bool。false即拒绝，即使已有NUL或BOOL为0；true仅表示提供者的读取声明，不证明真实采集完整，也不要求填满read_limit |
| 解码 | 实际调用legacy_source_api_buffers.decode_shell_folder，传原BOOL、bytes、读取上限／声明及原编码名；支持编码由原组件验证，不猜本机ACP，不复制编码白名单 |
| 未知／失败 | 非零BOOL且解码status=unknown时拒绝；BOOL=0且read_complete=true时，允许保留无NUL、不可解码或空残留缓冲的api_failed结果，path_text仍为null，不消费为路径；两个站点的先后因果、是否应触发第二次调用仍不由本组件推断。 |

v2报告的schema_version为2，并增加api_snapshots对象，以call_id为键；每项含line（从1起的输入物理行号）、原seq、tid、完整capture、decoded和accepted。已解码但因读取不完整／成功缓冲unknown而拒绝的快照也保留decoded和位置，accepted=false；字段或类型在解码前就无效时不伪造解码结果。accepted仅表示该条快照的局部字段与解码门通过，后续返回值错配等仍使整个integrity_passed=false。

解码器返回的raw_bytes及非null tail_bytes用明确的无损对象输出，例如：

```json
{"encoding": "hex", "hex": "ff0061"}
```

原capture.raw_hex仍按输入保留；不修剪NUL之后字节，也不替换解码失败字符。JSON输出可直接序列化，CLI在Python -I隔离模式下只显式加入工具自身固定目录以加载已存在的同级解码组件。内存输入仍按完整事件列表确定性序列化；文件输入的SHA对应读到的完整原JSONL（含快照、空白、CRLF和尾部字节），不对应过滤后的派生事件。原4MiB／64KiB／10000事件边界及超限read_prefix标记保持。

新Task task_370a66937002／Dispatch ctx_6736dc7cbbba沿Pi会话01a1d4e9-ce67-756e-8b4e-17d0dd926e95、deng/gpt-6.1-sol/high续作；环境和最新model／thinking事件、干净Git及工具exit0已核，status回执msg_532f0cf3f873。fetch后确认origin/dev含22d479e及字段契约登记，基f355d7ba180db69128e91d4e7234e56fe2e842b3新建feat/ex005-observation-v2。仅改本工具、本文并新增[手造v2测试](../tests/test_legacy_source_observation_v2.py)，不修改原v1测试、共用契约或前置设计。

本轮验证命令：

```powershell
python -B -m unittest discover -s tests -p 'test_legacy_source_observation*.py' -v
python tools/check_exploration_docs.py
git diff --check
```

首轮54项中51通过、3个CLI用例失败：新增同级导入在Python -I模式下发生ModuleNotFoundError，未触及v1字段或配对规则；修正为CLI显式使用工具自身固定目录后，第二轮54项全过（原v1 35项、新v2 19项）。原exit1保留于本树.local-analysis/ex005-observation-v2/tests-first.json，成功回执为tests-second.json；所有文件夹具在本任务忽略目录内创建并清理，原材料只读。新测试覆盖两个合法站点、signed BOOL及原返回一致、失败残留、unknown／截断、地址／数量边界、精确字段、跨线程／重复／孤立／非栈顶／缺快照、混版本拒绝、实际解码器调用、JSON字节表示、完整原输入摘要及排他输出。

文档检查实际exit0：164份Markdown／1335链接／41开放事项／137来源细节／148索引报告零错。首次git diff --check因本文EOF多一空行exit1，原diff-check.json保留，修正后另存最终差异回执；v1测试文件差异检查exit0且无改动。

**仍未覆盖：** 真实采集后端及ABI现场验证、实际用户根隔离、模块／编码来源真实性、Property、windir、GET输出及CONFIG环境、完整Host IO与原创建者退出见证。本子代理交付时仅手造有限fixture，生产者由另一独立worker交付；随后协调已完成下述离线互通验收。本轮无真实API／进程内存／目标或桌面调用，没有现场配置、plan或GO；通过仍恒source_attribution=null、execution_ready=false，EX-003／005不结。

<a id="capture-v2-integration"></a>

## 协调验收：提取输出到v2审计的离线互通

本节继续[EX-005](exploration-backlog.md#ex-005)。协调审阅原工具增量、完整372行v2测试、本文和首轮CLI导入失败／EOF差异失败及最终回执，确认原v1测试未改。首轮CLI失败由固定同级导入修正后通过，原失败保持；父树没有再修改子代理实现。

协调新增[6项跨模块测试](../tests/test_legacy_source_capture_integration.py)，实际调用begin_shell_folder_call／finish_shell_folder_call，将返回的完整14字段对象直接放入api_snapshot，再调用审计器及既有解码组件。测试没有手造capture替代生产者，也不重新实现提取或解码逻辑；仅外层运行／调用身份、时间和覆盖声明为合成数据。覆盖：

- 两站点、两线程交错的提取输出能被消费，精确FILETIME、signed BOOL及NUL后尾部原字节保持。
- 提取端保留不完整读取，消费端按incomplete_snapshot拒绝；成功但无NUL／解码失败按unknown_snapshot拒绝，BOOL失败残留保持api_failed且path_text为空。
- 成功空串、259字节加NUL的260字节边界和INT_MIN通过相应局部检查；原返回事件与capture BOOL不符仍拒绝。
- 原JSONL含完整capture及CRLF，审计SHA对应全部原字节，输入文件未修改。

父树命令 `python -B -m unittest discover -s tests -p 'test_legacy_source_*.py' -v` 实际100项全过：解码20、提取20、v1回归35、v2共19及跨模块6。父证 `.local-analysis/ex005-capture-binding-0174/observation-v2-parent-review.json`；这是当前集成树一次合成回归的数量，不与历史重复测试累加作新增能力。

因此，Shell32有界快照的**纯提取→v2绑定→既有解码**离线数据链已通过；真实内存读取、模块／编码来源、ABI现场、丢失检测真实性、用户根隔离、Property、windir、完整Host IO、GET输出及退出链仍缺。这6项测试的覆盖声明是夹具输入，不能当从首次目标指令到退出的采集证据。用户要求控制电脑前先说明，本轮未操作电脑。
