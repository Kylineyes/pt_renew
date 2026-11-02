#include "application/BoardEditSession.h"
#include "application/TrackPlacementController.h"
#include "io/LegacyFreeTrackCodec.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbWriter.h"
#include "ui/BoardCanvas.h"
#include "ui/MainWindow.h"
#include <QAction>
#include <QFile>
#include <QTemporaryDir>
#include <QtTest/QTest>

namespace {
QByteArray fixture() {
    return "PCB FILE 4\r\nFT\n0 0 100 0 10 1 42\r\n"
        "FT\r\n200 10 220 10 8 6\n"
        "FS\n0 0 10 0 1 7\nOpaque \x82\r\n"
        "COMP\nU1\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
        "CT\n10 10 20 10 5 1 9\nENDCOMP\r\n\t ENDPCB \t\r\n\x1a \t\r\n";
}
bool writeFile(const QString& path, const QByteArray& bytes) {
    QFile file(path);
    return file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size();
}
QByteArray readFile(const QString& path) {
    QFile file(path);
    return file.open(QIODevice::ReadOnly) ? file.readAll() : QByteArray();
}
pt::LegacyFreeTrackCodec::Options explicitOptions(bool seven) {
    pt::LegacyFreeTrackCodec::Options options;
    options.fields = seven ? pt::LegacyFreeTrackCodec::FieldLayout::SevenFields
                           : pt::LegacyFreeTrackCodec::FieldLayout::SixFields;
    options.lineEnding = pt::LegacyFreeTrackCodec::LineEnding::CrLf;
    // 合成参数只用于跨模块验证，不代表原软件缺省属性。
    if (seven) options.extra = 19;
    return options;
}
bool place(pt::TrackPlacementController& tool, QPointF start, QPointF end, int layer) {
    return tool.begin(15, layer, true) && tool.setStart(start, true)
        && tool.previewEnd(end, true) && tool.commit(true);
}
}

class TrackCreatedWorkflowTests final : public QObject {
    Q_OBJECT
private slots:
    void mixedHistoryPublishesSnapshotAndRetainsSavePoint_data() {
        QTest::addColumn<bool>("seven");
        QTest::newRow("explicit-six") << false;
        QTest::newRow("explicit-seven") << true;
    }
    void mixedHistoryPublishesSnapshotAndRetainsSavePoint() {
        QFETCH(bool, seven);
        QTemporaryDir dir; QVERIFY(dir.isValid());
        const auto input = dir.filePath(QStringLiteral("INPUT.PCB"));
        QVERIFY(writeFile(input, fixture()));
        const auto parsed = pt::LegacyPcbReader::readFile(input); QVERIFY(parsed.succeeded());
        pt::BoardEditSession edits; edits.reset(parsed.document);
        pt::TrackPlacementController tool(edits);
        QVERIFY(edits.moveTrack({pt::PrimitiveKind::Track, 0}, edits.revision(), {50,-25}));
        QVERIFY(edits.deleteTrack({pt::PrimitiveKind::Track, 1}, edits.revision()));
        QVERIFY(place(tool, {-10,20}, {30,40}, 1));
        QVERIFY(place(tool, {300,200}, {400,250}, 6));
        const auto committed = edits.document(); const auto revision = edits.revision();
        const auto firstIdentity = committed->tracks[2].identity;
        const auto secondIdentity = committed->tracks[3].identity;
        QVERIFY(tool.begin(15, 1, true)); QVERIFY(tool.setStart({500,500}, true));
        QVERIFY(tool.previewEnd({600,500}, true)); tool.cancel();
        QCOMPARE(edits.document(), committed); QCOMPARE(edits.revision(), revision);
        QVERIFY(edits.dirty());
        const auto failed = pt::LegacyPcbWriter::saveAsWithCreated(
            dir.filePath(QStringLiteral("MISSING.PCB")), *edits.original(), *committed, {});
        QVERIFY(!failed.succeeded()); QVERIFY(edits.dirty());
        QVERIFY(!QFile::exists(dir.filePath(QStringLiteral("MISSING.PCB"))));
        const auto options = explicitOptions(seven);
        const auto output = dir.filePath(QStringLiteral("CREATED.PCB"));
        const auto saved = pt::LegacyPcbWriter::saveAsWithCreated(output, *edits.original(), *committed, options);
        QVERIFY2(saved.succeeded(), qPrintable(saved.error));
        // 发布与保存点是两项职责；只有上层收到成功回执后才标记保存点。
        QVERIFY(edits.dirty()); edits.markSaved(); QVERIFY(!edits.dirty());
        QCOMPARE(edits.original()->filePath, input); QCOMPARE(edits.document(), committed);
        QCOMPARE(readFile(input), fixture()); QCOMPARE(readFile(output), saved.bytes);
        auto base = fixture();
        base.replace("0 0 100 0 10 1 42\r\n", "50 -25 150 -25 10 1 42\r\n");
        base.replace("FT\r\n200 10 220 10 8 6\n", "");
        const auto insertion = base.indexOf("\t ENDPCB \t\r\n");
        QCOMPARE(saved.bytes.left(insertion), base.left(insertion));
        QVERIFY(saved.bytes.endsWith(base.mid(insertion)));
        const auto reopened = pt::LegacyPcbReader::readFile(output); QVERIFY(reopened.succeeded());
        QCOMPARE(reopened.document->tracks.size(), committed->tracks.size());
        for (qsizetype i = 0; i < committed->tracks.size(); ++i) {
            const auto& before = committed->tracks[i]; const auto& after = reopened.document->tracks[i];
            QCOMPARE(after.start, before.start); QCOMPARE(after.end, before.end);
            QCOMPARE(after.width, before.width); QCOMPARE(after.layer, before.layer);
            QCOMPARE(after.extra, i < 2 ? before.extra : options.extra);
            QCOMPARE(after.identity.kind, pt::TrackIdentity::Kind::Loaded);
        }
        QVERIFY(tool.undo()); QVERIFY(edits.dirty());
        QVERIFY(tool.redo()); QVERIFY(!edits.dirty());
        QVERIFY(edits.document()->tracks[2].identity == firstIdentity);
        QVERIFY(edits.document()->tracks[3].identity == secondIdentity);
        QCOMPARE(pt::LegacyPcbWriter::prepareWithCreated(*edits.original(), *edits.document(), options).bytes, saved.bytes);
        QVERIFY(!pt::LegacyPcbWriter::saveAsWithCreated(output, *edits.original(), *edits.document(), options).succeeded());
        QVERIFY(!edits.dirty()); QCOMPARE(readFile(output), saved.bytes);
        // 截断保存点以后的分支不复用已分配的新建身份，也不能错误变 clean。
        QVERIFY(tool.undo());
        QVERIFY(place(tool, {500,600}, {700,600}, 6));
        QVERIFY(!edits.canRedo()); QVERIFY(edits.dirty());
        QVERIFY(edits.document()->tracks.back().identity.value > secondIdentity.value);
        QCOMPARE(readFile(input), fixture()); QCOMPARE(readFile(output), saved.bytes);
    }

