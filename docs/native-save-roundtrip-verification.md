# 原生另存与重新打开验证

2026-11-02 实际控制验证结果：**原生另存新文件、原生重新打开、正常退出均通过**。输入为既有核心生成的 SYN1 隔离副本，5 条自由 FT、180 字节；本轮没有编辑，不替代此前未保存移动的往返验收，也不验证原 AUTOTRAX 兼容性。

## 范围与操作结果

从 `origin/dev=78d3e817d04930d4552105de6be2be6cf81fac1f` 建立 `verify/native-save-roundtrip-worker`，仅提交本文。Pi 沿用会话 `01a19201-b349-7326-873c-dc74757f3daa`，环境与原 JSONL 确认 `deng/gpt-6.1-sol high`，未换模型。隔离 EXE SHA-256 为 `8730f39af09be8290e278d09ebb186c630e44d988a204237cc5f8bb5395d57df`，PATH 限运行包和 Windows 系统目录；没有重建、QTest、offscreen 或直接调用 Qt 方法。

| 验收项 | 实际证据与结论 |
| --- | --- |
| 原生另存 | 公开 App 切换聚焦后，`Ctrl+Shift+S` 打开 `#32770` 原生另存框；在截图确认的文件名字段 `[1500,1263]`，Type 直接使用计划 JSON 的 Windows 反斜杠 `save_target`，`clear=true, press_enter=true`，生成全新 `outputs/SAVED.PCB`。通过。 |
| 原生重开 | `Ctrl+O` 打开原生文件框，在 `[1530,1385]` 输入同一计划路径并提交；截图可见 `SAVED.PCB` 标题、5 个图元／5 条走线及“未修改或与最近另存为一致”，状态栏显示已载入 SAVED。通过。 |
| 正常退出 | 专用 Close 发送 `Alt+F4`，随后实际读取全桌面图确认无产品窗；`WaitOriginalExit` 核对原创建者 Popen 身份及返回 0。通过。 |

产品精确绑定 PID `2844`、创建 FILETIME `134380273510730407`、主 HWND `397486`，主窗类 `Qt6120QWindowIcon`。两个原生文件框分别为 HWND `20058524`、`12978624`，均属于产品同 PID owner 链且主窗已禁用；每次键盘／Type 前另做只读前景检查，驱动仍独立核对稳定、启用前景与窗口内坐标。续接实际输入为 App 1 次、Shortcut 3 次（含最终关闭）、Type 2 次，逐步看图后才发下一步，没有预排多个变更。

## 分段、读图与退出记录

首段 `.local-analysis/native-save-roundtrip/` 于 01:20 启动驱动并一次启动产品。Launch 截图时产品在前景，下步未再 App 聚焦；01:24:12 前景已变为其他终端 PID `19172`，驱动在发送 `Ctrl+Shift+S` 前拒绝。该段未发任何产品业务输入，保留失败与完整 120 秒静默；其服务原 Popen PID `48940`、handle `292`、创建时间 `134380272486332335` 于 01:26:14 返回 0。

新 Dispatch 使用已冻结 Attach 驱动及独立 `.local-analysis/native-save-focus/`，不恢复旧脚本、不重启产品。驱动 SHA-256 `308a231a6fb85644ed5b1316f68f18ecef3735b6afd17e575a3cfc30d2e03f0b`，计划 SHA-256 `0bc31b4b9f4822fe9fbfc40f670a4ff6e0f07ae433d32ec8ae5f41592fb4fcaf`，使用前实际核对。首次隐藏启动 shell 返回 255 后，只读确认没有该段启动记录、日志或对应进程；随后以隐藏子进程成功创建唯一续接驱动 PID `30520`，原启动回执保留。本段依次 baseline→Attach→App 聚焦→另存→重开→Close→WaitOriginalExit→Stop，未重连服务或绕过控制门。

本人实际用原 `tools.read`／`image` 查看首段 2 张、本段 8 张 PNG；两个分段的 `worker-final-audit.json` 记录会话原调用、成功读取回执与返回 image 解码 SHA 匹配。本段 005、007 截图含文件框消失动画的透明残影，主窗标题、图元数和 clean 文字可辨，保存事实另以实际文件字节证明，不将动画残影说成仍有模态。

原产品由首段 runner `52372` 持有的 Popen：identity `1920102161040`、handle `612`、上述 PID／创建时间，`target-late-normal-exit.json` 记录 **01:56:33.721728 UTC+8，wait_return=0**；续接 009 再读取核对。Stop 后，本段服务原 Popen PID `4400`、identity `2573319974464`、handle `180`、创建时间 `134380285911224280` 于 **02:00:14.017178 UTC+8，wait_return=0**。续接 `runner-finished.json` 仅为驱动结束标记，不扩大为驱动自身的操作系统退出码。

## 文件核对与边界

输入与输出均为 **180 字节且逐字相同**，SHA-256 同为 `dc2ed984c9af4d7c3e0bed26a6c9721565e5dfaa874ba495523370e69ee2c228`。收尾独立核对准备清单：原安装 `D:/project/pt_renew/pt` 的 **99 项**、隔离运行包 **18 项**及输入 **1 项**的完整集合、大小与摘要均未变。详细回执见本段 `worker-final-audit.json`，原图、输入、输出和二进制保持 Git 忽略。本轮没有移动、删除、取消或已有目标拒绝测试，没有证明生产输出、DRC 或原 AUTOTRAX 业务兼容。
