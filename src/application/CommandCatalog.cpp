#include "application/CommandCatalog.h"

#include <initializer_list>

namespace pt {
namespace {

CommandSpec command(const char* id, const char* text,
                    std::initializer_list<const char*> shortcuts = {},
                    bool implemented = false, bool checkable = false) {
    QStringList keys;
    for (const auto* key : shortcuts) {
        keys.append(QString::fromLatin1(key));
    }
    return {QString::fromLatin1(id), QString::fromUtf8(text), keys, implemented, checkable};
}

}

const QList<MenuSpec>& commandCatalog() {
    // 保留原一级菜单的字母顺序；未实现业务只展示入口，不能执行。
    static const QList<MenuSpec> menus{
        {QStringLiteral("B"), QStringLiteral("块操作(&B)"), {
            command("block.define", "定义范围(&D)"), command("block.move", "移动块(&M)"),
            command("block.copy", "复制块(&C)"), command("block.read", "读取块(&R)"),
            command("block.write", "写出块(&W)")}},
        {QStringLiteral("C"), QStringLiteral("当前(&C)"), {
            command("current.layer", "当前图层(&L)"), command("current.track_width", "走线宽度(&T)"),
            command("current.pad", "焊盘参数(&P)"), command("current.via", "过孔参数(&V)")}},
        {QStringLiteral("D"), QStringLiteral("删除(&D)"), {
            command("delete.arc", "删除圆弧(&A)"), command("delete.component", "删除元件(&C)"),
            command("delete.pad", "删除焊盘(&P)"), command("delete.track", "删除走线(&T)"),
            command("delete.via", "删除过孔(&V)")}},
        {QStringLiteral("E"), QStringLiteral("编辑(&E)"), {
            command("edit.arc", "编辑圆弧(&A)"), command("edit.component", "编辑元件(&C)"),
            command("edit.pad", "编辑焊盘(&P)"), command("edit.track", "编辑走线(&T)"),
            command("edit.string", "编辑文字(&S)")}},
        {QStringLiteral("F"), QStringLiteral("文件(&F)"), {
            command("file.inspect", "打开文件信息（只读）(&L)", {"Ctrl+O"}, true),
            command("file.close", "关闭文件信息(&C)", {"Ctrl+W"}, true),
            command("file.save", "保存板图(&S)", {"Ctrl+S"}),
            command("app.exit", "退出程序(&Q)", {"Alt+F4"}, true)}},
        {QStringLiteral("G"), QStringLiteral("网格(&G)"), {
            command("view.grid", "显示网格(&V)", {"Ctrl+G"}, true, true),
            command("grid.snap", "捕捉网格(&S)")}},
        {QStringLiteral("H"), QStringLiteral("高亮(&H)"), {
            command("highlight.connection", "高亮连接(&C)"), command("highlight.net", "高亮网络(&N)"),
            command("highlight.reset", "清除高亮(&R)")}},
        {QStringLiteral("I"), QStringLiteral("信息(&I)"), {
            command("info.file", "文件信息面板(&S)", {}, true),
            command("info.board", "板图尺寸(&B)"), command("info.components", "元件信息(&C)"),
            command("app.about", "关于当前阶段(&A)", {}, true)}},
        {QStringLiteral("J"), QStringLiteral("跳转(&J)"), {
            command("jump.component", "跳转到元件(&C)"), command("jump.net", "跳转到网络(&N)"),
            command("jump.origin", "跳转到原点(&O)")}},
        {QStringLiteral("L"), QStringLiteral("封装库(&L)"), {
            command("library.browse", "浏览封装(&B)"), command("library.file", "选择封装库(&F)"),
            command("library.add", "添加封装(&A)"), command("library.merge", "合并封装库(&M)")}},
        {QStringLiteral("M"), QStringLiteral("移动(&M)"), {
            command("move.component", "移动元件(&C)"), command("move.pad", "移动焊盘(&P)"),
            command("move.track", "移动走线(&T)"), command("move.break", "打断走线(&B)")}},
        {QStringLiteral("N"), QStringLiteral("网络(&N)"), {
            command("netlist.load", "读取网表(&G)"), command("netlist.drc", "设计规则检查(&D)"),
            command("netlist.autoplace", "自动布局(&A)"), command("netlist.route", "布线(&R)")}},
        {QStringLiteral("P"), QStringLiteral("放置(&P)"), {
            command("place.arc", "放置圆弧(&A)"), command("place.component", "放置元件(&C)"),
            command("place.fill", "放置填充(&F)"), command("place.pad", "放置焊盘(&P)", {"F1"}),
            command("place.string", "放置文字(&S)"), command("place.track", "放置走线(&T)", {"F3"}),
            command("place.via", "放置过孔(&V)")}},
        {QStringLiteral("R"), QStringLiteral("重复(&R)"), {
            command("edit.repeat", "重复上一操作(&R)")}},
        {QStringLiteral("S"), QStringLiteral("设置(&S)"), {
            command("setup.keys", "快捷键与宏(&K)"), command("setup.layers", "图层设置(&L)"),
            command("setup.options", "编辑选项(&O)")}},
        {QStringLiteral("U"), QStringLiteral("恢复(&U)"), {
            command("edit.undelete", "恢复删除(&U)")}},
        {QStringLiteral("Z"), QStringLiteral("视图(&Z)"), {
            command("view.redraw", "重绘(&R)", {"F9"}, true),
            command("view.zoom_in", "放大(&E)", {"Ctrl++", "F6"}, true),
            command("view.zoom_out", "缩小(&C)", {"Ctrl+-", "F5"}, true),
            command("view.center", "居中(&P)", {"F10"}, true),
            command("view.reset", "恢复默认视图(&A)", {"Ctrl+0"}, true)}}
    };
    return menus;
}

}
