#include "application/BoardEditSession.h"
#include "io/LegacyPcbReader.h"
#include "ui/BoardCanvas.h"
#include "ui/MainWindow.h"
#include "ui/NetlistBrowser.h"
#include <QAction>
#include <QApplication>
#include <QCryptographicHash>
#include <QDialog>
#include <QDialogButtonBox>
#include <QFile>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QMenu>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSignalSpy>
#include <QScopeGuard>
#include <QTemporaryDir>
#include <QTimer>
#include <QtTest/QTest>
#include <limits>

namespace {
QByteArray boardBytes() {
    return "PCB FILE 4\nFT\n100 100 400 500 10 1\nFT\n600 100 900 100 12 6 42\n"
        "COMP\nU1\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 2\n"
        "CT\n0 0 100 0 10 1\nCP\n100 100 60 60 1 20 1 13\n1\n"
        "CP\n400 500 60 60 1 20 1 13\n2\nENDCOMP\nENDPCB\n";
}
QByteArray netBytes() { return "[\nU1\nDIP\nValue\n\n\n\n]\n(\nGND\nU1-1\nU1-2\n)\n"; }
bool writeInput(const QString& path, const QByteArray& bytes) {
    QFile file(path); return file.open(QIODevice::WriteOnly) && file.write(bytes)==bytes.size();
}
QAction* action(pt::MainWindow& window, const char* id) { return window.findChild<QAction*>(QString::fromLatin1(id)); }
void answerDiscard(bool discard) {
    auto* timer = new QTimer(qApp); timer->setInterval(1);
    QObject::connect(timer, &QTimer::timeout, qApp, [discard,timer] {
        auto* box = qobject_cast<QMessageBox*>(QApplication::activeModalWidget());
        if (!box) return;
        timer->stop(); timer->deleteLater();
        auto guard=qScopeGuard([box] { if (box->isVisible()) box->reject(); });
        QCOMPARE(box->objectName(), QStringLiteral("discardChangesDialog"));
        QCOMPARE(box->buttons().size(), 2);
        for (auto* button : box->buttons()) {
            const auto role = box->buttonRole(button);
            if (role == (discard ? QMessageBox::DestructiveRole : QMessageBox::RejectRole)) { button->click(); return; }
        }
        QFAIL("没有找到放弃或取消按钮");
    });
    QTimer::singleShot(5000,timer,[timer] {
        if (timer->isActive()) { timer->stop(); timer->deleteLater(); QFAIL("等待放弃确认框超时"); }
    });
    timer->start();
}
}

class EditingTests final : public QObject {
    Q_OBJECT
private slots:
    void historyRestoresOrderPropertiesAndOriginal() {
        const auto input = pt::LegacyPcbReader::parse(boardBytes()); QVERIFY(input.succeeded());
        pt::BoardEditSession session; session.reset(input.document);
        const auto original = session.original();
        const auto third = original->tracks[2];
        QVERIFY(session.moveTrack({pt::PrimitiveKind::Track,0},session.revision(),{50,-25}));
        QCOMPARE(session.document()->tracks[0].start,QPointF(150,75));
        QVERIFY(session.deleteTrack({pt::PrimitiveKind::Track,1},session.revision()));
        QCOMPARE(session.document()->tracks.size(),2);
        QCOMPARE(session.document()->tracks[1].source.component,0);
        QVERIFY(session.dirty());
        QVERIFY(session.undo());
        QCOMPARE(session.document()->tracks[1].extra,std::optional<int>(42));
        QCOMPARE(session.document()->tracks[1].source.line,original->tracks[1].source.line);
        QCOMPARE(session.document()->tracks[2].start,third.start);
        QCOMPARE(session.document()->tracks[2].source.component,third.source.component);
        QVERIFY(session.undo()); QVERIFY(!session.dirty()); QVERIFY(!session.canUndo());
        QCOMPARE(session.document()->tracks[0].start,QPointF(100,100));
        QVERIFY(session.redo()); QVERIFY(session.redo()); QVERIFY(!session.canRedo());
        QCOMPARE(session.document()->tracks.size(),2);
        QCOMPARE(original->tracks.size(),3); QCOMPARE(original->tracks[0].start,QPointF(100,100));
        QCOMPARE(original->tracks[1].extra,std::optional<int>(42));
        QCOMPARE(session.document()->recordCounts,original->recordCounts);
        QCOMPARE(session.document()->sha256,original->sha256);
        QCOMPARE(session.document()->pads.constData(),original->pads.constData());
        QVERIFY(session.undo());
        QVERIFY(session.moveTrack({pt::PrimitiveKind::Track,1},session.revision(),{-5,15}));
        QVERIFY(!session.canRedo());
        while (session.undo()) {}
        QVERIFY(!session.dirty());
        QCOMPARE(session.document()->tracks[1].end,original->tracks[1].end);
    }

