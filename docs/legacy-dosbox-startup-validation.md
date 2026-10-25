# DOSBox 启动日志核验：verification-34

**结果为 `failed`：唯一 Windows-MCP 连接在首次截图前持续返回 `ControlStatus=user`，本地 30 秒截止后停止。没有调用截图或启动 DOSBox，因此没有取得目标启动日志和实际配置加载来源，verification-33 的黑色客户区与白横线仍未解释。** 主循环、菜单、Information、Status 工作文件名、八项图元计数及文字对象参数均未取得新运行证据；`runtime_verified=false`，产品保持 0.9.0。

基线为 `origin/dev=a5c2bde201bec8f7b405553a8bc0c5f0d2abe35f`，独立分支为 `Kylineyes/research-dosbox-startup-log`。只新增本页，既有 [运行报告](legacy-menu-runtime-validation.md)、[静态复核](legacy-menu-static-validation.md) 和工具均只读。按本任务要求只提交当前分支，由协调者验收合并，没有合并或推送 `dev`、`main`。

## 证据与输入保护

证据根目录为：

```text
C:/Users/rikideng/orca/workspaces/pt_renew/research-dosbox-startup-log/.local-analysis/verification-34/
```

下文相对文件名均以此为根。完整客户端、配置、日志、原生窗口观测与输入清单仅留在忽略目录；本轮没有原程序截图。

| 输入集合 | 文件数 | 前后完整集合与 SHA-256 结论 |
| --- | ---: | --- |
| 原安装 `D:/project/pt_renew/pt` | 99 | 与共享 `source-sha256.json` 相同，0 项差异 |
| 既有 `main-2/.local-analysis/verification-20/runtime-without-dft/pt` | 103 | 与 `inputs-without-dft-before.json` 相同，0 项差异 |
| 本轮 `runtime-without-dft/pt` | 103 | 从上述已核对副本复制，与同一清单相同，0 项差异 |

新副本没有 `TRAXEDIT.DFT`，未删除其他 DFT；原安装和共享副本均未执行或修改。完整证据为 `source-before/after.json`、`existing-inputs-before/after.json`、`fresh-inputs-before/after.json`，摘要结论为 `verification-before.json`、`verification-after.json`。本地复用的 `check-inputs.py` 已实际执行前后核验。

## 启动前已核对的日志方案

先读取已安装 DOSBox-X 2026.10.01 的 `README.txt`、`dosbox-x.conf` 第 108 至 117 行，以及 `dosbox-x.reference.full.conf` 第 109 至 191 行。安装配置明确将 `logfile` 放在 `[log]`，完整参考列出类别与 `true/false/debug/normal/warn/error/fatal/never` 等等级。对应日志配置摘录和文件摘要已留存，本轮配置新增：

```ini
[log]
logfile=C:\Users\rikideng\orca\workspaces\pt_renew\research-dosbox-startup-log\.local-analysis\verification-34\dosbox-startup.log
exec=normal
files=normal
vga=normal
int10=normal
gui=normal
```

其余仅替换 `captures` 和 C/D 挂载的隔离绝对路径；程序化反向归一化比较与 verification-33 完全一致，见 `configuration.diff`。保留 `output=opengl`、`machine=vgaonly`、`memsize=16`、`core=normal`、`cycles=fixed 10000`、`nosound=true`，以及 `c:` → `cd \pt` → `pt C21.PCB` 的启动序列。没有猜测命令行日志开关或改变渲染后端。

计划命令为 `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.exe -conf <本轮配置绝对路径>`，cwd 为本轮 `runtime-without-dft/pt`。本地复制客户端准备了受同一 ControlStatus 保护的 `LaunchTarget` 分支，以 `subprocess.Popen` 将 stdout/stderr 分别新建为 `dosbox-stdout.log`、`dosbox-stderr.log`，另由 DOSBox 写 `dosbox-startup.log`，避免既有 App 启动器的 DEVNULL。**该分支未执行，不能声称已验证其运行行为；三个目标日志文件均不存在。** `client-stderr.log` 是实际 MCP 与客户端异常日志，不是 DOSBox 日志。

