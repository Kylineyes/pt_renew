# 封装库与元件

[文档导航](../README.md) · [使用指南](../usage.md) · [完整资料索引](../reference-index.md)

## 先看结论

<a id="explore-ex-020"></a>

LIB 可以在独立窗口只读浏览、筛选、缩放并查看图元字节来源；PCB 内元件可以检索定位。封装放置、替换、库写入／合并／压缩及元件编辑尚未实现。

[探索 EX-020](../exploration-backlog.md#ex-020)。

## 第一层分析：库定义和板上实例

库定义保存可复用封装，PCB 的 COMP 保存板上实例及其几何。实例可能已修改焊盘、标签和属性，不能因封装名相同就用库覆盖板上对象。元件内部图元采用板坐标，不能在解析后重复平移或旋转。

当前 LIB 样例采用 16 字节记录、200 个目录槽；目录指针是记录号，需乘 16 得字节偏移。目录次序不保证等于数据物理次序；名称残留也不证明槽仍有效。[目录静态路径](../library-directory-state.md#directory-result)已证查名排除 `FFFF`、删除保留名称／计数、初始化使用双 `FFFF`、新增复用首个空槽；别名和非零保留字段仍缺证，继续严格拒绝。字符串续记录必须与相应焊盘或文字绑定。

## 第二层分析：从目录到独立预览

| 实现入口 | 职责 |
| --- | --- |
| [FootprintLibrary.h](../../src/domain/FootprintLibrary.h) | 整库快照、目录及条目状态 |
| [LegacyLibraryReader.h](../../src/io/LegacyLibraryReader.h) | 指针、范围、图元数及字段解码 |
| [LibraryBrowser.h](../../src/ui/LibraryBrowser.h) | 独立窗口、筛选、后台读取与预览 |
| [ComponentTableModel.h](../../src/application/ComponentTableModel.h) | PCB 实例筛选与定位数据 |
| [InspectLibrary.cpp](../../tools/InspectLibrary.cpp) | 只读结构诊断 pt-library-check |

库与主板使用不同文档和画布。库坏头／坏指针导致整库失败；单条目含未知图元或坏续记录时拒绝该条目的部分预览，其他完整条目仍可查看。库来源显示字节偏移，PCB 来源显示文本行，不能混用。

## 第三层分析：结构证据与兼容范围

本地四个真实库共 318 个有效指针条目、8026 个图元完成当前结构检查；既有 GUI 展示 AXIAL0.4、ER28 等条目并核对来源。目录、非法记录、异步取消和窗口隔离另有合成测试。

<a id="explore-ex-018"></a>

这些结果不证明全部历史库变体、原软件逐项电气语义或逐像素一致。类型附加标志、平面连接等含义未完整恢复；字形和部分焊盘轮廓仍沿用近似预览。

[探索 EX-018](../exploration-backlog.md#ex-018)。

## 下一步怎样推进

<a id="explore-ex-019"></a>

先取得原软件库选择／预览或导出对照，确认目录及图元变体。需要放置时再明确库局部坐标到板实例的变换、实例身份、历史与写出规则；复用板图、命令和编辑模型，不将只读预览直接当成放置完成。

[探索 EX-019](../exploration-backlog.md#ex-019)。

## 按需深入

- [LIB 二进制布局与浏览](../library-analysis.md)：字段、失败策略、CLI 和原验收。
- [LIB 目录状态的静态路径与残留边界](../library-directory-state.md)：删除／初始化／复用与改名、压缩副作用、分类工具及剩余未知。
- [板图模型](board.md)：COMP 和来源。
- [选择与定位](interaction.md)、[编辑与保存](editing.md)：后续放置需要遵循的交互及历史边界。
