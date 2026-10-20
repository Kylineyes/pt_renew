#include "io/LegacyPcbInspector.h"

#include <QCryptographicHash>
#include <QFile>
#include <QFileInfo>
#include <QSet>

namespace pt {

InspectionResult LegacyPcbInspector::inspect(const QString& filePath) {
    QFile file(filePath);
    if (!file.open(QIODevice::ReadOnly)) {
        return {{}, QStringLiteral("无法读取文件：%1").arg(file.errorString())};
    }
    constexpr qint64 maximumBytes = 64 * 1024 * 1024;
    if (file.size() > maximumBytes) {
        return {{}, QStringLiteral("首阶段文件探测仅支持不超过 64 MiB 的文件。")};
    }
    // 读取有明确上限，即使文件在探测期间增长也不无限分配内存。
    const QByteArray bytes = file.read(maximumBytes + 1);
    if (file.error() != QFileDevice::NoError) {
        return {{}, QStringLiteral("读取文件失败：%1").arg(file.errorString())};
    }
    if (bytes.size() > maximumBytes) {
        return {{}, QStringLiteral("文件在探测期间超过 64 MiB 限制。")};
    }
    if (bytes.contains('\0')) {
        return {{}, QStringLiteral("文件含有二进制零字节，不属于当前支持的 PCB 文本格式。")};
    }
    const qsizetype firstNewline = bytes.indexOf('\n');
    const QByteArray header = bytes.left(firstNewline < 0 ? bytes.size() : firstNewline).trimmed();
    if (header != "PCB FILE 4") {
        return {{}, QStringLiteral("不支持此文件头，目前只探测 PCB FILE 4 文本文件。")};
    }
    static const QSet<QByteArray> markers{
        "COMP", "ENDCOMP", "CP", "CT", "CA", "CS", "CV", "CF",
        "FP", "FT", "FA", "FS", "FV", "FF"
    };
    DocumentInfo info;
    info.filePath = QFileInfo(file).absoluteFilePath();
    info.byteSize = bytes.size();
    info.sha256 = QString::fromLatin1(QCryptographicHash::hash(bytes, QCryptographicHash::Sha256).toHex());
    // 逐行扫描，避免将大量空行展开为海量 QByteArray 对象。
    QByteArray lastNonEmpty;
    qsizetype offset = 0;
    while (offset < bytes.size()) {
        const qsizetype newline = bytes.indexOf('\n', offset);
        const qsizetype end = newline < 0 ? bytes.size() : newline;
        const QByteArray marker = bytes.mid(offset, end - offset).trimmed();
        if (!marker.isEmpty()) lastNonEmpty = marker;
        if (markers.contains(marker)) {
            ++info.markerCounts[QString::fromLatin1(marker)];
        }
        offset = end + 1;
    }
    if (lastNonEmpty != "ENDPCB") {
        return {{}, QStringLiteral("未找到文件末尾的 ENDPCB 标记，文件可能不完整。")};
    }
    return {info, {}};
}

}
