# PT Renew 唯一交接：当前进度与下一步

本文件是协调 agent 的唯一接手入口。当前协调者已完整读取本文件并沿原 Task／Dispatch／Pi 续接离线修复；用户本轮明确不启动新现场或新的接手 agent。能力概览见 [PROGRESS](PROGRESS.md)，知识入口见[文档导航](docs/README.md)，未知及领取状态见[探索待办](docs/exploration-backlog.md)。专题、冻结证据和旧会话保留历史事实，旧 GO／提示词不作现时指令。

<a id="baseline"></a>

## 接手基线和最短步骤

本轮接续前已实时核对共享本地及远端 `dev=7c91d804029c9a78a4f2a57a0287117ca282de4e`，协调工作区干净；原研究树仍为下文 `b38f153` 检查点，只有原配置草稿未跟踪。前轮文档整理最终核验为 `.local-analysis/handoff-refresh-20261112/final-state.json`；本轮事故后集合／原安装及配置复核见 `.local-analysis/config-path-incident-20261112/resume-verification.json`。实际最新 HEAD 仍以 Git 和远端为准；本轮交接更新在独立分支 `docs/offline-repair-resume`，研究实现仍在原独立分支。main 的合并／提交／推送由用户处理。

1. 完整读 [AGENTS](AGENTS.md)、本文件和[探索规则](docs/exploration-workflow.md)，核 `git status --short --branch`、`git log -5 --oneline`、远端 dev，以及活动研究树改动。未集成提交不能当共享 dev 已有。
2. **先接隔离事故，暂停新现场及进一步归档精简。** 所有原目标／控制服务／已知持柄链已退出；现存一个 Pi 子 agent 仅做离线保全和修复，没有获准的新候选现场或第四槽 GO。
3. 沿下文原 Task／Dispatch／Pi 继续，不重复领取 EX-003、不新建同义 worker、不重启原会话。新协调者使用自己的实际身份，不能冒用原父 Pi `01a1cb92-9f30-71d5-a89b-dca34f1b90e1`；该旧会话只作审计来源。
4. 用户模型覆盖、七小时授权和单操作者要求继续有效。事故暂停优先；只有核完事故、修复、测试和新冻结范围，才评估剩余有效时段能否重开现场。

远端为 `git@github.com:Kylineyes/pt_renew.git`。直连 DNS 和代理 SSH22 曾失败；已验证进程级 `GIT_SSH_COMMAND` 使用 `ssh.github.com:443`、`HostKeyAlias=github.com`，经 Git 自带 `C:/Users/rikideng/scoop/apps/git/current/ucrt64/bin/connect.exe -H 127.0.0.1:10808 %h %p` 可 fetch／push。保留主机密钥检查，不改全局配置；推送中断先查远端再普通重试，不强推，不把未确认写成成功。

<a id="capabilities"></a>

## 当前产品能力与严格边界

已发布 **v0.11.0-alpha 是只读包**；dev 另有自由 FT 编辑和受限另存，未发布新的编辑安装包。相同版本字符串不证明能力相同，用具体源码／EXE 摘要及入口判断。

| 范围 | 已有能力 | 保持的限制 |
| --- | --- | --- |
| PCB／视图 | 已覆盖记录严格载入、图层、选择属性、定位、测量和端点捕捉，正式 `pt-pcb-check` | 字形／部分轮廓近似，代码页／旧格式不全，CLI 解析不证明原软件兼容 |
| LIB／NET／铜 | 只读库浏览、受限 NET／NETDEF、引脚映射及保守几何分析 | 未实现元件放置／替换、库写入、完整 DRC、布线、生产输出 |
| 已载入自由 FT | 整数 mil 整线移动／删除、Undo／Redo、保存点和未保存保护 | 元件内及其他类型只读，宽／层／extra 不可改 |
| 普通另存 | 保原字节，只补四坐标词或删除 FT；新目标、临时文件后不覆盖发布 | 不覆盖原件或已有文件，Ctrl+S 覆盖未开放；保存点不重绑输入、不清历史 |
| 内部 Created | 身份／历史、预览／提交、显式编码／预检／writer、画布和 MainWindow 显式另存闭环 | 参数须显式，`trackPlacementUserEntryAvailable()` false；正式菜单／F3／P→T 禁用，默认 MainWindow／writer 拒绝 Created，新增遇 NETDEF 拒绝 |

