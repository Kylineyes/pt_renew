#pragma once

#include <QMap>
#include <QString>

namespace pt {

// 仅保存文件探测信息，不表示已解析或载入板图图元。
struct DocumentInfo {
    QString filePath;
    qint64 byteSize = 0;
    QString sha256;
    QMap<QString, qsizetype> markerCounts;
};

struct InspectionResult {
    DocumentInfo info;
    QString error;

    bool succeeded() const { return error.isEmpty(); }
};

}
