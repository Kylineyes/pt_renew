# 架构、构建与验证

[文档导航](../README.md) · [接手步骤](../../HANDOFF.md) · [完整资料索引](../reference-index.md)

## 先看结论

产品采用 C++ / Qt 6，几何、文档、命令、文件和界面分层。当前已有构建与专题验证可复用；历史桌面控制及异步实验用于取证和验证，不能将它们的通过数量当作产品整体通过。

## 第一层分析：按职责定位代码

| 层次 | 目录 | 负责的问题 |
| --- | --- | --- |
| 文档与身份 | src/domain | 图元、来源、网表、测量和走线身份 |
| 文件适配 | src/io | PCB / LIB / NET 读取，布局、显式编码、插入和写出 |
| 业务与命令 | src/application | 命令目录、编辑历史、放置状态与引脚映射 |
| 几何 | src/geometry | 轮廓、命中、端点查询、铜接触 |
| 界面 | src/ui | 主窗、画布、浏览器、渲染和交互 |
| 本地工具 | tools | 只读 CLI、研究与控制诊断；按用途区分 |
| 验证 | tests | 合成数据、Qt 事件、CLI 进程与工具测试 |

依赖从界面指向业务和模型，文件层不弹对话框；图元由模型及渲染器处理，不为每段线创建控件。[首阶段架构](../reverse-architecture.md)记录设计来源，其早期目录树不是当前完整源码清单。

## 第二层分析：怎样复现开发

在项目根目录的同一 PowerShell 中运行：

~~~powershell
& ./scripts/Enter-QtEnv.ps1
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
~~~

Release 使用同名 release 预设。Qt 6.12.0 MSVC x64、Visual Studio 2026、CMake / Ninja 已有；先检查[环境说明](../qt-development.md)和现有 build，不为文档调整安装依赖或重复构建。跨工作树构建写入独立。

桌面程序无需 Python；Python 用于研究和诊断。发布包使用方法见[发布说明](../releases/v0.11.0-alpha.md)，打包步骤见[构建与打包](../releases/v0.11.0-alpha-build.md)。dev 编辑功能不自动进入已有 alpha 压缩包。

## 第三层分析：怎样解释“通过”

| 证据 | 可以支持 | 不能自动支持 |
| --- | --- | --- |
| 解析／几何单元测试 | 明确输入和拒绝规则 | 原软件兼容 |
| Qt offscreen 事件测试 | 状态与命令逻辑 | Windows 桌面焦点、原生对话框 |
| 真实 Qt 窗口交互 | 指定候选的实际流程 | 所有历史格式、全部并发现场 |
| 原软件现场与文件往返 | 当次目标行为与字节 | 未覆盖层、字段、NETDEF 或全部生产规则 |
| <a id="explore-ex-035"></a> 控制驱动假环境／离线测试 | 门禁、时限和材料逻辑 | GUI 成功或目标实际退出  [探索 EX-035](../exploration-backlog.md#ex-035) |

产品已测固定候选 d2ee381 有 Debug/Release 各 24/24；定向核心审查另有 82 passed（含初始化／清理）。真实 Qt 核心有独立现场报告。最新菜单审计只验证离线三项，没有新 GUI 通过；本次文档整理也不重算为新构建或产品验收。

## 下一步怎样推进

变更先定位所属模块，运行对应检查；GUI 行为变化要实际启动交互。结果报告指明固定候选、输入、测试范围、失败与未覆盖项。跨模块接口变化再检查相邻消费者，避免堆叠重复实验框架。

## 按需深入

- [Qt 开发环境](../qt-development.md)：组件、路径、构建及平台限制。
- [综合候选验证](../native-sample-wave.md)、[核心边界审查](../track-core-boundary-review.md)：固定候选和检查范围。
- [主窗真实 Qt 验收](../parallel-save-hardening-live.md)：交互、文件输出及原创建者退出证据。
- [构建与打包](../releases/v0.11.0-alpha-build.md)、[发布冒烟验证](../releases/v0.11.0-alpha-verification.md)：发行物来源与局限。

临时材料放当前工作树已忽略目录；优先复用脚本、会话、SDK 和构建。冻结现场不覆盖。分支、提交、原件保护和清理遵循[AGENTS](../../AGENTS.md)。具体现场身份和本机证据见[技术交接](../agent-handoff-20261104-capture.md)，控制工具历史按[资料索引](../reference-index.md)查阅。
