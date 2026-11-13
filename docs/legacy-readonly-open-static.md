# 历史只读挂载：菜单打开探测与固定 DOSBox-X 拒绝链

本次为 [EX-005](exploration-backlog.md#ex-005) 的有界离线子题。固定 `PT.EXE` 的菜单查找包装**确实尝试打开文件**：它调用使用全局打开模式的 Reset 包装，映像中该模式初值为 `2`，对应 DOS `AH=3Dh` 的读写访问。固定 DOSBox-X 的目录挂载 `-ro` 会设置驱动只读字段；该字段非零且访问低四位为 `1` 或 `2` 时，`localDrive::FileOpen` 在宿主打开前返回失败。PT 查找失败统一走 `.MNU Not Found.` 提示，因此“文件存在却报 Not Found”有了具体静态机制支持。

**历史那一次实际 `AL`、驱动对象字段、DOS 返回码和系统调用仍没有记录，不能据此宣布唯一历史根因已证。** 本文证明固定文件的默认值、调用关系与失败条件，结合旧配置和原图解释其相容性；没有重跑旧场景，没有取得瞬时 I/O，也不结算 EX-005 整体。其它配置来源、DFT 字段消费和输入事件链由对应协作任务处理。

<a id="scope-and-inputs"></a>

## 范围、身份与输入

任务 `task_187604f25201`／Dispatch `ctx_da3215a4b70e`；分支 `research/readonly-open-static`，起点 `6c18d3eee998258129ed51d31133febbcd82caa0`。实际 Pi `01a1d35d-7ff3-72e4-ae8d-4e46727d2e84`，Orca 会话 `29638926-e7df-45bf-b460-1cebb17b6bd5`。环境四字段、原 JSONL 的 model／thinking 事件、实际 assistant 和成功工具回执均核为 `deng/gpt-6.1-sol/high`；收到协调者已将实际领取登记普通推送到共享 dev `63a1fc6` 的回执后继续深入。

| 固定输入 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `D:/project/pt_renew/pt/PT.EXE` | 210016 | `abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968` |
| 同目录 `TRAXEDIT.MNU` | 26311 | `ed9cc5f4b9e936e7f324e4f0ac632f34bff5b08951281df9672b7f9a2da1c040` |
| `C:/Users/rikideng/scoop/apps/dosbox-x/2026.10.01/dosbox-x.exe` | 25836544 | `a82adcfa7af2784566cfeff74c077cefed08505396db2948b7e6aa7d4cee0832` |

PE 首选映像基址 `0x140000000`，版本现场沿既有报告的 `2026.10.01 / b6abbd5`。本次读原字节，不执行映像取版本。PT 与 MNU 的当前摘要均匹配初次调查的 `source-sha256.json`；摘要相同不证明历史期间没有瞬时写入或恢复。

工具为既有 r2／rabin2 `6.2.6`、Python／Capstone。Capstone 分别记录 module `5.0.7`、distribution `5.0.9`、native API `(5,0,1280)`。复用原 worker 的 `ex-005-config-source/` 中 `E-triage-imports`／692 项导入、节表和字符串缓存，核缓存摘要；本次只在自己的忽略目录写入脚本和结果。radare2 技能引用的 `field-journal/precedent-reverse.md`、`tool-index.md` 实际缺失已保留，不 bootstrap；没有重新诊断 REA／Ghidra、安装或下载。

<a id="historical-observation"></a>

## 历史材料实际说明了什么

历史入口为 `C:/Users/rikideng/orca/workspaces/pt_renew/main-2/.local-analysis/`。本次只读核初次配置、原图及源摘要，不将较晚八槽日志拼作初次运行的 trace。

| 原件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `dosbox-readonly.conf` | 453 | `e9914a949a498e3f69144bb3f2b7cfb65bbc53b4d05a669e2b9f46d0e9ae5014` |
| `dosbox-snapshot.conf` | 589 | `2d205e981ebd9eabc4f11c9d7c94f9c0fc24676f8c65df1805c6d69d1d502a8d` |
| `dosbox-vga.conf` | 606 | `37ebf4e8ad52f99dc09b954e97c5557c19a7d70f32c9c5c34e174471c1237110` |
| `pt-initial.png` | 32276 | `623237955f9750daa35aba23dc734846500b9042ce02087babace4b6ae4b82e6` |
| `source-sha256.json` | 8470 | `81e2fdf01997e8eadbc18082452cecca378fbc91c630349a497e44fb0c4d0586` |

失败配置的 autoexec 为 `mount c "D:\project\pt_renew\pt" -ro` → `c:` → `pt placed.pcb`，即原安装成为客体 `C:\` 根目录；没有 `cd \pt`，也没有 D 挂载。图像实际显示 `Drive C is mounted as local directory D:\project\pt_renew\pt\`、`TRAXEDIT.MNU Not Found. TRAXEDIT Program Aborted.`，随后回到 `C:\>`。本 Pi 离线实际 read 原 PNG，自己的原 JSONL 记录 `083746d4`／UTC `2026-11-13T05:33:10.237Z` 的 image 字节 SHA 与原件一致；这是迟后的原件复核，没有新截图或桌面请求。

初次配置没有 `[log]`；在上述历史目录**顶层初次材料**没有定位到该次 stdout／stderr／INT21 日志。该有界盘点不代表穷尽所有历史存储；更不能把“没找到调用记录”解释为没有调用。原图版本文字也不补成当时进程映像 SHA 的独立见证。

可写 snapshot 将隔离根同时挂到 C／D，再 `cd \pt`，保留旧 DFT；后续 VGA 配置还改为 OpenGL、`vgaonly`、3000 cycles，改名 DFT 且不传 PCB 参数。它们同时改变多个条件，保留[初次调查](initial-assessment.md#explore-ex-005)所述非单变量限制，不能只用后续成功归因 `-ro`。本次未重新执行这些配置。

<a id="pt-probe-chain"></a>

## PT：Not Found 来自打开探测的布尔结果

地址沿[菜单静态报告](legacy-menu-keypath.md)的分析装载基段 `0x1000`。设分析段为 `S`、段内偏移为 `IP`，原文件偏移为 `0x3de0 + (S - 0x1000) * 16 + IP`。下表将原文件远调用段与分析段明确区分；它们都不是本次实测运行段。

| 分支／指令 | 原文件偏移及关键字节 | 可核行为 |
| --- | --- | --- |
| 分析 `1000:0126` | `0x3f06`，`9a93434e22` | 原远调用 `224e:4393`，分析目标 `324e:4393`；构造 `TRAXEDIT.MNU` 后进入查找 |
| 分析 `1000:012b..012d` | `0x3f0b`，`08c0 7545` | 只测 AL 是否非零；零走错误文字，非零到 `0174` 后调用菜单装载 |
| 分析 `324e:43be` | `0x2a67e`，`9a6409662a` | 原调用 `2a66:0964`，分析目标 `3a66:0964`；包装在栈中保存／回传候选文件名 |
| 分析 `3a66:099c..099d` | `0x2eddc`，`0e e856ff` | 先对当前候选调用同段 `08f6`，成功即可返回；失败才尝试环境搜索候选 |
| 分析 `3a66:092a` | `0x2ed6a`，`9a881c972c` | 原调用运行库 `2c97:1c88`，分析 `3c97:1c88`，给文件对象赋名 |
| 分析 `3a66:0935..0939` | `0x2ed75`，`b80100 50 9ab61c972c` | 压入 `1` 后调用 Reset 包装；`1` 是记录大小，不能把它误称 DOS 写访问模式 |
| 分析 `3a66:093e..0944` | `0x2ed7e`，`0e e88dff 09c0 7511` | 调 `08cf` 获取 I/O 结果，AX 非零返回 false；零返回 true 并关闭探测句柄 |
| 分析 `3c97:1cb6..1cbd` | `0x32406`，`a01c0c b43d 33d2 eb06` | `AL=[DS:0c1c]`、`AH=3d`；跳入公共打开体 |
| 分析 `3c97:1cf4..1cfc` | `0x32444` 起，末 `cd21` 在 `0x3244c` | 将文件对象 `+0x30` 的非空文件名交给 DS:DX，`CX=0` 后 `INT21` |
| 分析 `3c97:1cff..1d01` | `0x3244f`，`7306 a3160c` | CF 表示失败时把 AX 存到 I/O 错误单元 `DS:0c16` |

`3a66:08cf` 在 `DS:fa08/fa0a` 的 I/O 回调指针为空时调用运行库 `3c97:0207`，取出并清零 `DS:0c16`；非空时改走间接回调。本次保留这个守卫，不将任意回调值当作已恢复。`3a66:0964` 会对其它候选重复同一 `08f6` 探测；全失败时返回 false。这里只确认这些尝试共用同一打开包装，没有扩展恢复整套搜索算法或 DFT 路径。

程序错误文字分别是 `1000:003a` 的长度前缀字符串 `.MNU Not Found. ` 和 `1000:004b` 的 ` Program Aborted.`。错误分支不区分“路径不存在”与“存在但不能按请求模式打开”，所以提示本身不能证明 DOS 返回的是文件不存在。

### 打开模式字节的默认值

MZ 入口为原 `0000:05c0`，首调用原 `2c97:0000`；其 DS 初始化指令位于文件 `0x30750`，`baa62e 8eda`，即原数据段 `0x2ea6`。MZ 重定位表零基索引 3947 的项覆盖段立即数所在的原 image offset `0x2c971`／文件 `0x30751`，不能将这个段值当磁盘偏移或历史运行段。

由此映像中 `DS:0c1c` 位于 `0x3de0 + 0x2ea60 + 0xc1c = 0x3345c`，原字节为 **`02`**，相邻 12 字节为 `000000000000000002000000`。该包装将这个字节直接装入 AL，因此**在它保持映像初值时，请求为 `AX=3d02`，即读写打开，而非纯读 `3d00`**。文件对象记录大小 `1` 取自另一个参数，最终存入对象 `+4`。

本次没有历史寄存器，也没有证明所有初始化／别名写入／回调在任意运行中均不改变该全局字节；不得把“固定映像初值 2”改写成“历史调用实测 AL=2”。这不影响本次给出可逐字节复核的默认路径和条件性失败机制。

<a id="dosbox-ro-chain"></a>

## 固定 PE：-ro 到目录驱动拒绝条件

下表 VA 按首选基址，RVA 为 `VA - 0x140000000`。PE `.text` 在这里的文件偏移为 `RVA - 0xc00`；`.rdata` 另按节表映射，例如模式字符串 RVA `0x14cdd68` 的文件偏移是 `0x14cc768`，不能套 `.text` 的差值。

| VA／RVA | 原文件偏移、关键字节 | 静态含义 |
| --- | --- | --- |
| `140498273`／`498273` | `497673`，`488d1546480201` | MOUNT 参数循环引用 `-ro`，字符串 VA `1414bcac0`；比较相等分支到 `498291` |
| `1404982bd`／`4982bd` | `4976bd`，`c644247401` | 命中后将本地只读字节 `[rsp+74]=1`；其初值在 `498240` 为 0 |
| `14049833a`／`49833a` | `49773a`，`c644247400` | 后续 `-rw` 命中可清零同一字节；不能宣称只要出现 `-ro` 就永远只读 |
| `140499fb0`／`499fb0` | `4993b0`，`e80b9b0600` | 普通目录分支调用 `140503ac0` 构造驱动；没有将镜像／overlay 分支混入本次结论 |
| `140499fbf..499fc4` | `4993bf`，`0fb64c2474 884808` | 将该本地字节写入新驱动对象 `+8` |
| `140503b3d..503b44` | `502f3d`，`488d05eca5fc00 49894500` | 构造器将对象虚表设为 `1414ce130` |
| 虚表 `1414ce138`／`14ce138` | `14ccb38`，`80ff4f4001000000` | 虚槽 `+8` 指向 `1404fff80`，由函数内部 `localDrive::FileOpen` 字符串交叉确认 |
| `1404fffc1..4fffc4` | `4ff3c1`，`418bf4 83e60f` | 将传入 `r9d` 保存的原 flags 取低四位到 ESI |
| `1404fffc7..4fffd5` | `4ff3c7` 起，`807b0800 741d 83fe01 7405 83fe02 7513` | `object[8] != 0` 且低四位为 1 或 2 时，进入拒绝 |
| `1404fffd7..4fffe5` | `4ff3d7`，`b813000000 668905c7062701 32c0 e97d030000` | 内部错误单元 `1417706aa` 置 `0x13`，返回 false；位于所有宿主打开分支之前 |

`-ro` 和 `-rw` 原串相邻，文件 `0x14bb4bc` 为 `2d7277002d726f00`。本次仅解释普通 `MOUNT <drive> <directory>` 路径。历史配置只有 `-ro`，未写 `-rw`；没有历史参数循环／驱动对象的运行快照来补证它当时的实际字段。

### flags 与宿主访问

通过只读守卫后，固定函数按低四位选择：

| flags 低四位 | 宿主宽字符模式 | 原生 CreateFileW 路径的 desired access | 只读驱动的上述守卫 |
| --- | --- | --- | --- |
| 0 | `rb` | `0x80000000`，GENERIC_READ | 通过 |
| 1 | `rb+`；已原生打开后包装流使用 `wb+` | `0x40000000`，GENERIC_WRITE | 拒绝 |
| 2 | `rb+` | `0xc0000000`，GENERIC_READ \| GENERIC_WRITE | 拒绝 |
| 4 | `rb` | `0x80000000` | 通过，保留固定实现的特殊值，不泛化为 DOS 全版本定义 |
| 其它 | 尚未进入宿主打开 | 无 | 该函数另一分支置内部错误 `0x0c` 并失败 |

UTF-16LE `rb+` 位于 VA `1414cdd68`／文件 `14cc768`，字节 `720062002b000000`；`rb` 位于 VA `1414ae860`／文件 `14ad260`，字节 `720062000000`。`140500229` 的后端开关决定进入原生 `CreateFileW` 分支还是向 `140db6c7c` CRT 包装传入文件名和模式，不能假定历史选中哪个后端。

原生分支在 `140500255` 取原 flags 的 `0x70` 共享字段：`0x10→0`、`0x20→1`、`0x30→2`、其它→3；`14050027e..5002a1` 设置 `OPEN_EXISTING=3`、`FILE_ATTRIBUTE_NORMAL=0x80`，调用导入 `CreateFileW`。这些是**通过驱动只读守卫之后**的访问规则。在 `object[8]!=0 && access=2` 的条件下，此次 FileOpen 自身不会走到该系统调用；不意味着整个进程没有其它文件 I/O。

<a id="error-translation"></a>

## 外层错误码不能与 localDrive 内部值混同

固定 INT21 处理器的 AH 分派表位于 VA `140446fa8`；`3d` 项在 VA `14044709c`／文件 `44649c`，原 dword `33444400`，指向 RVA `444433`。该分支从客体 AL 对应单元 `141813578` 取 flags，在 `140444618` 调用 `14046b140`；失败路径将最终错误单元写回客体 AX 并置 CF。这里解释固定分派关系，没有历史实际进入该分支的 trace。

通用打开函数 `14046b140` 在 `14046b3ea..46b3f2` 把 flags 放入 `r9d`，经驱动虚槽 `+8` 调用；失败后把文件名转大写并在 `14046b447` 再调用同一虚槽。若两次均失败，它在 `14046b453` 对内部 `0x0c` 作特判，随后恢复保存的旧错误，并按访问方式／文件存在性生成最终错误。

对于低位为 `2` 的普通文件条件，`14046b469` 的 `test r13b,3` 会走 `14046b4a6` 的 FileExists 检查。虚槽 `+0x90` 位于 VA `1414ce1c0`，原 qword `202e504001000000`，目标 `140502e20`；该函数核路径转换、宿主 stat 成功且不是目录才返回 true。**若此检查为 true，通用函数在 `14046b4c5` 将最终错误改为 `5`（访问拒绝）**；不存在时还有目录检查及 `2/3` 分支。因此 `localDrive` 的内部 `0x13` 不是历史客体最终实收错误码的证明。

PT 的 `08f6` 只用 I/O 结果是否为零决定 true／false；在这些失败分支都可返回 false，经 `324e:4393` 与 `1000:012d` 到同一 `.MNU Not Found.` 提示。代码没有要求实际 DOS 错误必须等于 2。

<a id="conclusion-and-limits"></a>

## 可采用结论与精确未知

本节作为[EX-005剩余历史调用状态](exploration-backlog.md#ex-005)的具体证据入口；条件机制已定位，历史运行是否走到这些守卫仍未证。

可以将旧“符合 Pascal 读写打开失败表现”的猜测细化为：**固定 PT 的菜单存在性探测使用带全局模式的二进制 Reset；该模式映像初值为 2。固定 DOSBox-X 的普通目录只读挂载确实拒绝 access=2，而 PT 又把此类探测失败合并成 Not Found。** 这是逐字节支持的条件性机制，解释力已经强于单看报错时间或只依赖 Pascal 一般知识。

历史事实仍只到原配置和原图。尚缺当时实际 `DS:0c1c`／`AX=3dxx`、请求的最终客体路径、驱动 `+8`、两次 FileOpen／FileExists 的实际结果、最终 CF／AX，以及对应进程的系统调用记录。初始化、回调、搜索路径、配置继承或其它环境因素没有被历史单变量试验排除；不能声称已经独立恢复那一次失败的唯一原因。EX-005 保留；本次未扩大到整个 DOSBox 文件系统、DFT 消费、配置 parser 或默认根逆向。

未来若协调者另行授权运行验证，最小缺口是隔离副本上的相同文件与配置，只改变挂载读写属性，并在指定打开点记录路径／AL／驱动字段／返回值。本文只是指出缺证内容，不创建候选、GO、目标、控制服务或实机探针。

## 本机证据与验证

证据根：`C:/Users/rikideng/orca/workspaces/pt_renew/readonly-open/.local-analysis/readonly-open/`。不提交原程序、PNG、反汇编材料或 JSONL。

- `identity-and-inputs.json`：实际模型、会话、目标及复用缓存摘要。
- `pt-startup-menu.json`、`pt-file-lookup.json`、`pt-probe-open.json`、`pt-runtime-reset.json`、`pt-main-entry.json`、`pt-ioresult.json`、`pt-search-tail.json`：PT 常驻链、原字节和段／文件映射。
- `pe-mount-run.json`、`pe-localdrive-constructor.json`、`pe-local-fileopen.json`、`pe-dos-open.json`、`pe-fileexists.json`、`pe-int21-handler.json` 及对应短字符串／虚表／跳表字节文件：固定 PE 条件、访问 flags 和错误改写。
- `history-and-byte-verification.json`、`final-history-and-byte-verification.json`：历史摘要、原图实际 read 回执、PT 重定位／初值、指令逐原字节核验，以及 r2 对两处关键连续切片的独立 CLI 解码回执。
- `inspect_readonly.py`、`verify_readonly.py`：本子题只读提取／核验脚本；输出排他创建，不写原 worker 缓存。叶 thunk 没有 unwind 时仅作有界切片，不把相邻代码称为完整函数；本次未采用另一个不完整 OpenFileExtended 片段作结论。

早期 PowerShell 的通配路径传给 rg 被作为字面路径拒绝，未忽略目录初次搜索也漏掉材料；改为明确入口和 `--hidden --no-ignore` 后定位。一次临时查看误套 `.text` 的 RVA／文件差值到 `.rdata`，输出无关文本；随后按真实 PE 节映射纠正，模式字符串结论只采纳已落盘的正确映射。这些工具回执保留在本 Pi 原 JSONL，不以旧误输出作证。

仅文档和离线证据，不改产品；不运行 Qt 构建或 GUI。最终字节核验覆盖 22 份指令导出、13029 行原字节（含不同切片重复行，不称完整 CFG），两次 r2 切片解码与提取行的偏移／字节逐项一致且退出 0；历史输入摘要及原图实际 read 回执也通过。

标准 `python tools/check_exploration_docs.py` 已运行，154 份 Markdown／1091 个本地链接／41 个开放事项／116 个来源细节／138 份报告，**未通过，唯一错误为本报告尚未在 `reference-index.md` 中恰好出现一次**。依独占写入边界与协调回执，此项明确留给独立集成分支补索引及 EX-005 双向链接后重验；不冒称完整检查通过。`git diff --check` 通过，暂存报告还单独检查；原回执与最终状态保存于本树忽略证据 `validation-receipts.json`。
