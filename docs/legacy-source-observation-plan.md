# EX-005实际用户源继承：隔离与观测前置设计

本文供后续实现和验收使用，当前结论为**隔离、目录API返回及阶段Host I/O观测能力受阻，尚不能进入候选或GO**。本子题完成设计交付，不表示运行验证通过；[EX-005](exploration-backlog.md#ex-005)原完成条件、原Task及EX-003均保留。所有下述新增接口、能力验证和A/B都未执行。

<a id="scope-and-evidence"></a>

## 范围、身份与来源

子Task `task_c2952287f2e6`／Dispatch `ctx_755c0c2b2a20`，Orca会话 `c8188639-cf9d-454c-b1fe-82f424f7c28a`，实际Pi `01a1d4e9-ce67-756e-8b4e-17d0dd926e95`。启动环境、原会话model／thinking事件与实际assistant记录均核为 `deng/gpt-6.1-sol/high`，首个PowerShell回执exit0；Git身份 `kylineyes <kylineyes@github.com>`。干净基线 `f5499279ea94964721c0bbe292c25e82a468a826`，由Orca初始分支切到指定 `research/ex005-source-observation`，只提交本文；共享入口、合并和推送由协调负责。

固定PE为 `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.exe`，本次只读核25836544字节及SHA-256 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832`。未运行DOSBox／PT／Qt／控制服务、查询窗口或全机进程、截图键鼠、试目录API／新身份／VM、注入、安装下载、读取实时U或制作conf／候选／GO；未调用 `service_environment`，未运行历史脚本入口。

| 来源及实际阅读范围 | 本文用途／核验边界 |
| --- | --- |
| [环境与语义校验源码](../tools/legacy_runtime_config.py)，第14–21、44–103、124–151、185–260、269–281行 | 已有白名单、PT启动契约、链接检查、环境赋值及其非沙箱边界 |
| [准备器](../tools/prepare_legacy_click_observation.py)，第25–69行；第八冻结 `candidate-eighth-status/desktop_session.py` 第8–9、104–109、307–316行 | 原调用方确实向控制服务及target的Popen传环境；不是切身份接口 |
| [默认根报告](dosbox-default-roots-static.md#roots-and-fields)，第33–157、196–203、221–227行 | Shell32根／后备、三阶段、八候选及历史边界 |
| [配置专题](legacy-dosbox-configuration.md#remaining-configuration-plan)，第365–426、434–479、813–909行 | 路径、parser／清文本、完成条件、矩阵和最新两键绑定；旧矩阵缺类型的文字仅属当时范围 |
| 协调树 `main-2/.local-analysis/config-path-incident-20261112/key-binding-proof-6951.json`、`key-binding-query-proof-6951.json`、`key-binding-validation-note-6951.json`，完整JSON；同目录 `inspect_ex005_witness_binding_6951.py` 第1–120行 | 复用已核注册／类型／查询局部链；18条来源依赖摘要均复核相符，未执行该脚本；旧失败保留 |
| 旧研究树 `explore-ex001-observer/.local-analysis/ex-003-live/` 下第八 `live-plan.json`、`eighth-status-candidate-review.json` 完整JSON、冻结driver／conf、early stderr第1–100行；协调树 `eighth-parent-final-audit.json` 第1–60及700–775行 | driver／conf摘要与计划匹配，冻结30项为已有审查记录；原target／control／driver／owner四wait=0及join记录只按历史材料采用，未重新核图或退出对象 |
| 同第八槽 `service-profile/user/appdata/local/DOSBox-X/dosbox-x-2026.10.01.conf` | 仅核已有迟后副本摘要，不读实时U，不推创建者或当时加载 |

来源精确路径、大小、SHA及身份核验在本树忽略证据 `.local-analysis/ex005-source-observation/source-identity-audit.json`；只读核验器为同目录 `audit_sources.py`。该回执验证18份材料和18条父证明依赖记录的一致性，不是重新完成父二进制控制流证明或任何运行能力验证。

<a id="known-and-missing"></a>

## 已有定义、已有执行与新增需求分开

本节继续[EX-005](exploration-backlog.md#ex-005)，各能力仍须按实际回执判断。

| 层次 | 已有事实 | 不能据此推出／仍需新增 |
| --- | --- | --- |
| 现有源码定义 | `service_environment`复制传入环境，创建槽内user／roaming／local／temp等目录并替换8项环境变量；调用方Popen使用该env | 没有加载另一用户配置文件或切换令牌的调用，不能保证Shell32跟随env；目录存在不是隔离回执 |
| 现有源码定义 | `confined`拒绝联接／重解析点和多硬链接；校验器明说“不是文件系统沙箱”，且仍固定PT／SYN1.PCB和七查询 | 只核声明路径不限制整个目标的OS访问；现有准备器／校验器不能原样承载本设计，不可放宽旧白名单偷渡 |
| 固定PE静态结论 | `SHGetSpecialFolderPathA(NULL, buffer, 0x1c, false)`失败或首字节空才试 `0x1a`；再失败／空才取 `windir`，null时用 `c:\windows`；后接 `\Application Data`及 `\DOSBox-X\`等 | 环境变量、系统目录配置、令牌和实际返回之间的关系未实测；windir非null空串不另走默认字面回退 |
| 固定PE静态结论 | 最早 `834aa6` Parse(UV)在D／Uflag／显式列表门之前；清文本不恢复Property当前Value；后续预解析、目录偏好回读、延后用户、最终显式／默认和生成重读均有独立守卫 | 单 `-conf`、`-defaultconf`或未用 `-userconf`均不能充当“没有用户预读”的证据 |
| 固定PE静态结论 | `[sdl] fulldouble`／`waitonerror`均为 `Prop_bool`，构造当前／回退初值分别false／true，类型2；`0`／`1`有已证转换接受分支 | 类型不再未知；全部消费／回调效果、公开查询完整语法和新运行回执仍缺 |
| 已有执行回执 | 第八有唯一显式argv／cwd、early加载日志、七CONFIG输出、Status固定文件名／八计数、四原wait及join；迟后U*与冻结U同SHA | 七查询没有这两键；U*的false／true又与构造初值一致，数值相符不能归因；late同SHA／时间和early日志不能补API返回或逐阶段Host I/O |
| 建议新增且未验证 | 独立身份／目录边界、无泄入文件系统、目录返回与阶段解析联合采集、该键最终查询 | 未取得具体工具存在、权限、配置或真实可用回执；下节仅列实现接口，不声称本机具备 |

<a id="isolation-options"></a>

## 隔离接口与推荐边界

推荐先由协调审查**可回滚的独立Windows环境、专用测试用户及独立磁盘内容**这一组合。理由是已证路径不只Uroot：程序目录P、C0／C1、固定 `C:\DOSBox-X\`和失败后备都可能参与；只换身份仍会共享宿主这些位置。这里没有检查或假定VM产品、镜像、虚拟化权限或许可证可用，推荐不等于选定工具，更不等于批准创建或启动VM。

| 备选／具体接口 | 待审实现的输入→输出 | 必须先补的前置与限制 |
| --- | --- | --- |
| 独立Windows环境＋测试用户，优先候选 | 已确认的环境管理接口、可回滚基线ID、独立测试SID、相同SHA映像普通副本、限定输入集→基线摘要、客体身份／根回执及A/B后可审输出 | 无宿主用户盘、共享目录、网络配置来源映射；向内仅单向导入核过的PE及必要依赖／自造输入，不导入真实U／PT／板库／历史槽；禁用共享剪贴板／目录等自动同步并取配置回执。客体系统、依赖、代码页与本次环境差异须记录，结果仅适用于该新环境 |
| 同宿主独立用户，后备候选 | `CreateProcessWithLogonW`配 `LOGON_WITH_PROFILE`；或 `LogonUserW`→`LoadUserProfileW`→`CreateEnvironmentBlock`→`CreateProcessAsUserW`，输出新进程原HANDLE和实际token／profile回执 | 两条API链是待选择的Windows接口，未核本机可调用性；分别审账号建立权限、凭据不入日志、profile加载／卸载、所需特权、环境块和退出等待。仅 `CreateProcessWithTokenW`、env覆盖或restricted token的名称不能证明加载了目标profile。若不能在启动前证明原件不可访问和P／Sroot／后备隔离，本路线拒绝 |
| 仅现有service_environment | env字典与槽内目录 | 已有定义可复用作缓存管理，但缺实际根／访问边界，不接受为本题隔离路线 |

后续身份验收至少记录子进程token的SID、AuthenticationId／TokenId（LUID原整数或字符串）、会话ID、完整性级别、profile加载结果与归属；通过 `GetTokenInformation` 等明确接口读取，不能拿父用户名或env中的USERPROFILE代替。`SHGetKnownFolderPath`可作该测试身份的辅助检查，但固定PE调用的是旧Shell32 CSIDL接口，仍须观察目标实际 `0x1c/0x1a`调用；辅助检查不能替代它。

根白名单须覆盖Uroot／UV、P、C0／C1、Sroot和windir后备，区分可读输入、可写输出与系统DLL必要只读访问。启动前检查每个候选的逻辑／实际路径、重解析点／硬链接、完整集合及摘要；原件路径不能挂载到新环境，不通过硬链接／联接复用。必须先有OS隔离／访问控制的拒绝能力回执：事后发现越界再停不能保证真实U未泄入。遇到目录API失败／空串会转后备时，只有后备也已隔离且在本方案输入内才可继续，否则停止。

<a id="observation-contract"></a>

## 最小观测记录与阶段绑定

建议采用单次运行专属的有序事件文件和结束摘要；只是本消费者所需字段，不创建通用框架。所有事件带 `run_id`、A/B标识、递增 `seq`、UTC及单调时间、PID＋创建FILETIME原整数、TID、实际模块基址／映像SHA、来源事件ID。路径保留原始编码／原串与解析后路径，不用规范化值覆盖原始值。禁止只按PID或墙钟近似关联，丢事件／溢出／截断须显式计数并导致本轮不能验收。

| 事件 | 必需输入／输出字段 | 判定用途 |
| --- | --- | --- |
| 身份／启动 | 令牌与profile回执、argv原数组、初始cwd、实际映像路径／SHA／基址、已审环境键值白名单、基线和输入清单SHA | 证明启动身份及A/B不变量；不记录凭据，不复制全机环境 |
| Shell32进入／返回 | API名／导入槽与调用站点RVA、调用ID及TID、hwnd、buffer地址／可读上界、CSIDL原值、fCreate；返回BOOL原值、返回后有界buffer原字节（最多0x104字节）、NUL位置／长度／解码及读取是否完整 | 正常第1次调用点RVA `a56bbe`，第2次 `a56bec`。返回0与首字节0分开；失败缓冲也记录有效性，不把它当路径。第2次未调用应由第1次成功非空及控制流事件解释，不能伪造一条“成功” |
| windir后备／根构造 | 前两调用失败／空条件；CRT查询的返回指针null与否、字节串及长度；最终Uroot／UV原串 | 保留null、非null空串及长度门差异；常量后备也必须归属隔离区 |
| cwd／映像根 | 取程序目录、C0／C1取样时点；每次chdir的请求、返回／失败码和成功后cwd | 防止把相对路径按初始cwd错误还原；仅记录已审目标，不查询桌面 |
| 配置解析进入／返回 | `parse_call_id`、父阶段ID、caller RVA、路径原串／编码、该次cwd、实际解析路径、F计数前后、返回AL、流状态／读终止掩码、键写值或拒绝结果 | F已登记不等于接受键，AL=1不等于正常EOF；`mask6`统一结束仍须标明未区分的流原因，不补猜成功 |
| Host文件访问 | 对应解析／写出调用ID、尝试序号、API／操作、输入路径、解析后路径／文件身份、open／create disposition、访问权限、返回状态／原始错误、成功句柄；Read的偏移／请求与实际字节数、输入摘要绑定、Close及写出／删除结果 | 同一路径多次打开按调用ID分开；失败打开也保留；成功open不等于实际Read、parser接受或只读访问。采集需从首次目标指令前覆盖到退出 |
| Property见证 | sdl节／属性名、对象与Value地址、类型2和布尔值；初始、每次相关Parse及ClearText前后、最终解析结束、查询前后取样；写入来源调用ID | 连接“文件字节被读”与“当前值被写／保留”；读取仅限已证对象字段，不猜全内存布局 |
| 最终查询／退出 | 已审原命令字节、规范化节名／键名、执行时点、stdout原字节／编码／重定向文件SHA、实际写入数量、错误与命令返回；查询前后Property值、shell PSP／环境段／容量、CONFIG条目前后原字节及SetEnv返回；原创建者HANDLE等待结果、采集结束及丢失计数 | 查询仅在最终解析后；采用[最小查询契约](legacy-config-query-contract.md#minimal-contract)。已核GET尝试更新shell的CONFIG，容量失败可先删旧项且调用方不查结果；属性值、输出送达和环境更新须各自见证 |

静态地址一律先首选VA减 `0x140000000` 得RVA，再加本次核实的模块基址；运行代码字节与SHA不符即停。不能把下表当已经设置的断点或完整调试脚本。

| 阶段标记／已证caller RVA | 必须区分的调用 |
| --- | --- |
| A 最早探读 `834aa6`；写出 `834af0`；清文本 `834afe`／清F `834b0e` | Parse(UV)、可能Write(UV)及值是否跨清理保留 |
| B 目录预解析 `834b47`、`834c10`、`834c92/834cc3`、`834db9/834e19`、`834f12/834fd7/835096` | userconf、每个显式项、cwd／P／U候选；不能合成一个“启动读取” |
| 目录偏好 `835b80/835cd7`；延后用户 `835df0/835f54/835fd7` | R回读／保存与UV读取／生成重试；记录Q／Uflag条件或明确未捕获 |
| C 最终显式 `8360ac/8360e4`、默认 `836612`、生成／重读 `836670/83668c` | 原名／前缀重试分开；默认须有候选序号，路径重复也不能合并 |
| parser `a8d7d0`、writer `a8b7b0`、清文本 `81e6c0`、最终查询 | 捕获每次进入与匹配返回，caller关联阶段；取最终值须晚于全部配置阶段 |

<a id="capability-gates"></a>

## 观测手段与最小待审实现步骤

当前已有静态映射、历史日志及后续三项离线组件，仍没有上述完整观测的执行回执。[两键查询消费契约](legacy-config-query-consumer.md#offline-query-consumer)仅提供精确命令数据，[API缓冲解码](legacy-source-api-buffers.md#result-contract)仅解释显式快照，[序列审计v1](legacy-source-observation-audit.md#schema-v1)仅查已提供事件的结构和配对；三项均已父审及合成测试；后续[纯提取核心到审计v2的离线互通](legacy-source-observation-audit.md#capture-v2-integration)已接入Shell32原缓冲，并通过含6项跨模块测试的100项集成回归。v1保持原字段，v2仍不包含Property、windir或全部Host IO，当前尚无真实联合采集器或运行器。后续[有界读取适配](legacy-source-memory-reader.md#parent-review)已通过20项父树注入native测试并接提取／v2；真实工厂未调用，不能替代此处实际能力回执，状态化组装器及联合验证仍待。文件事件追踪可以提供Host打开／读写／失败及路径，但单独不能给Shell32缓冲、解析AL、F和Property取样；调试观察也不能只记入口而漏掉返回或其它线程。工具名称、Windows自带某接口、已装Capstone均不等于观测能力可用。

后续可以审查“文件I/O事件采集＋目标启动时的只读调试观察”这一组合：文件侧需选定可用ETW等提供者并证明字段／权限／丢失计数；内存侧可评估硬件执行断点和调试事件接口，按 `WaitForDebugEvent/ContinueDebugEvent`、线程上下文读取、`ReadProcessMemory`取得参数及返回数据。**本轮不调用这些接口。** 软件INT3断点、IAT hook、注入DLL和修改目标内存不属于只读方案，不可作为缺能力时的自动降级；硬件调试寄存器和暂停／单步仍会影响执行，亦须另行审核授权和影响范围。

x64硬件槽数量有限，不能同时固定覆盖全部站点；观测实现须给出阶段轮换、每线程／重入call-return配对、模块加载、线程创建及丢事件处理，并证明不会漏过首次Shell32和配置IO。没有这份能力回执就继续受阻，不在本报告虚构现成采集器。

以下步骤仅供协调审查实施，不是本轮执行清单或现场批准：

1. **消费者确认。** 先确认隔离路线、观察方式和GET最小契约；冻结所需字段、目标SHA／RVA与失败规则。明确实际可用工具路径／版本／摘要及权限来源；不遍历全机找工具，不先安装再补审。
2. **非目标能力夹具。** 在获准的独立测试身份内，用单独审过的最小测试程序请求完全相同CSIDL参数并执行一次可预知的文件成功／失败打开、读、写、关闭；输出身份、目录返回原字节、序列和原等待。与采集器逐事件核对，包括两个线程、重复路径、失败返回和故意制造的丢失／截断拒绝。只调用KnownFolder或夹具自己打印文本不足以验证外部观察能读参数／返回。当前没有编写或运行该夹具。
3. **隔离的拒绝证明。** 对该环境中专设的禁读哨兵文件先取得OS拒绝回执；哨兵不放真实U或原件。核候选各根与共享映射，证实权限/映射边界是预先生效；真实U不可用作隔离试验输入。若API返回隔离区外根、配置可来自未知共享位置，停止。
4. **固定映像绑定检查。** 无目标运行地审查映像映射／RVA、参数ABI和阶段表；夹具通过仍不能证明固定目标会完整捕获。后续全新获批目标场景必须从创建时采集，任何字段缺失都使该次结果无效，不能事后再启动补齐旧记录。
5. **分别审候选与执行。** 前述能力回执、GET契约及无PT消费者通过后，协调再评估新A/B候选、预算和独立GO；本设计不制作它们，不复活旧worker／旧槽／旧批准，也不延长桌面窗口。

<a id="minimal-ab"></a>

## 单键A/B的输入、输出和停止条件

仅为新的机制对照，拟用 `[sdl] waitonerror`作为一个待审见证键：具体Bool类型已证，构造初值1；A写合法词元 `1`，B写 `0`。`fulldouble`初值0可留作备选，但不同时改两键、不找第四键。选择waitonerror不代表其全部消费／错误路径安全性已验；其消费者和退出策略须在候选审查前确认，不以诱发错误来取值。

A/B从**同一个干净环境快照恢复**，使用同一测试SID、profile、映像绝对路径／SHA、argv、cwd、显式文件字节、采集器和GET命令。正常串行运行，前一个已等待结束、取出证据并恢复基线后才启动后一个。run_id和输出存放元数据可不同，目标看到的输入／输出逻辑路径须相同，防止把换槽路径也混为因果变因。

**唯一目标输入变因：** 实际Shell32返回的隔离Uroot内，版本文件 `dosbox-x-2026.10.01.conf`的同一键值单字节由 `1`变 `0`；文件其余字节、编码、长度、换行、权限和可控制的元数据相同。文件清单的SHA变化是这一个字节的派生结果，不能夹带真实U其它内容。此处仅定义数据，不生成任何配置。

两个用户源均仅含该sdl键，无autoexec章节、include／路径选项或其它业务命令；显式文件固定且不含该键，必要的启动与查询命令只能来自新审的最小消费者。其它已知候选配置均为空缺且状态相同，cwd／P／Sroot／后备在隔离白名单内；若运行产生其它配置或偏好写回，须捕获并在B前恢复，影响输入即拒绝比较。初始UV预先存在且有效可减少最早生成支路，但是否确实没有生成仍看执行证据。

不沿用第八autoexec或PT挂载／输入，尤其禁止把完整真实U（即使名为冻结副本）导入用户源。现有校验器要求PT且只认七查询，必须先取得独立最小消费者的审查结论；不得改旧conf／plan／driver、临时跳校验、假装七查询白名单已包含新键。并行交付现已提供[受限两独立参数的静态候选契约](legacy-config-query-contract.md#minimal-contract)，并核定GET尝试改shell环境；完整语法／外层shell预处理和实际输出／环境回执仍缺。本方案只指定语义输入“节sdl、键waitonerror”，不制作运行入口或将静态候选当执行批准。

| A/B观测组合 | 可接受解释 |
| --- | --- |
| 两轮初值均1，API根相同且隔离；确认A/B对应UV在A阶段被打开、读到唯一键且类型2接受；清理后和最终查询前A=1、B=0，查询也一致 | 支持该新场景中未显式覆盖普通属性受隔离用户源影响，并跨所记录清理保留；若后来还有同文件重读，只能称用户源继承，不能独断只由最早预读造成 |
| A阶段B已变0，后续某次Parse后回到1，最终两轮均1 | 支持发生过早期写入及后续覆盖／复位；须定位使其改变的阶段，不能据最终相同称“没有预读” |
| API和逐阶段链完整，但UV未被读取，最终两轮均1 | 只说明此新场景未沿所设来源读到见证值；记录实际守卫／路径，不外推第八或所有启动 |
| 只见open／最终相同值、缺Read或键接受、API根不符、查询错误／字段缺失 | 不能归因；本轮失败或受阻，保存缺口，不通过重跑追认原轮 |

A的1与构造初值相同是参照，B的0提供与初值不同的信号；这解决U*旧false／true与构造初值相同造成的不可辨识问题。单凭最终A/B不同仍不能分辨是最早还是后续用户解析，因此必须同时关联阶段、实际文件身份与Property写入。若需要独立证明“仅最早读取”，必须先证所有后续用户打开未发生；不通过新增开关或删除文件临时制造第二变因。

运行中任一条件即停止新增试验动作并走已审收尾：身份／根／SHA不符，原件或真实U可达，出现非白名单配置／autoexec／PT，写入越界，配置字节中途改变，采集未从首次调用覆盖、返回配对失败／丢失／截断、未预期后备／目录选择GUI、GET契约不符或预算不足。权限边界须在目标前建立；捕获到泄入只能记失败，不称保护成功。收尾保留原HANDLE等待、采集结束和所有失败；不为补字段另起目标，不修改旧历史。

<a id="validation-and-open-items"></a>

## 验证与交付限制

本子题只交本文和本树忽略的来源核验材料，不写实现、探针或运行配置。`python -B .local-analysis/ex005-source-observation/audit_sources.py`返回0：18份来源／18条父证明依赖摘要一致，冻结driver及conf匹配，实际身份与固定PE摘要通过；仅作只读来源核验。`python tools/check_exploration_docs.py`返回1：158份Markdown／1244本地链接／41开放事项／130来源细节／142索引报告，唯一错误是本文尚未在完整资料索引中恰好出现一次；原回执保留于 `.local-analysis/ex005-source-observation/document-check.json`，由协调统一入链，未改共享索引。`git diff --check`及 `git diff --cached --check`均返回0，后者实际覆盖暂存的唯一新增报告；回执在同目录 `diff-check.json`和 `staged-diff-check.json`。不运行无关构建或GUI测试。

协调已完整审阅方案，独立重核18来源及18条父依赖摘要、固定PE摘要和已证路径守卫，确认A/B设计限定为隔离用户源中一个字节的变更，旧值与构造初值相同不作归因，前置未验证时保持受阻；没有制作或运行A/B输入。随后按已审查询报告补齐CONFIG环境及输出数量的观测字段；父证据为协调树`.local-analysis/ex005-parallel-6951/query-and-source-parent-review.json`。此验收仅接受设计交付，不表示隔离或采集器已实现／实测。

**剩余未知：** 实际可用隔离环境与权限、身份profile的目录行为、OS拒绝边界、目录缓冲及阶段Host I/O联合采集工具、硬件观察覆盖和扰动、GET完整语法与实测、无PT最小消费者，以及A/B全部运行结果。当前设计可供后续实现者按字段和拒绝条件落地，但没有任何隔离／观测能力已经通过；不以预算估计、静态类型或文档检查作GO，亦不将新环境结果追认第八历史来源。
