#include "application/TrackPlacementController.h"
#include "application/BoardEditSession.h"

namespace pt {

bool TrackPlacementController::begin(int width, int layer, bool targetLayerVisible, QString* error) {
    return m_placement.begin(m_edits.document(), m_edits.revision(), width, layer,
                             targetLayerVisible, error);
}

bool TrackPlacementController::checkContext(bool targetLayerVisible) {
    return m_placement.checkContext(m_edits.document(), m_edits.revision(), targetLayerVisible);
}

bool TrackPlacementController::requireContext(bool targetLayerVisible, QString* error) {
    if (error) error->clear();
    if (checkContext(targetLayerVisible)) return true;
    if (error) *error = QStringLiteral("放置上下文已失效，预览已取消。");
    return false;
}

bool TrackPlacementController::setStart(QPointF start, bool targetLayerVisible, QString* error) {
    return requireContext(targetLayerVisible, error) && m_placement.setStart(start, error);
}

bool TrackPlacementController::previewEnd(QPointF end, bool targetLayerVisible, QString* error) {
    return requireContext(targetLayerVisible, error) && m_placement.previewEnd(end, error);
}

bool TrackPlacementController::commit(bool targetLayerVisible, QString* error) {
    const auto request = m_placement.prepareRequest(m_edits.document(), m_edits.revision(),
                                                    targetLayerVisible, error);
    if (!request) return false;
    // 同步调用现有后端完成唯一一次历史操作；容量、身份等保护仍由编辑会话负责。
    if (!m_edits.addTrack(request->start, request->end, request->width, request->layer,
                          request->revision, error)) return false;
    cancel();
    return true;
}

void TrackPlacementController::cancel() {
    m_placement.cancel();
}

bool TrackPlacementController::undo() {
    cancel();
    return m_edits.undo();
}

bool TrackPlacementController::redo() {
    cancel();
    return m_edits.redo();
}

}
