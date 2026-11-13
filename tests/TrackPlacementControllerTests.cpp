#include "application/BoardEditSession.h"
#include "application/TrackPlacementController.h"
#include <QtTest/QTest>
#include <limits>
#include <memory>

namespace {
std::shared_ptr<const pt::BoardDocument> board(qsizetype count = 0) {
    auto document = std::make_shared<pt::BoardDocument>();
    document->tracks.reserve(count);
    for (qsizetype index = 0; index < count; ++index) {
        pt::Track item{{0, 0}, {100, 100}, 10, 1, {}, {}, {}};
        item.source.line = index + 1;
        item.identity = pt::TrackIdentity::loaded(item.source.line);
        document->tracks.append(item);
    }
    document->recordCounts[QStringLiteral("FT")] = count;
    document->embeddedNetlist = std::make_shared<const pt::Netlist>();
    return document;
}

bool preview(pt::TrackPlacementController& controller) {
    return controller.begin(15, 6, true) && controller.setStart({-10, 20}, true)
        && controller.previewEnd({30, 40}, true);
}
}

class TrackPlacementControllerTests final : public QObject {
    Q_OBJECT
private slots:
    void successfulCommitCreatesExactlyOneHistoryOperation() {
        pt::BoardEditSession edits;
        edits.reset(board(1));
        pt::TrackPlacementController controller(edits);
        const auto before = edits.document();
        const auto revision = edits.revision();
        QVERIFY(preview(controller));
        QCOMPARE(edits.document(), before);
        QCOMPARE(edits.revision(), revision);
        QVERIFY(!edits.dirty());
        QVERIFY(!edits.canUndo());
        QVERIFY(!edits.canRedo());
        QString error = QStringLiteral("旧错误");
        QVERIFY2(controller.commit(true, &error), qPrintable(error));
        QVERIFY(error.isEmpty());
        QCOMPARE(controller.placement().state(), pt::TrackPlacementState::Idle);
        QCOMPARE(edits.revision(), revision + 1);
        QCOMPARE(edits.document()->tracks.size(), 2);
        const auto added = edits.document()->tracks.back();
        QCOMPARE(added.start, QPointF(-10, 20));
        QCOMPARE(added.end, QPointF(30, 40));
        QCOMPARE(added.width, 15);
        QCOMPARE(added.layer, 6);
        QCOMPARE(added.identity, pt::TrackIdentity::created(1));
        QVERIFY(!added.extra);
        QCOMPARE(added.source.line, 0);
        QCOMPARE(added.source.component, -1);
        QCOMPARE(added.source.byteOffset, -1);
        QCOMPARE(edits.document()->recordCounts, before->recordCounts);
        QCOMPARE(edits.document()->embeddedNetlist, before->embeddedNetlist);
        const auto committed = edits.document();
        QVERIFY(!controller.commit(true, &error));
        QVERIFY(!error.isEmpty());
        QCOMPARE(edits.document(), committed);
        QCOMPARE(edits.revision(), revision + 1);
        QVERIFY(controller.undo());
        QCOMPARE(edits.document()->tracks.size(), 1);
        QVERIFY(!edits.dirty());
        QVERIFY(!edits.canUndo());
        QVERIFY(controller.redo());
        QCOMPARE(edits.document()->tracks.back().identity, added.identity);
    }

