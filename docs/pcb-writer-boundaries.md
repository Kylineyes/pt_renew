# PCB 写出边界：精确几何校验

本轮基于 `0655a004a2772e3624f73eb9cb3341ded0f7ef74`，在独立分支 `fix/pcb-writer-boundaries` 复核已有自由 FT 移动／删除和显式 Created 输出。发现并修复一类可复现缺陷：writer 使用 Qt 的模糊几何相等判断，接受了本应拒绝的小数模型篡改，并以成功结果发布了丢弃该修改的文件。本轮只修改 writer 的比较逻辑及对应功能回归，不涉及 reader、codec、界面或能力门。

## 触发条件与影响

Qt 6.12 的 `QPointF::operator==` 使用模糊比较，`QRectF::operator==` 也通过模糊比较核对位置与尺寸。旧 writer 将这些运算符用于冻结原模型、工作模型的只读图元、已有走线和最终输出重解析校验，因而同一处小误差能够同时通过写出前与写出后的检查。

可复现流程：

1. 用严格 reader 载入合成 PCB，得到合法整数坐标的冻结文档。
2. 将工作副本中首条 FT 的起点 X 从 `100` 改成 `100 + 1e-13`，保持终点、身份、来源、冻结字节和摘要不变。
3. 调用默认 `saveAs`；或者先通过真实编辑会话新增一条 Created，修改其工作副本里的上述 Loaded 起点，再调用显式 `saveAsWithCreated`。
4. 旧实现返回成功并发布新文件，输出中 Loaded 起点仍是 `100`。在显式路径里，新建段被写出，非法旧段修改被静默丢弃。

同一问题还使冻结原模型与字节不一致时未被拒绝，并能绕过元件内 CT、焊盘、过孔、圆弧、填充位置／尺寸、文字位置及元件原点的只读保护。正常 `BoardEditSession` 的整数编辑接口不会产生这种小数输入；本缺陷发生在 writer 接受不符合约束的直接调用模型时。它不证明 reader 会产生小数，也不表示合成输入兼容原 AUTOTRAX。

## 最小修复

`src/io/LegacyPcbWriter.cpp` 内增加逐分量精确比较：点按 X／Y，矩形按 X／Y／宽／高比较。冻结模型、工作模型和输出重解析均使用这些比较；整线移动的两个端点位移也按分量精确核对。这样，小数修改不能再被“未修改”分支跳过，已有坐标／只读对象检查会明确拒绝，发布前即返回失败。

reader 产生的坐标、尺寸和合法整数 mil 平移均能在当前范围内精确表示，不需要容差。字节替换、来源行推导、Loaded 身份重建、记录计数、容量和文件发布代码保持既有行为。默认 `prepare`／`saveAs` 继续拒绝 Created；显式六／七字段、附加整数及 LF／CRLF 参数要求、无新增时 NETDEF 保留、有新增时 NETDEF 拒绝均保持原规则，普通产品新增能力门继续为 false。

## 先失败、后通过的功能回归

`tests/WritingTests.cpp::rejectsSubIntegerGeometryChanges` 用 10 种修改分别测试工作模型和冻结原模型，共 20 个数据行。每行实际调用 `saveAs`，断言拒绝、不产生目标文件、冻结输入字节不变，覆盖 FT 起点／终点、CT、各只读图元及填充位置与尺寸。

`tests/TrackCreatedWritingTests.cpp::fractionalLoadedEditCannotDisappearDuringCreatedPublish` 先通过真实 `BoardEditSession::addTrack` 新建一段，再对工作快照中的 Loaded 起点施加可表示的小数差异，实际调用显式发布入口。它核对非法组合不得发布，同时原字节、Created 身份和真实会话 dirty 保持原状。

在增加以上测试、生产实现仍为基线时，实际运行得到：

| 阶段 | 普通发布新增回归 | 显式 Created 发布新增回归 |
| --- | --- | --- |
| 旧实现 | 20 个失败，进程退出 20 | 1 个失败，进程退出 1 |
| 修复后 | 22 项通过，进程退出 0 | 3 项通过，进程退出 0 |

修复后统计包含 QtTest 初始化／清理，因此新增功能数据行仍为 20 + 1 个。失败点均为旧实现意外返回发布成功，并非编译或环境错误。

## Release 验证与证据

本树独立使用现有 Qt 6.12.0／MSVC x64／Ninja 环境，Release 配置、旧实现加回归构建、修复后构建均实际退出 0。修复后执行以下四组，CTest **4/4 通过、退出 0，耗时 18.90 秒**：

| 测试 | QtTest 通过项，含初始化／清理 |
| --- | ---: |
| `pt-writing-tests` | 60 |
| `pt-track-created-writing-tests` | 68 |
| `pt-track-insertion-plan-tests` | 72 |
| `pt-track-preflight-workflow-tests` | 8 |

现有功能回归同时覆盖：合法输入无编辑字节保留、混合换行和尾部 DOS EOF、已有移动／删除与元件前后记录、删除后的来源行和 Loaded 身份、尾部／交错 NETDEF 的默认保留与新增拒绝、200000 条真实语法记录及删除释放、64 MiB 边界及数字扩张、冻结输入不重读、新目标不覆盖、发布失败无临时残留。这些测试本轮均通过，未从这些范围另证其他缺陷。

复核命令：

```powershell
& './scripts/Enter-QtEnv.ps1'
cmake --preset release
cmake --build --preset release --parallel 2 --target pt-writing-tests pt-track-created-writing-tests pt-track-insertion-plan-tests pt-track-preflight-workflow-tests
$env:QT_QPA_PLATFORM='offscreen'
ctest --preset release --parallel 2 -R '^pt-(writing|track-created-writing|track-insertion-plan|track-preflight-workflow)-tests$'
```

本机证据保存在本树忽略目录 `.local-analysis/pcb-writer-boundaries/`：

- `old-build-exit.json`、`old-regression-results.json` 与 `old-regression-{writing,created}.txt` 保留基线加回归时的真实失败结果。
- `fixed-build-exit.json`、`fixed-regression-results.json`、`fixed-ctest-exit.json`、各完整 QtTest 日志和 `qt-test-totals.json` 保留修复后的真实结果。
- 原 PowerShell `.log` 保持原样，同时提供 `.utf8.log` 副本便于读取。
- `synthetic-writing-input.pcb` 和 `synthetic-input-sha256.json` 保留普通回归合成输入与摘要；两组测试中的输入构造本身也保留在提交的测试源码。
- `model-source-audit.json` 记录原 Pi 会话 `01a19f99-9252-74f7-9844-99633c12fe1f` 的 `deng/gpt-6.1-sol`、`high` 原事件、assistant／成功工具事件及基线 writer blob。

本轮没有 GUI 变更，不使用桌面或截图，不接触原安装、库或用户板图。全量 Debug／Release 集成验收交协调者；本页的专项通过不替代父验收，也不提升原 AUTOTRAX 格式兼容结论。
