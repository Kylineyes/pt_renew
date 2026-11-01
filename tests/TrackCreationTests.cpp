#include "application/BoardEditSession.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbWriter.h"
#include <QDir>
#include <QFile>
#include <QTemporaryDir>
#include <QtTest/QTest>
#include <limits>

namespace {
QByteArray fixture() {
    return "PCB FILE 4\r\n\r\n FT \n0 0 100 50 10 1 42\r\nFT\n200 0 300 50 12 6\n"
        "COMP\nU1\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 2\n"
        "CT\n0 0 100 0 10 1\nENDCOMP\nENDPCB\r\n";
}
pt::PrimitiveId track(qsizetype index) { return {pt::PrimitiveKind::Track, index}; }
bool add(pt::BoardEditSession& session, int layer = 1) {
    return session.addTrack({-10,20}, {30,40}, 15, layer, session.revision());
}
}

class TrackCreationTests final : public QObject {
    Q_OBJECT
private slots:
    void loadedIdentityUsesOriginalTagLines() {
        const auto loaded = pt::LegacyPcbReader::parse(fixture());
        QVERIFY2(loaded.succeeded(), qPrintable(loaded.error));
        const auto& tracks = loaded.document->tracks;
        QCOMPARE(tracks.size(), 3);
        QCOMPARE(tracks[0].source.line, 3);
        QCOMPARE(tracks[1].source.line, 5);
        QCOMPARE(tracks[2].source.line, 14);
        for (const auto& item : tracks) {
            QVERIFY(item.identity.valid());
            QVERIFY(item.identity == pt::TrackIdentity::loaded(item.source.line));
            QCOMPARE(item.source.byteOffset, -1);
        }
        QVERIFY(tracks[2].source.component >= 0);
        QVERIFY(pt::TrackIdentity::loaded(1) != pt::TrackIdentity::created(1));
        QVERIFY(!pt::TrackIdentity::loaded(0).valid());
        QVERIFY(!pt::TrackIdentity::created(0).valid());
    }

    void addMoveDeleteUndoRedoRestoresIdentitiesAndOrder() {
        const auto original = pt::LegacyPcbReader::parse(fixture()).document;
        pt::BoardEditSession session; session.reset(original);
        const auto first = original->tracks[0].identity;
        const auto component = original->tracks[2].identity;
        const auto initialRevision = session.revision();
        QVERIFY(add(session));
        const auto added = session.document()->tracks[3];
        QVERIFY(added.identity == pt::TrackIdentity::created(1));
        QCOMPARE(added.start, QPointF(-10,20)); QCOMPARE(added.end, QPointF(30,40));
        QCOMPARE(added.width, 15); QCOMPARE(added.layer, 1);
        QVERIFY(!added.extra.has_value());
        QCOMPARE(added.source.line, 0); QCOMPARE(added.source.component, -1); QCOMPARE(added.source.byteOffset, -1);
        QVERIFY(session.dirty()); QCOMPARE(session.revision(), initialRevision + 1);
        QCOMPARE(session.document()->workingRevision, session.revision());
        const auto afterAdd = session.document();
        QVERIFY(session.moveTrack(track(3), session.revision(), {10,-20}));
        QCOMPARE(session.document()->tracks[3].start, QPointF(0,0));
        QVERIFY(session.document()->tracks[3].identity == added.identity);
        QCOMPARE(afterAdd->tracks[3].start, added.start);
        QVERIFY(session.deleteTrack(track(0), session.revision()));
        QVERIFY(session.document()->tracks[1].identity == component);
        QVERIFY(session.document()->tracks[2].identity == added.identity);
        QVERIFY(session.deleteTrack(track(2), session.revision()));
        QCOMPARE(session.document()->tracks.size(), 2);
        QVERIFY(session.undo());
        QVERIFY(session.document()->tracks[2].identity == added.identity);
        QCOMPARE(session.document()->tracks[2].start, QPointF(0,0));
        QVERIFY(session.undo());
        QVERIFY(session.document()->tracks[0].identity == first);
        QVERIFY(session.document()->tracks[2].identity == component);
        QVERIFY(session.undo());
        QCOMPARE(session.document()->tracks[3].start, added.start);
        QVERIFY(session.undo());
        QCOMPARE(session.document()->tracks.size(), 3);
        QVERIFY(!session.dirty()); QVERIFY(!session.canUndo());
        for (int i = 0; i < 4; ++i) QVERIFY(session.redo());
        QVERIFY(!session.canRedo()); QCOMPARE(session.document()->tracks.size(), 2);
        QCOMPARE(original->tracks.size(), 3); QCOMPARE(original->tracks[0].extra, std::optional<int>(42));
        QCOMPARE(session.document()->sourceBytes, fixture());
        QCOMPARE(session.document()->recordCounts, original->recordCounts);
        QCOMPARE(session.document()->byteSize, original->byteSize);
        QCOMPARE(session.document()->sha256, original->sha256);
        QCOMPARE(session.document()->components.constData(), original->components.constData());
    }

