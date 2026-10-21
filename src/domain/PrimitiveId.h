#pragma once

#include <QtGlobal>

namespace pt {

enum class PrimitiveKind { Track, Pad, Via, Arc, Fill, Text };

// 只在同一份不可变文档内有效；载入新文档时必须清空选择。
struct PrimitiveId {
    PrimitiveKind kind = PrimitiveKind::Track;
    qsizetype index = -1;
    bool operator==(const PrimitiveId& other) const { return kind == other.kind && index == other.index; }
    bool operator!=(const PrimitiveId& other) const { return !(*this == other); }
};

struct PrimitiveSource {
    qsizetype line = 0;
    qsizetype component = -1;
};

}
