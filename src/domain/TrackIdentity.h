#pragma once

#include <QtGlobal>

namespace pt {

// 身份仅在同一来源文档的编辑会话内有效，不代替带修订号的画布选择。
struct TrackIdentity {
    enum class Kind { Unassigned, Loaded, Created };
    Kind kind = Kind::Unassigned;
    // 载入记录使用原标签行号；新建记录使用会话内单调递增的非零序号。
    quint64 value = 0;

    static TrackIdentity loaded(qsizetype line) {
        return line > 0 ? TrackIdentity{Kind::Loaded, quint64(line)} : TrackIdentity{};
    }
    static TrackIdentity created(quint64 sequence) { return {Kind::Created, sequence}; }
    bool valid() const { return value != 0 && (kind == Kind::Loaded || kind == Kind::Created); }
    bool operator==(const TrackIdentity& other) const { return kind == other.kind && value == other.value; }
    bool operator!=(const TrackIdentity& other) const { return !(*this == other); }
};

}
