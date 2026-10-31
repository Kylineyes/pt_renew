#include "application/BoardEditSession.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbWriter.h"
#include "ui/BoardCanvas.h"
#include "ui/MainWindow.h"
#include <QAction>
#include <QApplication>
#include <QCryptographicHash>
#include <QDialogButtonBox>
#include <QDir>
#include <QFile>
#include <QFileDialog>
#include <QLineEdit>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QScopeGuard>
#include <QTemporaryDir>
#include <QTimer>
#include <QtTest/QTest>
#include <limits>

namespace {
QByteArray fixture() {
    return "PCB FILE 4\r\n\r\n FT \r\n\t+00100  100\t400 500  10\t1  +0042 \r\n"
        "FT\n600 100 900 100 12 6\n"
        "FP\r\n100 100 60 80 1 20 1 13\r\nPin\r\n"
        "FV\n300 400 40 20\nFA\n100 100 50 5 10 7\nFF\n30 40 10 20 6\n"
        "FS\n100 200 60 17 10 7\nOpaque \x82\n"
        "COMP\nU1\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 2\n"
        "CT\n0 0 100 0 10 1\nCP\n100 100 60 60 1 20 1 13\n1\nENDCOMP\n"
        "NETDEF\nGND\n[\nmetadata untouched\n]\n(\nU1-1\n)\nENDPCB\r\n\x1a \t\r\n";
}
bool write(const QString& path, const QByteArray& bytes) { QFile file(path); return file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size(); }
QByteArray read(const QString& path) { QFile file(path); if (!file.open(QIODevice::ReadOnly)) return {}; return file.readAll(); }
QAction* action(pt::MainWindow& window, const char* id) { return window.findChild<QAction*>(QString::fromLatin1(id)); }
void screenshot(QWidget& widget, const QString& name) {
    const auto directory = qEnvironmentVariable("PT_TEST_SCREENSHOT_DIR");
    if (directory.isEmpty()) return;
    QVERIFY(QDir().mkpath(directory));
    QVERIFY(widget.grab().save(QDir(directory).filePath(name)));
}
}

