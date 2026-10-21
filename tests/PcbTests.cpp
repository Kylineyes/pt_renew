#include "io/LegacyPcbReader.h"
#include "ui/BoardCanvas.h"
#include "ui/BoardRenderer.h"
#include "ui/MainWindow.h"
#include <QAction>
#include <QDockWidget>
#include <QFile>
#include <QImage>
#include <QListWidget>
#include <QPainter>
#include <QSignalSpy>
#include <QStyle>
#include <QStyleOptionViewItem>
#include <QTemporaryDir>
#include <QtTest/QTest>

class PcbTests final : public QObject {
    Q_OBJECT
private:
    static QByteArray wrap(const QByteArray& records) { return "PCB FILE 4\n" + records + "ENDPCB\n"; }
    static QImage render(const pt::BoardDocument& board, const QSet<int>& layers) {
        QImage image(240,240,QImage::Format_ARGB32_Premultiplied);
        image.fill(QColor(26,30,35));
        QPainter painter(&image);
        painter.translate(120,120); painter.scale(1,-1);
        pt::drawBoard(painter, board, layers);
        return image;
    }
private slots:
    void parsesAllFreePrimitiveTypes() {
        const auto result = pt::LegacyPcbReader::parse(wrap(
            "FT\n-10 20 30 40 12 1\nFP\n100 200 60 80 1 20 1 13\nP1\n"
            "FV\n300 400 40 20\nFA\n100 100 50 5 10 7\n"
            "FF\n30 40 10 20 6\nFS\n100 200 60 17 10 7\nPCB FILE 4\n"));
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        const auto& b = *result.document;
        QCOMPARE(b.tracks.size(),1); QCOMPARE(b.pads.size(),1); QCOMPARE(b.vias.size(),1);
        QCOMPARE(b.arcs.size(),1); QCOMPARE(b.fills.size(),1); QCOMPARE(b.texts.size(),1);
        QCOMPARE(b.tracks[0].start,QPointF(-10,20));
        QCOMPARE(b.tracks[0].width,12); QCOMPARE(b.tracks[0].layer,1);
        QCOMPARE(b.pads[0].name,QStringLiteral("P1")); QCOMPARE(b.pads[0].drill,20);
        QCOMPARE(b.fills[0].rectangle,QRectF(10,20,20,20));
        QCOMPARE(b.arcs[0].quadrants,5);
        QVERIFY(b.texts[0].mirrored); QCOMPARE(b.texts[0].direction,1);
        QCOMPARE(b.texts[0].value,QStringLiteral("PCB FILE 4"));
        QCOMPARE(b.primitiveCount(),6);
    }

    void extendedTrackAttributeIsPreservedAndWarned() {
        const auto result = pt::LegacyPcbReader::parse(wrap("FT\n0 0 100 100 12 6 42\n"));
        QVERIFY(result.succeeded());
        QVERIFY(result.document->tracks[0].extra.has_value());
        QCOMPARE(*result.document->tracks[0].extra,42);
        QVERIFY(result.document->warnings.join('\n').contains(QStringLiteral("第七")));
    }

    void componentCoordinatesAreAlreadyAbsolute() {
        const auto result = pt::LegacyPcbReader::parse(wrap(
            "COMP\nR1\nAXIAL\n\n200 300 60 0 10 7\n250 350 60 1 10 7\n100 100 1 2 2\n"
            "CT\n150 160 170 180 12 7\nCP\n300 400 60 60 2 20 1 13\nENDPCB\nENDCOMP\n"));
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        const auto& b = *result.document;
        QCOMPARE(b.components.size(),1); QCOMPARE(b.components[0].origin,QPointF(100,100));
        QCOMPARE(b.components[0].comment,QString());
        QCOMPARE(b.tracks[0].start,QPointF(150,160));
        QCOMPARE(b.pads[0].name,QStringLiteral("ENDPCB"));
        QCOMPARE(b.texts.size(),1); QCOMPARE(b.texts[0].value,QStringLiteral("R1"));
        QCOMPARE(b.texts[0].position,QPointF(250,350));
    }