    void rejectsForeignScopeAndStaleIdentifiers() {
        const auto input=pt::LegacyPcbReader::parse(boardBytes());
        pt::BoardEditSession session; session.reset(input.document);
        for (const auto id : {pt::PrimitiveId{pt::PrimitiveKind::Track,2}, {pt::PrimitiveKind::Pad,0},
                 {pt::PrimitiveKind::Track,-1}, {pt::PrimitiveKind::Track,3}}) {
            QVERIFY(!session.moveTrack(id,session.revision(),{1,1}));
            QVERIFY(!session.deleteTrack(id,session.revision()));
        }
        const auto revision=session.revision();
        QVERIFY(session.deleteTrack({pt::PrimitiveKind::Track,0},revision));
        QVERIFY(!session.deleteTrack({pt::PrimitiveKind::Track,0},revision));
        QVERIFY(!session.moveTrack({pt::PrimitiveKind::Track,0},revision,{1,1}));
        QCOMPARE(session.document()->tracks[0].extra,std::optional<int>(42));
        auto library=std::make_shared<pt::BoardDocument>(*input.document);
        library->sourceContext=QStringLiteral("LIB 独立预览"); session.reset(library);
        QVERIFY(!session.deleteTrack({pt::PrimitiveKind::Track,0},session.revision()));
        session.reset(); QVERIFY(!session.moveTrack({pt::PrimitiveKind::Track,0},session.revision(),{1,1}));
    }

    void invalidOrZeroMovementHasNoHistory_data() {
        QTest::addColumn<QPointF>("delta");
        QTest::newRow("zero")<<QPointF();
        QTest::newRow("fraction")<<QPointF(0.5,0);
        QTest::newRow("nan")<<QPointF(std::numeric_limits<qreal>::quiet_NaN(),0);
        QTest::newRow("infinity")<<QPointF(0,std::numeric_limits<qreal>::infinity());
        QTest::newRow("delta-limit")<<QPointF(2000001,0);
        QTest::newRow("endpoint-limit")<<QPointF(999601,0);
        QTest::newRow("negative-limit")<<QPointF(-1000101,0);
    }
    void invalidOrZeroMovementHasNoHistory() {
        QFETCH(QPointF,delta);
        pt::BoardEditSession session; session.reset(pt::LegacyPcbReader::parse(boardBytes()).document);
        const auto current=session.document(); const auto revision=session.revision();
        QVERIFY(!session.moveTrack({pt::PrimitiveKind::Track,0},revision,delta));
        QCOMPARE(session.document(),current); QCOMPARE(session.revision(),revision);
        QVERIFY(!session.dirty()); QVERIFY(!session.canUndo()); QVERIFY(!session.canRedo());
    }

    void boundaryCoordinatesAndLargeBoardHistory() {
        auto board=std::make_shared<pt::BoardDocument>();
        board->tracks.fill({{0,0},{10,10},10,1},200000);
        pt::BoardEditSession session; session.reset(board);
        QVERIFY(session.moveTrack({pt::PrimitiveKind::Track,0},session.revision(),{999990,-1000000}));
        QCOMPARE(session.document()->tracks[0].end,QPointF(1000000,-999990));
        std::weak_ptr<const pt::BoardDocument> expired=session.document();
        QVERIFY(session.undo()); QVERIFY(expired.expired());
        for (int i=0;i<16;++i) {
            expired=session.document();
            QVERIFY(session.moveTrack({pt::PrimitiveKind::Track,0},session.revision(),{1,0}));
            QVERIFY(expired.expired());
        }
        for (int i=0;i<16;++i) QVERIFY(session.undo());
        QVERIFY(!session.dirty()); QCOMPARE(board->tracks[0].start,QPointF());
        session.reset(board); QVERIFY(!session.canUndo()); QVERIFY(!session.canRedo());
    }

