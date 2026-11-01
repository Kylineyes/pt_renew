#include "application/BoardEditSession.h"
#include "application/TrackPlacementController.h"
#include "io/LegacyFreeTrackCodec.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbWriter.h"
#include "io/LegacyTrackInsertionPlanner.h"
#include <QtTest/QTest>

namespace {
QByteArray fixture() {
    return "PCB FILE 4\r\nFT\n0 0 100 0 10 1 42\r\n"
        "FT\r\n200 10 220 10 8 6\n"
        "FS\n0 0 10 0 1 7\nOpaque \x82\r\n"
        "FP\r\n0 0 20 20 1 0 0 13\nENDPCB\n"
        "COMP\nU1\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
        "CT\n10 10 20 10 5 1 9\nENDCOMP\r\n\t ENDPCB \t\r\n\x1a \t\r\n";
}
bool place(pt::TrackPlacementController& controller, QPointF start, QPointF end, int layer) {
    return controller.begin(15, layer, true) && controller.setStart(start, true)
        && controller.previewEnd(end, true) && controller.commit(true);
}
}

class TrackPreflightWorkflowTests final : public QObject {
    Q_OBJECT
private slots:
    void explicitMemoryCandidatePreservesOldEditsAndUndo_data() {
        QTest::addColumn<int>("fields"); QTest::addColumn<QByteArray>("ending");
        QTest::newRow("six-lf") << 6 << QByteArray("\n");
        QTest::newRow("six-crlf") << 6 << QByteArray("\r\n");
        QTest::newRow("seven-lf") << 7 << QByteArray("\n");
        QTest::newRow("seven-crlf") << 7 << QByteArray("\r\n");
    }
    void explicitMemoryCandidatePreservesOldEditsAndUndo() {
        QFETCH(int, fields); QFETCH(QByteArray, ending);
        const auto original = pt::LegacyPcbReader::parse(fixture()).document; QVERIFY(original);
        pt::BoardEditSession edits; edits.reset(original);
        QVERIFY(edits.moveTrack({pt::PrimitiveKind::Track, 0}, edits.revision(), {50,-25}));
        QVERIFY(edits.deleteTrack({pt::PrimitiveKind::Track, 1}, edits.revision()));
        pt::TrackPlacementController controller(edits);
        QVERIFY(place(controller, {-10,20}, {30,40}, 1));
        QVERIFY(place(controller, {300,200}, {400,250}, 6));
        QCOMPARE(controller.placement().state(), pt::TrackPlacementState::Idle);
        QCOMPARE(edits.document()->tracks.size(), 4);
        const auto firstCreated = edits.document()->tracks[2].identity;
        const auto secondCreated = edits.document()->tracks[3].identity;
        const auto documentBeforePlan = edits.document(); const auto revisionBeforePlan = edits.revision();

        const auto plan = pt::LegacyTrackInsertionPlanner::prepare(*original, *edits.document());
        QVERIFY2(plan.succeeded(), qPrintable(plan.error));
        QCOMPARE(plan.createdTracks.size(), 2);
        QVERIFY(plan.createdTracks[0].identity == firstCreated);
        QVERIFY(plan.createdTracks[1].identity == secondCreated);
        auto expectedBase = fixture();
        expectedBase.replace("0 0 100 0 10 1 42\r\n", "50 -25 150 -25 10 1 42\r\n");
        expectedBase.replace("FT\r\n200 10 220 10 8 6\n", "");
        QCOMPARE(plan.baseBytes, expectedBase);
        const auto insertion = expectedBase.indexOf("\t ENDPCB \t\r\n");
        QCOMPARE(plan.insertionByteOffset, insertion);
        QVERIFY(insertion != fixture().indexOf("\t ENDPCB \t\r\n"));
        QCOMPARE(plan.baseLayout.endPcbOffset, insertion);
        QVERIFY(!plan.baseLayout.originalSoftwareInsertionVerified);

        pt::LegacyFreeTrackCodec::Options options;
        options.fields = fields == 6 ? pt::LegacyFreeTrackCodec::FieldLayout::SixFields
                                    : pt::LegacyFreeTrackCodec::FieldLayout::SevenFields;
        options.lineEnding = ending == "\n" ? pt::LegacyFreeTrackCodec::LineEnding::Lf
                                             : pt::LegacyFreeTrackCodec::LineEnding::CrLf;
        // 这里只测试显式合成参数，不把该值当作原软件的新建默认属性。
        if (fields == 7) options.extra = 19;
        QByteArray additions;
        for (const auto& item : plan.createdTracks) {
            const auto encoded = pt::LegacyFreeTrackCodec::encode(item.start, item.end, item.width, item.layer, options);
            QVERIFY2(encoded.succeeded(), qPrintable(encoded.error));
            additions += encoded.bytes;
        }
        QByteArray candidate = plan.baseBytes.left(insertion) + additions + plan.baseBytes.mid(insertion);
        QCOMPARE(candidate.left(insertion), expectedBase.left(insertion));
        QCOMPARE(candidate.mid(insertion + additions.size()), expectedBase.mid(insertion));
        QVERIFY(candidate.endsWith("\x1a \t\r\n"));
        const auto reopened = pt::LegacyPcbReader::parseWithLayout(candidate);
        QVERIFY2(reopened.succeeded(), qPrintable(reopened.error));
        QCOMPARE(reopened.document->tracks.size(), edits.document()->tracks.size());
        for (qsizetype i = 0; i < edits.document()->tracks.size(); ++i) {
            const auto& actual = reopened.document->tracks[i]; const auto& expected = edits.document()->tracks[i];
            QCOMPARE(actual.start, expected.start); QCOMPARE(actual.end, expected.end);
            QCOMPARE(actual.width, expected.width); QCOMPARE(actual.layer, expected.layer);
            QCOMPARE(actual.source.component, expected.source.component);
            QCOMPARE(actual.extra, i < 2 ? expected.extra : options.extra);
            QCOMPARE(actual.identity.kind, pt::TrackIdentity::Kind::Loaded);
        }
        QCOMPARE(edits.document(), documentBeforePlan); QCOMPARE(edits.revision(), revisionBeforePlan);
        QCOMPARE(original->sourceBytes, fixture()); QCOMPARE(edits.document()->sourceBytes, fixture());
        QVERIFY(edits.dirty());
        // 内存候选可被本项目读取，不会解锁现有产品的新增图元写出。
        QVERIFY(!pt::LegacyPcbWriter::prepare(*original, *edits.document()).succeeded());
        QVERIFY(controller.undo()); QVERIFY(controller.undo());
        const auto oldEditsOnly = pt::LegacyPcbWriter::prepare(*original, *edits.document());
        QVERIFY2(oldEditsOnly.succeeded(), qPrintable(oldEditsOnly.error));
        QCOMPARE(oldEditsOnly.bytes, expectedBase); QVERIFY(edits.dirty());
        QVERIFY(controller.undo()); QVERIFY(controller.undo()); QVERIFY(!edits.dirty());
        QCOMPARE(pt::LegacyPcbWriter::prepare(*original, *edits.document()).bytes, fixture());
        for (int i = 0; i < 4; ++i) QVERIFY(controller.redo());
        const auto redone = pt::LegacyTrackInsertionPlanner::prepare(*original, *edits.document());
        QVERIFY(redone.succeeded()); QCOMPARE(redone.baseBytes, expectedBase);
        QVERIFY(redone.createdTracks[0].identity == firstCreated);
        QVERIFY(redone.createdTracks[1].identity == secondCreated);
    }

