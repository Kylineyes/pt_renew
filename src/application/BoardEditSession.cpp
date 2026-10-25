#include "application/BoardEditSession.h"
#include <cmath>

namespace pt {

void BoardEditSession::reset(std::shared_ptr<const BoardDocument> original) {
    m_original = std::move(original);
    m_history.clear(); m_position = 0; ++m_revision;
    // 工作文档与来源分开；Qt 容器在真正写入时才分离数据。
    auto current = m_original ? std::make_shared<BoardDocument>(*m_original) : nullptr;
    if (current) current->workingRevision = m_revision;
    m_current = std::move(current);
}

bool BoardEditSession::editable(PrimitiveId id, quint64 revision) const {
    return revision == m_revision && m_current && m_original->sourceContext.isEmpty()
        && id.kind == PrimitiveKind::Track && id.index >= 0 && id.index < m_current->tracks.size()
        && m_current->tracks[id.index].source.component < 0;
}

bool BoardEditSession::moveTrack(PrimitiveId id, quint64 revision, QPointF delta, QString* error) {
    if (error) error->clear();
    if (!editable(id, revision)) return false;
    auto fail = [&] { if (error) *error = QStringLiteral("位移须为 ±2000000 mil 内的整数，移动后的端点须在 ±1000000 mil 内。"); return false; };
    for (const auto value : {delta.x(), delta.y()})
        if (!std::isfinite(value) || std::trunc(value) != value || std::abs(value) > 2000000) return fail();
    if (delta.isNull()) return false;
    const auto before = m_current->tracks[id.index];
    auto after = before; after.start += delta; after.end += delta;
    for (const auto value : {after.start.x(), after.start.y(), after.end.x(), after.end.y()})
        if (!std::isfinite(value) || std::abs(value) > 1000000 || std::trunc(value) != value) return fail();
    record({id.index, before, after}); return true;
}

bool BoardEditSession::deleteTrack(PrimitiveId id, quint64 revision) {
    if (!editable(id, revision)) return false;
    record({id.index, m_current->tracks[id.index], {}}); return true;
}

void BoardEditSession::record(Operation operation) {
    m_history.resize(m_position);
    m_history.push_back(std::move(operation));
    apply(m_history.back(), true); ++m_position;
}

void BoardEditSession::apply(const Operation& operation, bool forward) {
    auto next = std::make_shared<BoardDocument>(*m_current);
    if (operation.after) next->tracks[operation.index] = forward ? *operation.after : operation.before;
    else if (forward) next->tracks.removeAt(operation.index);
    else next->tracks.insert(operation.index, operation.before);
    next->workingRevision = ++m_revision;
    m_current = std::move(next);
}

bool BoardEditSession::undo() {
    if (!canUndo()) return false;
    apply(m_history[--m_position], false); return true;
}
bool BoardEditSession::redo() {
    if (!canRedo()) return false;
    apply(m_history[m_position++], true); return true;
}

}
