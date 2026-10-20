# Qt 6 开发环境

验证日期：2026-10-21。

## 已安装环境

| 组件 | 版本/配置 |
| --- | --- |
| Qt SDK | **6.12.0，MSVC 2022 x64 预编译开发包** |
| SDK 路径 | `C:\Users\rikideng\Qt\6.12.0\msvc2022_64` |
| 编译器 | Visual Studio Community 2026，MSVC 19.51.36252，x64 |
| MSVC 工具集 | 14.51.36231 |
| Windows SDK | 10.0.26100.0 |
| CMake | 4.3.1-msvc1，Visual Studio 自带 |
| Ninja | 1.13.2，Visual Studio 自带 |
| 本机验证平台 | Windows 11 x64 |

Qt 6.12.0 已从 Qt 官方正式发布目录及在线套件仓库确认。本次安装的是适用于当前项目的基础桌面开发组件，不是全部 Qt 附加模块。

包含：Qt Core、Gui、Widgets、Network、Test、PrintSupport 等 Qt Base 模块，Qt SVG、Qt Tools 和翻译资源，以及官方附带的图形运行库。`moc`、`uic`、`rcc`、`qmake`、`qtpaths`、`windeployqt` 可用。

**未安装 Qt Creator、MinGW、WebEngine、Android、WebAssembly、Qt Quick/QML 开发包。** 需要新增模块时再按实际功能安装。Qt Tools 中的 Designer 不等于 Qt Creator。

## 安装来源和完整性

- 正式发行目录：<https://download.qt.io/official_releases/qt/6.12/6.12.0/>
- 预编译包仓库：<https://download.qt.io/online/qtsdkrepository/windows_x86/desktop/qt6_6120/qt6_6120_msvc2022_64/>
- 套件标识：`qt.qt6.6120.win64_msvc2022_64`。
- 套件版本：`6.12.0-0-202609280346`。
- 已核对官方 `Updates.xml` 的 SHA-256，以及每个下载归档的官方 SHA-1；另行记录每个归档的 SHA-256，安装前再次检查。
- 本机安装清单：`C:\Users\rikideng\Qt\6.12.0\installation-manifest.json`。
- 不经过 Qt Creator 或在线账户登录；仅提取官方公开的预编译归档，并通过 `qt.conf` 设置可重定位安装前缀。
- `aqtinstall 3.3.0` 无法识别这一版本按架构划分的仓库结构，因此未通过关闭校验来绕过错误，而是改用官方仓库元数据和归档校验安装。
- SDK 与下载文件不在 Git 版本控制中；不修改系统级 PATH。

## 使用方法

在项目根目录的 PowerShell 中运行：

```powershell
& .\scripts\Enter-QtEnv.ps1
qmake -query QT_VERSION
cmake --version
ninja --version
```

脚本只设置当前进程的开发环境，包括 MSVC x64、Windows SDK、Qt 的 `PATH`、`QTDIR` 和 `CMAKE_PREFIX_PATH`，不切换工作目录。其他安装位置使用：

```powershell
& .\scripts\Enter-QtEnv.ps1 -QtPrefix 'D:\Qt\6.12.0\msvc2022_64'
```

正式项目建立后，构建方式统一使用 CMake；下面命令需要项目已有根 `CMakeLists.txt`，不能把尚未建立的工程当作已经存在：

```powershell
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
```

## 已完成的验证

使用隔离临时工程，未开发正式 PCB 功能：

1. `qmake -query` 与 `qtpaths --qt-version` 均返回 **6.12.0**，所有安装路径指向实际 SDK。
2. CMake 成功发现 Qt Core、Gui、Widgets、Test、SVG、PrintSupport。
3. 使用现有 **MSVC 2026** 成功编译、链接 Release Qt Widgets 程序，自动 MOC 正常。
4. `windeployqt --release --compiler-runtime` 完成 DLL、Windows 平台插件及运行库安装器收集。
5. 从部署目录实际启动中文窗口，Qt Test 模拟鼠标点击，信号槽改变界面文案，保存截图并检查结果；进程退出码为 **0**。
6. 已查看截图，确认窗口实际渲染、中文显示与交互成功，不是只检查程序进程存在。

这些结果证明本机 MSVC 2026 与该套 Qt 预编译库在上述测试中可用，因此本次没有补装 v143 工具集。不能由此宣称所有第三方 C++ 库、全部 Qt 模块或所有优化选项均已验证。

构建中的 `Could NOT find WrapVulkanHeaders` 是未安装可选 Vulkan SDK 的提示，不影响本次 Qt Widgets 二维界面构建；不需要为此安装 Vulkan。

临时验证源码、构建、部署、截图与结果位于被忽略的 `.local-analysis/qt-smoke/`。

## 尚未验证与发布注意事项

- 尚未在 Windows 10 实机或未安装开发工具的干净机器上验证。
- Qt 6.12 官方 Windows 平台文档仍列出 Windows 10 1809 及以后版本，并注明这是最后一个支持 Windows 10 的 Qt 次版本系列。以后升级 Qt 必须重新核对平台支持矩阵，不能无条件跟随最新版。
- `windeployqt` 收集到 VC++ 运行库安装器，不等于在目标机器上已安装运行库；正式安装包仍要处理运行库和许可文件。
- 使用公开预编译包不代表已购买 Qt 商业许可证。项目应逐模块核对 LGPL/GPL/商业许可及第三方许可；正式分发前另行处理动态链接、许可告知、对应源码等义务。
- 本机 SDK 的完整性校验不是对所有二进制行为的安全证明。