`startup-plan.json` 保存 argv、cwd、日志绝对路径、安装/用户配置和文档摘要；本轮配置 SHA-256 为 `73707bc3616a1b14099105fe32f4e2547ee08ff944c9bffc44f8c5dca78a6d39`，EXE 为 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832`。安装 `dosbox-x.conf` 摘要为 `733084f61ef2f4ec1710f5c3d7553d00e73e90650b9edd90056a7773d30d802c`；用户配置 `C:/Users/rikideng/AppData/Local/DOSBox-X/dosbox-x-2026.10.01.conf` 为 `0d19342e41a9c73304a0923cfb10b0acd433cc57e6482eefec9932536c056d38`。计划 cwd 内不存在 `dosbox.conf`、`dosbox-x.conf`，停止后来源文件及本轮配置摘要均未变。

显式 `-conf`、候选配置文件与摘要只是启动前来源证据；没有实际日志就不能断言安装或用户配置是否加载，也不能确定全部搜索、覆盖或 autoexec 拼接顺序。

## 实际控制过程与停止点

唯一 stdio Windows-MCP 连接初始化和 `list_tools` 成功，见 `connected.json`、`tools.json`、`client-identity.json`。收件箱仅提交一个完整 `Snapshot(use_ui_tree=true, use_vision=true)` 请求，没有排队其他动作。

Snapshot 前的 `step-001-initial-gate-00.json` 至 `step-001-initial-gate-15.json` 共 16 次 ControlStatus 全部返回 `user`、`generation=2`。首次 `wait_seconds` 约 6.76 秒，后续值随现场变化；客户端的本地 30 秒截止时间没有随之延长。到期抛出“控制状态未在30秒内恢复；本场景停止”，完整根异常见 `client-stderr.log`，外层 ExceptionGroup 摘要见 `stopped-error.json`。

Snapshot 本身未调用，因而没有截图，也没有桌面变更动作。没有启动 DOSBox、发送 Enter/Esc/菜单字母或鼠标输入，没有切换焦点、重连、重启或新增对照场景。动作后截图规则没有产生可执行的变更动作实例，不能将缺失截图解释为截图成功。

既有只读 `tools/inspect_legacy_desktop.py` 生成 `native-connection-review.json`、`native-final.json`。前一次原生枚举成功，观察进程位于 session 3、`WinSta0/Default`；前景 HWND 724700、PID 23836 在枚举前后稳定，映像属于其他应用。此证据只说明原生桌面可枚举、前景并非 DOSBox，不推断其他应用的输入行为；本轮没有 `use_ui_tree=false` 空元数据误判，也没有 DOSBox HWND/PID。

停止后已向协调者发送控制结果与无目标日志的 checkpoint。协调者随后明确接受 30 秒停止，要求不重连、不重启，提交失败报告。

## 进程清理与验证边界

`processes-connected.json` 记录本轮进程链 `33516 → 7572 → 9196 → 56856 → 62320`，分别为客户端启动器、客户端 Python、唯一 MCP shim、MCP Python 启动器及服务，均在 session 3。连接退出后，`processes-gate-check.json`、`processes-final.json` 的查询均无匹配记录；最终查询同时包含上述五个 PID 和 `dosbox-x.exe`。没有调用强制终止、关闭其他人的窗口或清理共享 Windows Terminal 宿主。

客户端 Python 语法检查、三组输入前后完整摘要核验、`validation-summary.json` 的证据断言以及 `git diff --check` 通过。没有新增提交工具、修改产品、第三方包、控制门、阈值、hooks 或系统设置；本轮文档变更不涉及 Qt 构建或 GUI 产品验收。

后续需在控制可用的独立场景实际执行已记录方案，先取得日志、配置加载行和目标窗口证据；启动页正常后才能单步核验菜单、Information、Status 文件名与计数，Status 截图后单个 Esc 返回。若仍异常，先将首轮真实日志与具体单变量候选交协调者决策，再考虑对照。本轮未完成启动日志诊断与菜单运行核验。
