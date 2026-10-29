# 监督器账本快照失败时保留原进程

2026-10-29，基于`dev=acb9c87`，在独立`fix/control-supervisor-snapshot-journal`分支实现，提交`a37ed03`。第三候选现场的监督器在替换`supervisor-chain-held.json`时遇到PermissionError，原异常路径随后关闭子孙查询句柄并退出1，客户端仍继续原预算，导致后续退出证明缺口。现场原件及failed结论见[第三候选报告](control-owned-close-v3-live.md)，不由本修复追溯改写。

`SnapshotJournal`只处理周期账本快照的写入，不操作桌面或进程生命周期。PermissionError最多3次写入尝试、两次各10毫秒等待；其它OSError一次后锁存。持续写入失败只累加失败次数及最多64条诊断，继续原进程枚举和持柄等待。原客户端及全部已发现子孙退出后，监督器调用原Popen.wait取得退出码，再将失败次数、重试次数、诊断和截断标记写入最终退出报告。有持续失败时，即使原进程均退出0，verified仍为false、监督器返回1，不能把生命周期完成改为完整通过。

最终退出报告等必要文件写入失败仍走原异常路径并如实失败；本修复没有证明底层权限错误原因或所有文件操作均可靠。若已发现子孙长期存活，监督器继续只读持柄等待，不强杀、不自动重连，也不宣称已退出。

新增2项实质测试覆盖临时权限拒绝、有界重试、持续拒绝锁存、非权限写入失败、诊断数量上限、后续写入恢复仍保持失败，以及真实无GUI客户端在持续账本写入失败时完成原正常生命周期、保留原退出码并返回失败。一次定向运行的既有子进程测试出现非0且原stderr为空，未据此记通过；补充失败时输出原退出账本诊断后，7项定向测试及[142项控制测试](../.local-analysis/control-owned-close-v3/tests-supervisor-journal.log)全部通过，后者16.848秒。该次未定位的定向失败保留为验证限制，不能以随后通过否定其发生。

新冻结候选位于`.local-analysis/control-owned-close-v3/frozen-next/candidate`，仍111文件（17客户端、13工具、3监督器和77文件包及清单），清单SHA-256 `f5ebb7a8b4dfb6b50b378fd54e0ab4d47cedd693607b159391f287cabb066b0e`。没有绑定Task/Dispatch、批准或运行状态，尚未现场验证。旧第三候选、旧失败execution、原批准及产品文件保持只读；此后遗留诊断窗已通过[独立生命周期](control-residual-lifecycle.md)一次WM_CLOSE正常退出；该新查询句柄exit0不补记旧验收或原Popen证明。后续可另立新Task/Dispatch及冻结批准验收，不能在failed任务追加关闭或新连接补验。