    void backendRefusalPreservesPreviewAndSavedRedoBranch() {
        pt::BoardEditSession edits;
        edits.reset(board(200000));
        // 在容量已满的合法板上建立保存点和重做分支，后端拒绝不能截断它们。
        QVERIFY(edits.moveTrack({pt::PrimitiveKind::Track, 0}, edits.revision(), {1, 0}));
        edits.markSaved();
        QVERIFY(edits.undo());
        const auto before = edits.document();
        const auto revision = edits.revision();
        pt::TrackPlacementController controller(edits);
        QVERIFY(preview(controller));
        QString backendError;
        QVERIFY(!edits.addTrack({-10, 20}, {30, 40}, 15, 6, revision, &backendError));
        QVERIFY(backendError.contains(QStringLiteral("200000")));
        QString error;
        for (int attempt = 0; attempt < 2; ++attempt) {
            QVERIFY(!controller.commit(true, &error));
            QCOMPARE(error, backendError);
            QCOMPARE(controller.placement().state(), pt::TrackPlacementState::WaitingForEnd);
            QCOMPARE(controller.placement().startPoint(), std::optional<QPointF>({-10, 20}));
            QCOMPARE(controller.placement().previewEndPoint(), std::optional<QPointF>({30, 40}));
            QCOMPARE(controller.placement().width(), 15);
            QCOMPARE(controller.placement().layer(), 6);
            QCOMPARE(edits.document(), before);
            QCOMPARE(edits.revision(), revision);
            QCOMPARE(edits.document()->workingRevision, revision);
            QVERIFY(edits.dirty());
            QVERIFY(!edits.canUndo());
            QVERIFY(edits.canRedo());
        }
        QVERIFY(controller.previewEnd({50, 60}, true));
        QVERIFY(controller.redo());
        QCOMPARE(controller.placement().state(), pt::TrackPlacementState::Idle);
        QCOMPARE(edits.document()->tracks[0].start, QPointF(1, 0));
        QVERIFY(!edits.dirty());
    }

    void previewAndBothCancelStagesPreserveHistoryAndIdentitySequence() {
        pt::BoardEditSession edits;
        edits.reset(board());
        pt::TrackPlacementController controller(edits);
        QVERIFY(preview(controller));
        QVERIFY(controller.commit(true));
        edits.markSaved();
        QVERIFY(controller.undo());
        const auto before = edits.document();
        const auto revision = edits.revision();
        QVERIFY(controller.begin(15, 1, true));
        controller.cancel();
        controller.cancel();
        QVERIFY(preview(controller));
        controller.cancel();
        QCOMPARE(edits.document(), before);
        QCOMPARE(edits.revision(), revision);
        QCOMPARE(edits.document()->workingRevision, revision);
        QCOMPARE(edits.document()->recordCounts, before->recordCounts);
        QCOMPARE(edits.document()->embeddedNetlist, before->embeddedNetlist);
        QVERIFY(edits.dirty());
        QVERIFY(!edits.canUndo());
        QVERIFY(edits.canRedo());
        QVERIFY(controller.redo());
        QVERIFY(!edits.dirty());
        QVERIFY(controller.undo());
        QVERIFY(preview(controller));
        QVERIFY(controller.commit(true));
        // 只有两次成功提交分配了身份；预览、取消和历史回放没有消耗序号。
        QCOMPARE(edits.document()->tracks.back().identity, pt::TrackIdentity::created(2));
        QVERIFY(!edits.canRedo());
    }

    void undoAndRedoCancelEvenWithoutHistory() {
        pt::BoardEditSession edits;
        edits.reset(board());
        pt::TrackPlacementController controller(edits);
        const auto before = edits.document();
        QVERIFY(controller.begin(15, 1, true));
        QVERIFY(!controller.undo());
        QCOMPARE(controller.placement().state(), pt::TrackPlacementState::Idle);
        QVERIFY(preview(controller));
        QVERIFY(!controller.redo());
        QCOMPARE(controller.placement().state(), pt::TrackPlacementState::Idle);
        QCOMPARE(edits.document(), before);
        QVERIFY(!edits.dirty());
    }

    void staleContextCancelsAtEveryEntry_data() {
        QTest::addColumn<int>("change");
        QTest::addColumn<int>("entry");
        for (int change = 0; change < 4; ++change)
            for (int entry = 0; entry < 4; ++entry)
                QTest::newRow(qPrintable(QStringLiteral("change-%1-entry-%2").arg(change).arg(entry)))
                    << change << entry;
    }
    void staleContextCancelsAtEveryEntry() {
        QFETCH(int, change);
        QFETCH(int, entry);
        pt::BoardEditSession edits;
        edits.reset(board());
        pt::TrackPlacementController controller(edits);
        QVERIFY(preview(controller));
        if (change == 0) edits.reset(board());
        if (change == 1) QVERIFY(edits.addTrack({1, 1}, {2, 2}, 5, 1, edits.revision()));
        if (change == 3) {
            // 换入修订号相同的独立编辑会话，仍须由文档指针挡住旧预览。
            pt::BoardEditSession replacement;
            replacement.reset(board());
            QCOMPARE(replacement.revision(), edits.revision());
            edits = std::move(replacement);
        }
        const auto before = edits.document();
        const auto revision = edits.revision();
        const auto dirty = edits.dirty();
        const bool visible = change != 2;
        QString error;
        if (entry == 0) QVERIFY(!controller.setStart({5, 6}, visible, &error));
        if (entry == 1) QVERIFY(!controller.previewEnd({7, 8}, visible, &error));
        if (entry == 2) QVERIFY(!controller.commit(visible, &error));
        if (entry == 3) QVERIFY(!controller.checkContext(visible));
        if (entry != 3) QVERIFY(!error.isEmpty());
        QCOMPARE(controller.placement().state(), pt::TrackPlacementState::Idle);
        QVERIFY(!controller.placement().startPoint());
        QVERIFY(!controller.placement().previewEndPoint());
        QCOMPARE(edits.document(), before);
        QCOMPARE(edits.revision(), revision);
        QCOMPARE(edits.dirty(), dirty);
        QVERIFY(!controller.commit(true));
    }

