#include "geometry/EndpointSnapIndex.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

namespace pt {

void EndpointSnapIndex::setDocument(const BoardDocument* document) {
    m_candidates.clear();
    if (!document) return;
    auto add = [this](QPointF position, PrimitiveId id, int layer) {
        if (!std::isfinite(position.x()) || !std::isfinite(position.y()) || layer < 1 || layer > 13) return;
        m_candidates.push_back({{position, id}, layer, qsizetype(m_candidates.size())});
    };
    for (qsizetype i = 0; i < document->tracks.size(); ++i) {
        const auto& track = document->tracks[i];
        add(track.start, {PrimitiveKind::Track, i}, track.layer);
        add(track.end, {PrimitiveKind::Track, i}, track.layer);
    }
    for (qsizetype i = 0; i < document->pads.size(); ++i) {
        const auto& pad = document->pads[i];
        add(pad.center, {PrimitiveKind::Pad, i}, pad.layer);
    }
    for (qsizetype i = 0; i < document->vias.size(); ++i) {
        add(document->vias[i].center, {PrimitiveKind::Via, i}, 13);
    }
    for (qsizetype i = 0; i < document->arcs.size(); ++i) {
        const auto& arc = document->arcs[i];
        if (arc.radius <= 0 || arc.quadrants < 1 || arc.quadrants > 15) continue;
        const std::array<QPointF, 4> offsets{{{qreal(arc.radius), 0}, {0, qreal(arc.radius)},
                                           {-qreal(arc.radius), 0}, {0, -qreal(arc.radius)}}};
        // 相邻启用象限的连接点不是圆弧端点；完整圆没有端点。
        for (int cardinal = 0; cardinal < 4; ++cardinal) {
            const bool before = (arc.quadrants & (1 << ((cardinal + 3) % 4))) != 0;
            const bool after = (arc.quadrants & (1 << cardinal)) != 0;
            if (before != after) add(arc.center + offsets[cardinal], {PrimitiveKind::Arc, i}, arc.layer);
        }
    }
    for (qsizetype i = 0; i < document->fills.size(); ++i) {
        const auto& fill = document->fills[i];
        const auto rectangle = fill.rectangle.normalized();
        for (const auto& corner : {rectangle.topLeft(), rectangle.topRight(), rectangle.bottomRight(), rectangle.bottomLeft()}) {
            add(corner, {PrimitiveKind::Fill, i}, fill.layer);
        }
    }
    std::stable_sort(m_candidates.begin(), m_candidates.end(), [](const Candidate& a, const Candidate& b) {
        return a.point.position.x() < b.point.position.x();
    });
}

std::optional<SnapPoint> EndpointSnapIndex::nearest(const QPointF& position, qreal tolerance,
                                                    const QSet<int>& visibleLayers) const {
    if (!std::isfinite(position.x()) || !std::isfinite(position.y()) ||
        !std::isfinite(tolerance) || tolerance < 0 || visibleLayers.isEmpty()) return {};
    const auto first = std::lower_bound(m_candidates.begin(), m_candidates.end(), position.x() - tolerance,
        [](const Candidate& candidate, qreal x) { return candidate.point.position.x() < x; });
    const Candidate* best = nullptr;
    qreal distance = tolerance;
    for (auto it = first; it != m_candidates.end() && it->point.position.x() <= position.x() + tolerance; ++it) {
        if (!visibleLayers.contains(it->layer)) continue;
        const auto delta = it->point.position - position;
        const qreal current = std::hypot(delta.x(), delta.y());
        if (current <= distance && (!best || current < distance || it->order < best->order)) {
            distance = current;
            best = &*it;
        }
    }
    return best ? std::optional<SnapPoint>(best->point) : std::nullopt;
}

}
