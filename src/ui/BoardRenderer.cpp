#include "ui/BoardRenderer.h"
#include <QFontDatabase>
#include <QPainter>
#include <QPolygonF>
#include <algorithm>
#include <cmath>

namespace pt {
QColor layerColor(int layer) {
    static const QColor colors[]{QColor(230,230,230), QColor(239,85,70), QColor(198,120,220),
        QColor(105,194,225), QColor(239,162,83), QColor(110,210,180), QColor(85,145,250),
        QColor(245,215,95), QColor(215,165,105), QColor(115,190,125), QColor(195,125,190),
        QColor(190,205,220), QColor(225,125,175), QColor(239,105,65)};
    return colors[qBound(0, layer, 13)];
}

QString layerName(int layer) {
    static const QStringList names{QStringLiteral("无"), QStringLiteral("顶层铜"), QStringLiteral("内层 1"),
        QStringLiteral("内层 2"), QStringLiteral("内层 3"), QStringLiteral("内层 4"), QStringLiteral("底层铜"),
        QStringLiteral("顶层丝印"), QStringLiteral("底层丝印"), QStringLiteral("地平面"), QStringLiteral("电源平面"),
        QStringLiteral("板框"), QStringLiteral("禁止布线层"), QStringLiteral("多层焊盘 / 过孔")};
    return names.value(layer, QStringLiteral("未知图层"));
}

void drawBoard(QPainter& painter, const BoardDocument& board, const QSet<int>& visible) {
    painter.save();
    painter.setRenderHint(QPainter::Antialiasing);
    // 只对当前视口内的图元提交绘图；图元从不创建 QWidget 子控件。
    bool invertible = false;
    const auto inverse = painter.worldTransform().inverted(&invertible);
    const QRectF viewport = invertible ? inverse.mapRect(QRectF(painter.viewport())).normalized() : board.bounds();
    auto inView = [&](const QRectF& bounds) { return viewport.intersects(bounds.normalized().adjusted(-1, -1, 1, 1)); };
    for (int layer : {11,12,9,10,5,4,3,2,6,1,13,8,7}) {
        if (!visible.contains(layer)) continue;
        const QColor color = layerColor(layer);
        painter.setPen(Qt::NoPen); painter.setBrush(color);
        for (const auto& fill : board.fills) {
            if (fill.layer == layer && inView(fill.rectangle)) painter.drawRect(fill.rectangle);
        }
        for (const auto& track : board.tracks) {
            if (track.layer != layer) continue;
            const qreal margin = track.width / 2.0;
            if (!inView(QRectF(track.start, track.end).normalized().adjusted(-margin,-margin,margin,margin))) continue;
            painter.setPen(QPen(color, track.width, Qt::SolidLine, Qt::RoundCap));
            painter.drawLine(track.start, track.end);
        }
        painter.setBrush(Qt::NoBrush);
        for (const auto& arc : board.arcs) {
            if (arc.layer != layer) continue;
            const QRectF box(arc.center.x() - arc.radius, arc.center.y() - arc.radius, 2.0 * arc.radius, 2.0 * arc.radius);
            if (!inView(box.adjusted(-arc.width,-arc.width,arc.width,arc.width))) continue;
            painter.setPen(QPen(color, arc.width, Qt::SolidLine, Qt::RoundCap));
            // Qt 的圆弧角度按逻辑坐标的 Y 向下解释，当前变换为 Y 向上，故取负角度。
            if (arc.quadrants == 15) painter.drawEllipse(box);
            else for (int quadrant = 0; quadrant < 4; ++quadrant) {
                if (arc.quadrants & (1 << quadrant)) painter.drawArc(box, -quadrant * 90 * 16, -90 * 16);
            }
        }
        painter.setPen(Qt::NoPen); painter.setBrush(color);
        for (const auto& pad : board.pads) {
            if (pad.layer != layer) continue;
            const qreal x = pad.center.x(), y = pad.center.y(), w = pad.width, h = pad.height;
            const QRectF box(x-w/2, y-h/2, w,h);
            if (!inView(box)) continue;
            if (pad.shape == 1) painter.drawRoundedRect(box, qMin(w,h)/2, qMin(w,h)/2, Qt::AbsoluteSize);
            else if (pad.shape == 2) painter.drawRect(box);
            else if (pad.shape == 4) {
                // 形状 4 的原始倒角参数尚未恢复，当前仅作预览近似。
                const qreal radius = qMin(w,h)/4;
                painter.drawRoundedRect(box, radius, radius, Qt::AbsoluteSize);
            } else {
                const qreal bevelX = w * (1.0 - 1.0/std::sqrt(2.0));
                const qreal bevelY = h * (1.0 - 1.0/std::sqrt(2.0));
                const qreal l=box.left(), r=box.right(), t=box.top(), b=box.bottom();
                painter.drawPolygon(QPolygonF{{l+bevelX,t},{r-bevelX,t},{r,t+bevelY},{r,b-bevelY},
                    {r-bevelX,b},{l+bevelX,b},{l,b-bevelY},{l,t+bevelY}});
            }
        }
        if (layer == 13) {
            for (const auto& via : board.vias) {
                const qreal r = via.diameter/2.0;
                if (inView(QRectF(via.center-QPointF(r,r),via.center+QPointF(r,r)))) painter.drawEllipse(via.center,r,r);
            }
        }
        for (const auto& text : board.texts) {
            if (text.layer != layer || text.value.isEmpty()) continue;
            const qreal radius = std::hypot(text.height * std::max<qsizetype>(1,text.value.size()) * 1.5, text.height * 1.5);
            if (!inView(QRectF(text.position-QPointF(radius,radius),text.position+QPointF(radius,radius)))) continue;
            painter.save();
            painter.translate(text.position);
            if (text.mirrored) painter.scale(-1,1);
            painter.rotate(text.direction * 90);
            painter.scale(text.height / 100.0, -text.height / 100.0);
            auto font = QFontDatabase::systemFont(QFontDatabase::FixedFont);
            font.setPixelSize(100);
            painter.setFont(font); painter.setPen(color);
            painter.drawText(QPointF(0,0), text.value);
            painter.restore();
        }
    }
    painter.setPen(Qt::NoPen); painter.setBrush(QColor(26,30,35));
    for (const auto& pad : board.pads) {
        const qreal r = pad.drill/2.0;
        if (visible.contains(pad.layer) && r > 0 && inView(QRectF(pad.center-QPointF(r,r),pad.center+QPointF(r,r)))) painter.drawEllipse(pad.center,r,r);
    }
    if (visible.contains(13)) for (const auto& via : board.vias) {
        const qreal r = via.drill/2.0;
        if (r > 0 && inView(QRectF(via.center-QPointF(r,r),via.center+QPointF(r,r)))) painter.drawEllipse(via.center,r,r);
    }
    painter.restore();
}
}
