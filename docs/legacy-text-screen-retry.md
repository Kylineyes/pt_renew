# 原文字形现场重试：A240 与独立尺标

本轮于2026-10-25晚开始，26日凌晨结束；使用当前Pi会话，实际环境为 `PI_PROVIDER=deng`、`PI_MODEL=gpt-6.1-sol`、`PI_REASONING_LEVEL=high`。工作分支 `Kylineyes/verify-text-screen-sol`，起点为上轮提交 `48f8178886de485c79dc241495bfd57e5a8f67f1`，未覆盖或改写该提交。产品保持 **0.10.0**，**`runtime_verified=false`**。

**本轮取得有效的AUTOTRAX启动、PCB加载状态、A240文字属性和640×480客体原生图，并完成范围有限的独立尺标与可见端点对照。** 父代理在任务中将本轮收口范围明确为A240单字符和尺标阶段，F、高度及方向变体不作为本轮结束前提。顶层隐藏被原程序的当前层保护拒绝；内部缩放、实际导入状态、被尺标遮挡的笔画及后续变体继续未验证。

## 验收结果

| 项目 | 状态 | 实际事实与边界 |
| --- | --- | --- |
| 当前Pi模型、独立分支与旧成果保护 | 通过 | 实际环境匹配指定模型/强度；未另起子代理；48f8178保留 |
| 重新核对桌面与残留进程 | 通过 | 本轮初始原生前景为普通应用；无DOSBox或pt-renew残留；LockApp存在但非前景，不将其进程存在当作锁屏 |
| 新副本、正确挂载、无BOM及独立日志 | 通过 | 本轮独立创建13场景，只有a240实际启动；每场景104文件；配置加载行指向本轮绝对路径 |
| 原生目标身份及启动页 | 通过 | PID21804/HWND2691042；前景反复与目标一致；原生图显示AUTOTRAX1.57及VGA640×480 |
| 工作文件与计数 | 通过 | Status实际读取SCREEN.PCB、C:\PT、Strings=1、Tracks=4；其他对象计数为0 |
| A240文字属性 | 通过 | Edit String实际显示Text=A、Size=240、Line Width=1；单个Esc取消，没有修改字段 |
| 同层独立尺标可见性 | 通过 | A及原点十字、L形尺标同时可见；输入全为1层；Setup显示Top Layer，切换颜色后五对象一起重绘为相同新色 |
| 顶层隐藏与恢复 | 阻塞 | Toggle Layer Display显示Top Layer=On；关闭当前顶层被“CURRENT LAYER MUST BE TURNED ON”拒绝，未完成隐藏/恢复；本轮未切换当前层后重试 |
| 客体原生截图 | 通过 | 通过DOSBox Capture→Take screenshot取得11张640×480 PNG，不含宿主窗框或输入法覆盖 |
| 独立像素比例、原点和轴向 | 通过，有限测量 | 原点(240,186)，横向约+0.5像素/mil，纵向−0.5像素/mil；横尺端帽估计带约±1像素的不确定性 |
| A可见端点与部分笔画图像支持 | 通过，有限对照 | 顶点和右上端点命中预测像素；右下最后着色像素距预测端点1像素；不是全部笔画或绘图算法验收 |
| 内部视图缩放值及完整/简化路径 | 未验证 | 原生图比例可测，不等于读取内部缩放变量；没有截获运行绘线或简化调用 |
| 实际导入变换状态、字体远指针 | 未验证 | 未读取DS:d59a或字体指针；可见形状不能证明这些全局状态 |
| F、高度240/251/252、AA/A A、旋转镜像 | 未验证 | 13份隔离场景已准备，除A240外均未启动；不能把准备完成记为行为通过 |
| 输入前后摘要与清理 | 通过 | 15组文件集合及SHA-256全部无变化；目标、桌面客户端及其MCP子进程均已退出 |

## 本轮与上轮的区别及实际操作

本轮证据根目录E为以下绝对路径，所有原图、配置、日志、脚本及完整摘要仅保存在这里：

```text
C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/
```

上轮只有被其他应用遮挡的宿主截图，未确认启动页。本轮没有沿用该结论：先创建新的 `worker-status.json`、重新记录 `native-initial.json`，再从已核验的历史副本复制到全新场景。原安装 `D:/project/pt_renew/pt` 99文件及历史verification-40副本103文件只读，C/D仅挂载本轮 `scenes/a240/runtime`。未执行旧verification-40准备脚本，未重复函数仿真。

本轮DOSBox-X为2026.10.01，映像SHA-256 `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832`。实际启动命令使用本轮 `scenes/a240/dosbox.conf`，cwd为本轮 `runtime/pt`。stderr第2行明确记录本轮配置加载，独立日志第68行记录执行pt.EXE；随后第130–131行记录SCREEN.PCB打开。日志与Status共同支持载入结论，单凭执行日志不判定载入通过。

