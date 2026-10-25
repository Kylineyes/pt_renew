# 基础编辑0.11.0真实GUI重新验收

日期：2026-10-26。使用原Pi会话，实际环境核对为 `deng/gpt-6.1-sol`、`PI_REASONING_LEVEL=high`，分支 `Kylineyes/verify-text-screen-sol`。任务为 `task_f5b3e12641b4` / `ctx_63d363c1c987`；服务超时/连接失败后的恢复仍沿用同一Task、同一会话，没有创建新代理或更换模型。

**结果为failed：本轮已实际启动固定部署候选，确认中文窗口、原输入/工作副本信息、自由走线原始属性，以及移动菜单和数值对话框；实际编辑前的恢复连接连续60秒门禁为user，移动、撤销重做及后续常规交互均未完成。** 本轮没有确认产品缺陷，也没有完成0.11.0发布GUI验收。系统会话结束保护继续作为受控环境未验证项，未在共享宿主注销/关机。

## 固定候选和实际启动

| 项目 | 实际记录 |
| --- | --- |
| 开发提交 | `b0e5ac7761f13690b5310bbc913ab7bfd2691d08`，本轮未更换 |
| EXE绝对路径 | `C:/Users/rikideng/orca/workspaces/pt_renew/feat-basic-editing/.local-analysis/basic-editing/release-candidate/pt-renew.exe` |
| EXE SHA-256，本轮前后均匹配 | `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8` |
| 部署包 | 23文件，包含 `platforms/qwindows.dll` |
| 实际目标 | PID **35888**，主窗口HWND **7932040**，session3，原生类 `Qt6120QWindowIcon` |
| 实际启动参数 | 上述部署EXE及本轮安全副本 `inputs/supported.pcb`；cwd为候选部署目录 |
| 子进程PATH | `C:\WINDOWS\System32;C:\WINDOWS;C:\WINDOWS\System32\Wbem` |
| Qt/SDK/VS环境 | 启动代码删除所有QT/QML/VS/VC/INCLUDE/LIB相关变量及SDK变量；实际父环境无匹配项，记录removed列表为空；没有offscreen变量 |
| 实际窗口 | “supported.pcb · 工作副本 · 不支持保存 · PT Renew”，可见、可最大化和实际选择图元，非offscreen |
| 标准流 | 本轮目标stdout/stderr均为空；真实窗口及交互为启动依据，未以空日志判定失败 |

完整阅读本轮任务文件、开发 `docs/basic-editing.md`、旧阻塞报告及父工作区最新PROGRESS。开发和父工作区已有Debug/Release各11/11 CTest、每配置270 QtTest及30 Python通过；本轮不重复未变化的自动测试，也不将这些自动结果替代现场交互。0.11.0版本绑定来自固定候选及开发版本记录，**本轮没有打开界面内版本对话框再次读取版本号**。

## 逐项验收