    void missingEncodingLeavesCommittedGeometryAndHistoryIntact() {
        const auto original = pt::LegacyPcbReader::parse("PCB FILE 4\nENDPCB").document; QVERIFY(original);
        pt::BoardEditSession edits; edits.reset(original); pt::TrackPlacementController controller(edits);
        QVERIFY(place(controller, {10,20}, {30,40}, 1));
        const auto document = edits.document(); const auto revision = edits.revision();
        const auto plan = pt::LegacyTrackInsertionPlanner::prepare(*original, *document);
        QVERIFY(plan.succeeded()); QCOMPARE(plan.createdTracks.size(), 1);
        const auto& item = plan.createdTracks[0];
        const pt::LegacyFreeTrackCodec::Options missing;
        const auto encoded = pt::LegacyFreeTrackCodec::encode(item.start, item.end, item.width, item.layer, missing);
        QVERIFY(!encoded.succeeded()); QVERIFY(encoded.bytes.isEmpty()); QVERIFY(!encoded.error.isEmpty());
        QCOMPARE(edits.document(), document); QCOMPARE(edits.revision(), revision);
        QVERIFY(edits.dirty()); QVERIFY(edits.canUndo()); QVERIFY(!edits.canRedo());
        QVERIFY(!pt::LegacyPcbWriter::prepare(*original, *document).succeeded());
        QVERIFY(controller.undo()); QVERIFY(!edits.dirty());
        QCOMPARE(pt::LegacyPcbWriter::prepare(*original, *edits.document()).bytes, original->sourceBytes);
    }

    void explicitCodecDoesNotAuthorizeNetdefInsertion() {
        const QByteArray bytes = "PCB FILE 4\nNETDEF\nGND\n(\nU1-1\n)\nENDPCB\n";
        const auto original = pt::LegacyPcbReader::parse(bytes).document; QVERIFY(original);
        pt::BoardEditSession edits; edits.reset(original); pt::TrackPlacementController controller(edits);
        QVERIFY(place(controller, {10,20}, {30,40}, 1));
        pt::LegacyFreeTrackCodec::Options options;
        options.fields = pt::LegacyFreeTrackCodec::FieldLayout::SixFields;
        options.lineEnding = pt::LegacyFreeTrackCodec::LineEnding::Lf;
        QVERIFY(pt::LegacyFreeTrackCodec::encode({10,20}, {30,40}, 15, 1, options).succeeded());
        const auto plan = pt::LegacyTrackInsertionPlanner::prepare(*original, *edits.document());
        QVERIFY(!plan.succeeded()); QVERIFY(!plan.error.isEmpty());
        QVERIFY(plan.baseBytes.isEmpty()); QVERIFY(plan.createdTracks.isEmpty());
        QCOMPARE(plan.insertionByteOffset, -1);
        QVERIFY(!pt::LegacyPcbWriter::prepare(*original, *edits.document()).succeeded());
        QVERIFY(controller.undo());
        const auto withoutAdditions = pt::LegacyTrackInsertionPlanner::prepare(*original, *edits.document());
        QVERIFY2(withoutAdditions.succeeded(), qPrintable(withoutAdditions.error));
        QCOMPARE(withoutAdditions.baseBytes, bytes); QCOMPARE(withoutAdditions.insertionByteOffset, -1);
    }
};

QTEST_APPLESS_MAIN(TrackPreflightWorkflowTests)
#include "TrackPreflightWorkflowTests.moc"