    void branchDoesNotReuseIdentitiesOrOldSavedPosition() {
        pt::BoardEditSession session; session.reset(pt::LegacyPcbReader::parse(fixture()).document);
        QVERIFY(add(session));
        const auto first = session.document()->tracks.back().identity;
        session.markSaved(); QVERIFY(!session.dirty());
        QVERIFY(add(session, 6));
        const auto abandoned = session.document()->tracks.back().identity;
        session.markSaved();
        QVERIFY(session.undo()); QVERIFY(session.dirty());
        const auto current = session.document(); const auto revision = session.revision();
        QString error;
        QVERIFY(!session.addTrack({1,2}, {3,4}, 0, 1, revision, &error));
        QVERIFY(!error.isEmpty()); QCOMPARE(session.document(), current);
        QCOMPARE(session.revision(), revision); QVERIFY(session.canRedo());
        QVERIFY(session.redo()); QVERIFY(!session.dirty());
        QVERIFY(session.document()->tracks.back().identity == abandoned);
        QVERIFY(session.undo());
        QVERIFY(add(session));
        const auto branched = session.document()->tracks.back().identity;
        QVERIFY(branched.value > abandoned.value); QVERIFY(branched != first);
        QVERIFY(!session.canRedo()); QVERIFY(session.dirty());
        QVERIFY(session.undo()); QVERIFY(session.undo());
        // 被截断的保存点不能因历史位置相同而恢复。
        QVERIFY(session.dirty());
        session.markSaved(); QVERIFY(!session.dirty());
        QVERIFY(session.redo()); QVERIFY(session.dirty());
        QVERIFY(session.document()->tracks.back().identity == first);
        QVERIFY(session.redo());
        QVERIFY(session.document()->tracks.back().identity == branched);
    }

