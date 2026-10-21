#include "io/LegacyLibraryReader.h"
#include <QCoreApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <iostream>

// 本地、只读的库结构诊断；仅输出摘要，不导出原封装图元。
int main(int argc,char** argv) {
    QCoreApplication application(argc,argv);
    if (application.arguments().size()<2) {
        std::cerr << "用法：pt-library-check <LIB 路径> [更多 LIB 路径]\n";
        return 1;
    }
    QJsonArray reports; int exitCode=0;
    for (const auto& path : application.arguments().mid(1)) {
        const auto result=pt::LegacyLibraryReader::readFile(path);
        QJsonObject report{{QStringLiteral("path"),path}};
        if (!result.succeeded()) {
            report.insert(QStringLiteral("error"),result.error); exitCode=1;
        } else {
            const auto& library=*result.library;
            int valid=0; qsizetype primitives=0; QJsonArray problems;
            for (const auto& entry : library.entries) {
                if (entry.preview) { ++valid; primitives+=entry.preview->primitiveCount(); }
                else problems.append(QJsonObject{{QStringLiteral("slot"),entry.slot+1},{QStringLiteral("name"),entry.name},{QStringLiteral("error"),entry.error}});
            }
            report.insert(QStringLiteral("sha256"),library.sha256);
            report.insert(QStringLiteral("entries"),int(library.entries.size()));
            report.insert(QStringLiteral("previewable"),valid);
            report.insert(QStringLiteral("primitives"),qint64(primitives));
            report.insert(QStringLiteral("unallocated_slots"),library.unallocatedSlots);
            report.insert(QStringLiteral("retained_name_slots"),library.retainedNameSlots);
            report.insert(QStringLiteral("problems"),problems);
            if (!problems.isEmpty() && exitCode==0) exitCode=2;
        }
        reports.append(report);
    }
    std::cout << QJsonDocument(reports).toJson(QJsonDocument::Indented).constData();
    return exitCode;
}
