# PT Renew

使用 **C++ + Qt 6** 重建 DOS 版 Protel AUTOTRAX 的 Windows 桌面工程。

当前为第四阶段：支持 PCB **只读预览、图元选择与属性查看、元件检索定位、两点自由取点测量**，以及 13 层显隐、菜单/快捷键和二维视图。**尚未实现编辑、保存、封装库载入、DRC、布线或生产输出。** 文字与部分焊盘轮廓为近似显示，测量未吸附端点，不能将预览和近似读数用于制造。

## 开发环境

已验证 Qt **6.12.0 MSVC x64**、Visual Studio 2026、CMake 和 Ninja；不需要 Qt Creator。

```powershell
& .\scripts\Enter-QtEnv.ps1
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
& .\build\debug\pt-renew.exe
```

其他 SDK 安装路径：

```powershell
& .\scripts\Enter-QtEnv.ps1 -QtPrefix 'D:\Qt\6.12.0\msvc2022_64'
```

可通过命令行只读打开一个旧 PCB 文件：

```powershell
& .\build\debug\pt-renew.exe 'D:\板图\样例.PCB'
```

载入在后台解析，显示走线、焊盘、过孔、圆弧、矩形填充、文字与元件标签，同时展示 SHA-256、图元数量和限制说明。当前仅支持已覆盖的 `PCB FILE 4` 记录；未知记录或畸形字段整体拒绝，不静默丢弃。上限为 64 MiB、200000 条结构记录，非 ASCII 代码页尚未确认。格式覆盖与显示限制见 [PCB 只读预览](docs/pcb-readonly.md)。

## 菜单与键盘

- 顶部菜单保留原程序 17 个一级入口及字母，窗口较窄时通过菜单溢出入口访问。
- **鼠标**：点击顶部菜单。
- **现代键盘**：Alt+F 等访问菜单，Ctrl+O 打开只读板图，Ctrl+W 关闭板图，Ctrl+G 切换网格。
- **旧式入口**：点击画布使其获得焦点，按 F 打开文件菜单，再按 L 打开同一个文件对话框；P、N 等字母可打开对应菜单。
- 单字母兼容只在画布焦点内生效，不抢占文本框中的文字。
- F5/F6 缩小/放大，F9 重绘，F10 居中；滚轮缩放，中键拖动视图。
- 左侧复选框控制 13 层显隐；面板关闭后，可从“设置 → 图层显隐面板”恢复。
- 单击图元查看只读属性，同位置再次单击或画布内 **Ctrl+Tab** 切换重叠候选；画布内 **Esc** 或单击空白清除选择。
- **Ctrl+I** 或“信息 → 图元属性面板”恢复属性面板；显示尺寸、源文件行和所属元件，不修改原板图。
- **Ctrl+F** 或“跳转 → 检索并定位元件”（画布 J→C）：按标号、封装或注释筛选，Enter 定位，不移动元件；画布 **Ctrl+Home** 跳转板坐标原点。
- 画布 **Ctrl+M** 或“信息 → 两点只读测量”：依次单击两点读取距离、ΔX/ΔY 和方向角；画布 **Esc** 退出模式并保留已完成结果。“清除测量”移除结果。
- 测量为屏幕自由取点，未吸附网格或端点；只是近似读数，不是 DRC 或生产尺寸校验。
- 未实现的业务明确标注并禁用，不提供伪保存或伪布线。

## 发布目录

在已启用 Qt 开发环境的终端运行：

```powershell
cmake --preset release
cmake --build --preset release
ctest --preset release
cmake --install build/release --prefix dist
windeployqt --release --compiler-runtime --no-translations dist/pt-renew.exe
```

`dist/` 是本地部署目录，不应提交。正式发布仍须在干净 Windows 10/11 上验证运行库、安装包及许可义务；本机运行成功不替代目标系统验收。

## 文档与协作

- [协作规范](AGENTS.md)：简体中文、约定式提交、独立分支 → dev → 用户合并 main。
- [Qt 开发环境](docs/qt-development.md)：安装组件、验证结果和平台限制。
- [首次调查](docs/initial-assessment.md)：软件身份、DOSBox 与文件现状。
- [逆向结构与架构](docs/reverse-architecture.md)：证据、分层、快捷键设计和后续步骤。
- [PCB 只读预览](docs/pcb-readonly.md)：第二阶段字段布局、扩展属性、渲染与失败策略。
- [选择与属性查看](docs/selection-inspector.md)：第三阶段命中规则、重叠切换、属性来源和操作验证。
- [元件检索与测量](docs/navigation-measure.md)：第四阶段筛选定位、自由取点、快捷键与近似读数限制。

`pt/`、`pt_install/` 和 `.local-analysis/` 永远不应提交。原软件及用户文件不属于本项目自行授权分发的内容。测试使用合成小样例，不提交原软件数据或反编译数据库。
