#pragma once

#include "domain/BoardDocument.h"
#include <QPointF>
#include <QString>
#include <memory>
#include <optional>

namespace pt {

enum class TrackPlacementState {
    Idle,
    WaitingForStart,
    WaitingForEnd,
};

// 确认结果只描述待提交的几何与上下文，不携带任何永久身份或原文件来源。
struct TrackPlacementRequest {
    QPointF start;
    QPointF end;
    int width = 0;
    int layer = 0;
    quint64 revision = 0;
    std::shared_ptr<const BoardDocument> document;
};

// 纯核心放置状态；预览期间不触碰 BoardEditSession 或 BoardDocument 内容。
class TrackPlacementSession final {
public:
    TrackPlacementState state() const { return m_state; }
    const std::shared_ptr<const BoardDocument>& document() const { return m_document; }
    quint64 revision() const { return m_revision; }
    int width() const { return m_width; }
    int layer() const { return m_layer; }
    std::optional<QPointF> startPoint() const { return m_start; }
    std::optional<QPointF> previewEndPoint() const { return m_end; }

    // 参数非法时不改变当前活动状态或已有预览。
    bool begin(std::shared_ptr<const BoardDocument> document, quint64 revision, int width,
               int layer, bool targetLayerVisible, QString* error = nullptr);
    // WaitingForEnd 时重新指定起点会丢弃旧终点预览，但仍保留本次放置上下文。
    bool setStart(QPointF start, QString* error = nullptr);
    // 端点非法时不改变已有预览；零长度终点不能进入预览。
    bool previewEnd(QPointF end, QString* error = nullptr);

    // 检查当前文档身份、修订和目标层可见性；失效时取消活动放置并返回 false。
    bool checkContext(const std::shared_ptr<const BoardDocument>& currentDocument,
                      quint64 currentRevision, bool targetLayerVisible);
    // 准备请求不清除有效预览；上下文失效仍会取消，供编辑后端成功后再结束放置。
    std::optional<TrackPlacementRequest> prepareRequest(
        const std::shared_ptr<const BoardDocument>& currentDocument,
        quint64 currentRevision, bool targetLayerVisible, QString* error = nullptr);
    // 只在上下文和完整几何均有效时返回一次请求，并回到 Idle。
    std::optional<TrackPlacementRequest> confirm(
        const std::shared_ptr<const BoardDocument>& currentDocument,
        quint64 currentRevision, bool targetLayerVisible, QString* error = nullptr);
    // 幂等丢弃上下文和临时预览。
    void cancel();

private:
    static bool coordinate(qreal value);
    static bool point(QPointF value);
    static bool validParameters(const std::shared_ptr<const BoardDocument>& document,
                                quint64 revision, int width, int layer,
                                bool targetLayerVisible, QString* error);
    static bool fail(QString* error, const QString& message);
    void clear();

    TrackPlacementState m_state = TrackPlacementState::Idle;
    std::shared_ptr<const BoardDocument> m_document;
    quint64 m_revision = 0;
    int m_width = 0;
    int m_layer = 0;
    std::optional<QPointF> m_start;
    std::optional<QPointF> m_end;
};

}
