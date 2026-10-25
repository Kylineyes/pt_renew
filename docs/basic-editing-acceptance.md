# 基础编辑0.11.0独立GUI验收：启动前门禁阻塞

日期：2026-10-26。本任务使用当前Pi会话，实际环境核对为 `PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`；验收分支为 `Kylineyes/verify-text-screen-sol`，起点为 `2435a3533c4baf448364eb1180df763b1c4ed578`。任务 `task_89e4937f7bc2`、Dispatch `ctx_4b72417a1ce3`，本轮唯一桌面/截图负责人未启动其他代理。

**结果为failed：独立GUI验收在产品启动前被公开控制门禁阻塞，全部产品现场交互项未验证。** 新建连接的ControlStatus在30秒内连续16次返回user，未取得ready/ai；本轮没有启动候选、没有产品PID/HWND、没有截图、没有发送键鼠或恢复焦点。没有把开发方offscreen测试通过写成真实桌面通过，也没有据此宣称0.11.0发布验收完成。

## 最终候选及开发验证资料

验收前完整阅读开发工作区 `docs/basic-editing.md`、最终 `validation.json`、Debug/Release CTest日志与部署烟雾记录。父代理通过本任务问答明确确认以下最终候选，未采用未确认的后续构建：

| 项目 | 确认值 |
| --- | --- |
| 开发提交 | `b0e5ac7761f13690b5310bbc913ab7bfd2691d08` |
| 开发分支 | `Kylineyes/feat-basic-editing`，检查时干净 |
| 开发报告绝对路径 | `C:/Users/rikideng/orca/workspaces/pt_renew/feat-basic-editing/docs/basic-editing.md` |
| 部署EXE绝对路径 | `C:/Users/rikideng/orca/workspaces/pt_renew/feat-basic-editing/.local-analysis/basic-editing/release-candidate/pt-renew.exe` |
| EXE SHA-256，本轮独立读取确认 | `dcf310949526eb2f9f5af4e6b0f28df8095b12a5f621733c9d964fc96e8f0fe8` |
| 部署目录文件数 | 23，包含 `platforms/qwindows.dll` |
| 开发方最终Debug/Release CTest | 各11/11组通过；本轮已阅读日志，没有重新执行 |
| 开发方最终QtTest/Python | 每配置270项QtTest、30项Python通过；Qt交互使用offscreen |
| 开发方部署烟雾 | 仅系统PATH、offscreen执行 `--version` 得到 `pt-renew 0.11.0`，退出0；本轮未重跑 |

开发自动验证及部署命令行记录属于已交付证据；本轮只做只读复核与文件摘要绑定。`qwindows.dll`存在也不能替代实际Windows桌面依赖加载与交互验收。

## 真实GUI验收逐项状态

| 要求 | 状态 | 本轮实际执行边界 |
| --- | --- | --- |
| 在移除Qt SDK/VS PATH及offscreen变量的子进程中启动部署包、确认中文界面和0.11.0 | 未验证，门禁阻塞 | 仅离线记录启动计划；没有执行Popen或命令行版本检查，没有产品PID |
| 自由走线菜单移动ΔX/ΔY，端点/长度/来源字段及画面正确 | 未验证 | 候选及合成输入已确认，未打开画布 |
| 取消、零位移、非法值不修改或增加历史 | 未验证 | 没有打开移动对话框 |
| 删除、撤销、重做、多步回干净点；菜单及画布快捷键一致 | 未验证 | 没有发送Delete、Ctrl+Z/Ctrl+Y或菜单命令 |
| 元件内部走线、非走线、隐藏层不能误编辑 | 未验证 | 没有执行选择、显隐或编辑操作 |
| 测量、捕捉、选择与PrimitiveId在编辑/Undo/Redo后清理或更新 | 未验证 | 没有创建测量/捕捉状态或编辑修订 |
| 受限铜层旧结论清理，外部NET保留并可重新分析 | 未验证 | 没有加载NET或启动分析 |
| 原输入SHA-256与未保存工作副本、标题/信息区区分 | 未验证 | 没有实际显示信息区或修改工作副本 |
| 关闭文件、换图、退出及窗口关闭的放弃/取消保护 | 未验证 | 没有启动产品或触发关闭；无更改需要放弃 |
| 失败载入保留当前工作副本与历史 | 未验证 | 没有执行载入 |
| 保存/另存为明确未实现且不伪造成功 | 未验证 | 文档说明了限制，未从界面确认 |
| 文本焦点下Delete/Ctrl+Z仅影响文本 | 未验证 | 没有打开搜索框/数值对话框 |
| 合成LIB预览保持只读且不误改主板 | 未验证 | 没有加载LIB |
| 系统会话结束保护 | 未验证 | 本轮未触发宿主注销或关机；后续应另安排受控环境，不能影响共享桌面 |
| 新证据目录、候选/输入摘要及清理核对 | 通过 | 仅离线操作和只读门禁探测，见下节 |

