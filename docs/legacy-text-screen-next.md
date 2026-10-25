# 原文字形下一现场阶段：无遮挡A、显隐恢复与缩放入口

日期：2026-10-26。沿用Pi会话，实际环境核对为 `PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`；分支 `Kylineyes/verify-text-screen-sol`，基线为已有提交 `d5931ea64dddc02a4653c5da8d47f9d012240237`。只读阅读父工作区最新PROGRESS和前轮报告，未修改旧报告或根交接文件，未另起子代理。产品仍为 **0.10.0**，**`runtime_verified=false`**。

**本轮已补齐A240被尺标遮挡的几何位置，确认切换当前层后的顶层隐藏/恢复，并实际进入Zoom菜单；F240和实际缩放前后对照因控制门禁超时未执行，任务按部分完成、最终failed报告。** 门禁后的预排捕获误执行了两次宿主点击，未计为有效验收；原始证据保留，后续输入已停止，并完成离线停止防护修正与核验。

## A与F逐项结论

| 验收项 | A240结果 | F240结果 |
| --- | --- | --- |
| 新隔离输入、正确挂载、无BOM、前置摘要 | 通过 | 通过，仅准备 |
| 原生目标前景和可辨启动页 | 通过，PID4092/HWND528210 | 未验证，未启动 |
| 实际加载文件与计数 | 通过：A240.PCB、Strings=1、Tracks=4，其余对象计数0 | 未验证 |
| 文字属性 | 通过：A、高度240、线宽1；取消未改字段 | 未验证 |
| 方向 | 输入0；可见形状支持相应静态预测，内部导入变换状态未读取 | 输入0，未运行 |
| 640×480客体原生工作图 | 通过，尺标与文字分离 | 未取得 |
| 独立尺度与端点 | 通过有限图像对照，见下表 | 未验证 |
| 切换当前层、顶层隐藏及恢复 | 通过：Bottom Layer下隐藏顶层，退出菜单后A及四尺标消失；恢复后红色像素集合一致 | 未验证 |
| 可操作Zoom菜单 | 已实际显示Redraw/Pan/Expand/Contract/All/Keyboard/Select/Window/Board | 未验证 |
| 一次实际缩放前后对照 | 阻塞：进入Keyboard前门禁超时，K未发送 | 未验证 |
| 内部缩放值、完整/简化分派、真实字体指针 | 未验证 | 未验证 |
| 输入前后摘要与清理 | 通过，未落盘修改；本轮目标及客户端已退出 | 通过，副本未变且未启动 |

本轮的完成范围没有扩展到其他高度、旋转镜像、间距、长串、完整笔宽栅格或铜层。原字体没有接入产品、命中或铜层判定。

## 隔离场景与可复核执行路径

本轮证据根目录E的绝对路径为：

```text
C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/
```

00:28:46开始重新核对模型、前景及残留进程。前景为普通应用；没有DOSBox或pt-renew残留，LockApp存在但不是前景。本轮随后创建 `scenes/a` 和 `scenes/f` 两份新隔离副本；原安装 `D:/project/pt_renew/pt` 99文件及历史verification-40副本103文件只读。每个新副本104文件，分别增加A240.PCB/F240.PCB，没有运行历史错误准备脚本。

两份FS均为原点(2000,2000)、高度240、方向0、笔宽1、层1，字符分别A/F。四条FT同为层1、宽10，尺标移至文字左侧及下方：

| FT参考 | 板坐标，mil | 与文字的关系 |
| --- | --- | --- |
| 下方长横尺 | (1800,1600)→(2400,1600) | 距文字基线400mil |
| 左竖尺 | (1800,1600)→(1800,2000) | 距文字原点左侧200mil |
| 左上短横尺 | (1800,2000)→(1900,2000) | 在文字原点左侧截止，间隔100mil |
| 右竖尺 | (2400,1600)→(2400,1800) | 位于文字右下方，不接触字形 |

每份配置以UTF-8无BOM生成，C/D只挂载各自 `scene/runtime`，cwd为 `runtime/pt`，保留既有OpenGL/VGA/normal core/fixed10000参数，日志与captures各自独立。实际仅启动A：stderr第2行记录本轮 `scenes/a/dosbox.conf` 加载，独立日志第68行执行pt.EXE，第130–131行打开A240.PCB；Status再次确认真实文件名、C:\PT及计数。

宿主启动页最初被其他窗口局部遮挡，公开Orca限定PID/HWND的标题栏点击后，原生前景确认为PID4092/HWND528210。宿主Capture菜单具有实际响应，用它保存客体原生图；客体键盘采用同一Windows-MCP受门禁连接，每步输入前核对原生PID/HWND。首次Snapshot明确报告3840×2160原屏、1920×1080返回图、坐标倍率2.0，本轮据此处理坐标，没有假定沿用上轮倍率。

