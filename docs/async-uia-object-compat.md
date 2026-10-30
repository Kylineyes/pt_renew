# 单次真实UIA对象兼容性核验

从 `dev=462bc5654842a1b221b1999a9f6e2d939ec5c264` 建立独立分支 `feat/async-product-uia-compat`。本阶段接续[探针运行时](async-product-probe-runtime.md)，准备并执行单次UIA自动化对象兼容性核验；最终实际结果及范围由本机证据记录，不以工具存在或假测试通过当现场成功。`ready_for_live=false`，PT产品、控制服务、窗口/桌面查询、截图和输入不在本次执行范围。

## 唯一对象入口与时限

`probe_async_uia_object.py` 只从冻结77文件包导入 `windows_mcp.uia`，核对类定义已经创建的原 `_AutomationClient._instance`、IUIAutomation及RawViewWalker，不再次调用instance，不查窗口、不遍历桌面、不订阅事件。它使用独立基础Python、156文件comtypes模板、私有依赖/缓存和COM原调用计数。

本组除通用余额归零外，明确要求两次CoInitializeEx、一次原UIA的CoInitialize和三次CoUninitialize，父子均独立重算，额外或缺失都拒绝。实际单例或包装生成不兼容时，保留首次异常，不自动重建缓存、重复创建或换入口。

`UiaObjectOwner` 在任何身份回调前持有直接创建的原Popen。原5秒截止从父材料预检前起算，request、启动、子导入/创建/清理、原退出、回执/来源复核及最终落盘都在同一截止内；不从ready/request/ack或子入口重新计时。超时保留原对象和stop标记，迟到exit0只能更新生命周期。

`run_async_uia_object.py` 绑定本轮Context、批准原字节、实际Pi环境及原JSONL已核验前缀。输出根必须全新，一次启动机会；原600/900单调截止保留。失败后保持failed/token/原5秒截止及完整120秒零新UIA/native/状态/截图/输入，只本地poll原对象并保存诊断，不强杀、不重试。最终落盘迟到也另存拒绝，不能以已写的临时成功文件继续操作。

## 指定Pi与任务边界

本次通过 `orchestration` 和 `orca-cli` 技能创建新独立工作树 `Kylineyes/verify-uia-object-compat`，使用Pi显式 `deng/gpt-6.1-sol high`，禁用自动MCP连接。阶段1只核对原会话、实际模型、范围和材料，阶段2须等待父完成可审阅冻结并说明具体开始时间与预计范围后才执行一次对象入口。

新Run为 `run_0db66155091d`，Task `task_d3f457a86360`，Dispatch `ctx_d507e4b3f6a7`；实际Pi session预期 `a8e82af0-6b64-4f65-bcce-51e8afec9ee2`，必须由原JSONL和工具回执复核，不能仅据启动参数。旧任务、批准、归档、失败、abandoned和冻结只读，不复用旧身份、不运行旧演练。

## 本轮实际结果与离线修复

本Task于2026-10-30 **18:03:07.5576101～18:05:08.5841699（UTC+8）**执行唯一入口一次，结论为 **failed**；独立[工作者报告](uia-object-compat-worker.md)已纳入仓库。实际Pi原JSONL共有68条assistant消息，父独立核对全部为deng/gpt-6.1-sol，thinking始终high；唯一runner工具调用及完整会话前缀已归档核验。

原Popen PID72256、birth134378281877983799、handle200、原映像为冻结基础Python，原退出1。子结果`object_created=true`，实际类型为POINTER(IUIAutomation)与POINTER(IUIAutomationTreeWalker)，但清单只有CoInitializeEx两次（HRESULT0/1）与CoUninitialize两次。严格三次验收保守拒绝，`accepted=false`，不能把记录余额0当全部实际调用均已平衡。

父首失败为object-finish，token=object-start，原5秒截止不变。子结果在原父起点后0.7160602秒结束，父0.7516047秒拒绝；这是协议/计数失败，不是5秒超时。首次父失败日志到最终记录120.0914348秒，未发新UIA/native/状态/截图/输入。产品、控制服务、窗口/桌面查询、截图、输入与事件订阅均0。全部6622文件实际候选、私有156文件及批准摘要前后保持。没有重跑或第二组。

父静态分析及假API复现定位：`core.py`中`from .enums import *`会导出真实ctypes，覆盖ImportLoader预先提供的局部代理，原UIA额外CoInitialize因而可能漏记。修复在core模块执行后、单例被events类定义创建之前重新绑定同一局部代理；回归模拟星号导出并确认额外调用可记录。另将停止检查抛为受控BaseException，避免原初始化兼容分支的`except Exception: pass`吞掉停止后继续创建。

这些修复仅存在于新源码/新离线候选，没有写回本轮实际候选、活进程或旧证据，也没有新增实际调用验证；真实三次生命周期仍未通过。不能据离线修复追溯将本Task改成功。

唯一worker_done为`msg_b1dbe0075c55`，父独立审计后接收failed并ack。worker-release回执为external_terminal retained/processAction=none，reclaimable0；闲置Pi终端不代表活Task或后台UIA服务，不恢复该Dispatch。

## 验证与证据

新增假API测试覆盖禁用/慢预检零创建、原Popen身份未知保留、原退出0、错请求与会话/范围拒绝、严格三次初始化/释放、迟到退出不清失败、子入口禁用不导入COM。仓库全回归和独立冻结结果另存本机 `.local-analysis/async-product-uia-compat/`。

执行前仓库417项通过43.338秒、实际候选独立223项通过26.669秒；离线修复后仓库 **419项通过43.476秒**，本轮总新增10项。后续新候选仅用于离线审阅和回归，未执行第二次真实UIA。原实际6622文件候选及其失败归档保持只读。

实际核验成功最多证明本组自动化对象创建、COM清理及原时限；它不能证明Qt主窗、文件框、完整UIA双轮查询、Snapshot/read、NET/铜竞争或长期稳定。正常NET/铜含发现31/22、原32次、5秒和20/50/55/60门槛、35/5/40退出余量及600/900预算均不扩大。若本组失败，先定位并离线修复，不能续投旧组追ready。
