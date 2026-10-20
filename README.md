# PT Renew

使用 **C++ + Qt 6** 重建 DOS 版 Protel AUTOTRAX 的 Windows 桌面工程。

当前为第一阶段：完成原程序结构调查、命令与菜单骨架、空白二维视图及只读文件信息探测。**尚未实现 PCB 图元显示、编辑、保存、DRC、布线或生产输出。**

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

可通过命令行只读探测一个旧 PCB 文件：

```powershell
& .\build\debug\pt-renew.exe 'D:\板图\样例.PCB'
```

此操作只展示 `PCB FILE 4` 文件信息、SHA-256 及标记行计数，不表示已解析或载入板图图元；探测上限为 64 MiB。

## 菜单与键盘

- 顶部菜单保留原程序 17 个一级入口及字母，窗口较窄时通过菜单溢出入口访问。
- **鼠标**：点击顶部菜单。
- **现代键盘**：Alt+F 等访问菜单，Ctrl+O 查看文件信息，Ctrl+W 关闭文件信息，Ctrl+G 切换网格。
- **旧式入口**：点击画布使其获得焦点，按 F 打开文件菜单，再按 L 打开同一个文件对话框；P、N 等字母可打开对应菜单。
- 单字母兼容只在画布焦点内生效，不抢占文本框中的文字。
- F5/F6 缩小/放大，F9 重绘，F10 居中；滚轮缩放，中键拖动视图。
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

`pt/`、`pt_install/` 和 `.local-analysis/` 永远不应提交。原软件及用户文件不属于本项目自行授权分发的内容。测试使用合成小样例，不提交原软件数据或反编译数据库。
