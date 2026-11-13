# 无 PT 的 CONFIG 两键离线查询消费契约

[文档导航](README.md) · [EX-005](exploration-backlog.md#ex-005) · [查询语法与影响](legacy-config-query-contract.md#minimal-contract) · [隔离与观测前置设计](legacy-source-observation-plan.md#capability-gates)

<a id="offline-query-consumer"></a>

本节继续[EX-005](exploration-backlog.md#ex-005)。`tools/legacy_config_query_consumer.py` 为未来已审运行器提供受限命令数据和精确校验入口。它只接受调用者明确指定的一至两个键，或显式 JSON 文件中的一至两条外部命令；保留顺序，拒绝重复和未知输入，输出 JSON 契约。工具不启动进程、不提供执行开关、不生成磁盘 conf 或现场计划，`execution_ready` 恒为 `false`。

本交付实现离线消费者，供协调审查后复用；它不证明实际 shell 能执行候选语法、查询输出已送达或实际来源已经归因，不结算 EX-005／EX-003，也不替代隔离和观测前置。旧 `legacy_runtime_config.py` 的 PT 启动白名单、七查询及既有测试均不调整；本工具也不接入该准备器或运行器。

## 可接受的最小数据

调用者用精确的小写裸键名 `fulldouble`、`waitonerror` 明确选择；不接受带节名的别名、大小写变体、两端空白或自动默认。输出将键规范化为 `{ "section": "sdl", "key": "fulldouble" }` 等对象。

唯一接受的完整命令字符串为：

```text
CONFIG -get sdl fulldouble
CONFIG -get sdl waitonerror
```

每项是一条独立 DOS shell 命令数据，不是宿主 EXE argv，也不合并为脚本。上述语法来自[已核最小静态契约](legacy-config-query-contract.md#minimal-contract)：内建 CONFIG 收到相应命令尾、对象有效和各辅助普通返回等前提仍须满足；外层 shell 预处理和实际运行回执保留未知。

消费入口对整串作精确匹配，没有前缀接受、`strip`、大小写折叠、参数重排或 shell 解析。因此引号、分号、重定向、管道、换行、NUL、额外空白或参数都不能进入输出；`mount`、PT、`exit`、任意 shell 语句及旧七查询形式也不在此接口内。合法前项不使非法后项获得接受，整个列表在生成输出前完成校验。

## CLI 示例与输入输出

按参数生成，两条命令保持指定顺序：

```powershell
python -B tools/legacy_config_query_consumer.py --key waitonerror --key fulldouble
```

也可只给一个 `--key`。没有键或重复键是错误，不自动补另一键。

验证外部数据时，调用者可将下面合成 JSON 数组保存为 `synthetic-commands.json`：

```json
[
  "CONFIG -get sdl waitonerror",
  "CONFIG -get sdl fulldouble"
]
```

```powershell
python -B tools/legacy_config_query_consumer.py --commands-json synthetic-commands.json
```

`--key` 与 `--commands-json` 必须二选一。文件只支持 UTF-8 严格解码（允许开头 BOM）后的顶层命令字符串数组；对象、契约报告、空数组、数字或嵌套值均拒绝，不从对象里寻找命令或信任 `execution_ready`。没有目录扫描、环境变量读取、stdin 默认输入、用户配置访问或外部工具调用。

默认 JSON 输出到 stdout；可追加 `--output 新报告.json`，父目录须存在。输出使用排他新建 `open('x')`，已有输入、已有报告和已有链接均拒绝覆写，不自动建目录。读取和校验先完成，再新建输出；输入不可读、JSON／编码非法、命令不符及已存在的输出均退出 2。成功输出退出 0，只表示离线数据校验成功。参数不支持缩写，没有 `--execute`、`--exit` 或其它执行模式。

## 纯函数入口与输出字段

| 入口 | 输入与结果 |
| --- | --- |
| `generate_commands(keys)` | 显式 `list`／`tuple` 裸键名，长度一至二、无重复；返回按原顺序排列的新命令列表。字符串本身或其它容器不接受。 |
| `consume_commands(commands)` | 外部完整命令 `list`／`tuple`，长度一至二、无重复；整串校验后返回新 JSON 可序列化字典，是实际消费入口。 |
| `contract_from_keys(keys)` | 生成后调用同一 `consume_commands`，避免命令生成和外部校验分成两套接受规则。 |

上述函数不读写文件、不读取环境、不执行命令；CLI 层只负责显式文件读入和 JSON 输出。返回数据不共享调用者的命令列表，后续调用也不受先前返回数据被修改的影响。

| JSON 字段 | 含义与证据边界 |
| --- | --- |
| `schema_version / scope` | 当前版本 1，明确这是静态候选语法的离线数据，不是查询执行回执。 |
| `keys / commands` | 规范化节／键对象及逐条精确 ASCII 命令，顺序与输入一致。 |
| `execution_ready` | 恒为 `false`；输入无法将其提升为执行许可。 |
| `known_effects.property` | 仅描述已有正常局部 getter 不写回该 Property 的结论，不承诺所有路径或整条命令零副作用。 |
| `known_effects.shell_environment` | `variable=CONFIG`、`operation=Program::SetEnv`；静态正常路径会尝试更新、调用方不查返回、失败可能先移除旧项、连续查询共享该变量。布尔字段描述既有机制，不是本次实际调用事件。 |
| `known_effects.output` | DOS 句柄 1，已有调用方不查实际写入结果；`delivery_verified=false` 表示没有输出送达回执。 |
| `missing_evidence` | 仍缺 `isolation`、`observation`、`actual_query`、`creator_exit` 四类证据及中文说明，不是自动 GO 判决框架。 |
| `boundary` | 将终止、输出捕获和执行时序留给未来已审运行器。 |

[SetEnv 与输出影响](legacy-config-query-contract.md#local-results)是消费者必须保留的约束：打印与环境更新分开；容量失败可能已删旧 CONFIG，普通返回不证明成功。连续查询复用同一个 shell 的 CONFIG，不能拿它作两键各自的持久快照。输出数据未设置预期值，不按 `false`／`true` 或同构造初值来归因用户源。

本工具默认没有 `exit`、挂载、重定向或自动启动，也不添加这些尾部命令。未来运行器须另行审查终止方式、每条输出捕获及实际写入数量、Property 与环境前后状态、原创建者 HANDLE 等待和采集收尾；命令列表本身不能提供这些回执。真实身份和用户根隔离、目录 API／逐阶段 Host I/O 观测仍按[前置设计](legacy-source-observation-plan.md#observation-contract)落实，不能从离线校验通过推导其已可用。

## 合成验证与交付范围

```powershell
python -B -m unittest discover -s tests -p test_legacy_config_query_consumer.py -v
python -B tools/check_exploration_docs.py
git diff --check
git diff --cached --check
```

测试使用仓库 `unittest`／`tools` 导入惯例，只在本树忽略的 `.local-analysis/ex005-query-consumer/fixture-*` 内建立可清理合成 JSON 输入。实际调用 `consume_commands` 和 CLI 的 `main` 验证拒绝边界，不仿造校验器，也不启动子进程；覆盖全部合法顺序、缺省／重复／未知键、列表类型、shell 注入与近似字符串、只读输入、返回数据独立性、JSON 编码及输出排他创建，包括已有输入硬链接不被覆写。

本轮身份为 `deng/gpt-6.1-sol/high`，实际 Pi 会话 `01a1d4e9-572b-702c-9e89-def55fdfb0ec`；环境与会话模型事件均已核。分支 `feat/ex005-query-consumer` 从 `origin/dev` 的 `ff7f23e267172f46e326e360c03b0b0f0a9fae4c` 建立，包含上一轮验收及本轮领取登记。当前协调确认此基线有效，沿用本次新 Task／Dispatch，未重新派发子代理。

实际命令、退出码、失败记录及交付 HEAD 见本树 `.local-analysis/ex005-query-consumer/validation.json`。首次 Orca 帮助命令的 Windows 路径因 JavaScript 反斜杠转义损坏而退出 1，改为同一二进制的正斜杠路径后成功；没有切换模型或执行器。新增报告尚未加入共享资料索引造成的文档检查失败由协调统一入链，不能把其它错误当预期；未修改共享文档或旧工具。

协调已完整审阅104行工具、219行测试、本文及原validation.json，在独立集成分支运行14项父树测试全部通过；核对整串接受规则、SetEnv说明、执行状态恒false和输出排他创建，无须修改子代理实现。父验收记录见协调树`.local-analysis/ex005-offline-0174/query-consumer-parent-review.json`；原文档检查因未入索引的exit1保持，随后由协调统一入链。此验收仅接受离线工具，不提供实际运行能力回执。

本子题只交工具、测试和本文，证据留本树忽略目录；子代理未合 dev、未推送，不生成现场配置或计划。尚缺的实际查询、隔离、观测和原创建者退出见证不由这些合成测试补齐，后续执行范围与授权由协调按具体场景审查。
