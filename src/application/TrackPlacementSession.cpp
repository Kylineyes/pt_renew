#include "application/TrackPlacementSession.h"
#include <cmath>

namespace pt {

bool TrackPlacementSession::coordinate(qreal value) {
    return std::isfinite(value) && std::trunc(value) == value && std::abs(value) <= 1000000;
}

bool TrackPlacementSession::point(QPointF value) {
    return coordinate(value.x()) && coordinate(value.y());
}

bool TrackPlacementSession::fail(QString* error, const QString& message) {
    if (error) *error = message;
    return false;
}

bool TrackPlacementSession::validParameters(
    const std::shared_ptr<const BoardDocument>& document, quint64 revision, int width,
    int layer, bool targetLayerVisible, QString* error) {
    if (!document || !document->sourceContext.isEmpty())
        return fail(error, QStringLiteral("放置必须绑定当前 PCB 工作文档，不能使用库预览。"));
    if (revision == 0 || revision != document->workingRevision)
        return fail(error, QStringLiteral("放置修订须与当前工作文档修订一致。"));
    if (width <= 0 || width > 1000000)
        return fail(error, QStringLiteral("走线宽度须为 1 至 1000000 mil 的整数。"));
    if (layer != 1 && layer != 6)
        return fail(error, QStringLiteral("新增自由走线仅支持顶层 1 或底层 6。"));
    if (!targetLayerVisible)
        return fail(error, QStringLiteral("目标铜层不可见，不能开始放置。"));
    return true;
}

bool TrackPlacementSession::begin(std::shared_ptr<const BoardDocument> document,
                                   quint64 revision, int width, int layer,
                                   bool targetLayerVisible, QString* error) {
    if (error) error->clear();
    // 所有检查在写入成员前完成，非法 begin 不会打断已有活动放置。
    if (!validParameters(document, revision, width, layer, targetLayerVisible, error))
        return false;

    cancel();
    m_document = std::move(document);
    m_revision = revision;
    m_width = width;
    m_layer = layer;
    m_state = TrackPlacementState::WaitingForStart;
    return true;
}

bool TrackPlacementSession::setStart(QPointF start, QString* error) {
    if (error) error->clear();
    if (m_state == TrackPlacementState::Idle)
        return fail(error, QStringLiteral("当前没有活动的走线放置。"));
    if (!point(start))
        return fail(error, QStringLiteral("走线端点须为 ±1000000 mil 内的整数。"));

    m_start = start;
    m_end.reset();
    m_state = TrackPlacementState::WaitingForEnd;
    return true;
}

bool TrackPlacementSession::previewEnd(QPointF end, QString* error) {
    if (error) error->clear();
    if (m_state != TrackPlacementState::WaitingForEnd || !m_start)
        return fail(error, QStringLiteral("当前正在等待有效的走线起点。"));
    if (!point(end))
        return fail(error, QStringLiteral("走线端点须为 ±1000000 mil 内的整数。"));
    if (end == *m_start)
        return fail(error, QStringLiteral("走线起点和终点不能相同。"));

    m_end = end;
    return true;
}

bool TrackPlacementSession::checkContext(
    const std::shared_ptr<const BoardDocument>& currentDocument,
    quint64 currentRevision, bool targetLayerVisible) {
    if (m_state == TrackPlacementState::Idle) return true;
    if (m_document == currentDocument && m_revision == currentRevision && targetLayerVisible
        && currentDocument && currentDocument->sourceContext.isEmpty()
        && currentDocument->workingRevision == currentRevision)
        return true;
    cancel();
    return false;
}

std::optional<TrackPlacementRequest> TrackPlacementSession::prepareRequest(
    const std::shared_ptr<const BoardDocument>& currentDocument,
    quint64 currentRevision, bool targetLayerVisible, QString* error) {
    if (error) error->clear();
    // 这里显式核对三项上下文，不能把旧预览交给换入的文档或新修订。
    if (!checkContext(currentDocument, currentRevision, targetLayerVisible))
        return fail(error, QStringLiteral("放置上下文已失效，预览已取消。")), std::nullopt;
    if (m_state == TrackPlacementState::Idle)
        return fail(error, QStringLiteral("当前没有活动的走线放置。")), std::nullopt;
    if (m_state != TrackPlacementState::WaitingForEnd || !m_start || !m_end)
        return fail(error, QStringLiteral("请先指定起点和有效的终点。")), std::nullopt;
    if (!point(*m_start) || !point(*m_end))
        return fail(error, QStringLiteral("走线端点须为 ±1000000 mil 内的整数。")), std::nullopt;
    if (*m_start == *m_end)
        return fail(error, QStringLiteral("走线起点和终点不能相同。")), std::nullopt;
    if (m_width <= 0 || m_width > 1000000 || (m_layer != 1 && m_layer != 6))
        return fail(error, QStringLiteral("放置参数已失效，请重新开始。")), std::nullopt;

    return TrackPlacementRequest{*m_start, *m_end, m_width, m_layer, m_revision, m_document};
}

std::optional<TrackPlacementRequest> TrackPlacementSession::confirm(
    const std::shared_ptr<const BoardDocument>& currentDocument,
    quint64 currentRevision, bool targetLayerVisible, QString* error) {
    auto request = prepareRequest(currentDocument, currentRevision, targetLayerVisible, error);
    if (request) clear();
    return request;
}

void TrackPlacementSession::clear() {
    m_state = TrackPlacementState::Idle;
    m_document.reset();
    m_revision = 0;
    m_width = 0;
    m_layer = 0;
    m_start.reset();
    m_end.reset();
}

void TrackPlacementSession::cancel() {
    clear();
}

}
