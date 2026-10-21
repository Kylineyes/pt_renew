#pragma once
#include "domain/Netlist.h"

namespace pt {
struct EmbeddedNetResult {
    Net net;
    qsizetype nextOffset=0;
    qsizetype nextLine=0;
    QString error;
};
class LegacyNetlistReader {
public:
    static NetlistReadResult readFile(const QString& path);
    static NetlistReadResult parse(const QByteArray& bytes,const QString& source={});
    // offset/line 指向 NETDEF 后一行；返回首个尚未消费的字节和行基数。
    static EmbeddedNetResult readEmbedded(const QByteArray& bytes,qsizetype offset,qsizetype line);
};
}
