# 原 AUTOTRAX 实际鼠标键盘验证

本轮实际执行了鼠标与键盘输入，但原软件输出重开兼容性仍未通过。2026-10-31，新隔离 DOSBox 窗口被公开控制工具聚焦后，实际点击标题栏 `(300,120)`，发送一次 Enter；指定 Pi 读取操作前后原图，客体始终为黑底白横线，未看到可辨认的 AUTOTRAX 启动页、菜单、工作文件名或图元计数。不能由此判定输出文件格式不兼容，渲染／客体初始化原因仍未知。

## 执行与证据

使用 Pi `deng/gpt-6.1-sol high`，会话 `01a19107-f43e-75fd-9e8c-0925f8c21dac`，模型、推理等级与原 JSONL assistant 记录均由父侧只读核对。Run `run_d4e19e957438`，Task `task_cb2239d708d0`；首次 Dispatch `ctx_e56a50997250` 在启动前公共状态返回 `user` 后停止，零目标、零键鼠，仅有一张桌面基线。其 worker_done 为 failed，旧结果保留。

用户进一步明确本周期由代理自主键鼠后，同一 Task 以 `retry-of` 派发 `ctx_763c733b72a8`，使用新隔离目录与新冻结驱动。公开 `ControlStatus=user` 时仅进行最多 30 秒的状态等待，只有 `ready/ai` 才执行桌面动作；未修改第三方控制门、钩子或输入实现。新驱动启动前通过九项截图区域边界、四项假时钟控制等待检查及 Python 语法检查。最小化、屏外、遮挡或窗口未出现时使用全桌面图，避免前轮无效区域问题。

新目标 PID **51276**，创建 FILETIME `134379212430315431`，窗口 HWND **460682**，原 Popen 身份 `2647783612304`、句柄 **568**，由 runner **41264** 创建并持续持有。输入均在本轮精确 PID/HWND 的稳定前景内执行，鼠标坐标在目标窗口内。六张本段原 PNG 均由指定 Pi 通过原 `tools.read` 读取并作为 image 返回，父侧核对成功 image 解码 SHA 与原图相等，不冒称父直接看图。

隔离输入 `SYN1.PCB` 为 180 字节，SHA-256 `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`。其生成与原字节比较见[原软件后续核验](pcb-legacy-native-verification.md)；本轮不重新生成或改写输入。

## 退出与准确边界

实际输入为一次鼠标 Click、一次 Enter，以及一次正常关闭快捷键 Alt+F4。Alt+F4 后窗口仍在，原 Popen 的五秒等待于 **20:12:54.480273（UTC+8）** 超时，驱动停止并完成 120 秒零桌面请求等待，控制服务原 Popen 返回 0。未重发该失败动作、未强杀、未热改或重连追通过。

随后独立产品任务在新的明确现场范围内接管同一已核对 DOSBox，只尝试宿主窗口 X 的正常关闭。**21:01:07.590170**，原 runner 写出的原 Popen 退出记录确认 PID、创建时间、对象身份和原句柄相同，返回码 **0**。该新证据证明目标最终正常退出，不把原五秒超时改写为通过，也不证明客体业务正常。

更早的旧 DOSBox PID11096，其原创建者于 **18:54:27.255282** 记录非零退出码 `1853227067`；原因不推断，不能与本次 PID51276 的退出 0 混用。

父侧脚本核对原安装 **99 个文件及完整集合**、隔离输入和 runtime 字节未变化。父证据位于 `.local-analysis/pcb-mouse-keyboard/`，含 `preflight*.json`、`parent-audit.json`、`parent-retry-audit.json` 及原会话前缀；原工作者证据位于 `../verify-pcb-legacy-native/.local-analysis/pcb-mouse-keyboard{,-retry}/`。原软件、截图、运行副本和构建均被 Git 忽略。

后续 Pi 文件收尾连续出现 `Connection error`／`Request timed out`，原 JSONL 的最终错误与 TUI 闲置状态得到确认；协调者将该 Dispatch 标记 abandoned、Task failed，保留终端和原始记录，不冒称收到第二段 worker_done。独立产品的实际键鼠及原生文件框结果见[产品核验报告](product-mouse-keyboard-verification.md)。

<a id="explore-ex-009"></a>

本报告证明已实际发送并观察了本轮鼠标、键盘输入，以及后续宿主正常关闭；未证明 `SYN1` 在原 AUTOTRAX 中正确载入、走线计数为 5、移动／删除及未修改对象兼容。未改变历史 failed、字形 runtime=false 或异步验收边界。

[探索 EX-009](exploration-backlog.md#ex-009)。
