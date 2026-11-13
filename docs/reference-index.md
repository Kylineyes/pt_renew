# 完整资料索引

[文档导航](README.md) → 软件主题 → 本页专题报告 → 报告中的本机证据。

本页是按问题查询的证据层。先读相应主题的当前结论，再选择字段、实现或验证报告；不要求顺序通读下面的全部记录。原报告按当次版本、固定候选和输入范围解读，旧“下一步”、失败、PID、时段和批准均不自动成为当前状态或新现场依据。

当前状态集中在[PROGRESS](../PROGRESS.md)，接手步骤集中在[HANDOFF](../HANDOFF.md)。桌面控制和异步实验是验证辅助材料，不能与产品功能或原软件兼容验收混为一体。

## 板图与文件

先读[主题概览或接手入口](topics/board.md)。本组 4 篇，以下保留原报告标题。

- [PCB 严格只读核验命令](pcb-check.md)
- [PCB 严格语法布局元数据](pcb-layout-analysis.md)
- [PCB FILE 4 只读解析与显示](pcb-readonly.md)
- [FT 第七字段：读入归一化、保存与预布走线消费者](ft-extra-static-semantics.md)

## 命令、视图与测量

先读[主题概览或接手入口](topics/interaction.md)。本组 4 篇，以下保留原报告标题。

- [两点测量的几何端点捕捉](measurement-snap.md)
- [元件检索、定位与两点只读测量](navigation-measure.md)
- [逆向结构分析与首阶段架构](reverse-architecture.md)
- [只读选择、命中测试与属性查看](selection-inspector.md)

## 编辑、历史与保存

先读[主题概览或接手入口](topics/editing.md)。本组 29 篇，以下保留原报告标题。

- [基础编辑0.11.0真实GUI重新验收](basic-editing-acceptance-retry.md)
- [基础编辑0.11.0独立GUI验收：启动前门禁阻塞](basic-editing-acceptance.md)
- [0.11.0 实际编辑 GUI 验收](basic-editing-actual-edit-acceptance.md)
- [0.11.0 固定候选剩余验收](basic-editing-remaining-acceptance.md)
- [基础编辑最小交付（0.11.0 候选）](basic-editing.md)
- [新增自由走线与工具取消设计](free-track-creation-design.md)
- [自由走线 FT 显式合成编码器](free-track-explicit-codec.md)
- [新增自由走线：身份与编辑历史核心](free-track-history-core.md)
- [主窗显式新增另存现场验收](mainwindow-created-save-live.md)
- [主窗显式新增另存闭环](mainwindow-created-save.md)
- [主窗后台载入生命周期修复](mainwindow-load-lifecycle.md)
- [原生另存与重新打开验证](native-save-roundtrip-verification.md)
- [主窗显式新增另存与保存点集成](parallel-mainwindow-created-save.md)
- [主窗载入生命周期与写出保留：独立现场验收](parallel-save-hardening-live.md)
- [并行修复：载入生命周期与 PCB 写出校验](parallel-save-hardening.md)
- [自由走线前置能力并行开发](parallel-track-foundations.md)
- [新增走线输出与界面接入的并行集成](parallel-track-native-output.md)
- [走线新增预检与提交控制：第二轮并行开发](parallel-track-preflight.md)
- [自由走线编辑与受限另存为独立验收](pcb-save-as-verification.md)
- [自由走线编辑与受限另存为](pcb-save-as.md)
- [PCB 写出边界：精确几何校验](pcb-writer-boundaries.md)
- [独立产品实际键鼠与原生文件框核验](product-mouse-keyboard-verification.md)
- [新增走线内部核心边界审查](track-core-boundary-review.md)
- [显式参数下的新增 FT 输出](track-explicit-output.md)
- [新增自由走线插入预检](track-insertion-plan.md)
- [自由走线放置提交控制器](track-placement-controller.md)
- [走线放置真实窗口验收记录](track-placement-live-verification.md)
- [TrackPlacementSession 放置状态模型](track-placement-session.md)
- [走线放置的主窗与画布接入](track-placement-ui.md)

