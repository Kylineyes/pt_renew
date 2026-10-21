#include "io/LegacyNetlistReader.h"
#include "io/LegacyPcbReader.h"
#include "application/NetlistMapping.h"
#include <QCoreApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <iostream>

int main(int argc,char** argv) {
    QCoreApplication app(argc,argv);const auto args=app.arguments();
    if (args.size()<2 || args.size()>3) { std::cerr<<"用法：pt-netlist-check <NET> [PCB]\n";return 1; }
    const auto net=pt::LegacyNetlistReader::readFile(args[1]);
    if (!net.succeeded()) { std::cout<<QJsonDocument(QJsonObject{{"error",net.error}}).toJson().constData();return 1; }
    pt::BoardReadResult board;
    if (args.size()==3) { board=pt::LegacyPcbReader::readFile(args[2]);if (!board.succeeded()) {std::cout<<QJsonDocument(QJsonObject{{"error",board.error}}).toJson().constData();return 1;} }
    const auto mapping=pt::mapNetlist(*net.netlist,board.document.get());qsizetype nodes=0;for (const auto& n:net.netlist->nets) nodes+=n.nodes.size();
    const QJsonObject result{{"sha256",net.netlist->sha256},{"components",qint64(net.netlist->components.size())},{"nets",qint64(mapping.nets.size())},
        {"nodes",qint64(nodes)},{"board_loaded",board.succeeded()},{"resolved",qint64(mapping.resolved)},{"missing",qint64(mapping.missing)},
        {"ambiguous",qint64(mapping.ambiguous)},{"conflicting",qint64(mapping.conflicting)},{"duplicates",qint64(mapping.duplicates)},
        {"diagnostics",QJsonArray::fromStringList(mapping.diagnostics)},{"notice",QStringLiteral("仅引脚归属映射，不是铜线连通或 DRC 检查。")}};
    std::cout<<QJsonDocument(result).toJson().constData();return mapping.missing || mapping.ambiguous || mapping.conflicting?2:0;
}
