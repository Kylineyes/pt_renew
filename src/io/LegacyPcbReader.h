#pragma once
#include "domain/BoardDocument.h"

namespace pt {

// 只读、严格解析；遇到未知记录或畸形字段时整体失败，不显示悄悄丢失图元的板图。
class LegacyPcbReader {
public:
    static BoardReadResult readFile(const QString& path);
    static BoardReadResult parse(const QByteArray& bytes, const QString& source = {});
};

}