    void onlyVisibleSelectedFreeTracksAreEditable() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("board.pcb")); QVERIFY(writeInput(path,boardBytes()));
        pt::MainWindow window; auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(!action(window,"move.track")->isEnabled()); QVERIFY(!window.deleteSelectedTrack());
        QVERIFY(window.inspectFile(path));
        QVERIFY(!action(window,"move.track")->isEnabled());
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,2}));
        QVERIFY(!action(window,"move.track")->isEnabled()); QVERIFY(!window.moveSelectedTrack({10,0}));
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Pad,0})); QVERIFY(!window.deleteSelectedTrack());
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); QVERIFY(action(window,"move.track")->isEnabled());
        canvas->setLayerVisible(1,false); QVERIFY(!action(window,"delete.track")->isEnabled());
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        QVERIFY(!window.deleteSelectedTrack()); QVERIFY(!action(window,"move.track")->isEnabled());
        canvas->setLayerVisible(1,true); QVERIFY(action(window,"move.track")->isEnabled());
        QVERIFY(window.moveSelectedTrack({20,30})); QVERIFY(!canvas->selection());
        QVERIFY(!window.deleteSelectedTrack());
        QVERIFY(!action(window,"file.save")->isEnabled()); QVERIFY(!action(window,"file.save_as")->isEnabled());
        QFile file(path); QVERIFY(file.open(QIODevice::ReadOnly)); QCOMPARE(file.readAll(),boardBytes());
        QCOMPARE(window.editSession().original()->sha256,QString::fromLatin1(QCryptographicHash::hash(boardBytes(),QCryptographicHash::Sha256).toHex()));
        QVERIFY(window.windowTitle().contains(QStringLiteral("已修改")));
        action(window,"edit.undo")->trigger(); QVERIFY(!window.editSession().dirty());
        QVERIFY(!window.windowTitle().contains(QStringLiteral("已修改")));
    }

    void moveDialogCancelsValidatesAndProtectsTextFocus() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("board.pcb")); QVERIFY(writeInput(path,boardBytes()));
        pt::MainWindow window; window.show(); QVERIFY(QTest::qWaitForWindowExposed(&window));
        QVERIFY(window.inspectFile(path)); auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        const auto revision=window.editSession().revision();
        QTimer::singleShot(0,&window,[&] {
            auto* dialog=window.findChild<QDialog*>(QStringLiteral("moveTrackDialog")); QVERIFY(dialog);
            dialog->activateWindow(); QVERIFY(QTest::qWaitForWindowActive(dialog));
            auto guard=qScopeGuard([dialog] { if (dialog->isVisible()) dialog->reject(); });
            auto* dx=dialog->findChild<QLineEdit*>(QStringLiteral("moveDeltaX"));
            dx->setText(QStringLiteral("50")); dx->setFocus();
            QTRY_COMPARE(QApplication::focusWidget(),dx);
            QTest::keyClick(dx,Qt::Key_Escape);
        });
        action(window,"move.track")->trigger();
        QCOMPARE(window.editSession().revision(),revision); QVERIFY(!window.editSession().dirty()); QVERIFY(canvas->selection());
        QTimer::singleShot(0,&window,[&] {
            auto* dialog=window.findChild<QDialog*>(QStringLiteral("moveTrackDialog")); QVERIFY(dialog);
            dialog->activateWindow(); QVERIFY(QTest::qWaitForWindowActive(dialog));
            auto guard=qScopeGuard([dialog] { if (dialog->isVisible()) dialog->reject(); });
            auto* dx=dialog->findChild<QLineEdit*>(QStringLiteral("moveDeltaX"));
            dx->setFocus(); QTRY_COMPARE(QApplication::focusWidget(),dx);
            auto* buttons=dialog->findChild<QDialogButtonBox*>();
            for (const auto& invalid : {QStringLiteral("1.5"),QStringLiteral("nan"),QStringLiteral("inf"),QStringLiteral("2000001"),QStringLiteral("999999")}) {
                dx->setText(invalid); buttons->button(QDialogButtonBox::Ok)->click();
                QVERIFY(dialog->isVisible()); QCOMPARE(window.editSession().revision(),revision);
            }
            dx->setText(QStringLiteral("120")); dx->setFocus(); dx->selectAll();
            QTest::keyClick(dx,Qt::Key_Delete); QCOMPARE(dx->text(),QString());
            QTest::keyClicks(dx,"25"); QTest::keyClick(dx,Qt::Key_Z,Qt::ControlModifier);
            QCOMPARE(window.editSession().revision(),revision);
            dx->setText(QStringLiteral("0")); buttons->button(QDialogButtonBox::Ok)->click();
        });
        action(window,"move.track")->trigger();
        QCOMPARE(window.editSession().revision(),revision); QVERIFY(!window.editSession().canUndo());
        QTimer::singleShot(0,&window,[&] {
            auto* dialog=window.findChild<QDialog*>(QStringLiteral("moveTrackDialog")); QVERIFY(dialog);
            auto guard=qScopeGuard([dialog] { if (dialog->isVisible()) dialog->reject(); });
            dialog->findChild<QLineEdit*>(QStringLiteral("moveDeltaX"))->setText(QStringLiteral("25"));
            dialog->findChild<QLineEdit*>(QStringLiteral("moveDeltaY"))->setText(QStringLiteral("-50"));
            dialog->findChild<QDialogButtonBox*>()->button(QDialogButtonBox::Ok)->click();
        });
        action(window,"move.track")->trigger();
        QCOMPARE(canvas->document()->tracks[0].start,QPointF(125,50));
        action(window,"edit.undo")->trigger(); QVERIFY(!window.editSession().dirty());
    }

    void canvasShortcutsAndLegacyMenusShareHistoryWithoutStealingText() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("board.pcb")); QVERIFY(writeInput(path,boardBytes()));
        pt::MainWindow window; window.show(); window.activateWindow(); QVERIFY(QTest::qWaitForWindowActive(&window));
        QVERIFY(window.inspectFile(path)); auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); canvas->setFocus();
        QTRY_COMPARE(QApplication::focusWidget(),canvas);
        QTest::keyClick(canvas,Qt::Key_Delete); QCOMPARE(canvas->document()->tracks.size(),2);
        QTest::keyClick(canvas,Qt::Key_Z,Qt::ControlModifier); QCOMPARE(canvas->document()->tracks.size(),3); QVERIFY(!window.editSession().dirty());
        QTest::keyClick(canvas,Qt::Key_Y,Qt::ControlModifier); QCOMPARE(canvas->document()->tracks.size(),2);
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        QLineEdit edit(&window); edit.setGeometry(100,180,240,30); edit.show(); edit.raise(); edit.setFocus();
        edit.setText(QStringLiteral("123")); edit.selectAll();
        QTest::keyClick(&edit,Qt::Key_Delete); QCOMPARE(edit.text(),QString());
        QTest::keyClicks(&edit,"abc"); QTest::keyClick(&edit,Qt::Key_Z,Qt::ControlModifier);
        QTest::keyClick(&edit,Qt::Key_Y,Qt::ControlModifier); QCOMPARE(edit.text(),QStringLiteral("abc"));
        QCOMPARE(canvas->document()->tracks.size(),2);
        canvas->setFocus(); QTest::keyClick(canvas,Qt::Key_D);
        auto* menu=window.findChild<QMenu*>(QStringLiteral("menu.D")); QTRY_VERIFY(menu->isVisible());
        QTest::keyClick(menu,Qt::Key_T); QTRY_COMPARE(canvas->document()->tracks.size(),1);
        action(window,"edit.undo")->trigger(); action(window,"edit.undo")->trigger();
        QVERIFY(!window.editSession().dirty());
    }

    void failedOpenAndCancelledReplacementsPreserveHistory_data() {
        QTest::addColumn<bool>("asynchronous");
        QTest::newRow("direct")<<false; QTest::newRow("background")<<true;
    }
    void failedOpenAndCancelledReplacementsPreserveHistory() {
        QFETCH(bool,asynchronous);
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("first.pcb")); QVERIFY(writeInput(path,boardBytes()));
        const auto other=dir.filePath(QStringLiteral("other.pcb")); QVERIFY(writeInput(other,"PCB FILE 4\nENDPCB\n"));
        pt::MainWindow window; QVERIFY(window.inspectFile(path)); auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); QVERIFY(window.moveSelectedTrack({25,30}));
        const auto edited=window.editSession().document(); const auto revision=window.editSession().revision();
        QSignalSpy loaded(&window,&pt::MainWindow::boardLoadFinished);
        if (asynchronous) {
            window.requestOpenFile(dir.filePath(QStringLiteral("missing.pcb"))); QTRY_COMPARE(loaded.size(),1);
            QVERIFY(!loaded.at(0).at(0).toBool());
        } else QVERIFY(!window.inspectFile(dir.filePath(QStringLiteral("missing.pcb"))));
        QCOMPARE(window.editSession().document(),edited); QVERIFY(window.editSession().canUndo());
        answerDiscard(false);
        if (asynchronous) { window.requestOpenFile(other); QTRY_COMPARE(loaded.size(),2); QVERIFY(!loaded.at(1).at(0).toBool()); }
        else QVERIFY(!window.inspectFile(other));
        QCOMPARE(window.editSession().document(),edited); QCOMPARE(window.editSession().revision(),revision);
        QVERIFY(window.windowTitle().contains(QStringLiteral("first.pcb")));
        answerDiscard(true);
        if (asynchronous) { window.requestOpenFile(other); QTRY_COMPARE(loaded.size(),3); QVERIFY(loaded.at(2).at(0).toBool()); }
        else QVERIFY(window.inspectFile(other));
        QCOMPARE(canvas->document()->tracks.size(),0); QVERIFY(!window.editSession().dirty());
        QVERIFY(!window.editSession().canUndo()); QVERIFY(!window.editSession().canRedo());
    }

    void closeAndSystemCloseCancellationKeepsWorkAndRedo() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("board.pcb")); QVERIFY(writeInput(path,boardBytes()));
        pt::MainWindow window; window.show(); QVERIFY(QTest::qWaitForWindowExposed(&window)); QVERIFY(window.inspectFile(path));
        auto* canvas=window.findChild<pt::BoardCanvas*>(); QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        QVERIFY(window.moveSelectedTrack({10,20})); QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,1}));
        QVERIFY(window.deleteSelectedTrack()); action(window,"edit.undo")->trigger();
        const auto edited=window.editSession().document(); QVERIFY(window.editSession().canRedo());
        answerDiscard(false); action(window,"file.close")->trigger();
        QCOMPARE(window.editSession().document(),edited); QVERIFY(window.editSession().canRedo());
        answerDiscard(false); QVERIFY(!window.close()); QVERIFY(window.isVisible());
        QCOMPARE(window.editSession().document(),edited); QVERIFY(window.editSession().canRedo());
        answerDiscard(true); action(window,"file.close")->trigger();
        QVERIFY(!canvas->document()); QVERIFY(!window.editSession().canUndo()); QVERIFY(!window.editSession().canRedo());
        QVERIFY(window.inspectFile(path)); QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        QVERIFY(window.deleteSelectedTrack()); answerDiscard(true); QVERIFY(window.close());
    }

    void editInvalidatesSelectionMeasurementSnapAndPreservesView() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("board.pcb")); QVERIFY(writeInput(path,boardBytes()));
        pt::MainWindow window; window.show(); QVERIFY(QTest::qWaitForWindowExposed(&window)); QVERIFY(window.inspectFile(path));
        auto* canvas=window.findChild<pt::BoardCanvas*>();
        canvas->zoomIn(); canvas->centerOn({200,300}); canvas->setLayerVisible(6,false);
        canvas->setMeasurementSnapEnabled(true); canvas->setMeasurementMode(true);
        QTest::mouseClick(canvas,Qt::LeftButton,Qt::NoModifier,canvas->boardToScreen({100,100}).toPoint());
        QTest::mouseClick(canvas,Qt::LeftButton,Qt::NoModifier,canvas->boardToScreen({400,500}).toPoint());
        QVERIFY(canvas->measurement()); QVERIFY(canvas->measurement()->startAnchor);
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        const auto screen=canvas->boardToScreen({100,100}); const auto zoom=canvas->zoom();
        QVERIFY(window.moveSelectedTrack({100,0}));
        QVERIFY(!canvas->selection()); QCOMPARE(canvas->overlapCount(),0);
        QVERIFY(!canvas->measurement()); QVERIFY(!canvas->measurementStart()); QVERIFY(!canvas->snapPreview());
        QCOMPARE(canvas->boardToScreen({100,100}),screen); QCOMPARE(canvas->zoom(),zoom); QVERIFY(!canvas->layerVisible(6));
        QVERIFY(canvas->measurementSnapEnabled()); canvas->setMeasurementMode(true);
        QTest::mouseClick(canvas,Qt::LeftButton,Qt::NoModifier,canvas->boardToScreen({200,100}).toPoint());
        QVERIFY(canvas->measurementStart()); QCOMPARE(*canvas->measurementStart(),QPointF(200,100));
        action(window,"edit.undo")->trigger(); QVERIFY(!canvas->measurementStart());
        QCOMPARE(canvas->boardToScreen({100,100}),screen); QVERIFY(!canvas->layerVisible(6));
        canvas->setMeasurementMode(true);
        QTest::mouseClick(canvas,Qt::LeftButton,Qt::NoModifier,canvas->boardToScreen({100,100}).toPoint());
        QCOMPARE(*canvas->measurementStart(),QPointF(100,100));
        action(window,"edit.redo")->trigger(); QVERIFY(!canvas->measurementStart());
        action(window,"edit.undo")->trigger();
    }

    void explicitResetFitsEditedGeometry() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("board.pcb")); QVERIFY(writeInput(path,boardBytes()));
        pt::MainWindow window; window.show(); QVERIFY(QTest::qWaitForWindowExposed(&window)); QVERIFY(window.inspectFile(path));
        auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        const auto originalScreen=canvas->boardToScreen({100,100});
        QVERIFY(window.moveSelectedTrack({10000,10000}));
        QCOMPARE(canvas->boardToScreen({100,100}),originalScreen);
        QVERIFY(!canvas->rect().contains(canvas->boardToScreen({10100,10100}).toPoint()));
        action(window,"view.reset")->trigger();
        QVERIFY(canvas->rect().contains(canvas->boardToScreen({10100,10100}).toPoint()));
        const auto center=canvas->document()->bounds().center();
        QVERIFY((canvas->boardToScreen(center)-QPointF(canvas->rect().center())).manhattanLength()<1);
        action(window,"edit.undo")->trigger(); action(window,"view.reset")->trigger();
        QVERIFY((canvas->boardToScreen(canvas->document()->bounds().center())-QPointF(canvas->rect().center())).manhattanLength()<1);
    }

    void pendingOpenProtectsEditsMadeDuringReadAndDropsClosedResults() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("board.pcb")); QVERIFY(writeInput(path,boardBytes()));
        const auto other=dir.filePath(QStringLiteral("empty.pcb")); QVERIFY(writeInput(other,"PCB FILE 4\nENDPCB\n"));
        pt::MainWindow window; QVERIFY(window.inspectFile(path)); auto* canvas=window.findChild<pt::BoardCanvas*>();
        QSignalSpy loaded(&window,&pt::MainWindow::boardLoadFinished);
        window.requestOpenFile(other);
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); QVERIFY(window.deleteSelectedTrack());
        const auto edited=window.editSession().document(); answerDiscard(false);
        QTRY_COMPARE(loaded.size(),1); QVERIFY(!loaded.at(0).at(0).toBool());
        QCOMPARE(window.editSession().document(),edited); QVERIFY(window.editSession().canUndo());
        window.requestOpenFile(other); answerDiscard(false); action(window,"file.close")->trigger();
        QTRY_VERIFY(action(window,"file.open")->isEnabled());
        QCOMPARE(loaded.size(),1); QCOMPARE(window.editSession().document(),edited); QVERIFY(window.editSession().canUndo());
        window.requestOpenFile(other); answerDiscard(true); action(window,"file.close")->trigger();
        QTRY_VERIFY(action(window,"file.open")->isEnabled());
        QCOMPARE(loaded.size(),1); QVERIFY(!canvas->document()); QVERIFY(!window.editSession().canUndo());
    }

    void newCopperConclusionFollowsDeleteAndUndo() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("supported.pcb"));
        auto bytes=boardBytes(); bytes.replace("12 6 42\n","12 6\n"); QVERIFY(writeInput(path,bytes));
        const auto netPath=dir.filePath(QStringLiteral("board.net")); QVERIFY(writeInput(netPath,netBytes()));
        pt::MainWindow window; QVERIFY(window.inspectFile(path));
        auto* canvas=window.findChild<pt::BoardCanvas*>(); auto* browser=window.findChild<pt::NetlistBrowser*>();
        QVERIFY(browser->loadFile(netPath)); auto* details=browser->findChild<QPlainTextEdit*>(QStringLiteral("netlistDetails"));
        QSignalSpy finished(browser,&pt::NetlistBrowser::copperAnalysisFinished);
        browser->runCopperAnalysis(); QTRY_COMPARE(finished.size(),1);
        QVERIFY(details->toPlainText().contains(QStringLiteral("支持模型内已连接")));
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); QVERIFY(window.deleteSelectedTrack());
        QVERIFY(!details->toPlainText().contains(QStringLiteral("支持模型内已连接")));
        browser->runCopperAnalysis(); QTRY_COMPARE(finished.size(),2);
        QVERIFY(details->toPlainText().contains(QStringLiteral("支持模型内仍分离")));
        action(window,"edit.undo")->trigger();
        QVERIFY(!details->toPlainText().contains(QStringLiteral("支持模型内仍分离")));
        browser->runCopperAnalysis(); QTRY_COMPARE(finished.size(),3);
        QVERIFY(details->toPlainText().contains(QStringLiteral("支持模型内已连接")));
    }

    void editRebuildsNetMappingAndRejectsLateCopperAndNetReads() {
        QTemporaryDir dir; const auto path=dir.filePath(QStringLiteral("board.pcb")); QVERIFY(writeInput(path,boardBytes()));
        const auto netPath=dir.filePath(QStringLiteral("board.net")); QVERIFY(writeInput(netPath,netBytes()));
        pt::MainWindow window; QVERIFY(window.inspectFile(path)); auto* canvas=window.findChild<pt::BoardCanvas*>();
        auto* browser=window.findChild<pt::NetlistBrowser*>(); QVERIFY(browser->loadFile(netPath));
        const auto net=browser->netlist(); QCOMPARE(browser->mapping().resolved,2);
        auto* details=browser->findChild<QPlainTextEdit*>(QStringLiteral("netlistDetails"));
        auto* issues=browser->findChild<QListWidget*>(QStringLiteral("copperCoverageIssues"));
        QSignalSpy finished(browser,&pt::NetlistBrowser::copperAnalysisFinished);
        browser->runCopperAnalysis(); QTRY_COMPARE(finished.size(),1);
        QVERIFY(details->toPlainText().contains(QStringLiteral("当前工作文档修订"))); QVERIFY(issues->count()>0);
        browser->runCopperAnalysis(); QVERIFY(browser->copperAnalysisRunning());
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); QVERIFY(window.deleteSelectedTrack());
        QCOMPARE(browser->netlist(),net); QCOMPARE(browser->mapping().resolved,2); QCOMPARE(issues->count(),0);
        QVERIFY(!details->toPlainText().contains(QStringLiteral("当前工作文档修订")));
        QTRY_VERIFY(!browser->copperAnalysisRunning()); QCOMPARE(finished.size(),1);
        QVERIFY(!details->toPlainText().contains(QStringLiteral("当前工作文档修订")));
        browser->runCopperAnalysis(); QTRY_COMPARE(finished.size(),2);
        QVERIFY(details->toPlainText().contains(QStringLiteral("当前工作文档修订：%1").arg(window.editSession().document()->workingRevision)));
        action(window,"edit.undo")->trigger(); QCOMPARE(browser->netlist(),net);
        QVERIFY(!details->toPlainText().contains(QStringLiteral("当前工作文档修订")));
        QSignalSpy read(browser,&pt::NetlistBrowser::netlistLoaded);
        browser->requestFile(netPath);
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); QVERIFY(window.deleteSelectedTrack());
        QTRY_VERIFY(browser->findChild<QPushButton*>(QStringLiteral("netlistOpen"))->isEnabled());
        QCOMPARE(read.size(),0); QCOMPARE(browser->netlist(),net);
        QVERIFY(browser->findChild<QLabel*>(QStringLiteral("netlistStatus"))->text().contains(QStringLiteral("结果已放弃")));
        action(window,"edit.undo")->trigger();
    }
};
QTEST_MAIN(EditingTests)
#include "EditingTests.moc"
