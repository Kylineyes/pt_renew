# 主窗显式新增另存与保存点集成

本轮从 `dev=fbbc572` 继续，将既有显式新增 writer 接入主窗保存收尾。`MainWindow::saveAsFileWithCreated(path, options, error)` 要求调用者明确提供编码选项，成功发布后才标记历史保存点并显示最近输出信息。**普通产品新增入口仍关闭，原 AUTOTRAX 默认字段仍未核定。**

## 实现与验证

[主窗显式保存说明](mainwindow-created-save.md)记录接口及边界。显式和默认入口共享 `saveAsFileImpl`，统一校验主窗来源、库和载入状态，复用原 writer 的发布保护，不复制文件写出逻辑。另存取消尚未提交的走线预览，保留既有选择和测量；失败保留当前文档、修订、历史、dirty 及上次成功输出信息。

原生文件框返回后新增文档、原输入指针及载入代次检查，避免载入请求虽然失败、修订未改变时仍发布陈旧路径选择。原保存点语义保持：另存不重绑输入、清空历史或改变 Created 内存身份，撤销离开保存点 dirty、重做返回保存点 clean，截断分支不会错误恢复 clean。

本轮有三路独立任务，源代码／静态报告／原软件现场各使用独立分支与工作树。复用既有 Pi 会话，指定模型和 high；没有因模型不可用替换模型。MainWindow 两文件、新专项及说明由 UI worker 所有；共享 CMake 和跨模块工作流由协调者修改。原软件与真实 GUI 的桌面权按时段串行交接。

| 任务 | 结果与依据 |
| --- | --- |
| 主窗显式保存开发 | `feat/mainwindow-explicit-save` 提交 `8a4c390`；新增主窗专项31项，既有Writing40／走线UI13／Library26／原工作流5项均实际wait0。独立harness初次缺少相邻检查工具的失败保留，部署修正后通过，未修改旧测试。 |
| 原软件Return及渲染对照 | `verify/native-created-retry` 提交 `e607ad8`；两个新隔离实例各实际请求一次Return，但未取得可辨AUTOTRAX业务及单线样例，Task failed。 |
| 启动／FT静态逆向 | `glm/glm-5.3 high` 配额失败，自动重试后终止，零工具调用、零结论；协调者按证据abandon并将Task标failed，不重派、不换模型。 |
| 原生新增保存与重开验收 | 同UI Pi会话独立Task，指定核心范围 succeeded；原生另存、保存点Undo/Redo、输出真实重开、隐藏目标层与菜单Escape取消通过，报告提交 `94a4c8d`，详见[真实窗口报告](mainwindow-created-save-live.md)。 |

正式产品源码及测试冻结为 `64e36d8e634f517fa86cb4b0266ace52911c5b56`。Debug／Release 配置、全量构建和 CTest 原创建者真实 wait 均为0，CTest各 **23/23组通过**。Debug CTest真实进程耗时227.75秒，Release25.96秒。新增 `MainWindowCreatedSaveTests` 31项及更新的 `TrackCreatedWorkflowTests` 5项均通过；其他既有回归全部通过。专项统计含初始化和清理。

更新后的跨模块工作流直接调用主窗显式保存API，覆盖提交新增、取消下一段、真实发布后clean、撤销dirty／重做clean、已有目标失败保持保存点、重开后Loaded身份及原输入字节不变；不再用直接writer调用加手动`markSaved()`代替主窗路径。

## 原软件兼容边界

[Return与软件输出对照报告](native-created-retry.md)记录了本轮实际运行。OpenGL及surface使用不同新隔离副本，原安装只读。surface配置与首槽除隔离路径外仅改变输出后端；两槽分别实际请求一次精确目标Return，窗口及物理图各自未变，均无SYN1打开记录，两个原Popen均正常wait0、forced=false。六图实际read回执与原图一致，原安装／运行副本各99项及输入集合、大小、摘要前后未变。

这是已执行的运行试验，不能继续描述为“Return未执行”；但合成键盘请求成功本身不能证明DOS客体已处理等价物理键。两后端表象不同也不能直接定位旧黑屏根因。未生成FTNEW，空板、真实单线创建／保存／重开、六／七字段、附加值、换行及默认参数仍未知。不得据内部显式六字段或七字段测试开放默认新增保存，NETDEF新增限制保持。

## 真实原生另存的已取得证据

使用集成源码冻结的诊断窗口，通过真实 Windows 原生文件框将新增段另存为全新 `DIAGNOSTIC-CREATED.PCB`，输出90字节。调用真实主窗显式API后，画面为3图元clean；菜单撤销为2图元dirty、重做为3图元clean。诊断文案明确六字段／LF只是显式合成参数，不是原 AUTOTRAX 默认值，普通产品能力门仍false。

协调者独立比较126个源码、测试与CMake文件和冻结HEAD内容一致；输出恰好为66字节隔离输入在ENDPCB前插入一条 `FT`，坐标200、250到800、550，宽17、层6，编码为显式六字段／LF，其余字节不变。最终24张原图均匹配原RPC图像并具有成功image回执。隐藏目标层取消取得原图；菜单Esc与真实窗口重开在追加现场完成。协调者此前误述首轮已重开，已经更正：首轮来源仍为INPUT，追加现场才以新进程载入输出，不将strict reader或自动化测试重开当作GUI重开。

首个诊断进程连接重试拖过延长截止；协调者在精确PID31364／birth `134380865164826143` 且dirty=false核对后，于UTC11:02:38通过 `Process.CloseMainWindow` 正常关闭。原持有Popen的owner记录wait0、forced=false，不能声称worker按时自行关闭。用户随后要求继续，同一Task／Pi会话追加最小重开及菜单Esc验收：新进程直接载入90字节输出，画面显示新文件名、3图元clean，三条Loaded身份且无历史；菜单Escape成功请求后的原图显示放置结束、3图元clean。新owner于20:45:18记录正常wait0、forced=false，早于20:53收尾。该Task指定核心范围通过，F3、完整文本输入及原AUTOTRAX兼容不在通过结论内，详见[真实窗口报告](mainwindow-created-save-live.md)。

## 本机证据与任务结算

Run为 `run_ba2b6ac49c4a`。原软件Task `task_c97906c5400d`／Dispatch `ctx_db8126806671`；主窗实现Task `task_4d5aa9b763e6`／Dispatch `ctx_4ed6d5bf848e`；静态Task `task_b84d052d1e94`／Dispatch `ctx_92006b122453`；真实GUI Task `task_ecdc9a63dfe3`／Dispatch `ctx_a91aa16f3171`。失败任务保留字面结果，不以部分证据替代完整成功。

协调者 `.local-analysis/save-roundtrip-wave/` 保存自包含spec、模型原事件审计、两配置构建及CTest日志／真实wait回执、父原软件图像与文件审计、最终结算与Git状态。子证据位于相邻 `feat-track-placement-ui/.local-analysis/mainwindow-explicit-save/`、`mainwindow-created-save-live/`，以及 `verify-native-menu-calibration/.local-analysis/native-created-retry/`。静态原会话只有失败API记录，未生成伪造的逆向报告。

原安装、运行副本、截图、会话、构建和原输出PCB不提交。main由用户管理；本轮不操作main、tag或发布。
