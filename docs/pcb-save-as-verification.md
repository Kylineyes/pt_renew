# 自由走线编辑与受限另存为独立验收

2026-10-31 完成静态审阅及一次真实 Qt Windows 窗口验收，结果通过，未发现阻断本次范围的问题。本次实际操作将既有自由走线平移后另存为全新 PCB，并在新的产品主窗口重新载入；取消保存、保存失败保护、文件框期间修订变化和临时文件发布失败也通过指定测试。第三张截图未直接显示滚动区域下方的最近保存路径和摘要，这一视觉覆盖限制保留，不补跑或补图。

执行者为任务 `task_7c4df24a2c54`、派发 `ctx_0bead893a9d1` 的独立工作者，分支 `verify/pcb-save-as`，开始时 HEAD 为 `ef86125ca0084f5aadecca3b84c637417f3c095c`。环境 `PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`、`PI_SESSION_ID=a456c840-52d0-4e61-a62b-df6e1c5c1974` 与原 JSONL 的会话、模型、推理等级及 assistant 记录一致。未替换模型，未编辑父实现，未合并或推送任何分支，未创建版本标签或发布。

证据均保存在本工作树被 Git 忽略的 `.local-analysis/pcb-save-as/`。身份见 `worker-identity.json`；原会话路径由其中的 `PI_SESSION_FILE` 记录。`session-evidence-prefix.jsonl` 保存取证时原会话前缀的原字节，`image-read-receipts.json` 关联四次原 `read` 调用与成功的 PNG image 回执，`authorization-original-tool-receipt.json` 保留协调者的最终执行授权原工具回执。

已完整阅读项目 `AGENTS.md`，并只读审阅父树 `src/io/LegacyPcbWriter.h/.cpp`、`LegacyPcbReader.cpp`、`src/domain/BoardDocument.h`、`src/application/BoardEditSession.h/.cpp`、`src/ui/MainWindow.h/.cpp` 及 `tests/WritingTests.cpp`，随后复核路径保护补丁和两项新增故障测试。审阅结论如下。

| 检查项 | 结论与依据 |
| --- | --- |
| 原字节与 FT 来源映射 | 读取器冻结完整输入字节、大小及 SHA-256；写出前重新解析核对基线。走线按原来源行建立映射，避免删除后的数组下标被误当记录身份；新增、重复、重排、元件内部走线变更被拒绝。 |
| 未改内容保留 | 平移只替换 FT 数值行的前四个坐标词，删除只移除该 FT 标签及数值行。其他分隔符、换行、非 ASCII 字节、DOS EOF、附加字段、元件、其他图元及 NETDEF 保留原字节；发布前再次解析核对模型。 |
| 原件与已有目标 | 拒绝原输入路径、已有文件及链接，要求 `.pcb`，并拒绝文件名冒号和常规 Windows 设备名。原件即使被移除也不能通过原输入路径重新写入；保存成功保留原输入身份。 |
| 临时文件发布 | 在目标同目录创建 `QTemporaryFile`，完整写入并 flush 后重命名；失败保留自动清理。父已下载的官方 Qt 6.12 源码确认 `QTemporaryFile::rename` 仅进行原子重命名且拒绝已有目标，不采用 `QFile::rename` 的复制删除回退；Windows 后端调用不覆盖的 `MoveFile`。原源码摘录和文件摘要见 `qt-rename-source.txt`。 |
| 保存点与历史 | 保存成功仅标记当前历史位置；Undo/Redo 可返回保存点，截断包含保存点的重做分支会使保存点失效。保存失败及取消不清理工作副本、修订或历史。 |
| 文件框期间修订 | 打开文件框前捕获修订号，返回后不匹配即拒绝保存。新增用例在嵌套事件循环期间实际移动走线，验证不生成旧状态目标文件且保留 dirty/Undo。 |

