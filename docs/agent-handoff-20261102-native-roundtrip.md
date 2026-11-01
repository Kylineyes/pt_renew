# PT Renew 新代理交接：2026-11-02 原生另存重开通过后

用户要求验证完成后总结进度和计划，由其安排新 agent。**本轮原生另存、重新打开和正常退出验证已经完成；交接整理后停止新任务。** 不创建 tag、不发布、不操作 main。开发主线继续是编辑与文件往返，原控制工具只作为配套，不重新从控制基础设施开始。

## 接手入口及分支

先读本文件、`AGENTS.md`、[编辑与另存为](pcb-save-as.md)、[原生三步验证](native-save-roundtrip-verification.md)，再根据具体任务读对应源码。实际键鼠及历史缺口见[产品交互报告](product-mouse-keyboard-verification.md)、[原 AUTOTRAX 键鼠报告](pcb-mouse-keyboard-verification.md)；下一编辑阶段设计见[新增自由走线与取消](free-track-creation-design.md)。更早完整实现交接为[2026-10-31 交接](agent-handoff-20261031-save-as.md)。

本轮产品验证基线 `dev=78d3e817d04930d4552105de6be2be6cf81fac1f`，父分支 `verify/native-save-roundtrip`，交接更新 `a5fc62d`，worker 原报告 `8e4703d` 已移植 `30aba11`，no-ff 合并并推送 `e1c859c8ce101fdeed7ead5034ab56fc64cbccd5`。本文件在独立 `docs/handoff-native-roundtrip` 整理，最终 dev／远端 SHA 与干净状态见本机 `.local-analysis/native-save-focus/final-state.json`。新代理先 fetch，再从最新 dev 建立独立工作分支。

main 未变：本地 `3e13f69528cfc033718ef8352b8d3fb7bce915bd`，远端 `3705e56cf12739fc27691cc8d80fda591bf5b73d`。没有新 tag 或发布，已发布 alpha 继续作为只读历史包。开发版版本字符串仍可能相同，按源码与 EXE 摘要识别，不凭版本号猜功能。main 的合并、提交、推送由用户执行。

## 当前产品能力

| 范围 | 已实现 | 边界 |
| --- | --- | --- |
| PCB 查看 | 已支持记录的载入、图层显隐、选择／属性、检索定位、测量及端点捕捉 | 非完整格式；文字和部分轮廓近似 |
| LIB／NET | 只读封装库、引脚映射与受限铜分析 | 非完整 DRC，不放置元件或输出生产文件 |
| 自由走线编辑 | 可见已有自由 FT 的整数 mil 整体移动、删除、撤销、重做 | 元件内部图元和其他图元仍只读；不新增 |
| 新文件写出 | 文件菜单／Ctrl+Shift+S 另存为全新 PCB，不覆盖原件或已有目标 | Ctrl+S 覆盖保存未开放，未知记录载入时拒绝 |
| 字节保留 | 移动只补四坐标，删除只移除对应 FT；其他字节保持 | 附加字段不作电气语义保证 |
| 历史和保护 | 保存点、失败／取消保留、文件框期间修订变化拒绝旧状态 | 不宣称断电、网络盘或系统结束全覆盖 |

核心代码：`src/io/LegacyPcbWriter.*`、`src/application/BoardEditSession.*`、`src/domain/BoardDocument.h`、`src/ui/MainWindow.*`。`sourceBytes` 是载入时冻结的原字节，保存时不会重新读取原件。写出前重解析并比较；目标同目录临时文件写完 flush 后原子改名，不复制回退、不覆盖已有目标，拒绝 Windows 设备名与备用数据流。

另存成功保留原输入身份、摘要和撤销历史，只标当前保存点；主窗可能仍叫 INPUT.PCB，这是当前设计。只有重新打开 SAVED.PCB 才建立新来源文档。不要把 clean 等同重载或清空历史。外部 NET 不写入 PCB，原内嵌 NETDEF 逐字保留。

## 已验证结果与准确范围

产品实现阶段 Debug／Release 的 CTest 各 **12/12 组通过**，写出专项各 40 项；此前真实 QtTest 链接产品 UI 的移动／另存／重开五业务函数一次通过，并由指定 Pi 读取四图。之后 Release 又跑过 12/12。本轮没有源码改动，不重复构建／CTest，不能说这些是本轮新跑。

真实独立产品键鼠已完成鼠标选线、Ctrl+G、M→T、位移输入 `(50,-25)` 并提交、原生另存取消、未保存关闭取消。指定 Pi 实际读取 **20 张**原图，父核对返回 image 解码 SHA、窗口归属及输入文件保护。移动后没有重选端点，也没有保存当时的 dirty 文档，因此不宣称精确坐标与该 dirty 会话往返已验收。已有目标测试停在原生“文件名无效”，未进入产品后端已有目标拒绝路径。

**本次最小原生文件三步通过：**

1. 对已载入的五条 FT 合成样例，经 Windows 原生 `#32770` 另存框写全新 `outputs/SAVED.PCB`。
2. 经原生 Ctrl+O 打开新文件，指定 Pi 实际看图确认 SAVED.PCB 标题、5 图元／5 走线、clean 和已载入状态。
3. Alt+F4 正常关闭，原创建者持有的产品 Popen 返回 **0**；控制服务原 Popen 也返回 **0**。

输入、输出均 **180 字节**，逐字相等，SHA-256 `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`。输入是此前产品核心生成的 `SYN1.PCB` 隔离副本，包含已移动／删除后的模型；本轮没有重新编辑。它证明独立产品原生文件流程，不补称此前未保存移动会话的完整往返、原 AUTOTRAX 重开或干净系统兼容。

