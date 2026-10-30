# 新单次UIA对象生命周期核验：工作者报告

本轮结论：**succeeded，仅本组UIA对象生命周期与原5秒关口通过**。新冻结唯一入口执行一次，直接持有的原Popen与实际子PID一致、原退出0；原COM调用严格为两次`CoInitializeEx`、一次`CoInitialize`和三次`CoUninitialize`，同线程返回、余额归零、清理完成且无清理异常。最终`accepted=true`，`ready_for_live=false`、`qt_verified=false`；不代表Qt、整窗UIA、GUI或产品全动作时限通过。

## 身份、范围与阶段一

- Task：`task_49c2158f60ce`；Dispatch：`ctx_15cecb4855e4`；Orca Run：`run_95717b0022a0`。
- 工作者终端：`term_07f77bcd-f73a-4897-a22a-4e6df9d6063e`；协调者：`term_ad3c37b1-ff0d-4026-92ca-2c46ba148798`。
- 实际环境及原Pi JSONL均为`deng/gpt-6.1-sol high`，session为`1ad5d64c-f53d-4a80-8a0c-d97720126a8b`，没有切换模型或会话。
- 独立分支：`verify/uia-object-lifecycle`；起点：`1789c328639181dc29508e3610448f029721237a`。只提交本报告，不合并dev/main、不推送；父实现文件未编辑。
- 本树证据根：`C:/Users/rikideng/orca/workspaces/pt_renew/verify-uia-object-lifecycle/.local-analysis/uia-object-lifecycle/`，不提交。
- 原session：该证据根下`sessions/2026-10-30T15-44-16-063Z_1ad5d64c-f53d-4a80-8a0c-d97720126a8b.jsonl`。
- 批准绑定的已读取原前缀：178383字节，SHA256=`89a8b9154541fc1bfc01f0e851d213436a9f714c55ad8a25cf64b43a7ab9906f`；执行前后均重新只读核对。身份与当前可用工具列表记录于`worker-identity.json`。

完整读取本树`AGENTS.md`及父`docs/agent-handoff-20261030-uia.md`、`docs/async-uia-object-compat.md`、`docs/uia-object-compat-worker.md`。静态审阅父`com_apartment.py`、`uia_object.py`、`probe_async_uia_object.py`、`run_async_uia_object.py`和`tests/test_async_product_probe_runtime.py`；另读`core.py`、`probe_workspace.py`核对截止及依赖审计。

父COM修改覆盖了普通回调失败后继续清理已知余额、原释放结果未知不重试、清理异常不报告balanced及core部分导入不阻断已知清理。阶段一发现两条最终回执缺口：进入finally前过期可能只得到accepted=false而未锁存failed/120秒，最终回执写盘异常也可能跳过统一收尾；prepared消息为`msg_9d6aa8d5b3f4`，原阻塞ask为`msg_84b1d73835a1`。父接受并离线修复，未修改旧失败组或活进程。

父新增`finalize`后，完整只读复审最新runner和`tests/test_async_uia_object.py`。最终回执前超时、写盘越时及写盘异常统一锁存首次失败；失败审计盘不可写及拒绝回执不可写仍完整本地120秒收尾，保留原Popen/token/截止。六模式假回归与首次失败、未知Popen覆盖与实现对应，补审消息为`msg_83bdcf891f41`；随后通过新ask取得最终材料。未知初始化或释放边界继续按unknown解释，不视作平衡。阶段一没有创建UIA或握手子进程、没有导入windows_mcp/comtypes或查询桌面。

## 最终批准与冻结

父范围批准消息：`msg_0f34cb968233`；新ask最终回复明确允许本Task/Dispatch唯一对象执行。计划2026-10-31 00:10（UTC+8）开始，整体预计3分钟；最终回复允许材料收到较晚时核对后按实际起止记录，不重置截止。对象上下文`run_id=b5625b21-68d1-4ed4-8537-2fae9992da5d`，与Orca Run分别记录。

父材料根：`C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/uia-object-lifecycle-review/`。

| 材料 | SHA256 |
| --- | --- |
| `frozen-final/frozen-manifest.json` | `f2514ebdd8e1daa57ac62e2703d8b088e98d27d2f443a277943a4d88963eef7e` |
| `live-materials/configuration.json` | `e38cc6c45e970a2820238d24d1b6e78be07d0bb67e850dd2d6507156bcff62cb` |
| `live-materials/approval.json` | `cb711f5486ff7da82d224c823a90cd73f7b689369966b88c220b0cdd18b3855f` |

执行前只读核对完整candidate **6623文件**及每个摘要、完整77文件原包、156文件探针模板、指定六份已审源码与冻结一致；基础Python SHA256为`1b276111176d62c944c84ccffc25aa1b861d45fea27131a4c31326ed5c0fb417`。批准、配置、本轮上下文、实际Pi环境及原会话前缀一致，输出根尚不存在。

唯一冻结入口命令为：

```powershell
& 'C:/Users/rikideng/scoop/persist/uv/python/versions/cpython-3.14.8-windows-x86_64-none/python.exe' -B -X utf8 'C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/uia-object-lifecycle-review/frozen-final/candidate/tools/run_async_uia_object.py' 'C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/uia-object-lifecycle-review/live-materials/configuration.json'
```

