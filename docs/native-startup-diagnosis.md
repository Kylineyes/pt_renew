# 原 AUTOTRAX 启动与输入定向诊断

本轮取得直接证据：**宿主窗口黑底白横线时，DOSBox 客体已经显示可辨板图；一次公开启动 Enter 后，日志也实际新增了 `SYN1.PCB` 打开记录。** 因而不能再由宿主图未变化推断本实例的客体没有推进。本轮没有修复可预测的宿主呈现，没有进入 File／Information／Status 核对文件名和计数，也没有取得原软件新建单线、保存或重开的样例。FT 六／七字段、附加值、换行和布局默认值仍未知。

本轮从 `dev=0655a004a2772e3624f73eb9cb3341ded0f7ef74` 的独立分支 `research/native-startup-diagnosis` 开始。当前 Pi 会话为 `01a19f6a-a52d-7333-95f3-2972829f4e9f`；环境、实际 assistant model／thinking 事件及成功工具事件均核对为 `deng/gpt-6.1-sol high`。工作期间用户将统一协调与验收交回 main-2，本会话按新指令收敛为启动／输入诊断，只新增本文和本树忽略证据，不派发代理、不改产品、不合并或推送 dev。没有复用旧 Task／Dispatch，也没有对失败的临时派发发送 worker_done。

## 先只读比较的结果

证据根记为 E：

`C:/Users/rikideng/orca/workspaces/pt_renew/native-startup-diagnosis/.local-analysis/native-startup-diagnosis/`

| 比较来源 | 本机绝对路径 |
| --- | --- |
| 旧可辨启动页／菜单现场 | `C:/Users/rikideng/orca/workspaces/pt_renew/feat-pcb-layout-boundaries/.local-analysis/native-ft-sample/` |
| 最新 OpenGL 重试 | `C:/Users/rikideng/orca/workspaces/pt_renew/verify-native-menu-calibration/.local-analysis/native-created-retry/` |
| 最新 surface 重试 | 同上路径下 `surface/` |
| 上轮父审计与退出记录 | `C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/save-roundtrip-wave/` |

本轮先完整阅读交接入口、最终状态和旧工作树归档通知，再读取上述配置、stdout／stderr、独立日志、控制脚本及挂载路径。没有修改归档联接或历史证据。旧现场来源详见[旧可辨核验](native-ft-sample-verification.md)，最新失败事实见[Return 与 surface 重试](native-created-retry.md)。

`E/comparison.json` 程序化确认：

- 将各自绝对证据根替换为同一占位后，旧可辨现场与最新 OpenGL 的配置全文相同；surface 配置仅多出 `opengl → surface` 的输出差异。
- 旧可辨与最新 OpenGL 的运行副本均为99文件，完整相对路径、大小、SHA-256相同。两者均只在新副本移除 `TRAXEDIT.DFT`、加入冻结 `SYN1.PCB`；C／D挂载各自 runtime，客体进入 `C:\PT` 后执行 `pt SYN1.PCB`，没有挂载原安装。
- 旧日志与两次失败日志都推进至 `GRAPH.DRV`、640×480、`TRAXEDIT.KEY`、`TRAXEDIT.PAD`。旧轮后续出现 `SYN1.PCB` 打开记录，最新两次重试没有该记录。
- 控制路径存在差异：旧轮使用 Windows-MCP 公开 `Shortcut`，最新两次重试使用 Orca 公开 `press-key`，其回执为 `synthetic_input/unverified`。旧启动器继承环境；最新 owner 还移除 `QT_QPA_PLATFORM`、设置 Qt 缩放和 PATH。这些差异不能直接当作因果结论。

可验证假设为：**启动等待和宿主呈现需要分开诊断；宿主图不变可能掩盖客体推进，公开输入请求成功也不足以证明推进。** 首个最小试验保持旧 OpenGL 配置、同一输入与模拟器，复用旧成功的公开输入路径，使用实际文件打开日志和 DOSBox 自身客体截图作为额外观察。没有原样重复上一轮 Return／surface 组合，没有从通用控制框架重新开发，也没有做纯二进制逆向或替换指定 GLM。

## OpenGL 槽：客体画面与宿主呈现分离