唯一执行目录为父树 `main-2/.local-analysis/pcb-save-as/frozen-gui-verified`，旧冻结目录均未执行。清单 `manifest.json` 的 SHA-256 为 `c002b01555ff752cce17d1b65e0365dbbf769902b7e7c6da88f56585a5d41aff`，`bin/pt-writing-tests.exe` 的 SHA-256 为 `aa2ea9f7b6da2a9efd3e91515c4950bacf9e4b2cbef3f718526ca5fb8bab5768`。运行前、后均核对清单的 57 个源码和 20 个二进制/依赖文件，且全部源码与父当前源码逐字相同；两次结果分别见 `frozen-before.json` 和 `frozen-after.json`。合成板模板嵌入冻结的 `tests/WritingTests.cpp`，也在上述摘要覆盖中。

父提供的构建来源为其 `feat/pcb-save-as` 当前源码及冻结的完整 CMake、产品源码和 C++ 测试。协调者报告 Debug、Release 各 12/12 测试组通过，最近完整 Release CTest 用时 4.70 秒、Debug 用时 19.61 秒；最后只校正临时文件原子语义注释并增量编译。独立工作者未重复构建或扩大测试范围，本报告独立执行结果限于下述五个函数。

协调者允许自 2026-10-31 15:35（UTC+8）开始；完成材料核对后的实际进程起止为 **15:37:38.239300 至 15:37:39.426584（UTC+8）**。`run_authorized_gui.py` 只创建一次测试进程并持有原始 `Popen` 至 `wait()` 返回，PID 为 **21564**，Windows 创建 FILETIME 为 `134379058582402521`，原句柄为 **496**。实际进程映像确为上述冻结 EXE，原始 `Popen` 对象及句柄在创建、退出记录中一致，实际退出码为 **0**；见 `gui/process-created.json`、`gui/process-exit.json` 和记录进程的 `monitor-launch-receipt.json`。

启动环境显式设为 `QT_QPA_PLATFORM=windows`，截图目录为本树全新 `gui/` 绝对路径；PATH 仅含冻结 `bin`、Windows `System32` 和 Windows 目录。启动器检查并移除原环境中的 QT/QML 及相关 CMake 路径变量，本次没有匹配的遗留变量。未使用 offscreen、SDK 运行路径、全局键鼠、旧演练或控制服务，未重试、强杀或追加 GUI 进程。

实际命令等价于以下内容，其中 `<冻结目录>` 和 `<本树证据目录>` 的真实绝对值完整保留在 `gui/process-exit.json`：

```text
<冻结目录>/bin/pt-writing-tests.exe menuSaveAsReopensEditedGeometry cancelledSaveDialogPreservesWorkingDocumentAndHistory windowSaveKeepsHistoryAndFailedSaveKeepsDirty documentChangedDuringSaveDialogDoesNotWriteStaleRevision failedPublishRemovesTemporaryAndPreservesInputs -o -,txt -o <本树证据目录>/gui/gui-results.txt,txt
```

`gui/gui-results.txt` 原日志报告 **7 passed、0 failed、0 skipped**，包括五个业务函数及初始化、清理，QtTest 用时 966 ms。五个业务函数分别验证移动框及 Ctrl+Shift+S 保存重开、取消保留工作与历史、拒绝原件保存且成功保存保留 Undo/Redo、文件框期间修订变化拒绝旧状态、发布失败清除临时文件并保持原输入。最后一项使用 300 字符的文件名触发重命名失败，并断言错误确来自发布阶段。原 stdout、stderr 按字节保存于 `gui/stdout.bin`、`gui/stderr.bin`，本次两者均为 0 字节；测试文本输出实际保存在指定日志文件，未改写或补造控制台输出。

本 Pi 使用原 `read` 分别打开并实际查看以下四张图片，四次均收到成功的 image 回执。图片来自窗口/控件的 `QWidget::grab()`，文件框图片不包含窗口外框标题栏。