本轮首次Shift+I出现输入法候选条；Esc取消、Ctrl+Space切换当前输入状态后，Shift+I实际显示Information，Shift+S实际进入Status。Esc返回后，经Edit→String、Up四次、Enter打开属性框，实际读到A/240/1，再Esc取消并退出选择。所有结论依据原生图及实际状态，没有把发出快捷键当作菜单响应。

## 当前层切换、显隐与恢复

通过 `Shift+C → Shift+L` 实际显示Current→Select Layer，原始Current显示Top Layer；随后 `Shift+B` 选择Bottom Layer，工作状态栏实际变为 **L: Bottom Layer**，没有仅凭按键推断切换。

在Bottom Layer为当前层的条件下，`Shift+S → Shift+T` 进入Setup→Toggle Layers，Top Layer初始On。Enter设为Off时，菜单内仍保留旧画面；**Esc退出菜单完成重绘后**，A及四条尺标全部消失。再次进入同一菜单，将Top Layer恢复On并Esc退出，五个对象重新出现。没有再次触发上轮“CURRENT LAYER MUST BE TURNED ON”保护，也没有改变图层颜色。

像素统计使用客体区域 `[100,40,551,421)`，排除菜单与底部状态栏，仅取几何颜色RGB(255,85,85)：

| 工作状态 | 区域内红色像素数 | 与基线的关系 |
| --- | ---: | --- |
| A与尺标可见，pt_001 | 3585 | 基线 |
| Top Off退出重绘，pt_008 | 0 | 文字与尺标均消失 |
| Top On恢复重绘，pt_009 | 3585 | 红色像素集合对称差为0 |

这验证本轮同层对象的显示开关行为，不证明内部对象布局或生产输出。基线和恢复图的底部当前层文字可能不同，像素一致结论只限上述几何区域及颜色集合。

## 独立标定与无遮挡A端点

测量使用 `scenes/a/captures/pt_001.png` 的640×480原生像素，左上为(0,0)、X向右、Y向下。两根分离竖尺的实测X条带为168–172及468–472，中心170及470；下横尺Y条带384–388、左上短横尺184–188，中心386及186。均为5像素宽。

因此横向尺度由两竖尺中心距300像素/600mil得到 **+0.5像素/mil**，纵向尺度由两横尺中心距200像素/400mil得到 **−0.5像素/mil**。本轮无需从端帽外缘估计长度，也不以文字反求尺度；整数栅格中心估计仍按约±1像素理解，不能称为内部视图参数的精确读取。

标定映射为 `u=170+0.5×(x−1800)`、`v=386−0.5×(y−1600)`，文字原点对应 **(270,186)**。参考中心本身参与标定，其零拟合残差不是独立亚像素精度证明；左上短尺右端约(220,186)、右竖尺上端约(470,286)也与板坐标投影相符。

用既有只读静态研究工具产生A/240/方向0预测，没有重跑函数仿真或改动工具的静态证据标记。与图中可独立辨认、已移开尺标的五个不同几何端点比较如下：

| 板坐标端点 | 预测客体像素 | 最近笔画像素 | 图像距离，像素 |
| --- | --- | --- | ---: |
| (2000,2000) | (270,186) | (270,185) | 1 |
| (2000,2080) | (270,146) | (270,146) | 0 |
| (2080,2240) | (310,66) | (310,66) | 0 |
| (2160,2080) | (350,146) | (350,146) | 0 |
| (2160,2000) | (350,186) | (350,185) | 1 |

原点到顶点纵距120像素，左右竖笔画横距80像素。两侧竖线最后着色像素分别止于Y=185，距预测基线Y=186各1像素；此结果保留为像素端部现象，不能直接判为原解释器几何错误。

`pixel-measurements.json` 逐条记录预测线段到最近同色像素的图像支持。所有不同几何笔画位置现已可见，但A中同一横线的两次反向绘制在静态图像中重合，**不能凭一张图证明两次绘线分别执行**。最近同色像素距离也不是原绘线实参、完整栅格算法、笔宽或铜面积的误差。DS:d59a、字体指针与完整/简化分派仍未观测。

## 缩放入口、门禁停止及防护修正

恢复显隐后，`Shift+Z`实际打开Zoom菜单，原生pt_010可读到Redraw、Pan、Expand、Contract、All、Keyboard、Select、Window、Board。本轮明确确认了可操作的入口，随后准备 `Shift+K` 进入Keyboard项；但该动作的前置ControlStatus连续16次为user、generation50，在30秒期限内未恢复，首末wait_seconds约9.7507903和9.9629106。客户端按既定期限退出，**K未发送，Keyboard输入框未取得，实际缩放前后对照未执行**。不能从0.5像素/mil宣称内部缩放值或完整/简化路径已确认。

