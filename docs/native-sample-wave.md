# 原软件样例取证与只读 PCB 核验命令

本轮从 `dev=6c08416423927f4ba8acf32dd000a71136bf230d` 继续，由父在 `feat/native-sample-verification` 集成验收。两路工作分别负责原软件真实单线保存重开和正式只读核验命令，文件所有权不重叠。正式新增入口和默认写出策略仍等待原软件样例证据。

## 可直接消费的核验命令

新增 `pt-pcb-check`，复用现有严格 `LegacyPcbReader::readFile` 和同一冻结输入的 `parseWithLayout`，提供 UTF-8 JSON 输出。它报告输入 SHA-256／大小、记录与图元计数、有限数量自由 FT 的端点／宽／层／六七字段／逐行换行／来源与 Loaded 身份，以及 ENDPCB／DOS EOF／NETDEF 和插入候选事实。

默认最多100条明细，可选0至1000条；即使不列明细，也严格验证整个文件。未知记录、畸形字段、损坏 EOF 或模型布局对应失败时整体拒绝，不导出局部几何。它只读一次文件，不写输入，不从正文搜索标签，不将元件 CT 或 FS 文本当成自由 FT。成功退出不表示原 AUTOTRAX 兼容，兼容验证标记始终为 false，也不会据观察字段选择默认编码。完整用法和退出码见[命令说明](pcb-check.md)。

工具由 `feat/pcb-check-cli` 提交 `3d219691695372eb69160749ecdaae44a546f7e4`，仅修改新 `tools/InspectPcb.cpp`、`tests/PcbCheckTests.cpp` 和专项文档。父另在 `d2ee381161fdb444255f7db931aa1f1290aa5bd7` 接入正式 CMake 目标和 CTest，测试通过环境变量定位该配置真正构建的可执行文件；未修改 reader、writer、命令能力门或 GUI。

## 构建与父独立验收

子代理实际 Pi 会话 `01a19f99-9252-74f7-9844-99633c12fe1f`，模型为 `deng/gpt-6.1-sol`、推理 high；原模型事件、assistant 和成功工具均已核对。独立 Debug 配置／构建／CTest退出0，QProcess真正启动 CLI 的15项测试通过，覆盖 Unicode 路径、明细限额、六七字段及混合换行、正文伪标签／CT 排除、参数错误和严格解析失败、NETDEF 布局及64 MiB上限。

父固定候选为 `d2ee381161fdb444255f7db931aa1f1290aa5bd7`，正式配置、构建及 CTest 均由原创建者逐步记录真实 wait=0：

| 配置 | CTest 组数 | 原创建者 CTest 计时 |
| --- | --- | ---: |
| Debug | 24/24 | 125.295秒 |
| Release | 24/24 | 19.142秒 |

受验127个源码／测试／CMake文件在测试前后摘要一致。父另用正式 Release `pt-pcb-check.exe` 实际运行前轮两份74字节合成文件，两进程退出0、输入字节前后不变：

| 合成文件 | SHA-256 | 首 FT |
| --- | --- | --- |
| INPUT.PCB | `0d0bec3a1975a44182dbe8abf7071c6e1f3d2ce6a5859acaebdc28a4178c189e` | `(100,100) → (400,500)` |
| HARDENED-SAVED.PCB | `51dbf589b06cc7b6fdd1d24b20f2c2b8b4a84fe4e95508b51466ee6474e786d3` | `(175,190) → (475,590)` |

报告正确识别两条自由 FT、七字段附加值42／CRLF和六字段／LF、混合换行、ENDPCB偏移65与DOS EOF偏移73。该次正式 Release EXE SHA-256为 `e0cc7fd9c64e7e332461b093ab2849aaedf978c0a247573c3c520c39331a0d8d`。上述均为合成文件核验，不是原软件单线样例。

父首轮审计直接比较 Git blob 与 Windows 工作区源码原字节时因 CRLF/LF 检出差异失败，原记录保留；改为分别记录原字节一致和仅换行归一后一致两个事实，再按受验工作区 manifest 核对实际文件。CLI过程和双配置测试未失败，没有为此重复全量测试。

## 原软件任务当前边界

沿用原 Pi 会话 `01a19f6a-a52d-7333-95f3-2972829f4e9f` 和指定 `deng/gpt-6.1-sol high`，独立分支 `verify/native-guest-save-sample`。首个 Task 尝试在模型自动重试后以超时／连接错误结束，零工具；父据原会话错误记录 abandon，processAction none，未启动服务、目标、截图或键鼠。随后压缩同一会话并对同 Task 正式重试，成功恢复工具执行；没有更换模型或原样循环启动桌面实例。

原软件首槽已启动，但本地新投递辅助脚本固定使用 `request-next.json`，第二次消费改名至已存在的 `.consumed` 文件时发生 `FileExistsError`；精确聚焦请求尚未执行，没有 Enter／Capture／编辑／保存业务输入。该错误属于本地试验脚本，不是原软件或门禁结果。冻结驱动按原路径完成120秒静默并关闭服务；父与代理核对精确目标身份后正常 `CloseMainWindow`，原创建者记录目标与服务均 wait=0，原安装、99项运行副本和输入集合／摘要不变，2张宿主原图均有实际image回执。

父在首槽完全退出后授权同 Task 的新独立 `retry-01` 槽，原槽、计划、收件箱和错误记录均不修改。新辅助脚本改为动作唯一请求名，拒绝已消费同名、已有未消费请求及缺少实际读图记录；离线真实模拟三轮投递／消费及三种拒绝通过。新子目录的仓库路径、驱动导入、挂载、日志和截图路径也已逐项核对。父新GO为北京时间15:35–16:20、16:13起只正常收尾，与原15:05–16:05单槽记录分别保存。

第二槽现场已结束，单线样例目标未通过，详见[两槽尝试与失败边界](native-guest-save-sample.md)。新槽唯一请求消费正常，指定模型在本机实际Capture菜单确认F11+P，并经当前菜单选择生成6350字节客体PNG；连续第二次捕获请求因模型连接延迟，在16:16:31被只允许收尾的时段检查拒绝，热键未发送。没有完成连续捕获、文件名计数、菜单、单线新增或保存。不能以单张截图或新CLI开放产品入口。

第二槽服务16:18:32原wait=0，目标未按16:20截止自行结束。父在16:25:44核对精确PID／创建时间／HWND／映像后正常CloseMainWindow，原owner16:25:45记录同Popen／HANDLE wait=0，无强杀。迟到父接手事实、缺失第二张PNG的ENOENT及模型连接错误全部保留。两槽8张PNG均匹配指定模型实际image回执，安装／运行副本／输入均未变，两个NEWFT目标均不存在。

代理最终自动重试以连接错误结束，没有提交worker_done或本轮报告；父依据原终止记录abandon，并根据已保存证据编写失败报告，不制造完成回执。原软件Task失败，工具Task成功；这些结果分别记录，不因工具成功改变真实样例结论。

## 证据与协作

父证据为 `main-2/.local-analysis/native-sample-wave/`，含完整任务范围、启动／重试回执、原模型审计、双配置日志和原 wait、正式工具两次实跑JSON及父独立审计。工具子证据在 `fix-pcb-writer-boundaries/.local-analysis/pcb-check-cli/`；原软件新证据预定 `native-startup-diagnosis/.local-analysis/native-guest-save-sample/`。

子代理不修改共享 CMake、其他工作树或产品入口；父审查后保留 no-ff 合并记录。原安装／库／用户文件只读，运行只用隔离副本，原图／原软件／构建／会话不提交。main、tag、发布及既有 dist 不操作。
