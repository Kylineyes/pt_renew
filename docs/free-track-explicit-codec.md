# 自由走线 FT 显式合成编码器

`LegacyFreeTrackCodec` 是仅依赖 Qt Core 的内存编码工具，将调用方独立提供的走线几何和明确编码选项转换为一条 FT 记录。它不读写文件，不接入生产入口，不改变 `LegacyPcbWriter` 的新增拒绝保护。原 AUTOTRAX 的 FT 默认字段、附加属性及默认换行编码仍未核定；本项目解析器能够读回合成结果，不构成原软件兼容验收。

本阶段基线为 `2c0a60697c20ac565759d052229749583e89f839`，开发分支为 `feat/free-track-codec`。仅新增编码器头／实现、专项测试和本文档；根 CMake 注册及集成回归由协调者完成。

## 接口与明确参数

```cpp
using Codec = pt::LegacyFreeTrackCodec;
const Codec::Options options{
    Codec::FieldLayout::SevenFields,
    Codec::LineEnding::CrLf,
    -9
};
const auto result = Codec::encode({10, 20}, {30, 40}, 8, 6, options);
// 成功字节：FT\r\n10 20 30 40 8 6 -9\r\n
```

`encode(start, end, width, layer, options)` 接收 `QPointF` 起终点、整数线宽、整数图层及 `Options`，返回 `Result{bytes, error}`；`succeeded()` 表示得到完整非空字节且无错误。失败时 `bytes` 为空，`error` 给出具体中文原因。

| 选项 | 默认值 | 合法显式值及要求 |
| --- | --- | --- |
| `Options::fields` | `FieldLayout::Unspecified` | `SixFields` 或 `SevenFields` |
| `Options::lineEnding` | `LineEnding::Unspecified` | `Lf` 或 `CrLf` |
| `Options::extra` | 空 `std::optional<int>` | 六字段必须为空；七字段必须显式提供整数 |

缺省选项、缺失或矛盾的附加整数、强制转换得到的非法枚举值一律拒绝。七字段不会自动填入 1；零、负数以及 `int` 的两端值均按调用方明确提供的值保留，不解释电气语义。接口不接收已有 `Track`，不会复制旧记录的 `extra`，也没有来源、身份、文件路径或隐式配置参数。

换行只通过枚举选择，没有任意字符串入口，因此不能传入混合换行、孤立 CR 或附带其他标签的注入文本。把 CR／LF 字节数值强转为枚举也会因枚举无效被拒绝。

## 几何与输出规则

几何规则与核心 `addTrack` 的单段约束一致：起终点四个坐标都必须为有限整数，范围为 ±1000000 mil；不接受小数、NaN、正负无穷及越界值。起终点不能相同，线宽为 1 至 1000000 mil，层仅允许顶层 1 或底层 6。编码器不维护文档和历史，因此不承担会话修订、数量或身份检查。

所有校验通过后才把坐标转换为整数，使用 `QByteArray::number` 生成规范 ASCII 十进制；字段之间恰好一个空格，没有前导加号、分组符或尾部空格。浮点负零输出为 `0`，区域设置不改变数字字节。输出恰好两行：`FT` 标签行和数值行，两行均使用所选换行并终止。没有网格捕捉、隐式取整、DOS EOF 或文件头／结束标签。

## 专项验证

本轮沿用 Pi 会话 `01a1986f-2198-700e-9abd-4b9af7a122c6`，核对实际 `deng/gpt-6.1-sol`、推理强度 `high`。新证据目录 `.local-analysis/free-track-codec/` 包含环境与分支基线记录 `model-session.json`、会话实际模型／推理及 assistant 消息摘要 `session-records.json`，未修改既有 provider 会话。

独立验证工程位于 `.local-analysis/free-track-codec/harness/CMakeLists.txt`：以 `BUILD_TESTING=OFF` 引入仓库，单独编译新增编码器及测试，链接 `pt_core` 和 `Qt6::Test`，仅构建 `pt-free-track-codec-tests`。复现时在工作树根使用 PowerShell 执行：

```powershell
& ./.local-analysis/free-track-codec/verify.ps1
```

脚本使用既有 `scripts/Enter-QtEnv.ps1`。实际环境为 Qt 6.12.0、MSVC 19.51 x64／Ninja，本轮一次 Debug 配置、构建及专项测试完成：

| 验证 | 实际结果 |
| --- | --- |
| CMake 配置 | 退出码 0 |
| Debug 专项目标构建 | 退出码 0 |
| CTest | 退出码 0，1/1 通过，0.21 秒 |
| QtTest | 72 通过，0 失败，0 跳过，包含初始化与清理 |

专项覆盖六／七字段与 LF／CRLF 四种组合的确切字节、正负边界坐标、最大与最小线宽、附加字段的 `int` 两端值／零／负数、阿拉伯区域设置及负零、缺省与矛盾选项、非法字段和换行枚举，并在四个坐标分量分别检查小数、NaN、正负无穷、极大数和最小非零浮点值等非法输入。宽度、图层和零长线均验证拒绝且不返回局部字节。

成功记录放入合成 `PCB FILE 4` 后通过现有解析器核对几何和附加字段。这仅证明项目内部语法往返。另以现有七字段源记录建立编辑会话，调用 `addTrack` 后执行显式编码，确认会话、修订、冻结原字节与原附加字段不变；`LegacyPcbWriter::prepare` 和 `saveAs` 仍拒绝新增工作副本，临时目录不产生目标或临时文件。

完整命令与退出码见 `verification-transcript.txt`，日志为 `configure-Debug.log`、`build-Debug.log`、`ctest-Debug.log`，详细断言结果为 `build-Debug/free-track-codec-test-results.txt`。本轮未运行 GUI、截图、原二进制或原安装，也未开放新增写出或 GUI 功能。后续仍需独立核定原 FT 默认编码及原软件兼容，不能用本工具的显式选择自动解锁 writer。
