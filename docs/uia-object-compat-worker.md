# 单次真实UIA对象兼容性核验：工作者报告

本轮结论：**failed**。唯一冻结入口执行一次，子进程创建了原UIA单例，但COM清单缺少要求中的原UIA `CoInitialize`，严格三次初始化与三次释放验收拒绝；原子进程退出1，父`accepted=false`，`ready_for_live=false`。首次失败、原token、原截止及全部原始证据保持，不修复、不重试、不采纳迟到结果。

## 本轮身份与准备

- Task：`task_d3f457a86360`；Dispatch：`ctx_d507e4b3f6a7`。
- 工作者终端：`term_ebd28cfb-6b5c-49ee-8869-13f33d108618`；父协调器：`term_9d0abe4f-d0dd-43f9-84b5-a81ddf9560a1`。
- 实际环境与原JSONL均为Pi `deng/gpt-6.1-sol high`，session `a8e82af0-6b64-4f65-bcce-51e8afec9ee2`；未切换模型或会话。
- 独立分支：`Kylineyes/verify-uia-object-compat`；准备时HEAD：`462bc5654842a1b221b1999a9f6e2d939ec5c264`，工作区干净。只提交本报告，不合并或推送。
- 当前工作树证据目录：`.local-analysis/uia-object-compat/`；证据不提交。
- 原session JSONL：`.local-analysis/uia-object-compat/sessions/2026-10-30T09-17-37-910Z_a8e82af0-6b64-4f65-bcce-51e8afec9ee2.jsonl`。
- 已绑定前缀101727字节，SHA256为`96a0b8b220b2760d4949e581701a0b99cca89cf20eab73c3e75bcd70c3a396f5`；执行前再次复核相同。JSONL持续追加，摘要只绑定该已读取前缀。

完整读取当前`AGENTS.md`、父`docs/async-product-probe-runtime.md`及父`.local-analysis/async-product-probe-runtime/NEXT_AGENT_BRIEF.md`，静态审阅父指定的对象核验代码。准备消息`msg_841d1fea90ca`后，通过原阻塞问题`msg_3a52f1488cba`等待最终冻结材料；未先创建握手或UIA子进程。父批准消息为`msg_28824f39bc02`，其原ask最终回复给出唯一入口和具体时间，执行前后及结算前检查父补充消息。

## 冻结与唯一执行

父材料位于`C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/async-product-uia-compat/`。完整candidate文件集合及每个摘要执行前后均只读核对通过，共6622文件；基础解释器SHA256为`1b276111176d62c944c84ccffc25aa1b861d45fea27131a4c31326ed5c0fb417`。

| 材料 | SHA256 |
| --- | --- |
| `frozen-prelive/frozen-manifest.json` | `2d0775d17331c92cc386cbdd8064f2438ccaae5a6c14a4b8bc4c343483551543` |
| `live-materials/configuration.json` | `454afe86a2b18cf0c8e462eea34a3cff6db9039f401c6da318fa2b506f385ac6` |
| `live-materials/approval.json` | `03364033c939fa43f4dd1296789ee03d992692f42f5431e84a5d33272e79d72a` |

执行上下文中的对象核验`run_id`为`b934ad73-f692-4eb9-9f60-d3dc430b6b0d`；与Orca消息Run `run_0db66155091d`分别记录，未混用。配置、批准、本轮Task/Dispatch及当前Pi身份一致。输出目录执行前不存在。

仅运行一次父指定的基础Python入口：

```powershell
& 'C:/Users/rikideng/scoop/persist/uv/python/versions/cpython-3.14.8-windows-x86_64-none/python.exe' -B -X utf8 'C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/async-product-uia-compat/frozen-prelive/candidate/tools/run_async_uia_object.py' 'C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/async-product-uia-compat/live-materials/configuration.json'
```

计划时间17:58（UTC+8），最终回复允许收到晚于该时间时按实际记录。原工具实际起止为2026-10-30 **18:03:07.5576101～18:05:08.5841699（UTC+8）**，入口退出1；没有第二次调用。原工具记录为`tool-execution.json`。

## 原对象、首次错误与COM证据

父直接持有的原`Popen`创建身份：PID **72256**，birth **134378281877983799**，handle **200**，`original_handle=true`，映像为上述冻结基础Python。原对象poll取得退出码**1**；没有未知在途子进程，也未强杀或另查PID替代原句柄。

