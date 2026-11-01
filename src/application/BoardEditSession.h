#pragma once

#include "domain/BoardDocument.h"
#include <vector>

namespace pt {

// 历史只保存一条走线的前后值与位置，不持有整板快照。
class BoardEditSession final {
public:
    void reset(std::shared_ptr<const BoardDocument> original = {});
    const std::shared_ptr<const BoardDocument>& original() const { return m_original; }
    const std::shared_ptr<const BoardDocument>& document() const { return m_current; }
    quint64 revision() const { return m_revision; }
    bool dirty() const { return !m_savedPosition || m_position != *m_savedPosition; }
    void markSaved() { m_savedPosition = m_position; }
    bool canUndo() const { return m_position > 0; }
    bool canRedo() const { return m_position < m_history.size(); }
    bool editable(PrimitiveId id, quint64 revision) const;
    bool moveTrack(PrimitiveId id, quint64 revision, QPointF delta, QString* error = nullptr);
    bool deleteTrack(PrimitiveId id, quint64 revision);
    // 仅供核心编辑使用；新增 FT 的原文件编码尚未核定，界面与写出入口不开放。
    bool addTrack(QPointF start, QPointF end, int width, int layer, quint64 revision, QString* error = nullptr);
    bool undo();
    bool redo();
private:
    struct Operation { qsizetype index; std::optional<Track> before, after; };
    bool apply(const Operation& operation, bool forward);
    bool record(Operation operation);
    std::shared_ptr<const BoardDocument> m_original, m_current;
    std::vector<Operation> m_history;
    size_t m_position = 0;
    std::optional<size_t> m_savedPosition = 0;
    quint64 m_revision = 0;
    quint64 m_nextTrackSequence = 1;
    bool m_identitiesValid = false;
};

}
