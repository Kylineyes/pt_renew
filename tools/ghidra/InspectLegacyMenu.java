// 导出本项目已核对的菜单、宏和键盘常驻路径；只在本地生成研究证据。
// 应以 -process PT.EXE -noanalysis -readOnly 运行，不将输出提交到仓库。
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import com.google.gson.GsonBuilder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class InspectLegacyMenu extends GhidraScript {
    private static final String EXPECTED_SHA256 =
        "abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968";
    private static final String[][] ANCHORS = {
        {"1000:0027", "程序名"}, {"1000:0035", "菜单扩展名"},
        {"1000:003a", "菜单缺失提示"}, {"1000:0091", "宏扩展名"},
        {"324e:2c16", "段标记"}, {"324e:2c20", "消息段"},
        {"324e:2c29", "消息分隔符"}, {"324e:2c2b", "菜单段"}
    };
    private static final String[][] FUNCTIONS = {
        {"1000:00aa", "启动文件装载"}, {"1000:0420", "主菜单命令分派"},
        {"1000:0503", "Enter 菜单入口"}, {"1000:054a", "主菜单首字母匹配"},
        {"1000:05c0", "主循环"}, {"2964:36cc", "编辑器按键入口"},
        {"324e:0616", "底层键盘状态"}, {"324e:0650", "底层键码转换"},
        {"324e:0779", "输入收集"}, {"324e:08a4", "按键入队"},
        {"324e:0965", "宏展开"}, {"324e:0a30", "队列取键和宏匹配"},
        {"324e:0fa4", "菜单文字绘制调用"}, {"324e:10ae", "菜单行绘制"},
        {"324e:14ba", "菜单表绘制入口"}, {"324e:16bb", "菜单选择"},
        {"324e:2c31", "菜单文件解析"}, {"324e:4393", "文件查找包装"}
    };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1 || !Path.of(args[0]).isAbsolute()) {
            throw new IllegalArgumentException("请指定一个绝对路径，输出到新的本地 JSON 文件。");
        }
        Path output = Path.of(args[0]);
        if (Files.exists(output)) {
            throw new IllegalArgumentException("输出已存在，请使用新的证据文件名。");
        }
        if (!EXPECTED_SHA256.equalsIgnoreCase(currentProgram.getExecutableSHA256()) ||
                !"x86:LE:16:Real Mode".equals(currentProgram.getLanguageID().toString())) {
            throw new IllegalArgumentException("输入摘要或语言与已核对的 PT.EXE 不符。");
        }
        // 哈希绑定文件身份；再检查地址基准，防止复用其他装载基址的数据库。
        for (String[] anchor : ANCHORS) {
            if (!currentProgram.getMemory().contains(toAddr(anchor[0]))) {
                throw new IllegalArgumentException("数据库未按本项目的 0x1000 基段装载。");
            }
        }
        if (!"TRAXEDIT".equals(readPascalString(toAddr("1000:0027")))) {
            throw new IllegalArgumentException("程序名锚点不符，不能沿用当前地址表。");
        }

        Map<String, Object> report = new LinkedHashMap<>();
        report.put("schema_version", 1);
        report.put("evidence_kind", "static_instruction_analysis");
        report.put("runtime_verified", false);
        report.put("sha256", currentProgram.getExecutableSHA256());
        report.put("language", currentProgram.getLanguageID().toString());
        report.put("ghidra_load_segment", "0x1000");
        List<Object> anchors = new ArrayList<>();
        for (String[] anchor : ANCHORS) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("address", anchor[0]);
            row.put("role", anchor[1]);
            row.put("text", readPascalString(toAddr(anchor[0])));
            anchors.add(row);
        }
        report.put("pascal_strings", anchors);

        DecompInterface decompiler = new DecompInterface();
        List<Object> functions = new ArrayList<>();
        try {
            if (!decompiler.openProgram(currentProgram)) {
                throw new IllegalStateException("无法打开反编译器。");
            }
            for (String[] target : FUNCTIONS) {
                monitor.checkCancelled();
                Address address = toAddr(target[0]);
                Function function = getFunctionAt(address);
                Map<String, Object> row = new LinkedHashMap<>();
                row.put("address", target[0]);
                row.put("role", target[1]);
                row.put("function_present", function != null);
                if (function != null) {
                    var result = decompiler.decompileFunction(function, 25, monitor);
                    row.put("decompile_completed", result.decompileCompleted());
                    if (result.decompileCompleted()) {
                        row.put("pseudocode", result.getDecompiledFunction().getC());
                    } else {
                        row.put("decompile_error", result.getErrorMessage());
                    }
                    List<Object> references = new ArrayList<>();
                    for (var reference : getReferencesTo(address)) {
                        Map<String, Object> ref = new LinkedHashMap<>();
                        Function caller = getFunctionContaining(reference.getFromAddress());
                        ref.put("from", reference.getFromAddress().toString());
                        ref.put("type", reference.getReferenceType().toString());
                        ref.put("function", caller == null ? null : caller.getEntryPoint().toString());
                        references.add(ref);
                    }
                    row.put("references", references);
                    List<String> instructions = new ArrayList<>();
                    var iterator = currentProgram.getListing().getInstructions(function.getBody(), true);
                    while (iterator.hasNext()) {
                        monitor.checkCancelled();
                        var instruction = iterator.next();
                        instructions.add(instruction.getAddress() + " " + instruction);
                    }
                    row.put("instructions", instructions);
                }
                functions.add(row);
            }
        } finally {
            decompiler.dispose();
        }
        report.put("functions", functions);
        report.put("limitations", List.of(
            "地址适用于指定摘要和 0x1000 装载基段；不是运行时段地址。",
            "导出已有数据库定义，不创建函数、不重新分析，不代表函数发现完整。",
            "反编译的参数、段寄存器和条件标志可能不准确，须以指令和重定位交叉核对。",
            "调用指令的段地址可能采用等价别名，不能仅按显示的段名判断模块。",
            "本工具不导出 OVR 覆盖块，不证明菜单、宏、PCB 或默认配置实际载入。"
        ));
        Files.createDirectories(output.getParent());
        Files.writeString(output, new GsonBuilder().setPrettyPrinting().create().toJson(report),
            StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        println("菜单常驻路径已导出到新的本地证据文件：" + output);
    }

    private String readPascalString(Address address) throws Exception {
        int length = currentProgram.getMemory().getByte(address) & 0xff;
        byte[] bytes = new byte[length];
        currentProgram.getMemory().getBytes(address.add(1), bytes);
        return new String(bytes, StandardCharsets.ISO_8859_1);
    }
}
