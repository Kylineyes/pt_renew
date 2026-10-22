#pragma once

#include "application/NetlistMapping.h"

namespace pt {

enum class CopperNetState { Connected, Separated, Indeterminate };
struct CopperNetResult {
    QString name;
    CopperNetState state=CopperNetState::Indeterminate;
    qsizetype padCount=0;
    qsizetype definiteGroups=0,possibleGroups=0;
    QString reason;
};
struct CopperContact {
    QStringList nets;
    QList<qsizetype> pads;
    QStringList identities;
};
struct CopperCoverageIssue {
    PrimitiveId primitive;
    PrimitiveSource source;
    int layer=0;
    QString object,reason;
};
inline constexpr qsizetype maximumCopperCoverageIssues=200;
struct CopperAnalysis {
    QList<CopperNetResult> nets;
    QList<CopperCoverageIssue> coverageIssues;
    qsizetype coverageIssueCount=0;
    QList<CopperContact> crossNetContacts;
    QStringList limitations;
    qsizetype copperElements=0,pairChecks=0;
    bool coverageComplete=true;
    bool limitReached=false;
};
struct CopperAnalysisLimits {
    qsizetype maximumElements=4000;
    qsizetype maximumPairChecks=250000;
    qint64 maximumMilliseconds=10000;
};

// 用内接/外接多边形建立两个接触图；边界接触只进入“可能图”，避免近似误报通过。
CopperAnalysis analyzeCopper(const BoardDocument& board,const Netlist& netlist,
                            const CopperAnalysisLimits& limits={});
QString copperCoverageIssueText(const CopperCoverageIssue& issue);
QString copperAnalysisText(const CopperAnalysis& analysis);

}
