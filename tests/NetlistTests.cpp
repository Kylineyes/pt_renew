#include "io/LegacyNetlistReader.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbInspector.h"
#include "application/NetlistMapping.h"
#include "ui/MainWindow.h"
#include "ui/NetlistBrowser.h"
#include "ui/BoardCanvas.h"
#include <QAction>
#include <QComboBox>
#include <QProcess>
#include <QStandardPaths>
#include <QJsonDocument>
#include <QJsonObject>
#include <QFile>
#include <QImage>
#include <QLineEdit>
#include <QListWidget>
#include <QMenu>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QtTest/QTest>

namespace {
QByteArray pcb(const QByteArray& suffix={}) {
    return "PCB FILE 4\nCOMP\nU1\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 2\n"
           "CP\n0 0 60 60 1 20 1 13\n1\nCP\n100 0 60 60 1 20 1 13\n2\nENDCOMP\n"+suffix+"ENDPCB\n";
}
QByteArray net() { return "[\nU1\nDIP\nValue\n\n\n\n]\n(\nGND\nU1-1\nU1-2\n)\n"; }
}
class NetlistTests final:public QObject {
    Q_OBJECT
private slots:
    void externalPreservesBytesMetadataAndDosEof() {
        const QByteArray input="[\r\nU1\r\nDIP\r\nValue\r\nextra\r\n\r\n\r\n]\r\n(\r\nGND\r\nU1-1\r\n)\r\n\x1a";
        const auto result=pt::LegacyNetlistReader::parse(input);
        QVERIFY2(result.succeeded(),qPrintable(result.error));
        QCOMPARE(result.netlist->sourceBytes,input);QCOMPARE(result.netlist->components.size(),1);QCOMPARE(result.netlist->nets.size(),1);
        QCOMPARE(result.netlist->components[0].additionalFields,QStringList({QStringLiteral("extra"),{}, {}}));
        QCOMPARE(result.netlist->nets[0].nodes[0].sourceLine,11);QCOMPARE(result.netlist->sha256.size(),64);
    }
    void invalidExternal_data() {
        QTest::addColumn<QByteArray>("input");
        QTest::newRow("unclosed-component")<<QByteArray("[\nU1\nDIP\nV\n");
        QTest::newRow("unclosed-net")<<QByteArray("(\nGND\nU1-1\n");
        QTest::newRow("nested-net")<<QByteArray("(\nGND\n(\nU1-1\n)\n");
        QTest::newRow("bad-node")<<QByteArray("(\nGND\nU1 1\n)\n");
        QTest::newRow("middle-eof")<<QByteArray("(\nGND\nU1-1\n)\n\x1a\n(\nX\nU1-2\n)\n");
        QTest::newRow("unknown-top")<<QByteArray("NETDEF\nGND\n");
        QTest::newRow("missing-comment")<<QByteArray("[\nU1\nDIP\n]\n");
        QTest::newRow("binary")<<(QByteArray("(\nGND\nU1-")+QByteArray(1,'\0')+"\n)\n");
        QTest::newRow("encoding")<<(QByteArray("(\nGND\nU1-")+QByteArray::fromHex("82")+"\n)\n");
        QTest::newRow("empty")<<QByteArray();
    }
    void invalidExternal() { QFETCH(QByteArray,input);const auto result=pt::LegacyNetlistReader::parse(input);QVERIFY(!result.succeeded());QVERIFY(!result.netlist); }
    void embeddedKeepsMetadataAndContinuesGeometry() {
        const QByteArray block="NETDEF\nGND\n[\noriginal metadata\n]\n(\nU1-1\n{\nraw node table\n}\nU1-2\n)\nFT\n0 0 100 0 12 1\n";
        const auto result=pt::LegacyPcbReader::parse(pcb(block));QVERIFY2(result.succeeded(),qPrintable(result.error));
        QVERIFY(result.document->embeddedNetlist);QCOMPARE(result.document->tracks.size(),1);
        const auto& network=*result.document->embeddedNetlist;QVERIFY(network.embedded);QCOMPARE(network.nets.size(),1);QCOMPARE(network.nets[0].nodes.size(),2);
        QCOMPARE(network.nets[0].sourceLine,17); QCOMPARE(network.nets[0].nodes[0].sourceLine,22);
        QVERIFY(network.nets[0].metadata.contains("original metadata"));QVERIFY(network.nets[0].metadata.contains("raw node table"));
        QCOMPARE(pt::mapNetlist(network,result.document.get()).resolved,2);
    }
    void badEmbeddedNeverReturnsPartialBoard_data() {
        QTest::addColumn<QByteArray>("block");
        QTest::newRow("missing-list-end")<<QByteArray("NETDEF\nGND\n(\nU1-1\n");
        QTest::newRow("unclosed-metadata")<<QByteArray("NETDEF\nGND\n[\nX\n");
        QTest::newRow("nested-metadata")<<QByteArray("NETDEF\nGND\n[\n{\n}\n]\n(\nU1-1\n)\n");
        QTest::newRow("missing-list")<<QByteArray("NETDEF\nGND\nU1-1\n");
    }
    void badEmbeddedNeverReturnsPartialBoard() {
        QFETCH(QByteArray,block);const auto result=pt::LegacyPcbReader::parse(pcb(block));QVERIFY(!result.succeeded());QVERIFY(!result.document);
    }
    void mappingExactAndReportsMetadataDifferences() {
        const auto board=pt::LegacyPcbReader::parse(pcb());QVERIFY(board.succeeded());
        auto input=net();input.replace("DIP","OTHER");const auto result=pt::LegacyNetlistReader::parse(input);QVERIFY(result.succeeded());
        const auto map=pt::mapNetlist(*result.netlist,board.document.get());QCOMPARE(map.resolved,2);QCOMPARE(map.missing,0);
        QVERIFY(map.diagnostics.join('\n').contains(QStringLiteral("封装差异")));QCOMPARE(map.nets[0].uniquePads.size(),2);
        input="(\nGND\nu1-1\n)\n";const auto lower=pt::LegacyNetlistReader::parse(input);
        QCOMPARE(pt::mapNetlist(*lower.netlist,board.document.get()).missing,1);
    }
    void missingAmbiguousDuplicateAndCrossNetMembership() {
        auto board=std::make_shared<pt::BoardDocument>();board->components.append({QStringLiteral("U-1"),{},{},{},0});
        board->pads.append({{0,0},60,60,1,20,1,13,QStringLiteral("P-1"),{0,0}});
        const auto network=pt::LegacyNetlistReader::parse("(\nA\nU-1-P-1\nU-1-P-1\nMISSING-1\n)\n(\nB\nU-1-P-1\n)\n");QVERIFY(network.succeeded());
        auto result=pt::mapNetlist(*network.netlist,board.get());QCOMPARE(result.conflicting,3);QCOMPARE(result.duplicates,1);QCOMPARE(result.missing,1);
        QVERIFY(result.nets[0].uniquePads.isEmpty());QVERIFY(result.nets[1].uniquePads.isEmpty());
        board->pads.append(board->pads.first());result=pt::mapNetlist(*network.netlist,board.get());QCOMPARE(result.ambiguous,3);
        QVERIFY(result.nets[0].uniquePads.isEmpty());
    }
    void duplicateReferencesAndHyphenCollisionsNeverAutoResolve() {
        auto board=std::make_shared<pt::BoardDocument>();
        board->components.append({QStringLiteral("U1"),{},{},{},0});board->components.append(board->components.first());
        board->pads.append({{0,0},60,60,1,20,1,13,QStringLiteral("1"),{0,0}});
        auto input=pt::LegacyNetlistReader::parse("(\nA\nU1-1\n)\n");QVERIFY(input.succeeded());
        auto result=pt::mapNetlist(*input.netlist,board.get());QCOMPARE(result.ambiguous,1);QCOMPARE(result.resolved,0);QVERIFY(result.nets[0].uniquePads.isEmpty());
        board->components.removeLast();
        input=pt::LegacyNetlistReader::parse("[\nU1\nDIP\nV\n]\n[\nU1\nDIP\nV\n]\n(\nA\nU1-1\n)\n");QVERIFY(input.succeeded());
        QCOMPARE(pt::mapNetlist(*input.netlist,board.get()).ambiguous,1);
        board->components[0].designator=QStringLiteral("U-1");board->components.append({QStringLiteral("U"),{},{},{},0});
        board->pads.append({{100,0},60,60,1,20,1,13,QStringLiteral("1-1"),{0,1}});
        input=pt::LegacyNetlistReader::parse("(\nA\nU-1-1\n)\n");QVERIFY(input.succeeded());
        QCOMPARE(pt::mapNetlist(*input.netlist,board.get()).ambiguous,1);
    }

