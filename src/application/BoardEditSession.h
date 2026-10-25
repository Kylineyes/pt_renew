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
    bool dirty() const { return m_position != 0; }
    bool canUndo() const { return m_position > 0; }
    bool canRedo() const { return m_position < m_history.size(); }
    bool editable(PrimitiveId id, quint64 revision) const;
    bool moveTrack(PrimitiveId id, quint64 revision, QPointF delta, QString* error = nullptr);
    bool deleteTrack(PrimitiveId id, quint64 revision);
    bool undo();
    bool redo();
private:
    struct Operation { qsizetype index; Track before; std::optional<Track> after; };
    void apply(const Operation& operation, bool forward);
    void record(Operation operation);
    std::shared_ptr<const BoardDocument> m_original, m_current;
    std::vector<Operation> m_history;
    size_t m_position = 0;
    quint64 m_revision = 0;
};

}
