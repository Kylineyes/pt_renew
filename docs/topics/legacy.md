# 原软件行为与兼容研究

[文档导航](../README.md) · [当前阻塞](../../PROGRESS.md) · [完整资料索引](../reference-index.md)

## 先看结论

原 AUTOTRAX 的菜单、覆盖模块、文字解释路径和部分运行行为已有证据。原软件自建单段 FT 保存重开及其默认字段仍未核定；[一次菜单时序与真实后验](../native-menu-click-audit.md#live-menu-conclusion)已在新槽取得，旧终端前景事故的触发者仍不可追溯。正式新增继续等待原软件保存重开等证据。

## 第一层分析：围绕具体软件行为提问

| 软件部分 | 要回答的问题 | 当前依据 |
| --- | --- | --- |
| 启动与默认配置 | 真正载入哪个文件、采用什么参数？ | 配置／日志及 Information / Status；历史 DFT 路径不能照搬 |
| 菜单与键盘 | 菜单字段、宏、按键序列如何调度？ | [宏与命令状态模型](../legacy-command-dispatch-static.md)、[Shortcut原AST的VK／Unicode分流与IME边界](../native-menu-calibration.md#shortcut-offline-semantics)、MNU / KEY及局部现场 |
| 文件新增与保存 | 新 FT 的宽、层、extra、换行和布局是什么？ | 默认策略仍缺自建单线的保存重开证据 |
| 文字 | 字符如何产生中心线、方向、边界和像素？ | 静态路径、受控机器码、A240 局部现场，整体 runtime_verified=false |
| 模块 | EXE、OVR 和配套输出工具如何分工？ | MZ / TPOV 结构与调用候选，未恢复完整源码 |

先定义待确认的行为，再选静态、函数级或现场方法；不因工具可用就泛化为整个软件已经逆向完成。

## 第二层分析：证据怎样逐步加强

静态字段与调用路径 → 受控函数实验 → 实际启动及当前文件状态 → 可重复单动作 → 保存字节与重开。前一层帮助设计后一层，不能提前给出后一层的结论。[EX-006 静态状态模型](../legacy-command-dispatch-static.md) 已补齐宏队列、放置模板和删除链的调用依据，运行响应仍待核定。

文字已有 21792 组合与 105504 中心线的函数级交叉验证、1458 例边界补验、16 例创建复制验证；无遮挡 A240 和层隐藏／恢复有局部现场证据。它们没有完成所有高度、方向、真实缩放、导入状态、VGA 像素与保存的联合对照，字形仍未进入 Qt 或铜分析。

原软件写入测试只使用隔离副本，原件和冻结失败材料保持只读。字段语法观察用 pt-pcb-check 核对；它不会替原 AUTOTRAX 判断是否兼容。

## 第三层分析：当前 FT 取证卡在哪里

两槽均未完成连续客体捕获，guest PNG 为 0、NEWFT 未产生。首槽 Click 前因终端前景拒绝；第二槽确实发送 Click(545,160)，但后图是终端前景且没有菜单后验。

<a id="explore-ex-001"></a>

历史[离线点击审计](../native-menu-click-audit.md)已对齐原图、裁剪、RPC、原生窗口和父原会话：安装函数不自动乘二，父聚焦后无 shell 插入，旧前景变化限定在约 0.574 秒采样间隔内。后续[新槽实机结论](../native-menu-click-audit.md#live-menu-conclusion)已补齐33样本兼容及真实线程结束、189样本单Click时序和Capture菜单原图；该次前景稳定、逻辑／物理光标到达请求点，并由原创建者正常wait0。旧触发者仍不可恢复，来源观测边界进入已有EX-038；不把本次通过外推旧因果、真实接收者或全部DPI兼容。公开 Shortcut f11+p 仍是释放 F11 后发字符 p，不能当保持 F11 的组合使用。

[一次菜单观测结论及后续消费者边界](../native-menu-click-audit.md#live-menu-conclusion)。

本页及历史报告都不是新现场的可直接执行批准。新槽须绑定实际身份、当下截图、冻结输入和明确时段，沿用公开控制门、单操作者、失败静默及原 owner 正常退出约束；详细现场约定见[统一交接](../../HANDOFF.md#evidence)。

## 下一步怎样推进

当前[路径隔离事故后的离线修复与合成回归](../native-menu-calibration.md#isolation-offline-repair)已审查集成并在协调树28项复测通过：配置按语义重建、逻辑／物理归属、联接／硬链接及实际创建前拒绝门已纳入工具；这不恢复旧日志、不使前三槽合法，也不是EX-003运行条件闭环。本轮暂停现场与归档精简，后续步骤只作依赖顺序，不据旧GO执行。

1. [两轮新客体 PNG 及真实逐图读取](../native-capture-checkpoint.md#continuous-capture-conclusion)已完成，四组原创建链正常wait0；复用此有限结论和当前图方式，不复用已退出槽、旧GO或坐标。
2. 两轮捕获结论中的客体均为启动页；后续[第八固定场景](../legacy-dosbox-configuration.md#eighth-status-conclusion)已逐新图直接取得SYN1.PCB／Tracks5／其余七类0、Information首行Up→Status与唯一Esc，原四wait及join正常。旧Shift+I后IME候选与失败仍保留；[输入静态链](../legacy-input-event-static.md#remaining-unknowns)只定位通道和守卫，不恢复当时消息／IME状态或INT33。EX-003／005整体仍未结。
3. 固定GUI状态不等空板或默认FT字段已证；后续自建单线、保存全新8.3文件须另获明确范围并审新候选／GO，本轮没有EX-007授权。
4. 原 AUTOTRAX 重开、图像、字节、日志及摘要共同核定字段，再交[编辑主题](editing.md)接通正式产品。

## 按需深入

- [配置parser、Property写值与autoexec文本](../legacy-dosbox-configuration.md#fixed-config-parser-setter)：文件登记、共同读终止返回、转换失败／回退赋值／范围截限分开；同对象追加与阶段清文本不等于最终执行，特殊输入和回调效果仍缺。
- [autoexec初始化取样、自有复制与本地开关门](../legacy-dosbox-configuration.md#autoexec-initial-consumer)：securemode先保存、noautoexec后读取，跳过Section内容段不等于禁止全部来源；后续[BOOT调用与动态槽](../legacy-dosbox-configuration.md#autoexec-boot-upstream)已补同表安装／派发，最终解析到消费的连续时序与DOS执行仍缺。
- [默认配置根、三阶段守卫与八候选](../dosbox-default-roots-static.md#final-explicit-and-eight)：已打开登记不等所有属性有效，cwd与特殊开关按阶段核。
- [DFT工作名恢复与命令行优先关系](../pt-dft-load-static.md#working-name-and-cli)：WD1EL为Block Read记忆名，POWER3恢复有守卫；原DFT内容不补为第八生效值。
- [Windows／SDL／DOS输入链及剩余边界](../legacy-input-event-static.md#remaining-unknowns)：有条件ImmDisableIME及返回未查、扫描码与文本双通道已定位，旧消息／实际绑定／完整IRQ-PT与INT33仍缺。
- [历史只读挂载的条件性打开／拒绝链](../legacy-readonly-open-static.md#conclusion-and-limits)：Reset模式映像初值2与DOSBox-X只读拒绝已静态核定，历史实际调用状态仍未知，不能宣布唯一根因。
- [首次软件调查](../initial-assessment.md)、[覆盖模块](../legacy-overlays.md)。
- [文字静态路径](../legacy-text.md)、[机器码核验](../legacy-text-machine-verification.md)、[无遮挡现场](../legacy-text-screen-next.md)。
- [两槽与输入语义](../native-capture-checkpoint.md)、[驱动审查](../native-capture-driver-review.md)、[最新点击审计](../native-menu-click-audit.md)。
- 其余文字、菜单、启动和原 FT 尝试按问题查[完整索引](../reference-index.md)。