    void emptyAndKeywordTextAreNotControlRecords() {
        const auto result = pt::LegacyPcbReader::parse(wrap(
            "FS\n0 0 10 0 1 7\n\nFS\n0 0 10 0 1 7\nFT\n"));
        QVERIFY2(result.succeeded(),qPrintable(result.error));
        QCOMPARE(result.document->texts.size(),2);
        QCOMPARE(result.document->recordCounts.value(QStringLiteral("FT")),0);
        QCOMPARE(result.document->texts[1].value,QStringLiteral("FT"));
    }

    void rejectsMalformedRecords_data() {
        QTest::addColumn<QByteArray>("records");
        QTest::newRow("unknown") << QByteArray("UNKNOWN\nGND\n");
        QTest::newRow("bad-number") << QByteArray("FT\n0 0 bad 10 1 1\n");
        QTest::newRow("bad-count") << QByteArray("FT\n0 0 10 10 1 1 9 10\n");
        QTest::newRow("integer-overflow") << QByteArray("FT\n99999999999999 0 10 10 1 1\n");
        QTest::newRow("coordinate-limit") << QByteArray("FT\n1000001 0 10 10 1 1\n");
        QTest::newRow("negative-width") << QByteArray("FT\n0 0 10 10 -1 1\n");
        QTest::newRow("bad-layer") << QByteArray("FT\n0 0 10 10 1 14\n");
        QTest::newRow("bad-quadrant") << QByteArray("FA\n0 0 10 16 1 7\n");
        QTest::newRow("pad-shape") << QByteArray("FP\n0 0 10 10 5 0 1 1\n1\n");
        QTest::newRow("drill-too-big") << QByteArray("FP\n0 0 10 10 1 12 1 13\n1\n");
        QTest::newRow("missing-text") << QByteArray("FS\n0 0 10 0 1 7\n");
        QTest::newRow("invalid-rotation") << QByteArray("FS\n0 0 10 5 1 7\nText\n");
        QTest::newRow("unmatched-component") << QByteArray("ENDCOMP\n");
        QTest::newRow("wrong-scope") << QByteArray("CT\n0 0 10 10 1 7\n");
        QTest::newRow("degenerate-fill") << QByteArray("FF\n0 0 0 20 1\n");
    }
    void rejectsMalformedRecords() {
        QFETCH(QByteArray,records);
        const auto result = pt::LegacyPcbReader::parse(wrap(records));
        QVERIFY(!result.succeeded()); QVERIFY(!result.document); QVERIFY(!result.error.isEmpty());
    }

    void preservesLineNumbersAndRejectsUnclosedComponents() {
        const auto result = pt::LegacyPcbReader::parse(wrap("FT\n0 0 1 1 abc 7\n"));
        QVERIFY(result.error.contains(QStringLiteral("第 3 行")));
        const auto unclosed = pt::LegacyPcbReader::parse(wrap(
            "COMP\nU1\nDIP\nV\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 1 1 2\n"));
        QVERIFY(!unclosed.succeeded());
    }

