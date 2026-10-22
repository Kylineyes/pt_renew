#include "geometry/CopperConnectivity.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyNetlistReader.h"
#include "ui/MainWindow.h"
#include "ui/NetlistBrowser.h"
#include "ui/BoardCanvas.h"
#include <QAction>
#include <QFile>
#include <QMenu>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QProcess>
#include <QStandardPaths>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QtTest/QTest>
#include <cmath>

namespace {
pt::BoardDocument board(int layer=1,int shape=2,int drill=0) {
    pt::BoardDocument result;
    result.components.append({QStringLiteral("U1"),{},{},{},0});
    result.components.append({QStringLiteral("U2"),{},{},{},0});
    result.pads.append({{0,0},40,40,shape,drill,1,layer,QStringLiteral("1"),{0,0}});
    result.pads.append({{200,0},40,40,shape,drill,1,layer,QStringLiteral("1"),{0,1}});
    return result;
}
pt::Netlist netlist() {
    pt::Netlist result;result.nets.append({QStringLiteral("A"),{{QStringLiteral("U1-1"),1},{QStringLiteral("U2-1"),2}},1,{}});return result;
}
QByteArray pcbBytes() {
    return "PCB FILE 4\nCOMP\nU1\nDIP\nV\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 2\nCP\n0 0 40 40 2 0 1 1\n1\nENDCOMP\n"
           "COMP\nU2\nDIP\nV\n200 0 10 0 1 7\n200 0 10 0 1 7\n200 0 2 2 2\nCP\n200 0 40 40 2 0 1 1\n1\nENDCOMP\nFT\n0 0 200 0 10 1\nENDPCB\n";
}
QByteArray netBytes() { return "(\nA\nU1-1\nU2-1\n)\n"; }
}
class CopperTests final:public QObject {
    Q_OBJECT
private slots:
    void separatedPadsDoNotBecomeConnectedFromMappingAlone() {
        const auto result=pt::analyzeCopper(board(),netlist());
        QVERIFY(result.coverageComplete);QCOMPARE(result.nets[0].state,pt::CopperNetState::Separated);
        QCOMPARE(result.nets[0].definiteGroups,2);QCOMPARE(result.nets[0].possibleGroups,2);
    }
    void straightTrackAndTransitiveSegmentsConnect() {
        auto b=board();b.tracks.append({{0,0},{100,0},10,1});b.tracks.append({{100,0},{200,0},10,1});
        const auto result=pt::analyzeCopper(b,netlist());
        QCOMPARE(result.nets[0].state,pt::CopperNetState::Connected);QCOMPARE(result.nets[0].definiteGroups,1);
        QCOMPARE(b.tracks.size(),2);
    }
    void copperCrossingsAndRoundCapsConnect() {
        auto b=board();b.pads[1].center={0,200};
        b.tracks.append({{-100,100},{100,100},20,1});b.tracks.append({{0,0},{0,200},10,1});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
        b=board();b.tracks.append({{15,0},{185,0},20,1});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
    }
    void differentLayersDoNotJoinAtCrossings() {
        auto b=board();b.pads[1].layer=6;
        b.tracks.append({{0,0},{100,0},20,1});b.tracks.append({{100,0},{200,0},20,6});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Separated);
        b.vias.append({{100,0},60,20});
        const auto result=pt::analyzeCopper(b,netlist());QCOMPARE(result.nets[0].state,pt::CopperNetState::Connected);
        QVERIFY(result.limitations.join('\n').contains(QStringLiteral("理想镀通孔")));
    }
    void multilayerPlatedPadBridgesButUnplatedIsUnknown() {
        auto b=board();b.pads[1].layer=6;
        b.components.append({QStringLiteral("BRIDGE"),{},{},{},0});
        b.pads.append({{100,0},60,60,1,20,1,13,QStringLiteral("1"),{0,2}});
        b.tracks.append({{0,0},{100,0},12,1});b.tracks.append({{100,0},{200,0},12,6});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
        b.pads.last().drill=0;const auto result=pt::analyzeCopper(b,netlist());
        QVERIFY(!result.coverageComplete);QCOMPARE(result.nets[0].state,pt::CopperNetState::Indeterminate);
    }
    void rectangularCopperFillConnectsButSilkscreenCannot() {
        auto b=board();b.fills.append({QRectF(-10,-10,220,20),1});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
        b.fills[0].layer=7;const auto result=pt::analyzeCopper(b,netlist());
        QVERIFY(result.coverageComplete);QCOMPARE(result.nets[0].state,pt::CopperNetState::Separated);
    }
    void drilledHoleIsNotSolidCopper() {
        auto b=board();b.pads[0].width=100;b.pads[0].height=100;b.pads[0].drill=80;b.pads[0].shape=1;
        b.pads[1].center={0,0};b.pads[1].width=10;b.pads[1].height=10;b.pads[1].shape=1;
        const auto result=pt::analyzeCopper(b,netlist());
        QVERIFY(result.coverageComplete);QCOMPARE(result.nets[0].state,pt::CopperNetState::Separated);
    }
    void tangentAndNearEnvelopeAreIndeterminate() {
        auto b=board(1,1);b.pads[1].center={40,0};
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Indeterminate);
        b.pads[1].center={40.02,0};QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Indeterminate);
        b.pads[1].center={40.2,0};QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Separated);
        b.pads[1].center={39,0};QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
    }
    void arcMasksKeepDisconnectedQuadrantsSeparate_data() {
        QTest::addColumn<int>("mask");
        QTest::addColumn<int>("targetQuadrant");
        for (int mask=1;mask<=15;++mask) for (int quadrant=0;quadrant<4;++quadrant) {
            const auto name=QByteArray::number(mask)+"-"+QByteArray::number(quadrant);
            QTest::newRow(name.constData()) << mask << quadrant;
        }
    }
    void arcMasksKeepDisconnectedQuadrantsSeparate() {
        QFETCH(int,mask);
        QFETCH(int,targetQuadrant);
        int first=0;while (!(mask&(1<<first))) ++first;
        int reachable=1<<first;
        for (int step=0;step<4;++step) {
            const int neighbors=((reachable<<1)|(reachable>>3)|(reachable>>1)|(reachable<<3))&15;
            reachable|=neighbors&mask;
        }
        const qreal diagonal=100/std::sqrt(2.0);
        const QPointF midpoints[]{{diagonal,diagonal},{-diagonal,diagonal},
                                 {-diagonal,-diagonal},{diagonal,-diagonal}};
        const QPointF center(100000,-200000);
        auto b=board();
        for (auto& pad:b.pads) { pad.width=4;pad.height=4; }
        b.pads[0].center=center+midpoints[first];b.pads[1].center=center+midpoints[targetQuadrant];
        b.arcs.append({center,100,mask,10,1});
        const auto result=pt::analyzeCopper(b,netlist());
        QVERIFY(result.coverageComplete);
        const auto expected=(reachable&(1<<targetQuadrant))?pt::CopperNetState::Connected:pt::CopperNetState::Separated;
        QCOMPARE(result.nets[0].state,expected);
    }
    void arcEndpointsAndLayerIsolation() {
        auto b=board();b.pads[0].center={100,-8};b.pads[1].center={-8,100};
        for (auto& pad:b.pads) { pad.width=2;pad.height=2; }
        b.arcs.append({{0,0},100,1,20,1});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
        b.arcs[0].layer=6;
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Separated);
        b.arcs[0].layer=7;
        const auto silk=pt::analyzeCopper(b,netlist());
        QVERIFY(silk.coverageComplete);QCOMPARE(silk.copperElements,2);
        QCOMPARE(silk.nets[0].state,pt::CopperNetState::Separated);
    }
    void arcInteriorStaysEmptyAndTouchingIsIndeterminate() {
        auto b=board();b.pads[0].center={100,0};b.pads[1].center={0,0};
        for (auto& pad:b.pads) { pad.width=2;pad.height=2; }
        b.arcs.append({{0,0},100,15,20,1});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Separated);
        b.pads[1].center={111,0};
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Indeterminate);
        b.pads[1].center={112,0};
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Separated);
        b.pads[1].center={110,0};
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
    }
    void arcTrackViaAndContactCandidates() {
        auto b=board();b.pads[0].center={100,-100};b.pads[1].center={-100,100};b.pads[1].layer=6;
        b.arcs.append({{0,0},100,1,20,1});
        b.tracks.append({{100,-100},{100,0},10,1});
        b.tracks.append({{0,100},{-100,100},10,6});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Separated);
        b.vias.append({{0,100},40,10});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
        auto n=netlist();n.nets[0].nodes.removeLast();n.nets.append({QStringLiteral("B"),{{QStringLiteral("U2-1"),1}},1,{}});
        const auto result=pt::analyzeCopper(b,n);
        QCOMPARE(result.crossNetContacts.size(),1);
        QCOMPARE(result.crossNetContacts[0].identities,QStringList({QStringLiteral("U1-1"),QStringLiteral("U2-1")}));
    }
    void unsupportedArcsKeepAllNetsIndeterminate_data() {
        QTest::addColumn<int>("variant");
        QTest::newRow("zero-radius") << 0;QTest::newRow("zero-width") << 1;
        QTest::newRow("empty-mask") << 2;QTest::newRow("invalid-mask") << 3;
        QTest::newRow("thin-envelope") << 4;QTest::newRow("plane") << 5;
        QTest::newRow("multilayer") << 6;
    }
    void unsupportedArcsKeepAllNetsIndeterminate() {
        QFETCH(int,variant);
        auto b=board();b.tracks.append({{0,0},{200,0},10,1});
        pt::Arc arc{{500,500},100,1,10,1};
        if (variant==0) arc.radius=0;
        if (variant==1) arc.width=0;
        if (variant==2) arc.quadrants=0;
        if (variant==3) arc.quadrants=16;
        if (variant==4) { arc.radius=1000000;arc.width=1; }
        if (variant==5) arc.layer=9;
        if (variant==6) arc.layer=13;
        b.arcs.append(arc);
        const auto result=pt::analyzeCopper(b,netlist());
        QVERIFY(!result.coverageComplete);QCOMPARE(result.nets[0].state,pt::CopperNetState::Indeterminate);
    }
    void wideArcsAndInnerTangencyStayConservative() {
        auto b=board();b.pads[0].center={100,0};b.pads[1].center={88,0};
        for (auto& pad:b.pads) { pad.width=2;pad.height=2; }
        b.arcs.append({{0,0},100,1,20,1});
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Separated);
        b.pads[1].center={89,0};
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Indeterminate);
        b.pads[1].center={90,0};
        QCOMPARE(pt::analyzeCopper(b,netlist()).nets[0].state,pt::CopperNetState::Connected);
        b.pads[1].center={0,0};b.arcs[0].width=220;
        const auto wide=pt::analyzeCopper(b,netlist());
        QVERIFY(wide.coverageComplete);QCOMPARE(wide.nets[0].state,pt::CopperNetState::Connected);
    }
    void arcQuadrantsRespectElementBudget() {
        auto b=board();b.pads[0].center={100,0};b.pads[1].center={-100,0};
        b.arcs.append({{0,0},100,15,10,1});
        pt::CopperAnalysisLimits limits;limits.maximumElements=5;
        const auto result=pt::analyzeCopper(b,netlist(),limits);
        QVERIFY(result.limitReached);QVERIFY(!result.coverageComplete);
        QCOMPARE(result.copperElements,5);QCOMPARE(result.nets[0].state,pt::CopperNetState::Indeterminate);
    }
    void unsupportedCopperCannotProduceFalseSeparatedResult_data() {
        QTest::addColumn<int>("variant");QTest::newRow("text")<<1;
        QTest::newRow("plane")<<2;QTest::newRow("octagon")<<3;QTest::newRow("plane-flags")<<4;
    }
    void unsupportedCopperCannotProduceFalseSeparatedResult() {
        QFETCH(int,variant);auto b=board();
        if (variant==1) b.texts.append({{0,0},100,0,10,1,false,QStringLiteral("铜字")});
        if (variant==2) b.fills.append({QRectF(-20,-20,240,40),9});
        if (variant==3) b.pads[0].shape=3;
        if (variant==4) b.pads[0].planeFlags=2;
        const auto result=pt::analyzeCopper(b,netlist());QVERIFY(!result.coverageComplete);
        QCOMPARE(result.nets[0].state,pt::CopperNetState::Indeterminate);
    }
    void unsupportedExtraCannotReportAnyNetAsConnectedOrSeparated() {
        auto b=board();b.tracks.append({{0,0},{200,0},10,1});b.texts.append({{400,400},100,0,10,6,false,QStringLiteral("未知铜字")});
        const auto result=pt::analyzeCopper(b,netlist());QVERIFY(!result.coverageComplete);
        QCOMPARE(result.nets[0].state,pt::CopperNetState::Indeterminate);
        QVERIFY(result.nets[0].reason.contains(QStringLiteral("全板铜几何覆盖不完整")));
        QVERIFY(pt::copperAnalysisText(result).contains(QStringLiteral("存在未覆盖内容")));
    }
    void unexplainedTrackFieldsKeepCopperIndeterminate_data() {
        QTest::addColumn<int>("layer");
        QTest::addColumn<int>("extra");
        QTest::newRow("copper-zero") << 1 << 0;
        QTest::newRow("copper-nonzero") << 1 << 17;
        QTest::newRow("silkscreen-zero") << 7 << 0;
        QTest::newRow("silkscreen-nonzero") << 7 << 17;
    }
    void unexplainedTrackFieldsKeepCopperIndeterminate() {
        QFETCH(int,layer);
        QFETCH(int,extra);
        auto b=board();
        b.tracks.append({{0,0},{200,0},10,1});
        b.tracks.append({{0,100},{200,100},10,layer,extra});
        const auto result=pt::analyzeCopper(b,netlist());
        QCOMPARE(result.nets[0].definiteGroups,1);
        if (layer==1) {
            QVERIFY(!result.coverageComplete);
            QCOMPARE(result.nets[0].state,pt::CopperNetState::Indeterminate);
            QVERIFY(result.limitations.join('\n').contains(QStringLiteral("第七附加字段")));
        } else {
            QVERIFY(result.coverageComplete);
            QCOMPARE(result.nets[0].state,pt::CopperNetState::Connected);
        }
        QCOMPARE(b.tracks.last().extra.value(),extra);
    }
    void sameCopperAcrossNetworksProducesContactCandidate() {
        auto b=board();b.tracks.append({{0,0},{200,0},10,1});
        auto n=netlist();n.nets[0].nodes.removeLast();n.nets.append({QStringLiteral("B"),{{QStringLiteral("U2-1"),1}},1,{}});
        const auto result=pt::analyzeCopper(b,n);QCOMPARE(result.crossNetContacts.size(),1);
        QCOMPARE(result.crossNetContacts[0].nets,QStringList({QStringLiteral("A"),QStringLiteral("B")}));
        QCOMPARE(result.crossNetContacts[0].identities.size(),2);
        QVERIFY(pt::copperAnalysisText(result).contains(QStringLiteral("U1-1")));
    }
    void ambiguousMissingOrUnknownMetadataNeverPass() {
        auto b=board();b.tracks.append({{0,0},{200,0},10,1});auto n=netlist();
        n.nets[0].nodes.append({QStringLiteral("MISSING-1"),3});
        QCOMPARE(pt::analyzeCopper(b,n).nets[0].state,pt::CopperNetState::Indeterminate);
        n=netlist();n.nets[0].metadata="uninterpreted";
        QCOMPARE(pt::analyzeCopper(b,n).nets[0].state,pt::CopperNetState::Indeterminate);
        n=netlist();b.pads.append(b.pads.first());
        QCOMPARE(pt::analyzeCopper(b,n).nets[0].state,pt::CopperNetState::Indeterminate);
    }
    void elementPairAndTimeBudgetsCannotReportPass_data() {
        QTest::addColumn<int>("variant");QTest::newRow("elements")<<0;QTest::newRow("pairs")<<1;QTest::newRow("time")<<2;
    }
    void elementPairAndTimeBudgetsCannotReportPass() {
        QFETCH(int,variant);auto b=board();b.tracks.append({{0,0},{200,0},10,1});pt::CopperAnalysisLimits limits;
        if (variant==0) limits.maximumElements=0;
        if (variant==1) limits.maximumPairChecks=0;
        if (variant==2) limits.maximumMilliseconds=0;
        const auto result=pt::analyzeCopper(b,netlist(),limits);QVERIFY(result.limitReached);QVERIFY(!result.coverageComplete);
        QCOMPARE(result.nets[0].state,pt::CopperNetState::Indeterminate);
    }
    void backgroundUiAndStaleResultProtection_data() {
        QTest::addColumn<bool>("useArc");
        QTest::newRow("straight") << false;QTest::newRow("arc") << true;
    }
    void backgroundUiAndStaleResultProtection() {
        QFETCH(bool,useArc);
        auto input=pcbBytes();
        if (useArc) input.replace("FT\n0 0 200 0 10 1\n","FA\n100 0 100 3 10 1\n");
        QTemporaryDir dir;QFile pcb(dir.filePath(QStringLiteral("board.pcb")));QVERIFY(pcb.open(QIODevice::WriteOnly));pcb.write(input);pcb.close();
        QFile net(dir.filePath(QStringLiteral("fixture.net")));QVERIFY(net.open(QIODevice::WriteOnly));net.write(netBytes());net.close();
        pt::MainWindow window;window.show();window.activateWindow();QVERIFY(QTest::qWaitForWindowExposed(&window));QVERIFY(window.inspectFile(pcb.fileName()));
        auto* browser=window.findChild<pt::NetlistBrowser*>();QVERIFY(browser->loadFile(net.fileName()));
        auto* button=browser->findChild<QPushButton*>(QStringLiteral("copperAnalyze"));QVERIFY(button->isEnabled());
        QSignalSpy finished(browser,&pt::NetlistBrowser::copperAnalysisFinished);
        QTest::mouseClick(button,Qt::LeftButton);QTRY_COMPARE(finished.size(),1);QVERIFY(!browser->copperAnalysisRunning());
        auto* text=browser->findChild<QPlainTextEdit*>(QStringLiteral("netlistDetails"));QVERIFY(text->isReadOnly());
        QVERIFY(text->toPlainText().contains(QStringLiteral("支持模型内已连接")));
        QVERIFY(QTest::qWaitForWindowActive(&window));
        auto* canvas=window.findChild<pt::BoardCanvas*>();canvas->setFocus();
        QTest::keyClick(canvas,Qt::Key_C,Qt::ControlModifier|Qt::AltModifier);QTRY_COMPARE(finished.size(),2);
        canvas->setFocus();QTest::keyClick(canvas,Qt::Key_N);
        auto* menu=window.findChild<QMenu*>(QStringLiteral("menu.N"));QTRY_VERIFY(menu->isVisible());
        QTest::keyClick(menu,Qt::Key_A);QTRY_COMPARE(finished.size(),3);
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("netlist.drc"))->isEnabled());QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.save"))->isEnabled());
        browser->runCopperAnalysis();browser->setBoard(nullptr);QTRY_VERIFY(!browser->copperAnalysisRunning());
        QCOMPARE(finished.size(),3);QVERIFY(!text->toPlainText().contains(QStringLiteral("支持模型内已连接")));
        QVERIFY(pcb.open(QIODevice::ReadOnly));QCOMPARE(pcb.readAll(),input);
    }
    void cliReportsModelStateAndInvalidInputs() {
        QTemporaryDir dir;QFile pcb(dir.filePath(QStringLiteral("board.pcb")));QVERIFY(pcb.open(QIODevice::WriteOnly));pcb.write(pcbBytes());pcb.close();
        QFile net(dir.filePath(QStringLiteral("fixture.net")));QVERIFY(net.open(QIODevice::WriteOnly));net.write(netBytes());net.close();
        const auto executable=QStandardPaths::findExecutable(QStringLiteral("pt-copper-check"),{QCoreApplication::applicationDirPath()});QVERIFY(!executable.isEmpty());
        QProcess process;process.start(executable,{pcb.fileName(),net.fileName()});QVERIFY(process.waitForFinished(15000));QCOMPARE(process.exitCode(),0);
        const auto report=QJsonDocument::fromJson(process.readAllStandardOutput());QVERIFY(report.isObject());QCOMPARE(report.object().value(QStringLiteral("connected")).toInt(),1);
        QCOMPARE(report.object().value(QStringLiteral("nets")).toArray().size(),1);
        QVERIFY(report.object().contains(QStringLiteral("modeled_copper_elements")));
        QVERIFY(report.object().value(QStringLiteral("limitations")).isArray());
        QVERIFY(report.object().value(QStringLiteral("cross_net_contacts")).isArray());
        QVERIFY(pcb.open(QIODevice::WriteOnly));
        auto extendedBytes=pcbBytes();extendedBytes.replace("0 0 200 0 10 1\n","0 0 200 0 10 1 0\n");
        QCOMPARE(pcb.write(extendedBytes),extendedBytes.size());pcb.close();
        process.start(executable,{pcb.fileName(),net.fileName()});QVERIFY(process.waitForFinished(15000));QCOMPARE(process.exitCode(),3);
        const auto extendedReport=QJsonDocument::fromJson(process.readAllStandardOutput()).object();
        QVERIFY(!extendedReport.value(QStringLiteral("coverage_complete")).toBool());
        QCOMPARE(extendedReport.value(QStringLiteral("connected")).toInt(),0);
        QCOMPARE(extendedReport.value(QStringLiteral("indeterminate")).toInt(),1);
        QVERIFY(pcb.open(QIODevice::WriteOnly));auto bytes=pcbBytes();bytes.replace("FT\n0 0 200 0 10 1\n","");pcb.write(bytes);pcb.close();
        process.start(executable,{pcb.fileName(),net.fileName()});QVERIFY(process.waitForFinished(15000));QCOMPARE(process.exitCode(),2);
        QVERIFY(pcb.open(QIODevice::WriteOnly));bytes.replace("ENDPCB\n","FA\n100 0 100 15 10 1\nENDPCB\n");pcb.write(bytes);pcb.close();
        process.start(executable,{pcb.fileName(),net.fileName()});QVERIFY(process.waitForFinished(15000));QCOMPARE(process.exitCode(),0);
        const auto arcReport=QJsonDocument::fromJson(process.readAllStandardOutput()).object();
        QVERIFY(arcReport.value(QStringLiteral("coverage_complete")).toBool());
        QCOMPARE(arcReport.value(QStringLiteral("connected")).toInt(),1);
        QVERIFY(pcb.open(QIODevice::WriteOnly));bytes.replace("ENDPCB\n","FS\n0 0 100 0 10 1\nUNKNOWN\nENDPCB\n");pcb.write(bytes);pcb.close();
        process.start(executable,{pcb.fileName(),net.fileName()});QVERIFY(process.waitForFinished(15000));QCOMPARE(process.exitCode(),3);
        process.start(executable,{pcb.fileName()});QVERIFY(process.waitForFinished(15000));QCOMPARE(process.exitCode(),1);
    }
};
QTEST_MAIN(CopperTests)
#include "CopperTests.moc"
