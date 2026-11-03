# 原软件捕获驱动审查与隔离工具包

本轮完成旧驱动离线审查，并按父协调者后续扩展授权，在本工作树的忽略目录制作最小修订、隔离副本和冻结启动包。**工具修订与冻结已完成；没有执行 COM、UIA、MCP、原软件、截图、桌面或真实目标退出验收。** GUI、实际 read 与原 Popen 正常退出由父协调者执行，不能将本文假 fixture 结果当成现场通过。

## 基线、授权与来源

分支 `review/native-capture-driver` 从固定 `origin/dev=672351eb89734c0b508fadfefc577af09928a550` 建立。沿用 Pi 会话 `01a1a161-c684-75ff-8e81-5918e22bf0ce`，环境及原会话记录均为 `deng/gpt-6.1-sol/high`，工具成功记录在本树 `.local-analysis/native-capture-driver-review/session.json`。

旧只读来源是 `native-startup-diagnosis/.local-analysis/native-guest-save-sample/retry-01/` 的 `desktop_session.py`、`submit.py`；其 SHA-256 分别为 `4470713e8bd6afcb2b2f687ba1894e0df8e04081994c24b1a70726f269095323`、`c5f1dfad884fe69c8f0d60b58d2e797f2c2912f86bc1375e1d120f6ecced272d`。随后只读复核新 `native-capture-checkpoint/` 的门、submit、prepare、生成 driver/plan 及完整文件清单。没有改写这两个目录。

父在 `msg_2d7efb0c287b` 扩展授权：原操作者停止写槽，无 GO，父成为唯一现场操作者；本 worker 可在自己 `final-candidate/` 修订驱动并建立全新隔离槽。冻结 plan 的 session 按父要求绑定 `01a1a15a-5307-7312-a21c-9c61e64983f5`，task/dispatch 保留本工具任务 `task_46be31be3ba2/ctx_c38cc667f1c9`，明确由父实际执行和看图。

## 具体发现与最小修订

| 边界 | 已复现旧行为或新槽中间问题 | 最终自有候选 |
| --- | --- | --- |
| 客体原图审核 | 旧两侧只比宿主 images/review 字符串；没有新 guest read 仍可继续，实际图片字节变化也未重算 | 当前步骤、nonce、session/task/dispatch、实际路径/字节 SHA 和 host/guest 清单均核对；实际 read 回执由父负责产生 |
| 回放与消费 | submit 任意 previous 可通过；driver 当前审核缺失时先 consumed 再拒绝 | 当前步骤两侧验证；driver 验证后才消费；唯一动作名、单待消费请求、consumed/rejected 防复用 |
| 菜单顺序 | 新槽首版只允许 `Shortcut f11+p`，无 guest 时第一次普通菜单 Click 也被拒绝 | 两步 `Click`：`capture_menu_open` 打开菜单，当前宿主图审核后 `guest_capture` 选择 Take screenshot；不使用 F11+p |
| 捕获结果 | 旧代码未约束新客体集合 | 选截图项前后全集合差，恰一张新 PNG、非空及 IHDR 640×480；旧图改写/删除、零张/多张拒绝。相同画面字节可相同，不要求 SHA 必须变化 |
| 缺审核收尾 | 旧 Close/WaitExit/Stop 全被审核门拦；新槽首版 submit 还先 load current-state | 最终生命周期请求不读取 state/review，缺失或损坏 state 仍可投递；Close 仍走公开门、原 Popen 精确身份和稳定目标前景 |
| 截止与等待 | 原七分钟只拒业务；控制门返回后未重查，单 RPC 固定 35 秒可越界 | 20 分钟总预算、最后七分钟只收尾；每次 RPC 受剩余预算约束，控制门返回后和真正输入前重查；不足七分钟 GO 拒绝 |
| 失败静默 | 异常后静默 120 秒、关闭控制服务、原目标无界 wait，无法继续收尾请求 | 失败后保持 120 秒无桌面请求，结束后仅接受父显式 Close/WaitExit/Stop，不重连、不恢复业务、不自动关闭；再拒绝仍静默 |
| 完整预检 | 旧 Launch 只核 EXE/input/config，runtime 清单只存不检查 | 启动前、Launch 前核 runtime/inputs 的完整相对路径集合、大小与 SHA，冻结 driver/门/submit/配置/控制入口及相关文件；额外文件也拒绝 |

父只读安装源码并以假 API 证明 `f11+p` 被解析为 F11 down/up 后 Unicode p，本 worker 未执行该按键或读取安装源码；这不是现场热键失败证据。最终计划使用父指定的 Capture 菜单两步点击，坐标来自实际宿主图，不提供盲点坐标。

正常收尾不能由驱动单方面保证：如果截止时目标仍活着，最终仍记录 `target-exit-unproven.json`，保留原 Popen 等父正常关闭并记录真实 wait。此处无界等待是明确保留的证据责任边界，**不是已实现自动有界退出**；不强杀、不绕公开门、不把控制服务退出当成目标退出。父须持续监督 20 分钟预算和七分钟收尾点。

## 离线验证与真实等待

全部脚本及结果位于本树 `.local-analysis/native-capture-driver-review/`；假文件与中间失败快照不覆盖重跑。