    void invalidCreationPreservesRevisionHistoryAndSequence_data() {
        QTest::addColumn<QPointF>("start"); QTest::addColumn<QPointF>("end");
        QTest::addColumn<int>("width"); QTest::addColumn<int>("layer");
        QTest::newRow("zero-length") << QPointF(1,2) << QPointF(1,2) << 10 << 1;
        QTest::newRow("fraction-start") << QPointF(.5,0) << QPointF(1,2) << 10 << 1;
        QTest::newRow("fraction-end") << QPointF(0,0) << QPointF(1,2.5) << 10 << 1;
        QTest::newRow("negative-limit") << QPointF(-1000001,0) << QPointF(1,2) << 10 << 1;
        QTest::newRow("positive-limit") << QPointF(0,0) << QPointF(1000001,2) << 10 << 1;
        QTest::newRow("nan") << QPointF(std::numeric_limits<qreal>::quiet_NaN(),0) << QPointF(1,2) << 10 << 1;
        QTest::newRow("infinity") << QPointF(0,0) << QPointF(1,std::numeric_limits<qreal>::infinity()) << 10 << 1;
        QTest::newRow("zero-width") << QPointF() << QPointF(1,2) << 0 << 1;
        QTest::newRow("negative-width") << QPointF() << QPointF(1,2) << -1 << 1;
        QTest::newRow("large-width") << QPointF() << QPointF(1,2) << 1000001 << 1;
        QTest::newRow("other-layer") << QPointF() << QPointF(1,2) << 10 << 7;
        QTest::newRow("invalid-layer") << QPointF() << QPointF(1,2) << 10 << 0;
    }
    void invalidCreationPreservesRevisionHistoryAndSequence() {
        QFETCH(QPointF, start); QFETCH(QPointF, end); QFETCH(int, width); QFETCH(int, layer);
        pt::BoardEditSession session; session.reset(pt::LegacyPcbReader::parse(fixture()).document);
        QVERIFY(add(session)); session.markSaved(); QVERIFY(session.undo());
        const auto document = session.document(); const auto revision = session.revision();
        QString error = QStringLiteral("旧错误");
        QVERIFY(!session.addTrack(start, end, width, layer, revision, &error));
        QVERIFY(!error.isEmpty()); QVERIFY(error != QStringLiteral("旧错误"));
        QCOMPARE(session.document(), document); QCOMPARE(session.revision(), revision);
        QVERIFY(session.canRedo()); QVERIFY(!session.canUndo()); QVERIFY(session.dirty());
        QVERIFY(add(session));
        QVERIFY(session.document()->tracks.back().identity == pt::TrackIdentity::created(2));
        QVERIFY(!session.canRedo());
    }

    void scopeAndStaleRevisionCannotCreateOnAnotherBoard() {
        const auto board = pt::LegacyPcbReader::parse(fixture()).document;
        pt::BoardEditSession session;
        QString error;
        QVERIFY(!session.addTrack({1,2},{3,4},10,1,session.revision(),&error));
        QVERIFY(!error.isEmpty()); QVERIFY(!session.document());
        auto library = std::make_shared<pt::BoardDocument>(*board);
        library->sourceContext = QStringLiteral("封装预览"); session.reset(library);
        QVERIFY(!add(session)); QVERIFY(!session.dirty());
        session.reset(board); const auto oldRevision = session.revision();
        QVERIFY(add(session)); const auto current = session.document();
        QVERIFY(!session.addTrack({1,2},{3,4},10,1,oldRevision,&error));
        QCOMPARE(session.document(), current);
        const auto previousBoardRevision = session.revision();
        session.reset(board);
        QVERIFY(!session.addTrack({1,2},{3,4},10,1,previousBoardRevision,&error));
        QVERIFY(!session.dirty()); QVERIFY(!session.canUndo());
        QVERIFY(add(session));
        QVERIFY(session.document()->tracks.back().identity == pt::TrackIdentity::created(1));
    }

    void invalidLoadedIdentitiesDisableEditing_data() {
        QTest::addColumn<QString>("mode");
        for (const auto* mode : {"unassigned", "duplicate", "line-mismatch", "created", "zero"})
            QTest::newRow(mode) << QString::fromLatin1(mode);
    }
    void invalidLoadedIdentitiesDisableEditing() {
        QFETCH(QString, mode);
        auto board = std::make_shared<pt::BoardDocument>(*pt::LegacyPcbReader::parse(fixture()).document);
        if (mode == "unassigned") board->tracks[0].identity = {};
        if (mode == "duplicate") board->tracks[1] = board->tracks[0];
        if (mode == "line-mismatch") ++board->tracks[0].source.line;
        if (mode == "created") board->tracks[0].identity = pt::TrackIdentity::created(1);
        if (mode == "zero") board->tracks[0].identity.value = 0;
        pt::BoardEditSession session; session.reset(board);
        const auto current = session.document(); const auto revision = session.revision();
        QVERIFY(!session.editable(track(0), revision));
        QVERIFY(!session.moveTrack(track(0), revision, {1,1}));
        QVERIFY(!session.deleteTrack(track(0), revision)); QVERIFY(!add(session));
        QCOMPARE(session.document(), current); QCOMPARE(session.revision(), revision);
        QVERIFY(!session.dirty()); QVERIFY(!session.canUndo());
    }

