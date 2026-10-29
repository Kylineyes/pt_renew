# 产品原始回执与原Popen适配：离线阶段

2026-10-30，从`dev=883f33323b6519e6ea4bb9a2095e0a5277247e9d`建立`feat/async-product-evidence-adapters`。本阶段继续[产品客户端离线核心](async-product-client-offline.md)，增加可信原MCP结果、PNG/region物理坐标、原Popen创建和原句柄身份适配，以及全新的归档图片顺序计时器。模块仍默认禁用，产品启动和桌面请求均0，**ready_for_live=false**。

## 已实现的适配

`tools/async_product_client/transport.py`只接收已建立且以后须冻结的MCP连接对象，不创建服务或连接。调用前沿用共享账本、失败锁存和120秒零桌面请求，限制原工具最多35秒超时并要求schema验证器。只接受明确region的纯图像Snapshot、单次物理坐标Click及Delete/专用收尾Alt+F4；拒绝ControlStatus、Enter、通用文本及额外输入参数。

适配器先记录调用起点，再保存原对象`model_dump(mode='json')`结果和调用终点。原协议使用`is_error`及image的`mime_type`；后续才规范成核心使用的`mimeType`，不接受调用者提交的规范JSON冒充原回执。工具正文错误、缺图/多图、未知类型、错误MIME及传输异常均拒绝，已尝试动作不重发。保存原件不意味着GUI通过。

Snapshot明确把经过前置归属核对的窗口物理rect作为`region`。解析原image的PNG块结构、CRC、IHDR尺寸，并要求回执明确声明相同region及virtual desktop坐标空间，再用实际图像尺寸计算两个方向的倍率。不会将1920×1080全桌面图按产品窗口rect静默映射；不使用DPI逻辑rect。核心`ProductIO.capture`仍核对截图前后精确HWND及物理rect。

只读解析历史最新控制组两份原Snapshot JSON，确认原协议及1920×1080的PNG结构兼容；未实际读图，未把旧全桌面图传给新region接口，更不授予新GUI结论。来源hash和结构核对保存在本机`worker-parent-audit.json`。

`tools/async_product_client/process.py`提供默认禁用的`OwnedProductProcess`创建器。它直接创建产品原Popen，以当前持续存活客户端PID作为实验owner，NET配置skip=1、铜skip=0，固定60000ms看门狗由原实验EXE决定。应用事件目录与stdout/stderr证据目录必须全新且分离。原Popen在任何身份回调前保存，随后`OriginalHandleApi`从该对象的原`_handle`核对GetProcessId、GetProcessTimes及QueryFullProcessImageNameW，不按PID调用OpenProcess，也不创建临时PowerShell持有者。

创建后的身份核验失败时，创建器和核心ProductOwner都继续保留同一原Popen，机会已经消费；不强杀、不重新按PID接管。日志在原Popen实际退出后才关闭，非0退出及失败ID保持。本阶段只用假Popen/API测试这些路径；真实kernel32接口仅在显式调用时加载，未用于产品启动或桌面检查。

这两项是可注入的窄适配，**尚不构成可运行产品现场客户端**。native/UIA精确窗口及模态按钮的可信数据采集、文件框阶段、实验原run UUID与Task上下文的绑定、门闩事件/唯一release和全链监督器接入仍需继续开发。不能仅因为类存在或已复制见证器而宣称全链完成。

## 新归档图片任务的真实失败

使用[orchestration技能](C:/Users/rikideng/.pi/agent/skills/orchestration/SKILL.md)与[orca-cli技能](C:/Users/rikideng/.agents/skills/orca-cli/SKILL.md)，新建独立工作树`Kylineyes/verify-async-image-probe-v2`，原基线883f333。Run `run_e79a93df45bb`、Task `task_70c8976c2e7e`、Dispatch `ctx_1e46f88cbaf6`，使用显式`pi --provider deng --model gpt-6.1-sol --thinking high --no-mcp --no-extensions`启动的新会话。

实际session为`01a188b6-141b-7023-bb48-f7b9d57d707a`。父独立核对原header、环境及12条实际assistant记录，全为`deng/gpt-6.1-sol/high`；不能以Orca model=null或标题代替此证明。本次指定模型能够响应，不能沿用旧模型不可用的原因解释本次失败。

