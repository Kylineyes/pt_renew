# 冻结配置文字见证工具

[文档导航](README.md) · [配置来源与见证矩阵](legacy-dosbox-configuration.md#ex005-witness-matrix) · [两键具体绑定的证据边界](legacy-dosbox-configuration.md#ex005-witness-key-binding)

<a id="ex005-text-witness-tool"></a>

本工具接续[EX-005](exploration-backlog.md#ex-005)。`tools/inspect_legacy_config_witness.py` 是标准库离线工具：只读调用者明确指定的两个文件，对一至三个 `SECTION/KEY` 候选列出文字出现情况、原文字值及可区分性。它用于把既有显式 conf／U 等价副本文字矩阵变成可复核输出，不要求输入符合现场小配置白名单，也不调用或放宽 `legacy_runtime_config.parse_config`。

相同文字或相同文件 SHA-256 都不能证明加载来源；不同文字也不证明目标读取或采用了该值。工具始终将类型、合法值、实际有效值及实际加载来源留为未知，不自动选择合格见证键，不生成配置、候选或 GO。本工具交付不结算 EX-005，不改变其原完成条件。

## 合成输入示例

下面两段是供读者自行保存的合成文字，不是现场配置或运行建议。左文件 `synthetic-left.txt`：

```ini
[dosbox]
memsize=16
[sdl]
fulldouble=false
[autoexec]
set SYNTHETIC=value
```

右文件 `synthetic-right.txt`：

```ini
[dosbox]
memsize=16
[sdl]
fulldouble=false
waitonerror=true
```

```powershell
python -B tools/inspect_legacy_config_witness.py synthetic-left.txt synthetic-right.txt --candidate dosbox/memsize --candidate sdl/fulldouble --candidate sdl/waitonerror
```

左文件的 `memsize`、`fulldouble` 为 `present`，`waitonerror` 为 `absent`；右文件三者均为 `present`。前两键的 `single_value_text_equal` 为 `true`、`text_distinguishable` 为 `false`，说明这些文字不能区分来源；第三键因一侧没有出现，比较为 `null`，不能把未出现当成空值、编译默认或继承值。

默认 JSON 输出到 stdout。可追加 `--output 新报告.json`，父目录须已存在；输出使用 `open('x')` 排他新建，已有证据、输入文件及其已有硬链接／符号链接均拒绝覆写，错误退出码为 2。工具不创建父目录，不搜索安装目录、用户目录或环境变量，不执行 autoexec，也不启动外部命令。命令必须明确给出两个输入路径；两者允许是同一文件，结果依然不产生来源归因。

## 扫描规则与保守边界

这些是本工具可解释的文字扫描规则，不是 DOSBox parser 的替代实现，也不是通用 INI 库：

- 默认对两输入分别用 `utf-8-sig` 严格解码，允许文件开头 UTF-8 BOM。可分别通过 `--left-encoding`／`--right-encoding` 显式选择 `utf-8-sig`、`utf-8`、`utf-16`（须 BOM）、`cp437` 或 `cp1252`。不自动猜编码，不用替换字符修补；解码失败仍报告原字节大小与摘要，`scan_complete=false`、候选覆盖为 `unknown`。显式编码是调用者假设，不证明目标使用该编码。
- 仅 CRLF、CR、LF 划分物理行，行号从 1 开始；不把 Unicode 行分隔符当换行。两端仅剥离 ASCII 空格与制表符；节名、键名仅支持 ASCII 字母数字、下划线、点、横线和内部空格，首字符须为字母数字或下划线，匹配时折叠 ASCII 大小写。完整节头允许括号内两端空格，例如 `[ SDL ]`。未支持名称保守列为畸形，不推断目标是否接受。
- 空行和去除两端空格后以 `#`／`;` 开头的整行是注释。完整 `[section]` 是节头；普通节内在第一个 `=` 处分开属性名和值。值可为空，原始等号后文字完整保留，另提供去两端空格／制表符的 `value_text`。不移除行内注释、不去引号、不展开变量、不转换布尔／数字、不判断合法域。
- `[autoexec]` 内所有非完整合法节头行都作为命令文字跳过，含 `=` 或类似畸形节头的命令亦然；完整合法节头结束该命令区。这是扫描约定，不证明目标的全部 Section_line 规则。对 `autoexec/KEY` 的候选一律标记 `unknown`，不产生属性出现。工具不认识其他目标专用行节的语义。
- 普通节中畸形节头会清空当前节归属，后续属性不会偷偷继承前一节；无节属性、无等号普通行、非法键名均记录问题。NUL、其他 ASCII 控制字符（制表符除外）、DEL、U+FEFF、U+0085、U+2028、U+2029 使该行记为问题并清空节归属，不默默截断或丢弃。正常文件开头由 `utf-8-sig` 移除的 BOM 不属此类。
- 所有重复节头与候选键出现按原顺序保留，不做 last-wins。候选所属节重复，即使键只出现一次或从未出现，也存在歧义。输入任意扫描问题会使所有候选带 `input_has_scan_issues`，因此唯一值比较降为未知；这是避免过强缺席结论的保守选择，可能比目标 parser 更严格。

`explicit_override` 只表示扫描范围内的文字事实：有已识别出现为 `present`，没有出现且扫描无歧义为 `absent`，其余为 `unknown`。`present` 与 `ambiguous=true` 可同时存在；前者不能冒称唯一赋值或目标实际覆盖，后者不能被消费者忽略。`scan_complete=true` 仅表示完成解码和逐行扫描，仍须检查 `issues`。

## JSON 字段

| 字段 | 含义 |
| --- | --- |
| `schema_version` | 当前为 1。 |
| `inputs[0/1].path / bytes / sha256 / encoding` | 调用者给出的路径及该次只读原字节大小、SHA-256、显式解码选择；不是来源路径证明。 |
| `inputs[].scan_complete / issues` | 解码／扫描完成标志与问题列表；问题包含 `line`、稳定 `code` 及 `raw_line`，解码问题为 `line=null` 和 `detail`。 |
| `inputs[].candidates[].section / key / section_lines` | 规范化候选及其所有已识别节头行号。 |
| `occurrences[]` | 每次出现的 `line`、`section_line`、`raw_line`、`raw_key`、`raw_value`、`value_text`；换行符不包括在 `raw_line` 内。 |
| `explicit_override / ambiguous / ambiguity_reasons` | 文字出现状态及歧义。原因包括输入扫描问题、重复节、重复键及 autoexec 命令区。 |
| `unknown` | 报告全局及每个输入候选的 `type / legal_values / effective_value / loaded_source` 全为 `null`。 |
| `input_bytes_equal` | 两次读取的 SHA-256 是否相同；不表示曾加载、加载顺序或创建时间。 |
| `comparisons[].raw_value_sequences_equal` | 双侧均有已识别出现时，对原值的完整有序序列作相等比较；含重复，且可在歧义时给出，仅是原文序列事实。任一侧没有出现时为 `null`。 |
| `single_value_text_equal / text_distinguishable` | 双侧均有唯一、无歧义候选时，比较去两端空格后的文字；分别为相等与不等，否则均为 `null`。不等也不表示合法值或实际生效差异。 |
| `comparisons[].source_attribution` | 恒为 `null`，工具不判断来源。 |
| `scope / limitations` | 随 JSON 附带的文字证据适用边界。 |

扫描问题会生成可审查 JSON，CLI 仍退出 0；消费者必须检查上述状态和问题字段。路径不可读、候选非法／重复／超过三个、输出已存在等调用错误退出 2，不据此生成成功报告。默认 stdout，可将含原值的 JSON 保存到项目忽略的任务证据目录；输入可能包含敏感原文，调用者自行控制证据分发。

## 验证与本次交付

```powershell
python -B -m unittest discover -s tests -p test_legacy_config_witness.py -v
python tools/check_exploration_docs.py
git diff --check
```

测试仅在当前树忽略目录 `.local-analysis/ex005-config-witness/fixture-*` 建立并清理临时合成输入，复用仓库 `unittest` 与 `tools` 导入惯例；不读取真实用户配置、不写测试镜像、不运行目标或 GUI。测试覆盖显式／未覆盖、同值无法归因、完整原值与行号、重复节／键、命令区、畸形归属、编码、控制字符及 CLI 只读／输出排他创建。

子代理本次限定三个文件交付；共享主题、完整资料索引和交接由协调者统一维护。子代理交付时本报告未入完整资料索引，因此文档检查仅此一项失败；原失败保留，随后由协调补齐入链再检查，不能把子代理原回执改成通过。实际测试和检查回执见本树 `.local-analysis/ex005-config-witness/validation.json`；首轮检索中的缺目录／PowerShell 正则转义失败只影响工具惯例查询，没有运行历史脚本或访问现场配置。

协调已完整审源并在父树独立复测19项，全部通过；另用第八既有两份冻结配置核三个候选的原行号／文字值与历史矩阵一致，CLI输出与库接口一致，输入大小／SHA前后未变，见协调树`.local-analysis/ex005-parallel-6951/witness-parent-review.json`。完整参考副本有53行超出本工具的保守扫描规则，因此相应候选带歧义、唯一值比较为null；这是扫描器支持范围，不证明原配置非法，也不作为配置来源验证通过。

后续仍需由协调者核对具体候选的目标类型、合法域、查询语法与副作用、真实用户根隔离和实际阶段 I/O。冻结文字工具只提供离线文字矩阵，不能补这些 EX-005 现场前置，也不能追认旧运行的加载来源。