本树新建标准库`execute_once.py`仅一次直接调用上述argv并等待原runner，stdout/stderr原字节直接保存到二进制文件，没有PowerShell管道转码。该包装器不导入UIA、不查询桌面、不启动产品或服务；runner只直接创建一个UIA对象基础Python子进程。没有执行旧准备脚本或第二组入口。

## 原Popen与严格COM

工具实际起止：**2026-10-31 00:13:40.281170～00:13:41.598159（UTC+8）**，累计**1.3169555秒**，原runner PID42080、退出0；`tool-execution.json`保存原argv、起止、退出及原字节输出摘要。

UIA原Popen由冻结runner直接持有，身份为：PID **35196**，birth **134378504205474034**，handle **352**，`original_handle=true`，映像为上述冻结基础Python。子结果PID同为35196，父原对象poll取得退出码0。工作者只审计创建者证据，不冒称自己持有该UIA子Popen，也没有通过PID补建句柄或重新查询进程。

子记录：`completed=true`、`object_created=true`、`object_creations=1`，原类型为`POINTER(IUIAutomation)`及`POINTER(IUIAutomationTreeWalker)`。实际导入源均在本轮candidate的`runtime/windows_mcp/uia/`；入口读取类定义已创建的原`_AutomationClient._instance`，没有再次调用instance。

| 次序 | API | 原返回值 | 余额 |
| --- | --- | --- | ---: |
| 1 | `CoInitializeEx` | HRESULT 0 | 1 |
| 2 | `CoInitializeEx` | HRESULT 1 | 2 |
| 3 | `CoInitialize` | HRESULT 1 | 3 |
| 4 | `CoUninitialize` | null | 2 |
| 5 | `CoUninitialize` | null | 1 |
| 6 | `CoUninitialize` | null | 0 |

独立逐条重算确认六条均在线程**30664**正常返回，严格计数2/1/3、顺序与余额一致。`cleanup_completed=true`、`cleanup_errors=[]`、`balanced=true`；没有未知释放或清理异常，也没有未知在途对象需要保留创建者。

## 原5秒与预算

- 原runner起点：`7401247122600 ns`；诊断截止`8001247122600 ns`，收尾截止`8301247122600 ns`，严格分别为原600/900秒。
- 原对象父预检起点：`7401253993800 ns`；原5秒截止：`7406253993800 ns`，未从request、ready、子入口或回执重计。
- 子执行自身约**0.776352秒**；原父预检到子结果结束约**0.9714317秒**。
- 原父预检到最终报告记录约**1.0972397秒**；原父预检到包装器观察runner退出约**1.1150096秒**，仍在同一原5秒内。runner退出之前已完成预检、原对象创建/清理/退出、父验收、回执和最终落盘；`write_once`使用flush/fsync后原子发布。
- 父账本仅`object-start`、`object-finish`、`object-settle`三个顺序请求，全部时间在原截止内；最终`failed_id=null`、`failure=null`、`not_before_ns=0`、token=`object-settle`。

本组没有触发失败或超时，故没有新增120秒冷却；`failure.json`、`final-result-rejected.json`、`deadline-unknown.json`和stop标记均不存在。没有重试、换入口、清除failed/token/截止、强杀或采纳迟到成功。

## 执行后核对与唯一入口证据

`pre-execution-verification.json`和`post-execution-verification.json`确认全部6623文件集合及摘要完全一致，manifest、配置和批准原字节摘要未变。私有`execution/object-probe/runtime/dependencies`完整**156文件**与冻结探针模板逐字一致，无缺失或额外可执行文件。私有temp仅零字节`comtypes-gen-390be1ea2d17150e5ebb1bc0f6b95a3e.lock`，SHA256为`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

原JSONL已读取执行审计前缀**382479字节**，SHA256=`2f151b9a6a927d3eda5c64a0cdaec4161a01ef731651c74430acfe344929d011`，副本为`session-execution-audit-prefix.jsonl`。解析实际assistant模型、模型切换和推理记录，唯一执行工具调用及对应原成功回执保存于`independent-execution-audit.json`；仅有一次调用`execute_once.py`的PowerShell工具，包装器的唯一冻结argv与本轮批准对应。原会话继续追加，以上摘要只绑定已读取前缀。

runner stdout为860字节、stderr为0；UIA子stdout/stderr均为0。原字节保存在`runner-stdout.bin`、`runner-stderr.bin`和`execution/object-probe/{stdout,stderr}.log`，未经过PowerShell转UTF-16。

本轮没有输出完整运行时DLL加载遥测；未补做native枚举，也不声称额外DLL加载为零。阶段一代码缺口由父离线修复，本工作者未修改父源码或任何旧Task、批准、冻结、输出、时钟与worker证据。

## 结论边界与证据入口

实际窗口/桌面枚举及查询、事件订阅、截图、输入钩子、键鼠、PT产品、控制服务和NET/铜竞争均0，`max_product_launches=0`、`ready_for_live=false`。本组成功证明当前冻结及当前运行中的原对象创建、严格COM清理、原Popen退出0和原5秒关口；Qt主窗、整窗UIA双轮、文件框、GUI兼容性、真实产品全动作预算及完整竞争仍未验证，本工作者未进入下一现场阶段。

关键证据位于本树`.local-analysis/uia-object-lifecycle/`：`worker-identity.json`、`static-review.md`、`static-rereview.md`、前后摘要核对、`tool-execution.json`、`independent-execution-audit.json`和`execution/`原请求/子结果/账本/verified/final-result。报告可由父独立审计整合；下一阶段范围及新批准由父另行组织。
