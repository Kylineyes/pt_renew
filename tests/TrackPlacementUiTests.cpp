#include "application/CommandCatalog.h"
#include "ui/BoardCanvas.h"
#include "ui/MainWindow.h"
#include <QAction>
#include <QApplication>
#include <QDialog>
#include <QDockWidget>
#include <QFile>
#include <QLabel>
#include <QLineEdit>
#include <QMenu>
#include <QMouseEvent>
#include <QPushButton>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QtTest/QTest>
#include <limits>

namespace {
QAction* action(pt::MainWindow& window, const char* id) {
    return window.findChild<QAction*>(QString::fromLatin1(id));
}
bool writeBoard(const QString& path) {
    QFile file(path);
    const QByteArray bytes("PCB FILE 4\nFT\n0 0 1000 1000 10 1\nFT\n0 1000 1000 0 12 6\nENDPCB\n");
    return file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size();
}
void exactClick(pt::BoardCanvas* canvas, QPointF point) {
    // 保留浮点屏幕坐标，验证画布取点本身不会经过 QPoint 取整。
    const auto screen = canvas->boardToScreen(point);
    QMouseEvent event(QEvent::MouseButtonPress, screen, canvas->mapToGlobal(screen),
                      Qt::LeftButton, Qt::LeftButton, Qt::NoModifier);
    QApplication::sendEvent(canvas, &event);
}
}

