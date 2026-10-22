#include "geometry/CopperConnectivity.h"

#include <QHash>
#include <QElapsedTimer>
#include <QPolygonF>
#include <QPainterPath>
#include <QPainterPathStroker>
#include <QSet>
#include <algorithm>
#include <cmath>
#include <numeric>

namespace pt {
namespace {
constexpr int circleSides=64;
constexpr qreal numericalBand=0.0001;
constexpr int allCopperLayers=0x3f;
struct Element {
    QPainterPath inside,outside;
    QRectF bounds;
    int layers=0;
    qsizetype pad=-1;
};
struct DisjointSet {
    explicit DisjointSet(qsizetype count):parent(count) { std::iota(parent.begin(),parent.end(),qsizetype(0)); }
    qsizetype find(qsizetype index) {
        qsizetype root=index;while (parent[root]!=root) root=parent[root];
        while (parent[index]!=index) { const auto next=parent[index];parent[index]=root;index=next; }
        return root;
    }
    void join(qsizetype a,qsizetype b) { a=find(a);b=find(b);if (a!=b) parent[qMax(a,b)]=qMin(a,b); }
    QList<qsizetype> parent;
};
int copperMask(int layer) { return layer>=1 && layer<=6 ? 1<<(layer-1):0; }
bool plane(int layer) { return layer==9 || layer==10; }
qreal cross(const QPointF& a,const QPointF& b,const QPointF& c) {
    return (b.x()-a.x())*(c.y()-a.y())-(b.y()-a.y())*(c.x()-a.x());
}
QPainterPath hull(QList<QPointF> points) {
    std::sort(points.begin(),points.end(),[](const QPointF& a,const QPointF& b) { return a.x()==b.x()?a.y()<b.y():a.x()<b.x(); });
    QList<QPointF> result;
    for (const auto& point:points) {
        while (result.size()>1 && cross(result[result.size()-2],result.last(),point)<=0) result.removeLast();
        result.append(point);
    }
    const auto lower=result.size();
    for (qsizetype i=points.size()-2;i>=0;--i) {
        while (result.size()>lower && cross(result[result.size()-2],result.last(),points[i])<=0) result.removeLast();
        result.append(points[i]);
    }
    QPainterPath path;if (result.size()>2) { result.removeLast();path.addPolygon(QPolygonF(result));path.closeSubpath(); }
    return path;
}
QPainterPath capsule(const QPointF& a,const QPointF& b,qreal radius,bool outer) {
    QList<QPointF> points;points.reserve(2*circleSides);
    const qreal pi=std::acos(-1.0);
    if (outer) radius/=std::cos(pi/circleSides);
    for (const auto& center:{a,b}) for (int i=0;i<circleSides;++i) {
        const qreal angle=2*pi*i/circleSides;
        points.append(center+QPointF(radius*std::cos(angle),radius*std::sin(angle)));
    }
    return hull(points);
}
QPainterPath rectangle(const QRectF& box) { QPainterPath path;path.addRect(box);return path; }
void removeHole(Element& item,const QPointF& center,qreal radius) {
    if (radius<=0) return;
    item.inside=item.inside.subtracted(capsule(center,center,radius,true));
    item.outside=item.outside.subtracted(capsule(center,center,radius,false));
}
bool positiveIntersection(const QPainterPath& a,const QPainterPath& b) {
    const auto overlap=a.intersected(b);
    // 明确正面积重叠才是已知连接；相切和零面积退化不算确定边。
    qreal area=0;
    for (const auto& polygon:overlap.toFillPolygons()) {
        qreal sum=0;
        const auto origin=polygon.isEmpty()?QPointF():polygon.first();
        for (qsizetype i=1;i+1<polygon.size();++i) sum+=cross(origin,polygon[i],polygon[i+1]);
        area+=qAbs(sum)/2;
    }
    return area>1e-8;
}
QPainterPath expanded(const QPainterPath& path) {
    QPainterPathStroker stroker;stroker.setWidth(2*numericalBand);stroker.setJoinStyle(Qt::RoundJoin);
    return path.united(stroker.createStroke(path));
}
QString stateText(CopperNetState state) {
    switch (state) {
    case CopperNetState::Connected:return QStringLiteral("支持模型内已连接");
    case CopperNetState::Separated:return QStringLiteral("支持模型内仍分离");
    case CopperNetState::Indeterminate:return QStringLiteral("无法确定");
    }
    return {};
}
}

CopperAnalysis analyzeCopper(const BoardDocument& board,const Netlist& netlist,const CopperAnalysisLimits& limits) {
    CopperAnalysis result;QElapsedTimer timer;timer.start();
    QList<Element> elements;QHash<qsizetype,qsizetype> padElements;
    QSet<QString> unsupported;
    auto unknown=[&](const QString& reason) { result.coverageComplete=false;unsupported.insert(reason); };
    auto append=[&](Element item) {
        if (timer.elapsed()>=qMax<qint64>(0,limits.maximumMilliseconds)) {
            result.limitReached=true;unknown(QStringLiteral("几何构建超过时间预算，结果不完整。"));return;
        }
        if (elements.size()>=qMax<qsizetype>(0,limits.maximumElements)) {
            result.limitReached=true;unknown(QStringLiteral("铜图元超过分析数量上限。"));return;
        }
        if (item.inside.isEmpty() || item.outside.isEmpty()) { unknown(QStringLiteral("铜图元没有可验证的正面积轮廓。"));return; }
        item.bounds=item.outside.boundingRect().adjusted(-numericalBand,-numericalBand,numericalBand,numericalBand);
        item.outside=expanded(item.outside);
        if (item.pad>=0) padElements.insert(item.pad,elements.size());
        elements.append(std::move(item));
    };
    for (const auto& track:board.tracks) {
        if (result.limitReached) break;
        const int mask=copperMask(track.layer);
        if (!mask) { if (plane(track.layer) || track.layer==13) unknown(QStringLiteral("存在平面层或多层编号的走线，未建模。"));continue; }
        if (track.extra.has_value()) unknown(QStringLiteral("铜层走线含未解释的第七附加字段，几何分组仅供诊断。"));
        if (track.width<=0) { unknown(QStringLiteral("走线尺寸无效。"));continue; }
        append({capsule(track.start,track.end,track.width/2.0,false),capsule(track.start,track.end,track.width/2.0,true),{},mask,-1});
    }
    for (qsizetype i=0;i<board.pads.size();++i) {
        if (result.limitReached) break;
        const auto& pad=board.pads[i];
        int mask=copperMask(pad.layer);
        if (pad.layer==13) {
            if (pad.drill<=0) { unknown(QStringLiteral("多层无孔焊盘的跨层关系未知。"));continue; }
            mask=allCopperLayers;
        }
        if (!mask) { if (plane(pad.layer)) unknown(QStringLiteral("存在平面层焊盘，未建模。"));continue; }
        if (pad.width<=0 || pad.height<=0 || pad.drill<0 || pad.drill>=qMin(pad.width,pad.height)) { unknown(QStringLiteral("焊盘外形或孔径退化。"));continue; }
        if (pad.shape!=1 && pad.shape!=2) { unknown(QStringLiteral("铜层八角/圆角或其他焊盘轮廓尚未精确支持。"));continue; }
        if (pad.planeFlags>1) unknown(QStringLiteral("焊盘平面连接标志尚未解释，不能确认负片平面连通。"));
        Element item;item.layers=mask;item.pad=i;
        if (pad.shape==2) item.inside=item.outside=rectangle(QRectF(pad.center-QPointF(pad.width/2.0,pad.height/2.0),QSizeF(pad.width,pad.height)));
        else {
            const qreal radius=qMin(pad.width,pad.height)/2.0;
            const QPointF delta=pad.width>=pad.height?QPointF((pad.width-pad.height)/2.0,0):QPointF(0,(pad.height-pad.width)/2.0);
            item.inside=capsule(pad.center-delta,pad.center+delta,radius,false);
            item.outside=capsule(pad.center-delta,pad.center+delta,radius,true);
        }
        removeHole(item,pad.center,pad.drill/2.0);append(std::move(item));
    }
    for (const auto& via:board.vias) {
        if (result.limitReached) break;
        if (via.diameter<=0 || via.drill<=0 || via.drill>=via.diameter) { unknown(QStringLiteral("过孔尺寸退化或无孔，跨层关系未知。"));continue; }
        Element item{capsule(via.center,via.center,via.diameter/2.0,false),capsule(via.center,via.center,via.diameter/2.0,true),{},allCopperLayers,-1};
        removeHole(item,via.center,via.drill/2.0);append(std::move(item));
    }
    for (const auto& fill:board.fills) {
        if (result.limitReached) break;
        const auto mask=copperMask(fill.layer);
        if (!mask) { if (plane(fill.layer) || fill.layer==13) unknown(QStringLiteral("存在平面层/多层填充，未建模。"));continue; }
        if (fill.rectangle.width()<=0 || fill.rectangle.height()<=0) { unknown(QStringLiteral("铜填充尺寸退化。"));continue; }
        const auto path=rectangle(fill.rectangle);append({path,path,{},mask,-1});
    }
    for (const auto& arc:board.arcs) if (copperMask(arc.layer) || plane(arc.layer) || arc.layer==13) unknown(QStringLiteral("存在铜层圆弧，当前接触分析不覆盖。"));
    for (const auto& text:board.texts) if ((copperMask(text.layer) || plane(text.layer) || text.layer==13) && !text.value.isEmpty()) unknown(QStringLiteral("存在铜层文字，原始字形尚未恢复。"));
    result.copperElements=elements.size();
    DisjointSet definite(elements.size()),possible(elements.size());
    QList<qsizetype> order(elements.size());std::iota(order.begin(),order.end(),qsizetype(0));
    std::sort(order.begin(),order.end(),[&](qsizetype a,qsizetype b) { return elements[a].bounds.left()<elements[b].bounds.left(); });
    bool stopped=result.limitReached;
    for (qsizetype a=0;a<order.size() && !stopped;++a) for (qsizetype b=a+1;b<order.size();++b) {
        const auto left=order[a],right=order[b];const auto& x=elements[left];const auto& y=elements[right];
        if (y.bounds.left()>x.bounds.right()) break;
        if (result.pairChecks%64==0 && timer.elapsed()>=qMax<qint64>(0,limits.maximumMilliseconds)) {
            result.limitReached=true;unknown(QStringLiteral("接触分析超过时间预算，结果不完整。"));stopped=true;break;
        }
        if (++result.pairChecks>qMax<qsizetype>(0,limits.maximumPairChecks)) { result.limitReached=true;unknown(QStringLiteral("候选比较次数达到上限，结果不完整。"));stopped=true;break; }
        if (!(x.layers&y.layers) || !x.bounds.intersects(y.bounds)) continue;
        if (positiveIntersection(x.inside,y.inside)) { definite.join(left,right);possible.join(left,right); }
        else if (x.outside.intersects(y.outside)) possible.join(left,right);
    }
    const auto mapping=mapNetlist(netlist,&board);
    QHash<qsizetype,QSet<QString>> componentNets;QHash<qsizetype,QList<qsizetype>> componentPads;
    for (qsizetype i=0;i<mapping.nets.size();++i) {
        const auto& net=mapping.nets[i];const auto& declaration=netlist.nets[i];
        CopperNetResult item;item.name=net.name;item.padCount=net.uniquePads.size();
        bool mappedAll=declaration.metadata.isEmpty() && !net.nodes.isEmpty();
        for (const auto& node:net.nodes) if (node.pads.size()!=1 || node.ambiguous || node.conflicting) mappedAll=false;
        QSet<qsizetype> definiteRoots,possibleRoots;
        for (const auto pad:net.uniquePads) {
            if (!padElements.contains(pad)) { mappedAll=false;continue; }
            const auto element=padElements.value(pad),root=definite.find(element);
            definiteRoots.insert(root);possibleRoots.insert(possible.find(element));
            componentNets[root].insert(net.name);componentPads[root].append(pad);
        }
        item.definiteGroups=definiteRoots.size();item.possibleGroups=possibleRoots.size();
        if (!mappedAll) item.reason=QStringLiteral("节点缺失、歧义、冲突、未支持焊盘或未解释 NETDEF 元数据。");
        else if (!result.coverageComplete) item.reason=QStringLiteral("全板铜几何覆盖不完整；本网络的支持模型分组仅供诊断，不可判为通过或断路。%1")
            .arg(item.padCount<2?QStringLiteral("有效焊盘少于两个。") : QString());
        else if (item.padCount<2) item.reason=QStringLiteral("去重后的有效焊盘少于两个，不判断连接。");
        else if (item.definiteGroups==1) { item.state=CopperNetState::Connected;item.reason=QStringLiteral("支持图元的内接铜轮廓存在明确正面积接触路径。"); }
        else if (item.possibleGroups>1) { item.state=CopperNetState::Separated;item.reason=QStringLiteral("即使考虑外接轮廓及数值带仍有多个独立铜组。"); }
        else item.reason=QStringLiteral("连接依赖相切、数值边界或内外轮廓差异，需要精确对照。");
        result.nets.append(item);
    }
    for (auto it=componentNets.cbegin();it!=componentNets.cend();++it) if (it.value().size()>1) {
        auto names=it.value().values();std::sort(names.begin(),names.end());
        auto pads=componentPads.value(it.key());std::sort(pads.begin(),pads.end());
        QStringList identities;
        for (const auto index:pads) {
            const auto& pad=board.pads[index];
            const auto owner=pad.source.component;
            identities.append(owner>=0 && owner<board.components.size()
                ? board.components[owner].designator+QLatin1Char('-')+pad.name
                : QStringLiteral("自由焊盘[%1]").arg(index+1));
        }
        result.crossNetContacts.append({names,pads,identities});
    }
    std::sort(result.crossNetContacts.begin(),result.crossNetContacts.end(),[](const CopperContact& a,const CopperContact& b) { return a.pads.first()<b.pads.first(); });
    result.limitations=unsupported.values();std::sort(result.limitations.begin(),result.limitations.end());
    result.limitations.prepend(QStringLiteral("按六个铜层及理想镀通孔筒建模；多层有孔焊盘和有效过孔假设为镀通，不验证实际镀层、盲埋孔或负片平面。"));
    result.limitations.append(QStringLiteral("圆/长圆及钻孔用 64 边内接/外接包络；仅明确正面积接触确认为连接，0.0001 mil 数值带只用于可能接触图。未做生产精度或完整 DRC 验收。"));
    return result;
}

QString copperAnalysisText(const CopperAnalysis& analysis) {
    QString result=QStringLiteral("受限铜层几何分析（不是完整 DRC）\n支持覆盖：%1；资源限制：%2\n已建模铜对象：%3；候选比较：%4\n\n")
        .arg(analysis.coverageComplete?QStringLiteral("完整支持模型"):QStringLiteral("存在未覆盖内容"))
        .arg(analysis.limitReached?QStringLiteral("已触发"):QStringLiteral("未触发")).arg(analysis.copperElements).arg(analysis.pairChecks);
    qsizetype connected=0,separated=0,indeterminate=0;
    for (const auto& net:analysis.nets) {
        if (net.state==CopperNetState::Connected) ++connected;
        else if (net.state==CopperNetState::Separated) ++separated;
        else ++indeterminate;
    }
    result+=QStringLiteral("网络汇总：支持模型内连接 %1，仍分离 %2，无法确定 %3\n跨网铜接触候选组 %4（未确认短路，清单见报告下方）\n\n")
        .arg(connected).arg(separated).arg(indeterminate).arg(analysis.crossNetContacts.size());
    for (const auto& net:analysis.nets) result+=QStringLiteral("%1：%2；有效焊盘 %3；明确铜组 %4 / 可能铜组 %5\n%6\n\n")
        .arg(net.name,stateText(net.state)).arg(net.padCount).arg(net.definiteGroups).arg(net.possibleGroups).arg(net.reason);
    result+=QStringLiteral("跨网络明确铜接触候选组：%1\n").arg(analysis.crossNetContacts.size());
    for (const auto& contact:analysis.crossNetContacts) {
        QStringList identities;
        for (const auto pad:contact.identities) { if (identities.size()>=12) { identities.append(QStringLiteral("……"));break; } identities.append(pad); }
        result+=contact.nets.join(QStringLiteral(" ↔ "))+QStringLiteral("；焊盘 %1（接触候选，需人工核查，不等于已确认短路）\n").arg(identities.join(QStringLiteral(", ")));
    }
    result+=QStringLiteral("\n模型假设与限制：\n");
    for (const auto& limitation:analysis.limitations) result+=limitation+QLatin1Char('\n');
    return result;
}
}