按已加载的orca-cli技能及本机公开帮助操作，首先确认PID21804、HWND2691042及可辨启动页。Orca `press-key Return`、`hotkey Shift+Return`曾返回成功但未立即取得可辨工作画面；宿主Capture菜单则有可见响应。通过Main→Capture keyboard后，再次Return取得A与尺标画面，但未以先后关系认定哪个单独动作解决了输入。后续Orca Return/Shift+I未唤出菜单，Shift+I出现了输入法候选；Esc取消候选、Ctrl+Space切换当前输入状态后仍未取得Information。一次客体右键也未取得可辨菜单。

当时原生前景持续属于目标，未遇锁屏或控制门禁拒绝。向父代理报告后，在同一授权范围内使用已安装Windows-MCP的**公开受门禁通道**核对输入兼容性。新客户端只建一个stdio连接，每步先查ControlStatus，最多等待30秒；所有Shortcut/Click前再强制核对原生PID/HWND，失配即停止。没有修改第三方包、控制阈值或门禁，也没有绕过拒绝切换入口。

Windows-MCP `Shortcut("enter")`实际出现主菜单，`shift+i`实际出现Information，`shift+s`实际出现Status；随后Esc返回工作区，`shift+e`、`shift+s`实际进入Edit→String。鼠标未选中文字后，改用已验证的键盘Up四次，将客体光标从(2150,1900)移至(2150,2000)，Enter实际打开属性框；读取A/240/1，再Esc取消。

MCP Snapshot明确报告原屏3840×2160、返回图1920×1080及坐标比例2.0。一次点击遗漏倍率，实际打开了DOSBox CPU菜单，立即Esc取消，没有选择CPU选项；后续按2倍传入(380,306)，没有据此宣称选中A。最终文字选择使用上述键盘路径。宿主截图裁剪只为阅读，不用于像素测量。Win32观察进程的DPI坐标、Orca窗口坐标及MCP缩图坐标没有混用于测量。

图层步骤经过Setup→Layer Colors：Top Layer初始颜色12；Enter将会话颜色改为13，Left未恢复，Esc关闭菜单后重绘为紫色。这个内存显示设置变化如实保留，没有保存PCB或默认设置。随后Setup→Toggle Layers显示Top Layer=On；Enter试图关闭时明确被当前层保护拒绝。警告Esc后返回Toggle菜单，后续Shift+Z仍停留在该菜单，**不是成功打开Zoom或改变缩放的证据**。再次Esc关闭菜单后固定最终原生图，停止GUI输入。

## 独立尺标与端点测量

测量只使用原生 `pt_001.png`，640×480，像素左上角为(0,0)，X向右、Y向下。参考线来自独立合成FT记录，均为1层、宽10；文字为FS，高240、方向0、宽1、原点(2000,2000)。没有使用文字自身反求比例。

| 独立参考 | 板坐标，mil | 原生图观测或中心估计，像素 |
| --- | --- | --- |
| 原点十字横线 | (1920,2000)→(2080,2000) | 中心端点约(200,186)→(280,186) |
| 原点十字竖线 | (2000,1920)→(2000,2080) | 中心端点约(240,226)→(240,146) |
| L形横尺 | (2000,1600)→(2400,1600) | 中心端点约(240,386)→(440,386) |
| L形竖尺 | (2000,1600)→(2000,1800) | 中心端点约(240,386)→(240,286) |

直线内部实测竖尺X条带为238–242、L形横尺Y条带384–388、原点横线Y条带184–188，均为5像素宽。因此其中心分别为X=240、Y=386和Y=186。纵向比例由两个独立横线的200像素中心距除以400mil坐标差得到−0.5像素/mil。横尺最右着色外缘为X=442，扣除实测半宽2估计端点X=440，得到横向0.5像素/mil；该端帽中心估计约有±1像素不确定性，对应约±0.0025像素/mil，不能写成读取到的精确运行时缩放值。

由此使用映射 `u=240+0.5×(x−2000)`、`v=186−0.5×(y−2000)`。其余十字/L尺中心估计与该映射的残差为0像素；这些是有限栅格中心估计，不能将其包装成亚像素测量精度。

只读调用既有静态研究工具，得到A在高度240/方向0下的预测。未执行原函数仿真，未改变工具的 `static_instruction_derivation` 或 `runtime_verified=false` 标记。独立尺标建立映射后，比较如下：