本槽使用 E 下的新 runtime，复用既有 `desktop_session.py`，仅适配当前独立会话计划和至少七分钟收尾。驱动冻结后未热改；目标由原创建者持续持有 Popen／HANDLE。每次动作前检查公开控制门和精确窗口／稳定前景，动作后实际读取原图。窗口截取与全桌面截取的范围记录均保留。

北京时间预告窗口为 **2026-11-03 11:23–12:08**，12:01起只收尾。实际只启动一个新控制服务和一个 DOSBox 目标；原安装 `D:/project/pt_renew/pt` 只读，未被挂载。

1. 新目标宿主首图为黑底白横线。
2. 精确前景下只发送一次公开 `Shortcut enter`，宿主后图仍相同，两个662×566 PNG的 SHA-256均为 `f102ec6ad53b460feb3cf9ecbd98577cc7c75838f9cebf56e5c99723b0479b6f`。
3. 独立日志新增两行：计数 `882485906` 的 `file open command 2 file SYN1.PCB`，随后 `882631081` 的 `file open command 0 file SYN1.PCB`。这是输入后客体状态推进的实际日志证据，不只是主机 API 成功回执；打开请求本身仍不能代替 GUI 文件名／计数确认。
4. 根据实际读到的宿主 Capture 菜单，点击 **Take screenshot**。DOSBox 保存 `E/captures/pt_000.png`；本模型实际读取该原图，看到红色板图外框、内部水平线、十字光标，以及底部黄色状态栏。底栏可辨 `X:2000 Y:2000 mils`、`L:Top Layer`、`P:ROUND62`、`T:12 S:60 G:25`。这些值只是当时状态，不是新建走线参数或文件计数验收。
5. 同步宿主截图仍显示黑底白横线。这一对照足以证明本实例存在客体图像与宿主呈现不一致；不能泛化为历史每次失败都具有相同客体状态，也尚未定位到具体显卡、SDL、窗口刷新或输入实现。
6. 根据实际宿主 Video 菜单选择 **Reset window size** 后，宿主图仍黑线，不能称已恢复显示。

客体原图为 **640×480、2371字节**，SHA-256：

`d35bb9242f15c58478c39ac21e252bb613c9a45e1e8fc5ab7420ca1db8a24cf5`

本模型另只读检查了旧公开 Shortcut 的实现：其调用 `uia.SendKeys`；命名键与普通字符可能走不同发送分支。这能说明主机输入接口存在不同路径，不能据此认定旧轮 f／i 失败或 Orca Return 未推进的根因。本轮没有修改第三方输入实现，也没有在门拒绝后切换接口绕过。

本槽后续诊断请求发生我方 PowerShell 向 Python 传 JSON 时的引号错误，驱动在 **11:38:20** 记录 `JSONDecodeError`，没有执行该请求；随后按原驱动完成120秒零桌面请求，11:40:21控制服务原 wait0。原目标 Popen仍由创建者持有；11:45按本轮记录的PID、创建时间和HWND再次核对后正常 `CloseMainWindow`，原创建者 **11:45:23.975259** 真实 `wait_return=0`。没有恢复或关闭历史PID，没有强杀，也没有把窗口消失或runner标记当作目标退出码。

## 第二槽：请求 Direct3D 未恢复宿主显示

基于首槽已得到的客体／宿主分离证据，第二槽从原安装重新复制到 `E/direct3d/runtime/pt`。除隔离路径外，配置只将 `output=opengl` 改成 `output=direct3d`；沿用同一公开控制路径、输入、机器、CPU和周期设置。

北京时间预告窗口为 **11:48–12:33**，**12:26起只收尾**。实际首服务启动11:49，目标11:52启动。本轮只记录**配置请求 Direct3D**；stdout／stderr和现有日志没有足够的实际后端初始化证据，不能宣称 Direct3D 已生效，亦不能将两槽提升为严格证明实际后端差异的实验。

