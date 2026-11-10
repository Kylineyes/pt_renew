# 新增自由走线插入预检

本阶段基于 `dev=2c0a60697c20ac565759d052229749583e89f839`，在 `feat/track-insertion-plan` 实现纯 QtCore 的 `LegacyTrackInsertionPlanner`。它只准备未编码的内存插入计划，检查新增记录身份、几何和旧记录保护，并重新取得受限编辑后的语法布局。

成功仅表示内部结构检查通过。新增 FT 的字段编码、未知附加属性、换行策略及原软件兼容性仍待独立核定；计划不能用于宣称新增可发布或原 AUTOTRAX 已兼容。现有 `LegacyPcbWriter` 继续拒绝包含新建段的工作文档，本阶段没有接入 writer、文件发布或产品入口。完整目标见[新增自由走线设计](free-track-creation-design.md)，布局定义见[严格语法布局元数据](pcb-layout-analysis.md)。

## 接口与结果

```cpp
const auto plan = pt::LegacyTrackInsertionPlanner::prepare(original, current);
if (!plan.succeeded()) {
    // plan.error 为具体的中文错误；失败时不提供可用局部计划。
    return;
}
// 此处仅可审查结构，尚不能把 plan 当成已编码文件或发布许可。
```

接口声明在 `src/io/LegacyTrackInsertionPlanner.h`，实现位于同名 `.cpp`。输入均为只读引用，不读取 `filePath` 指向的文件，也不修改文档、编辑历史、dirty、保存点或修订。

`LegacyTrackInsertionPlan` 包含：

| 字段 | 含义 |
| --- | --- |
| `baseBytes` | 只应用旧记录合法整线位移／删除的完整字节，不含新增 FT 字节 |
| `baseLayout` | 严格重新解析 `baseBytes` 得到的布局；所有偏移相对这些字节 |
| `createdTracks` | 按严格递增创建序号排列的新建段，尚未编码 |
| `insertionByteOffset` | 有新增时为 `baseBytes` 中顶层 ENDPCB 标签行起点；无新增时为 `-1` |
| `error`／`succeeded()` | 结构检查错误／结果是否完整有效，不表达原软件兼容性或发布能力 |

无新增时依然执行 writer 校验及严格布局解析，成功返回受限编辑后的基础字节和布局，`createdTracks` 为空、`insertionByteOffset=-1`。此路径允许原 writer 支持的尾部或交错 NETDEF 输入；`baseLayout.insertion` 仍是读取器报告的语法事实，不能因存在语法候选就执行新增。

所有失败统一返回空 `baseBytes`、空新段列表、`insertionByteOffset=-1` 和不含记录区间／ENDPCB 偏移的默认布局；`baseLayout.insertion.unavailableReason` 同时解释预检失败。不会先返回部分合法新段、原偏移或局部基础字节。

## 校验与基础字节路径

先遍历当前走线列表，拒绝 Unassigned 和未知身份类型。载入记录必须全部在新建记录之前；新建身份必须非零，且创建序号严格递增，因此不会有重复或倒序，撤销／分支截断产生的缺号允许保留。

每条 Created 记录还须满足：

- 来源保持无来源状态：`source.line=0`、`source.byteOffset=-1`、`source.component=-1`，拒绝伪造来源和其他负值。
- `extra` 必须没有值，即使附加值为 0 也拒绝；本阶段不选择六字段、七字段或默认附加属性。
- 四个坐标为有限整数且均在 ±1000000 mil 内；线宽为 1 至 1000000 mil，层号为 1 或 6，起终点不同。

通过后，从当前文档副本剥离 Created，交给现有 `LegacyPcbWriter::prepare(original, loadedOnly)`。冻结字节摘要、字节数、载入走线身份及来源、旧记录相对次序、整线平移和删除限制、其他图元／元件／NETDEF 不可修改规则全部复用原 writer；不复制一份 writer 的完整校验。原件中伪造 Created 或其他原件字段同样由 writer 对冻结字节的重解析比较拒绝。

随后使用 `LegacyPcbReader::parseWithLayout(baseBytes, original.filePath)`，获得删除、位移后实际字节的布局。数字位数变化和删除都会移动 ENDPCB，不能沿用原输入的偏移。高位字节、关键字内容字段、完整 COMP 区间、混合换行、无末尾换行和 DOS EOF 的处理继续经过原有共用路径；预检器不搜索 ENDPCB 文本，不选择换行，不归一化字节。

