#pragma once

#include "application/TrackPlacementSession.h"

namespace pt {

class BoardEditSession;

// 编辑会话须比控制器活得更久，所有访问在同一线程串行进行；控制器不拥有编辑会话。
class TrackPlacementController final {
public:
    explicit TrackPlacementController(BoardEditSession& edits) : m_edits(edits) {}
    TrackPlacementController(const TrackPlacementController&) = delete;
    TrackPlacementController& operator=(const TrackPlacementController&) = delete;

    // 只读状态供未来界面查询；不能通过控制器直接改写编辑会话或放置内部状态。
    const TrackPlacementSession& placement() const { return m_placement; }
    bool begin(int width, int layer, bool targetLayerVisible, QString* error = nullptr);
    bool setStart(QPointF start, bool targetLayerVisible, QString* error = nullptr);
    bool previewEnd(QPointF end, bool targetLayerVisible, QString* error = nullptr);
    bool checkContext(bool targetLayerVisible);
    // 后端拒绝时保留有效预览并返回原错误；成功后才结束放置。
    bool commit(bool targetLayerVisible, QString* error = nullptr);
    void cancel();
    // 即使没有可撤销或重做的历史，也先取消临时放置。
    bool undo();
    bool redo();

private:
    bool requireContext(bool targetLayerVisible, QString* error);
    BoardEditSession& m_edits;
    TrackPlacementSession m_placement;
};

}
