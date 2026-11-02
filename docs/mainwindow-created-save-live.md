# 主窗显式新增另存现场验收

2026-11-02，Task `task_ecdc9a63dfe3`，Dispatch `ctx_a91aa16f3171`。本次指定核心范围通过：Windows 原生另存、保存点 Undo/Redo、输出真实重开、隐藏目标层取消和菜单 Escape 取消。未修改产品源码、产品 CMake 或测试，未开放普通产品新增入口。

沿用 Pi `deng/gpt-6.1-sol`、`high`，会话 `01a19a2e-36c1-7793-8cc2-3f7677a76600`。父授权源码为 `64e36d8e634f517fa86cb4b0266ace52911c5b56`；使用该提交的精确 `git archive` 快照构建独立诊断宿主，341 个文件最终复核无差异。诊断 exe SHA-256 为 `19eeb60f8e16854ebe9a994e1e1e7e3cd243f11991b971819e67642dc0bba8a0`，两次现场使用同一文件。

## 实际结果

证据根为 `.local-analysis/mainwindow-created-save-live/`，下表图片均为 `rpc/` 内原 PNG，已实际 read 并获得成功 image 回执。身份和状态 JSON 仅作辅助交叉核验。

| 范围 | 真实交互及观察 | 主要证据 |
| --- | --- | --- |
| 新增与原生另存 | 整数取点新增 `(200,250) → (800,550)`、17 mil、层 6；提交后 3 图元 dirty，取消下一段；真实 Windows 原生文件框写出全新默认目标，保存后 3 图元 clean | `n11-preview-0.png`、`n12-commit-0.png`、`n14-next-cancel-0.png`、`n15-native-save-0.png`、`n25-native-save-click-0.png` |
| 保存点 | 菜单 Undo 后 2 图元 dirty，菜单 Redo 后 3 图元 clean | `n27-undo-0.png`、`n29-redo-0.png` |
| 隐藏目标层取消 | 未提交 `(100,100) → (300,300)` 预览时隐藏层 6，面板显示放置结束且预览消失；恢复层 6 后已保存走线重现，仍 3 图元 clean | `n42-preview-0.png`、`n43-hide-target-0.png`、`n44-show-target-0.png` |
| 输出真实重开 | 新进程直接以已保存输出为输入启动；标题、原输入路径及 90 字节均指向 `DIAGNOSTIC-CREATED.PCB`，显示 3 图元 clean；辅助状态为三条 Loaded 身份 2/4/6、无 Undo/Redo 历史 | `r201-reopen-0.png`、`runtime/reopen2-held.json`、`runtime/reopen2-state.json.jsonl` |
| 菜单 Escape 取消 | 等待起点时打开编辑菜单；带窗口 ID 的两次 Escape 定位失败，随后以精确 `--app pid:19508 --key Escape --restore-window` 成功发送；读图显示菜单关闭、放置结束、无待提交预览、3 图元 clean，辅助状态为 Idle | `r202-edit-menu-0.png`、`r205-edit-reopen-raw.json`、`r207-escape-app-raw.json`、`r207-escape-app-0.png` |

真实重开仅在追加现场完成。首轮 `n31-start-cancel-test` 并非重开，首轮最终来源仍是 `INPUT.PCB`，新增身份仍为 Created；此前协调过程中关于已重开的误述已更正，不作为通过依据。

## 输入、输出和能力边界

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `runtime/INPUT.PCB` | 66 | `26424e685617887aa7573434c338d8b8ebc7c4cdb0131b1ad03b27583148a4a5` |
| `runtime/DIAGNOSTIC-CREATED.PCB` | 90 | `57892d56b1698d7f0d28d340881e3be2e3ccd8350ccece819478e0e095da9224` |

输入前后摘要一致，追加重开未修改输出。输出精确保留输入原字节，并在 `ENDPCB` 前插入 `FT\n200 250 800 550 17 6\n`。新增记录使用显式指定的**合成六字段／LF**；原输入既有行尾保持原样，不能把整份文件称为统一 LF。

诊断调用真实 `MainWindow::saveAsFileWithCreated`，未禁用原生对话框。普通产品 `place.track`／F3 能力门始终为 false。上述结果不证明普通产品入口开放、原 AUTOTRAX 默认编码或原软件兼容性，也不覆盖本任务外的 F3、文本输入等现场范围。

## 退出与失败记录

首轮 PID `31364`，birth FILETIME `134380865164826143`，owner `20196`。连接错误／超时使现场超过延长后的 18:55 截止；父于 19:02:38 核对精确进程身份、dirty=false 后调用 `Process.CloseMainWindow` 正常关闭。原 owner 记录 `waitReturn=0`、`forcedDeadlineTermination=false`；这是父接手的延后收尾，不能称 worker 按时自行退出。依据为 `runtime/diagnostic-exit.json` 和父证据 `.local-analysis/save-roundtrip-wave/parent-graceful-close.json`。

用户再次授权后，按父 `msg_5467ddbcc098` 在 20:30–21:00（20:53 收尾）追加最小现场。新 owner `7880`、PID `19508`、birth FILETIME `134380965448161576`，20:35:44 启动，20:45:18 正常点 X 退出。`runtime/reopen2-exit.json` 记录真实 `waitReturn=0`、`forcedDeadlineTermination=false`，早于收尾时间。关闭 RPC `r208` 因窗口已消失返回错误，退出结论依据原 owner 的真实 wait。

原生文件框的 modal HWND 定位、主窗键盘焦点和文件名 set-value 曾失败；最终使用文件框已有的全新默认文件名保存，没有把失败输入称为成功。`r203`／`r206` 的 Escape 返回 `windowNotFound`，通过依据仅为后续实际 `pressKey` 成功与读图结果。所有原始 RPC、错误和旧 GO 均保留。

## 证据索引与验证

- `SOURCE-GO.json`、`source-snapshot.json`、`source-snapshot.zip`、`source-snapshot/`：授权提交及逐文件摘要。
- `Diagnostic.cpp`、`Inspect.cpp`、本地 `CMakeLists.txt`、`build-exit*.json`、配置／构建日志：隔离宿主与构建回执；初次 HEAD 检查及 Qt package 作用域配置失败记录保留。
- `GO-original.json`、`GO-continuation1.json`、`GO-before-reopen.json`、`GO.json`：原时段、延长和追加现场安排。
- `rpc/*-raw.json`、`*-receipt.json`、原 PNG：原始操作、窗口及图片 SHA；共 24 张原 PNG，全部与 receipt 匹配且有成功读图回执。
- `runtime/*-held.json`、`*-exit.json`、`*-state.json`／JSONL、stdout／stderr：两个创建者的原 Popen 身份、真实 wait 和辅助状态。
- `session-audit.json`、`final-audit.json`、`audit_finish.py`：同会话模型／high 记录、源码与输入输出摘要、image 回执事件索引。初次离线字节比对误将新增记录放在文件尾，假设错误的结果保留为 `final-audit-attempt1.json`；改为实际规范的 `ENDPCB` 前插入后重新核对。

父集成 Debug／Release 的配置、构建、CTest 均真实退出 0，各 23/23；回执位于父树 `.local-analysis/save-roundtrip-wave/checks-debug-1.json`、`checks-release-1.json` 及同名日志。本任务的 GUI 通过依据是上表真实交互与读图，不以自动化测试替代现场。此次仅提交本文档，原 PNG、原软件、诊断产物和本地证据不入库。
