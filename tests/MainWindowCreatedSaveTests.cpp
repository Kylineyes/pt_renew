#include "application/CommandCatalog.h"
#include "io/LegacyPcbReader.h"
#include "ui/BoardCanvas.h"
#include "ui/MainWindow.h"
#include "ui/LibraryBrowser.h"
#include <QAction>
#include <QApplication>
#include <QCryptographicHash>
#include <QDialogButtonBox>
#include <QDir>
#include <QFile>
#include <QFileDialog>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QTimer>
#include <QtTest/QTest>

namespace {
QByteArray fixture() {
    return "PCB FILE 4\r\nFT\n0 0 100 0 10 1 42\r\nFT\r\n200 10 220 10 8 6\n"
        "FS\n0 0 10 0 1 7\nOpaque \x82\r\n"
        "COMP\nU1\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
        "CT\n10 10 20 10 5 1 9\nENDCOMP\r\n\t ENDPCB \t\r\n\x1a \t\r\n";
}
bool writeFile(const QString& path, const QByteArray& bytes) {
    QFile file(path); return file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size();
}
QByteArray readFile(const QString& path) {
    QFile file(path); return file.open(QIODevice::ReadOnly) ? file.readAll() : QByteArray();
}
pt::LegacyFreeTrackCodec::Options options(bool seven = false) {
    // 全部是合成验收参数；不代表原 AUTOTRAX 默认值或兼容证明。
    pt::LegacyFreeTrackCodec::Options value;
    value.fields = seven ? pt::LegacyFreeTrackCodec::FieldLayout::SevenFields
                         : pt::LegacyFreeTrackCodec::FieldLayout::SixFields;
    value.lineEnding = seven ? pt::LegacyFreeTrackCodec::LineEnding::CrLf
                             : pt::LegacyFreeTrackCodec::LineEnding::Lf;
    if (seven) value.extra = 19;
    return value;
}
bool place(pt::MainWindow& window, int offset = 0) {
    return window.beginTrackPlacement(17, 6) && window.setTrackPlacementStart({200., 250. + offset})
        && window.previewTrackPlacementEnd({800., 550. + offset}) && window.commitTrackPlacement();
}
QAction* action(pt::MainWindow& window, const char* id) {
    return window.findChild<QAction*>(QString::fromLatin1(id));
}
QString fileInfo(pt::MainWindow& window) {
    return window.findChild<QPlainTextEdit*>(QStringLiteral("fileInfoText"))->toPlainText();
}
QString savedInfo(pt::MainWindow& window) {
    return fileInfo(window).section(QStringLiteral("最近另存为："), 1);
}
}