class WritingTests final : public QObject {
    Q_OBJECT
private slots:
    void untouchedBytesRoundTripExactly_data() {
        QTest::addColumn<QByteArray>("bytes");
        QTest::newRow("mixed-encoding-and-netdef") << fixture();
        QTest::newRow("empty-no-final-newline") << QByteArray("PCB FILE 4\nENDPCB");
        QTest::newRow("all-crlf") << QByteArray("PCB FILE 4\r\nFT\r\n0 0 10 10 1 1\r\nENDPCB\r\n");
    }
    void untouchedBytesRoundTripExactly() {
        QFETCH(QByteArray, bytes);
        const auto loaded = pt::LegacyPcbReader::parse(bytes); QVERIFY2(loaded.succeeded(), qPrintable(loaded.error));
        const auto result = pt::LegacyPcbWriter::prepare(*loaded.document, *loaded.document);
        QVERIFY2(result.succeeded(), qPrintable(result.error)); QCOMPARE(result.bytes, bytes);
    }
    void movementAndDeletionPreserveAllUnmodifiedBytes() {
        const auto original = pt::LegacyPcbReader::parse(fixture()).document; QVERIFY(original);
        pt::BoardEditSession session; session.reset(original);
        QVERIFY(session.moveTrack({pt::PrimitiveKind::Track, 0}, session.revision(), {50,-25}));
        QVERIFY(session.deleteTrack({pt::PrimitiveKind::Track, 1}, session.revision()));
        const auto result = pt::LegacyPcbWriter::prepare(*original, *session.document());
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        auto expected = fixture();
        expected.replace("\t+00100  100\t400 500  10\t1  +0042 \r\n", "\t150  75\t450 475  10\t1  +0042 \r\n");
        expected.replace("FT\n600 100 900 100 12 6\n", "");
        QCOMPARE(result.bytes, expected);
        const auto reopened = pt::LegacyPcbReader::parse(result.bytes); QVERIFY(reopened.succeeded());
        QCOMPARE(reopened.document->tracks.size(), 2);
        QCOMPARE(reopened.document->tracks[0].start, QPointF(150,75));
        QCOMPARE(reopened.document->tracks[0].extra, std::optional<int>(42));
        QCOMPARE(reopened.document->tracks[1].source.component, 0);
        QCOMPARE(reopened.document->embeddedNetlist->nets[0].metadata, original->embeddedNetlist->nets[0].metadata);
        QCOMPARE(original->sourceBytes, fixture());
        QVERIFY(session.undo()); QVERIFY(session.undo());
        QCOMPARE(pt::LegacyPcbWriter::prepare(*original,*session.document()).bytes, fixture());
    }
    void rejectsUnsupportedOrForgedEdits_data() {
        QTest::addColumn<QString>("mode");
        for (const auto* mode : {"shape", "width", "layer", "extra", "component-move", "component-delete", "source", "reorder", "duplicate", "new-track",
             "pad", "via", "arc", "fill", "text", "component", "netdef", "fraction", "nan", "limit", "bytes", "hash", "path", "counts", "library"})
            QTest::newRow(mode) << QString::fromLatin1(mode);
    }
    void rejectsUnsupportedOrForgedEdits() {
        QFETCH(QString, mode);
        const auto original = pt::LegacyPcbReader::parse(fixture()).document; QVERIFY(original);
        auto current = *original;
        if (mode=="shape") current.tracks[0].end += QPointF(1,0);
        if (mode=="width") ++current.tracks[0].width;
        if (mode=="layer") current.tracks[0].layer=6;
        if (mode=="extra") current.tracks[0].extra=11;
        if (mode=="component-move") { current.tracks[2].start+=QPointF(1,0); current.tracks[2].end+=QPointF(1,0); }
        if (mode=="component-delete") current.tracks.removeAt(2);
        if (mode=="source") ++current.tracks[0].source.byteOffset;
        if (mode=="reorder") current.tracks.swapItemsAt(0,1);
        if (mode=="duplicate") current.tracks.insert(0,current.tracks[0]);
        if (mode=="new-track") { auto track=current.tracks[0]; track.source.line=9999; current.tracks.append(track); }
        if (mode=="pad") ++current.pads[0].width;
        if (mode=="via") ++current.vias[0].diameter;
        if (mode=="arc") ++current.arcs[0].quadrants;
        if (mode=="fill") current.fills[0].rectangle.translate(1,0);
        if (mode=="text") current.texts[0].value=QStringLiteral("Changed");
        if (mode=="component") current.components[0].placement=9;
        if (mode=="netdef") { auto net=std::make_shared<pt::Netlist>(*current.embeddedNetlist); net->nets[0].metadata="changed"; current.embeddedNetlist=net; }
        if (mode=="fraction" || mode=="nan" || mode=="limit") {
            const auto x=mode=="fraction" ? 0.5 : mode=="nan" ? std::numeric_limits<qreal>::quiet_NaN() : 1000001.;
            current.tracks[0].start+=QPointF(x,0); current.tracks[0].end+=QPointF(x,0);
        }
        if (mode=="bytes") current.sourceBytes+=" ";
        if (mode=="hash") current.sha256="forged";
        if (mode=="path") current.filePath="foreign.pcb";
        if (mode=="counts") ++current.recordCounts["FT"];
        if (mode=="library") current.sourceContext=QStringLiteral("LIB 预览");
        const auto result=pt::LegacyPcbWriter::prepare(*original,current);
        QVERIFY2(!result.succeeded(),qPrintable(mode)); QVERIFY(!result.error.isEmpty());
    }
    void originalSnapshotMustMatchBytes() {
        const auto original=pt::LegacyPcbReader::parse(fixture()).document;
        auto forged=*original; forged.tracks[0].width=123;
        QVERIFY(!pt::LegacyPcbWriter::prepare(forged,forged).succeeded());
        forged=*original; forged.sourceBytes.clear();
        QVERIFY(!pt::LegacyPcbWriter::prepare(forged,forged).succeeded());
        forged=*original; auto net=std::make_shared<pt::Netlist>(*original->embeddedNetlist); net->nets[0].nodes[0].token="U1-2"; forged.embeddedNetlist=net;
        QVERIFY(!pt::LegacyPcbWriter::prepare(forged,forged).succeeded());
    }
    void newFilePublishesAndAllExistingFilesRemainUntouched() {
        QTemporaryDir directory; QVERIFY(directory.isValid());
        const auto input=directory.filePath(QStringLiteral("原件.pcb")); QVERIFY(write(input,fixture()));
        const auto original=pt::LegacyPcbReader::readFile(input).document; QVERIFY(original);
        pt::BoardEditSession session; session.reset(original);
        QVERIFY(session.deleteTrack({pt::PrimitiveKind::Track,0},session.revision()));
        const auto destination=directory.filePath(QStringLiteral("新工作副本.PCB"));
        const auto result=pt::LegacyPcbWriter::saveAs(destination,*original,*session.document());
        QVERIFY2(result.succeeded(),qPrintable(result.error)); QCOMPARE(read(destination),result.bytes);
        QCOMPARE(read(input),fixture());
        QVERIFY(pt::LegacyPcbReader::readFile(destination).succeeded());
        QVERIFY(!pt::LegacyPcbWriter::saveAs(destination,*original,*original).succeeded());
        QCOMPARE(read(destination),result.bytes);
        QVERIFY(!pt::LegacyPcbWriter::saveAs(input,*original,*session.document()).succeeded());
        QVERIFY(!pt::LegacyPcbWriter::saveAs(directory.path()+"/./原件.pcb",*original,*session.document()).succeeded());
        QCOMPARE(read(input),fixture());
        const auto unrelated=directory.filePath("existing.pcb"); QVERIFY(write(unrelated,"keep-me"));
        QVERIFY(!pt::LegacyPcbWriter::saveAs(unrelated,*original,*session.document()).succeeded()); QCOMPARE(read(unrelated),QByteArray("keep-me"));
        QVERIFY(!pt::LegacyPcbWriter::saveAs(directory.filePath("missing/output.pcb"),*original,*session.document()).succeeded());
        QVERIFY(!pt::LegacyPcbWriter::saveAs(directory.filePath("wrong.txt"),*original,*session.document()).succeeded());
        QVERIFY(!pt::LegacyPcbWriter::saveAs(directory.filePath("input.pcb:stream.pcb"),*original,*session.document()).succeeded());
        QVERIFY(!pt::LegacyPcbWriter::saveAs(directory.filePath("NUL.pcb"),*original,*session.document()).succeeded());
        QVERIFY(!pt::LegacyPcbWriter::saveAs(directory.filePath("COM1.pcb"),*original,*session.document()).succeeded());
        QCOMPARE(read(input),fixture());
        QVERIFY(!pt::LegacyPcbWriter::saveAs({},*original,*session.document()).succeeded());
        QVERIFY(QDir(directory.path()).entryList({".pt-renew-*"},QDir::Files|QDir::Hidden).isEmpty());
    }
    void failedPublishRemovesTemporaryAndPreservesInputs() {
        QTemporaryDir directory; const auto input=directory.filePath("input.pcb"); QVERIFY(write(input,fixture()));
        const auto original=pt::LegacyPcbReader::readFile(input).document; QVERIFY(original);
        const auto impossible=directory.filePath(QString(300,QLatin1Char('x'))+QStringLiteral(".pcb"));
        const auto result=pt::LegacyPcbWriter::saveAs(impossible,*original,*original);
        QVERIFY(!result.succeeded()); QVERIFY2(result.error.contains(QStringLiteral("无法发布新文件")),qPrintable(result.error));
        QCOMPARE(read(input),fixture());
        QCOMPARE(QDir(directory.path()).entryList(QDir::Files|QDir::Hidden|QDir::NoDotAndDotDot),QStringList{"input.pcb"});
    }
    void removedOriginalStillCannotBeWrittenThroughSaveAs() {
        QTemporaryDir directory; const auto input=directory.filePath("input.pcb"); QVERIFY(write(input,fixture()));
        const auto original=pt::LegacyPcbReader::readFile(input).document;
        QVERIFY(QFile::remove(input));
        QVERIFY(!pt::LegacyPcbWriter::saveAs(input,*original,*original).succeeded()); QVERIFY(!QFile::exists(input));
        const auto result=pt::LegacyPcbWriter::saveAs(directory.filePath("new.pcb"),*original,*original);
        QVERIFY2(result.succeeded(),qPrintable(result.error)); QCOMPARE(result.bytes,fixture());
    }
    void savedCheckpointSurvivesUndoRedoAndInvalidatesOnBranch() {
        pt::BoardEditSession session; session.reset(pt::LegacyPcbReader::parse(fixture()).document);
        QVERIFY(session.moveTrack({pt::PrimitiveKind::Track,0},session.revision(),{1,0}));
        session.markSaved(); QVERIFY(!session.dirty());
        QVERIFY(session.undo()); QVERIFY(session.dirty());
        QVERIFY(session.redo()); QVERIFY(!session.dirty());
        QVERIFY(session.undo());
        QVERIFY(session.moveTrack({pt::PrimitiveKind::Track,0},session.revision(),{2,0}));
        QVERIFY(session.dirty()); QVERIFY(!session.canRedo());
        QVERIFY(session.undo()); QVERIFY(session.dirty());
        session.markSaved(); QVERIFY(!session.dirty());
    }
    void windowSaveKeepsHistoryAndFailedSaveKeepsDirty() {
        QTemporaryDir directory; const auto input=directory.filePath("input.pcb"); QVERIFY(write(input,fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input)); auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); QVERIFY(window.moveSelectedTrack({50,-25}));
        const auto revision=window.editSession().revision(); QString error;
        QVERIFY(!window.saveAsFile(input,&error)); QVERIFY(!error.isEmpty()); QVERIFY(window.editSession().dirty());
        QCOMPARE(window.editSession().revision(),revision); QVERIFY(window.editSession().canUndo());
        const auto output=directory.filePath("edited.pcb"); QVERIFY2(window.saveAsFile(output,&error),qPrintable(error));
        QVERIFY(!window.editSession().dirty()); QCOMPARE(window.editSession().revision(),revision);
        action(window,"edit.undo")->trigger(); QVERIFY(window.editSession().dirty());
        action(window,"edit.redo")->trigger(); QVERIFY(!window.editSession().dirty());
        QCOMPARE(pt::LegacyPcbReader::readFile(output).document->tracks[0].start,QPointF(150,75));
        QCOMPARE(window.editSession().original()->filePath,input); QCOMPARE(read(input),fixture());
        QVERIFY(window.close());
    }
    void cancelledSaveDialogPreservesWorkingDocumentAndHistory() {
        QTemporaryDir directory; const auto input=directory.filePath("input.pcb"); QVERIFY(write(input,fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input));
        auto* canvas=window.findChild<pt::BoardCanvas*>(); QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        QVERIFY(window.moveSelectedTrack({1,0})); const auto current=window.editSession().document();
        bool cancelled=false;
        QTimer::singleShot(0,&window,[&] {
            auto* dialog=qobject_cast<QFileDialog*>(QApplication::activeModalWidget()); QVERIFY(dialog);
            cancelled=true; dialog->reject();
        });
        action(window,"file.save_as")->trigger();
        QVERIFY(cancelled); QCOMPARE(window.editSession().document(),current);
        QVERIFY(window.editSession().dirty()); QVERIFY(window.editSession().canUndo());
        QCOMPARE(QDir(directory.path()).entryList(QDir::Files),QStringList{"input.pcb"});
        action(window,"edit.undo")->trigger(); QVERIFY(!window.editSession().dirty());
    }
    void documentChangedDuringSaveDialogDoesNotWriteStaleRevision() {
        QTemporaryDir directory; const auto input=directory.filePath("input.pcb"), output=directory.filePath("stale.pcb");
        QVERIFY(write(input,fixture())); pt::MainWindow window; QVERIFY(window.inspectFile(input));
        auto* canvas=window.findChild<pt::BoardCanvas*>(); QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        bool changed=false, warned=false;
        auto* timer=new QTimer(&window); timer->setInterval(10);
        connect(timer,&QTimer::timeout,&window,[&] {
            if (auto* dialog=qobject_cast<QFileDialog*>(QApplication::activeModalWidget())) {
                if (changed) return;
                QVERIFY(window.moveSelectedTrack({1,0})); changed=true;
                dialog->selectFile(output);
                auto* buttons=dialog->findChild<QDialogButtonBox*>(); QVERIFY(buttons);
                QTest::mouseClick(buttons->button(QDialogButtonBox::Save),Qt::LeftButton);
            } else if (auto* box=qobject_cast<QMessageBox*>(QApplication::activeModalWidget())) {
                warned=true; timer->stop(); box->accept();
            }
        });
        QTimer::singleShot(5000,&window,[&] {
            if (!warned) { timer->stop(); if (auto* dialog=qobject_cast<QDialog*>(QApplication::activeModalWidget())) dialog->reject(); }
        });
        timer->start(); action(window,"file.save_as")->trigger();
        QVERIFY(changed); QVERIFY(warned); QVERIFY(!QFile::exists(output));
        QVERIFY(window.editSession().dirty()); QVERIFY(window.editSession().canUndo());
        QCOMPARE(read(input),fixture()); action(window,"edit.undo")->trigger(); QVERIFY(!window.editSession().dirty());
    }
    void menuSaveAsReopensEditedGeometry() {
        QTemporaryDir directory; const auto input=directory.filePath("source.pcb"); QVERIFY(write(input,fixture()));
        const auto output=directory.filePath("edited.pcb");
        pt::MainWindow window; window.show(); QVERIFY(QTest::qWaitForWindowExposed(&window));
        QVERIFY(window.inspectFile(input)); auto* canvas=window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        // 使用与用户相同的移动对话框，通过可见输入框提交坐标。
        QTimer::singleShot(0,&window,[&] {
            auto* dialog=window.findChild<QDialog*>("moveTrackDialog"); QVERIFY(dialog);
            auto* dx=dialog->findChild<QLineEdit*>("moveDeltaX"); auto* dy=dialog->findChild<QLineEdit*>("moveDeltaY");
            QVERIFY(dx); QVERIFY(dy); dx->setFocus(); dx->selectAll(); QTest::keyClicks(dx,"50");
            dy->setFocus(); dy->selectAll(); QTest::keyClicks(dy,"-25");
            auto* buttons=dialog->findChild<QDialogButtonBox*>(); QVERIFY(buttons);
            QTest::mouseClick(buttons->button(QDialogButtonBox::Ok),Qt::LeftButton);
        });
        action(window,"move.track")->trigger(); QVERIFY(window.editSession().dirty());
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); screenshot(window,"01-moved.png");
        bool accepted=false;
        auto* timer=new QTimer(&window); timer->setInterval(10);
        connect(timer,&QTimer::timeout,&window,[&] {
            auto* dialog=qobject_cast<QFileDialog*>(QApplication::activeModalWidget());
            if (!dialog) return;
            timer->stop(); dialog->selectFile(output); screenshot(*dialog,"02-save-dialog.png");
            auto* buttons=dialog->findChild<QDialogButtonBox*>(); QVERIFY(buttons);
            auto* button=buttons->button(QDialogButtonBox::Save); QVERIFY(button); accepted=true;
            QTest::mouseClick(button,Qt::LeftButton);
        });
        QTimer::singleShot(5000,&window,[&] { if (!accepted) { if (auto* dialog=qobject_cast<QDialog*>(QApplication::activeModalWidget())) dialog->reject(); } });
        timer->start();
        // 文件菜单和快捷键共用同一保存命令；等待移动框关闭后的窗口激活事件。
        window.activateWindow(); QVERIFY(QTest::qWaitForWindowActive(&window));
        canvas->setFocus(); QTRY_VERIFY(canvas->hasFocus());
        QTest::keyClick(canvas,Qt::Key_S,Qt::ControlModifier|Qt::ShiftModifier);
        QVERIFY(accepted); QVERIFY(QFile::exists(output)); QVERIFY(!window.editSession().dirty());
        screenshot(window,"03-saved.png");
        pt::MainWindow reopened; QVERIFY(reopened.inspectFile(output)); reopened.show();
        QVERIFY(QTest::qWaitForWindowExposed(&reopened));
        auto* reopenedCanvas=reopened.findChild<pt::BoardCanvas*>(); QVERIFY(reopenedCanvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        QCOMPARE(reopened.editSession().document()->tracks[0].start,QPointF(150,75));
        QCOMPARE(reopened.editSession().document()->tracks[0].end,QPointF(450,475));
        QVERIFY(!reopened.editSession().dirty()); screenshot(reopened,"04-reopened.png");
        QCOMPARE(read(input),fixture());
        const auto evidence=qEnvironmentVariable("PT_TEST_SCREENSHOT_DIR");
        if (!evidence.isEmpty()) {
            QVERIFY(write(QDir(evidence).filePath("source-before.pcb"),fixture()));
            QVERIFY(write(QDir(evidence).filePath("saved-roundtrip.pcb"),read(output)));
            const QJsonObject record{{"input_unchanged",read(input)==fixture()},
                {"saved_clean",!window.editSession().dirty()}, {"reopened_clean",!reopened.editSession().dirty()},
                {"start_x",150}, {"start_y",75}, {"end_x",450}, {"end_y",475},
                {"input_sha256",QString::fromLatin1(QCryptographicHash::hash(read(input),QCryptographicHash::Sha256).toHex())},
                {"output_sha256",QString::fromLatin1(QCryptographicHash::hash(read(output),QCryptographicHash::Sha256).toHex())}};
            QVERIFY(write(QDir(evidence).filePath("roundtrip.json"),QJsonDocument(record).toJson()));
        }
        QVERIFY(window.close()); QVERIFY(reopened.close());
    }
};

int main(int argc,char** argv) {
    QApplication::setAttribute(Qt::AA_DontUseNativeDialogs);
    QApplication app(argc,argv);
    WritingTests tests;
    return QTest::qExec(&tests,argc,argv);
}
#include "WritingTests.moc"