本轮还发生必须保留的执行失误：PowerShell同一组合命令在MCP请求失败后没有检查LASTEXITCODE，预排的capture脚本继续调用两次Orca宿主菜单点击，生成pt_011。它没有发送客体缩放键，但属于门禁失败后的不应继续动作；该图及两次原始返回保留，**不计为可接受验证**。检查stderr根因后停止全部GUI，没有重连、修改门禁、切换入口或启动F。此前两次MCP后置Snapshot另报“Previous screenshot flash did not close before capture”，相关菜单/属性以已保存的独立客体原生图判断，没有把缺失Snapshot视作成功截图。

按父代理要求，在保留修改前脚本后仅离线修正本轮忽略目录的辅助入口：capture-native、run-orca及mcp-request在首个动作前检查停止标记；capture每次输入前再次检查；公开CLI失败会写停止标记；PowerShell包装明确检查LASTEXITCODE并抛出失败，阻止后续组合命令。没有修改第三方包或产品工具。

`verify-guards.py` 离线检查三个入口的停止拒绝，并用模拟subprocess验证一次工具失败会阻止后续调用，4项通过且实际桌面调用0次；PowerShell停止标记检查也通过，实际输入0次。PowerShell脚本为兼容本机Windows PowerShell以UTF-8 BOM保存，这与必须无BOM的DOSBox配置是不同文件类型。原调用证据及修改前脚本均保留，修复后没有再尝试GUI。

## 主要原图与摘要绝对路径

以下原图均640×480；全部截图、日志、配置和脚本的绝对路径及SHA-256由E下 `evidence-index.json` 索引，原程序与图片均不提交。

| 原图绝对路径 | 用途 | SHA-256 |
| --- | --- | --- |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/scenes/a/captures/pt_001.png` | 无遮挡A及独立尺标 | `98c2c0b4fda19b974ac8f1043b44dc5f14715e79e661a802d654442f3afafc5d` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/scenes/a/captures/pt_002.png` | 实际文件和计数 | `3275b666af59430f96fd4a888ae9fcd3a944255af0fc572df4c1edc415902de9` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/scenes/a/captures/pt_003.png` | A/240/1属性 | `18e8798441e8d43129aca0cf815fdaa72105405cc0d8f8055a521f804a8b1a06` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/scenes/a/captures/pt_006.png` | Bottom Layer当前层 | `675e5699430286ad6464c66d591d46ce6cbbeacd0e8fe5ec15c7537c01f99dcc` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/scenes/a/captures/pt_008.png` | 隐藏后无几何红色像素 | `37423542c95ebdfe95af867eee5a3d719b933aa28cc2c0edb5a622b6ec326934` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/scenes/a/captures/pt_009.png` | 恢复后重现 | `675e5699430286ad6464c66d591d46ce6cbbeacd0e8fe5ec15c7537c01f99dcc` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/scenes/a/captures/pt_010.png` | 有效Zoom菜单 | `f150a9f86636cb6e317d792e50f5e98457b8bdb22d1a1355f3878d657c196a53` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/scenes/a/captures/pt_011.png` | 门禁后误执行捕获，未采纳 | `d054f2dedcdd6f86df2f97efccd71d05b4ab78ef8299701d9829592a6941cbda` |

总汇绝对路径为 `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-next/verification-summary.json`，测量为同目录 `pixel-measurements.json`；门禁的16份逐次返回为 `step-030-a-zoom-keyboard-gate-00.json` 至 `-15.json`，根异常在 `mcp-stderr.log`，停止标记为 `stopped-error.json` 与 `input-stopped.json`，防护核验在 `guard-verification.json` 和 `powershell-guard-verification.json`。

`input-checks.json` 实际核验原安装99文件、历史副本103文件、A/F两份各104文件，前后集合及SHA-256全部相同；两份DOSBox配置摘要未变且无BOM。PT.EXE及TRAXEDIT.OVR继续匹配已核对摘要 `abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968` 和 `cab0fc0571c5a295c396bd6479a57f060bb18a01d2c2ffc5b438cc1b65f8a0d8`。

清理前重新核对PID4092映像和含本轮a配置的命令行，仅终止该目标；客户端PID10724及其MCP子进程已在门禁失败后退出。最终 `processes-final.json` 匹配集合为空，没有清理其他应用。后续任务必须重新只读核对控制状态，明确恢复允许状态后才能输入；本轮不提前尝试。

本轮仅提交本文，保留d5931ea及旧报告，未修改dev/main、未合并或推送。文档执行 `git diff --check`，未改产品而不重复Qt构建、CTest或函数仿真；父工作区负责集成，下一产品0.11.0 GUI验收应使用新Task/Dispatch。
