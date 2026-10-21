#include "application/ComponentTableModel.h"
#include "domain/Measurement.h"
#include "geometry/BoardGeometry.h"
#include "ui/BoardCanvas.h"
#include "ui/ComponentBrowser.h"
#include "ui/MainWindow.h"
#include <QAction>
#include <QFile>
#include <QLineEdit>
#include <QMenu>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSignalSpy>
#include <QTableView>
#include <QTemporaryDir>
#include <QtTest/QTest>

class NavigationTests final : public QObject {
    Q_OBJECT
private:
    static std::shared_ptr<pt::BoardDocument> board() {
        auto result=std::make_shared<pt::BoardDocument>();
        result->components.append({QStringLiteral("U1"),QStringLiteral("DIP8"),QStringLiteral("控制器"),{100,100},2});
        result->components.append({QStringLiteral("R7"),QStringLiteral("AXIAL0.4"),QStringLiteral("4k7"),{900,400},2});
        result->pads.append({{100,100},60,60,1,20,1,13,QStringLiteral("1"),{9,0}});
        result->pads.append({{900,400},60,60,1,20,1,13,QStringLiteral("1"),{20,1}});
        return result;
    }
    static QByteArray fileBytes() {
        return "PCB FILE 4\nCOMP\nR7\nAXIAL\n4k7\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 2\n"
               "CP\n0 0 60 60 1 20 1 13\n1\nENDCOMP\nFT\n0 0 300 400 10 1\nENDPCB\n";
    }
    static void expose(pt::MainWindow& window) {
        window.show(); window.activateWindow();
        QVERIFY(QTest::qWaitForWindowExposed(&window));
        QVERIFY(QTest::qWaitForWindowActive(&window));
    }
    static void click(pt::BoardCanvas* canvas,const QPointF& p) {
        QTest::mouseClick(canvas,Qt::LeftButton,Qt::NoModifier,canvas->boardToScreen(p).toPoint());
    }
private slots:
    void componentModelAndSourceIndexes() {
        pt::ComponentTableModel model; QCOMPARE(model.rowCount(),0);
        model.setDocument(board()); QCOMPARE(model.rowCount(),2); QCOMPARE(model.columnCount(),3);
        QCOMPARE(model.data(model.index(1,0)).toString(),QStringLiteral("R7"));
        QCOMPARE(model.data(model.index(1,1)).toString(),QStringLiteral("AXIAL0.4"));
        QVERIFY(!model.data(model.index(10,0)).isValid());
        QCOMPARE(model.rowCount(model.index(0,0)),0);
        model.setDocument(nullptr); QCOMPARE(model.rowCount(),0);
    }
    void browserFiltersLiteralTextAndActivatesSourceRow() {
        pt::ComponentBrowser browser; browser.setDocument(board()); browser.show();
        QVERIFY(QTest::qWaitForWindowExposed(&browser));
        auto* search=browser.findChild<QLineEdit*>(QStringLiteral("componentSearch"));
        auto* table=browser.findChild<QTableView*>(QStringLiteral("componentTable"));
        auto* go=browser.findChild<QPushButton*>(QStringLiteral("componentGo"));
        QSignalSpy spy(&browser,&pt::ComponentBrowser::componentActivated);
        search->setText(QStringLiteral("axial0.4")); QCOMPARE(table->model()->rowCount(),1);
        QTest::keyClick(search,Qt::Key_Return); QCOMPARE(spy.size(),1); QCOMPARE(spy.last().at(0).toLongLong(),1);
        search->setText(QStringLiteral("[")); QCOMPARE(table->model()->rowCount(),0); QVERIFY(!go->isEnabled());
        QTest::keyClick(search,Qt::Key_Return); QCOMPARE(spy.size(),1);
        search->setText(QStringLiteral("控制")); QCOMPARE(table->model()->rowCount(),1);
        QTest::mouseClick(go,Qt::LeftButton); QCOMPARE(spy.last().at(0).toLongLong(),0);
        search->clear(); table->sortByColumn(0,Qt::DescendingOrder); table->setCurrentIndex(table->model()->index(1,0));
        QTest::mouseClick(go,Qt::LeftButton); QCOMPARE(spy.last().at(0).toLongLong(),1);
        browser.setDocument(nullptr); QCOMPARE(table->model()->rowCount(),0); QVERIFY(!go->isEnabled());
    }
    void componentBoundsUseAbsoluteOwnershipAndFallbackOrigin() {
        const auto document=board();
        const auto bounds=pt::componentBounds(*document,1);
        QCOMPARE(bounds,QRectF(870,370,60,60));
        QVERIFY(pt::componentBounds(*document,99).isEmpty());
        document->components.append({QStringLiteral("EMPTY"),{},{},{3000,4000},2});
        QCOMPARE(pt::componentBounds(*document,2).center(),QPointF(3000,4000));
        pt::BoardCanvas canvas; canvas.resize(800,600); canvas.setDocument(document);
        canvas.setLayerVisible(13,false);
        QVERIFY(canvas.focusComponent(1)); QCOMPARE(*canvas.focusedComponent(),1);
        QVERIFY(!canvas.layerVisible(13));
        QVERIFY((canvas.boardToScreen({900,400})-QPointF(canvas.rect().center())).manhattanLength()<1e-6);
        QVERIFY(!canvas.focusComponent(-1));
        canvas.clearSelection(); QVERIFY(!canvas.focusedComponent());
    }
    void measurementMath() {
        const pt::Measurement measurement{{10,20},{310,420}};
        QCOMPARE(measurement.deltaX(),300); QCOMPARE(measurement.deltaY(),400); QCOMPARE(measurement.distance(),500);
        QVERIFY(qAbs(measurement.angleDegrees()-53.130102)<0.00001);
        QCOMPARE((pt::Measurement{{1,1},{1,1}}).distance(),0);
        QCOMPARE((pt::Measurement{{0,0},{-1,0}}).angleDegrees(),180);
    }
    void measurementTwoPointsPanZoomAndLifecycle() {
        pt::BoardCanvas canvas; canvas.resize(900,650); canvas.setDocument(board()); canvas.show();
        QVERIFY(QTest::qWaitForWindowExposed(&canvas));
        canvas.setMeasurementMode(true); QVERIFY(canvas.measurementMode());
        const auto screenA=canvas.boardToScreen({100,100}).toPoint();
        const auto screenB=canvas.boardToScreen({400,500}).toPoint();
        const auto expectedA=canvas.screenToBoard(screenA),expectedB=canvas.screenToBoard(screenB);
        QTest::mouseClick(&canvas,Qt::LeftButton,Qt::NoModifier,screenA);
        QVERIFY(canvas.measurementStart()); QVERIFY(!canvas.selection());
        QTest::mouseClick(&canvas,Qt::LeftButton,Qt::NoModifier,screenB);
        QVERIFY(canvas.measurement()); QVERIFY(!canvas.measurementStart());
        QCOMPARE(canvas.measurement()->start,expectedA); QCOMPARE(canvas.measurement()->end,expectedB);
        const qreal distance=canvas.measurement()->distance();
        canvas.zoomIn(); canvas.centerOn({400,500}); QCOMPARE(canvas.measurement()->distance(),distance);
        canvas.setMeasurementMode(false); QVERIFY(canvas.measurement());
        canvas.setMeasurementMode(true); click(&canvas,{100,100}); QVERIFY(canvas.measurementStart()); QVERIFY(!canvas.measurement());
        canvas.setMeasurementMode(false); QVERIFY(!canvas.measurementStart());
        canvas.setMeasurementMode(true); click(&canvas,{100,100}); click(&canvas,{100,100});
        QCOMPARE(canvas.measurement()->distance(),0);
        canvas.clearMeasurement(); QVERIFY(!canvas.measurement()); QVERIFY(canvas.measurementMode());
        canvas.setDocument(nullptr); QVERIFY(!canvas.measurementMode()); QVERIFY(!canvas.measurement());
    }
    void commandsSearchMeasurementAndEscape() {
        QTemporaryDir directory; const auto path=directory.filePath(QStringLiteral("board.pcb"));
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); file.write(fileBytes()); file.close();
        pt::MainWindow window; expose(window); QVERIFY(window.inspectFile(path));
        auto* canvas=window.findChild<pt::BoardCanvas*>();
        auto* search=window.findChild<QLineEdit*>(QStringLiteral("componentSearch"));
        QSignalSpy commands(&window,&pt::MainWindow::commandInvoked);
        canvas->setFocus(); QTest::keyClick(canvas,Qt::Key_J);
        auto* jumpMenu=window.findChild<QMenu*>(QStringLiteral("menu.J")); QTRY_VERIFY(jumpMenu->isVisible());
        QTest::keyClick(jumpMenu,Qt::Key_C); QTRY_VERIFY(search->hasFocus());
        QVERIFY(!commands.isEmpty()); QCOMPARE(commands.last().at(0).toString(),QStringLiteral("jump.component"));
        canvas->setFocus(); QTest::keyClick(canvas,Qt::Key_F,Qt::ControlModifier);
        QTRY_VERIFY(search->hasFocus()); QTest::keyClicks(search,"r7"); QTest::keyClick(search,Qt::Key_Return);
        QVERIFY(canvas->focusedComponent()); QCOMPARE(*canvas->focusedComponent(),0);
        QVERIFY(window.findChild<QPlainTextEdit*>(QStringLiteral("selectionText"))->toPlainText().contains(QStringLiteral("R7")));
        QVERIFY(canvas->hasFocus());
        QTest::keyClick(canvas,Qt::Key_M,Qt::ControlModifier); QVERIFY(canvas->measurementMode());
        QVERIFY(window.findChild<QAction*>(QStringLiteral("measure.toggle"))->isChecked());
        click(canvas,{0,0}); click(canvas,{100,100}); QVERIFY(canvas->measurement());
        auto* output=window.findChild<QPlainTextEdit*>(QStringLiteral("measureText")); QVERIFY(output->isReadOnly());
        QVERIFY(output->toPlainText().contains(QStringLiteral("距离：")));
        QTest::keyClick(canvas,Qt::Key_I);
        auto* menu=window.findChild<QMenu*>(QStringLiteral("menu.I")); QTRY_VERIFY(menu->isVisible());
        QTest::keyClick(menu,Qt::Key_Escape); QVERIFY(canvas->measurementMode());
        canvas->setFocus(); QTest::keyClick(canvas,Qt::Key_Escape); QVERIFY(!canvas->measurementMode()); QVERIFY(canvas->measurement());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("measure.toggle"))->isChecked());
        window.findChild<QAction*>(QStringLiteral("measure.clear"))->trigger(); QVERIFY(!canvas->measurement());
        canvas->setFocus(); QTest::keyClick(canvas,Qt::Key_Home,Qt::ControlModifier);
        QVERIFY((canvas->boardToScreen({0,0})-QPointF(canvas->rect().center())).manhattanLength()<1e-6);
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.save"))->isEnabled());
        QVERIFY(file.open(QIODevice::ReadOnly)); QCOMPARE(file.readAll(),fileBytes()); file.close();
        window.findChild<QAction*>(QStringLiteral("file.close"))->trigger();
        QVERIFY(!canvas->measurement()); QVERIFY(!canvas->focusedComponent());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("jump.component"))->isEnabled());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("measure.toggle"))->isEnabled());
    }
    void emptyBoardAndTextFocus() {
        pt::MainWindow window; expose(window);
        auto* canvas=window.findChild<pt::BoardCanvas*>(); canvas->setDocument(board());
        canvas->setFocus(); QTest::keyClick(canvas,Qt::Key_M,Qt::ControlModifier); QVERIFY(canvas->measurementMode());
        QLineEdit text(&window); text.setGeometry(100,180,220,32); text.show(); text.setFocus();
        QTest::keyClick(&text,Qt::Key_Escape); QVERIFY(canvas->measurementMode());
        QTest::keyClicks(&text,"jump"); QCOMPARE(text.text(),QStringLiteral("jump"));
        canvas->setFocus(); QTest::keyClick(canvas,Qt::Key_Escape); QVERIFY(!canvas->measurementMode());
        QVERIFY(!canvas->focusComponent(99));
    }
};
QTEST_MAIN(NavigationTests)
#include "NavigationTests.moc"