class MainWindowCreatedSaveTests final : public QObject {
    Q_OBJECT
private slots:
    void publishesCreatedAndReopensWithLoadedIdentity_data() {
        QTest::addColumn<bool>("seven");
        QTest::newRow("六字段LF合成参数") << false;
        QTest::newRow("七字段CRLF合成参数") << true;
    }
    void publishesCreatedAndReopensWithLoadedIdentity() {
        QFETCH(bool, seven);
        QTemporaryDir dir; QVERIFY(dir.isValid());
        const auto input = dir.filePath(QStringLiteral("INPUT.PCB"));
        const auto output = dir.filePath(QStringLiteral("CREATED.PCB"));
        QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input));
        const auto original = window.editSession().original();
        QVERIFY(place(window));
        const auto committed = window.editSession().document();
        const auto identity = committed->tracks.back().identity;
        const auto revision = window.editSession().revision();
        QVERIFY(window.editSession().dirty());
        QString error = QStringLiteral("旧错误");
        QVERIFY2(window.saveAsFileWithCreated(output, options(seven), &error), qPrintable(error));
        QVERIFY(error.isEmpty()); QVERIFY(!window.editSession().dirty()); QVERIFY(window.editSession().canUndo());
        QCOMPARE(window.editSession().document(), committed); QCOMPARE(window.editSession().original(), original);
        QCOMPARE(window.editSession().revision(), revision); QCOMPARE(committed->tracks.back().identity, identity);
        QCOMPARE(committed->tracks.back().extra, std::optional<int>());
        QCOMPARE(committed->sourceBytes, fixture()); QCOMPARE(committed->filePath, input);
        auto expected = fixture();
        expected.insert(expected.indexOf("\t ENDPCB"), seven ? "FT\r\n200 250 800 550 17 6 19\r\n" : "FT\n200 250 800 550 17 6\n");
        QCOMPARE(readFile(output), expected); QCOMPARE(readFile(input), fixture());
        QVERIFY(fileInfo(window).contains(output));
        QVERIFY(fileInfo(window).contains(QString::number(expected.size())));
        QVERIFY(fileInfo(window).contains(QString::fromLatin1(QCryptographicHash::hash(expected, QCryptographicHash::Sha256).toHex())));
        QVERIFY(!window.windowTitle().contains(QStringLiteral("已修改")));
        action(window, "edit.undo")->trigger(); QVERIFY(window.editSession().dirty());
        QCOMPARE(window.editSession().document()->tracks.size(), committed->tracks.size() - 1);
        action(window, "edit.redo")->trigger(); QVERIFY(!window.editSession().dirty());
        QCOMPARE(window.editSession().document()->tracks.back().identity, identity);
        // 再次显式另存可选择不同投影；不反写内存附加字段，也不重绑原输入。
        const auto projected = dir.filePath(QStringLiteral("PROJECTED.PCB"));
        QVERIFY(window.saveAsFileWithCreated(projected, options(!seven), &error));
        QVERIFY(!window.editSession().dirty()); QCOMPARE(window.editSession().original(), original);
        QCOMPARE(window.editSession().document()->tracks.back().extra, std::optional<int>());
        pt::MainWindow reopened; QVERIFY(reopened.inspectFile(output));
        QVERIFY(!reopened.editSession().dirty()); QVERIFY(!reopened.editSession().canUndo());
        const auto& reloaded = *reopened.editSession().document();
        QCOMPARE(reloaded.tracks.size(), committed->tracks.size());
        for (qsizetype i = 0; i < reloaded.tracks.size(); ++i) {
            const auto& before = committed->tracks[i]; const auto& after = reloaded.tracks[i];
            QCOMPARE(after.start, before.start); QCOMPARE(after.end, before.end);
            QCOMPARE(after.width, before.width); QCOMPARE(after.layer, before.layer);
            QCOMPARE(after.identity.kind, pt::TrackIdentity::Kind::Loaded);
            QCOMPARE(after.identity.value, quint64(after.source.line));
            QCOMPARE(after.extra, i + 1 == reloaded.tracks.size() ? options(seven).extra : before.extra);
        }
        QCOMPARE(reloaded.filePath, output); QCOMPARE(reloaded.sourceBytes, expected);
        QVERIFY(!pt::trackPlacementUserEntryAvailable()); QVERIFY(!action(window, "place.track")->isEnabled());
    }

    void mixedExistingEditsAndCreatedSaveThroughWindow() {
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input));
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0})); QVERIFY(window.moveSelectedTrack({50,-25}));
        QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,1})); QVERIFY(window.deleteSelectedTrack());
        QVERIFY(place(window)); const auto document = window.editSession().document();
        const auto output = dir.filePath(QStringLiteral("MIXED.PCB")); QString error;
        QVERIFY2(window.saveAsFileWithCreated(output, options(true), &error), qPrintable(error));
        QVERIFY(!window.editSession().dirty());
        auto expected = fixture(); expected.replace("0 0 100 0 10 1 42\r\n", "50 -25 150 -25 10 1 42\r\n");
        expected.replace("FT\r\n200 10 220 10 8 6\n", "");
        expected.insert(expected.indexOf("\t ENDPCB"), "FT\r\n200 250 800 550 17 6 19\r\n");
        QCOMPARE(readFile(output), expected); QCOMPARE(readFile(input), fixture());
        QCOMPARE(window.editSession().document(), document);
        for (int i = 0; i < 3; ++i) action(window, "edit.undo")->trigger();
        QVERIFY(window.editSession().dirty()); QCOMPARE(window.editSession().document()->tracks.size(), 3);
        for (int i = 0; i < 3; ++i) action(window, "edit.redo")->trigger();
        QVERIFY(!window.editSession().dirty()); QCOMPARE(readFile(output), expected);
    }

    void branchesOnEitherSideOfSavedPosition_data() {
        QTest::addColumn<bool>("beforeSaved");
        QTest::newRow("截断保存点之前") << true;
        QTest::newRow("截断保存点之后") << false;
    }
    void branchesOnEitherSideOfSavedPosition() {
        QFETCH(bool, beforeSaved);
        QTemporaryDir dir;
        const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input)); QVERIFY(place(window));
        const auto savedIdentity = window.editSession().document()->tracks.back().identity;
        QVERIFY(window.saveAsFileWithCreated(dir.filePath(QStringLiteral("SAVED.PCB")), options()));
        quint64 abandonedIdentity = savedIdentity.value;
        if (!beforeSaved) {
            QVERIFY(place(window, 10)); QVERIFY(place(window, 20));
            abandonedIdentity = window.editSession().document()->tracks.back().identity.value;
        }
        action(window, "edit.undo")->trigger(); QVERIFY(window.editSession().dirty());
        QVERIFY(place(window, 30)); QVERIFY(!window.editSession().canRedo()); QVERIFY(window.editSession().dirty());
        QVERIFY(window.editSession().document()->tracks.back().identity.value > abandonedIdentity);
        action(window, "edit.undo")->trigger();
        if (!beforeSaved) action(window, "edit.undo")->trigger();
        QCOMPARE(window.editSession().dirty(), beforeSaved);
        if (!beforeSaved) QCOMPARE(window.editSession().document()->tracks.back().identity, savedIdentity);
        action(window, "edit.redo")->trigger(); QVERIFY(window.editSession().dirty());
        QCOMPARE(readFile(input), fixture());
    }

    void failureKeepsSnapshotHistoryAndSavedMetadata_data() {
        QTest::addColumn<QString>("mode");
        for (const auto* mode : {"unspecified", "seven-missing-extra", "existing", "same-input", "empty", "missing-directory", "suffix", "netdef-tail", "netdef-interleaved", "default-rejects-created"})
            QTest::newRow(mode) << QString::fromLatin1(mode);
    }
    void failureKeepsSnapshotHistoryAndSavedMetadata() {
        QFETCH(QString, mode);
        QTemporaryDir dir;
        const auto input = dir.filePath(QStringLiteral("INPUT.PCB"));
        auto bytes = fixture();
        const QByteArray net("NETDEF\nGND\n[\nmetadata\n]\n(\nU1-1\n)\n");
        if (mode == "netdef-tail") bytes.insert(bytes.indexOf("\t ENDPCB"), net);
        if (mode == "netdef-interleaved") bytes.insert(bytes.indexOf("FS\n"), net);
        QVERIFY(writeFile(input, bytes));
        pt::MainWindow window; QVERIFY(window.inspectFile(input));
        // 先走默认主窗保存，以便验证失败不能清掉之前的输出元信息。
        const auto prior = dir.filePath(QStringLiteral("PRIOR.PCB")); QVERIFY(window.saveAsFile(prior));
        const auto previousMetadata = savedInfo(window);
        QVERIFY(place(window)); const auto committed = window.editSession().document();
        const auto original = window.editSession().original(); const auto revision = window.editSession().revision();
        const auto identity = committed->tracks.back().identity;
        auto codec = options(); auto output = dir.filePath(QStringLiteral("FAILED.PCB"));
        if (mode == "unspecified") codec = {};
        if (mode == "seven-missing-extra") { codec = options(true); codec.extra.reset(); }
        if (mode == "existing") { output = prior; }
        if (mode == "same-input") output = input;
        if (mode == "empty") output.clear();
        if (mode == "missing-directory") output = dir.filePath(QStringLiteral("absent/FAILED.PCB"));
        if (mode == "suffix") output = dir.filePath(QStringLiteral("FAILED.txt"));
        QString error;
        const bool saved = mode == "default-rejects-created" ? window.saveAsFile(output, &error)
            : window.saveAsFileWithCreated(output, codec, &error);
        QVERIFY(!saved); QVERIFY(!error.isEmpty());
        QCOMPARE(window.editSession().document(), committed); QCOMPARE(window.editSession().original(), original);
        QCOMPARE(window.editSession().revision(), revision); QVERIFY(window.editSession().dirty());
        QVERIFY(window.editSession().canUndo()); QVERIFY(!window.editSession().canRedo());
        QCOMPARE(savedInfo(window), previousMetadata); QCOMPARE(readFile(prior), bytes); QCOMPARE(readFile(input), bytes);
        QCOMPARE(QDir(dir.path()).entryList(QDir::Files | QDir::Hidden | QDir::NoDotAndDotDot), (QStringList{QStringLiteral("INPUT.PCB"), QStringLiteral("PRIOR.PCB")}));
        action(window, "edit.undo")->trigger(); QVERIFY(!window.editSession().dirty());
        action(window, "edit.redo")->trigger(); QVERIFY(window.editSession().dirty());
        QCOMPARE(window.editSession().document()->tracks.back().identity, identity);
    }

    void failureAfterSavedCreatedPreservesCleanPoint() {
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input)); QVERIFY(place(window));
        const auto output = dir.filePath(QStringLiteral("SAVED.PCB"));
        QVERIFY(window.saveAsFileWithCreated(output, options(true)));
        const auto savedBytes = readFile(output); const auto metadata = savedInfo(window);
        const auto document = window.editSession().document(); const auto revision = window.editSession().revision();
        QString error;
        QVERIFY(!window.saveAsFileWithCreated(output, options(), &error)); QVERIFY(!error.isEmpty());
        QVERIFY(!window.editSession().dirty()); QCOMPARE(window.editSession().document(), document);
        QCOMPARE(window.editSession().revision(), revision); QCOMPARE(savedInfo(window), metadata);
        QVERIFY(!window.saveAsFile(dir.filePath(QStringLiteral("DEFAULT.PCB")), &error));
        QVERIFY(!window.editSession().dirty()); QVERIFY(!QFile::exists(dir.filePath(QStringLiteral("DEFAULT.PCB"))));
        action(window, "edit.undo")->trigger(); QVERIFY(window.editSession().dirty());
        action(window, "edit.redo")->trigger(); QVERIFY(!window.editSession().dirty());
        QCOMPARE(readFile(output), savedBytes); QCOMPARE(readFile(input), fixture());
    }

    void publicSaveCancelsPreviewWithoutCommitting_data() {
        QTest::addColumn<bool>("explicitSave"); QTest::addColumn<bool>("created");
        QTest::newRow("默认无新增") << false << false;
        QTest::newRow("显式无新增") << true << false;
        QTest::newRow("默认拒绝新增仍取消预览") << false << true;
        QTest::newRow("显式保存新增但不保存预览") << true << true;
    }
    void publicSaveCancelsPreviewWithoutCommitting() {
        QFETCH(bool, explicitSave); QFETCH(bool, created);
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input)); if (created) QVERIFY(place(window));
        QVERIFY(window.beginTrackPlacement(23, 1)); QVERIFY(window.setTrackPlacementStart({111,222}));
        QVERIFY(window.previewTrackPlacementEnd({333,444}));
        const auto document = window.editSession().document(); const auto revision = window.editSession().revision();
        const auto output = dir.filePath(QStringLiteral("SAVED.PCB"));
        QString error;
        const bool saved = explicitSave ? window.saveAsFileWithCreated(output, options(), &error) : window.saveAsFile(output, &error);
        QCOMPARE(saved, explicitSave || !created);
        QCOMPARE(window.trackPlacement().state(), pt::TrackPlacementState::Idle);
        QVERIFY(!window.findChild<pt::BoardCanvas*>()->trackPlacementMode());
        QCOMPARE(window.editSession().document(), document); QCOMPARE(window.editSession().revision(), revision);
        if (saved) {
            const auto reopened = pt::LegacyPcbReader::readFile(output); QVERIFY(reopened.succeeded());
            QCOMPARE(reopened.document->tracks.size(), document->tracks.size()); QVERIFY(!window.editSession().dirty());
        } else { QVERIFY(window.editSession().dirty()); QVERIFY(!QFile::exists(output)); }
        QCOMPARE(readFile(input), fixture());
    }

    void savePreservesExistingSelectionAndMeasurement_data() {
        QTest::addColumn<bool>("explicitSave"); QTest::addColumn<bool>("measure");
        for (bool explicitSave : {false, true}) for (bool measure : {false, true})
            QTest::newRow(qPrintable(QStringLiteral("%1-%2").arg(explicitSave).arg(measure))) << explicitSave << measure;
    }
    void savePreservesExistingSelectionAndMeasurement() {
        QFETCH(bool, explicitSave); QFETCH(bool, measure);
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input));
        auto* canvas = window.findChild<pt::BoardCanvas*>(); QVERIFY(canvas);
        if (measure) {
            canvas->setMeasurementMode(true);
            QTest::mouseClick(canvas, Qt::LeftButton, Qt::NoModifier, {40,40});
            QTest::mouseClick(canvas, Qt::LeftButton, Qt::NoModifier, {90,70});
            QVERIFY(canvas->measurement());
        } else QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
        const auto selection = canvas->selection(); const auto measurement = canvas->measurement();
        const auto output = dir.filePath(QStringLiteral("SAVED.PCB"));
        QVERIFY(explicitSave ? window.saveAsFileWithCreated(output, options()) : window.saveAsFile(output));
        QCOMPARE(canvas->selection(), selection); QCOMPARE(canvas->measurementMode(), measure);
        QCOMPARE(canvas->measurement().has_value(), measurement.has_value());
        if (measurement) {
            QCOMPARE(canvas->measurement()->start, measurement->start); QCOMPARE(canvas->measurement()->end, measurement->end);
        }
    }

    void noDocumentAndLoadingRejectBothPaths() {
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QString error;
        const auto output = dir.filePath(QStringLiteral("FAILED.PCB"));
        QVERIFY(!window.saveAsFileWithCreated(output, options(), &error)); QVERIFY(!error.isEmpty());
        QVERIFY(!window.saveAsFile(output, &error)); QVERIFY(!error.isEmpty());
        QVERIFY(window.inspectFile(input)); QVERIFY(place(window));
        const auto document = window.editSession().document(); const auto revision = window.editSession().revision();
        QSignalSpy loaded(&window, &pt::MainWindow::boardLoadFinished);
        window.requestOpenFile(dir.filePath(QStringLiteral("MISSING.PCB")));
        // requestOpenFile到finished事件前，主窗必须拒绝同步保存旧工作副本。
        QVERIFY(!window.saveAsFileWithCreated(output, options(), &error)); QVERIFY(!error.isEmpty());
        QVERIFY(!window.saveAsFile(output, &error)); QVERIFY(!error.isEmpty());
        QCOMPARE(window.editSession().document(), document); QCOMPARE(window.editSession().revision(), revision);
        QVERIFY(window.editSession().dirty()); QVERIFY(!QFile::exists(output));
        QTRY_COMPARE(loaded.size(), 1); QCOMPARE(loaded.front().front().toBool(), false);
        QCOMPARE(window.editSession().document(), document); QVERIFY(window.editSession().dirty());
    }

    void librarySourceCannotSaveThroughEitherPath() {
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input));
        // 仅设置来源上下文模拟库预览；保存调用始终经过真实主窗API。
        auto library = std::make_shared<pt::BoardDocument>(*window.editSession().original());
        library->sourceContext = QStringLiteral("LIB 只读预览");
        auto& edits = const_cast<pt::BoardEditSession&>(window.editSession()); edits.reset(library);
        window.findChild<pt::BoardCanvas*>()->setDocument(edits.document());
        const auto document = edits.document(); const auto revision = edits.revision();
        const auto output = dir.filePath(QStringLiteral("FAILED.PCB")); QString error;
        QVERIFY(!window.saveAsFileWithCreated(output, options(), &error)); QVERIFY(!error.isEmpty());
        QVERIFY(!window.saveAsFile(output, &error)); QVERIFY(!error.isEmpty());
        QCOMPARE(edits.document(), document); QCOMPARE(edits.revision(), revision);
        QVERIFY(!edits.dirty()); QVERIFY(!edits.canUndo()); QVERIFY(!QFile::exists(output));
    }

    void activeLibraryWindowRejectsBothPaths() {
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input)); QVERIFY(place(window));
        const auto document = window.editSession().document(); const auto revision = window.editSession().revision();
        auto* library = window.findChild<pt::LibraryBrowser*>(); QVERIFY(library);
        library->showBrowser(); library->activateWindow(); QTRY_VERIFY(library->isActiveWindow());
        const auto output = dir.filePath(QStringLiteral("FAILED.PCB")); QString error;
        QVERIFY(!window.saveAsFileWithCreated(output, options(), &error)); QVERIFY(!error.isEmpty());
        QVERIFY(!window.saveAsFile(output, &error)); QVERIFY(!error.isEmpty());
        QCOMPARE(window.editSession().document(), document); QCOMPARE(window.editSession().revision(), revision);
        QVERIFY(window.editSession().dirty()); QVERIFY(window.editSession().canUndo()); QVERIFY(!QFile::exists(output));
        library->hide();
    }

    void cancelledMenuDialogCancelsPreviewWithoutWriting() {
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input)); QVERIFY(place(window));
        QVERIFY(window.beginTrackPlacement(12, 1)); QVERIFY(window.setTrackPlacementStart({1,2}));
        QVERIFY(window.previewTrackPlacementEnd({3,4}));
        const auto document = window.editSession().document(); const auto revision = window.editSession().revision();
        bool cancelled = false;
        QTimer::singleShot(0, &window, [&] {
            auto* dialog = qobject_cast<QFileDialog*>(QApplication::activeModalWidget()); QVERIFY(dialog);
            QCOMPARE(window.trackPlacement().state(), pt::TrackPlacementState::Idle);
            cancelled = true; dialog->reject();
        });
        action(window, "file.save_as")->trigger(); QVERIFY(cancelled);
        QCOMPARE(window.editSession().document(), document); QCOMPARE(window.editSession().revision(), revision);
        QVERIFY(window.editSession().dirty()); QVERIFY(window.editSession().canUndo());
        QCOMPARE(QDir(dir.path()).entryList(QDir::Files), QStringList{QStringLiteral("INPUT.PCB")});
    }

    void loadRequestDuringMenuDialogRejectsStaleWrite() {
        QTemporaryDir dir; const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        const auto output = dir.filePath(QStringLiteral("STALE.PCB"));
        pt::MainWindow window; QVERIFY(window.inspectFile(input));
        const auto document = window.editSession().document(); const auto revision = window.editSession().revision();
        bool requested = false, warned = false;
        QTimer timer; timer.setInterval(10);
        connect(&timer, &QTimer::timeout, &window, [&] {
            if (auto* dialog = qobject_cast<QFileDialog*>(QApplication::activeModalWidget())) {
                if (requested) return;
                requested = true;
                // 失败载入完成后修订和文档仍相同，代次变化仍须使旧文件框失效。
                connect(&window, &pt::MainWindow::boardLoadFinished, dialog, [&, dialog](bool success) {
                    QVERIFY(!success);
                    dialog->selectFile(output);
                    auto* buttons = dialog->findChild<QDialogButtonBox*>(); QVERIFY(buttons);
                    buttons->button(QDialogButtonBox::Save)->click();
                }, Qt::SingleShotConnection);
                window.requestOpenFile(dir.filePath(QStringLiteral("MISSING.PCB")));
            } else if (auto* box = qobject_cast<QMessageBox*>(QApplication::activeModalWidget())) {
                warned = true; timer.stop(); box->accept();
            }
        });
        QTimer::singleShot(5000, &window, [&] {
            timer.stop(); if (auto* dialog = qobject_cast<QDialog*>(QApplication::activeModalWidget())) dialog->reject();
        });
        timer.start(); action(window, "file.save_as")->trigger();
        QVERIFY(requested); QVERIFY(warned); QVERIFY(!QFile::exists(output));
        QTRY_VERIFY(action(window, "file.save_as")->isEnabled());
        QCOMPARE(window.editSession().document(), document); QCOMPARE(window.editSession().revision(), revision);
        QVERIFY(!window.editSession().dirty()); QCOMPARE(readFile(input), fixture());
    }
};

int main(int argc, char** argv) {
    QApplication::setAttribute(Qt::AA_DontUseNativeDialogs);
    QApplication app(argc, argv);
    MainWindowCreatedSaveTests tests;
    return QTest::qExec(&tests, argc, argv);
}
#include "MainWindowCreatedSaveTests.moc"
