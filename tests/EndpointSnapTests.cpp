#include "geometry/EndpointSnapIndex.h"
#include "io/LegacyPcbReader.h"
#include "ui/BoardCanvas.h"
#include "ui/MainWindow.h"
#include <QAction>
#include <QFile>
#include <QLineEdit>
#include <QMenu>
#include <QMouseEvent>
#include <QPlainTextEdit>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QtTest/QTest>
#include <limits>

class EndpointSnapTests final : public QObject {
    Q_OBJECT
private:
    static std::shared_ptr<pt::BoardDocument> board() {
        auto result = std::make_shared<pt::BoardDocument>();
        result->tracks.append({{100,100}, {400,500}, 10, 1, {}, {2,-1}});
        return result;
    }
    static void expose(QWidget& widget) {
        widget.show(); widget.activateWindow();
        QVERIFY(QTest::qWaitForWindowExposed(&widget));
        QVERIFY(QTest::qWaitForWindowActive(&widget));
    }
    static void pick(pt::BoardCanvas& canvas, QPointF point, QPoint offset = {4,3}) {
        QTest::mouseClick(&canvas, Qt::LeftButton, Qt::NoModifier, canvas.boardToScreen(point).toPoint() + offset);
    }
    static void hover(pt::BoardCanvas& canvas, QPoint position) {
        QMouseEvent event(QEvent::MouseMove, QPointF(position), QPointF(canvas.mapToGlobal(position)),
                          Qt::NoButton, Qt::NoButton, Qt::NoModifier);
        QCoreApplication::sendEvent(&canvas, &event);
    }
private slots:
    void nearestUsesCircleLayersAndStableTieOrder() {
        pt::BoardDocument document;
        document.tracks.append({{5,0}, {-5,0}, 1, 1});
        document.pads.append({{0,0}, 10, 10, 1, 0, 0, 7});
        pt::EndpointSnapIndex index; index.setDocument(&document);
        const auto tied = index.nearest({0,0}, 5, {1});
        QVERIFY(tied); QCOMPARE(tied->position, QPointF(5,0));
        QCOMPARE(index.nearest({0,0}, 5, {1,7})->primitive.kind, pt::PrimitiveKind::Pad);
        QVERIFY(!index.nearest({0,0}, 4.99, {1}));
        QVERIFY(!index.nearest({9,4}, 5, {1}));
        QVERIFY(!index.nearest({0,0}, 100, {}));
        QVERIFY(!index.nearest({0,0}, -1, {1}));
        QVERIFY(!index.nearest({0,0}, std::numeric_limits<qreal>::infinity(), {1}));
        QVERIFY(!index.nearest({std::numeric_limits<qreal>::quiet_NaN(),0}, 10, {1}));
        index.setDocument(nullptr); QVERIFY(!index.nearest({0,0}, 100, {1,7}));
    }
    void centersCornersAndTextExclusion() {
        pt::BoardDocument document;
        document.pads.append({{100,100}, 80, 60, 2, 20, 0, 13});
        document.vias.append({{300,100}, 60, 20});
        document.fills.append({QRectF(600,200,-100,-100), 6});
        document.texts.append({{900,100}, 100, 0, 1, 1, false, QStringLiteral("A")});
        pt::EndpointSnapIndex index; index.setDocument(&document);
        QCOMPARE(index.nearest({100,100}, 0, {13})->primitive.kind, pt::PrimitiveKind::Pad);
        QCOMPARE(index.nearest({300,100}, 0, {13})->primitive.kind, pt::PrimitiveKind::Via);
        QVERIFY(!index.nearest({140,100}, 1, {13}));
        for (const auto point : {QPointF(500,100), QPointF(600,100), QPointF(500,200), QPointF(600,200)}) {
            const auto result = index.nearest(point, 0, {6});
            QVERIFY(result); QCOMPARE(result->primitive.kind, pt::PrimitiveKind::Fill);
            QCOMPARE(result->position, point);
        }
        QVERIFY(!index.nearest({550,100}, 1, {6}));
        QVERIFY(!index.nearest({900,100}, 10, {1}));
    }
    void arcEndpointsFollowEnabledRuns_data() {
        QTest::addColumn<int>("mask"); QTest::addColumn<int>("endpoints");
        QTest::newRow("quarter") << 1 << 3;
        QTest::newRow("upper-half") << 3 << 5;
        QTest::newRow("disjoint") << 5 << 15;
        QTest::newRow("three-quarters") << 7 << 9;
        QTest::newRow("wrap") << 9 << 10;
        QTest::newRow("full-circle") << 15 << 0;
    }
    void arcEndpointsFollowEnabledRuns() {
        QFETCH(int, mask); QFETCH(int, endpoints);
        pt::BoardDocument document;
        document.arcs.append({{200,200}, 100, mask, 10, 7});
        pt::EndpointSnapIndex index; index.setDocument(&document);
        const QList<QPointF> points{{300,200}, {200,300}, {100,200}, {200,100}};
        for (int i = 0; i < 4; ++i) {
            const auto result = index.nearest(points[i], 0, {7});
            QCOMPARE(bool(result), (endpoints & (1 << i)) != 0);
            if (result) QCOMPARE(result->primitive.kind, pt::PrimitiveKind::Arc);
        }
        QVERIFY(!index.nearest({200,200}, 1, {7}));
    }
    void replacingIndexRemovesOldPointsAndFindsDistantCoordinates() {
        auto document = board();
        pt::EndpointSnapIndex index; index.setDocument(document.get());
        QVERIFY(index.nearest({100,100}, 1, {1}));
        document = std::make_shared<pt::BoardDocument>();
        for (int i = 0; i < 12000; ++i) document->vias.append({{qreal(i*80), -qreal(i*20)}, 20, 10});
        index.setDocument(document.get());
        QVERIFY(!index.nearest({100,100}, 1, {1,13}));
        const auto result = index.nearest({880000,-220000}, 1, {13});
        QVERIFY(result); QCOMPARE(result->primitive.index, 11000);
    }
    void canvasUsesExactCoordinatesAndKeepsCompletedProvenance() {
        pt::BoardCanvas canvas; canvas.resize(900,650); canvas.setDocument(board()); expose(canvas);
        QVERIFY(!canvas.measurementSnapEnabled());
        canvas.setMeasurementSnapEnabled(true); canvas.setMeasurementMode(true);
        pick(canvas, {100,100}); pick(canvas, {400,500});
        QVERIFY(canvas.measurement());
        QCOMPARE(canvas.measurement()->start, QPointF(100,100));
        QCOMPARE(canvas.measurement()->end, QPointF(400,500));
        QCOMPARE(canvas.measurement()->distance(), 500);
        QVERIFY(canvas.measurement()->startAnchor); QVERIFY(canvas.measurement()->endAnchor);
        canvas.setMeasurementSnapEnabled(false);
        QCOMPARE(canvas.measurement()->distance(), 500);
        QVERIFY(canvas.measurement()->startAnchor);
        // 第一端捕捉后关闭设置，第二端仍可自由取点；结果保留各自实际来源。
        canvas.setMeasurementSnapEnabled(true); pick(canvas, {100,100});
        canvas.setMeasurementSnapEnabled(false); pick(canvas, {400,500});
        QVERIFY(canvas.measurement()->startAnchor); QVERIFY(!canvas.measurement()->endAnchor);
        canvas.setDocument(board());
        QVERIFY(!canvas.measurement()); QVERIFY(!canvas.measurementSnapEnabled());
    }
    void screenRadiusHiddenLayersAndPreviewLifecycle() {
        pt::BoardCanvas canvas; canvas.resize(900,650); canvas.setDocument(board()); expose(canvas);
        canvas.setMeasurementSnapEnabled(true); canvas.setMeasurementMode(true);
        for (int zoom = 0; zoom < 3; ++zoom) {
            if (zoom) canvas.zoomIn();
            canvas.centerOn({100,100});
            pick(canvas, {100,100}, {8,0});
            QCOMPARE(*canvas.measurementStart(), QPointF(100,100)); canvas.clearMeasurement();
            pick(canvas, {100,100}, {14,0});
            QVERIFY(*canvas.measurementStart() != QPointF(100,100)); canvas.clearMeasurement();
        }
        const auto screen = canvas.boardToScreen({100,100}).toPoint() + QPoint(2,2);
        hover(canvas, screen); QVERIFY(canvas.snapPreview());
        QCOMPARE(canvas.snapPreview()->position, QPointF(100,100));
        canvas.setLayerVisible(1,false); QVERIFY(!canvas.snapPreview());
        pick(canvas, {100,100}); pick(canvas, {400,500});
        QVERIFY(!canvas.measurement()->startAnchor); QVERIFY(!canvas.measurement()->endAnchor);
        canvas.setLayerVisible(1,true);
        hover(canvas, screen + QPoint(1,0)); QVERIFY(canvas.snapPreview());
        canvas.zoomIn(); QVERIFY(!canvas.snapPreview());
        canvas.setMeasurementMode(false); QVERIFY(!canvas.snapPreview());
        canvas.setDocument(nullptr); QVERIFY(!canvas.measurementSnapEnabled());
    }
    void commandsShareMenuStateRespectTextFocusAndNeverChangeInput() {
        QTemporaryDir directory; const auto path = directory.filePath(QStringLiteral("端点.PCB"));
        const QByteArray bytes("PCB FILE 4\nFT\n100 100 400 500 10 1\nENDPCB\n");
        QFile input(path); QVERIFY(input.open(QIODevice::WriteOnly)); input.write(bytes); input.close();
        pt::MainWindow window; expose(window);
        auto* action = window.findChild<QAction*>(QStringLiteral("measure.snap"));
        QVERIFY(!action->isEnabled()); QVERIFY(window.inspectFile(path)); QVERIFY(action->isEnabled());
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        canvas->setFocus(); QTest::keyClick(canvas, Qt::Key_M, Qt::ControlModifier | Qt::ShiftModifier);
        QVERIFY(action->isChecked()); QVERIFY(canvas->measurementSnapEnabled());
        QTest::keyClick(canvas, Qt::Key_M, Qt::ControlModifier); QVERIFY(canvas->measurementMode());
        pick(*canvas, {100,100}); pick(*canvas, {400,500});
        const auto output = window.findChild<QPlainTextEdit*>(QStringLiteral("measureText"))->toPlainText();
        QVERIFY(output.contains(QStringLiteral("500.00 mil")));
        QVERIFY(output.contains(QStringLiteral("模型几何捕捉（源文件行 2）")));
        canvas->setFocus(); QTest::keyClick(canvas, Qt::Key_I);
        auto* menu = window.findChild<QMenu*>(QStringLiteral("menu.I")); QTRY_VERIFY(menu->isVisible());
        QTest::keyClick(menu, Qt::Key_E); QTRY_VERIFY(!action->isChecked());
        QVERIFY(!canvas->measurementSnapEnabled()); QVERIFY(canvas->measurement()->startAnchor);
        QLineEdit edit(&window); edit.setGeometry(100,180,220,32); edit.show(); edit.setFocus();
        QTest::keyClick(&edit, Qt::Key_M, Qt::ControlModifier | Qt::ShiftModifier);
        QVERIFY(!canvas->measurementSnapEnabled());
        window.findChild<QAction*>(QStringLiteral("file.close"))->trigger();
        QVERIFY(!action->isEnabled()); QVERIFY(!action->isChecked());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.save"))->isEnabled());
        QVERIFY(input.open(QIODevice::ReadOnly)); QCOMPARE(input.readAll(), bytes);
    }
};
QTEST_MAIN(EndpointSnapTests)
#include "EndpointSnapTests.moc"