    void readOnlyInputAndUnsupportedEncodingAreExplicit() {
        QTemporaryDir directory;
        const auto path=directory.filePath(QStringLiteral("只读板图.PCB"));
        const auto bytes=wrap(QByteArray("FS\n0 0 10 0 1 7\n") + QByteArray::fromHex("82") + '\n');
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); file.write(bytes); file.close();
        const auto result=pt::LegacyPcbReader::readFile(path);
        QVERIFY2(result.succeeded(),qPrintable(result.error));
        QVERIFY(result.document->warnings.join('\n').contains(QStringLiteral("非 ASCII")));
        QVERIFY(file.open(QIODevice::ReadOnly)); QCOMPARE(file.readAll(),bytes);
    }

    void rendererRespectsLayersAndDrillHoles() {
        pt::BoardDocument board;
        board.pads.append({{0,0},60,60,1,20,1,13,QStringLiteral("1")});
        board.tracks.append({{-80,60},{80,60},10,1});
        const QColor background(26,30,35);
        const auto image=render(board,{1,13});
        QCOMPARE(image.pixelColor(120,120),background);
        QCOMPARE(image.pixelColor(140,120),pt::layerColor(13));
        QCOMPARE(image.pixelColor(120,60),pt::layerColor(1));
        const auto hidden=render(board,{});
        QCOMPARE(hidden.pixelColor(140,120),background);
        QCOMPARE(hidden.pixelColor(120,60),background);
    }

    void arcQuadrantUsesYUpCoordinates() {
        pt::BoardDocument board;
        board.arcs.append({{0,0},60,1,8,7});
        const auto image=render(board,{7});
        QCOMPARE(image.pixelColor(162,78),pt::layerColor(7));
        QCOMPARE(image.pixelColor(162,162),QColor(26,30,35));
        QCOMPARE(image.pixelColor(78,78),QColor(26,30,35));
    }

    void canvasFitsCoordinatesAndClearsOnClose() {
        auto board=std::make_shared<pt::BoardDocument>();
        board->tracks.append({{0,0},{1000,500},10,1});
        pt::BoardCanvas canvas; canvas.resize(800,600); canvas.setDocument(board);
        const auto center=canvas.boardToScreen(QPointF(500,250));
        QVERIFY((center-QPointF(canvas.rect().center())).manhattanLength()<1);
        QVERIFY(canvas.boardToScreen({0,500}).y()<canvas.boardToScreen({0,0}).y());
        canvas.setLayerVisible(1,false); QVERIFY(!canvas.layerVisible(1));
        canvas.setDocument(nullptr); QVERIFY(!canvas.document());
    }

    void layerCheckboxFollowsMouseAndPanelCanBeRestored() {
        pt::MainWindow window; window.show();
        QVERIFY(QTest::qWaitForWindowExposed(&window));
        auto* canvas=window.findChild<pt::BoardCanvas*>();
        auto* layers=window.findChild<QListWidget*>(QStringLiteral("layerList"));
        auto* dock=window.findChild<QDockWidget*>(QStringLiteral("layerDock"));
        const auto rect=layers->visualItemRect(layers->item(0));
        QVERIFY(canvas->layerVisible(1));
        QStyleOptionViewItem option;
        option.initFrom(layers->viewport());
        option.rect=rect;
        option.features=QStyleOptionViewItem::HasCheckIndicator;
        option.checkState=Qt::Checked;
        const QRect indicator=layers->style()->subElementRect(QStyle::SE_ItemViewItemCheckIndicator,&option,layers);
        QVERIFY(indicator.isValid());
        QTest::mouseClick(layers->viewport(),Qt::LeftButton,Qt::NoModifier,indicator.center());
        QVERIFY(!canvas->layerVisible(1));
        dock->hide(); QVERIFY(dock->isHidden());
        window.findChild<QAction*>(QStringLiteral("setup.layers"))->trigger();
        QVERIFY(!dock->isHidden());
    }

    void asynchronousOpenAndCloseCannotRestoreStaleBoard() {
        QTemporaryDir directory;
        const auto path=directory.filePath(QStringLiteral("async.pcb"));
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly));
        file.write(wrap("FT\n0 0 100 100 10 1 1\n")); file.close();
        pt::MainWindow window;
        QSignalSpy finished(&window,&pt::MainWindow::boardLoadFinished);
        window.requestOpenFile(path);
        QTRY_COMPARE(finished.size(),1);
        QVERIFY(finished.at(0).at(0).toBool());
        auto* canvas=window.findChild<pt::BoardCanvas*>(); QVERIFY(canvas->document());
        window.requestOpenFile(path);
        window.findChild<QAction*>(QStringLiteral("file.close"))->trigger();
        QTRY_VERIFY(window.findChild<QAction*>(QStringLiteral("file.open"))->isEnabled());
        QVERIFY(!canvas->document());
        QCOMPARE(finished.size(),1);
    }

    void windowSharesLayersAndRejectsPartialBoards() {
        QTemporaryDir directory;
        const auto path=directory.filePath(QStringLiteral("board.pcb"));
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly));
        file.write(wrap("FT\n0 0 100 100 10 1\n")); file.close();
        pt::MainWindow window;
        QVERIFY(window.inspectFile(path));
        auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->document()); QCOMPARE(canvas->document()->tracks.size(),1);
        auto* layers=window.findChild<QListWidget*>(QStringLiteral("layerList"));
        layers->item(0)->setCheckState(Qt::Unchecked); QVERIFY(!canvas->layerVisible(1));
        QVERIFY(file.open(QIODevice::WriteOnly)); file.write(wrap("NETDEF\nGND\n")); file.close();
        QVERIFY(!window.inspectFile(path)); QVERIFY(!canvas->document());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.save"))->isEnabled());
    }
};
QTEST_MAIN(PcbTests)
#include "PcbTests.moc"