    void uiCommittedSnapshotUsesExplicitWriterAndReopensAsLoaded() {
        QTemporaryDir dir; QVERIFY(dir.isValid());
        const auto input = dir.filePath(QStringLiteral("INPUT.PCB")); QVERIFY(writeFile(input, fixture()));
        pt::MainWindow window; QVERIFY(window.inspectFile(input));
        auto* canvas = window.findChild<pt::BoardCanvas*>(); QVERIFY(canvas);
        const auto originalRevision = window.editSession().revision();
        QString error;
        QVERIFY(window.beginTrackPlacement(15, 1, &error));
        QVERIFY(window.setTrackPlacementStart({-10,20}, &error));
        QVERIFY(window.previewTrackPlacementEnd({30,40}, &error));
        QCOMPARE(window.editSession().revision(), originalRevision); QVERIFY(!window.editSession().dirty());
        QVERIFY(window.commitTrackPlacement(&error)); QVERIFY(window.editSession().dirty());
        const auto committed = window.editSession().document();
        QCOMPARE(canvas->document(), committed.get()); QVERIFY(!canvas->selection());
        QVERIFY(!canvas->measurement());
        const auto createdIdentity = committed->tracks.back().identity;
        // 先从真实主窗验证默认产品路径拒绝新增，并保留工作文档与 dirty。
        QVERIFY(window.editSession().dirty());
        const auto unavailable = dir.filePath(QStringLiteral("PRODUCT.PCB"));
        QVERIFY(!window.saveAsFile(unavailable, &error)); QVERIFY(!error.isEmpty());
        QVERIFY(!QFile::exists(unavailable)); QCOMPARE(window.editSession().document(), committed);
        QVERIFY(window.beginTrackPlacement(15, 6, &error));
        QVERIFY(window.setTrackPlacementStart({300,300}, &error));
        QVERIFY(window.previewTrackPlacementEnd({400,300}, &error));
        const auto output = dir.filePath(QStringLiteral("CREATED.PCB"));
        QVERIFY2(window.saveAsFileWithCreated(output, explicitOptions(true), &error), qPrintable(error));
        // 主窗取消未提交的下一段，收到真实发布成功后标记保存点，保留当前文档身份。
        QCOMPARE(window.trackPlacement().state(), pt::TrackPlacementState::Idle);
        QCOMPARE(window.editSession().document(), committed);
        QCOMPARE(window.editSession().original()->filePath, input);
        QVERIFY(!window.editSession().dirty());
        const auto published = readFile(output); QVERIFY(!published.isEmpty());
        QVERIFY(window.editSession().canUndo());
        auto* undo = window.findChild<QAction*>(QStringLiteral("edit.undo"));
        auto* redo = window.findChild<QAction*>(QStringLiteral("edit.redo")); QVERIFY(undo); QVERIFY(redo);
        undo->trigger(); QVERIFY(window.editSession().dirty());
        QCOMPARE(window.editSession().document()->tracks.size(), committed->tracks.size() - 1);
        redo->trigger(); QVERIFY(!window.editSession().dirty());
        QVERIFY(window.editSession().document()->tracks.back().identity == createdIdentity);
        QVERIFY(!window.saveAsFileWithCreated(output, explicitOptions(true), &error));
        QVERIFY(!error.isEmpty()); QVERIFY(!window.editSession().dirty());
        QCOMPARE(readFile(output), published);
        pt::MainWindow reopened; QVERIFY(reopened.inspectFile(output));
        QVERIFY(!reopened.editSession().dirty()); QVERIFY(!reopened.editSession().canUndo());
        QCOMPARE(reopened.editSession().document()->tracks.size(), committed->tracks.size());
        QCOMPARE(reopened.editSession().document()->tracks.back().identity.kind, pt::TrackIdentity::Kind::Loaded);
        QCOMPARE(reopened.editSession().document()->tracks.back().extra, std::optional<int>(19));
        QCOMPARE(readFile(input), fixture());
    }
};

QTEST_MAIN(TrackCreatedWorkflowTests)
#include "TrackCreatedWorkflowTests.moc"