- 首图与显式精确 App 聚焦后仍为黑底白线。
- 单次公开 `Shortcut enter` 后，日志在计数 `288610754`／`288748325` 记录 `SYN1.PCB` 的command2／command0打开请求，宿主仍黑线。
- 已实际读取 Capture 菜单，并选择 **Take screenshot**；该槽 `captures/` 最终为空，未取得客体 PNG。菜单选择和控制回执不等于捕获成功；未定位未生成原因，没有伪造第二槽客体对照。
- 没有继续盲按菜单、编辑或保存。12:22:48按实际读图确认的位置点击本轮宿主 X，关闭后原图确认窗口消失；**12:27:40.162120** 原创建者真实wait0。12:30:45投递 Stop，控制服务 **12:30:45.978014** 原wait0，runner随后完成，早于12:33截止。12:26之后只有既定收尾，没有业务输入或新槽。

## 生命周期、完整摘要与图像验收

| 槽 | 目标身份 | 目标原wait | 控制服务原wait |
| --- | --- | --- | --- |
| OpenGL | PID25640，FILETIME `134381498355484606`，HWND1770276，Popen identity2698015513552，HANDLE576 | 11:45:23，0 | PID10416，11:40:21，0 |
| 请求Direct3D | PID63896，FILETIME `134381515545204413`，HWND528150，Popen identity2355555802704，HANDLE480 | 12:27:40，0 | PID32992，12:30:45，0 |

精确进程身份、完整argv、映像／配置／输入摘要、原句柄和退出记录均在各槽 `step-002-launch-isolated-created.json`、binding、原exit文件中。FILETIME按Python整数或原JSON保存，不用JavaScript Number重新构造身份。两目标和两控制服务全部正常结束；没有将原owner的完成标记冒称owner自身操作系统退出码。桌面已交回main-2协调，后续不再启动窗口、控制服务、截图或输入。

`python .local-analysis/native-startup-diagnosis/audit_after.py` 本轮退出0，结果在 `E/audit-final.json`：

- 原安装每槽前后99项，运行副本每槽99项，冻结输入每槽1项；完整路径集合、大小、SHA-256全部一致。新副本复制原件后的摘要也先确认一致。
- 冻结输入180字节，SHA-256 `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`；两个新 `NEWFT.PCB` 均不存在。
- 首槽7张宿主PNG＋1张客体PNG，第二槽7张宿主PNG，共15张。当前指定模型均实际读取；审计保存原entryId、toolCallId、时间、图像尺寸及解码摘要。本轮所有回执图像字节均与对应保存PNG匹配。全桌面PNG本身为公开Snapshot返回的1920×1080图，不把它们宣称为3840×2160未经缩放的物理屏幕原图；菜单点击使用另存的DPI感知窗口／虚拟桌面范围核对。
- 两槽目标身份与其原Popen退出记录一致，原wait均0；两控制服务原wait均0，冻结driver摘要未变。

main-2也已独立复核上述集合、15图image字节回执及四个原wait，父证据位于：

`C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/parallel-development-20261103/parent-native-audit.json`

本轮验证对象为配置、日志、真实桌面、客体捕获及只读摘要；仅新增诊断文档，不重跑Qt构建／CTest，不把历史Debug／Release各23/23写成本轮运行结果。

## 明确保留的阻塞与后续最小方向

本轮已将“输入没有推进”与“显示没有更新”分离：公开命名Enter路径在新实例中有客体文件打开证据，首槽还具有正常客体图像。宿主呈现仍不可靠；窗口尺寸重置和请求更换输出均未取得恢复，实际后端状态也需要进一步明确。配置继承、有效配置值、视频模式切换后宿主输出刷新、不同公开输入实现及字符键路径仍各有未证部分，不归因到单一组件。

下一项诊断应优先保留可稳定取得的客体Capture及其原图回执，用最少公开动作确认可辨菜单／文件名／计数；第二槽Capture未生成须先解释，不能用黑图预排业务。是否安排新现场由main-2协调，沿用同Pi会话与新正式Task，不重复已经失败的无观察Return／surface组合，不重建通用控制框架。

空板确认、明确层／宽／端点的新单线、全新8.3文件保存、原软件重开和FT字段／换行／排序证据均未完成。`trackPlacementUserEntryAvailable()`仍应保持false，默认保存继续拒绝Created，新增NETDEF继续拒绝；本轮没有产品修改，也没有开放任何入口。
