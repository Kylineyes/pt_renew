#pragma once

#include "domain/BoardDocument.h"
#include <QSet>
#include <optional>
#include <vector>

namespace pt {

struct SnapPoint {
    QPointF position;
    PrimitiveId primitive;
};

// 只索引确定的模型坐标；文字外形和推测的交点不参与捕捉。
class EndpointSnapIndex final {
public:
    void setDocument(const BoardDocument* document);
    std::optional<SnapPoint> nearest(const QPointF& position, qreal tolerance,
                                     const QSet<int>& visibleLayers) const;

private:
    struct Candidate {
        SnapPoint point;
        int layer;
        qsizetype order;
    };
    std::vector<Candidate> m_candidates;
};

}
