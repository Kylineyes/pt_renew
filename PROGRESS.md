# 当前能力概览

新 agent 接手只读 [HANDOFF.md](HANDOFF.md)：当前基线、已交付研究、剩余问题、下一步、授权和本机证据均在其中。本页只提供能力速览；软件模型与实现见[文档导航](docs/README.md)，未知问题见[探索待办](docs/exploration-backlog.md)。

| 范围 | 已有能力 | 当前边界 |
| --- | --- | --- |
| 已发布 v0.11.0-alpha | PCB／LIB／NET 只读查看、选择定位、测量／端点捕捉、受限铜分析 | 不包含 dev 编辑功能；部分字形／轮廓近似 |
| dev 编辑与另存 | 已载入自由 FT 的整数整线移动／删除、历史、保存点、全新目标另存 | 不覆盖原件或已有目标，不改宽／层／extra；其他图元／元件仍只读 |
| 内部显式 Created | 身份、预览、提交、编码、插入与 MainWindow 显式另存闭环 | 正式新增门 false，默认 writer／主窗拒绝 Created，含 NETDEF 的新增拒绝 |
| 原软件兼容 | 一次菜单时序／真实后验、连续两轮新客体捕获；固定场景Information／Status文件名及八计数；配置与AUTOEXEC有界静态链 | 完整配置继承归因、IME／队列条件、自建单线保存重开、默认策略与完整输出兼容仍未过 |
| LIB／网络 | 严格库浏览、引脚映射及保守铜几何 | 未实现元件放置／替换、库写入、完整 DRC、布线及生产输出 |

EX-001及EX-004已闭环；EX-003已核Shift／VK／Unicode离线语义，并在第六／第八新槽逐图到达Information，第八另进入Status并Esc返回。EX-005在同一第八场景交叉确认`SYN1.PCB`、Tracks=5及其余七计数为0，静态来源／写值／DFT／AUTOEXEC机制已有专题；完整配置继承归因与实际API／I/O仍缺。EX-003／005整体及EX-006／008／017未闭环，EX-007未启动。

EX-005另已提供[两键离线命令消费](docs/legacy-config-query-consumer.md#offline-query-consumer)、[目录API缓冲解释](docs/legacy-source-api-buffers.md#result-contract)和[单运行观测记录审计v1](docs/legacy-source-observation-audit.md#schema-v1)，分别通过14／20／35项父树合成测试。三者不启动目标；真实隔离、采集器、输出送达及联合运行仍缺，审计v1尚不含原缓冲和Property字段。

配置隔离预检、owner投递线程与后续文件适配已修复并分别验证；第三槽事故、第四／第五／第七未达目标的记录保持。当前能力与剩余未知见[原软件主题](docs/topics/legacy.md)和[EX-005证据缺口](docs/legacy-dosbox-configuration.md#ex005-evidence-gap-matrix)；实时任务、授权与下一步只看[HANDOFF.md](HANDOFF.md)，本页不保存现场执行安排。
