# 走线放置真实窗口验收记录

2026-11-02 对父集成源码 `bd885c148b48e40edbfee6d30582a59d86732ff6` 完成了有限范围的真实 Windows 窗口验收。整数面板预览、取消不修改、诊断提交及菜单撤销/重做、普通产品新增菜单禁用、已有走线删除/撤销均取得原图证据；第三槽诊断及普通产品均取得创建者真实正常退出回执。完整 Task **未完成，结算为 failed**：现场 F3、完整文本焦点路径、隐藏目标层和菜单 Esc 取消尚未验证，不能报告全部 GUI 验收通过。

产品 `place.track`／F3 能力门继续为 `false`。诊断程序通过显式 `beginTrackPlacement(17, 6)` 进入内部放置，窗口标题和工具栏均标注“仅诊断入口；产品新增未开放”；其成功提交不证明普通产品新增命令、默认 FT 编码或新增保存已经开放。本轮没有进行新增文件写出，也没有验证原软件兼容性。

## 源码、构建和会话

- Task：`task_4d9205c7b9c2`；Dispatch：`ctx_fb7a2a49bf0f`。
- 验收工作树：`feat/track-placement-ui`；父源码路径：`C:/Users/rikideng/orca/workspaces/pt_renew/main-2`。
- 冻结时父分支为 `feat/track-native-integration`，唯一 dirty 文件为 `docs/free-track-creation-design.md`。完整差异保存在本地 `source-diff.patch`；没有产品源码脏改。
- 独立冻结副本位于 `.local-analysis/track-placement-live/source-snapshot/`，共记录 335 个文件。验收后复核 125 个源码、测试及 CMake 文件，SHA-256 全部匹配冻结清单。
- 本地 `harness/` 复用冻结副本的 `pt_ui`；Debug 构建输出在 `build-frozen/`，构建退出为 0。真实窗口运行未设置 `QT_QPA_PLATFORM=offscreen`；第二、三槽使用 `QT_SCALE_FACTOR=0.666667`。
- 沿用 Pi `deng/gpt-6.1-sol`、`high` 和会话 `01a19a2e-36c1-7793-8cc2-3f7677a76600`，未换模型、会话或派生代理。`session-final-audit.json` 记录实际模型事件及助手消息模型。

| 现场构建产物（相对于本地证据根） | SHA-256 |
| --- | --- |
| `build-frozen/pt-track-placement-diagnostic.exe` | `4ceca7a6dd0f8fc5224736ffd82d93f1a1cc89fb2bce66d624d5fbb0aeede888` |
| `build-frozen/product/pt-renew.exe` | `b47c321846a8cb714a4381188722bcadb7f174a502a098118e190dfd8a6eab71` |

父提供的 Debug 第二轮和 Release 第一轮配置、构建、CTest 创建者 wait 均为 0，父报告两轮均为 22/22。本地保存原检查回执；这是自动化验证证据，不能替代下面的真实窗口证据。Release 回执中的 CTest 实际时长为约 31.95 秒。

## 输入保护与进程退出

本轮仅使用新建合成 `runtime/DIAG.PCB` 和 `runtime/PRODUCT.PCB`，各 66 字节，含两条已有 FT：`0 0 1000 0 12 1`、`0 800 1000 800 12 6`。两文件验收前后 SHA-256 均为 `26424e685617887aa7573434c338d8b8ebc7c4cdb0131b1ad03b27583148a4a5`，见 `inputs-before.json` 和 `inputs-after.json`。没有覆盖原软件、库或用户板图，没有发布任何 PCB 输出文件。

每次运行由 `launch_owner.py` 持有实际 `subprocess.Popen` 与 HANDLE，记录 PID、创建 FILETIME、可执行摘要及真实 `wait()`；不是从进程消失推断退出码。每个 owner 启动时读取固定截止，未通过修改 GO 延长旧进程。

