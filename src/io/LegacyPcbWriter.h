#pragma once

#include "domain/BoardDocument.h"

namespace pt {

struct BoardWriteResult {
    QByteArray bytes;
    QString filePath, sha256, error;
    bool succeeded() const { return error.isEmpty() && !bytes.isEmpty(); }
};

// 只修改原始FT记录坐标或移除该记录；其他字节保持不变，禁止覆盖任何现有文件。
class LegacyPcbWriter final {
public:
    static BoardWriteResult prepare(const BoardDocument& original, const BoardDocument& current);
    static BoardWriteResult saveAs(const QString& path, const BoardDocument& original, const BoardDocument& current);
};

}
