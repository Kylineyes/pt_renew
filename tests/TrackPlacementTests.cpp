#include "application/BoardEditSession.h"
#include "application/TrackPlacementSession.h"
#include <QtTest/QTest>
#include <limits>
#include <memory>

namespace {
std::shared_ptr<const pt::BoardDocument> board(quint64 revision = 1) {
    auto result = std::make_shared<pt::BoardDocument>();
    result->workingRevision = revision;
    return result;
}

pt::TrackPlacementSession started(const std::shared_ptr<const pt::BoardDocument>& document,
                                  quint64 revision = 1) {
    pt::TrackPlacementSession placement;
    const auto begun = placement.begin(document, revision, 15, 1, true);
    Q_ASSERT(begun);
    Q_UNUSED(begun);
    return placement;
}
}

class TrackPlacementTests final : public QObject {
    Q_OBJECT
private slots:
    void lifecycleReturnsOneIdentityFreeRequest() {
        const auto document = board(7);
        pt::TrackPlacementSession placement;
        QVERIFY(placement.begin(document, 7, 15, 6, true));
        QCOMPARE(placement.state(), pt::TrackPlacementState::WaitingForStart);
        QCOMPARE(placement.document(), document);
        QCOMPARE(placement.revision(), quint64(7));
        QVERIFY(placement.setStart({-10, 20}));
        QCOMPARE(placement.state(), pt::TrackPlacementState::WaitingForEnd);
        QVERIFY(placement.previewEnd({30, 40}));
        QCOMPARE(placement.previewEndPoint(), std::optional<QPointF>(QPointF(30, 40)));

        QString error = QStringLiteral("旧错误");
        const auto request = placement.confirm(document, 7, true, &error);
        QVERIFY2(request.has_value(), qPrintable(error));
        QCOMPARE(error, QString());
        QCOMPARE(request->start, QPointF(-10, 20));
        QCOMPARE(request->end, QPointF(30, 40));
        QCOMPARE(request->width, 15);
        QCOMPARE(request->layer, 6);
        QCOMPARE(request->revision, quint64(7));
        QCOMPARE(request->document, document);
        QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);
        QVERIFY(!placement.startPoint().has_value());
        QVERIFY(!placement.previewEndPoint().has_value());
        QVERIFY(!placement.confirm(document, 7, true, &error).has_value());
        QVERIFY(!error.isEmpty());
    }

    void invalidBeginPreservesActivePreview() {
        const auto document = board(3);
        const auto other = board(3);
        pt::TrackPlacementSession placement = started(document, 3);
        QVERIFY(placement.setStart({1, 2}));
        QVERIFY(placement.previewEnd({3, 4}));
        const auto beforeStart = placement.startPoint();
        const auto beforeEnd = placement.previewEndPoint();

        QString error;
        QVERIFY(!placement.begin({}, 3, 15, 1, true, &error));
        QVERIFY(!error.isEmpty());
        QVERIFY(!placement.begin(other, 3, 0, 1, true, &error));
        QVERIFY(!placement.begin(other, 3, 15, 7, true, &error));
        QVERIFY(!placement.begin(other, 3, 15, 1, false, &error));
        QVERIFY(!placement.begin(other, 0, 15, 1, true, &error));
        QVERIFY(!placement.begin(other, 4, 15, 1, true, &error));
        QVERIFY(!placement.begin(other, 3, -1, 1, true, &error));
        QVERIFY(!placement.begin(other, 3, 1000001, 1, true, &error));
        auto library = std::make_shared<pt::BoardDocument>(*other);
        library->sourceContext = QStringLiteral("库预览");
        QVERIFY(!placement.begin(library, 3, 15, 1, true, &error));
        QCOMPARE(placement.state(), pt::TrackPlacementState::WaitingForEnd);
        QCOMPARE(placement.document(), document);
        QCOMPARE(placement.revision(), quint64(3));
        QCOMPARE(placement.startPoint(), beforeStart);
        QCOMPARE(placement.previewEndPoint(), beforeEnd);
    }

    void invalidGeometryKeepsStateAndPreview() {
        const auto document = board();
        pt::TrackPlacementSession placement = started(document);
        QString error;
        QVERIFY(!placement.setStart({0.5, 0}, &error));
        QVERIFY(placement.state() == pt::TrackPlacementState::WaitingForStart);
        QVERIFY(!placement.setStart({-1000001, 0}, &error));
        QVERIFY(placement.setStart({0, 0}, &error));
        QVERIFY(!placement.previewEnd({0, 0}, &error));
        QVERIFY(!placement.previewEnd({1.5, 0}, &error));
        QVERIFY(!placement.previewEnd({std::numeric_limits<qreal>::quiet_NaN(), 2}, &error));
        QVERIFY(!placement.previewEnd({0, std::numeric_limits<qreal>::infinity()}, &error));
        QVERIFY(!placement.previewEnd({1000001, 0}, &error));
        QVERIFY(placement.state() == pt::TrackPlacementState::WaitingForEnd);
        QVERIFY(!placement.previewEndPoint().has_value());
        QVERIFY(!placement.confirm(document, 1, true, &error).has_value());
        QVERIFY(placement.state() == pt::TrackPlacementState::WaitingForEnd);
        QVERIFY(placement.previewEnd({1, 2}, &error));
        QVERIFY(!placement.previewEnd({2.5, 3}, &error));
        QCOMPARE(placement.previewEndPoint(), std::optional<QPointF>(QPointF(1, 2)));
        QVERIFY(placement.setStart({-1, -2}));
        QVERIFY(!placement.previewEndPoint().has_value());
        QVERIFY(!placement.confirm(document, 1, true, &error).has_value());
        QVERIFY(placement.previewEnd({1, 2}, &error));
        QVERIFY(placement.confirm(document, 1, true, &error).has_value());
    }

    void contextChangeCancelsAndCannotReuseOldPreview() {
        const auto document = board(4);
        const auto other = board(4);
        QString error;
        pt::TrackPlacementSession placement = started(document, 4);
        QVERIFY(placement.setStart({1, 2}));
        QVERIFY(placement.previewEnd({3, 4}));
        QVERIFY(!placement.checkContext(other, 4, true));
        QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);
        QVERIFY(!placement.confirm(document, 4, true, &error).has_value());

        QVERIFY(placement.begin(document, 4, 15, 1, true));
        QVERIFY(placement.setStart({1, 2}));
        QVERIFY(placement.previewEnd({3, 4}));
        QVERIFY(!placement.checkContext(document, 5, true));
        QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);

        QVERIFY(placement.begin(document, 4, 15, 1, true));
        QVERIFY(placement.setStart({1, 2}));
        QVERIFY(placement.previewEnd({3, 4}));
        QVERIFY(!placement.checkContext(document, 4, false));
        QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);
    }

    void confirmRechecksEveryContextBoundary() {
        const auto document = board(4);
        for (int change = 0; change < 4; ++change) {
            auto placement = started(document, 4);
            QVERIFY(placement.setStart({1, 2}));
            QVERIFY(placement.previewEnd({3, 4}));
            const auto current = change == 0 ? board(4)
                : change == 3 ? std::shared_ptr<const pt::BoardDocument>{} : document;
            QString error;
            QVERIFY(!placement.confirm(current, change == 1 ? 5 : 4, change != 2, &error));
            QVERIFY(!error.isEmpty());
            QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);
            QVERIFY(!placement.confirm(document, 4, true));
        }

        pt::BoardEditSession edits;
        edits.reset(board());
        auto placement = started(edits.document(), edits.revision());
        QVERIFY(placement.setStart({1, 2}));
        QVERIFY(placement.previewEnd({3, 4}));
        QVERIFY(edits.addTrack({10, 10}, {20, 20}, 5, 6, edits.revision()));
        QVERIFY(!placement.confirm(edits.document(), edits.revision(), true));
        QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);
        QCOMPARE(edits.document()->tracks.size(), 1);
    }

    void integerMilBoundariesRemainExact() {
        const auto document = board();
        pt::TrackPlacementSession placement;
        for (const auto width : {1, 1000000}) {
            QVERIFY(placement.begin(document, 1, width, 6, true));
            QVERIFY(placement.setStart({-1000000, 1000000}));
            QVERIFY(placement.previewEnd({1000000, -1000000}));
            const auto request = placement.confirm(document, 1, true);
            QVERIFY(request);
            QCOMPARE(request->start, QPointF(-1000000, 1000000));
            QCOMPARE(request->end, QPointF(1000000, -1000000));
            QCOMPARE(request->width, width);
        }
    }

    void cancelIsIdempotentAndDoesNotTouchEditSession() {
        const auto source = board();
        pt::BoardEditSession edits;
        edits.reset(source);
        QVERIFY(edits.addTrack({10, 10}, {20, 20}, 5, 6, edits.revision()));
        edits.markSaved();
        QVERIFY(edits.undo());
        QVERIFY(edits.canRedo());
        const auto beforeDocument = edits.document();
        const auto beforeRevision = edits.revision();
        const auto beforeDirty = edits.dirty();
        const auto beforeUndo = edits.canUndo();
        const auto beforeRedo = edits.canRedo();
        const auto beforeCounts = edits.document()->recordCounts;

        pt::TrackPlacementSession placement;
        QVERIFY(placement.begin(beforeDocument, beforeRevision, 15, 1, true));
        placement.cancel();
        placement.cancel();
        QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);
        QVERIFY(placement.begin(beforeDocument, beforeRevision, 15, 1, true));
        QVERIFY(placement.setStart({1, 2}));
        QVERIFY(placement.previewEnd({3, 4}));
        QCOMPARE(edits.document(), beforeDocument);
        QCOMPARE(edits.revision(), beforeRevision);
        QCOMPARE(edits.dirty(), beforeDirty);
        QCOMPARE(edits.canUndo(), beforeUndo);
        QCOMPARE(edits.canRedo(), beforeRedo);
        QCOMPARE(edits.document()->recordCounts, beforeCounts);
        QCOMPARE(edits.document()->workingRevision, beforeRevision);
        QCOMPARE(edits.document()->embeddedNetlist, source->embeddedNetlist);
        placement.cancel();
        placement.cancel();
        QCOMPARE(placement.state(), pt::TrackPlacementState::Idle);
        QCOMPARE(edits.document(), beforeDocument);
        QCOMPARE(edits.revision(), beforeRevision);
        QCOMPARE(edits.dirty(), beforeDirty);
        QCOMPARE(edits.canUndo(), beforeUndo);
        QCOMPARE(edits.canRedo(), beforeRedo);
        QVERIFY(edits.redo());
        QCOMPARE(edits.document()->tracks.size(), 1);
        QVERIFY(!edits.dirty());
    }

    void requestCanBeSubmittedOnceAndUsesEditHistory() {
        auto source = std::make_shared<const pt::BoardDocument>();
        pt::BoardEditSession edits;
        edits.reset(source);
        const auto document = edits.document();
        pt::TrackPlacementSession placement;
        QVERIFY(placement.begin(document, edits.revision(), 15, 1, true));
        QVERIFY(placement.setStart({-10, 20}));
        QVERIFY(placement.previewEnd({30, 40}));
        const auto request = placement.confirm(edits.document(), edits.revision(), true);
        QVERIFY(request.has_value());
        QCOMPARE(request->document, document);

        QString error;
        QVERIFY(edits.addTrack(request->start, request->end, request->width, request->layer,
                               request->revision, &error));
        QVERIFY2(error.isEmpty(), qPrintable(error));
        QCOMPARE(edits.document()->tracks.size(), 1);
        QVERIFY(edits.document()->tracks[0].identity == pt::TrackIdentity::created(1));
        QVERIFY(edits.dirty());
        const auto changedRevision = edits.revision();
        QVERIFY(!edits.addTrack(request->start, request->end, request->width, request->layer,
                                request->revision, &error));
        QVERIFY(!error.isEmpty());
        QCOMPARE(edits.revision(), changedRevision);
        QVERIFY(edits.undo());
        QVERIFY(edits.document()->tracks.isEmpty());
        QVERIFY(edits.redo());
        QCOMPARE(edits.document()->tracks.size(), 1);
        QVERIFY(edits.document()->tracks[0].identity == pt::TrackIdentity::created(1));
        QVERIFY(!placement.confirm(edits.document(), edits.revision(), true, &error).has_value());
    }

    void cancelDoesNotConsumeEditIdentitySequence() {
        auto source = std::make_shared<const pt::BoardDocument>();
        pt::BoardEditSession edits;
        edits.reset(source);
        pt::TrackPlacementSession placement;
        placement.begin(edits.document(), edits.revision(), 15, 1, true);
        placement.setStart({1, 2});
        placement.cancel();
        QVERIFY(placement.state() == pt::TrackPlacementState::Idle);

        QVERIFY(placement.begin(edits.document(), edits.revision(), 15, 1, true));
        QVERIFY(placement.setStart({1, 2}));
        QVERIFY(placement.previewEnd({3, 4}));
        auto request = placement.confirm(edits.document(), edits.revision(), true);
        QVERIFY(request.has_value());
        QVERIFY(edits.addTrack(request->start, request->end, request->width, request->layer,
                               request->revision));
        QVERIFY(edits.document()->tracks[0].identity == pt::TrackIdentity::created(1));
    }
};

QTEST_APPLESS_MAIN(TrackPlacementTests)
#include "TrackPlacementTests.moc"