class TrackPlacementUiTests final : public QObject {
    Q_OBJECT
private:
    QTemporaryDir m_dir;
    QString m_path;
    static void expose(pt::MainWindow& window) {
        window.show(); window.activateWindow();
        QVERIFY(QTest::qWaitForWindowExposed(&window));
        QVERIFY(QTest::qWaitForWindowActive(&window));
    }
    static void idle(pt::MainWindow& window) {
        QCOMPARE(window.trackPlacement().state(), pt::TrackPlacementState::Idle);
        QVERIFY(!window.findChild<pt::BoardCanvas*>()->trackPlacementMode());
    }
private slots:
    void initTestCase() {
        QVERIFY(m_dir.isValid()); m_path = m_dir.filePath(QStringLiteral("input.pcb"));
        QVERIFY(writeBoard(m_path));
    }
    void capabilityGateKeepsProductEntryClosed() {
        QVERIFY(!pt::trackPlacementUserEntryAvailable());
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path)); expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        auto* place = action(window,"place.track");
        QVERIFY(!place->isEnabled()); QVERIFY(place->text().contains(QStringLiteral("未实现")));
        QCOMPARE(place->shortcutContext(), Qt::WidgetShortcut);
        QVERIFY(place->shortcuts().contains(QKeySequence(QStringLiteral("F3"))));
        QSignalSpy invoked(&window, &pt::MainWindow::commandInvoked);
        canvas->setFocus(); QTest::keyClick(canvas,Qt::Key_F3); idle(window);
        QTest::keyClick(canvas,Qt::Key_P);
        auto* menu = window.findChild<QMenu*>(QStringLiteral("menu.P"));
        QTRY_VERIFY(menu->isVisible()); QVERIFY(menu->actions().contains(place));
        QTest::keyClick(menu,Qt::Key_T); idle(window);
        QTest::keyClick(menu,Qt::Key_Escape);
        QCOMPARE(invoked.size(),0); QVERIFY(!window.editSession().dirty());
    }
    void previewCancelAndFailuresDoNotAllocateIdentityOrHistory() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path));
        const auto document = window.editSession().document(); const auto revision = window.editSession().revision();
        QString error;
        QVERIFY(!window.beginTrackPlacement(0,1,&error)); QVERIFY(!error.isEmpty());
        QVERIFY(!window.beginTrackPlacement(10,2,&error));
        QVERIFY(window.beginTrackPlacement(17,6,&error));
        QVERIFY(window.setTrackPlacementStart({100,200}));
        QVERIFY(window.previewTrackPlacementEnd({300,400}));
        QVERIFY(!window.beginTrackPlacement(-1,1,&error));
        QCOMPARE(window.trackPlacement().width(),17);
        QVERIFY(!window.previewTrackPlacementEnd({300.25,400},&error)); QVERIFY(!error.isEmpty());
        QCOMPARE(window.trackPlacement().previewEndPoint(),std::optional<QPointF>({300,400}));
        QVERIFY(!window.pickTrackPlacementPoint({100,200},&error));
        QCOMPARE(window.editSession().document(),document); QCOMPARE(window.editSession().revision(),revision);
        QVERIFY(!window.editSession().dirty()); QVERIFY(!window.editSession().canUndo());
        window.cancelTrackPlacement(); window.cancelTrackPlacement(); idle(window);
        QVERIFY(!window.commitTrackPlacement(&error)); QVERIFY(!error.isEmpty());
        QVERIFY(window.beginTrackPlacement(19,1)); QVERIFY(!window.commitTrackPlacement(&error));
        QCOMPARE(window.trackPlacement().state(),pt::TrackPlacementState::WaitingForStart);
        QVERIFY(window.pickTrackPlacementPoint({10,20})); QVERIFY(window.pickTrackPlacementPoint({30,40}));
        QCOMPARE(window.editSession().document()->tracks.last().identity,pt::TrackIdentity::created(1));
    }
    void exactCanvasPointsCommitPublishAndUndoRedo() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path)); expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        canvas->zoomIn(); canvas->centerOn({500,500});
        canvas->setMeasurementMode(true);
        QVERIFY(window.beginTrackPlacement(23,6)); QVERIFY(!canvas->measurementMode()); QVERIFY(!canvas->selection());
        QApplication::processEvents();
        const auto zoom = canvas->zoom(); const auto screen = canvas->boardToScreen({0,0});
        exactClick(canvas,{500,500});
        QCOMPARE(window.trackPlacement().startPoint(),std::optional<QPointF>({500,500}));
        const auto endScreen = canvas->boardToScreen({600,500});
        QMouseEvent move(QEvent::MouseMove,endScreen,canvas->mapToGlobal(endScreen),
                         Qt::NoButton,Qt::NoButton,Qt::NoModifier);
        QApplication::sendEvent(canvas,&move);
        QCOMPARE(window.trackPlacement().previewEndPoint(),std::optional<QPointF>({600,500}));
        QVERIFY(!window.editSession().dirty()); QCOMPARE(canvas->document()->tracks.size(),2);
        exactClick(canvas,{600,500}); idle(window);
        QCOMPARE(canvas->document(),window.editSession().document().get());
        QCOMPARE(canvas->document()->tracks.size(),3);
        const auto created = canvas->document()->tracks.last();
        QCOMPARE(created.start,QPointF(500,500)); QCOMPARE(created.end,QPointF(600,500));
        QCOMPARE(created.width,23.0); QCOMPARE(created.layer,6); QVERIFY(!created.extra);
        QCOMPARE(created.identity,pt::TrackIdentity::created(1)); QVERIFY(created.source.line <= 0);
        QVERIFY(window.editSession().dirty()); QVERIFY(!canvas->selection()); QVERIFY(!canvas->measurement());
        QCOMPARE(canvas->zoom(),zoom); QCOMPARE(canvas->boardToScreen({0,0}),screen);
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,2}));
        QVERIFY(action(window,"move.track")->isEnabled()); QVERIFY(action(window,"delete.track")->isEnabled());
        QVERIFY(window.moveSelectedTrack({1,2}));
        action(window,"edit.undo")->trigger();
        QVERIFY(window.beginTrackPlacement(1,1)); action(window,"edit.undo")->trigger(); idle(window);
        QCOMPARE(canvas->document()->tracks.size(),2); QVERIFY(!window.editSession().dirty());
        QVERIFY(window.beginTrackPlacement(1,1)); action(window,"edit.redo")->trigger(); idle(window);
        QCOMPARE(canvas->document()->tracks.last().identity,created.identity);
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,2})); QVERIFY(window.deleteSelectedTrack());
        QCOMPARE(canvas->document()->tracks.size(),2);
    }
    void fractionalCanvasClickExplainsAndIntegerPanelWorks() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path)); expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        QVERIFY(window.beginTrackPlacement(11,1)); exactClick(canvas,{500.5,500});
        QCOMPARE(window.trackPlacement().state(),pt::TrackPlacementState::WaitingForStart);
        QVERIFY(!window.editSession().dirty());
        auto* status = window.findChild<QLabel*>(QStringLiteral("trackPlacementStatus"));
        QVERIFY(status->text().contains(QStringLiteral("整数"))); QVERIFY(status->text().contains(QStringLiteral("没有网格捕捉或取整")));
        auto* x = window.findChild<QLineEdit*>(QStringLiteral("trackPointX"));
        auto* y = window.findChild<QLineEdit*>(QStringLiteral("trackPointY"));
        auto* pick = window.findChild<QPushButton*>(QStringLiteral("trackPointPick"));
        x->setText(QStringLiteral("1.5")); y->setText(QStringLiteral("2")); pick->click();
        QCOMPARE(window.trackPlacement().state(),pt::TrackPlacementState::WaitingForStart);
        x->setText(QStringLiteral("-50")); y->setText(QStringLiteral("75")); pick->click();
        QVERIFY(status->text().contains(QStringLiteral("(-50, 75)")));
        x->setText(QStringLiteral("100")); y->setText(QStringLiteral("-200")); pick->click();
        QVERIFY(status->text().contains(QStringLiteral("(100, -200)")));
        QVERIFY(!window.editSession().dirty());
        window.findChild<QPushButton*>(QStringLiteral("trackPlacementCommit"))->click(); idle(window);
        QCOMPARE(canvas->document()->tracks.last().start,QPointF(-50,75));
        QCOMPARE(canvas->document()->tracks.last().end,QPointF(100,-200));
    }
    void canvasMenuAndButtonCancelShareState() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path)); expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        QVERIFY(window.beginTrackPlacement(10,1)); QVERIFY(window.setTrackPlacementStart({10,10}));
        QTest::keyClick(canvas,Qt::Key_Escape); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1));
        QTest::keyClick(canvas,Qt::Key_P);
        auto* menu = window.findChild<QMenu*>(QStringLiteral("menu.P")); QTRY_VERIFY(menu->isVisible());
        QTest::keyClick(menu,Qt::Key_Escape); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1)); action(window,"selection.clear")->trigger(); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1)); window.findChild<QPushButton*>(QStringLiteral("trackPlacementCancel"))->click(); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1)); action(window,"edit.undo")->trigger(); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1)); action(window,"edit.redo")->trigger(); idle(window);
        QVERIFY(!window.editSession().dirty()); QVERIFY(!window.editSession().canUndo());
    }
    void modalLayerDocumentAndMeasurementCancel() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path)); expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        QVERIFY(window.beginTrackPlacement(10,1)); canvas->setLayerVisible(6,false);
        QCOMPARE(window.trackPlacement().state(),pt::TrackPlacementState::WaitingForStart);
        canvas->setLayerVisible(1,false); idle(window); canvas->setLayerVisible(1,true);
        QVERIFY(window.beginTrackPlacement(10,1));
        QDialog dialog(&window); dialog.setWindowModality(Qt::WindowModal); dialog.show();
        idle(window); dialog.hide();
        QVERIFY(window.beginTrackPlacement(10,1)); canvas->setMeasurementMode(true); idle(window); QVERIFY(canvas->measurementMode());
        QVERIFY(window.beginTrackPlacement(10,1)); QVERIFY(!canvas->measurementMode());
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1)); QVERIFY(!window.inspectFile(m_dir.filePath(QStringLiteral("missing.pcb")))); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1)); QVERIFY(window.inspectFile(m_path)); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1)); canvas->setDocument(window.editSession().original()); idle(window);
        QVERIFY(!window.beginTrackPlacement(10,1));
        QVERIFY(window.inspectFile(m_path)); QVERIFY(window.beginTrackPlacement(10,1));
        window.findChild<QDockWidget*>(QStringLiteral("trackPlacementDock"))->hide(); idle(window);
        QVERIFY(window.beginTrackPlacement(10,1));
        QSignalSpy loaded(&window,&pt::MainWindow::boardLoadFinished);
        window.requestOpenFile(m_path); idle(window); QTRY_COMPARE(loaded.size(),1);
        QVERIFY(window.beginTrackPlacement(10,1)); action(window,"file.close")->trigger(); idle(window);
        QVERIFY(!window.editSession().document());
    }
    void modalCancellationPreservesExistingSelection() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path)); expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        const auto selection = canvas->selection();
        QDialog dialog(&window); dialog.setWindowModality(Qt::WindowModal); dialog.show();
        QCOMPARE(canvas->selection(),selection);
        dialog.hide();
        QVERIFY(window.beginTrackPlacement(10,1));
        dialog.show(); idle(window);
        QVERIFY(!window.editSession().dirty());
    }
    void idleCanvasEscapePropagatesToDialog() {
        QDialog dialog; pt::BoardCanvas canvas(&dialog);
        dialog.resize(800,600); canvas.resize(800,600); dialog.show(); dialog.activateWindow();
        QVERIFY(QTest::qWaitForWindowActive(&dialog)); canvas.setFocus();
        QTest::keyClick(&canvas,Qt::Key_Escape);
        QTRY_VERIFY(!dialog.isVisible());
    }
    void backendFailurePreservesPreviewAndHistory() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path));
        // 构造后端不能编辑的模型，覆盖控制器拒绝提交后保留预览的主窗分支。
        auto malformed = std::make_shared<pt::BoardDocument>(*window.editSession().original());
        malformed->tracks[0].identity = {};
        auto& edits = const_cast<pt::BoardEditSession&>(window.editSession());
        edits.reset(malformed);
        auto* canvas = window.findChild<pt::BoardCanvas*>(); canvas->setDocument(edits.document());
        const auto document = edits.document(); const auto revision = edits.revision();
        QVERIFY(window.beginTrackPlacement(10,1)); QVERIFY(window.setTrackPlacementStart({10,10}));
        QVERIFY(window.previewTrackPlacementEnd({20,20}));
        QString error; QVERIFY(!window.commitTrackPlacement(&error)); QVERIFY(!error.isEmpty());
        QCOMPARE(window.trackPlacement().state(),pt::TrackPlacementState::WaitingForEnd);
        QCOMPARE(window.trackPlacement().previewEndPoint(),std::optional<QPointF>({20,20}));
        QCOMPARE(edits.document(),document); QCOMPARE(edits.revision(),revision);
        QVERIFY(!edits.dirty()); QVERIFY(!edits.canUndo()); QVERIFY(canvas->trackPlacementMode());
    }
    void staleRevisionFailsBeforeCommit() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path));
        QVERIFY(window.beginTrackPlacement(10,1)); QVERIFY(window.setTrackPlacementStart({10,10}));
        QVERIFY(window.previewTrackPlacementEnd({20,20}));
        // 模拟另一消费者修改会话，验证主窗不能用旧预览提交到新修订。
        auto& edits = const_cast<pt::BoardEditSession&>(window.editSession());
        QVERIFY(edits.moveTrack({pt::PrimitiveKind::Track,0},edits.revision(),{1,0}));
        QString error; QVERIFY(!window.commitTrackPlacement(&error)); QVERIFY(!error.isEmpty()); idle(window);
        QCOMPARE(edits.document()->tracks.size(),2);
    }
    void textInputKeepsF3LettersAndUndo() {
        pt::MainWindow window; QVERIFY(window.inspectFile(m_path)); expose(window);
        QVERIFY(window.beginTrackPlacement(10,1));
        QLineEdit edit(&window); edit.setGeometry(100,180,240,30); edit.show(); edit.raise(); edit.setFocus();
        QTRY_COMPARE(QApplication::focusWidget(),&edit);
        QSignalSpy invoked(&window,&pt::MainWindow::commandInvoked);
        // 即使 QAction 将来启用，画布 WidgetShortcut 也不能抢文本输入。
        action(window,"place.track")->setEnabled(true);
        QTest::keyClick(&edit,Qt::Key_F3); QTest::keyClicks(&edit,"pt");
        QCOMPARE(edit.text(),QStringLiteral("pt")); QVERIFY(!QApplication::activePopupWidget());
        QTest::keyClick(&edit,Qt::Key_Z,Qt::ControlModifier);
        QVERIFY(!window.editSession().dirty()); QCOMPARE(invoked.size(),0);
        QCOMPARE(window.trackPlacement().state(),pt::TrackPlacementState::WaitingForStart);
    }
};
QTEST_MAIN(TrackPlacementUiTests)
#include "TrackPlacementUiTests.moc"