此结果没有定位或确认任何基础编辑产品缺陷；目前阻塞来自桌面控制条件。实现正确性仍需后续独立现场验收，不能以本轮未执行为产品功能失败。

## 本轮桌面检查与停止边界

本轮证据根目录E为：

```text
C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance/
```

本轮没有沿用历史任务的连接；实际开始时间为2026-10-26 **00:58:19（北京时间）**，以状态文件为准。首先只读Win32观察得到前景HWND3477956/PID36428，属于普通应用；LockApp存在但非前景，没有发现pt-renew或DOSBox残留。该事实不等于公开控制门禁已允许输入。

随后在本轮新证据目录启动一个只读Windows-MCP探测客户端，仅调用ControlStatus，不调用Snapshot、App、Click、Shortcut或任何产品启动入口。16份结构化返回从 `control-00.json` 至 `control-15.json` 均为user、generation2；30秒期限结束时wait_seconds仍为约9.9999673。脚本写 `input-stopped.json` 后退出，没有重连、改门禁、切换工具或排入捕获命令。持续user不能识别输入来源，本轮不推断是否有人操作鼠标或设备产生事件。

外层PowerShell调用返回码1，其标准错误记录包含MCP启动/弃用提示及PowerShell NativeCommandError；16份结构化ControlStatus和停止文件均有效保留。停止结论依据明确的门禁状态，**不是候选程序启动失败**，候选根本未启动。原始标准错误保留为UTF-16文件，并另有只供阅读的UTF-8派生文本。

本轮没有产品截图，所以不存在可列举的有效截图绝对路径；不会引用其他任务截图冒充本候选证据。未运行任何后置capture，未发生上一任务的门禁后预排点击问题。

## 离线输入保护与后续启动计划

只读核对最终部署包的23文件集合及SHA-256；按开发方manifest逐项核对6份合成PCB/NET/LIB，然后完整复制inputs到本工作区E下，含manifest共7文件。只使用合成材料，没有读取或操作唯一原板图、原库或原软件安装。

| 输入集合 | 前后文件数 | SHA-256结论 |
| --- | ---: | --- |
| 开发方最终release-candidate | 23 / 23 | 集合及逐文件摘要相同 |
| 开发方inputs（六份材料及manifest） | 7 / 7 | 集合及逐文件摘要相同；六项均与manifest匹配 |
| 本轮安全输入副本 `E/inputs/` | 7 / 7 | 与来源相同，前后不变 |

开发文档规定的自由走线移动案例预期为 `(100,100)→(400,500)` 在ΔX=100、ΔY=−50后变为 `(200,50)→(500,450)`；这只是后续验收判据，本轮没有观察或验证该结果。

`launch-plan.json` 记录最终EXE及副本supported.pcb参数，计划子进程PATH只保留Windows系统目录，并移除QT_QPA_PLATFORM、QT_PLUGIN_PATH、QT_QPA_PLATFORM_PLUGIN_PATH、QML2_IMPORT_PATH、QTDIR及SDK/VS环境；部署自带qwindows用于未来真实窗口。计划明确 `executed=false`、`target_pid=null`，本轮没有修改当前环境或执行该计划。以后必须使用新Task/Dispatch、重新只读确认门禁明确恢复允许状态，再依既定失败即停止保护逐步验收，不能在本轮提前尝试。

## 证据绝对路径与收尾

关键证据均在本轮忽略目录，不提交候选EXE、DLL、合成副本、截图、日志或原始分析材料：

- 总汇：`C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/basic-editing-acceptance/verification-summary.json`。
- 初始桌面：同目录 `native-initial.json`；原生前景检查没有发送输入。
- 逐次门禁：同目录 `control-00.json` 至 `control-15.json`，停止文件 `input-stopped.json`。
- 候选前后摘要：同目录 `candidate-before.json`、`candidate-after.json`。
- 开发输入前后摘要：同目录 `source-inputs-before.json`、`source-inputs-after.json`；本轮副本前后为 `inputs-before.json`、`inputs-after.json`。
- 开发报告和测试日志摘要：同目录 `development-evidence.json`；完整引用保留开发工作区绝对路径。
- 最终进程：同目录 `processes-final-confirmed.json`，按探测客户端实际PID及父子关系核对，无匹配进程；早期宽泛查询 `processes-final.json` 包含查询自身PowerShell，未据此终止任何进程。
- 完整证据索引：同目录 `evidence-index.json`，包含绝对路径与SHA-256；状态 `worker-status.json` 记录模型、结果、完成时间、提交及清理核对。

本轮没有启动产品，因而没有产品进程可清理，也没有调用Stop-Process。只读探测客户端和其MCP子进程已退出。最终候选和安全输入均未变化，文档执行 `git diff --check`；没有修改开发源码、旧验收报告、dev/main或根交接文件，仅提交本文，由父工作区集成并汇报GUI验收仍受阻。