    void invalidInputsPreserveActivePreviewAndCannotCommitIncompleteSegment() {
        pt::BoardEditSession edits;
        edits.reset(board());
        pt::TrackPlacementController controller(edits);
        QVERIFY(controller.begin(15, 6, true));
        QVERIFY(!controller.commit(true));
        QVERIFY(!controller.setStart({0.5, 1}, true));
        QVERIFY(controller.setStart({0, 0}, true));
        QVERIFY(!controller.previewEnd({0, 0}, true));
        QVERIFY(!controller.previewEnd({1000001, 0}, true));
        QVERIFY(!controller.previewEnd({0, std::numeric_limits<qreal>::infinity()}, true));
        QVERIFY(!controller.commit(true));
        QVERIFY(controller.previewEnd({3, 4}, true));
        const auto document = edits.document();
        for (const auto width : {0, -1, 1000001})
            QVERIFY(!controller.begin(width, 6, true));
        QVERIFY(!controller.begin(15, 7, true));
        QVERIFY(!controller.begin(15, 1, false));
        QCOMPARE(controller.placement().previewEndPoint(), std::optional<QPointF>({3, 4}));
        QCOMPARE(controller.placement().startPoint(), std::optional<QPointF>({0, 0}));
        QCOMPARE(controller.placement().layer(), 6);
        QCOMPARE(edits.document(), document);
        QVERIFY(!edits.dirty());
        QVERIFY(!edits.canUndo());
        QVERIFY(controller.commit(true));
    }

    void libraryAndClosedDocumentCannotBegin() {
        pt::BoardEditSession edits;
        pt::TrackPlacementController controller(edits);
        QString error;
        QVERIFY(!controller.begin(15, 1, true, &error));
        QVERIFY(!error.isEmpty());
        auto library = std::make_shared<pt::BoardDocument>();
        library->sourceContext = QStringLiteral("库预览");
        edits.reset(library);
        QVERIFY(!controller.begin(15, 1, true, &error));
        QVERIFY(!error.isEmpty());
        QCOMPARE(controller.placement().state(), pt::TrackPlacementState::Idle);
        QVERIFY(!edits.dirty());
    }

    void prepareRequestKeepsPreviewAndConfirmRemainsCompatible() {
        pt::BoardEditSession edits;
        edits.reset(board());
        pt::TrackPlacementSession placement;
        QVERIFY(placement.begin(edits.document(), edits.revision(), 15, 1, true));
        QVERIFY(placement.setStart({1, 2}));
        QVERIFY(placement.previewEnd({3, 4}));
        const auto request = placement.prepareRequest(edits.document(), edits.revision(), true);
        QVERIFY(request);
        QCOMPARE(placement.state(), pt::TrackPlacementState::WaitingForEnd);
        const auto confirmed = placement.confirm(edits.document(), edits.revision(), true);
        QVERIFY(confirmed);
        QCOMPARE(confirmed->document, request->document);
        QCOMPARE(confirmed->revision, request->revision);
        QCOMPARE(confirmed->start, request->start);
        QCOMPARE(confirmed->end, request->end);
        QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);
        QVERIFY(!placement.prepareRequest(edits.document(), edits.revision(), true));
        QVERIFY(!edits.dirty());
    }
};

QTEST_APPLESS_MAIN(TrackPlacementControllerTests)
#include "TrackPlacementControllerTests.moc"