| A的板坐标端点 | 预测客体像素 | 实际图像支持 | 结论 |
| --- | --- | --- | --- |
| (2000,2000) | (240,186) | 落在同色原点竖尺内 | 文字端点被覆盖，未独立验收 |
| (2000,2080) | (240,146) | 同色竖尺上端与文字折点重合 | 未独立验收 |
| (2080,2240) | (280,66) | 顶点着色像素(280,66) | 可见端点偏差0像素 |
| (2160,2080) | (320,146) | 横线及右竖线起点(320,146) | 可见端点偏差0像素 |
| (2160,2000) | (320,186) | 右侧竖线最后着色像素(320,185) | 可见端部相差1像素；未认定为几何或解释器错误 |

A的原点到顶点纵距120像素，原点到右侧竖线横距80像素。两条不被尺标大面积遮盖的斜线分别采样81点，预测点到最近同色像素的平均距离均约0.246914像素、最大0.5像素；右竖线采样41点，平均约0.024390像素、最大1像素。原生图实际支持这些预测位置，但**最近同色像素距离不是绘线调用中心线误差或完整栅格等价证明**；它不能分辨重复横线、被遮挡笔画或铜面积。

本轮不能宣称A全部六次绘线都独立通过。原点附近两端和左竖笔画被同色宽尺标遮挡，下一轮应在保持独立坐标标定的前提下移开参考十字或使用不同颜色/层，并独立确认显隐、缩放和绘制路径。F、251/252、AA/A A及方向变体继续用新尝试目录逐项进行。

## 原生截图与摘要索引

以下为主要原图的**绝对路径及SHA-256**；所有原生图均640×480。其他宿主截图、工具返回、配置、日志、脚本及前后文件摘要均由E下 `evidence-index.json` 索引绝对路径与SHA-256。

| 原生图绝对路径 | 内容 | SHA-256 |
| --- | --- | --- |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/scenes/a240/captures/pt_000.png` | AUTOTRAX启动页 | `eeb87e89693a12bdc2008113016e6cfc8fd29d36d037b3f9a337897066bfb628` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/scenes/a240/captures/pt_001.png` | 工作画面及测量输入 | `c9339a5fbca63407933ed386355a1fc5a4e6aaf274a8ed0bf289381ee453c486` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/scenes/a240/captures/pt_002.png` | Status | `c99fe90eebc3763a5999fd5e5e8f41077a186781a1beba851a88f0a8de19d996` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/scenes/a240/captures/pt_003.png` | A属性 | `9f9f3a1cf99f65e3dcbded18b18357968106fc7003bda6e462c47b27e404bf8b` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/scenes/a240/captures/pt_007.png` | 顶层On及颜色变化 | `950139d28f0d8b1d7e645be7ff1dfbda7a725475f4490ff37512e6e6d3ea3444` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/scenes/a240/captures/pt_008.png` | 当前层关闭被拒绝 | `a34763342b97e3075c17c832784dc5ded2958eab3e1a1a8a26635e2dc7da6f0f` |
| `C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/scenes/a240/captures/pt_010.png` | 关闭菜单后的最终工作图 | `945369e744b8fcd24fbb258707e3ddf274bf88db60d4f9aff1980432be0642ab` |

总汇绝对路径：`C:/Users/rikideng/orca/workspaces/pt_renew/verify-text-screen-sol/.local-analysis/text-screen-retry-20261025/verification-summary.json`；测量明细为同目录 `pixel-measurements.json`，可由现有Windows-MCP虚拟环境中的Pillow执行 `measure-a240.py` 复算。系统Python的Pillow扩展导入失败，故使用已有虚拟环境，未安装依赖。首次/关键前景记录为 `native-initial.json`、`native-launched.json`、`native-before-enter*.json`，MCP每步另有前后原生观察和ControlStatus记录。

输入继续匹配已核对版本：PT.EXE SHA-256 `abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968`，TRAXEDIT.OVR SHA-256 `cab0fc0571c5a295c396bd6479a57f060bb18a01d2c2ffc5b438cc1b65f8a0d8`。`source-before/after.json`、`historical-copy-before/after.json`及每个场景 `inputs-before/after.json` 实际核验15组输入：99、103及13×104文件，集合与SHA-256全部未变化。13份配置摘要一致且无BOM；场景运行中的颜色调整没有落盘。

结束前向同一MCP连接发stop，客户端及服务子进程退出；核对本轮DOSBox映像和含本轮配置的命令行后仅终止PID21804。即时查询短暂显示退出中的无映像PID条目，最终 `processes-final.json` 明确匹配集合为空。未操作无关应用、其他工作区或dev/main。

本轮仅提交此专题报告，原程序、字体、截图、配置、反编译和构建产物均不提交；没有修改产品、工具或根README/HANDOFF/PROGRESS。文档运行 `git diff --check`，未重复Qt构建、CTest或既有函数仿真矩阵。父工作区负责集成；完整原文字形运行验收继续未完成。