内部新增约束：整数 mil，端点 ±1000000、宽 1..1000000、层1／6、零长拒绝，无隐含取整／吸附。总文件64MiB、语法记录最多200000（含COMP／ENDCOMP／内部记录／ENDPCB）。这些是当前工程规则，不是已恢复的全部原格式限制。原 AUTOTRAX 自建单线保存重开和默认 FT 编码仍缺；静态 extra 结论不替代样例、不解除铜覆盖保守策略或正式新增门。

<a id="validation"></a>

## 已有验证与适用范围

产品 `src/`、根 CMake／预设沿用已测 `d2ee381161fdb444255f7db931aa1f1290aa5bd7` 基线；之后 tools／tests 有研究增量，不能称全部相同。本次交接只改文档，不重复完整产品构建或 GUI。

- 固定候选 Debug／Release 配置、构建及 CTest 各24/24，正式 CLI QProcess 专项15项；核心审查82 passed含初始化／清理。见[核心边界](docs/track-core-boundary-review.md)、[综合记录](docs/native-sample-wave.md)、[离线集成](docs/native-evidence-wave.md)，不同候选数量不累加为当前整体覆盖。
- [真实 Qt 核心现场](docs/parallel-save-hardening-live.md)：固定374b1d7，载入生命周期、失败保留、旧watcher隔离、关闭取消、主窗另存、保存点／历史／输出重开，18图及原owner wait0；未覆盖模态重入等仍按原范围。
- [内部显式新增现场](docs/mainwindow-created-save-live.md)：合成六字段／LF、取消／原生另存／历史／隐藏层／新进程重开，24图及正常退出。不是正式新增门或原 AUTOTRAX 兼容通过。
- [独立原生保存往返](docs/native-save-roundtrip-verification.md)仅有限通过，不等于全部dirty／失败／覆盖路径通过。原字形静态／机器码／复制／边界及A240局部证据已有，整体 `runtime_verified=false`。真实NET／铜竞争、极端坐标、系统会话结束、干净Windows等仍在队列。

<a id="research"></a>

## 已完成研究与剩余未知

当前队列41项。EX-001／EX-004已按完成条件闭环并删项，EX-003／005／006／008／017仍保留；EX-007未启动。

