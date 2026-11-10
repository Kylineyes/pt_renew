# 显式参数下的新增 FT 输出

<a id="explore-ex-007"></a>

`LegacyPcbWriter` 增加可消费现有插入预检与编码器的输出入口。调用方必须明确提供编码参数；本功能通过本项目严格解析与语义检查，**不是原 AUTOTRAX 接受这些新增记录的兼容证明**。原软件默认六／七字段、附加整数和换行尚未核定，现有默认写出入口仍拒绝新建走线。

[探索 EX-007](exploration-backlog.md#ex-007)。

## 接口与调用责任

```cpp
using Codec = pt::LegacyFreeTrackCodec;
Codec::Options options;
options.fields = Codec::FieldLayout::SixFields;
options.lineEnding = Codec::LineEnding::Lf;
// 上述取值仅是调用示例，不能视为原软件默认值。
auto prepared = pt::LegacyPcbWriter::prepareWithCreated(original, current, options);
auto saved = pt::LegacyPcbWriter::saveAsWithCreated(newPath, original, current, options);
```

两个入口均返回 `BoardWriteResult`：内存准备成功返回字节及其 SHA-256；文件发布成功另返回目标绝对路径。失败必须检查 `succeeded()`／`error`，不能把失败结果中可能保留的已准备字节当成保存成功。`prepare`／`saveAs` 继续只处理已有自由 FT 的整体移动和删除。

`Options` 没有自动策略。存在新建段时，必须显式指定 `SixFields` 或 `SevenFields`，以及 `Lf` 或 `CrLf`；七字段必须提供 `extra`，六字段禁止提供 `extra`。未指定或无效枚举均拒绝。参数对本次所有新增段统一生效，不重新编码已有段。没有新建段时沿用已有受限输出并忽略编码参数，因此空 `Options` 可用于纯旧段输出，包括已有 NETDEF 的板图。

会话内 `Created.extra` 必须为空，七字段编码的附加整数属于调用方明确要求的输出投影。输出复核按投影后的 `extra` 比较，不把它误判为编辑会话已经拥有该属性，也不写回工作文档。调用方负责决定是否调用该显式入口；writer 不选择默认值，不修改修订、dirty、撤销重做或保存点，不重新绑定原输入。UI 保存点与产品入口由集成层处理。

## 复用与校验顺序

1. 显式入口调用 `LegacyTrackInsertionPlanner::prepare`。planner 剥离新建段后只调用原 `LegacyPcbWriter::prepare`，执行已有保护并得到旧段编辑后的 `baseBytes`；原 `prepare` 不调用 planner，因此不存在递归。
2. planner 核对 Loaded／Created 身份、来源、旧段先于新建段、严格递增的新建序号及几何。允许序号缺号，禁止重排、重复、未分配身份及伪造来源。坐标须为 ±1000000 mil 内有限整数，宽度 1..1000000，新增层仅 1／6，长度非零。
3. 新建段存在时，仍拒绝尾部及交错 NETDEF。只使用严格解析得到的无 NETDEF、ENDPCB 前插入位置，禁止搜索文本 `ENDPCB` 来猜位置；元件名／焊盘名／文字中同名内容不会变成锚点。
4. 复用 `LegacyFreeTrackCodec` 编码各新增段，按已核定的创建顺序拼接。已有段移动仍只替换四坐标词，删除仍只移除对应原记录，其余分隔符、混合换行、未解释字段、非 ASCII 字节、ENDPCB 尾部及 DOS EOF 均沿用冻结原字节。
5. 在分配／追加整体输出前检查 64 MiB；既检查旧段位移造成的十进制位数增长，也检查所有新建编码累积大小。planner 使用编辑后实际语法计数，200000 条上限包含 COMP、ENDCOMP、内部记录及 ENDPCB，删除可释放容量。
6. 两条入口共用输出复核：整体重新严格解析，核对全部走线、其他对象、记录计数和 NETDEF 语义，并核对独立预期的重载身份与来源。输出通过才进入共享发布逻辑。

身份不是简单忽略后比较几何。默认路径依据实际替换区间删去的换行数，计算每条保留走线输出标签行，预期身份为 `Loaded(输出行)`；元件内 CT 同样随前面删除前移。新增路径保留已经复核的 base 走线身份，从插入位置前实际 LF 数计算第一个新增标签行，再根据每段编码的实际换行递增，将每个 `Created(序号)` 按位置明确对应到 `Loaded(输出标签行)`。重载来源的行和元件归属也参与比较；当前 reader 未提供的字节来源偏移仍是 `-1`，不伪造偏移。相同几何的两条新建段保持两条记录与两个行身份。

文件发布共用原有同目录 `QTemporaryFile`、完整写入、`flush`、关闭和不覆盖的原子改名。原路径（即使已删除）、已有目标、符号链接、设备名、备用数据流、错误扩展名和无法创建临时文件的目录均拒绝。失败由临时文件自动清理；writer 只使用冻结字节，不重新读取可能已被外部修改或删除的输入。

## 专项验证与边界

`tests/TrackCreatedWritingTests.cpp` 直接调用真实 writer，覆盖：

- 六／七字段、LF／CRLF、零及有符号边界附加值、缺失／冲突／非法参数；默认 writer 仍拒绝 Created。
- 新增与已有移动／删除混合、创建后移动、undo／redo 和持久快照、旧字节及 DOS EOF 保留。
- 多新建顺序、缺号和极大序号、相同几何不同身份、输出实际行身份、其他图元及原始身份／摘要／计数等伪造拒绝。
- 尾部／交错 NETDEF 拒绝、无新建时 NETDEF 原样保留与语义篡改拒绝、未知记录和损坏冻结输入拒绝。
- 真实 200000 条语法记录容量与删除释放、64 MiB 恰好边界、新增累计超限、位移放大超限及删除释放字节。
- 冻结输入与原件只读、全新文件严格重开、不覆盖已有目标、默认入口与无效参数不发布、改名失败无临时残留。

本次独立 harness 的 Debug／Release 配置、构建（并行最多 2）及 CTest 真实退出均为 0，各 3/3 专项通过。新增 writer 专项各 67 项，现有插入预检各 72 项、预检工作流各 8 项，均零失败、零跳过；QtTest 统计包含初始化和清理。Debug CTest 合计 156.15 秒，Release 21.26 秒；其中新增 writer 专项分别 124.22／18.54 秒，正式 CTest 建议至少 240 秒预算。首次构建曾发现测试中把 NETDEF 的 QByteArray 元数据赋为 QString，修正后两配置通过，初次失败日志另存。

本专项只涉及源代码与文件系统，不启动桌面，不读截图。独立工作树使用忽略的 `.local-analysis/track-explicit-output/harness/`，不修改跟踪 CMake；专项目标与全量 Debug／Release 验收由协调者纳入正式构建。测试结果和本次实际模型／thinking／assistant／工具审计保存在同一证据目录。原 AUTOTRAX 实际生成样例、默认编码和原软件重开验收仍待专门证据，不能由本次合成测试替代。
