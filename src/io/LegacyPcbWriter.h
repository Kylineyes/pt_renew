#pragma once

#include "domain/BoardDocument.h"
#include "io/LegacyFreeTrackCodec.h"

namespace pt {

struct BoardWriteResult {
    QByteArray bytes;
    QString filePath, sha256, error;
    bool succeeded() const { return error.isEmpty() && !bytes.isEmpty(); }
};

// 默认只移动或删除原始 FT；新增输出须使用显式编码入口，禁止覆盖任何现有文件。
class LegacyPcbWriter final {
public:
    static BoardWriteResult prepare(const BoardDocument& original, const BoardDocument& current);
    static BoardWriteResult saveAs(const QString& path, const BoardDocument& original, const BoardDocument& current);
    // 编码参数不设默认值；仅证明严格格式与工作副本一致，不代表原 AUTOTRAX 兼容。
    // 无新建段时沿用 prepare/saveAs，不消费编码参数；不改变编辑会话保存点。
    static BoardWriteResult prepareWithCreated(const BoardDocument& original, const BoardDocument& current,
        const LegacyFreeTrackCodec::Options& options);
    static BoardWriteResult saveAsWithCreated(const QString& path, const BoardDocument& original, const BoardDocument& current,
        const LegacyFreeTrackCodec::Options& options);
};

}
