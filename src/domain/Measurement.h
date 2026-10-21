#pragma once

#include <QPointF>
#include <cmath>

namespace pt {

// 屏幕取点换算得到的临时测量，不写入板图；坐标单位为 mil。
struct Measurement {
    QPointF start, end;
    qreal deltaX() const { return end.x()-start.x(); }
    qreal deltaY() const { return end.y()-start.y(); }
    qreal distance() const { return std::hypot(deltaX(),deltaY()); }
    qreal angleDegrees() const {
        return distance()==0 ? 0 : std::atan2(deltaY(),deltaX())*180.0/std::acos(-1.0);
    }
};

}