| 运行 | owner PID / 目标 PID | 创建 FILETIME | 真实 wait | 截止强制退出 | 结束时间（北京时间） |
| --- | --- | --- | --- | --- | --- |
| 诊断第一槽 | 57844 / 40700 | 134380665925682337 | 1 | 是 | 12:31:00 |
| 诊断第二槽 | 16528 / 24468 | 134380677500840020 | 1 | 是 | 13:03:00 |
| 诊断第三槽 | 47520 / 56396 | 134380697509869796 | 0 | 否 | 13:17:42 |
| 普通产品第三槽 | 49132 / 63396 | 134380704101690134 | 0 | 否 | 13:30:34 |

第一、二槽均未及时正常关闭，必须保留为 forced wait1。第三槽诊断点窗口关闭后读图看到 `discardChangesDialog`，再点“放弃更改”；普通产品撤销到 clean 后点关闭。后两次关闭操作的 RPC 因目标已退出返回 `app_not_found`，分别与创建者同刻记录的 wait0 对照，不把 RPC 退出 1 本身当作正常退出证据。诊断第三槽的正常退出依据为 `runtime/diagnostic3-exit.json`，产品为 `runtime/product3-exit.json`。

第三槽授权为 13:05–13:50、13:43 起收尾；本 worker 在 13:30 关闭产品，随后结构化交回桌面，不再键鼠。父于 13:35 将桌面移交原软件 worker。

## 实际通过的业务边界

以下证据名相对于 `.local-analysis/track-placement-live/rpc/`；原 PNG、原始 RPC JSON 和 receipt JSON 均保留。第三槽每个列出的业务结果图均在下一业务动作前实际 read，获得成功 image 回执。同一点的 X/Y 按父授权成组填写，再抓图/read，确认后才取点。

| 项目 | 现场结果 | 关键原图 |
| --- | --- | --- |
| 初始诊断状态 | 2 图元、未修改，宽 17 mil、目标层 6、等待起点，标题明确内部诊断 | `t301-initial-0.png` |
| 整数起点 | 输入 `(200,250)` 后取点，显示起点标记，工作副本未修改 | `t304-start-fields-0.png`、`t305-start-0.png` |
| 整数终点与预览 | 输入 `(800,550)` 后生成可辨的蓝色半透明线，显示宽/层/起终点；仍为 2 图元未修改 | `t309-end-fields-0.png`、`t310-preview-0.png` |
| 取消不修改 | 第一槽点取消后临时线和起点消失，放置结束，仍为 2 图元未修改 | `d07-preview-0.png`、`d09-cancel-coordinate-0.png` |
| 显式诊断提交 | 点击确认后斜线为正式图元，共 3 图元且 dirty；面板显示放置结束、没有待提交预览 | `t311-commit-0.png`（第二槽亦有 `s212-commit-0.png`） |
| 新增撤销 | 编辑菜单点击撤销，斜线消失，恢复 2 图元、clean，无临时预览 | `t317-undo-click-0.png` |
| 新增重做 | 编辑菜单点击重做，斜线恢复，3 图元、dirty，无临时预览 | `t319-redo-click-0.png` |
| 诊断关闭确认 | 关闭 dirty 工作副本时弹出放弃更改确认，随后创建者 wait0 | `t320-close-0.png` |
| 普通产品能力门 | “放置走线(T)（未实现）”灰显，显示 F3 标签；无内部诊断工具栏和放置面板 | `p301-initial-0.png`、`p304-place-menu-0.png` |
| 既有图元选择 | 选中顶层 12 mil、`(0,0)` 到 `(1000,0)` 的自由走线，属性只读显示对应数据 | `p305-select-existing-0.png` |
| 既有删除 | 删除菜单的“删除所选自由走线”可用；执行后红色走线消失，1 图元、dirty | `p306-delete-menu-0.png`、`p308-delete-existing-0.png` |
| 既有撤销 | 编辑菜单撤销后红线恢复，2 图元、clean；随后正常关闭产品，创建者 wait0 | `p310-undo-existing-0.png` |

