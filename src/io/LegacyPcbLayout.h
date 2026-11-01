#pragma once
#include "domain/BoardDocument.h"

namespace pt {

// 均为冻结原始输入的字节偏移；负值表示不存在，区间采用 [beginOffset, endOffset)。
struct LegacyPcbRecordBoundary {
    QByteArray tag;
    qsizetype line = 0;
    qsizetype beginOffset = -1;
    qsizetype endOffset = -1;
};

struct LegacyPcbNewlineFacts {
    // 仅统计 DOS EOF 前的文本，包含 NETDEF 和 ENDPCB 后的空白。
    qsizetype lfCount = 0;
    qsizetype crlfCount = 0;
    qsizetype bareCarriageReturnCount = 0;
    bool textEndsWithNewline = false;
    QByteArray firstLineEnding;
    bool mixed() const { return lfCount > 0 && crlfCount > 0; }
};

enum class LegacyPcbInsertionKind { None, BeforeEndPcb, BeforeTrailingNetdefs };

struct LegacyPcbInsertionCandidate {
    LegacyPcbInsertionKind kind = LegacyPcbInsertionKind::None;
    qsizetype byteOffset = -1;
    // 仅描述锚点标签行的实际终止字节；空值表示该行没有 LF，并非写出默认值。
    QByteArray anchorLineEnding;
    QString unavailableReason = QStringLiteral("尚未完成严格语法解析。");
    bool isValid() const { return kind != LegacyPcbInsertionKind::None && byteOffset >= 0; }
};

struct LegacyPcbLayout {
    qsizetype sourceByteSize = 0;
    qsizetype textEndOffset = -1;
    qsizetype dosEofOffset = -1;
    qsizetype endPcbOffset = -1;
    qsizetype trailingNetdefsOffset = -1;
    qsizetype netdefCount = 0;
    bool geometryAfterNetdef = false;
    // COMP 是一个完整顶层区间，内部图元与 ENDCOMP 不另列顶层记录。
    QList<LegacyPcbRecordBoundary> topLevelRecords;
    LegacyPcbNewlineFacts newlines;
    LegacyPcbInsertionCandidate insertion;
    // 候选只证明语法位置；当前所有布局均未通过新增写出的原软件兼容验收。
    bool originalSoftwareInsertionVerified = false;
    QStringList unverifiedReasons;
};

struct LegacyPcbLayoutReadResult {
    std::shared_ptr<const BoardDocument> document;
    LegacyPcbLayout layout;
    QString error;
    bool succeeded() const { return document && error.isEmpty(); }
};

}
