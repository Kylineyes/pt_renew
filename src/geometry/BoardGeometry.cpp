#include "geometry/BoardGeometry.h"

#include <QFontDatabase>
#include <QFontMetricsF>
#include <QPainterPathStroker>
#include <QTransform>
#include <cmath>

namespace pt {
namespace {
bool valid(const BoardDocument& board, PrimitiveId id) {
    if (id.index < 0) return false;
    switch (id.kind) {
    case PrimitiveKind::Track: return id.index < board.tracks.size();
    case PrimitiveKind::Pad: return id.index < board.pads.size();
    case PrimitiveKind::Via: return id.index < board.vias.size();
    case PrimitiveKind::Arc: return id.index < board.arcs.size();
    case PrimitiveKind::Fill: return id.index < board.fills.size();
    case PrimitiveKind::Text: return id.index < board.texts.size();
    }
    return false;
}
QRectF centered(const QPointF& point, qreal width, qreal height) {
    return {point.x()-width/2, point.y()-height/2, width, height};
}
QPainterPath stroke(const QPainterPath& path, qreal width) {
    QPainterPathStroker stroker;
    stroker.setWidth(width);
    stroker.setCapStyle(Qt::RoundCap);
    stroker.setJoinStyle(Qt::RoundJoin);
    return stroker.createStroke(path);
}
QString length(qreal value) {
    return QStringLiteral("%1 mil（%2 mm）").arg(QString::number(value,'g',12),QString::number(value*0.0254,'f',4));
}
QString point(const QPointF& value) {
    return QStringLiteral("X：%1\nY：%2").arg(length(value.x()),length(value.y()));
}
}

QFont boardTextFont() {
    auto font=QFontDatabase::systemFont(QFontDatabase::FixedFont);
    font.setPixelSize(100);
    return font;
}

QPainterPath padOutline(const Pad& pad) {
    QPainterPath path;
    const QRectF box=centered(pad.center,pad.width,pad.height);
    switch (pad.shape) {
    case 1: path.addRoundedRect(box,qMin(pad.width,pad.height)/2.0,qMin(pad.width,pad.height)/2.0); break;
    case 2: path.addRect(box); break;
    case 3: {
        const qreal x=pad.width*(1.0-1.0/std::sqrt(2.0));
        const qreal y=pad.height*(1.0-1.0/std::sqrt(2.0));
        path.moveTo(box.left()+x,box.top());
        path.lineTo(box.right()-x,box.top()); path.lineTo(box.right(),box.top()+y);
        path.lineTo(box.right(),box.bottom()-y); path.lineTo(box.right()-x,box.bottom());
        path.lineTo(box.left()+x,box.bottom()); path.lineTo(box.left(),box.bottom()-y);
        path.lineTo(box.left(),box.top()+y); path.closeSubpath();
        break;
    }
    case 4: path.addRoundedRect(box,qMin(pad.width,pad.height)/4.0,qMin(pad.width,pad.height)/4.0); break;
    }
    return path;
}

QPainterPath arcCenterline(const Arc& arc) {
    QPainterPath path;
    const auto box=centered(arc.center,2.0*arc.radius,2.0*arc.radius);
    if (arc.quadrants==15) path.addEllipse(box);
    else for (int i=0;i<4;++i) if (arc.quadrants & (1<<i)) {
        path.arcMoveTo(box,-90.0*i);
        path.arcTo(box,-90.0*i,-90);
    }
    return path;
}

QPainterPath primitiveOutline(const BoardDocument& board, PrimitiveId id) {
    QPainterPath path;
    if (!valid(board,id)) return path;
    switch (id.kind) {
    case PrimitiveKind::Track: {
        const auto& t=board.tracks[id.index];
        if (t.start==t.end) { path.addEllipse(t.start,t.width/2.0,t.width/2.0); return path; }
        path.moveTo(t.start); path.lineTo(t.end); return stroke(path,t.width);
    }
    case PrimitiveKind::Pad: return padOutline(board.pads[id.index]);
    case PrimitiveKind::Via: {
        const auto& v=board.vias[id.index]; path.addEllipse(v.center,v.diameter/2.0,v.diameter/2.0); break;
    }
    case PrimitiveKind::Arc: return stroke(arcCenterline(board.arcs[id.index]),board.arcs[id.index].width);
    case PrimitiveKind::Fill: path.addRect(board.fills[id.index].rectangle); break;
    case PrimitiveKind::Text: {
        const auto& t=board.texts[id.index];
        if (t.value.isEmpty()) return path;
        // 文字按实际预览字体的包围框命中，空格和字形内留白也属于该文字对象。
        path.addRect(QFontMetricsF(boardTextFont()).boundingRect(t.value));
        QTransform transform;
        transform.translate(t.position.x(),t.position.y());
        if (t.mirrored) transform.scale(-1,1);
        transform.rotate(t.direction*90);
        transform.scale(t.height/100.0,-t.height/100.0);
        return transform.map(path);
    }
    }
    return path;
}

QRectF primitiveBounds(const BoardDocument& board, PrimitiveId id) {
    if (!valid(board,id)) return {};
    switch (id.kind) {
    case PrimitiveKind::Track: {
        const auto& t=board.tracks[id.index];
        const qreal r=t.width/2.0;
        return QRectF(t.start,t.end).normalized().adjusted(-r,-r,r,r);
    }
    case PrimitiveKind::Pad: {
        const auto& p=board.pads[id.index]; return centered(p.center,p.width,p.height);
    }
    case PrimitiveKind::Via: {
        const auto& v=board.vias[id.index]; return centered(v.center,v.diameter,v.diameter);
    }
    case PrimitiveKind::Arc: {
        const auto& a=board.arcs[id.index]; return centered(a.center,2.0*a.radius+a.width,2.0*a.radius+a.width);
    }
    case PrimitiveKind::Fill: return board.fills[id.index].rectangle;
    case PrimitiveKind::Text: return primitiveOutline(board,id).boundingRect();
    }
    return {};
}

int primitiveLayer(const BoardDocument& board, PrimitiveId id) {
    if (!valid(board,id)) return 0;
    switch (id.kind) {
    case PrimitiveKind::Track: return board.tracks[id.index].layer;
    case PrimitiveKind::Pad: return board.pads[id.index].layer;
    case PrimitiveKind::Via: return 13;
    case PrimitiveKind::Arc: return board.arcs[id.index].layer;
    case PrimitiveKind::Fill: return board.fills[id.index].layer;
    case PrimitiveKind::Text: return board.texts[id.index].layer;
    }
    return 0;
}

PrimitiveSource primitiveSource(const BoardDocument& board, PrimitiveId id) {
    if (!valid(board,id)) return {};
    switch (id.kind) {
    case PrimitiveKind::Track: return board.tracks[id.index].source;
    case PrimitiveKind::Pad: return board.pads[id.index].source;
    case PrimitiveKind::Via: return board.vias[id.index].source;
    case PrimitiveKind::Arc: return board.arcs[id.index].source;
    case PrimitiveKind::Fill: return board.fills[id.index].source;
    case PrimitiveKind::Text: return board.texts[id.index].source;
    }
    return {};
}

QString primitiveDescription(const BoardDocument& board, PrimitiveId id) {
    if (!valid(board,id)) return QStringLiteral("尚未选择图元。");
    QString text;
    switch (id.kind) {
    case PrimitiveKind::Track: {
        const auto& t=board.tracks[id.index];
        text=QStringLiteral("类型：走线\n起点\n%1\n终点\n%2\n线宽：%3\n长度：%4\n")
            .arg(point(t.start),point(t.end),length(t.width),length(std::hypot(t.end.x()-t.start.x(),t.end.y()-t.start.y())));
        if (t.extra) text+=QStringLiteral("附加字段：%1（语义未确认）\n").arg(*t.extra);
        break;
    }
    case PrimitiveKind::Pad: {
        const auto& p=board.pads[id.index];
        text=QStringLiteral("类型：焊盘\n名称：%1\n中心\n%2\n宽：%3\n高：%4\n孔径：%5\n形状编号：%6\n平面标志：%7（未做电气解释）\n")
            .arg(p.name,point(p.center),length(p.width),length(p.height),length(p.drill)).arg(p.shape).arg(p.planeFlags);
        break;
    }
    case PrimitiveKind::Via: {
        const auto& v=board.vias[id.index];
        text=QStringLiteral("类型：过孔\n中心\n%1\n外径：%2\n孔径：%3\n").arg(point(v.center),length(v.diameter),length(v.drill));
        break;
    }
    case PrimitiveKind::Arc: {
        const auto& a=board.arcs[id.index];
        text=QStringLiteral("类型：圆弧\n中心\n%1\n半径：%2\n线宽：%3\n象限掩码：%4\n")
            .arg(point(a.center),length(a.radius),length(a.width)).arg(a.quadrants);
        break;
    }
    case PrimitiveKind::Fill: {
        const auto& f=board.fills[id.index];
        text=QStringLiteral("类型：矩形填充\n最小坐标\n%1\n最大坐标\n%2\n宽：%3\n高：%4\n")
            .arg(point(f.rectangle.topLeft()),point(f.rectangle.bottomRight()),length(f.rectangle.width()),length(f.rectangle.height()));
        break;
    }
    case PrimitiveKind::Text: {
        const auto& t=board.texts[id.index];
        text=QStringLiteral("类型：文字\n内容：%1\n基准点\n%2\n字高：%3\n方向：%4°\n镜像：%5\n原始笔画宽：%6\n预览字体与命中框为近似值。\n")
            .arg(t.value,point(t.position),length(t.height)).arg(t.direction*90)
            .arg(t.mirrored?QStringLiteral("是"):QStringLiteral("否")).arg(length(t.stroke));
        break;
    }
    }
    text+=QStringLiteral("\n图层编号：%1\n本图元序号：%2\n").arg(primitiveLayer(board,id)).arg(id.index+1);
    const auto source=primitiveSource(board,id);
    if (source.line>0) text+=QStringLiteral("源文件行：%1\n").arg(source.line);
    if (source.component>=0 && source.component<board.components.size()) {
        const auto& c=board.components[source.component];
        text+=QStringLiteral("\n所属元件：%1\n封装：%2\n注释：%3\n元件原点\n%4\n").arg(c.designator,c.footprint,c.comment,point(c.origin));
    } else text+=QStringLiteral("\n所属：自由图元\n");
    return text+QStringLiteral("\n全部属性仅供查看，不可编辑；未建立网络连通性或生产校验。");
}

void BoardHitTester::setDocument(std::shared_ptr<const BoardDocument> document) {
    m_document=std::move(document);
    m_items.clear();
    if (!m_document) return;
    const auto& board=*m_document;
    auto append=[&](PrimitiveKind kind, qsizetype count, int layer) {
        for (qsizetype index=0;index<count;++index) {
            const PrimitiveId id{kind,index};
            if (primitiveLayer(board,id)==layer) {
                const auto box=primitiveBounds(board,id);
                if (!box.isEmpty()) m_items.append({id,box,layer});
            }
        }
    };
    // 与渲染顺序一致：结果逆序返回，优先选择上方可见图层和后绘制图元。
    for (int layer : boardLayerDrawOrder) {
        append(PrimitiveKind::Fill,board.fills.size(),layer);
        append(PrimitiveKind::Track,board.tracks.size(),layer);
        append(PrimitiveKind::Arc,board.arcs.size(),layer);
        append(PrimitiveKind::Pad,board.pads.size(),layer);
        if (layer==13) append(PrimitiveKind::Via,board.vias.size(),layer);
        append(PrimitiveKind::Text,board.texts.size(),layer);
    }
}

QList<PrimitiveId> BoardHitTester::hitTest(const QPointF& position, qreal toleranceMil, const QSet<int>& visible) const {
    QList<PrimitiveId> result;
    if (!m_document || !std::isfinite(position.x()) || !std::isfinite(position.y()) ||
        !std::isfinite(toleranceMil) || toleranceMil<0) return result;
    for (auto item=m_items.crbegin();item!=m_items.crend();++item) {
        if (!visible.contains(item->layer) || !item->bounds.adjusted(-toleranceMil,-toleranceMil,toleranceMil,toleranceMil).contains(position)) continue;
        const auto outline=primitiveOutline(*m_document,item->id);
        if (outline.contains(position) || (toleranceMil>0 && stroke(outline,2*toleranceMil).contains(position))) result.append(item->id);
    }
    return result;
}
}
