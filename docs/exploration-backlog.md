# 工程逻辑探索待办

这里是探索 agent 领取任务的唯一清单，只保留尚未闭环的工程问题。先读[领取与研究规则](exploration-workflow.md)和[项目规范](../AGENTS.md)，再从下表选择一项；[当前能力](../PROGRESS.md)和[软件主题](README.md)用于理解整体状态。

每项都列出原文细节、已有结论、待回答问题和完成条件。原文对应段落反向链接到该项。编号固定，事项完成后删除其正文和索引行，并把所有入链替换为沉淀结论；Git 历史保留旧编号，不在这里积累已完成事项。状态只在事项正文维护。

本轮基于 `7e8477b` 的现有文档盘点，归并当前未知、缺证和有明确文档来源的待设计规则。未实现功能以研究问题登记，不代表已授权实现或开放产品能力。验证辅助工具的问题与产品能力分开说明，历史 failed 不升级为当前缺陷或通过。

## 领取索引

### 原软件输入、配置与取证

| 编号 | 探索问题 | 类型 |
| --- | --- | --- |
| [EX-001](#ex-001) | 菜单点击期间的前景、光标与命中窗口变化 | 行为根因 |
| [EX-002](#ex-002) | DOSBox 宿主呈现与客体状态不一致的条件 | 行为根因 |
| [EX-003](#ex-003) | 宿主按键、DOS 鼠标与菜单选择的实际映射 | 输入语义 |
| [EX-004](#ex-004) | 连续两轮真实客体 PNG 的可靠获取 | 验证缺口 |
| [EX-005](#ex-005) | 启动配置继承、DFT 和实际工作文件状态 | 配置语义 |
| [EX-006](#ex-006) | KEY 宏、Repeat 与 Un-Delete 的上下文调度 | 命令语义 |
| [EX-007](#ex-007) | 原 AUTOTRAX 自建单线保存重开与默认 FT 编码 | 兼容证据 |

### 板图、编码与文字

| 编号 | 探索问题 | 类型 |
| --- | --- | --- |
| [EX-008](#ex-008) | 既有 FT 第七附加字段的电气与保存语义 | 格式语义 |
| [EX-009](#ex-009) | 产品移动／删除及新增输出的原软件兼容 | 兼容证据 |
| [EX-010](#ex-010) | 含 NETDEF 时新增图元的合法布局与网络关系 | 格式语义 |
| [EX-011](#ex-011) | PCB 历史变体与焊盘、坐标、图层的精确几何 | 格式语义 |
| [EX-012](#ex-012) | PCB／LIB／NET 旧代码页与非 ASCII 名称 | 编码语义 |
| [EX-013](#ex-013) | 文字实际导入方向、长度截断与保存往返 | 运行语义 |
| [EX-014](#ex-014) | 非对称字形、高度量化、字距与旋转镜像 | 运行语义 |
| [EX-015](#ex-015) | 真实缩放、简化字形分派、字体指针与 VGA 像素 | 绘图语义 |
| [EX-016](#ex-016) | 经验证字形接入渲染、命中与铜层的边界 | 工程设计 |

### 库、网络、铜层与生产规则

| 编号 | 探索问题 | 类型 |
| --- | --- | --- |
| [EX-017](#ex-017) | LIB 目录残留、未分配、别名与保留标志 | 格式语义 |
| [EX-018](#ex-018) | LIB 图元附加标志、电气意义与原软件预览 | 格式语义 |
| [EX-019](#ex-019) | 封装放置、替换及板上元件编辑的实例规则 | 工程设计 |
| [EX-020](#ex-020) | LIB 写入、合并和压缩的格式及保留规则 | 工程设计 |
| [EX-021](#ex-021) | 真实 NETDEF、元数据和其他网表语法 | 格式语义 |
| [EX-022](#ex-022) | 铜层、负片平面、孔与镀通的实际连接规则 | 电气语义 |
| [EX-023](#ex-023) | 圆弧、端帽和近似包络边界的原规则 | 几何语义 |
| [EX-024](#ex-024) | 跨网候选的地面真值与完整 DRC 规则 | 电气验证 |
| [EX-025](#ex-025) | 交互与自动布线的约束及网络状态机 | 工程设计 |
| [EX-026](#ex-026) | 打印、Gerber、钻孔与配套工具的生产语义 | 输出语义 |

### 性能、交互与产品验证

| 编号 | 探索问题 | 类型 |
| --- | --- | --- |
| [EX-027](#ex-027) | 最大板图、索引、编辑历史与网表映射性能 | 规模验证 |
| [EX-028](#ex-028) | 编辑网格、吸附、约束与测量精度契约 | 工程设计 |
| [EX-029](#ex-029) | 正式新增默认策略、统一入口与真实交互验收 | 产品接入 |
| [EX-030](#ex-030) | 载入、确认框与保存的剩余真实重入路径 | 验证缺口 |
| [EX-031](#ex-031) | 900000 mil 极端移动后的可见性与属性 | 验证缺口 |
| [EX-032](#ex-032) | 系统会话结束时未保存文档与后台任务保护 | 平台验证 |
| [EX-033](#ex-033) | NET 迟到结果的有效竞争与候选适用范围 | 并发验证 |
| [EX-034](#ex-034) | 铜分析迟到结果的有效竞争与覆盖失效 | 并发验证 |
| [EX-035](#ex-035) | 真实 Qt／UIA、冷探针时限与完整客户端链 | 运行兼容 |

### 控制运行时、平台与扩展边界

| 编号 | 探索问题 | 类型 |
| --- | --- | --- |
| [EX-036](#ex-036) | 心跳真实滞后、位图上传与诊断开销的因果 | 行为根因 |
| [EX-037](#ex-037) | 不可变图层资源复用的性能与长期稳定性 | 性能验证 |
| [EX-038](#ex-038) | 持续 user 输入事件与非目标前景的来源边界 | 行为根因 |
| [EX-039](#ex-039) | 创建者见证、短命子进程与间歇失败的可证明范围 | 生命周期语义 |
| [EX-040](#ex-040) | 干净 Windows、平台版本与发行依赖矩阵 | 平台验证 |
| [EX-041](#ex-041) | OVR 可达控制流、间接调用与模块职责 | 静态逻辑 |
| [EX-042](#ex-042) | 覆盖保存与扩展写入的身份、原件和冲突策略 | 工程设计 |
| [EX-043](#ex-043) | 走线属性及其它图元编辑的身份与精确写出 | 工程设计 |

## 如何选择下一项

可以立即从离线分析开始的首要项为 [EX-001](#ex-001)，与当前原软件取证主线一致。随后依赖关系为 [EX-004](#ex-004) → [EX-007](#ex-007) → [EX-029](#ex-029)；输入语义 [EX-003](#ex-003)、配置状态 [EX-005](#ex-005) 可先独立收敛。其它事项不按编号代表优先级。

依赖表示完成该事项所需的已有结论；前置未结时仍可领取并开展不依赖它的阅读、静态分析或方案工作，不能越过证据边界宣布闭环。依赖项完成删除后，应将依赖链接改成其结论文档。

## 探索事项

<a id="ex-001"></a>

### EX-001 菜单点击期间的前景、光标与命中窗口变化

- 状态：研究中；负责人：task_3903c40083a3／ctx_cdfee6b64af8；分支：research/ex001-readonly-observer；会话／证据：Pi 01a1cb26-1411-7553-be7e-98cfa74d0e98（deng/gpt-6.1-sol high），Orca 2930bf6d-29b4-46e5-8f58-30f170d8d47c；本工作树 .local-analysis/ex-001/。
- 类型：行为根因。依赖：无，可先独立研究。
- 原文细节：[native-menu-click-audit.md：细节1](native-menu-click-audit.md#explore-ex-001)；[topics/legacy.md：细节2](topics/legacy.md#explore-ex-001)。
- 已知：安装原 AST 已排除 Click 自动乘二；第二槽无父 shell 插入。前景变化只定位到约 0.574 秒采样间隔。
- 要回答：一次公开 Click 内，前景、逻辑／物理光标和命中窗口怎样变化？哪些外部 DPI、API 返回或菜单瞬时状态可观测，哪些仍不能证明实际接收者？
- 完成条件：先离线核验最小只读观测器；再据明确假设取得一次动作的时序与菜单后验，记录已排除解释和剩余边界。证据不足时保留事项，不盲改坐标。

<a id="ex-002"></a>

### EX-002 DOSBox 宿主呈现与客体状态不一致的条件

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：行为根因。依赖：无，可先独立研究。
- 原文细节：[native-startup-diagnosis.md：细节1](native-startup-diagnosis.md#explore-ex-002)；[legacy-menu-runtime-validation.md：细节2](legacy-menu-runtime-validation.md#explore-ex-002)；[legacy-menu-live-verification.md：细节3](legacy-menu-live-verification.md#explore-ex-002)。
- 已知：已有一轮宿主黑底白线而客体图可辨、Enter 后打开 SYN1 的直接证据；不能推广到所有旧失败。
- 要回答：OpenGL／SDL／刷新、输出后端、窗口尺寸和启动阶段分别影响什么？历史黑屏、白横线、surface 残影是否有共同原因？
- 完成条件：复用现有日志与客体／宿主原图，给出可复现的最小单变量解释或明确的适用条件；区分已证现象、因果和无法追溯的历史。

<a id="ex-003"></a>

### EX-003 宿主按键、DOS 鼠标与菜单选择的实际映射

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：输入语义。依赖：无，可先独立研究。
- 原文细节：[native-menu-calibration.md：细节1](native-menu-calibration.md#explore-ex-003)；[legacy-text-screen-retry.md：细节2](legacy-text-screen-retry.md#explore-ex-003)。
- 已知：File 点击已含裁剪原点；小写字符与修饰键走不同通道；主机成功文字不证明 DOS 指针或选择器收到同义事件。
- 要回答：鼠标捕获、INT 33h 坐标、SDL 事件、IME、命名键／Unicode 字符和当前菜单高亮如何影响实际选择？误入 BLOCK 和 Return 差异能否解释？
- 完成条件：对有明确问题的最小动作建立输入通道→客体响应对照，记录坐标、捕获及输入状态；不将回执或时间先后当作送达因果。

<a id="ex-004"></a>

### EX-004 连续两轮真实客体 PNG 的可靠获取

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：验证缺口。依赖：[EX-001](#ex-001)。
- 原文细节：[native-capture-checkpoint.md：细节1](native-capture-checkpoint.md#explore-ex-004)；[native-guest-save-sample.md：细节2](native-guest-save-sample.md#explore-ex-004)；[native-short-observation.md：细节3](native-short-observation.md#explore-ex-004)。
- 已知：旧单张 640×480 客体图存在，但最近两槽 guest PNG 均为 0；公开 Shortcut f11+p 不保持 F11，这个假设已排除。
- 要回答：当前可用的公开 Capture 路径能否连续产生两张新的、可读的客体原图，并证明每张图对应的动作与时刻？
- 完成条件：两轮分别核对捕获动作、文件集合差、唯一新增非空 640×480 PNG、摘要和指定模型实际读图；旧图复读不算新捕获。

<a id="ex-005"></a>

### EX-005 启动配置继承、DFT 和实际工作文件状态

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：配置语义。依赖：无，可先独立研究。
- 原文细节：[legacy-dosbox-configuration.md：细节1](legacy-dosbox-configuration.md#explore-ex-005)；[initial-assessment.md：细节2](initial-assessment.md#explore-ex-005)；[native-created-retry.md：细节3](native-created-retry.md#explore-ex-005)。
- 已知：旧 C21／A240 场景已有文件名和计数证据，不是当前新槽的状态。显式 -conf 的搜索／覆盖／autoexec 继承仍未核定。
- 要回答：固定 DOSBox 版本如何合并配置；DFT 历史路径与命令行如何决定载入文件及默认参数；只读挂载失败是否来自 DOS 打开模式？
- 完成条件：记录有效配置来源和覆盖规则；对具体新场景用日志、Information／Status 文件名和图元计数共同确认状态，区分静态 DFT 内容与实际生效值。

<a id="ex-006"></a>

### EX-006 KEY 宏、Repeat 与 Un-Delete 的上下文调度

- 状态：研究中；负责人：task_97a62f2a4660 / ctx_54f4486b50d7；分支：research/ex006-command-dispatch；会话／证据：Pi 01a1cb42-030b-7113-982d-8f6a4bd79ba1（deng/gpt-6.1-sol，high，本轮用户授权）；本工作树 `.local-analysis/ex-006/`，身份核验 `identity-verification.json`。
- 类型：命令语义。依赖：无，可先独立研究。
- 原文细节：[reverse-architecture.md：细节1](reverse-architecture.md#explore-ex-006)；[legacy-menu-static-validation.md：细节2](legacy-menu-static-validation.md#explore-ex-006)；[legacy-menu-keypath.md：细节3](legacy-menu-keypath.md#explore-ex-006)。
- 已知：MNU／KEY 装载和宏展开已有静态链，默认启用与主循环 Esc 行为已细化；真实宏状态和宿主键码未联合核定。
- 要回答：宏启停、录制、递归限制和上下文如何影响命令？Repeat／Un-Delete 实际重放哪些状态，能否对应新版命令与历史？
- 完成条件：以具体宏或菜单路径交叉验证运行响应及状态条件，沉淀命令调度规则；不重做已确认的 Information／Status 编号。

<a id="ex-007"></a>

### EX-007 原 AUTOTRAX 自建单线保存重开与默认 FT 编码

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：兼容证据。依赖：[EX-003](#ex-003)、[EX-004](#ex-004)、[EX-005](#ex-005)。
- 原文细节：[topics/editing.md：细节1](topics/editing.md#explore-ex-007)；[free-track-creation-design.md：细节2](free-track-creation-design.md#explore-ex-007)；[native-ft-created-roundtrip.md：细节3](native-ft-created-roundtrip.md#explore-ex-007)；[track-explicit-output.md：细节4](track-explicit-output.md#explore-ex-007)；[native-ft-sample-verification.md：细节5](native-ft-sample-verification.md#explore-ex-007)；[free-track-history-core.md：细节6](free-track-history-core.md#explore-ex-007)。
- 已知：内部显式六／七字段编码与新增另存闭环已完成；NEWFT 尚未生成，不能由合成样例推默认值。
- 要回答：原软件在已确认空板、层、宽和端点下新建一条线，实际写出六／七字段、附加值、换行、记录排序和结束布局是什么？
- 完成条件：取得全新 8.3 文件、保存前后图像／参数／日志／摘要及原 AUTOTRAX 重开；按观测范围给出默认策略，不外推到全层或 NETDEF。

<a id="ex-008"></a>

### EX-008 既有 FT 第七附加字段的电气与保存语义

- 状态：研究中；负责人：task_d913518e29a3 / ctx_abb7c92f8325；分支：research/ex008-ft-extra；会话／证据：Pi 01a1cb42-06ef-7017-9f48-3ada4f0d4276，deng/gpt-6.1-sol high（本轮用户授权），本工作树 `.local-analysis/ex-008/`。
- 类型：格式语义。依赖：无，可先独立研究。
- 原文细节：[topics/board.md：细节1](topics/board.md#explore-ex-008)；[copper-analysis.md：细节2](copper-analysis.md#explore-ex-008)。
- 已知：六／七字段均可读取，已有字段原样保留；铜分析对含 extra 的铜走线继续保守拒绝完整覆盖，值为 0 也不例外。
- 要回答：extra 的值域、缺省和存在性分别代表什么？对网络、平面、接触与编辑有什么影响，和原程序新建默认值有何关系？
- 完成条件：用原字节、读写调用或最小原软件对照解释已观察值及缺省，明确未覆盖值的拒绝策略；不能只验证新增缺省就宣布全部语义恢复。

<a id="ex-009"></a>

### EX-009 产品移动／删除及新增输出的原软件兼容

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：兼容证据。依赖：[EX-004](#ex-004)、[EX-005](#ex-005)。
- 原文细节：[pcb-legacy-native-verification.md：细节1](pcb-legacy-native-verification.md#explore-ex-009)；[pcb-mouse-keyboard-verification.md：细节2](pcb-mouse-keyboard-verification.md#explore-ex-009)；[pcb-compat-continuation.md：细节3](pcb-compat-continuation.md#explore-ex-009)。
- 已知：Qt 自重开、原字节保护和原生文件框往返已有证据；原软件打开合成输出及真实输出的完整兼容闭环未过。
- 要回答：AUTOTRAX 是否实际接受产品输出，并保留工作文件、走线数量、移动／删除／新增几何和全部未改对象？
- 完成条件：在隔离副本对照源／输出的文件名、计数、指定几何、未改对象及正常退出。新增部分依赖 EX-007；Qt 自重开不能替代目标验证。

<a id="ex-010"></a>

### EX-010 含 NETDEF 时新增图元的合法布局与网络关系

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：格式语义。依赖：[EX-007](#ex-007)、[EX-021](#ex-021)。
- 原文细节：[track-insertion-plan.md：细节1](track-insertion-plan.md#explore-ex-010)；[pcb-layout-analysis.md：细节2](pcb-layout-analysis.md#explore-ex-010)。
- 已知：解析器能识别尾部及交错 NETDEF；有新增时两种布局都拒绝，候选偏移不是原软件兼容证明。
- 要回答：尾部 NETDEF 前插入 FT 是否被原软件接受？交错布局、记录顺序、节点／附加元数据和新增几何的网络归属有哪些约束？
- 完成条件：分别核定尾部和交错输入，保留网络原字节及语义，给出可支持布局或有证据的拒绝边界；不能用无 NETDEF 单线样例解锁。

<a id="ex-011"></a>

### EX-011 PCB 历史变体与焊盘、坐标、图层的精确几何

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：格式语义。依赖：无，可先独立研究。
- 原文细节：[pcb-readonly.md：细节1](pcb-readonly.md#explore-ex-011)；[topics/board.md：细节2](topics/board.md#explore-ex-011)；[selection-inspector.md：细节3](selection-inspector.md#explore-ex-011)。
- 已知：当前严格支持有限记录和形状；八角／圆角焊盘近似，5／6 靶标等拒绝；保护上限不是原格式上限。
- 要回答：尚未覆盖的记录、层号、精度、坐标范围、旋转／镜像和焊盘形状有哪些真实变体？预览、命中、孔洞与原输出边界如何统一？
- 完成条件：按单图元样例归档字段与几何证据，逐项给出精确公式、支持范围及拒绝样例，不将文本可读或相似预览当兼容完成。

<a id="ex-012"></a>

### EX-012 PCB／LIB／NET 旧代码页与非 ASCII 名称

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：编码语义。依赖：无，可先独立研究。
- 原文细节：[netlist-compatibility.md：细节1](netlist-compatibility.md#explore-ex-012)；[library-analysis.md：细节2](library-analysis.md#explore-ex-012)。
- 已知：PCB／LIB 可保留原字节并提示替代显示；NET 电气名称只接受已确认 ASCII；原软件非 ASCII 文件名未验证。
- 要回答：原文件、DOS 显示、元件／引脚名及 Windows 路径各用什么编码？怎样避免替代字符导致名称误匹配或保存损失？
- 完成条件：用来源明确的字节与目标显示／往返确立各格式编码及错误策略，区分文件内容编码与操作系统路径，不静默猜 UTF-8。

<a id="ex-013"></a>

### EX-013 文字实际导入方向、长度截断与保存往返

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：运行语义。依赖：[EX-004](#ex-004)。
- 原文细节：[legacy-pcb-text-path.md：细节1](legacy-pcb-text-path.md#explore-ex-013)；[legacy-text-copy-verification.md：细节2](legacy-text-copy-verification.md#explore-ex-013)。
- 已知：FS 静态读入上限 80、对象创建上限 32，受控复制已证；DS:d59a 条件映射和方向 32／48 的实际接受未证。
- 要回答：实际导入时坐标／方向变换全局值是什么？33–80 字符是否截到 32；驱动就绪的层校验、方向组合和保存后的字段如何变化？
- 完成条件：对真实载入、属性和保存重开联合核验，记录导入状态、对象字段及长度／方向边界；函数实验不升级为完整运行已过。

<a id="ex-014"></a>

### EX-014 非对称字形、高度量化、字距与旋转镜像

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：运行语义。依赖：[EX-013](#ex-013)。
- 原文细节：[legacy-text-screen-next.md：细节1](legacy-text-screen-next.md#explore-ex-014)；[legacy-text-screen-retry.md：细节2](legacy-text-screen-retry.md#explore-ex-014)；[legacy-text-boundary-verification.md：细节3](legacy-text-boundary-verification.md#explore-ex-014)。
- 已知：解释器机器码矩阵、边界计算与 A240 有限尺标已证；F、251／252、AA／A A 和完整方向矩阵未做实际联合对照。
- 要回答：真实字符笔画端点、字距、空白、负向边界、高度整除和多种镜像是否与静态工具一致？
- 完成条件：以独立尺标、无遮挡客体图和明确文件／对象状态比对代表性变体，说明残差与适用条件，不重复已过函数矩阵代替运行。

<a id="ex-015"></a>

### EX-015 真实缩放、简化字形分派、字体指针与 VGA 像素

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：绘图语义。依赖：[EX-004](#ex-004)。
- 原文细节：[legacy-text-screen-next.md：细节1](legacy-text-screen-next.md#explore-ex-015)；[legacy-text-screen-acceptance.md：细节2](legacy-text-screen-acceptance.md#explore-ex-015)。
- 已知：Zoom 菜单已出现；尺标可估比例，但没有读取内部缩放、实际字体远指针或完整／简化分派。
- 要回答：运行中采用哪张字形表、缩放和绘图路径？线宽、裁剪、像素取整、端帽及替代显示如何决定实际 VGA 图像？
- 完成条件：关联实际缩放动作、运行状态与原生像素，解释完整／简化条件及误差；像素比例估计不冒称内部变量。

<a id="ex-016"></a>

### EX-016 经验证字形接入渲染、命中与铜层的边界

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：工程设计。依赖：[EX-013](#ex-013)、[EX-014](#ex-014)、[EX-015](#ex-015)。
- 原文细节：[legacy-text.md：细节1](legacy-text.md#explore-ex-016)；[copper-coverage.md：细节2](copper-coverage.md#explore-ex-016)。
- 已知：当前文字仍近似显示／选择，字形未接入铜模型；已有中心线与边界工具不能自动证明实际铜覆盖。
- 要回答：应共享哪些文字几何与变换，怎样处理描边、边界模式、未知字符、缓存、命中及铜覆盖，哪些状态必须继续未知？
- 完成条件：沉淀模型与消费者契约、参考结果和支持／拒绝矩阵；实现如在任务范围内，须分别验证显示、命中和铜分析，不能以一项替另一项。

<a id="ex-017"></a>

### EX-017 LIB 目录残留、未分配、别名与保留标志

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：格式语义。依赖：无，可先独立研究。
- 原文细节：[library-analysis.md：细节1](library-analysis.md#explore-ex-017)。
- 已知：四库目录与记录边界已结构核验；FFFF 槽可能残留名称，重复指针／未知标志不预览。
- 要回答：FFFF、保留字段、别名指针和数据残留对应删除、未分配还是历史状态？其他版本目录如何组织？
- 完成条件：用原库操作前后差异或可达读写路径恢复目录状态机和布局，明确安全预览／拒绝规则，不按名称恢复失效槽。

<a id="ex-018"></a>

### EX-018 LIB 图元附加标志、电气意义与原软件预览

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：格式语义。依赖：无，可先独立研究。
- 原文细节：[library-analysis.md：细节1](library-analysis.md#explore-ex-018)；[topics/library.md：细节2](topics/library.md#explore-ex-018)。
- 已知：类型 1–8 和续记录已解释有限布局；类型 8 附加位、平面连接与逐项原软件对照未完成。
- 要回答：库图元层／类型标志、孔与焊盘形状、文字方向及平面连接在原软件中实际代表什么，和 PCB 实例有何差异？
- 完成条件：取得可解释的原库选择／预览或导出对照及字段依据，区分结构通过、视觉和电气语义；未知字段继续保留。

<a id="ex-019"></a>

### EX-019 封装放置、替换及板上元件编辑的实例规则

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：工程设计。依赖：[EX-011](#ex-011)、[EX-018](#ex-018)。
- 原文细节：[topics/library.md：细节1](topics/library.md#explore-ex-019)。
- 已知：库定义和 PCB 实例不能按同名直接覆盖；PCB 内图元是绝对板坐标，主板和库画布隔离。
- 要回答：库局部坐标怎样变换为实例；替换如何保留标号／引脚／已改焊盘；元件移动旋转如何维护身份、网络、历史和原字节？
- 完成条件：给出放置／替换／元件编辑的最小领域契约、冲突与取消规则及可验证样例；只读浏览不能算放置实现。

<a id="ex-020"></a>

### EX-020 LIB 写入、合并和压缩的格式及保留规则

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：工程设计。依赖：[EX-017](#ex-017)、[EX-018](#ex-018)。
- 原文细节：[topics/library.md：细节1](topics/library.md#explore-ex-020)。
- 已知：目前库只读，未引用数据、名称残留、目录和原快照不改写。
- 要回答：增删条目、同名冲突、指针重排、压缩和合并怎样保留未知字段及历史状态；原程序如何重开并解释新库？
- 完成条件：明确新文件写出与原件保护策略、目录／数据不变量、失败语义和原软件往返判据；尚未实现的操作继续标未实现。

<a id="ex-021"></a>

### EX-021 真实 NETDEF、元数据和其他网表语法

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：格式语义。依赖：无，可先独立研究。
- 原文细节：[netlist-compatibility.md：细节1](netlist-compatibility.md#explore-ex-021)；[topics/connectivity.md：细节2](topics/connectivity.md#explore-ex-021)。
- 已知：NETDEF 当前主要依公开结构与合成测试；非嵌套元数据原样保留，不据未知字段推电气属性。
- 要回答：真实原软件生成的 NETDEF 及 NET 变体如何表达节点、元数据、命名和终止边界？与实际引脚／封装声明如何对应？
- 完成条件：取得可追溯真实样例并核定已支持与拒绝语法、元数据意义及映射结果；不能用合成样例证明所有变体。

<a id="ex-022"></a>

### EX-022 铜层、负片平面、孔与镀通的实际连接规则

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：电气语义。依赖：[EX-008](#ex-008)、[EX-018](#ex-018)。
- 原文细节：[copper-analysis.md：细节1](copper-analysis.md#explore-ex-022)；[topics/connectivity.md：细节2](topics/connectivity.md#explore-ex-022)。
- 已知：当前模型是分层几何，贯穿孔按理想镀通假设；9／10 平面、部分 13 层几何、零孔多层焊盘仍不完整。
- 要回答：层号、负片平面、热焊盘、孔环、平面标志及多层对象实际如何导通或隔离？理想镀通假设适用于哪些输入？
- 完成条件：建立来自单图元及网络对照的层／孔／平面规则矩阵，给出覆盖与未知条件；不从图像接触直接推实际电气导通。

<a id="ex-023"></a>

### EX-023 圆弧、端帽和近似包络边界的原规则

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：几何语义。依赖：[EX-011](#ex-011)。
- 原文细节：[copper-arcs.md：细节1](copper-arcs.md#explore-ex-023)；[copper-arcs.md：细节2](copper-arcs.md#explore-ex-023-2)。
- 已知：圆弧象限已有受限内外包络；圆端帽是模型假设，细线大圆弧可能因连续性条件被拒绝。
- 要回答：原 DRC／输出的象限端点、端帽、相切和公差如何定义？当前保护门槛与精确形状之间哪些边界可安全覆盖？
- 完成条件：用独立几何和原软件／输出样例核定代表性边界及公差，记录模型保护条件，不能把内部阈值当原格式尺寸上限。

<a id="ex-024"></a>

### EX-024 跨网候选的地面真值与完整 DRC 规则

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：电气验证。依赖：[EX-008](#ex-008)、[EX-016](#ex-016)、[EX-021](#ex-021)、[EX-022](#ex-022)、[EX-023](#ex-023)。
- 原文细节：[copper-analysis.md：细节1](copper-analysis.md#explore-ex-024)；[topics/connectivity.md：细节2](topics/connectivity.md#explore-ex-024)。
- 已知：真实样例的 21 组跨网接触只是候选，88 网络保持无法确定；完整 DRC 尚未实现。
- 要回答：候选到底是短路、合法连接还是模型／映射差异？完整 DRC 需要哪些电气、间距、层、孔和制造规则及参考结果？
- 完成条件：人工／原软件对照建立候选解释和最小规则集、参考用例与未知传播；将完整性、资源限制和 DRC 通过分开，不能凭 CLI 0 放行。

<a id="ex-025"></a>

### EX-025 交互与自动布线的约束及网络状态机

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：工程设计。依赖：[EX-019](#ex-019)、[EX-024](#ex-024)、[EX-028](#ex-028)。
- 原文细节：[free-track-creation-design.md：细节1](free-track-creation-design.md#explore-ex-025)。
- 已知：内部单段自由 FT 放置存在；折线连续布线、自动避障和网络归属不在首版范围。
- 要回答：原软件走线／自动布线如何处理网格、层切换、过孔、网络、避障、回退、取消和失败；新版最小可验证范围是什么？
- 完成条件：沉淀具体命令与工具状态、几何／电气约束及参考用例，再确定实现边界；不能把可新增一段自由线当布线完成。

<a id="ex-026"></a>

### EX-026 打印、Gerber、钻孔与配套工具的生产语义

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：输出语义。依赖：[EX-011](#ex-011)、[EX-012](#ex-012)、[EX-016](#ex-016)、[EX-022](#ex-022)。
- 原文细节：[initial-assessment.md：细节1](initial-assessment.md#explore-ex-026)；[initial-assessment.md：细节2](initial-assessment.md#explore-ex-026-2)。
- 已知：打印、Gerber／钻孔、GVIEW 等配套工具具体功能和完整生产输出尚未验证。
- 要回答：各工具处理哪些文件与规则；层、极性、单位、孔表、字体和输出设备参数怎样映射为可制造结果？
- 完成条件：先恢复工具／文件／参数关系和最小输出样例，定义独立查看与几何／孔位比对判据；没有证据不宣称生产可用。

<a id="ex-027"></a>

### EX-027 最大板图、索引、编辑历史与网表映射性能

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：规模验证。依赖：无，可先独立研究。
- 原文细节：[measurement-snap.md：细节1](measurement-snap.md#explore-ex-027)；[netlist-compatibility.md：细节2](netlist-compatibility.md#explore-ex-027)；[basic-editing.md：细节3](basic-editing.md#explore-ex-027)；[topics/interaction.md：细节4](topics/interaction.md#explore-ex-027)。
- 已知：已有 12000 候选查询与 200000 走线内存用例，但最大板图真实交互和 UI 线程映射响应性没有基准。
- 要回答：密集同 X 候选、最大记录、Qt 写时复制、重建索引、NET 映射和铜比较上限下，耗时／峰值内存／界面延迟是多少？
- 完成条件：固定输入和机器条件测量代表性／极端分布，分清算法预算与用户响应，按瓶颈给出是否优化及限额依据。

<a id="ex-028"></a>

### EX-028 编辑网格、吸附、约束与测量精度契约

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：工程设计。依赖：无，可先独立研究。
- 原文细节：[measurement-snap.md：细节1](measurement-snap.md#explore-ex-028)；[free-track-creation-design.md：细节2](free-track-creation-design.md#explore-ex-028)；[navigation-measure.md：细节3](navigation-measure.md#explore-ex-028)。
- 已知：只读端点捕捉使用模型坐标；屏幕自由取点存在像素误差；当前新增不隐含取整或网格吸附。
- 要回答：编辑取点怎样从浮点屏幕位置形成明确整数 mil；网格、端点、角度／轴约束的优先级和误差如何告知用户？多段测量、尺寸标注与制造测量应采用哪些模型及精度判据？
- 完成条件：写明取点来源、取整／冲突／取消规则及单位误差判据，用边界样例验证；不能直接将测量浮点坐标送 writer。

<a id="ex-029"></a>

### EX-029 正式新增默认策略、统一入口与真实交互验收

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：产品接入。依赖：[EX-007](#ex-007)、[EX-009](#ex-009)。
- 原文细节：[track-placement-ui.md：细节1](track-placement-ui.md#explore-ex-029)；[track-placement-live-verification.md：细节2](track-placement-live-verification.md#explore-ex-029)；[topics/editing.md：细节3](topics/editing.md#explore-ex-029)；[track-placement-live-verification.md：细节4](track-placement-live-verification.md#explore-ex-029-2)；[parallel-track-native-output.md：细节5](parallel-track-native-output.md#explore-ex-029)。
- 已知：内部身份、预览、提交及显式 MainWindow 另存已实现；唯一正式入口门 false，默认 writer 拒绝 Created。
- 要回答：有证据的默认策略如何接到现有路径；菜单／F3／P→T、文本焦点／IME、隐藏层、取消、历史和原生文件框是否共同成立？
- 完成条件：复用已有模块，明确支持范围后再接唯一能力门；取得正式产品入口和输出重开的真实证据，F3 工具拒绝不当作产品通过。

<a id="ex-030"></a>

### EX-030 载入、确认框与保存的剩余真实重入路径

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：验证缺口。依赖：无，可先独立研究。
- 原文细节：[parallel-save-hardening-live.md：细节1](parallel-save-hardening-live.md#explore-ex-030)；[pcb-save-as.md：细节2](pcb-save-as.md#explore-ex-030)。
- 已知：代次、失败保留和双闸门旧回调已有修复及真实现场；本轮没有重演全部模态重入、同步成功替换与默认拒绝。
- 要回答：嵌套原生框／放弃确认期间同步替换、旧载入返回或修订变化时，当前实际窗口是否始终保留正确文档、历史、busy 和保存点？
- 完成条件：只补未覆盖的具体触发顺序，核对状态和实际窗口证据；已过路径及其它候选的 Created 通过不重复或交叉冒认。

<a id="ex-031"></a>

### EX-031 900000 mil 极端移动后的可见性与属性

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：验证缺口。依赖：无，可先独立研究。
- 原文细节：[basic-editing-remaining-acceptance.md：细节1](basic-editing-remaining-acceptance.md#explore-ex-031)。
- 已知：10000 mil 的远移、reset、属性和历史已有通过；900000 mil 仅提交成功，reset 后亚像素三次未命中，完整属性未验。
- 要回答：极端坐标下视口适配、选择容差、属性定位和历史保持是否可用；需要怎样的可解释定位方式？
- 完成条件：在明确范围内取得极端对象可见／定位及几何属性和撤销重做证据，区分模型正确与可交互性，不从较小位移外推。

<a id="ex-032"></a>

### EX-032 系统会话结束时未保存文档与后台任务保护

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：平台验证。依赖：无，可先独立研究。
- 原文细节：[basic-editing.md：细节1](basic-editing.md#explore-ex-032)。
- 已知：Qt commitDataRequest 接入及标准关窗测试存在；共享宿主未执行注销／关机。
- 要回答：Windows 注销、关机与无交互会话结束时，dirty、后台读取、确认和取消语义是否与设计一致？
- 完成条件：在独立可控环境验证允许／取消／无交互路径及进程退出，不在共享桌面触发破坏性验证；写明系统限制。

<a id="ex-033"></a>

### EX-033 NET 迟到结果的有效竞争与候选适用范围

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：并发验证。依赖：[EX-035](#ex-035)。
- 原文细节：[async-races-adaptive.md：细节1](async-races-adaptive.md#explore-ex-033)；[async-result-boundaries.md：细节2](async-result-boundaries.md#explore-ex-033)。
- 已知：独立实验正向对照已过；自适应竞争虽实际删除但截图拒绝后 cancel，discard 仅证明中止路径。固定候选仍未完整通过。
- 要回答：有效门闩下编辑先发布，随后唯一 release，NET B 旧结果是否按身份／代次丢弃并保留 A；此证据适用于哪个候选？
- 完成条件：取得同应用 worker-entered→gate-ready→document-published→gate-released→worker-returned→callback-discarded 严格时间线及门内／终态真实图；cancel 或事后图不补成通过。

<a id="ex-034"></a>

### EX-034 铜分析迟到结果的有效竞争与覆盖失效

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：并发验证。依赖：[EX-035](#ex-035)。
- 原文细节：[async-races-adaptive.md：细节1](async-races-adaptive.md#explore-ex-034)；[async-gui-recovered-120.md：细节2](async-gui-recovered-120.md#explore-ex-034)。
- 已知：铜正向对照已有；删除后旧铜结果丢弃仅在 aborted 路径观察到，缺有效 release 和门内编辑图。
- 要回答：完整有效竞争中旧板／修订／网表身份结果是否被淘汰，旧铜报告／覆盖诊断是否保持清空？
- 完成条件：独立核定铜工作线程、编辑、有效释放、返回和丢弃的严格时序，结合 dirty／几何／A 来源及最终界面；不由 NET 竞争替铜验收。

<a id="ex-035"></a>

### EX-035 真实 Qt／UIA、冷探针时限与完整客户端链

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：运行兼容。依赖：无，可先独立研究。
- 原文细节：[uia-object-lifecycle-worker.md：细节1](uia-object-lifecycle-worker.md#explore-ex-035)；[async-product-deadlines.md：细节2](async-product-deadlines.md#explore-ex-035)；[async-product-probe-runtime.md：细节3](async-product-probe-runtime.md#explore-ex-035)；[topics/engineering.md：细节4](topics/engineering.md#explore-ex-035)；[async-product-gate-binding.md：细节5](async-product-gate-binding.md#explore-ex-035)；[async-product-drivers.md：细节6](async-product-drivers.md#explore-ex-035)；[async-product-file-dialog.md：细节7](async-product-file-dialog.md#explore-ex-035)。
- 已知：单 UIA 对象严格 COM／原 Popen／原 5 秒限定已过，无 GUI 四身份报告链已过；真实整窗、文件框及完整流程仍 ready_for_live=false。
- 要回答：真实 Qt 控件／owner／焦点／DPI 和默认按钮是否符合严格适配；整窗冷探针及模型读图、编辑、release、失败退出能否满足原预算并完成原创建者见证？
- 完成条件：先做有边界的真实兼容验证再评估竞争准备；保持 5 秒／32 次、20／50／55／60 秒和 600／900 秒原预算，完整审计输入、实际 read、原退出链及失败，不靠加时或降低检查追通过。

<a id="ex-036"></a>

### EX-036 心跳真实滞后、位图上传与诊断开销的因果

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：行为根因。依赖：无，可先独立研究。
- 原文细节：[control-health-validation.md：细节1](control-health-validation.md#explore-ex-036)；[control-upload-offline-analysis.md：细节2](control-upload-offline-analysis.md#explore-ex-036)。
- 已知：原 1 秒阈值下真实 stale／fail-open 已记录；上传累计占时有上下界，不能当 CPU 占比或可节省量。
- 要回答：整轮心跳更新间隔由上传、显示器枚举、消息泵、线程调度及高频日志各贡献多少？哪些截图拒绝与它有直接因果？
- 完成条件：先复用原 trace 离线收敛假设，再按必要最小观测区分原因；不放宽阈值、提前续心跳或关闭指示层掩盖问题。

<a id="ex-037"></a>

### EX-037 不可变图层资源复用的性能与长期稳定性

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：性能验证。依赖：[EX-036](#ex-036)。
- 原文细节：[control-bitmap-surface-live.md：细节1](control-bitmap-surface-live.md#explore-ex-037)；[control-bitmap-surface.md：细节2](control-bitmap-surface.md#explore-ex-037)；[control-diagnostics-tools.md：细节3](control-diagnostics-tools.md#explore-ex-037)。
- 已知：多组单次资源寿命与零账本已有证据；单组 healthy 及 API 次数减少不证明性能倍率、长稳或历史根因修复。
- 要回答：同等负载下资源复用的墙钟、CPU、内存／GDI 常驻成本和长期拒绝率如何；显示器变化、模式切换、线程结束与失败退役是否可靠？
- 完成条件：定义等条件基准及最小寿命／变化／失败场景，分别记录性能、资源和稳定性结论；复用已有单组证据，不重复刷次数。

<a id="ex-038"></a>

### EX-038 持续 user 输入事件与非目标前景的来源边界

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：行为根因。依赖：无，可先独立研究。
- 原文细节：[control-user-timeline.md：细节1](control-user-timeline.md#explore-ex-038)；[basic-editing-remaining-acceptance.md：细节2](basic-editing-remaining-acceptance.md#explore-ex-038)；[desktop-control-recovery.md：细节3](desktop-control-recovery.md#explore-ex-038)。
- 已知：user 的最近事件续期和曾恢复 ready 已证；injected=false 不标识操作者、设备或来源进程。多个旧文件框／前景异常来源未证。
- 要回答：在不更改门禁或干扰他人输入的前提下，哪些设备／进程／事件来源可合法只读观测；怎样区分输入续期、目标激活与其它前景变化？旧 VK192 释放事件为何漏失、保持集合与实际键态何时会分离？
- 完成条件：定义必要且最小的来源观测与证据限度，能解释的事件写结论，不能恢复的旧来源明确不可追溯；不凭日志猜用户或要求关闭未知程序。

<a id="ex-039"></a>

### EX-039 创建者见证、短命子进程与间歇失败的可证明范围

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：生命周期语义。依赖：无，可先独立研究。
- 原文细节：[control-supervisor-local-live.md：细节1](control-supervisor-local-live.md#explore-ex-039)；[control-owned-close.md：细节2](control-owned-close.md#explore-ex-039)；[control-next-stage.md：细节3](control-next-stage.md#explore-ex-039)；[control-supervisor-snapshot-journal.md：细节4](control-supervisor-snapshot-journal.md#explore-ex-039)；[control-close-journal-live.md：细节5](control-close-journal-live.md#explore-ex-039)。
- 已知：已有连续启动器和完整单组原退出链；50 ms 枚举不能排除未知短命子进程。旧退出证据缺失不可事后补造，握手权限及 runner 偶发失败未全部定位。
- 要回答：未来创建链如何在源头完整见证而不靠枚举补证；握手权限错误、账本写盘和 runner 间歇失败的真实条件是什么？
- 完成条件：区分原创建对象与查询句柄的可证明范围，沉淀可重现原因和必要改进；历史无法恢复的 exit 缺口留在原报告，不声称新通过修复旧失败。

<a id="ex-040"></a>

### EX-040 干净 Windows、平台版本与发行依赖矩阵

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：平台验证。依赖：无，可先独立研究。
- 原文细节：[qt-development.md：细节1](qt-development.md#explore-ex-040)；[releases/v0.11.0-alpha.md：细节2](releases/v0.11.0-alpha.md#explore-ex-040)。
- 已知：Qt／运行库和本机移除 SDK PATH 冒烟存在；已发布只读 alpha 与 dev 编辑能力不同，Win10／干净机器未完整验。
- 要回答：锁定 Qt／MSVC 后哪些 Windows 版本、DPI／IME、原生文件框和运行库部署可支持；发布包实际包含哪些已验能力？
- 完成条件：用可追溯包摘要和独立干净环境验证平台／依赖／入口矩阵，明确支持与不支持；更新环境及发布说明，功能与包版本不混同。

<a id="ex-041"></a>

### EX-041 OVR 可达控制流、间接调用与模块职责

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：静态逻辑。依赖：无，可先独立研究。
- 原文细节：[legacy-overlays.md：细节1](legacy-overlays.md#explore-ex-041)；[legacy-menu-static-validation.md：细节2](legacy-menu-static-validation.md#explore-ex-041)。
- 已知：MZ／TPOV 描述符、入口与远调用候选已有只读映射；字节模式不是可达 CFG，间接调用和完整类型未恢复。
- 要回答：为具体功能所需的候选调用是否可达；常驻／覆盖块／GRAPH.DRV 的调用约定与模块状态如何衔接？工具导出缺锚点如何补齐？
- 完成条件：围绕实际消费者补足指令、重定位、调用约定与可达证据，标明间接路径和未知；不以函数识别数或编译器线索声称恢复源码。

<a id="ex-042"></a>

### EX-042 覆盖保存与扩展写入的身份、原件和冲突策略

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：工程设计。依赖：[EX-009](#ex-009)。
- 原文细节：[pcb-save-as.md：细节1](pcb-save-as.md#explore-ex-042)。
- 已知：目前只另存全新文件，不重绑原输入或清历史；Ctrl+S 覆盖未开放。
- 要回答：若扩展覆盖保存，应如何处理来源重绑、保存点、外部文件变化、失败恢复、备份和原子发布，并保持唯一原件保护？
- 完成条件：先形成可评审的保存语义与失败／冲突模型及验证方案；研究结论可明确继续不支持，不能在缺策略时直接打开覆盖入口。

<a id="ex-043"></a>

### EX-043 走线属性及其它图元编辑的身份与精确写出

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：工程设计。依赖：[EX-008](#ex-008)、[EX-011](#ex-011)、[EX-013](#ex-013)。
- 原文细节：[pcb-save-as.md：细节1](pcb-save-as.md#explore-ex-043)。
- 已知：当前仅 Loaded 自由 FT 整体移动／删除及内部 Created；宽、层、extra、其它图元与内嵌网络修改均拒绝。
- 要回答：线宽／层修改、拖拽和焊盘／过孔／圆弧／填充／文字编辑如何维护精确字段、对象身份、历史、网络和失败保护？
- 完成条件：按具体图元定义最小编辑与原字节补丁契约、未解释字段拒绝策略及目标软件往返；不要从近似渲染重建未改原记录。

## 新事项模板

先核对当前清单和 Git 历史，选未使用的编号；填写具体内容并在领取索引中加一行，再给原文细节加回链。模板不是待领取事项。

```markdown
<a id="ex-nnn"></a>

### EX-NNN 具体且能独立回答的问题

- 状态：待领取；负责人：无；分支：无；会话／证据：无。
- 类型：格式语义／行为根因／工程设计／验证缺口。依赖：无，或前置事项／结论链接。
- 原文细节：[报告里的具体段落](某报告.md#稳定锚点)。
- 已知：已有事实及其输入、候选和验证边界。
- 要回答：仍未知的具体工程问题。
- 完成条件：应沉淀的结论、证据和验证。
```
