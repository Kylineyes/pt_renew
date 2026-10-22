#include "geometry/CopperConnectivity.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyNetlistReader.h"
#include <QCoreApplication>
#include <QJsonArray>
#include <QJsonObject>
#include <QJsonDocument>
#include <iostream>

int main(int argc,char** argv) {
    QCoreApplication application(argc,argv);const auto args=application.arguments();
    if (args.size()<2 || args.size()>3) { std::cerr<<"用法：pt-copper-check <PCB> [NET；省略则使用板内 NETDEF]\n";return 1; }
    const auto board=pt::LegacyPcbReader::readFile(args[1]);
    if (!board.succeeded()) { std::cout<<QJsonDocument(QJsonObject{{"error",board.error}}).toJson().constData();return 1; }
    auto network=board.document->embeddedNetlist;
    if (args.size()==3) {
        const auto input=pt::LegacyNetlistReader::readFile(args[2]);
        if (!input.succeeded()) { std::cout<<QJsonDocument(QJsonObject{{"error",input.error}}).toJson().constData();return 1; }
        network=input.netlist;
    }
    if (!network || network->nets.isEmpty()) { std::cout<<QJsonDocument(QJsonObject{{"error",QStringLiteral("没有可用网络，请指定 NET 或提供含 NETDEF 的板图。")}}).toJson().constData();return 1; }
    const auto result=pt::analyzeCopper(*board.document,*network);QJsonArray nets;
    int connected=0,separated=0,unknown=0;
    for (const auto& net:result.nets) {
        QString state;
        if (net.state==pt::CopperNetState::Connected) { ++connected;state=QStringLiteral("connected_in_model"); }
        else if (net.state==pt::CopperNetState::Separated) { ++separated;state=QStringLiteral("separated_in_model"); }
        else { ++unknown;state=QStringLiteral("indeterminate"); }
        nets.append(QJsonObject{{"name",net.name},{"state",state},{"pads",qint64(net.padCount)},
            {"definite_groups",qint64(net.definiteGroups)},{"possible_groups",qint64(net.possibleGroups)},{"reason",net.reason}});
    }
    QJsonArray contacts;
    for (const auto& contact:result.crossNetContacts) {
        QJsonArray indices,identities;for (const auto pad:contact.pads) indices.append(qint64(pad+1));
        for (const auto& identity:contact.identities) identities.append(identity);
        contacts.append(QJsonObject{{"nets",QJsonArray::fromStringList(contact.nets)},{"pad_numbers_1_based",indices},{"pad_identities",identities}});
    }
    const QJsonObject output{{"board_sha256",board.document->sha256},{"netlist_sha256",network->sha256},
        {"coverage_complete",result.coverageComplete},{"limit_reached",result.limitReached},{"connected",connected},
        {"separated",separated},{"indeterminate",unknown},{"cross_net_contact_groups",qint64(result.crossNetContacts.size())},
        {"modeled_copper_elements",qint64(result.copperElements)},
        {"pair_checks",qint64(result.pairChecks)},{"nets",nets},{"cross_net_contacts",contacts},
        {"limitations",QJsonArray::fromStringList(result.limitations)},
        {"notice",QStringLiteral("理想镀通孔及受限几何模型，不是完整 DRC；退出码 0 也不代表制造验收通过。")}};
    std::cout<<QJsonDocument(output).toJson().constData();
    if (!result.coverageComplete || unknown>0) return 3;
    return separated>0 || !result.crossNetContacts.isEmpty()?2:0;
}
