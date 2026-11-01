#pragma once

#include "io/LegacyPcbLayout.h"

namespace pt {

struct LegacyTrackInsertionPlan {
    // 仅包含旧记录受限移动／删除后的字节，绝不含新增 FT 的编码。
    QByteArray baseBytes;
    // 所有偏移均相对 baseBytes，不能用于原输入字节。
    LegacyPcbLayout baseLayout;
    QList<Track> createdTracks;
    // 没有新增段时为 -1；此时即使存在 NETDEF，也只返回旧记录编辑结果。
    qsizetype insertionByteOffset = -1;
    QString error;
    bool succeeded() const { return error.isEmpty() && !baseBytes.isEmpty() && baseLayout.endPcbOffset >= 0; }
};

// 纯内存结构预检；成功不代表已有 FT 编码策略或通过原软件兼容验收。
class LegacyTrackInsertionPlanner final {
public:
    static LegacyTrackInsertionPlan prepare(const BoardDocument& original, const BoardDocument& current);
};

}
