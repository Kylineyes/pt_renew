# 网络、铜层与检查

[文档导航](../README.md) · [使用指南](../usage.md) · [完整资料索引](../reference-index.md)

## 先看结论

网络声明可以映射到板上焊盘，支持高亮、定位和冲突报告；受限铜分析可以计算支持几何中的接触关系。完整 DRC、断短路确认、交互／自动布线和生产输出尚未实现。

## 第一层分析：三个问题分别判断

| 问题 | 输入与模型 | 结论边界 |
| --- | --- | --- |
| 这个节点属于哪个焊盘？ | NET / NETDEF 的元件-引脚声明与 PCB 实例 | 唯一、缺失、歧义、重复或跨网冲突 |
| 这些铜几何在模型中接触吗？ | 图层、带宽轮廓、孔洞及保守内外包络 | 支持模型内连接、分离或无法确定 |
| 板图符合设计／制造规则吗？ | 完整几何、电气语义与规则集 | 当前没有完整 DRC 或生产放行能力 |

外部 NET 与内嵌 NETDEF 明确切换来源，不自动合并。节点按完整组合键精确匹配；封装或注释差异只报告，不自动替换。自由焊盘不会凭空获得元件归属。

## 第二层分析：从声明到几何报告

| 实现入口 | 职责 |
| --- | --- |
| [LegacyNetlistReader.h](../../src/io/LegacyNetlistReader.h) | 严格读外部 NET 及保留元数据 |
| [NetlistMapping.h](../../src/application/NetlistMapping.h) | 元件引脚匹配、歧义和冲突 |
| [CopperConnectivity.h](../../src/geometry/CopperConnectivity.h) | 分层接触图与覆盖诊断 |
| [NetlistBrowser.h](../../src/ui/NetlistBrowser.h) | 来源、筛选、高亮、后台结果 |
| [InspectNetlist.cpp](../../tools/InspectNetlist.cpp)、[InspectCopper.cpp](../../tools/InspectCopper.cpp) | 两种不同含义的只读 CLI |

<a id="explore-ex-022"></a>

铜几何采用确定与可能包络，圆弧按实际象限处理；贯穿孔采用理想镀通假设。未解释 extra、铜文字、平面及不支持轮廓都可能使覆盖不完整。只要全板覆盖不足，网络状态保持“无法确定”，不能凭局部路径报告通过。

[探索 EX-022](../exploration-backlog.md#ex-022)。

编辑或换图使旧分析失效；后台结果依文档身份与代次核对后才可发布。完整 NET／铜竞争现场的旧缺口仍保留，不能由局部测试通过自动补齐。

## 第三层分析：已有证据说明什么

PLACED.PCB + DEMO.NET 的 36 个声明元件、88 网络、370 节点已有唯一映射证据。既有铜模型报告 430 对象、5211 次比较、21 组跨网接触候选；88 网络均无法确定。候选用于人工核对，不能读成 21 个短路。

<a id="explore-ex-021"></a>

真实 NETDEF 样例仍缺，当前结构主要依公开格式与合成测试。铜文字等覆盖缺口未消除；资源限制、模型近似及理想孔假设也必须随报告解释。CLI 退出码不能脱离具体 succeeded、board_loaded、覆盖和限制字段单独作为工程结论。

[探索 EX-021](../exploration-backlog.md#ex-021)。

## 下一步怎样推进

<a id="explore-ex-024"></a>

先补真实 NETDEF 与单几何原程序对照，明确文字、平面、附加字段和接触语义，再扩展模型。DRC、布线和生产输出分别需要规则、参考结果和输出往返验证，目前没有可直接开放的实现。

[探索 EX-024](../exploration-backlog.md#ex-024)。

## 按需深入

- [NET / NETDEF 语法和映射](../netlist-compatibility.md)。
- [铜层模型与退出码](../copper-analysis.md)、[圆弧包络](../copper-arcs.md)、[未覆盖对象定位](../copper-coverage.md)。
- [异步结果边界](../async-result-boundaries.md)：与[工程验证主题](engineering.md)一起阅读竞争实验的适用范围。