    void emptyLoadedBoardAndBoundaryGeometry() {
        const auto board = pt::LegacyPcbReader::parse("PCB FILE 4\nENDPCB").document; QVERIFY(board);
        pt::BoardEditSession session; session.reset(board);
        QString error = QStringLiteral("旧错误");
        QVERIFY(session.addTrack({-1000000,1000000}, {1000000,-1000000}, 1000000, 6, session.revision(), &error));
        QVERIFY(error.isEmpty()); QCOMPARE(session.document()->tracks.size(), 1);
        QCOMPARE(session.document()->primitiveCount(), 1); QCOMPARE(board->primitiveCount(), 0);
        QVERIFY(session.undo()); QVERIFY(!session.dirty()); QVERIFY(session.document()->tracks.isEmpty());
        QVERIFY(session.redo()); QCOMPARE(session.document()->tracks[0].layer, 6);
    }

    void newTracksCannotBeWrittenAndUndoRestoresByteRoundtrip() {
        QTemporaryDir directory; QVERIFY(directory.isValid());
        const auto original = pt::LegacyPcbReader::parse(fixture(), directory.filePath("INPUT.PCB")).document;
        pt::BoardEditSession session; session.reset(original);
        QVERIFY(add(session));
        const auto document = session.document(); const auto revision = session.revision();
        const auto output = directory.filePath("SAVED.PCB");
        const auto result = pt::LegacyPcbWriter::saveAs(output, *original, *session.document());
        QVERIFY(!result.succeeded()); QVERIFY(!result.error.isEmpty()); QVERIFY(!QFile::exists(output));
        QCOMPARE(QDir(directory.path()).entryList(QDir::Files | QDir::Hidden | QDir::NoDotAndDotDot).size(), 0);
        QCOMPARE(session.document(), document); QCOMPARE(session.revision(), revision); QVERIFY(session.dirty());
        QVERIFY(session.undo());
        const auto restored = pt::LegacyPcbWriter::prepare(*original, *session.document());
        QVERIFY2(restored.succeeded(), qPrintable(restored.error)); QCOMPARE(restored.bytes, fixture());
        QVERIFY(session.redo());
        QVERIFY(session.deleteTrack(track(3), session.revision()));
        const auto deleted = pt::LegacyPcbWriter::prepare(*original, *session.document());
        QVERIFY2(deleted.succeeded(), qPrintable(deleted.error)); QCOMPARE(deleted.bytes, fixture());
        // 删除新段后的几何相同，但只有明确标记保存点才能清除修改状态。
        QVERIFY(session.dirty());
    }

    void writerRejectsIdentityReclassification_data() {
        QTest::addColumn<QString>("mode");
        for (const auto* mode : {"created-with-loaded-source", "changed-loaded-line", "unassigned"})
            QTest::newRow(mode) << QString::fromLatin1(mode);
    }
    void writerRejectsIdentityReclassification() {
        QFETCH(QString, mode);
        const auto original = pt::LegacyPcbReader::parse(fixture()).document;
        auto current = *original;
        if (mode == "created-with-loaded-source") current.tracks[0].identity = pt::TrackIdentity::created(1);
        if (mode == "changed-loaded-line") current.tracks[0].identity = current.tracks[1].identity;
        if (mode == "unassigned") current.tracks[0].identity = {};
        QVERIFY(!pt::LegacyPcbWriter::prepare(*original, current).succeeded());
        // 同时篡改来源快照也必须被冻结原字节的重新解析挡住。
        QVERIFY(!pt::LegacyPcbWriter::prepare(current, current).succeeded());
    }
};

QTEST_APPLESS_MAIN(TrackCreationTests)
#include "TrackCreationTests.moc"
