#include "domain/BoardDocument.h"
#include <algorithm>
#include <cmath>
#include <limits>

namespace pt {

qsizetype BoardDocument::primitiveCount() const {
    return tracks.size() + pads.size() + vias.size() + arcs.size() + fills.size() + texts.size();
}

QRectF BoardDocument::bounds() const {
    qreal left = std::numeric_limits<qreal>::max();
    qreal top = left, right = -left, bottom = -left;
    auto add = [&](const QRectF& rectangle) {
        const auto r = rectangle.normalized();
        left = std::min(left, r.left()); top = std::min(top, r.top());
        right = std::max(right, r.right()); bottom = std::max(bottom, r.bottom());
    };
    for (const auto& t : tracks) add(QRectF(t.start, t.end).normalized().adjusted(-t.width / 2.0, -t.width / 2.0, t.width / 2.0, t.width / 2.0));
    for (const auto& p : pads) add(QRectF(p.center.x() - p.width / 2.0, p.center.y() - p.height / 2.0, p.width, p.height));
    for (const auto& v : vias) add(QRectF(v.center.x() - v.diameter / 2.0, v.center.y() - v.diameter / 2.0, v.diameter, v.diameter));
    for (const auto& a : arcs) {
        const qreal r = a.radius + a.width / 2.0;
        add(QRectF(a.center - QPointF(r, r), a.center + QPointF(r, r)));
    }
    for (const auto& f : fills) add(f.rectangle);
    for (const auto& t : texts) {
        // 字体是近似显示，用保守包围盒避免自动适配时裁掉旋转文字。
        const qreal w = t.height * std::max<qsizetype>(1, t.value.size()) * 1.5;
        const qreal r = std::hypot(w, t.height * 1.5);
        add(QRectF(t.position - QPointF(r, r), t.position + QPointF(r, r)));
    }
    return left <= right ? QRectF(QPointF(left, top), QPointF(right, bottom)) : QRectF(-500, -500, 1000, 1000);
}

}