## 封装库与元件

先读[主题概览或接手入口](topics/library.md)。本组 2 篇，以下保留原报告标题。

- [PCB 4 LIBRARY 二进制分析与只读浏览](library-analysis.md)
- [LIB 目录状态的静态路径与残留边界](library-directory-state.md)

## 网络、铜层与检查

先读[主题概览或接手入口](topics/connectivity.md)。本组 4 篇，以下保留原报告标题。

- [铜层几何连通分析（受限预览）](copper-analysis.md)
- [铜层圆弧分析](copper-arcs.md)
- [铜层覆盖诊断与文字研究](copper-coverage.md)
- [NET / NETDEF 只读兼容与引脚映射](netlist-compatibility.md)

## 原软件行为与兼容研究

先读[主题概览或接手入口](topics/legacy.md)。本组 39 篇，以下保留原报告标题。

- [固定 DOSBox-X 默认配置根与启动守卫静态核验](dosbox-default-roots-static.md)
- [原 PT 的 DFT 载入、历史路径与命令行消费](pt-dft-load-static.md)
- [固定 DOSBox-X 的 Windows／SDL／DOS 输入静态链](legacy-input-event-static.md)
- [历史只读挂载：菜单打开探测与固定 DOSBox-X 拒绝链](legacy-readonly-open-static.md)
- [PT 现状调查与 Windows 迁移建议](initial-assessment.md)
- [DOSBox-X 配置状态、启动顺序与AUTOEXEC聚合登记边界](legacy-dosbox-configuration.md#autoexec-generated-vfile-data)
- [DOSBox 启动日志核验：verification-34](legacy-dosbox-startup-validation.md)
- [原菜单、宏与键盘分派的静态路径](legacy-menu-keypath.md)
- [verification-35：菜单、工作文件名与启动日志现场验证](legacy-menu-live-verification.md)
- [原菜单运行核验与桌面观测诊断](legacy-menu-runtime-validation.md)
- [Information、Status 与 KEY 宏的独立静态复核](legacy-menu-static-validation.md)
- [KEY 宏、Repeat 与 Un-Delete 的静态状态模型](legacy-command-dispatch-static.md)
- [DOS 覆盖模块映射与文字研究入口](legacy-overlays.md)
- [PCB 文字字段到解释器的静态路径](legacy-pcb-text-path.md)
- [原文字形边界计算模式补验](legacy-text-boundary-verification.md)
- [原文字对象创建的 32 字符复制边界验证](legacy-text-copy-verification.md)
- [原文字形的受控机器码交叉验证](legacy-text-machine-verification.md)
- [verification-36：文字属性、计数修正与中断恢复](legacy-text-object-verification.md)
- [原文字形运行对照步骤](legacy-text-runtime.md)
- [原文字形截图现场验收](legacy-text-screen-acceptance.md)
- [原文字形下一现场阶段：无遮挡A、显隐恢复与缩放入口](legacy-text-screen-next.md)
- [原文字形现场重试：A240 与独立尺标](legacy-text-screen-retry.md)
- [原文字形的静态证据与检查工具](legacy-text.md)
- [原软件连续捕获：两轮新客体 PNG、逐图审核与原创建者正常退出](native-capture-checkpoint.md#continuous-capture-conclusion)
- [原软件捕获驱动审查与隔离工具包](native-capture-driver-review.md)
- [原软件单线重试：Return 启动转换及软件输出对照](native-created-retry.md)
- [并行推进与父验收：原软件短观察和新增核心](native-evidence-wave.md)
- [原 AUTOTRAX 新建单线保存重开取证：未完成](native-ft-created-roundtrip.md)
- [原软件单线样例：下一次桌面控制范围](native-ft-sample-control-plan.md)
- [原 AUTOTRAX 单线样例现场核验](native-ft-sample-verification.md)
- [原软件单线样例尝试：客体捕获与投递修复](native-guest-save-sample.md)
- [原 AUTOTRAX 菜单／输入语义与路径隔离事故后的离线预检修复](native-menu-calibration.md#isolation-offline-repair)
- [菜单点击审计、实机短时观测与一次菜单后验](native-menu-click-audit.md#live-menu-conclusion)
- [原软件样例取证与只读 PCB 核验命令](native-sample-wave.md)
- [原 AUTOTRAX 短观察方案与本轮阻塞](native-short-observation.md)
- [原 AUTOTRAX 启动与输入定向诊断](native-startup-diagnosis.md)
- [原软件最小兼容闭环继续核验](pcb-compat-continuation.md)
- [受限另存为的原软件与原生流程后续核验](pcb-legacy-native-verification.md)
- [原 AUTOTRAX 实际鼠标键盘验证](pcb-mouse-keyboard-verification.md)

## 构建与发布

先读[主题概览或接手入口](topics/engineering.md)。本组 4 篇，以下保留原报告标题。

- [Qt 6 开发环境](qt-development.md)
- [v0.11.0-alpha 构建与打包](releases/v0.11.0-alpha-build.md)
- [v0.11.0-alpha Windows 发布包冒烟核验](releases/v0.11.0-alpha-verification.md)
- [PT Renew v0.11.0-alpha](releases/v0.11.0-alpha.md)

## 异步结果与产品验收工具记录

先读[主题概览或接手入口](topics/engineering.md)。本组 20 篇，以下保留原报告标题。

- [独立异步实验构建：NET与铜层结果门闩](async-experiment-development.md)
- [独立异步实验候选GUI验收：受控阻塞](async-experiment-gui-acceptance.md)
- [异步实验接管续验：控制工具持续拒绝](async-experiment-resume.md)
- [控制恢复后的独立异步GUI验收（120秒版）](async-gui-recovered-120.md)
- [归档图片顺序阅读演练：准备阶段未执行](async-image-review-rehearsal.md)
- [批量窗口观察与冷探针预算收敛](async-product-batch-observation.md)
- [有界UIA探针与初始主窗发现](async-product-bounded-probe.md)
- [产品竞争客户端的实现约束](async-product-client-contract.md)
- [产品客户端离线实现与冻结时限](async-product-client-offline.md)
- [原阶段剩余时限、创建者运行器与失败收尾](async-product-deadlines.md)
- [实际兼容性驱动与基础解释器依赖](async-product-drivers.md)
- [产品原始回执与原Popen适配：离线阶段](async-product-evidence-adapters.md)
- [原生NET文件框与原Popen账本离线接入](async-product-file-dialog.md)
- [应用UUID、原门闩与可信窗口的离线接入](async-product-gate-binding.md)
- [探针专用依赖、私有缓存与COM生命周期](async-product-probe-runtime.md)
- [统一产品会话、可见命令与创建者见证](async-product-session.md)
- [产品NET／铜竞争的离线预检](async-race-offline-preflight.md)
- [异步竞争续验：按运行中截图自适应选线](async-races-adaptive.md)
- [异步迟到结果：源码审查与可重复实验协议](async-result-boundaries.md)
- [单次真实UIA对象兼容性核验](async-uia-object-compat.md)

## 桌面控制工具与诊断记录

先读[主题概览或接手入口](topics/engineering.md)。本组 35 篇，以下保留原报告标题。

- [15分钟位图计时有界取证（已许可，现场结束）](control-bitmap-retry-plan.md)
- [位图重试：初始观察通过，首图本地前景拒绝](control-bitmap-retry.md)
- [不可变图层资源复用现场验收记录](control-bitmap-surface-live.md)
- [不可变图层资源复用：原生适配器与待许可现场候选](control-bitmap-surface.md)
- [位图细分取证计划（本轮已许可并结束）](control-bitmap-timing-plan.md)
- [位图上传计时现场：门禁受阻，未进入有效上传路径](control-bitmap-timing.md)
- [监督器快照修复后的完整关闭现场](control-close-journal-live.md)
- [控制诊断工具：当前能力、验证与使用限制](control-diagnostics-tools.md)
- [健康采样验证：采样有效，真实心跳滞后仍未解决](control-health-validation.md)
- [初始原App激活与位图成本取证](control-initial-activation.md)
- [首次真实UIA对象核验failed，代理覆盖已离线修复](control-next-stage.md)
- [健康日志离线重放：多阶段累计覆盖心跳停更区间](control-offline-replay.md)
- [精确自建诊断窗专用关闭：本轮启动失败](control-owned-close-live.md)
- [第三份冻结候选的自建诊断窗关闭现场](control-owned-close-v3-live.md)
- [精确自建诊断窗的专用正常关闭](control-owned-close.md)
- [物理窗口矩形修复与有界诊断组验证](control-physical-geometry.md)
- [遗留自建诊断窗的独立生命周期收尾](control-residual-lifecycle.md)
- [控制工具截图诊断：首次基线在目标恢复阶段受阻](control-snapshot-diagnostics.md)
- [控制工具修复验收：预算恢复生效，App目标恢复仍受阻](control-snapshot-fix.md)
- [直启监督器接入与新候选](control-supervisor-direct-launch.md)
- [直启监督器现场验收的启动前超时记录](control-supervisor-direct-live.md)
- [本机连续启动器真实单组验收](control-supervisor-local-live.md)
- [本机连续启动监督器](control-supervisor-local-runner.md)
- [监督器账本快照失败时保留原进程](control-supervisor-snapshot-journal.md)
- [15分钟初始目标激活与位图计时验证（本次已许可并结束）](control-target-activation-plan.md)
- [初始目标激活：补齐窗口启动到首图之间的前景步骤](control-target-activation.md)
- [最新心跳超时的上传边界与资源复用评估](control-upload-offline-analysis.md)
- [user门禁时间线：空闲计时被新事件续期，曾正常恢复ready](control-user-timeline.md)
- [诊断窗口兼容前置与单组验证](control-window-compat.md)
- [测试窗日志修复与完整回调取证](control-window-logging.md)
- [见证器venv重定向缺口与基础Python直启修正](control-witness-launch.md)
- [桌面控制恢复与旧连接正常退出](desktop-control-recovery.md)
- [单次真实UIA对象兼容性核验：工作者报告](uia-object-compat-worker.md)
- [UIA对象生命周期修复与新单次核验](uia-object-lifecycle-review.md)
- [新单次UIA对象生命周期核验：工作者报告](uia-object-lifecycle-worker.md)

## 探索队列与共识

[工程逻辑探索待办](exploration-backlog.md)列出仍需回答的问题，每项回到本索引报告中的具体细节；原文反向链接到事项。[领取与研究规则](exploration-workflow.md)规定自由扩展阅读、修正文档、追加未知和完成后沉淀删除的流程。两页属于维护入口，不计入上述 141 篇专题报告。

## 增补与追溯规则

新增专题须由对应软件主题链接，并加入本索引的相应分组。一个报告在索引中只归属一个主分组，跨主题关系由主题页链接说明。计划、离线验证、真实现场和综合交接保留原标题及适用范围，不因归组而改判。

本机 .local-analysis/ 的截图、输入副本、会话、摘要和失败材料不在 Git 中。索引只列仓库专题报告；接手状态与本机位置从[唯一交接](../HANDOFF.md#evidence)进入，旧交接全文按[历史追溯说明](../HANDOFF.md#history)查 Git，不保留第二套交接正文，也不为整理重复复制原件。