| 原图 | 实际可见内容与判断 |
| --- | --- |
| `gui/01-moved.png` | 真实产品主窗显示所选顶层自由走线，属性中起点 `(150,75)`、终点 `(450,475)` mil、宽度 10 mil、附加字段 42，右上方为“有未另存为的更改”，底部也显示工作副本已修改。 |
| `gui/02-save-dialog.png` | 可见 Qt 保存文件框、临时目录定位栏、文件名 `edited.pcb`、AUTOTRAX 板图过滤器及 Save/Cancel。定位栏完整路径被省略，图中不能直接读出完整目录或中文标题；具体临时目标由冻结测试源码及成功断言补充。 |
| `gui/03-saved.png` | 同一几何和附加字段仍在；右上方变为“未修改或与最近另存为一致”，底部显示 `file.save_as` 及工作副本未修改。最近另存为路径和 SHA 位于滚动区域下方，截图未直接覆盖，不声称已从此图读到。 |
| `gui/04-reopened.png` | 新主窗右上方输入路径为 `edited.pcb`，大小 361 字节，显示新的 SHA-256；工作副本未修改，属性中的移动端点、宽度和附加字段 42 一致，底部明确提示已载入 `edited.pcb`。 |

测试使用 `QTemporaryDir` 创建项目合成板与全新目标，结束前实际读回输入并与模板比较，然后导出 `gui/source-before.pcb`、`gui/saved-roundtrip.pcb` 与 `gui/roundtrip.json`。`source-before.pcb` 是模板证据副本；原临时输入结束时保持不变由测试末次实际读回断言和 roundtrip 记录证明，并非独立保留的第二份原路径现场文件。

独立脚本 `verify_gui_artifacts.py` 从冻结源码提取合成模板，核对源导出逐字相同，并要求目标恰好等于将原 FT 四个坐标词替换后的模板。结果见 `gui/independent-byte-verification.json`：

| 对象 | 字节数 | SHA-256 |
| --- | ---: | --- |
| 合成源板及保持不变的输入 | 365 | `c633bb29e87b1f774950d3a188e583bd413a430de20c46747fcb5564ea1f2ff7` |
| 新保存 PCB | 361 | `7699d0341a27bd82b526ca38a379b1c0179bac79dce8c9ae0262f78763358b46` |

目标第一条自由 FT 为 `(150,75)→(450,475)`、宽度 10、图层 1、附加字段 42；第二条自由 FT 及元件 CT 均保持不变。逐字节相等检查证明四个坐标词以外的全部内容，包括元件、NETDEF、其他图元、混合换行、非 ASCII 文本及尾部 DOS EOF 均保持原样。产品 `LegacyPcbReader` 由新主窗口实际重读目标并通过端点断言，独立脚本还提取目标 FT/CT 数值进行交叉核对。`roundtrip.json` 的输入不变、保存后 clean、重开后 clean 及源/目标摘要均与独立结果一致。

本次通过的范围是：**链接同一真实产品 UI 的独立 QtTest 驱动，实际使用产品 MainWindow、移动对话框、命令模型、Ctrl+Shift+S、Qt 文件框和保存/重开实现**。移动输入及文件框保存按钮由进程内 QTest 事件完成，选择既有图元和部分辅助检查使用测试 API。QtTest 显式设置 `AA_DontUseNativeDialogs`，因此未证明 Windows 原生文件框行为；也未直接操作独立发行 EXE、验证原 AUTOTRAX 重开兼容、干净系统安装、完整异步竞争、DRC、布线或生产输出。自由走线删除和其他伪造输入的更广覆盖来自静态审阅及父报告的完整测试组，本次单次真实窗口主场景为移动，没有扩大为删除的独立 GUI 场景。

未接触原安装、用户板图或库写入，未新增图元或编辑元件。协调者随后独立复核了原会话、四次图片回执、进程退出、测试结果及源码/字节一致性，通知审计通过并要求仅完成本报告与结算；父证据为其 `parent-gui-audit.json`。本工作者仅提交本报告，忽略的本地证据留在原树供复核，后续整合与交接由协调者负责。
