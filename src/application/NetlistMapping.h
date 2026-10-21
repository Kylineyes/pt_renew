#pragma once
#include "domain/BoardDocument.h"

namespace pt {
struct NodeResolution {
    QString token;
    qsizetype sourceLine=0;
    // 歧义时至多保留两个示例索引；原始板图不截断，状态报告候选数量下界。
    QList<qsizetype> pads;
    bool conflicting=false;
    bool ambiguous=false;
    QString status;
};
struct ResolvedNet {
    QString name;
    QList<NodeResolution> nodes;
    QList<qsizetype> uniquePads;
};
struct NetlistMapping {
    QList<ResolvedNet> nets;
    QStringList diagnostics;
    qsizetype resolved=0,missing=0,ambiguous=0,conflicting=0,duplicates=0;
};
NetlistMapping mapNetlist(const Netlist& netlist,const BoardDocument* board);
}
