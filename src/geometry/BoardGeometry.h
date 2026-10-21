#pragma once

#include "domain/BoardDocument.h"
#include <QFont>
#include <QPainterPath>
#include <QSet>
#include <array>

namespace pt {

inline constexpr std::array<int,13> boardLayerDrawOrder{11,12,9,10,5,4,3,2,6,1,13,8,7};

// 与显示端共享的轮廓，均为板坐标（mil，Y 向上）。
QPainterPath padOutline(const Pad& pad);
QPainterPath arcCenterline(const Arc& arc);
QFont boardTextFont();
QPainterPath primitiveOutline(const BoardDocument& board, PrimitiveId id);
QRectF primitiveBounds(const BoardDocument& board, PrimitiveId id);
int primitiveLayer(const BoardDocument& board, PrimitiveId id);
PrimitiveSource primitiveSource(const BoardDocument& board, PrimitiveId id);
QString primitiveDescription(const BoardDocument& board, PrimitiveId id);
QRectF componentBounds(const BoardDocument& board, qsizetype index);
QString componentDescription(const BoardDocument& board, qsizetype index);

// 缓存包围盒粗筛，候选再做轮廓精测，不按包围盒直接选中圆弧内部空白。
class BoardHitTester {
public:
    void setDocument(std::shared_ptr<const BoardDocument> document);
    QList<PrimitiveId> hitTest(const QPointF& position, qreal toleranceMil, const QSet<int>& visible) const;
private:
    struct Item { PrimitiveId id; QRectF bounds; int layer; };
    std::shared_ptr<const BoardDocument> m_document;
    QList<Item> m_items;
};

}