| 验收内容 | 结果 | 实际证据与边界 |
| --- | --- | --- |
| 仅系统PATH的真实部署启动、中文界面 | 通过 | 原生进程/窗口、5张有效产品截图、最大化及选择有真实响应 |
| 工作副本、不支持保存及近似/非生产输出说明 | 通过，文案观察 | 标题、画布顶部、信息区和移动框均有相应限制；不等同保存菜单已测试 |
| 原输入SHA与当前工作副本/修订/统计区分 | 通过初始状态 | 信息区明确“原输入（始终只读）”“当前工作副本：未修改”、修订2、当前5图元/走线3，源204字节及SHA独立列出 |
| 自由走线选择及原始属性 | 通过 | 属性实际显示(100,100)→(400,500)、宽10mil、长500mil、顶层铜、自由图元、源文件行2 |
| 菜单移动入口与对话框 | 通过入口观察 | “移动所选自由走线”启用；打开整数ΔX/ΔY、仅内存、不支持保存的对话框，初始0/0 |
| ΔX=100/ΔY=−50的实际移动和500mil保持 | 未验证，门禁阻塞 | 没有输入/提交数值；(200,50)→(500,450)仍为预期判据，未观察 |
| 取消、零位移、小数/非法值/越界不修改历史 | 未验证 | 请求输入1.5时Type工具缺loc参数被校验拒绝；未送入应用，不能算产品拒绝小数通过 |
| 文本焦点Delete/Ctrl+Z不误编辑主板 | 未验证 | 数值框显示过，但没有发送相关文本快捷键 |
| 删除、Undo/Redo、多步回干净点、redo分支失效 | 未验证 | 没有实际编辑或发送这些快捷键 |
| 菜单和画布快捷键共用编辑功能 | 未验证 | 只实际打开菜单；没有完成画布快捷键编辑 |
| 元件内部走线、非走线、隐藏层和LIB保持只读 | 未验证 | 初始画面可见元件内部短线、焊盘和底层自由线，但没有逐项选择/误编辑测试 |
| 编辑/Undo/Redo后测量、捕捉、选择及分析失效 | 未验证 | 没有建立前置状态或编辑修订 |
| 外部NET保留/映射、受限铜层结论清理/重算/迟到结果 | 未验证 | 没有加载NET或启动铜层分析 |
| 视图和层显隐保持、显式视图重置 | 未验证 | 最大化窗口不等于编辑后视图保持或重置测试 |
| 关闭文件、换图、菜单退出、窗口关闭的取消/放弃保护 | 未验证 | 最终通过核对进程后的清理结束，没有把终止进程当正常关闭保护验收 |
| 失败读取保留当前工作和历史 | 未验证 | 未执行失败读取 |
| 保存/另存为菜单明确禁用 | 未验证 | 文案观察通过，未展开文件菜单核对动作状态 |
| 系统会话结束保护 | 未验证，受控环境限制 | 未影响共享宿主，不触发注销/关机 |
| 候选、来源合成输入及副本前后摘要；清理 | 通过 | 23/7/7文件集合及SHA-256一致；仅清理本任务目标，各客户端退出 |

任务失败表示本轮常规GUI范围未完成，不是“移动失败”或“Undo存在缺陷”。没有对未执行功能作产品通过/失败判断。

## 实际执行、工具修正与停止条件

本轮证据根目录E为：

```text
C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance-retry/
```

最初服务连接错误耗尽重试时没有工具成果；用户要求从断点恢复后，02:58:36核对模型，完整读取任务并创建E。只读Win32核对桌面、锁屏和残留进程，没有pt-renew/DOSBox残留；LockApp进程存在但非前景，未据此宣称锁屏。本轮新MCP连接首次ControlStatus明确ready/generation1；复制合成输入及核验固定候选后，仍经同一连接检查状态，于03:00:29启动上述候选。

启动后首次Snapshot捕获的是其他应用前景，虽然任务栏已有pt-renew，也**不能作为产品画面证据**。随后只读枚举得到本轮目标PID/HWND和真实标题。按完整标题调用App switch返回Application not found，此次门禁为ready/generation3；停止标记和完整错误保留，客户端退出。此为验收工具窗口匹配失败，不是产品窗口不存在或产品缺陷。

父代理通过本Task明确允许保留停止记录后在 `recovery-01/` 修正工具使用。先核对旧客户端已退出，新连接重新取得允许状态，再使用公开Orca按PID/HWND的restore。该restore截图仍为其他应用，不能当作成功恢复前景；随后同一连接 `App switch("PT Renew")` 成功取得真实窗口。原生前景及后续每个Click的PID/HWND均受本任务校验；没有因App返回成功就跳过截图判断。

随后实际最大化窗口，点击自由走线中段。属性读数和图像一致显示500mil走线及自由来源。点击顶部移动菜单后，“移动所选自由走线”可用；再点击该动作打开“移动所选自由走线（仅内存）”框。对话框说明ΔX向右为正、ΔY向上为正，位移范围±2000000、端点范围±1000000mil，并提示不支持保存。

首次Type试图输入1.5，但没有传工具要求的loc或label，工具直接返回 **Either loc or label must be provided**。门禁仍为ready/generation17，**该数值没有进入产品**；脚本按失败即停止退出，未预排下一次点击。原schema、参数及完整错误保存，属于验收工具使用错误，不是产品的输入拒绝行为。

按父代理此前允许的参数修正流程，确认 `recovery-01` 客户端退出后，在 `recovery-02/` 使用当前截图的明确坐标，并降低无需UI树的截图开销；未删除或覆盖旧停止标记。该新连接的首次ControlStatus却连续60秒、31次为user/generation2，首次wait_seconds约9.9996987，最后约9.6131778，没有ready/ai。它在处理任何数值请求前就停止；因此修正后的1.5也没有发送，且没有移动提交或其他键鼠输入。

