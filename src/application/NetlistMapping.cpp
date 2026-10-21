#include "application/NetlistMapping.h"
#include <QHash>
#include <QSet>
#include <algorithm>

namespace pt {
NetlistMapping mapNetlist(const Netlist& netlist,const BoardDocument* board) {
    NetlistMapping result;
    QHash<QString,QList<qsizetype>> pins;
    QHash<QString,QList<qsizetype>> components;
    if (board) {
        for (qsizetype i=0;i<board->components.size();++i) {
            auto& candidates=components[board->components[i].designator];if (candidates.size()<2) candidates.append(i);
        }
        for (qsizetype i=0;i<board->pads.size();++i) {
            const auto& pad=board->pads[i];
            if (pad.source.component>=0 && pad.source.component<board->components.size()) {
                auto& candidates=pins[board->components[pad.source.component].designator+QLatin1Char('-')+pad.name];
                // 两个候选足以证明歧义，避免重复标号输入造成节点×焊盘的乘法膨胀。
                if (candidates.size()<2) candidates.append(i);
            }
        }
    }
    for (auto it=components.cbegin();it!=components.cend();++it) if (it.value().size()>1)
        result.diagnostics.append(QStringLiteral("板上存在重复元件标号：%1；相关节点不视为唯一归属。").arg(it.key()));
    QHash<QString,QSet<qsizetype>> memberships;
    QHash<qsizetype,QSet<qsizetype>> physicalMemberships;
    QHash<QString,qsizetype> names;
    QSet<QString> duplicateNetNames;
    for (qsizetype i=0;i<netlist.nets.size();++i) {
        const auto& net=netlist.nets[i];
        if (names.contains(net.name)) {
            duplicateNetNames.insert(net.name);
            result.diagnostics.append(QStringLiteral("重复网络名：%1；条目未自动合并，相关节点禁止自动高亮或定位。").arg(net.name));
        }
        names.insert(net.name,i);
        for (const auto& node:net.nodes) {
            memberships[node.token].insert(i);
            const auto matched=pins.value(node.token);
            for (const auto pad:matched) physicalMemberships[pad].insert(i);
        }
    }
    QSet<QString> declared,duplicateDeclarations;
    for (const auto& component:netlist.components) {
        if (declared.contains(component.designator)) {
            duplicateDeclarations.insert(component.designator);
            result.diagnostics.append(QStringLiteral("重复元件声明：%1").arg(component.designator));
        }
        declared.insert(component.designator);
        for (const auto& field:component.additionalFields) if (!field.trimmed().isEmpty()) {
            result.diagnostics.append(QStringLiteral("元件 %1 存在未解释的附加字段，原文已保留。").arg(component.designator)); break;
        }
        if (!board) continue;
        const auto matched=components.value(component.designator);
        if (matched.isEmpty()) result.diagnostics.append(QStringLiteral("板上缺少声明元件：%1").arg(component.designator));
        else if (matched.size()>1) result.diagnostics.append(QStringLiteral("板上存在重复元件标号：%1").arg(component.designator));
        else {
            const auto& placed=board->components[matched.first()];
            if (component.footprint!=placed.footprint) result.diagnostics.append(QStringLiteral("封装差异 %1：网表 [%2]，板上 [%3]；未自动替换。").arg(component.designator,component.footprint,placed.footprint));
            if (component.comment!=placed.comment) result.diagnostics.append(QStringLiteral("注释差异 %1：网表 [%2]，板上 [%3]。").arg(component.designator,component.comment,placed.comment));
        }
    }
    for (const auto& net:netlist.nets) {
        ResolvedNet mapped; mapped.name=net.name;
        if (!net.metadata.isEmpty()) result.diagnostics.append(QStringLiteral("网络 %1 含未解释元数据，映射仅覆盖显式节点。").arg(net.name));
        if (net.nodes.size()<2) result.diagnostics.append(QStringLiteral("网络 %1 的声明节点少于两个；不据此判断导通情况。").arg(net.name));
        QSet<QString> seen; QSet<qsizetype> unique;
        for (const auto& node:net.nodes) {
            NodeResolution item; item.token=node.token;item.sourceLine=node.sourceLine;
            item.pads=pins.value(node.token);
            item.ambiguous=item.pads.size()>1 || duplicateNetNames.contains(net.name);
            if (board) for (const auto pad:item.pads) {
                const auto owner=board->pads[pad].source.component;
                if (owner>=0 && owner<board->components.size()) {
                    const auto& ref=board->components[owner].designator;
                    item.ambiguous=item.ambiguous || components.value(ref).size()>1 || duplicateDeclarations.contains(ref);
                }
            }
            bool collision=memberships.value(node.token).size()>1;
            for (const auto pad:item.pads) collision=collision || physicalMemberships.value(pad).size()>1;
            item.conflicting=collision;
            if (collision) ++result.conflicting;
            if (seen.contains(node.token)) { ++result.duplicates;item.status=QStringLiteral("同网络重复节点；未重复绘制。"); }
            seen.insert(node.token);
            if (!board) item.status+=QStringLiteral("尚未载入板图，未映射。");
            else if (item.pads.isEmpty()) { ++result.missing; item.status+=QStringLiteral("板上未找到此精确元件-引脚标识。"); }
            else if (item.ambiguous) { ++result.ambiguous; item.status+=QStringLiteral("网络名、焊盘或元件声明存在歧义（焊盘候选至少 %1 个），不自动选择。").arg(item.pads.size()); }
            else { ++result.resolved; item.status+=QStringLiteral("唯一匹配焊盘。"); }
            if (collision) item.status+=QStringLiteral("跨网络重复归属冲突，不作为有效连接绘制。");
            if (item.pads.size()==1 && !item.ambiguous && !collision) unique.insert(item.pads.first());
            mapped.nodes.append(item);
        }
        mapped.uniquePads=unique.values();std::sort(mapped.uniquePads.begin(),mapped.uniquePads.end());
        result.nets.append(mapped);
    }
    return result;
}
}
