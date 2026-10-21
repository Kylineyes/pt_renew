#pragma once

#include <QList>
#include <QPointF>
#include <QRectF>
#include <QString>
#include <QStringList>
#include <QMap>
#include <memory>
#include <optional>

namespace pt {

// 旧格式以整数 mil 为单位（1 mil = 0.0254 mm），不使用屏幕像素保存几何。
struct Track {
    QPointF start, end;
    int width = 0, layer = 1;
    // 部分实测文件有第七字段，先原样保留，尚不推断其电气语义。
    std::optional<int> extra;
};
struct Pad {
    QPointF center;
    int width = 0, height = 0, shape = 1, drill = 0, planeFlags = 0, layer = 13;
    QString name;
};
struct Via { QPointF center; int diameter = 0, drill = 0; };
struct Arc { QPointF center; int radius = 0, quadrants = 15, width = 0, layer = 7; };
struct Fill { QRectF rectangle; int layer = 1; };
struct BoardText {
    QPointF position;
    int height = 0, direction = 0, stroke = 0, layer = 7;
    bool mirrored = false;
    QString value;
};
struct Component {
    QString designator, footprint, comment;
    QPointF origin;
    int placement = 0;
};

struct BoardDocument {
    QString filePath, sha256;
    qint64 byteSize = 0;
    QList<Track> tracks;
    QList<Pad> pads;
    QList<Via> vias;
    QList<Arc> arcs;
    QList<Fill> fills;
    QList<BoardText> texts;
    QList<Component> components;
    QMap<QString, qsizetype> recordCounts;
    QStringList warnings;

    QRectF bounds() const;
    qsizetype primitiveCount() const;
};

struct BoardReadResult {
    std::shared_ptr<const BoardDocument> document;
    QString error;
    bool succeeded() const { return document != nullptr && error.isEmpty(); }
};

}
