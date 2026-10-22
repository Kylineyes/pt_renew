#pragma once
#include <QByteArray>
#include <QList>
#include <QStringList>
#include <memory>

namespace pt {
struct NetlistComponent {
    QString designator,footprint,comment;
    QStringList additionalFields;
    qsizetype sourceLine=0;
};
struct NetNode { QString token; qsizetype sourceLine=0; };
struct Net {
    QString name;
    QList<NetNode> nodes;
    qsizetype sourceLine=0;
    // NETDEF 中尚未解释的元数据原样保留，不推断连接或电气属性。
    QByteArray metadata;
};
struct Netlist {
    QString filePath,sha256;
    QByteArray sourceBytes;
    QList<NetlistComponent> components;
    QList<Net> nets;
    QStringList warnings;
    bool embedded=false;
};
struct NetlistReadResult {
    std::shared_ptr<const Netlist> netlist;
    QString error;
    bool succeeded() const { return netlist!=nullptr && error.isEmpty(); }
};
}
