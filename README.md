# PT Renew

**v0.12.0-alpha 轻量编辑发布候选已准备**，见[候选范围与验证](docs/releases/v0.12.0-alpha.md)：独立Release构建和24/24组自动测试通过，正式新增仍禁用；真实新包窗口验收、main合并与新标签尚待完成。下方v0.11.0-alpha下载仍指向原只读发行包。

使用 **C++ + Qt 6** 重建 DOS 版 Protel AUTOTRAX 的 Windows 桌面工程。当前支持旧 PCB / LIB / NET 资料查看、选择定位、测量及受限铜层分析；dev 另有自由走线编辑和保留原件的另存为。

[下载 Windows 测试版](https://github.com/Kylineyes/pt_renew/releases/tag/v0.11.0-alpha) · [使用指南](docs/usage.md) · [按软件主题阅读文档](docs/README.md) · [当前进度](PROGRESS.md)

## 选择使用范围

| 版本或路径 | 可以使用的能力 | 当前限制 |
| --- | --- | --- |
| 已发布 v0.11.0-alpha | PCB / LIB / NET 只读查看，选择、定位、测量及端点捕捉，受限铜分析 | 不含编辑、保存或新增；见[发布说明](docs/releases/v0.11.0-alpha.md) |
| dev | 已载入自由 FT 的整数整线移动、删除、撤销重做、保存点及另存全新 PCB | 不覆盖原件或已有目标，Ctrl+S 未开放 |
| 内部显式新增 | 参数明确时的预览、提交、编码和新文件另存闭环 | 正式菜单／F3／P→T 仍禁用，默认字段待原软件核定 |

文字与部分轮廓为近似显示，旧格式覆盖受限。网络引脚映射与铜几何接触各有独立边界；当前不提供完整 DRC、断短路确认、交互布线、元件放置或生产输出。

## 开始使用

下载压缩包后完整解压，运行 pt-renew.exe；保留配套 DLL、插件和许可目录。Ctrl+O 打开板图，Ctrl+L 浏览封装库，Ctrl+Shift+N 载入外部网表。详细操作见[使用指南](docs/usage.md)。

从源码构建，在项目根目录的 PowerShell 中运行：

~~~powershell
& ./scripts/Enter-QtEnv.ps1
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
& ./build/debug/pt-renew.exe
~~~

已有环境为 Qt 6.12.0 MSVC x64、Visual Studio 2026、CMake 和 Ninja。安装路径及平台验证范围见[开发环境](docs/qt-development.md)，打包见[发布构建](docs/releases/v0.11.0-alpha-build.md)。

## 逐步了解软件

[文档导航](docs/README.md)按“能力概览 → 软件主题 → 实现与验证 → 原始报告”组织。可直接选择[板图](docs/topics/board.md)、[交互测量](docs/topics/interaction.md)、[编辑保存](docs/topics/editing.md)、[封装库](docs/topics/library.md)、[网络检查](docs/topics/connectivity.md)、[原软件研究](docs/topics/legacy.md)或[工程验证](docs/topics/engineering.md)。

开发接手读[HANDOFF](HANDOFF.md)；探索 agent 从[工程逻辑待办](docs/exploration-backlog.md)领取事项，并遵循[研究与沉淀规则](docs/exploration-workflow.md)。按问题追查全部报告使用[资料索引](docs/reference-index.md)。协作遵循[AGENTS](AGENTS.md)：独立分支开发、验证后合入 dev，main 由用户处理。

原软件、安装介质、用户板图、库及字体不随本项目授权分发；pt/、pt_install/、.local-analysis/、SDK、构建、截图和数据库不提交。测试优先使用自主合成数据，写入验证使用隔离副本。