记录容量使用这次严格解析的 `document->recordCounts` 总和，再加未列入该映射的 ENDPCB 一条，最后加新段数，总计不得超过读取器的 200000 条上限。COMP、ENDCOMP、元件内部记录均计入，字段行和元件隐式文字不额外计数。不能以 `tracks.size()`、图元数或顶层区间数替代。原输入 `recordCounts` 仍由 writer 校验且保持不变；删除旧段会通过基础字节的真实计数释放容量。测试样例实际构造和冻结对应语法字节，不伪造计数来证明成功。

## NETDEF 和能力边界

<a id="explore-ex-010"></a>

有新段时，只接受 `netdefCount=0` 且候选为 `BeforeEndPcb` 的严格布局。尾部 NETDEF 返回“原软件排序尚未验证，本版暂不支持”，交错 NETDEF 与几何／COMP 返回明确的交错拒绝错误。不会依据尾部候选自行开放插入；即使原尾部 NETDEF 字节可完整保留，也不代表新增后的排序已获原软件验证。

[探索 EX-010](exploration-backlog.md#ex-010)。

`baseLayout.originalSoftwareInsertionVerified` 保持读取器返回的 `false`，未核定说明完整保留。`anchorLineEnding` 和其他换行字段只作观测，不成为新增 FT 的缺省编码。预检器不估算未知新增编码的字节数，不编码、不拼接新增 FT，也不调用任何文件保存接口。未来采用显式编码策略后，仍需对完整输出执行大小检查、严格重解析、语义比较及原软件兼容验收，并沿用新文件发布保护。

## 实际验证与证据

实际 Pi 会话为 `01a19892-370a-771e-a211-24198906e402`，环境与会话记录核对 provider/model 为 `deng/gpt-6.1-sol`、推理强度为 `high`，cwd 为本工作树，起始分支／HEAD 与上述基线一致。记录保存在被忽略的 `.local-analysis/track-insertion-plan/model-session.json` 和 `session-records.json`，后者包含真实 `model_change`、`thinking_level_change` 与 assistant 模型元数据。

临时工程为 `.local-analysis/track-insertion-plan/harness/CMakeLists.txt`，设置 `BUILD_TESTING=OFF` 后 `add_subdirectory` 本仓库，只额外编译新预检器与本次测试，链接 `pt_core`／`Qt6::Test`。根 CMake 和现有测试均未修改；正式注册及两配置全量集成验证由协调者完成。

执行脚本 `.local-analysis/track-insertion-plan/verify.ps1` 先启用 `scripts/Enter-QtEnv.ps1`，使用已有 Qt 6.12.0、MSVC 19.51 x64 和 Ninja。最终结果为：

| 配置 | 配置／构建／CTest 退出码 | CTest | QtTest |
| --- | --- | --- | --- |
| Debug | 0／0／0 | 1/1 通过，73.48 秒，超时预算 180 秒 | 72 通过、0 失败、0 跳过，含初始化和清理 |

实际命令依次为：

```powershell
& './scripts/Enter-QtEnv.ps1'
cmake -S .local-analysis/track-insertion-plan/harness -B .local-analysis/track-insertion-plan/build-Debug -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build .local-analysis/track-insertion-plan/build-Debug --target pt-track-insertion-plan-tests
ctest --test-dir .local-analysis/track-insertion-plan/build-Debug --output-on-failure -V
```

命令、退出码和输出保存在 `verification-transcript.txt`、`exit-codes.json`、`configure-Debug.log`、`build-Debug.log` 和 `ctest-Debug.log`；完整逐项结果为 `build-Debug/track-insertion-plan-test-results.txt`。本次只完成所要求的 Debug 专项，Release 和两配置全量验证由协调者执行。

专项覆盖新增后移动／删除旧记录的基础偏移、创建顺序和缺号／极限几何、重复或伪造身份／来源／附加属性、非法几何与参数、旧走线属性／元件内走线／其他图元修改保护、冻结原件篡改、尾部／交错 NETDEF、无新增、关键字字段／COMP／高位字节／DOS EOF／混合换行／无末尾换行、严格解析失败无局部计划，以及真实记录上限和删除释放容量。另直接断言原 writer 仍拒绝含新段文档，基础字节未包含新段，原冻结字节和编辑状态不变。

首次临时 CMake 工程误把仓库相对路径写多一级，导致配置失败；修正路径与 PowerShell 标准错误采集后完成首轮 Debug 验证。失败脚本退出码为 1，原始输出保留在追加式 `verification-transcript.txt`，说明见 `initial-attempt.json`。补充删除释放容量边界后的同步调用被工具的 60 秒等待上限终止，未视为测试结果；当次未完成日志和说明保存在 `ctest-interrupted.log`、`test-results-interrupted.txt` 和 `interrupted-attempt.json`，随后以独立进程完整重跑同一最终代码，取得上述明确退出码与 72 项通过结果。本阶段没有 GUI、截图、原软件运行或安装目录操作。
