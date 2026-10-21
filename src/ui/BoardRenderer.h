#pragma once
#include "domain/BoardDocument.h"
#include <QColor>
#include <QSet>

class QPainter;
namespace pt {

QColor layerColor(int layer);
QString layerName(int layer);

// 只负责绘图，不持有文件或编辑状态；外部设置 mil 到屏幕的变换。
void drawBoard(QPainter& painter, const BoardDocument& board, const QSet<int>& visibleLayers);

}