子结果`execution/object-probe/object-result.json`记录：`object_created=true`、`object_creations=1`，类型分别为`POINTER(IUIAutomation)`和`POINTER(IUIAutomationTreeWalker)`，实际来源为冻结candidate的`runtime/windows_mcp/uia/__init__.py`和`uia/core.py`。没有第二次调用`instance()`。

原COM清单均在线程7676返回：

| 次序 | 原记录API | 返回值 | 记录余额 |
| --- | --- | --- | ---: |
| 1 | `CoInitializeEx` | HRESULT 0 | 1 |
| 2 | `CoInitializeEx` | HRESULT 1 | 2 |
| 3 | `CoUninitialize` | null | 1 |
| 4 | `CoUninitialize` | null | 0 |

独立重算确认这四条记录线程、顺序和余额一致，但**没有`CoInitialize`记录，只有两次初始化和两次释放**。不得把`balanced=true`或记录余额0当作全部实际COM调用已平衡的证据。

首次子端原始错误为`ValueError: 真实UIA对象必须有显式/自动/原UIA三次成功初始化和三次释放`，`completed=false`。父随后因原退出1拒绝，原始错误为`ValueError: 原UIA核验尚未退出0或缺创建时身份`；`failure.json`保存`failed_id=object-finish`、`token=object-start`、`accepted=false`。身份已经存在，该父错误文本为共享条件提示，不代表身份缺失。

静态源码显示`core.py:46`的`from .enums import *`可能将`enums.py`导出的原`ctypes`覆盖模块局部代理，随后`core.py:64`的原`CoInitialize`调用因此可能逃过计数；父补充消息`msg_6528e59d89cd`提出相同怀疑，并要求只按首次失败结算。此为源码推断，没有新增现场验证；修复归父，本轮candidate与失败不得修改。

## 原截止、停止与120秒收尾

- 原runner起点：`1011645419235600 ns`；600/900秒预算从此起算，未重置。
- 原父探针预检起点：`1011645424798700 ns`；原5秒截止：`1011650424798700 ns`。
- 子从execute入口到首次错误结束约**0.554735秒**；从原父预检起点到子结束约**0.7160602秒**。
- 父首次拒绝约在原父预检起点后**0.7516047秒**；不是5秒超时，不因较快返回而改判通过。
- 原`not_before_ns=1011766176401300`，最终`finished_ns=1011766267838200`；首次父失败日志到最终记录约**120.0914348秒**，runner累计**120.8486028秒**。
- 父在原退出1后进入冷却，无需写stop标记，原`stop_requested=false`且没有`stop-requested`文件；未伪造停止请求或清除失败。

入口在冷却期间只持有/轮询原对象，没有新UIA/native/状态/截图/输入。本工作者等待原工具返回后才读取新本地日志；没有重试、换入口、修复冻结或运行旧演练。`verified.json`不存在，无迟到成功接收；最终结果仍`accepted=false`。

## 摘要与加载证据边界

执行前`pre-execution-verification.json`和执行后`post-execution-verification.json`确认完整candidate6622文件集合及摘要均未改变，配置、批准和manifest摘要相同。私有`runtime/dependencies`完整156文件与冻结探针模板逐字相同，无缺少或额外文件；原UIA包77文件与完整服务依赖亦包含在全candidate复核中。

私有`runtime/temp`只有零字节`comtypes-gen-390be1ea2d17150e5ebb1bc0f6b95a3e.lock`，SHA256为`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。未重生成或修改可执行依赖；stdout/stderr均为空。

本次入口没有输出运行时DLL加载清单，不补做native枚举。静态源码可见原对象通过`safe_get_module("UIAutomationCore.dll")`访问类型库，导入过程还取`user32/gdi32/kernel32/ntdll`符号并加载COM支持；这些源码事实不能充当完整运行时加载遥测，也不能声称额外DLL加载为零。未安装额外依赖或启动额外服务。

本轮实际产品、控制服务、窗口或桌面查询、事件订阅、截图、输入均0；没有NET/铜新竞争，也未恢复旧Task/Dispatch/批准/失败/abandoned或旧演练。对象创建曾成功，但**本组生命周期验收未通过**；Qt、完整冷探针、UIA属性/read、GUI、完整产品动作及竞争均未验收，`ready_for_live=false`。

关键本地证据为`worker-identity.json`、`pre-execution-verification.json`、`tool-execution.json`、`post-execution-verification.json`及`execution/`下原请求、子结果、原父账本、失败和最终结果。实现修复、后续任何新验收与结算释放均由父协调器负责。
