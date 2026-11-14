# PT Renew

使用 **C++ + Qt 6** 重建 DOS 版 Protel AUTOTRAX 的 Windows 桌面工程。支持旧 PCB／LIB／NET 查看、选择定位、测量和受限铜分析；当前发布候选提供已载入自由走线的移动、删除、撤销重做及另存新 PCB。

**新版候选：v0.12.0-alpha**，范围及验证状态见[发布说明](docs/releases/v0.12.0-alpha.md)。当前固定候选已通过独立Release构建、24/24组CTest及[48项本机合成GUI验收](docs/releases/v0.12.0-alpha-verification.md#gui-matrix)。候选尚未打标签或发布附件；已有 [v0.11.0-alpha 下载包](https://github.com/Kylineyes/pt_renew/releases/tag/v0.11.0-alpha)仍为只读版本。

## 可用范围

| 能力 | 当前候选 |
| --- | --- |
| PCB／LIB／NET | 查看、缩放、图层、选择、属性、检索与网络引脚映射 |
| 测量 | 两点距离与可选端点捕捉 |
| 编辑 | 已载入自由走线的整数 mil 整线移动、删除、撤销和重做 |
| 保存 | Ctrl+Shift+S 另存全新目标，保留原件；已有目标和 Ctrl+S 覆盖保存拒绝 |
| 新增与生产 | 正式新增走线、元件编辑、完整 DRC、交互布线及生产输出未开放 |

文字和部分轮廓近似显示；铜分析不是完整 DRC，不能作为生产放行依据。编辑与写出边界见[编辑与另存](docs/pcb-save-as.md)。

## 构建

已验证的工具链为 Qt 6.12.0 MSVC x64、Visual Studio 2026、CMake 和 Ninja：

```powershell
& ./scripts/Enter-QtEnv.ps1
cmake --preset release
cmake --build --preset release
ctest --preset release
& ./build/release/pt-renew.exe
```

打开 PCB 使用 Ctrl+O，库浏览使用 Ctrl+L，载入 NET 使用 Ctrl+Shift+N。发布包完整解压后运行 pt-renew.exe，保留 DLL、插件及许可目录；最终包验证完成前不宣称新版已可下载。

原软件、安装介质、用户板图、库和字体不随本项目分发。研究材料、SDK、构建和发布二进制不提交 Git。协作规范见[AGENTS.md](AGENTS.md)，开发环境见[Qt 环境](docs/qt-development.md)。