| 执行 | 结果与证据 | 同步真实等待 |
| --- | --- | --- |
| `check_offline.py` | 旧 submit 副本及 driver 原 AST 片段，12 项符合预期，包括成功复现缺口；`offline-results.json`。父在自己新目录独立重跑结果一致 | exit 0，0.6062814 秒 |
| `check_new_gate.py` | 新槽首批门快照与标准库生成有效假 PNG，16 项符合预期；菜单 Click 拒绝、缺 state 收尾受阻均被复现，`new-gate-results-01.json` | exit 0，0.4784599 秒 |
| `check_preparation.py` | 只做语法编译及纯字符串生成；中间 `check_offline.py:34` 的非 ASCII bytes 字面量发生真实 SyntaxError，保留 `preparation-results-01.json`；随后生成槽版本已修语法 | 失败事实保留，不冒称该中间文件语法通过 |
| `check_generated_slot.py` | 生成首版的 16 项摘要/路径/完整集合自洽检查通过，同时明确记录五项未修边界；`generated-slot-results-01.json` | exit 0，内部计时 0.075515 秒 |
| `check_final_candidate.py` | 最终 36 项假 fixture：菜单两步、旧 nonce/guest/派发/改字节拒绝、缺失及损坏 state 的真实 submit 子进程、门后截止、RPC 余量、完整 preflight 和 GO 时长；`final-fixture-results.json` | exit 0，1.0740446 秒 |
| `check_final_main.py` | 原 main 的 AST 在假时钟/假 RPC/假 Popen 环境执行八步：Launch、两轮菜单 Open/选择、Close、WaitExit、Stop；两张假图、一次假目标 wait，`final-main-loop-results.json` | exit 0，0.2155946 秒 |
| `freeze_final_candidate.py` | 原安装 99 项与冻结清单一致、隔离 runtime 99 项及 inputs 1 项一致、语法及纯 preflight 通过，未 import driver 顶层；`freeze-wait.json` | exit 0，0.3404806 秒 |

假观察字段用于门行为测试，不是模型 image read。main 的假 wait 也不是实际目标退出。没有重跑产品 24 组、安装依赖或二进制逆向。

## 冻结包与父执行入口

包根绝对路径：`C:/Users/rikideng/orca/workspaces/pt_renew/review-track-core-boundaries/.local-analysis/native-capture-driver-review/final-candidate/`。隔离槽为包根下 `slot/`；driver 以该路径作动态 ROOT，REPO 固定到本工作树绝对路径。门和 submit 在脚本目录及 slot 各保留同摘要副本，均进入冻结文件检查；没有修改其他槽。

| 文件 | SHA-256 |
| --- | --- |
| `slot/live-plan.json` | `d6bf6e572854050aeb6d8f2b4ab54715623c85ef5bca39b026e26d9d7b96f660` |
| `desktop_session.py` | `7e9f9b6fc29da2e082cbf793d996a46bbd956bed33f46bad979d9099fce4db55` |
| `review_gate.py` | `e7a22fa31f6cc1f80165da6aac23539e6a6e4b7693d614454b19844f70ad92fe` |
| `submit.py` | `576be158c2d3cc3e16598e0b89eed52b6986eea24c092299f3cb99e546f94304` |
| `start-owner.py` | `00630faedc393100a4a6b2c4497837b9cf8f63a317bfb1402f62a4bfa1d372c2` |

`frozen-package.json` 记录 BASE 为 `C:/Users/rikideng/scoop/persist/uv/python/versions/cpython-3.14.8-windows-x86_64-none/python.exe`。父写 `slot/go-start.json`，绑定上述 plan SHA、session/task/dispatch 和明确 UTC 起止后，用 `[BASE, 包根/start-owner.py]` 启动一次；当前入口持原 driver Popen，driver 持目标和控制服务至正常 wait。父的上层进程也应保留自己创建的 Popen 和真实 wait。缺 GO 时启动入口拒绝，worker 没有创建 GO。

父每次实际读取 `slot/current-state.json` 指定的 host/guest 原图后，在 `<step>-host-read-review.json` 和有 guest 时的 `<step>-guest-read-review.json` 写绑定字段、当前 step/nonce、模型/强度、完整 `images` 列表及真实观察。请求带相同身份、`previous=step`、`nonce` 与唯一 `request.name`，通过 `[BASE, slot/submit.py, slot, 请求JSON]` 投递；每次等 complete/error 才能下一步。菜单请求只允许 `arguments={"loc":[x,y]}` 的默认单击。

现成 `slot/lifecycle-close.json`、`lifecycle-wait.json`、`lifecycle-stop.json` 不依赖原图审核；仍必须单个投递、等实际完成。失败静默期间不投桌面请求，看到 `cleanup-only-ready.json` 才按父决定收尾。最终真实证据应包括目标 `*-exit.json`、`control-exit.json`、`driver-exit.json` 及上层原 Popen wait；未退出或非零要如实报告。

本 Git 提交仅包含本报告，冻结包及证据按规则留在忽略目录。没有合 dev、push、main/tag/dist 操作，父负责验收与集成。
