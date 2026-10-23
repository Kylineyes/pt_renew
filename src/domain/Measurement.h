#pragma once

#include "domain/PrimitiveId.h"
#include <QPointF>
#include <optional>
#include <cmath>

namespace pt {

// 临时只读测量；自由取点来自屏幕换算，捕捉点直接使用模型坐标，单位为 mil。
struct Measurement {
    QPointF start, end;
    std::optional<PrimitiveId> startAnchor, endAnchor;
    qreal deltaX() const { return end.x()-start.x(); }
    qreal deltaY() const { return end.y()-start.y(); }
    qreal distance() const { return std::hypot(deltaX(),deltaY()); }
    qreal angleDegrees() const {
        return distance()==0 ? 0 : std::atan2(deltaY(),deltaX())*180.0/std::acos(-1.0);
    }
};

}
