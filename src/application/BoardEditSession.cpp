#include "application/BoardEditSession.h"
#include <QSet>
#include <algorithm>
#include <cmath>

namespace pt {
namespace {
bool coordinate(qreal value) {
    return std::isfinite(value) && std::trunc(value) == value && std::abs(value) <= 1000000;
}
bool sameTrack(const Track& a, const Track& b) {
    return a.identity == b.identity && a.start == b.start && a.end == b.end
        && a.width == b.width && a.layer == b.layer && a.extra == b.extra
        && a.source.line == b.source.line && a.source.component == b.source.component
        && a.source.byteOffset == b.source.byteOffset;
}
}

void BoardEditSession::reset(std::shared_ptr<const BoardDocument> original) {
    m_original = std::move(original);
    m_history.clear(); m_position = 0; m_savedPosition = 0; ++m_revision;
    m_nextTrackSequence = 1;
    m_identitiesValid = m_original != nullptr;
    QSet<quint64> loadedLines;
    if (m_original) {
        for (const auto& track : m_original->tracks) {
            if (!track.identity.valid() || track.identity.kind != TrackIdentity::Kind::Loaded
                || track.identity != TrackIdentity::loaded(track.source.line) || loadedLines.contains(track.identity.value)) {
                m_identitiesValid = false; break;
            }
            loadedLines.insert(track.identity.value);
        }
    }
    // 工作文档与来源分开；Qt 容器在真正写入时才分离数据。
    auto current = m_original ? std::make_shared<BoardDocument>(*m_original) : nullptr;
    if (current) current->workingRevision = m_revision;
    m_current = std::move(current);
}

bool BoardEditSession::editable(PrimitiveId id, quint64 revision) const {
    return revision == m_revision && m_current && m_identitiesValid && m_original->sourceContext.isEmpty()
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
        if (!coordinate(value)) return fail();
    return record({id.index, before, after});
}

bool BoardEditSession::deleteTrack(PrimitiveId id, quint64 revision) {
    if (!editable(id, revision)) return false;
    return record({id.index, m_current->tracks[id.index], {}});
}

bool BoardEditSession::addTrack(QPointF start, QPointF end, int width, int layer, quint64 revision, QString* error) {
    if (error) error->clear();
    auto fail = [&](const QString& message) { if (error) *error = message; return false; };
    if (!m_current || !m_identitiesValid || !m_original->sourceContext.isEmpty())
        return fail(QStringLiteral("只能在具有唯一载入走线身份的 PCB 工作副本中新增自由走线。"));
    if (revision != m_revision) return fail(QStringLiteral("板图已变化，请基于当前修订重新确认走线。"));
    for (const auto value : {start.x(), start.y(), end.x(), end.y()})
        if (!coordinate(value)) return fail(QStringLiteral("走线端点须为 ±1000000 mil 内的整数。"));
    if (start == end) return fail(QStringLiteral("走线起点和终点不能相同。"));
    if (width <= 0 || width > 1000000) return fail(QStringLiteral("走线宽度须为 1 至 1000000 mil 的整数。"));
    if (layer != 1 && layer != 6) return fail(QStringLiteral("新增自由走线仅支持顶层 1 或底层 6。"));
    if (m_current->tracks.size() >= 200000) return fail(QStringLiteral("走线数量已达到 200000 的安全限制。"));
    if (m_nextTrackSequence == 0) return fail(QStringLiteral("会话走线身份已耗尽，请重新载入板图。"));
    // 新建记录不伪造来源行，也不从已有线复制未解释的附加字段。
    Track after{start, end, width, layer, {}, {}, TrackIdentity::created(m_nextTrackSequence)};
    if (!record({m_current->tracks.size(), {}, after})) return fail(QStringLiteral("走线历史状态不一致，未提交新增。"));
    ++m_nextTrackSequence;
    return true;
}

bool BoardEditSession::record(Operation operation) {
    // 先验证并应用，再截断重做分支；失败不能丢失历史或保存点。
    if (!apply(operation, true)) return false;
    if (m_savedPosition && *m_savedPosition > m_position) m_savedPosition.reset();
    m_history.resize(m_position);
    m_history.push_back(std::move(operation)); ++m_position;
    return true;
}

bool BoardEditSession::apply(const Operation& operation, bool forward) {
    if (!m_current || (!operation.before && !operation.after)) return false;
    if (operation.before && operation.after && operation.before->identity != operation.after->identity) return false;
    const auto& expected = forward ? operation.before : operation.after;
    const auto& replacement = forward ? operation.after : operation.before;
    const auto index = operation.index;
    if (index < 0 || index > m_current->tracks.size()) return false;
    if (expected) {
        if (index == m_current->tracks.size() || !expected->identity.valid()
            || !sameTrack(m_current->tracks[index], *expected)) return false;
    } else {
        // 撤销删除或重做新增时也核对身份，不能在当前位置插入重复记录。
        if (!replacement || !replacement->identity.valid()
            || std::any_of(m_current->tracks.cbegin(), m_current->tracks.cend(), [&](const Track& track) {
                return track.identity == replacement->identity;
            })) return false;
    }
    auto next = std::make_shared<BoardDocument>(*m_current);
    if (expected && replacement) next->tracks[index] = *replacement;
    else if (expected) next->tracks.removeAt(index);
    else next->tracks.insert(index, *replacement);
    next->workingRevision = ++m_revision;
    m_current = std::move(next);
    return true;
}

bool BoardEditSession::undo() {
    if (!canUndo() || !apply(m_history[m_position - 1], false)) return false;
    --m_position; return true;
}
bool BoardEditSession::redo() {
    if (!canRedo() || !apply(m_history[m_position], true)) return false;
    ++m_position; return true;
}

}