成功续接由 Pi `deng/gpt-6.1-sol high` 执行，session `01a19201-b349-7326-873c-dc74757f3daa`。Run `run_ef2220ef26c4`，Task `task_918621be94b6`，成功 Dispatch `ctx_175ea9ba3424`。实际操作 App 1 次、Shortcut 3 次、Type 2 次，8 张原图均由指定 Pi `tools.read`／image 实际查看；首段另有 2 图。父只复核原 JSONL、成功 image SHA、输入 owner／前景和文件字节，不冒称直接看图或持有原 Popen。005／007 含文件框消失透明动画残影，主窗结果可辨，保存事实由实际文件补证。

产品 PID **2844**、创建 FILETIME `134380273510730407`、主 HWND **397486**、原 Popen 对象 `1920102161040`／句柄 **612**，由首段 runner **52372** 持有，**01:56:33.721728（UTC+8）** 返回 **0**。续接服务 PID **4400**、创建 FILETIME `134380285911224280`、原 Popen 对象 `2573319974464`／句柄 **180**，**02:00:14.017178** 返回 **0**。runner-finished 仅证明脚本完成标记，不等同其自身操作系统退出码。本轮产品窗口已关闭。

首段 `ctx_bf1303844706` 因其他终端取得前景，驱动在发送 Ctrl+Shift+S 前拒绝；零产品输入、120 秒静默和服务退出 0 的失败记录保持。成功段使用新冻结 Attach 驱动，先公开 App 聚焦，不恢复旧已停止脚本。唯一成功 done `msg_b66cbda5aef3` 已父审阅接受，ack `delivery_eac54a457a7e`；release 为 `external_terminal retained/processAction=none`，reclaimable 0。原终端闲置，不复用 settled Dispatch。

## 旧残留与未验证边界

之前未保存产品 PID **46856** 的原创建者已在 **2026-11-02 01:04:01.803586** 记录原 Popen 返回 **0**，没有生成旧 SAVED，不推断其未保存修改被恢复或写出；旧文件保护结论保持。

原 AUTOTRAX 输入尝试只确认 Click／Enter 实际发送，客体黑底白线，未取得工作文件名、计数或几何属性。DOSBox PID51276 后续宿主 X 正常关闭，原 Popen 返回 0；更早 PID11096 原 Popen 返回非零 `1853227067`。正常关闭宿主不等于原软件业务兼容。原字形 runtime=false、异步 ready_for_live=false、旧竞争次数与时限等全部保持，不因本次保存通过改写。

指定 `glm-5.3 high` 的 FT 新建默认字段纯静态任务曾因 quota hard fail，零工具调用，没有更换模型或形成新格式结论。不要把已有第七字段值 1、可读取六字段或本次字节保留当新建默认编码的依据。

## 后续计划

建议新代理按产品目标选择一个明确任务，避免重新跑已经通过的纯文件流程：

1. **补 dirty 编辑到原生文件的单次完整往返。** 新隔离样例，鼠标选自由线、移动或删除一次，确认 dirty，经原生框保存全新文件、重开、核对精确属性和未改字节、正常退出。正确使用计划 JSON 中的 Windows 反斜杠路径；保存和重开主流程优先，不夹带可选测试耗尽收尾时间。
2. **原软件兼容性单独安排。** 先解决黑底白线或客体启动条件，取得可辨启动／菜单后，核对源与输出工作文件名、走线数、修改及未改对象。不从 Qt 自重开推导原软件通过，不循环旧失败演练追结果。
3. **推进新增自由走线。** 按设计先核定原程序新 FT 的字段及默认值，再实现原记录／新建记录身份、Undo／Redo、预览取消和合法插入边界。当前 writer 明确拒绝新增，不简单放宽校验；NETDEF 交错、DOS EOF、混合换行和关键词标签必须有明确规则。

如用户优先开发，也可先做身份和核心新增历史的内部实现，但不能提前开放用户可保存的新建能力或宣称布局／布线／DRC 已实现。GUI 变化须按项目规定实际启动交互核验，截图始终交指定 Pi 模型；纯逆向仍按指定 GLM 模型，不可用如实报告。

## 本机证据与保护

- 父 `.local-analysis/native-save-roundtrip/`：新隔离准备、源码／依赖核对、首段失败审计及原会话前缀。
- 父 `.local-analysis/native-save-focus/`：Attach 驱动准备、原图回执／owner／文件／原 Popen 父审计、`session-prefix.jsonl`、最终 Git 与 Task 状态 `final-state.json`、旧入口备份。
- worker `../verify-product-mouse-keyboard/.local-analysis/native-save-roundtrip/`：唯一新产品的 bin、inputs、outputs/SAVED、原创建者、首段2图和失败／退出原记录。
- worker 同树 `.local-analysis/native-save-focus/`：8图、公开输入回执、原服务、WaitOriginalExit、worker-final-audit。
- `.local-analysis/CURRENT_AGENT_HANDOFF.md` 已更新，可直接发送提示词见父 `.local-analysis/native-save-focus/NEW_AGENT_PROMPT.txt`。

原软件安装、板库、SDK、截图、二进制、构建与逆向数据库都不提交。原安装 `D:/project/pt_renew/pt` 只读；测试用新隔离副本并保存前后摘要。历史工作区可能已归档为目录联接，先读 `.local-analysis/WORKTREE_CLEANUP_NOTICE.md`，不把归档当活 Git 工作树。

后续每项开发从最新 dev 建独立分支，验证后按项目规范 no-ff 合 dev 并推送；main 仍由用户操作。必要键鼠授权已存在，但新现场仍须明确具体时间、窗口／进程范围与预算；公开控制门拒绝时保留真实结果，不改第三方门禁或强杀不明进程。