| 事项／交付 | 已得结论 | 仍须保持的范围 |
| --- | --- | --- |
| [一次菜单观测](docs/native-menu-click-audit.md#live-menu-conclusion)，4266c52 | 实机兼容33样本／join；一次Click的189样本完整覆盖与菜单真实后图；七组原创建退出wait0；28定向测试／13阶段注错 | 不定位旧终端前景来源，来源边界留EX-038；菜单活动Alt+F4语义留EX-003 |
| [两轮客体捕获](docs/native-capture-checkpoint.md#continuous-capture-conclusion)，ceee461 | 同新目标两轮各一新640×480PNG，路径／动作独立，十图read回执匹配；四组wait0 | 两张同为启动页，字节可相同；不证明板名／计数、状态或编辑 |
| [EX-003离线语义](docs/native-menu-calibration.md#shortcut-offline-semantics)，c4ddfeb | Shift+I为Shift down/VK_I down/up/Shift up；普通i/I为Unicode；假API失败仍可能Pressed；16测试两个Python／23回放 | 真实HKL／队列／IME／SDL／DOS消费和鼠标映射未证，不能靠大小写称绕IME |
| [EX-005配置阶段](docs/legacy-dosbox-configuration.md#effective-state-attempt)，082aca3／纠错72c620c | 有效opengl／vgaonly／fixed10000／16及本槽captures、AXTYPE；Enter后客体与合成5FT结构相符 | Shift+I后IME候选框，无Information／Status文件名和计数；完整来源覆盖仍缺 |
| [EX-006宏调度](docs/legacy-command-dispatch-static.md)，6281f84 | 宏队列／录制／递归截断、Repeat模板、Un-Delete删除链，96静态核验 | 真实宿主键码、上下文及运行响应缺证 |
| [EX-008 FT extra](docs/ft-extra-static-semantics.md)，bb3b540 | 缺失→0、仅整数1置真、核定保存路径输出0/1，局部预布消费者 | 完整电气／间接消费者、非规范输入缺证；保原值及存在性 |
| [EX-017 LIB目录](docs/library-directory-state.md)，3ff4a3d | FFFF、删除留名称计数、首空槽复用、同名压缩去重 | 合法别名、保留字段、版本／中断状态缺证，不猜恢复 |

EX-005客体底栏曾被误读，经父及原Pi复读纠正为 `1:Top Layer / P:ROUND62 / T:12 / S:60 / G:25`；原错误和冻结审核保留，不当文件名／图元计数／新线默认值。阶段报告已集成，不能重做已完成模块；完整条件未达保留事项，不因agent退出／工具失败删项。新未知先去重、建立双向链接，主题和专题是知识落点。

<a id="plan"></a>

## 最高优先级：隔离事故与当前任务

截至本轮独立字节复核 UTC **2026-11-12 05:05:38**（北京时间13:05:38），旧包事故后400项、原安装99项及三份配置均与保全记录完全一致，父／worker保存的400项清单也一致。前轮UTC04:19核对的原软件／控制服务／已知持柄链已退出及原wait证据仍按当时范围成立；本轮只读进程清单工具调用超时，未据此声称实时无进程。原Pi子agent已经确认续作同Task的离线修复，尚无修复交付可审。**本轮不启动新现场或新的接手agent，新现场与进一步归档精简暂停，第四槽没有批准或GO。**

### 有效授权和接续身份

用户先给四小时，后明确“现在延迟到7小时控制时间”，按同轮总时长登记：UTC **2026-11-12 02:00:53–09:00:53**，北京时间 **10:00:53–17:00:53**；UTC **08:50:53** 起至少10分钟整体收尾。窗口内新协调者可自主调度必要控制，不重复索同一许可；超时后不沿用。用户要求阶段完成或受阻主动通知。**事故修复和隔离复核通过前，这一授权不自动解除暂停。**

全部子agent继续 **Pi、`deng/gpt-6.1-sol / high`**，显式用户覆盖优先于AGENTS旧GLM默认分工，不自行换模型／重索权。启动配置不等于模型证明，核PI环境、原JSONL model/thinking/assistant及成功工具回执；同Task沿原Pi，不重启。本轮已复核原JSONL模型变更、high记录、最新assistant及成功工具回执，与原会话一致。

当前协调Pi为 **`01a1ce1a-7d18-7607-ad1d-cc38ad702860`**，实际环境为 `deng/gpt-6.1-sol / high`，已通过自身身份 `run-use --id run_3efe904a98f0` 成功绑定原Run；未冒用旧父身份或重启worker。离线续作消息 `msg_5d2fa9e736ec` 已获原Pi状态确认 `msg_8e41ee3529a1`。本轮只授权继续离线实现、合成夹具／假创建测试、文档与审查，不生成现场候选或新GO；旧七小时时段不扩大本轮范围。

| 项目 | 实际记录 |
| --- | --- |
| 未结 Task／Dispatch | `task_db06ca9d4229`／`ctx_e3ea7d528345` |
| Run | `run_3efe904a98f0`，名称仍为首轮EX-001，不代表当前任务范围 |
| 原 Pi／模型 | `01a1cb98-e57e-75d0-9b06-c40a941eaaf0`／`deng/gpt-6.1-sol / high` |
| 原终端 | `term_896ab8d5-51f6-4082-b741-6eec0625269e` |
| 工作树／显示名 | `C:/Users/rikideng/orca/workspaces/pt_renew/explore-ex001-observer`／EX-003-输入导航 |
| 分支／离线检查点 | `research/ex003-live-navigation`，最新观察HEAD为`b38f1531b77d09d0d863ca297a731116b898f0ab`；跟踪文件干净，仅未跟踪`tools/legacy_runtime_config.py`，接手复核 |
| 未完成修复边界 | 该模块尚未接入准备器、owner或driver，尚无语义回归测试通过；不能因文件存在就称隔离已修复或直接生成现场 |
| 本Task证据 | 活动树 `.local-analysis/ex-003-live/` |
| 接续检查点 | 原worker于UTC04:30:23保存`.local-analysis/ex-003-live/paused-checkpoint.json`；本轮核验后一致并已由原Pi确认续作离线修复，原Task仍未结，不发整体worker_done。原检查点保留为历史，不覆盖成当前完成记录 |

先加载实时 orchestration／orca-cli 技能。用 `orca orchestration worker-show --dispatch ctx_e3ea7d528345 --json`／`worker-read` 核状态；通过 `orca orchestration send --to dispatch:ctx_e3ea7d528345 --subject ... --body ...` 协调，不给终端追加业务。本轮已核原Dispatch `ready/live`、原终端保留和原暂停回执，随后才发离线续作；这些是核验时状态，不是修复完成。新协调者若需绑定Run，先看 `orca orchestration run-use --help`，按实际权限 `run-use --id run_3efe904a98f0`；绑定／身份拒绝时保留资源和回执，不reset、不stop/restart规避。先核最后回执，避免重复已执行动作。多个旧Dispatch共享该终端，不算多个活agent。

### 未集成的活动分支提交

以下工具／历史提交尚未作为完整交付集成，先审差分、代码与测试，尤其不要让其旧HANDOFF增量覆盖本新版。事故专题检查点`b38f153`的文档及第一段事实已单独选择集成，未带入未验工具草稿；未来整分支合并需处理已选择文档的上下文和HANDOFF差异。

| 提交 | 内容 |
| --- | --- |
| `321cc4e` | 逐客体审核的命名键导航准备器 |
| `a4affb2` | 第一分段有限导航事实，未达Information |
| `e573ef3` | 预算参数及原owner／driver60分钟上限边界测试 |
| `f7f6dca` | 任何owner创建前核GO时段，真实-File／假创建测试；保留owner／driver二道门 |
| `9a07c5c` | 同步事故和暂停的旧HANDOFF增量；当前交接只以本文件新版为准 |
| `b38f153` | 事故和离线暂停专题／待办状态检查点，文档已由父选择集成；修复草稿不在此提交 |

未跟踪`tools/legacy_runtime_config.py`为9137字节、SHA `718dc94d29ac5104fa4d680227c92ea6cee74608ec4e233e1d1918313d023f63`，只做过AST语法检查，无语义测试、无接入，不能add/commit时混作已验工具。已读取worker的`.local-analysis/ex-003-live/paused-checkpoint.json`，其中列明生成器、派生Capture／State／Navigation、owner／driver服务启动前预检、别名／联接及零创建测试和可写白名单均未完成，未生成修复后候选／GO。状态消息`msg_7ae7d2dbb3a4`确认原Pi停在该检查点，待新协调者通过原Dispatch续接；不为干净而丢弃未跟踪草稿。

### 三个导航槽的实际结果

| 槽 | 已得事实 | 未达及失败 |
| --- | --- | --- |
| `candidate/slot`，02:22–03:02 | 02:55正常停业务；新guest逐步证Block→Current→Delete→Edit→File→Grid五次Down，35原PNG匹配read；四组原wait0至03:00:15，父另read Grid／核原wait | 未发第6/7Down、Information确认、Esc，不是Information到达或完整EX-003完成 |
| `candidate-second/slot`，原批03:25–04:25 | 操作者03:24:28提前32秒调用；owner21372原创建者wait1于03:24:30；driver／服务／目标／桌面请求0 | 许可撤销不重试，不改旧GO；是提前起跑错误，不是桌面／IME失败 |
| `candidate-third/slot`，原批03:45–04:45 | 时段内启动／33兼容样本join；首截图后本槽captures空，03:52:37集合差拒绝；完整120秒静默后正常X，target28820／服务19000／driver45320／owner41048原wait0至04:01:50 | **配置未重绑写入旧包，隔离失败。未发客体Enter／Down。旧GO已失效，不重跑、不当捕获成功** |

### 隔离事故：差分、保全与不可恢复边界

归档清理后 `review-track-core-boundaries` 为指向归档物理树的目录联接。准备器入口将source `Path.resolve()`，旧conf仍是逻辑原路径；字符串replace找归档物理路径，**0次命中却未拒绝**。第三conf仍为旧SHA `e2931daeac67ece9c8f0b64012814ec334066c45f0b315580a3f54d7a57b9486`，logfile／captures／C、D挂载4处都指旧 `slot-retry-01`。父核摘要／集合却漏查conf内部归属而批准，工具和审查均遗漏；first／second配置各自正确，不能归因IME。

父和worker独立以原399项清单得到相同差分：现400项，新增1、修改1、无删除，其余原文件大小／SHA一致。

| 旧包内相对路径 | 事故前 | 事故后 |
| --- | --- | --- |
| `slot-retry-01/captures/pt_000.png` | 不存在 | 6155字节；`e473d5d1817063b927ca7493c3920f78b6282ccf4ed70f87badaf9161ad665e6` |
| `slot-retry-01/dosbox-startup.log` | 8846字节；`fc4680bc51d3c8c0e17672cbc5f8d3d14956c7d3f39acdab8d36058e7ab8ab34` | 9038字节；`d41cddaa69f8ab0fa24b592ded8d8c957073132dd4630684daeb6a98c08666bb` |

旧runtime／PCB／库在399集合内，除上表外字节未变；worker `path-incident-preservation.json`已复核原安装99项、first及前轮证据集合／大小／SHA不变，父已读该结果；这不证明没有瞬时写入后恢复同字节。旧“399不变”、清理和精简保留清单只在当时核验时刻成立，不据旧清单否认本次污染。

父保全 `main-2/.local-analysis/config-path-incident-20261112/`：`incident.json`、`old-source-current-manifest.json`、`changed-current-bytes/`及三份conf；worker另有 `third-path-boundary-audit.json`、`path-incident-preservation.json`。当前副本不冒充原日志。父在项目归档根及主／活动树忽略证据的普通文件中未找到8846字节精确副本，见 `log-copy-search.json`。worker另查6份已知项目ZIP元数据及相关Pi工具回执日志文本，也未找到原字节匹配，见 `original-log-copy-search.json`；未扫任意外部备份或全部7z，不扩大为已穷尽恢复来源。Git bundle通常不含忽略日志，不能当备份。**不删新增PNG、不覆盖恢复旧日志、不改旧manifest／冻结审核／原JSONL、不重跑历史清理脚本。**

### 接手后的执行顺序

1. **接住原worker离线检查点。** 已授权同Task修复，无需再问是否允许离线研究。收最新HEAD／未提交改动／测试和根因报告，核保全与原安装摘要；有限查原日志副本，未找到就明确损失范围，不伪造恢复。
2. **修配置生成和启动前隔离。** 按配置节／autoexec语义重绑logfile／captures／C、D挂载／程序输入输出，匹配0次、多次或残留旧根拒绝。生成后及**创建控制服务／目标前**核逻辑和resolve物理写入目标都在新槽内，拒绝联接／符号链接逃逸、外部挂载；列可写路径和只读来源。补逻辑路径≠物理归档路径、替换0次、旧log／captures／mount、外部链接等离线拒绝测试，失败必须零服务／目标／输入。
3. **先沉淀事故和修复，本轮停在离线可审检查点。** 原失败保留；结论补现有专题及待办，不只存私有日志。实际读代码、当前conf及测试，不只比SHA。原Pi负责在独立分支完成实现、必要回归、白名单及文档并提交，协调者审查后集成；EX-003总体仍受阻，不以离线修复冒充现场通过。用户本轮明确不启动新现场，因此下列恢复导航步骤仅为后续顺序，不在本轮执行；不生成第四槽候选／新GO、不复用前三槽。每段上限3600秒、至少7分钟收尾，总最后10分钟只收尾等原门继续保留。
4. **恢复后只做EX-003最小导航。** 每键新host／guest实际read，保持Enter各1、Down最多7／Up最多1、实际Information高亮才确认、最多Esc1后验，未知即停。有限导航成功不等于IME／队列／鼠标映射全部解决，按原完整条件评估，不硬删项。
5. **可靠导航后EX-005，再EX-007。** EX-005缺Information／Status当前文件名、计数及完整配置来源覆盖，实测值／5FT外观不替代GUI核定。EX-007须确认空板／层宽／端点、新建一段、全新8.3另存并原软件重开，核字节／图像／日志／摘要及默认FT编码。最后才考虑EX-029正式入口；NETDEF拒绝和保守产品门不变。

<a id="scene"></a>

## 原软件现场约束

- 原安装 `D:/project/pt_renew/pt/`／`pt_install/`、原库和板图只读，运行／写入用隔离副本及完整前后集合／大小／SHA，不用硬链接。归档联接只作历史来源，不能作可写挂载源。
- 单桌面操作者、公开ControlStatus门、锁屏、精确PID+FILETIME+映像+HWND和当下原图保持。首次拒绝／观察失败完整120秒零新增桌面请求，含只读；在途不能打断，输入已发后验失败不重发、不换接口绕拒绝。
- 聚焦后不启shell抢前景，常驻驱动／单步文件投递；每步看图后决定，不预排菜单。指定模型实际read原PNG并匹配原JSONL image字节SHA；成功文字、menu_open标记、命中预测不代真实消费。大image.data落盘筛字段。
- 当前图CleanupSnapshot／必要精确CleanupFocus一次／正常宿主X一次／原WaitExit／Stop已验。target／service／driver／owner各原创建者持Popen/HANDLE至真实wait，服务退出不代目标退出，不强杀／WM_CLOSE；外层隐藏PowerShell自身无原Popen退出证据，不从下层wait0外推。FILETIME用Python／PowerShell原整数，不经JS Number。
- 每段至少7分钟正常收尾，实际总时段最后10分钟只收尾；旧GO／截止／PID不沿用。原Shortcut f11+p先释放F11再Unicode p，不是保持组合；Click不自动套Snapshot比例，DPI数值不是自动倍乘依据。
- 旧EX-001／004成功不否定本次事故；新事故不改写旧成功／失败原件。旧终端前景来源留EX-038，宿主黑线而客体可辨留EX-002；不能猜统一根因。
- 异步产品竞争另守原5秒／32次、20／50／55／60秒及600／900秒预算，`ready_for_live=false`范围不因本窗口扩大。

<a id="agents"></a>

## 工作树、清理和空间

本工程仅3工作树：原 `D:/project/pt_renew` main、本协调 `main-2` dev、活动 `explore-ex001-observer` 的 `research/ex003-live-navigation`。只有一个子agent终端，当前仅离线修复。旧91条派发／29个失效终端引用是历史，不算活agent；不要关闭当前worker或重置跨项目数据库。

用户要求清理后，14个已合入、干净且无agent／活终端／不可核验终端的工作树从Orca和Git撤下，14普通分支安全-d删除。HEAD在 `refs/archive/pt-renew-cleanup-20261112/` 和已验证bundle保留，旧会话保留；原路径为指向项目既有归档区的目录联接、无.git，不当活工作树或递归跟随清理。EX-006/008/017等完整事项仍受阻。

归档根 `C:/Users/rikideng/orca/worktree-archives/pt_renew/20261112-cleanup/`：最初10314文件／2160940892字节；随后删除589个非冻结、未引用的构建缓存971990804字节（39ILK、432OBJ、30构建LIB、16Ninja依赖、17CMakeCache、16Ninja日志、39RES），保留集核验时9725文件／1188950088字节，扣新增记录等保守净减少 **969318076字节**。原PNG／日志／EXE/DLL/PDB／源码／冻结文件未被精简删除；原捕获源399项在精简时完整，此后第三槽误写产生上文400项差分，两个时刻不可混称。

剩余约1.19GB主要是PDB747MiB、EXE93MiB、CMake YAML72MiB、JSON/JSONL52MiB、冻结或引用命中的ILK/LIB/OBJ80MiB、源码文档等。用户后来只询问用途，未授权另一轮具体删除；事故后已暂停进一步精简。`original-manifest.json`为精简前历史，各record的`current-retained-manifest.json`为精简完成时清单，事故后来源当前状态看incident。旧摘要不能代原字节恢复。

清理用途与回执见 `.local-analysis/worktree-cleanup-20261112/REPORT.md`；精简删项和空间见 `.local-analysis/archive-trim-20261112/REPORT.md`、`space-accounting.json`。最初同盘移动没有算释放。当前已有归档／删除脚本只作历史，不直接再运行。

<a id="evidence"></a>

## 本机证据和可复用环境

协调根 `C:/Users/rikideng/orca/workspaces/pt_renew/main-2`。下表相对 `C:/Users/rikideng/orca/workspaces/pt_renew/`；忽略材料不随clone分发，不为接手重复复制整套现场。新工作树缺忽略材料不自动否定专题结论。

| 位置 | 用途 |
| --- | --- |
| `main-2/.local-analysis/config-path-incident-20261112/` | 父事故差分、当前变更字节、三conf和日志副本搜索范围 |
| `explore-ex001-observer/.local-analysis/ex-003-live/` | 未结Task三槽、原wait／导航35图、事故审计、离线修复；third隔离失败 |
| `main-2/.local-analysis/control-window-04h/` | 新授权／七小时延期、spec及三段审核；历史目录名不是只剩4小时 |
| `explore-ex001-observer/.local-analysis/ex-003/` | 原AST输入语义、23假回放和16测试证据 |
| `explore-ex001-observer/.local-analysis/ex-005/` | 配置／Enter／IME受阻、12图／退出链、底栏纠错原记录 |
| `explore-ex001-observer/.local-analysis/ex-004/` | 两轮新客体原图、集合差、10图回执及原wait |
| `explore-ex001-observer/.local-analysis/ex-001-continuation/` | 菜单时序、189采样、5图、编码／关闭失败与7链wait |
| `review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate/` | 旧driver/gate/submit及双槽；当前只读历史，retry日志和新增PNG已污染，见事故差分 |
| `main-2/.local-analysis/native-capture-checkpoint/` | 更早AST／点击审计、旧双槽失败／7图和摘要 |
| `main-2/.local-analysis/exploration-wave-01/` | 首轮四项spec、模型错误／配额失败与父集成；旧GLM文本被新授权覆盖 |
| `explore-ex006-command-dispatch/.local-analysis/ex-006/` | 归档联接：宏/Repeat/Un-Delete、96核验、103输入摘要 |
| `explore-ex008-ft-extra/.local-analysis/ex-008/` | 归档联接：extra原字节、178记录／30指令、消费者 |
| `explore-ex017-lib-directory/.local-analysis/ex-017/` | 归档联接：七原件／四库／25根CFG及验证 |
| `main-2/.local-analysis/worktree-cleanup-20261112/`、`archive-trim-20261112/` | 工作树退役、589删项及当时保留清单／空间核算，事故后暂停精简 |
| `main-2/.local-analysis/native-sample-wave/`、`parallel-development-20261103/` | 产品24/24及前轮23/23、CLI与真实现场父审计 |
| `verify-parallel-save-hardening/.local-analysis/parallel-save-hardening-live/` | 归档联接：Qt核心18图／输出／原owner退出 |
| `feat-track-placement-ui/.local-analysis/mainwindow-created-save-live/` | 归档联接：内部显式新增／原生另存／重开证据 |
| `main-2/.local-analysis/agent-cleanup/`、`temp-maintenance/`、`handoff-maintenance/` | 旧派发／7shell退出、旧会话归档、12旧交接及4本机摘要归档核验，仅作历史 |

先读 `.local-analysis/WORKTREE_CLEANUP_NOTICE.md`，目录联接不开发不跟随清理。原安装、截图、字体、SDK、构建、会话、反编译数据库和全部`.local-analysis`不提交，不`git add -f`。

既有Qt6.12.0／MSVC x64／Ninja，SDK `C:/Users/rikideng/Qt/6.12.0/msvc2022_64`。研究用既有Python／Capstone，不下载无关依赖。产品复现入口如下；改变GUI仍需真实交互，writer大容量Debug用例用原预算，不以短工具超时打断：

```powershell
& ./scripts/Enter-QtEnv.ps1
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
# Release用release预设
& ./build/release/pt-pcb-check.exe --track-limit 100 <隔离PCB路径>
python tools/check_exploration_docs.py
```

CLI帮助及schema见[说明](docs/pcb-check.md)。`e0cc7fd9c64e7e332461b093ab2849aaedf978c0a247573c3c520c39331a0d8d`是历史已验CLI摘要，重建后重新记录，不当自动身份。PowerShell5.1脚本须BOM/CRLF；已有启动器真实-File离线检查及前置时段门可复用，不能只用ParseInput代实际文件加载。近期本地PowerShell工具偶有超时／255，现有bash宿主可运行同只读Python核验；保留原失败，不换低层输入接口。

<a id="history"></a>

## 唯一入口维护和历史追溯

以后只更新本文件承载当前进度、授权、接手约束和下一步；PROGRESS只做能力概览，专题／主题存技术结论，待办存未闭环问题。不另建SESSION_HANDOFF、日期agent-handoff、CURRENT_AGENT_HANDOFF、NEXT_AGENT_BRIEF或其它当前摘要。旧原文可从Git与已验归档追溯，冻结材料中的历史正文不改成新指令。

此前已移除12份受版本控制旧交接／历史根文档和4份本机活跃旧摘要，完整归档及SHA核验见 `.local-analysis/handoff-maintenance/`；例如 `git show c05baff:docs/agent-handoff-20261104-capture.md` 可读旧文。本次重整删除了累积的过时“当前”和重复计划，历史事实优先查[专题索引](docs/reference-index.md)及原报告，不补造失败／迟到／退出或删除剩余未知。
