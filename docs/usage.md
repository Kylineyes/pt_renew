# 使用指南

[返回项目首页](../README.md) · [按软件主题了解实现](README.md) · [当前开发状态](../PROGRESS.md)

## 先选择运行版本

发布的 v0.11.0-alpha 是只读资料查看器，下载后完整解压并运行 pt-renew.exe，保留 DLL、插件和许可目录，使用附件 SHA256SUMS.txt 核对压缩包。无需安装 Python、Qt SDK 或开发工具。范围见[发布说明](releases/v0.11.0-alpha.md)。

dev 源码另有自由 FT 编辑与受限另存，需按[开发环境](qt-development.md)构建。以下“dev”操作不适用于已有 alpha 包，正式新增图元仍禁用。

## 打开板图并观察

Ctrl+O 或“文件”菜单打开已支持的 PCB FILE 4。也可运行：

~~~powershell
& ./pt-renew.exe 'D:/板图/样例.PCB'
~~~

载入后先查看文件名、摘要、图元数量和限制提示。未知记录或错误字段整体拒绝，不把局部结果当作完整板图。文字及部分轮廓为近似预览。

| 操作 | 入口 |
| --- | --- |
| 缩放／平移 | 滚轮、中键拖动，F5/F6 缩小／放大 |
| 重绘／居中 | F9 / F10 |
| 图层显隐 | 左侧复选框；从“设置”恢复面板 |
| 选择／重叠切换 | 单击，同位置再单击或画布 Ctrl+Tab |
| 清除选择 | 画布 Esc 或单击空白 |
| 属性面板 | Ctrl+I |
| 元件检索 | Ctrl+F，或画布 J→C；Enter 定位 |
| 板原点 | 画布 Ctrl+Home |

鼠标顶部菜单、Alt 访问和旧式字母使用共同命令。例如画布 F→L 与 Ctrl+O 打开同一文件对话框。旧式字母仅在画布有焦点时生效，检索和文件名输入仍可正常打字。

## 测量距离

画布 Ctrl+M 或“信息 → 两点只读测量”，依次点击两点，读取距离、ΔX/ΔY、方向和来源。Esc 退出模式并保留已完成结果，“清除测量”移除结果。

需要精确取已知模型端点时，从“信息”开启端点捕捉，或在画布按 Ctrl+Shift+M。靠近可见走线端点、焊盘／过孔中心、圆弧端点或填充角点会出现黄色标记；未命中时仍自由取点。分别检查两点来源，不把开关开启当作每点已捕捉。几何范围见[端点捕捉](measurement-snap.md)。

## 浏览封装库

Ctrl+L 或画布 L→B 打开独立只读库窗口，Ctrl+Shift+L 选择 LIB。库内 Ctrl+F 筛选名称、Ctrl+O 换库，可缩放平移及选择图元查看字节偏移。

~~~powershell
& ./pt-renew.exe --library 'D:/库/示例.LIB'
~~~

库浏览不会替换主板、放置元件或写回库。当前结构覆盖与限制见[封装库主题](topics/library.md)。

## 载入网表并检查

Ctrl+Shift+N 或画布 N→G 载入外部 NET，Ctrl+Alt+N 或 N→N 打开网络与引脚映射。选择网络高亮无歧义、无冲突的焊盘，激活节点定位。板内 NETDEF 与外部 NET 切换来源，不自动合并；换板后需重新载入外部 NET。

~~~powershell
& ./pt-renew.exe 'D:/板图/样例.PCB' --netlist 'D:/网表/样例.NET'
~~~

引脚映射不检查铜线导通。可从网络面板、“网络”菜单或 Ctrl+Alt+C 运行受限铜层分析；覆盖不完整时网络保持“无法确定”。诊断候选不等于断短路确认，不能用于生产放行。进一步阅读[网络与检查](topics/connectivity.md)。

## 编辑与另存：仅 dev

选择可见自由走线后，从“移动”菜单输入整数 mil 位移，或在画布按 Delete 删除；Ctrl+Z / Ctrl+Y 撤销／重做。元件内部走线及其他图元仍只读。

Ctrl+Shift+S 或“文件 → 另存为新 PCB”选择尚不存在的目标。原件和已有目标不覆盖；成功后设置保存点，历史保留。取消或失败保留修改和历史。Ctrl+S 覆盖保存、正式新增、元件编辑和布线未开放。行为边界见[编辑与另存](pcb-save-as.md)。

## 按需使用只读诊断

在源码工作区启用 Qt 环境后调用相应 Release 构建：

~~~powershell
& ./scripts/Enter-QtEnv.ps1
& ./build/release/pt-pcb-check.exe --track-limit 100 'D:/板图/样例.PCB'
& ./build/release/pt-library-check.exe 'D:/库/示例.LIB'
& ./build/release/pt-netlist-check.exe 'D:/网表/样例.NET' 'D:/板图/样例.PCB'
& ./build/release/pt-copper-check.exe 'D:/板图/样例.PCB' 'D:/网表/样例.NET'
~~~

这些是不同范围的结构或几何检查，须同时检查退出码、JSON 状态和限制。PCB 检查成功不证明原 AUTOTRAX 接受文件；NET 和铜分析的退出码也不能直接表示 DRC 通过。字段与退出码从[PCB](pcb-check.md)、[LIB](library-analysis.md)、[NET](netlist-compatibility.md)、[铜分析](copper-analysis.md)各专题查阅。