门禁持续user后，全部GUI链停止，没有重连、换入口、修改第三方包或排入capture。父代理确认按真实阻塞收尾。本轮未重现此前原文字形任务的“失败后组合命令仍继续点击”错误。来源仅能确定为门禁检测到未达允许条件，**无法可靠识别输入来源，不推测人工干扰、设备或其他进程**。

本轮Snapshot明确3840×2160原屏、1920×1080返回图、坐标倍率2.0；实际点击均根据当时有效截图和倍率，最大化前后坐标重新取值。原生Win32矩形受DPI上下文影响，没有直接用于屏幕点击。

## 有效截图绝对路径与摘要

5张有效截图均位于 `recovery-01/`，原始返回图1920×1080；没有用裁剪放大增加测量精度。以下证据只支持各行列明的实际观察：

| 截图绝对路径 | 观察范围 | SHA-256 |
| --- | --- | --- |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance-retry/recovery-01/002-focus-visible-post-00.png` | 首张有效产品窗口及中文限制 | `2333ac63085af856865c91e9de533e3e3cf7675b40c7984d96f2cec56ebcfab7` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance-retry/recovery-01/003-maximize-post-00.png` | 最大化、源SHA和当前工作副本区分 | `a5945b35993f4f03666f6fdcb57cfb1d62f0cf53d1c64a8b126b7c44d5894d21` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance-retry/recovery-01/004-select-free-post-00.png` | 原走线端点/500mil/自由来源 | `bc67fd1748da904d502c1d9cee0c099f3300d88524b07d8afe45c9ab62cecd85` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance-retry/recovery-01/005-move-menu-post-00.png` | 移动所选自由走线入口 | `506746b4601081e8bca6f6d0591ec0b27d543594aa633cd3f73bf29842a6621d` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance-retry/recovery-01/006-move-open-post-00.png` | 仅内存移动数值框及范围文案 | `b4f0546c0aaef4becf6c214aabf9e569457ad2cd54e8d424394fb7d1708a0a63` |

根目录 `001-launch-post-00.png`、`recovery-01/001-focus-exact.png` 和其post图为其他应用前景，明确不采纳为产品证据；绝对路径和摘要在总汇中仍保留，不会删图掩盖失败过程。

总汇绝对路径为 `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance-retry/verification-summary.json`。根 `target.json` 保存实际启动参数、系统PATH、PID和移除变量列表；`native-after-launch.json`保存主窗口身份；各动作另有前后原生观察及门禁返回。`recovery-02/initial-gate-00.json`至`-30.json`和该目录停止标记/完整stderr记录最终阻塞。`evidence-index.json`在最终状态写入后生成，列全部证据绝对路径与SHA-256，排除索引自身及动态状态文件以避免自引用。

## 输入保护与清理

只使用开发方自行合成PCB/NET/LIB，没有读取、运行或修改原安装、原板图、原库或其他用户文件。`supported.pcb`原输入SHA-256为 `cc3bd87d4f9c077b05b8619969114fca493bddba552aa95c1485a764c7de6d30`，与真实界面信息区相符；候选及输入前后核验如下：

| 集合 | 文件数 | 前后摘要 |
| --- | ---: | --- |
| 开发方固定release-candidate | 23 | 集合及每文件SHA-256一致 |
| 来源inputs，含六份合成材料及manifest | 7 | 与manifest和前置摘要一致 |
| E下全新inputs安全副本 | 7 | 与来源及前置摘要一致 |

门禁阻塞后没有尝试通过GUI关闭对话框。清理前通过CIM重新核对PID35888、映像绝对路径和含本轮supported.pcb的完整命令行，只终止该目标；当时未输入数值、未发生产品编辑或保存，不把此清理算作关闭保护验收。初始和两次恢复客户端PID54744、27652、55588及其MCP子进程均已退出，最终 `processes-final.json`匹配集合为空。没有终止未知进程或操作其他应用。

本轮仅提交本文，旧报告、根README/HANDOFF/PROGRESS、产品源码及dev/main均未修改，没有合并或推送。`git diff --check`通过；所有图片、候选包、输入、日志和辅助脚本只留在新忽略目录。后续继续真实验收需要明确恢复允许的控制状态，并从实际移动及剩余清单开展新的受控尝试，不能据本轮有限画面通过0.11.0全部常规GUI范围。