父在执行前冻结11文件的新计时器及两张归档副本，4项契约测试、冻结副本测试及修改后的27项核心测试通过，向用户说明约01:30 UTC+8开始、预计5～10分钟、只读两图且无产品/桌面操作。随后worker预检使用未指定UTF-8的PowerShell Get-Content，中文被错误解码，ConvertFrom-Json报错。错误回执正文明确失败，即使shell的isError=false也不能当通过；空集合manifest_count=0/all_matched=true无效。

遵循本任务“任一步失败立即停止”的具体约束，worker没有执行init/request/read/ack，也没有创建measurement或timing-result。只补充只读诊断，11文件原摘要全部匹配，并提交唯一done `msg_150a1878ddbd`、outcome=failed。父审阅原会话、报告和摘要后验收该失败，ack `delivery_282f92e1bf5d`；worker-release返回external_terminal/retained、processAction=none，reclaimable0。任务已结算，不声称Pi进程退出，不恢复或续投该Task/Dispatch。

本次实际图片read0、request0、ack0，**没有新的读图时序或20/50秒比较结果**。未开始不能等同60秒超时，更不能换算成模型推理耗时。两张图仍分别是历史门闩图和取消后的事后图；没有补记产品GUI通过。旧failed/abandoned任务和旧演练脚本保持只读。

## 新计时器和失败后的修复

`tools/probe_async_images.py`是全新标准库工具，已在上述任务前冻结；支持新目录两图副本、绑定本轮原session、顺序request1→实际read→ack1→request2→实际read→ack2。ack直接调用核心PiReadVerifier核对唯一实际read成功image/hash/模型/session，并记录request1到ack2完整单调时钟区间；即使很快也始终ready_for_live=false。

归档输入与产品Snapshot类型分开。核心验证器保留产品Snapshot的结束时间检查，归档类型不伪造Snapshot工具时间。request必须先持久化，实际read回执必须晚于发布；不接受辅助observed=true。所有证据独占创建，不覆盖旧目录。

本轮任务失败后，在父新分支补入`preflight`子命令：用Python显式UTF-8解析bundle及原会话，检查非空完整文件集合、逐文件摘要、原会话固定路径/header和实际assistant模型/推理强度。空清单、额外/缺失/改变文件和身份错误均不能发布preflight成功。此修复未写回已结算worker冻结目录，也未重跑其失败任务。测试使用中文路径、中文JSON和坏清单回归；以后若另行授权新的具体读图任务，应先冻结修复版并使用新上下文。

## 验证和交付边界

新测试仅用合成PNG、临时原会话JSONL、假MCP/Popen/API和假时钟，不启动产品或输入钩子。覆盖原协议字段、PNG/CRC/尺寸、region/物理倍率、错误正文/无image、默认禁用/schema/时限/未知调用、owner/原Popen对象/创建后身份失败、显式UTF-8预检和严格顺序计时。早期计时器开发时出现多余括号和归档类型误依赖Snapshot结束字段，修复后测试通过；原失败日志保留，不伪称首次即成功。

新增`tests/test_async_product_adapters.py` **14项**、`tests/test_probe_async_images.py` **6项**，本阶段共**20项新增测试通过**；仓库Python全集**254项通过，20.816秒**，见[最终测试日志](../.local-analysis/async-product-evidence-adapters/tests-all-final.log)。本阶段还核对了10组旧参考摘要不变（实验22、稳定22、固定23、旧对照9/竞争14/输入3、最新控制278/worker归档216、实验src45/tests13），见[只读基线](../.local-analysis/async-product-evidence-adapters/readonly-before.json)。这些结果不替代Qt GUI或实际模型读图。

后续仍先完善native/UIA、文件框和门闩/全链接入，冻结新版本并离线回归。指定模型实际两图read时序尚未取得，原20/50/55/60秒门槛与35/5/40秒正常退出余量、失败120秒零桌面请求保持。必要控制授权持续，新现场前完成可审阅材料并说明实际开始时间、预计时长与范围；当前不安排产品现场，不重跑已成功控制诊断组。