原任务写“虚线预览”，实际实现为目标层颜色的半透明实线及端点标记，父已明确接受该样式，本轮没有修改源码来改变样式。预览坐标和宽/层由窗口文案与实际画面共同确认，不单独依赖诊断遥测。

## 失败、未覆盖和证据限制

- **现场 F3 未验证**：`p302-f3` 的 `press-key F3` 被 Orca 以 `invalid_argument / Unsupported key: F3` 拒绝；`p303-f3-hotkey` 的 `hotkey F3` 则被本地参数校验以 `Hotkey requires a modifier and one key` 拒绝，两者均未送达产品。父随后要求保留工具边界，不另造注入；不能将此记录为产品失败或“F3 不新增已通过”。F3 与文本焦点的自动化测试结果应与现场证据分列。
- **Ctrl+Z 快捷键未通过现场确认**：第二槽 `s214-undo` 因 `window_not_focused` 未发送；第三槽 `t312-undo` 加 `--restore-window` 后 RPC 成功，但原图仍为 3 图元 dirty，因此不能把快捷键计为成功。之后菜单 Undo/Redo 成功只证明共享命令行为。没有实际通过的 Ctrl+Y 现场证据。
- **文本 P 只观察到有限状态**：`p313-text-p-0.png` 中搜索框显示输入法预编辑 `P` 和候选窗，未见放置菜单；`p314-commit-text-0.png` 回车后搜索框为空。没有完整验证文本编辑快捷键，不能把预编辑状态冒称已提交文本输入。画布 P 唤出菜单、P→T、菜单 Esc 退出也未完成现场验证。
- **隐藏目标层、菜单 Esc 的统一取消未覆盖**，不能由显式取消按钮推导这些路径已通过。原生另存框和保存重开属于可选回归，本轮未执行；没有任何新增保存或原软件兼容通过结论。
- **旧索引失败保留**：第一槽 `d08-cancel` 原错误为 `element 107 is not in the current cached snapshot; run get-app-state again and use a fresh element index`，随后按已读图坐标取消成功。第二槽 `s202/s203` 也发生旧索引失效；未删除失败回执。
- **第一槽逐步读图不完整**：`d05-endx-0.png`、`d06-endy-0.png` 没有可核验的成功 image 回执，不能补造提交之前的读图时序。第一槽部分原图为 2272×1481，read 返回缩放图为 2000×1304，不能声称缩图 SHA 等于原 PNG。第二、三槽主要窗口原图为 1522×1006；普通产品为 1462×906，菜单截图尺寸更小。
- 本地审计共 39 张原始 PNG，39 张均与 RPC receipt 的原图 SHA 匹配，37 张关联成功 image 回执。`image-read-audit.json` 分别记录原图 SHA、尺寸、read 关联、成功回执事件 ID、回执图尺寸和真实字节比较结果；同路径关联不自动意味着相同字节。原图受其他窗口遮挡的 `s208-refresh` 也原样保留，不以它证明完整预览画面。

## 回归修复与后续交付

验收准备时发现两个原有测试回归，经父授权提交 `4c3b7645be6a1299be3e4980c56db601d0943f7f` 并已纳入上述父冻结 HEAD：模态和另存只取消走线放置、保留原选择；画布仅在活动走线/测量时消费 Esc，空闲 Esc 可继续传播到 LIB 对话框。修前两项测试真实退出 1，修后 Writing 40、Library 26、UI 13 用例全部通过，相关退出均为 0，见本地 `regression-before-exit.json`、`regression-after-exit.json` 及对应文本日志。本轮后续真实窗口阶段未再修改产品源码。

本地证据根为 `.local-analysis/track-placement-live/`，其中 `REPORT.md`、`image-read-audit.json`、`inputs-after.json`、`source-integrity-after.json`、`exits-summary.json` 和 `session-final-audit.json` 可供父复核；诊断源码、冻结清单、构建日志和原始窗口证据均在该目录。该目录、原软件截图、构建产物及合成运行输入不提交 Git，本次 Git 交付仅为本中文验收文档。未合并 dev、未推送，完整验收仍需后续任务补齐上述未覆盖路径。
