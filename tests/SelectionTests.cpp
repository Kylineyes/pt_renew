#include "geometry/BoardGeometry.h"
#include "io/LegacyPcbReader.h"
#include "ui/BoardCanvas.h"
#include "ui/MainWindow.h"
#include <QAction>
#include <QDockWidget>
#include <QFile>
#include <QLineEdit>
#include <QMenu>
#include <QPlainTextEdit>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QtTest/QTest>
#include <limits>

class SelectionTests final : public QObject {
    Q_OBJECT
private:
    static std::shared_ptr<pt::BoardDocument> overlapBoard() {
        auto board=std::make_shared<pt::BoardDocument>();
        board->pads.append({{0,0},60,60,1,20,1,13,QStringLiteral("1")});
        board->tracks.append({{-100,0},{100,0},10,1});
        return board;
    }
    static void expose(pt::MainWindow& window) {
        window.show(); window.activateWindow();
        QVERIFY(QTest::qWaitForWindowExposed(&window));
        QVERIFY(QTest::qWaitForWindowActive(&window));
    }
    static pt::BoardCanvas* canvas(pt::MainWindow& window) { return window.findChild<pt::BoardCanvas*>(); }
    static void clickOrigin(pt::BoardCanvas* view) {
        QTest::mouseClick(view,Qt::LeftButton,Qt::NoModifier,view->boardToScreen({0,0}).toPoint());
    }
private slots:
    void trackUsesStrokeAndRoundCapsNotBoundingBox() {
        auto board=std::make_shared<pt::BoardDocument>();
        board->tracks.append({{0,0},{100,100},10,1});
        pt::BoardHitTester tester; tester.setDocument(board);
        QCOMPARE(tester.hitTest({50,50},0,{1}).size(),1);
        QVERIFY(tester.hitTest({0,100},0,{1}).isEmpty());
        QVERIFY(!tester.hitTest({-3,-3},0,{1}).isEmpty());
        QVERIFY(tester.hitTest({-6,-6},0,{1}).isEmpty());
        QCOMPARE(tester.hitTest({-6,-6},5,{1}).size(),1);
    }
    void padsUseActualOutlinesAndIncludeLogicalDrill() {
        auto board=std::make_shared<pt::BoardDocument>();
        board->pads.append({{0,0},40,40,1,20,1,13,{}});
        pt::BoardHitTester tester; tester.setDocument(board);
        QCOMPARE(tester.hitTest({0,0},0,{13}).size(),1);
        QVERIFY(tester.hitTest({19,19},0,{13}).isEmpty());
        QVERIFY(!tester.hitTest({20,0},2,{13}).isEmpty());
        for (int shape : {1,2,3,4}) {
            board=std::make_shared<pt::BoardDocument>();
            board->pads.append({{0,0},40,60,shape,0,1,13,{}});
            tester.setDocument(board);
            QCOMPARE(tester.hitTest({0,0},0,{13}).size(),1);
        }
    }
    void arcQuadrantsAndCenterVoid_data() {
        QTest::addColumn<int>("mask"); QTest::addColumn<QPointF>("hit");
        QTest::newRow("upper-right") << 1 << QPointF(70.71,70.71);
        QTest::newRow("upper-left") << 2 << QPointF(-70.71,70.71);
        QTest::newRow("lower-left") << 4 << QPointF(-70.71,-70.71);
        QTest::newRow("lower-right") << 8 << QPointF(70.71,-70.71);
    }
    void arcQuadrantsAndCenterVoid() {
        QFETCH(int,mask); QFETCH(QPointF,hit);
        auto board=std::make_shared<pt::BoardDocument>();
        board->arcs.append({{0,0},100,mask,10,7});
        pt::BoardHitTester tester; tester.setDocument(board);
        QCOMPARE(tester.hitTest(hit,1,{7}).size(),1);
        QVERIFY(tester.hitTest(-hit,1,{7}).isEmpty());
        QVERIFY(tester.hitTest({0,0},5,{7}).isEmpty());
    }
    void viaFillTextAndInvalidIdentifiers() {
        auto board=std::make_shared<pt::BoardDocument>();
        board->vias.append({{0,0},40,20});
        board->fills.append({QRectF(100,100,50,50),6});
        board->texts.append({{300,300},40,1,3,7,true,QStringLiteral("R1")});
        pt::BoardHitTester tester; tester.setDocument(board);
        QCOMPARE(tester.hitTest({0,0},0,{13}).first().kind,pt::PrimitiveKind::Via);
        QCOMPARE(tester.hitTest({120,120},0,{6}).first().kind,pt::PrimitiveKind::Fill);
        const pt::PrimitiveId text{pt::PrimitiveKind::Text,0};
        const auto bounds=pt::primitiveBounds(*board,text);
        QVERIFY(!bounds.isEmpty());
        QCOMPARE(tester.hitTest(bounds.center(),0,{7}).first().kind,pt::PrimitiveKind::Text);
        QVERIFY(pt::primitiveOutline(*board,{pt::PrimitiveKind::Pad,99}).isEmpty());
        QCOMPARE(pt::primitiveLayer(*board,{pt::PrimitiveKind::Via,-1}),0);
    }
    void layeringAndInputValidation() {
        const auto board=overlapBoard();
        pt::BoardHitTester tester; tester.setDocument(board);
        const auto hits=tester.hitTest({0,0},1,{1,13});
        QCOMPARE(hits.size(),2); QCOMPARE(hits[0].kind,pt::PrimitiveKind::Pad);
        QCOMPARE(hits[1].kind,pt::PrimitiveKind::Track);
        QCOMPARE(tester.hitTest({0,0},1,{1}).size(),1);
        QVERIFY(tester.hitTest({0,0},1,{}).isEmpty());
        QVERIFY(tester.hitTest({0,0},-1,{1}).isEmpty());
        QVERIFY(tester.hitTest({0,0},std::numeric_limits<qreal>::quiet_NaN(),{1}).isEmpty());
        QVERIFY(tester.hitTest({std::numeric_limits<qreal>::infinity(),0},1,{1}).isEmpty());
        tester.setDocument(nullptr); QVERIFY(tester.hitTest({0,0},1,{1}).isEmpty());
    }
    void sourceRowsAndOwnershipSurviveParsing() {
        const QByteArray bytes(
            "PCB FILE 4\nCOMP\nU9\nDIP\nComment\n10 20 60 0 10 7\n20 30 60 0 10 7\n100 200 1 1 2\n"
            "CP\n10 10 60 60 2 20 1 13\n1\nENDCOMP\nFT\n0 0 100 0 10 1 42\nENDPCB\n");
        const auto result=pt::LegacyPcbReader::parse(bytes);
        QVERIFY2(result.succeeded(),qPrintable(result.error));
        const auto& board=*result.document;
        const auto source=pt::primitiveSource(board,{pt::PrimitiveKind::Pad,0});
        QCOMPARE(source.line,9); QCOMPARE(source.component,0);
        QCOMPARE(pt::primitiveSource(board,{pt::PrimitiveKind::Text,0}).line,7);
        QCOMPARE(pt::primitiveSource(board,{pt::PrimitiveKind::Track,0}).component,-1);
        const auto description=pt::primitiveDescription(board,{pt::PrimitiveKind::Pad,0});
        QVERIFY(description.contains(QStringLiteral("U9")));
        QVERIFY(description.contains(QStringLiteral("DIP")));
        QVERIFY(description.contains(QStringLiteral("0.5080 mm")));
        QVERIFY(pt::primitiveDescription(board,{pt::PrimitiveKind::Track,0}).contains(QStringLiteral("42（语义未确认）")));
    }
    void repeatedClickCyclesAndBlankClears() {
        pt::MainWindow window; expose(window);
        auto* view=canvas(window); view->setDocument(overlapBoard());
        clickOrigin(view);
        QVERIFY(view->selection()); QCOMPARE(view->selection()->kind,pt::PrimitiveKind::Pad);
        QCOMPARE(view->overlapCount(),2);
        clickOrigin(view); QCOMPARE(view->selection()->kind,pt::PrimitiveKind::Track);
        clickOrigin(view); QCOMPARE(view->selection()->kind,pt::PrimitiveKind::Pad);
        auto* properties=window.findChild<QPlainTextEdit*>(QStringLiteral("selectionText"));
        QVERIFY(properties->isReadOnly()); QVERIFY(properties->toPlainText().contains(QStringLiteral("类型：焊盘")));
        QTest::mouseClick(view,Qt::LeftButton,Qt::NoModifier,QPoint(30,view->height()-30));
        QVERIFY(!view->selection());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("selection.next"))->isEnabled());
    }
    void keyboardAndMenuShareSelectionCommands() {
        pt::MainWindow window; expose(window);
        auto* view=canvas(window); view->setDocument(overlapBoard()); clickOrigin(view);
        QSignalSpy spy(&window,&pt::MainWindow::commandInvoked);
        QTest::keyClick(view,Qt::Key_Tab,Qt::ControlModifier);
        QTRY_COMPARE(spy.size(),1);
        QVERIFY(view->selection()); QCOMPARE(view->selection()->kind,pt::PrimitiveKind::Track);
        QCOMPARE(spy.last().at(0).toString(),QStringLiteral("selection.next"));
        auto* edit=window.findChild<QMenu*>(QStringLiteral("menu.E"));
        QTest::keyClick(view,Qt::Key_E);
        QTRY_VERIFY(edit->isVisible());
        auto* next=window.findChild<QAction*>(QStringLiteral("selection.next"));
        QTest::mouseClick(edit,Qt::LeftButton,Qt::NoModifier,edit->actionGeometry(next).center());
        QCOMPARE(view->selection()->kind,pt::PrimitiveKind::Pad);
        view->setFocus(); QTest::keyClick(view,Qt::Key_Escape);
        QVERIFY(!view->selection());
        QCOMPARE(spy.last().at(0).toString(),QStringLiteral("selection.clear"));
    }
    void textFocusAndMenuEscapeDoNotStealSelection() {
        pt::MainWindow window; expose(window);
        auto* view=canvas(window); view->setDocument(overlapBoard()); clickOrigin(view);
        QLineEdit edit(&window); edit.setGeometry(80,180,180,32); edit.show(); edit.setFocus();
        QTest::keyClicks(&edit,"file"); QTest::keyClick(&edit,Qt::Key_Escape);
        QCOMPARE(edit.text(),QStringLiteral("file")); QVERIFY(view->selection());
        view->setFocus(); QTest::keyClick(view,Qt::Key_F);
        auto* menu=window.findChild<QMenu*>(QStringLiteral("menu.F"));
        QTRY_VERIFY(menu->isVisible()); QTest::keyClick(menu,Qt::Key_Escape);
        QVERIFY(view->selection());
    }
    void hiddenLayerAndNewDocumentInvalidateSelection() {
        pt::MainWindow window; expose(window);
        auto* view=canvas(window); view->setDocument(overlapBoard()); clickOrigin(view);
        view->setLayerVisible(13,false); QVERIFY(!view->selection());
        clickOrigin(view); QVERIFY(view->selection()); QCOMPARE(view->selection()->kind,pt::PrimitiveKind::Track);
        view->setLayerVisible(13,true); QCOMPARE(view->overlapCount(),0);
        view->setDocument(overlapBoard()); QVERIFY(!view->selection());
        clickOrigin(view); view->setDocument(nullptr); QVERIFY(!view->selection());
        QVERIFY(window.findChild<QPlainTextEdit*>(QStringLiteral("selectionText"))->toPlainText().contains(QStringLiteral("尚未选择")));
    }
    void coordinateRoundtripAndSelectionSurviveZoomPan() {
        pt::MainWindow window; expose(window);
        auto* view=canvas(window); view->setDocument(overlapBoard());
        for (int i=0;i<5;++i) view->zoomIn();
        const QPointF original(30,-12);
        QVERIFY((view->screenToBoard(view->boardToScreen(original))-original).manhattanLength()<1e-7);
        clickOrigin(view); QVERIFY(view->selection());
        const auto selected=*view->selection();
        const QPoint middle=view->rect().center();
        QTest::mousePress(view,Qt::MiddleButton,Qt::NoModifier,middle);
        QTest::mouseMove(view,middle+QPoint(50,30));
        QTest::mouseRelease(view,Qt::MiddleButton,Qt::NoModifier,middle+QPoint(50,30));
        QVERIFY(view->selection()); QVERIFY(*view->selection()==selected);
        view->clearSelection(); clickOrigin(view); QVERIFY(view->selection());
    }
    void screenToleranceIsStableAcrossZoomLevels() {
        pt::MainWindow window; expose(window);
        auto* view=canvas(window);
        for (int zoomSteps : {-2,0,2}) {
            view->setDocument(overlapBoard());
            for (int step=0;step<qAbs(zoomSteps);++step) {
                if (zoomSteps<0) view->zoomOut(); else view->zoomIn();
            }
            const QPointF edge=view->boardToScreen({0,30});
            QTest::mouseClick(view,Qt::LeftButton,Qt::NoModifier,(edge-QPointF(0,3)).toPoint());
            QVERIFY(view->selection()); QCOMPARE(view->selection()->kind,pt::PrimitiveKind::Pad);
            QTest::mouseClick(view,Qt::LeftButton,Qt::NoModifier,(edge-QPointF(0,10)).toPoint());
            QVERIFY(!view->selection());
        }
    }

    void selectingNeverModifiesSourceOrEnablesSave() {
        QTemporaryDir directory;
        const auto path=directory.filePath(QStringLiteral("board.pcb"));
        const QByteArray bytes("PCB FILE 4\nFP\n0 0 60 60 1 20 1 13\n1\nENDPCB\n");
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); file.write(bytes); file.close();
        pt::MainWindow window; expose(window); QVERIFY(window.inspectFile(path));
        auto* view=canvas(window); clickOrigin(view); QVERIFY(view->selection());
        const auto text=window.findChild<QPlainTextEdit*>(QStringLiteral("selectionText"))->toPlainText();
        QVERIFY(text.contains(QStringLiteral("源文件行：2")));
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.save"))->isEnabled());
        QVERIFY(file.open(QIODevice::ReadOnly)); QCOMPARE(file.readAll(),bytes);
        window.findChild<QAction*>(QStringLiteral("file.close"))->trigger(); QVERIFY(!view->selection());
    }
};
QTEST_MAIN(SelectionTests)
#include "SelectionTests.moc"