    void duplicateNetNamesAreNotMerged() {
        const auto input=pt::LegacyNetlistReader::parse("(\nGND\nU1-1\n)\n(\nGND\nU1-2\n)\n");QVERIFY(input.succeeded());
        const auto result=pt::mapNetlist(*input.netlist,nullptr);QCOMPARE(result.nets.size(),2);QVERIFY(result.diagnostics.join('\n').contains(QStringLiteral("重复网络名")));QCOMPARE(result.resolved,0);
        const auto board=pt::LegacyPcbReader::parse(pcb());QVERIFY(board.succeeded());
        const auto mapped=pt::mapNetlist(*input.netlist,board.document.get());
        QCOMPARE(mapped.ambiguous,2);QCOMPARE(mapped.resolved,0);
        QVERIFY(mapped.nets[0].uniquePads.isEmpty());QVERIFY(mapped.nets[1].uniquePads.isEmpty());
    }
    void uiHighlightActivationAndBoardLifecycle() {
        QTemporaryDir dir;QFile boardFile(dir.filePath(QStringLiteral("board.pcb")));QVERIFY(boardFile.open(QIODevice::WriteOnly));boardFile.write(pcb());boardFile.close();
        QFile netFile(dir.filePath(QStringLiteral("fixture.net")));QVERIFY(netFile.open(QIODevice::WriteOnly));netFile.write(net());netFile.close();
        pt::MainWindow window;window.show();window.activateWindow();QVERIFY(QTest::qWaitForWindowExposed(&window));QVERIFY(QTest::qWaitForWindowActive(&window));QVERIFY(window.inspectFile(boardFile.fileName()));
        auto* browser=window.findChild<pt::NetlistBrowser*>();auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(browser->loadFile(netFile.fileName()));QCOMPARE(canvas->netPads().size(),2);
        auto* nodes=browser->findChild<QListWidget*>(QStringLiteral("netlistNodes"));QCOMPARE(nodes->count(),2);
        browser->show();browser->raise();nodes->setCurrentRow(1);nodes->setFocus();QTest::keyClick(nodes,Qt::Key_Return);
        QVERIFY(canvas->selection());QCOMPARE(canvas->selection()->index,1);
        QVERIFY((canvas->boardToScreen({100,0})-QPointF(canvas->rect().center())).manhattanLength()<1e-6);
        auto* search=browser->findChild<QLineEdit*>(QStringLiteral("netlistSearch"));search->setText(QStringLiteral("[") );QVERIFY(canvas->netPads().isEmpty());search->clear();QCOMPARE(canvas->netPads().size(),2);
        window.findChild<QAction*>(QStringLiteral("highlight.reset"))->trigger();QVERIFY(canvas->netPads().isEmpty());
        canvas->setFocus();QTest::keyClick(canvas,Qt::Key_N);auto* menu=window.findChild<QMenu*>(QStringLiteral("menu.N"));QTRY_VERIFY(menu->isVisible());QTest::keyClick(menu,Qt::Key_N);QTRY_VERIFY(search->hasFocus());
        search->clear();canvas->setFocus();QTest::keyClick(canvas,Qt::Key_N,Qt::ControlModifier|Qt::AltModifier);
        QTRY_VERIFY(search->hasFocus());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("netlist.drc"))->isEnabled());QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.save"))->isEnabled());
        QVERIFY(netFile.open(QIODevice::ReadOnly));QCOMPARE(netFile.readAll(),net());netFile.close();
        window.findChild<QAction*>(QStringLiteral("file.close"))->trigger();QVERIFY(!browser->netlist());QVERIFY(canvas->netPads().isEmpty());
    }
    void hiddenLayerNavigationDoesNotRevealPadOutline() {
        const auto board=pt::LegacyPcbReader::parse(pcb());QVERIFY(board.succeeded());
        pt::BoardCanvas canvas;canvas.resize(800,600);canvas.setDocument(board.document);canvas.setGridVisible(false);canvas.setLayerVisible(13,false);canvas.show();
        QVERIFY(QTest::qWaitForWindowExposed(&canvas));canvas.centerOn({0,0});
        const auto before=canvas.grab().toImage();QVERIFY(canvas.focusPad(0));QVERIFY(!canvas.layerVisible(13));
        QCOMPARE(canvas.grab().toImage(),before);
        canvas.setDocument(nullptr);QVERIFY(canvas.netPads().isEmpty());
    }

    void missingFileAndExplicitCancelClearPreviousExternalNetwork() {
        const auto board=pt::LegacyPcbReader::parse(pcb());QVERIFY(board.succeeded());
        QTemporaryDir dir;QFile file(dir.filePath(QStringLiteral("fixture.net")));
        QVERIFY(file.open(QIODevice::WriteOnly));file.write(net());file.close();
        pt::NetlistBrowser browser;browser.setBoard(board.document);
        QVERIFY(browser.loadFile(file.fileName()));QVERIFY(browser.netlist());
        QVERIFY(!browser.loadFile(dir.filePath(QStringLiteral("missing.net"))));QVERIFY(!browser.netlist());
        QSignalSpy loaded(&browser,&pt::NetlistBrowser::netlistLoaded);
        browser.requestFile(file.fileName());browser.clearExternal();
        QTRY_VERIFY(browser.findChild<QPushButton*>(QStringLiteral("netlistOpen"))->isEnabled());
        QVERIFY(!browser.netlist());QCOMPARE(loaded.size(),0);
        browser.requestFile(file.fileName());QTRY_COMPARE(loaded.size(),1);QVERIFY(browser.netlist());
        browser.setBoard(pt::LegacyPcbReader::parse(pcb()).document);
        QVERIFY(!browser.netlist());
    }

    void embeddedFallbackAndFailedExternalClearStaleData() {
        const auto board=pt::LegacyPcbReader::parse(pcb("NETDEF\nINTERNAL\n(\nU1-1\n)\n"));QVERIFY(board.succeeded());
        QTemporaryDir dir;QFile file(dir.filePath(QStringLiteral("external.net")));QVERIFY(file.open(QIODevice::WriteOnly));file.write(net());file.close();
        pt::NetlistBrowser browser;browser.setBoard(board.document);QVERIFY(browser.netlist()->embedded);
        QVERIFY(browser.loadFile(file.fileName()));QVERIFY(!browser.netlist()->embedded);
        auto* source=browser.findChild<QComboBox*>(QStringLiteral("netlistSource"));QCOMPARE(source->count(),2);
        source->setCurrentIndex(source->findData(0));QVERIFY(browser.netlist()->embedded);
        source->setCurrentIndex(source->findData(1));QVERIFY(!browser.netlist()->embedded);
        browser.clearExternal();QVERIFY(browser.netlist()->embedded);
        QVERIFY(!browser.loadFile(dir.filePath(QStringLiteral("missing.net"))));QVERIFY(browser.netlist()->embedded);QCOMPARE(browser.netlist()->nets[0].name,QStringLiteral("INTERNAL"));
        browser.setBoard(nullptr);QVERIFY(!browser.netlist());
    }
    void backgroundBoardChangeDiscardsLateResult() {
        QTemporaryDir dir;QFile file(dir.filePath(QStringLiteral("fixture.net")));QVERIFY(file.open(QIODevice::WriteOnly));file.write(net());file.close();
        pt::NetlistBrowser browser;QSignalSpy loaded(&browser,&pt::NetlistBrowser::netlistLoaded);
        browser.requestFile(file.fileName());browser.setBoard(nullptr);
        QTRY_VERIFY(browser.findChild<QPushButton*>(QStringLiteral("netlistOpen"))->isEnabled());QVERIFY(!browser.netlist());QCOMPARE(loaded.size(),0);
        browser.requestFile(file.fileName());QTRY_COMPARE(loaded.size(),1);QVERIFY(loaded.last()[0].toBool());QVERIFY(browser.netlist());
    }
    void dosEofAndMetadataArePreservedExactly() {
        const QByteArray block="NETDEF\r\nA\r\n[\r\n x  \r\n]\r\n(\r\nU1-1\r\n)\r\n";
        const auto embedded=pt::LegacyNetlistReader::readEmbedded(block,8,1);
        QVERIFY2(embedded.error.isEmpty(),qPrintable(embedded.error));QCOMPARE(embedded.net.metadata,QByteArray("[\r\n x  \r\n]\r\n"));
        const auto input=pcb("NETDEF\nA\n(\nU1-1\n)\n")+QByteArray("\x1a \t\r\n");
        const auto result=pt::LegacyPcbReader::parse(input);QVERIFY2(result.succeeded(),qPrintable(result.error));QCOMPARE(result.document->byteSize,input.size());
        QTemporaryDir directory;QFile file(directory.filePath(QStringLiteral("eof.pcb")));QVERIFY(file.open(QIODevice::WriteOnly));file.write(input);file.close();
        const auto info=pt::LegacyPcbInspector::inspect(file.fileName());QVERIFY(info.succeeded());QCOMPARE(info.info.sha256,result.document->sha256);
        QVERIFY(!pt::LegacyPcbReader::parse(input+"FT\n0 0 1 1 1 1\n").succeeded());
        QVERIFY(pt::LegacyNetlistReader::parse(net()+QByteArray("\x1a \t\r\n")).succeeded());
        auto board=std::make_shared<pt::BoardDocument>();board->components.append({QStringLiteral("U1"),{},{},{},0});
        board->pads.append({{0,0},60,60,1,20,1,13,QStringLiteral("-"),{0,0}});
        const auto negativePin=pt::LegacyNetlistReader::parse("(\nA\nU1--\n)\n");QVERIFY(negativePin.succeeded());
        QCOMPARE(pt::mapNetlist(*negativePin.netlist,board.get()).resolved,1);
    }

    void diagnosticToolExitCodesAndReadOnlyInputs() {
        QTemporaryDir dir;
        QFile boardFile(dir.filePath(QStringLiteral("board.pcb")));QVERIFY(boardFile.open(QIODevice::WriteOnly));boardFile.write(pcb());boardFile.close();
        QFile netFile(dir.filePath(QStringLiteral("fixture.net")));QVERIFY(netFile.open(QIODevice::WriteOnly));netFile.write(net());netFile.close();
        const auto executable=QStandardPaths::findExecutable(QStringLiteral("pt-netlist-check"),{QCoreApplication::applicationDirPath()});QVERIFY(!executable.isEmpty());
        QProcess process;process.start(executable,{netFile.fileName(),boardFile.fileName()});QVERIFY(process.waitForFinished(10000));QCOMPARE(process.exitCode(),0);
        const auto result=QJsonDocument::fromJson(process.readAllStandardOutput());QVERIFY(result.isObject());QCOMPARE(result.object().value(QStringLiteral("resolved")).toInt(),2);
        QVERIFY(netFile.open(QIODevice::ReadOnly));QCOMPARE(netFile.readAll(),net());netFile.close();
        QVERIFY(netFile.open(QIODevice::WriteOnly));netFile.write("(\nA\nMISSING-1\n)\n");netFile.close();
        process.start(executable,{netFile.fileName(),boardFile.fileName()});QVERIFY(process.waitForFinished(10000));QCOMPARE(process.exitCode(),2);
        QVERIFY(netFile.open(QIODevice::WriteOnly));netFile.write("invalid");netFile.close();
        process.start(executable,{netFile.fileName(),boardFile.fileName()});QVERIFY(process.waitForFinished(10000));QCOMPARE(process.exitCode(),1);
    }

    void resourceLimitsAndEofPlacement() {
        QVERIFY(!pt::LegacyNetlistReader::parse(QByteArray(8*1024*1024+1,' ')).succeeded());
        QVERIFY(!pt::LegacyNetlistReader::parse(QByteArray(65537,'A')).succeeded());
        QVERIFY(!pt::LegacyNetlistReader::parse("(\nA\nU1-1\n)\n\x1a\x1a").succeeded());
    }
};
QTEST_MAIN(NetlistTests)
#include "NetlistTests.moc"
