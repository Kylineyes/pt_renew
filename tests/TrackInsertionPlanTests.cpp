#include "application/BoardEditSession.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbWriter.h"
#include "io/LegacyTrackInsertionPlanner.h"
#include <QCryptographicHash>
#include <QtTest/QTest>
#include <limits>

namespace {
const QByteArray header = "PCB FILE 4\n";
const QByteArray oldTrack = "FT\n1 -2 11 8 10 1 42\n";
const QByteArray component = "COMP\nENDPCB\nENDPCB\nENDPCB\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
    "CT\n0 0 100 0 12 1 9\nCP\n0 0 60 60 1 20 1 13\nENDPCB\n"
    "CS\n0 0 10 0 1 7\nENDPCB\nENDCOMP\n";
QByteArray net() { return "NETDEF\nGND\n[\ncontains ENDPCB\n]\n(\nENDPCB-1\n)\n"; }
QByteArray fixture() {
    return header + oldTrack + "FT\n200 0 300 50 12 6\n" + component + "FV\n500 600 30 10\nENDPCB\n";
}
pt::Track created(quint64 sequence = 1) {
    pt::Track result;
    result.start = {-100, 200}; result.end = {300, -400};
    result.width = 15; result.layer = 1; result.identity = pt::TrackIdentity::created(sequence);
    return result;
}
pt::PrimitiveId track(qsizetype index) { return {pt::PrimitiveKind::Track, index}; }
void rejected(const pt::LegacyTrackInsertionPlan& plan) {
    QVERIFY(!plan.succeeded());
    QVERIFY(!plan.error.isEmpty());
    QVERIFY(plan.baseBytes.isEmpty());
    QVERIFY(plan.createdTracks.isEmpty());
    QCOMPARE(plan.insertionByteOffset, -1);
    QCOMPARE(plan.baseLayout.endPcbOffset, -1);
    QVERIFY(plan.baseLayout.topLevelRecords.isEmpty());
    QVERIFY(!plan.baseLayout.insertion.isValid());
}
}

class TrackInsertionPlanTests final : public QObject {
    Q_OBJECT
private slots:
    void creationThenOldEditsUseBaseOffsets() {
        const auto original = pt::LegacyPcbReader::parse(fixture(), QStringLiteral("不存在的冻结输入.pcb")).document;
        QVERIFY(original);
        const auto originalLayout = pt::LegacyPcbReader::parseWithLayout(fixture()).layout;
        pt::BoardEditSession session; session.reset(original);
        QVERIFY(session.addTrack({-10, 20}, {30, 40}, 15, 6, session.revision()));
        QVERIFY(session.moveTrack(track(0), session.revision(), {100000, -9999}));
        QVERIFY(session.deleteTrack(track(1), session.revision()));
        const auto snapshot = session.document(); const auto revision = session.revision();
        const auto plan = pt::LegacyTrackInsertionPlanner::prepare(*original, *snapshot);
        QVERIFY2(plan.succeeded(), qPrintable(plan.error));
        QByteArray expected = fixture();
        expected.replace("1 -2 11 8 10 1 42", "100001 -10001 100011 -9991 10 1 42");
        expected.replace("FT\n200 0 300 50 12 6\n", "");
        QCOMPARE(plan.baseBytes, expected);
        QCOMPARE(plan.insertionByteOffset, expected.size() - qsizetype(QByteArray("ENDPCB\n").size()));
        QVERIFY(plan.insertionByteOffset != originalLayout.insertion.byteOffset);
        QCOMPARE(plan.baseLayout.sourceByteSize, expected.size());
        QCOMPARE(plan.baseLayout.insertion.byteOffset, plan.insertionByteOffset);
        QCOMPARE(plan.baseLayout.insertion.kind, pt::LegacyPcbInsertionKind::BeforeEndPcb);
        QCOMPARE(plan.createdTracks.size(), 1);
        QCOMPARE(plan.createdTracks[0].identity, snapshot->tracks.back().identity);
        QCOMPARE(plan.createdTracks[0].start, QPointF(-10, 20));
        QCOMPARE(plan.createdTracks[0].layer, 6);
        QVERIFY(!plan.baseLayout.originalSoftwareInsertionVerified);
        QVERIFY(!plan.baseLayout.unverifiedReasons.isEmpty());
        const auto base = pt::LegacyPcbReader::parse(plan.baseBytes);
        QVERIFY(base.succeeded()); QCOMPARE(base.document->tracks.size(), 2);
        QVERIFY(!pt::LegacyPcbWriter::prepare(*original, *snapshot).succeeded());
        QCOMPARE(original->sourceBytes, fixture());
        QCOMPARE(snapshot->sourceBytes, fixture());
        QCOMPARE(session.document(), snapshot); QCOMPARE(session.revision(), revision);
        QVERIFY(session.dirty());
    }

    void creationOrderAllowsGapsAndExtremeGeometry() {
        const auto original = pt::LegacyPcbReader::parse(header + "ENDPCB").document;
        QVERIFY(original);
        auto current = *original;
        auto first = created(2); first.start = {-1000000, 1000000}; first.end = {1000000, -1000000};
        first.width = 1000000; first.layer = 6;
        auto second = created(std::numeric_limits<quint64>::max()); second.width = 1;
        current.tracks = {first, second};
        const auto plan = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        QVERIFY2(plan.succeeded(), qPrintable(plan.error));
        QCOMPARE(plan.baseBytes, original->sourceBytes);
        QCOMPARE(plan.insertionByteOffset, header.size());
        QCOMPARE(plan.createdTracks.size(), 2);
        QCOMPARE(plan.createdTracks[0].identity, first.identity);
        QCOMPARE(plan.createdTracks[1].identity, second.identity);
        QCOMPARE(plan.createdTracks[0].width, 1000000);
        QCOMPARE(plan.createdTracks[1].width, 1);
        QVERIFY(plan.baseLayout.insertion.anchorLineEnding.isEmpty());
        QVERIFY(!plan.baseLayout.newlines.textEndsWithNewline);
    }

    void invalidNewRecords_data() {
        QTest::addColumn<QString>("mode");
        for (const auto* mode : {"zero-id", "duplicate-id", "decreasing-id", "loaded-after-created", "unassigned", "unknown-kind",
                "source-line", "negative-line", "source-offset", "negative-offset", "component", "invalid-component", "extra",
                "fraction-start", "fraction-end", "negative-limit", "positive-limit", "nan", "infinite-start", "infinite-end",
                "zero-width", "negative-width", "large-width", "other-layer", "zero-layer", "zero-length"})
            QTest::newRow(mode) << QString::fromLatin1(mode);
    }
    void invalidNewRecords() {
        QFETCH(QString, mode);
        const auto original = pt::LegacyPcbReader::parse(fixture()).document; QVERIFY(original);
        auto current = *original; auto item = created();
        if (mode == "zero-id") item.identity.value = 0;
        if (mode == "unassigned") item.identity = {};
        if (mode == "unknown-kind") item.identity.kind = static_cast<pt::TrackIdentity::Kind>(99);
        if (mode == "source-line") item.source.line = original->tracks[0].source.line;
        if (mode == "negative-line") item.source.line = -1;
        if (mode == "source-offset") item.source.byteOffset = 0;
        if (mode == "negative-offset") item.source.byteOffset = -2;
        if (mode == "component") item.source.component = 0;
        if (mode == "invalid-component") item.source.component = -2;
        if (mode == "extra") item.extra = 0;
        if (mode == "fraction-start") item.start.setX(.5);
        if (mode == "fraction-end") item.end.setY(-.5);
        if (mode == "negative-limit") item.start.setY(-1000001);
        if (mode == "positive-limit") item.end.setX(1000001);
        if (mode == "nan") item.start.setX(std::numeric_limits<qreal>::quiet_NaN());
        if (mode == "infinite-start") item.start.setY(-std::numeric_limits<qreal>::infinity());
        if (mode == "infinite-end") item.end.setY(std::numeric_limits<qreal>::infinity());
        if (mode == "zero-width") item.width = 0;
        if (mode == "negative-width") item.width = -1;
        if (mode == "large-width") item.width = 1000001;
        if (mode == "other-layer") item.layer = 7;
        if (mode == "zero-layer") item.layer = 0;
        if (mode == "zero-length") item.end = item.start;
        current.tracks.append(item);
        if (mode == "duplicate-id") current.tracks.append(item);
        if (mode == "decreasing-id") { current.tracks.back().identity.value = 5; current.tracks.append(created(3)); }
        if (mode == "loaded-after-created") current.tracks.append(current.tracks.takeFirst());
        rejected(pt::LegacyTrackInsertionPlanner::prepare(*original, current));
        QCOMPARE(current.sourceBytes, fixture());
    }

    void oldRecordRestrictionsRemainInForce_data() {
        QTest::addColumn<QString>("mode");
        for (const auto* mode : {"width", "layer", "extra", "shape", "offset", "line", "component", "identity", "unassigned",
                "reclassified", "duplicate", "reorder", "component-move", "component-delete", "via", "pad", "text", "component-field",
                "source-bytes", "digest", "byte-size", "record-counts", "file-path", "library"})
            QTest::newRow(mode) << QString::fromLatin1(mode);
    }
    void oldRecordRestrictionsRemainInForce() {
        QFETCH(QString, mode);
        const auto original = pt::LegacyPcbReader::parse(fixture()).document; QVERIFY(original);
        auto current = *original;
        if (mode == "width") ++current.tracks[0].width;
        if (mode == "layer") current.tracks[0].layer = 6;
        if (mode == "extra") current.tracks[0].extra = 0;
        if (mode == "shape") current.tracks[0].end += QPointF(1, 0);
        if (mode == "offset") current.tracks[0].source.byteOffset = 0;
        if (mode == "line") current.tracks[0].source.line = current.tracks[1].source.line;
        if (mode == "component") current.tracks[0].source.component = 0;
        if (mode == "identity") ++current.tracks[0].identity.value;
        if (mode == "unassigned") current.tracks[0].identity = {};
        if (mode == "reclassified") current.tracks[0].identity = pt::TrackIdentity::created(9);
        if (mode == "duplicate") current.tracks.insert(1, current.tracks[0]);
        if (mode == "reorder") current.tracks.swapItemsAt(0, 1);
        if (mode == "component-move") { current.tracks[2].start += QPointF(1, 1); current.tracks[2].end += QPointF(1, 1); }
        if (mode == "component-delete") current.tracks.removeAt(2);
        if (mode == "via") current.vias[0].diameter = 50;
        if (mode == "pad") current.pads[0].name = QStringLiteral("篡改");
        if (mode == "text") current.texts[0].value = QStringLiteral("篡改");
        if (mode == "component-field") current.components[0].designator = QStringLiteral("篡改");
        if (mode == "source-bytes") current.sourceBytes.append('\n');
        if (mode == "digest") current.sha256 = QStringLiteral("篡改");
        if (mode == "byte-size") ++current.byteSize;
        if (mode == "record-counts") ++current.recordCounts[QStringLiteral("FT")];
        if (mode == "file-path") current.filePath = QStringLiteral("篡改.pcb");
        if (mode == "library") current.sourceContext = QStringLiteral("库预览");
        current.tracks.append(created());
        rejected(pt::LegacyTrackInsertionPlanner::prepare(*original, current));
    }

    void forgedOriginalCannotAuthorizeCreatedIdentity_data() {
        QTest::addColumn<QString>("mode");
        for (const auto* mode : {"created", "unassigned", "loaded-id", "loaded-width", "counts", "digest"})
            QTest::newRow(mode) << QString::fromLatin1(mode);
    }
    void forgedOriginalCannotAuthorizeCreatedIdentity() {
        QFETCH(QString, mode);
        auto original = *pt::LegacyPcbReader::parse(fixture()).document;
        if (mode == "created") { original.tracks[0] = created(7); }
        if (mode == "unassigned") original.tracks[0].identity = {};
        if (mode == "loaded-id") ++original.tracks[0].identity.value;
        if (mode == "loaded-width") ++original.tracks[0].width;
        if (mode == "counts") original.recordCounts.clear();
        if (mode == "digest") original.sha256 = QStringLiteral("伪造");
        auto current = original;
        if (mode == "created") current.tracks.removeFirst();
        current.tracks.append(created(8));
        rejected(pt::LegacyTrackInsertionPlanner::prepare(original, current));
    }

    void netdefPolicies_data() {
        QTest::addColumn<QByteArray>("input"); QTest::addColumn<bool>("interleaved");
        QTest::newRow("tail") << (header + oldTrack + net() + "ENDPCB\n") << false;
        QTest::newRow("interleaved-track") << (header + net() + oldTrack + "ENDPCB\n") << true;
        QTest::newRow("interleaved-component") << (header + net() + component + "ENDPCB\n") << true;
    }
    void netdefPolicies() {
        QFETCH(QByteArray, input); QFETCH(bool, interleaved);
        const auto original = pt::LegacyPcbReader::parse(input).document; QVERIFY(original);
        // 无新增时仍可预检既有受限操作，不因新增插入策略收窄原 writer 的能力。
        auto current = *original;
        const auto unchanged = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        QVERIFY2(unchanged.succeeded(), qPrintable(unchanged.error));
        QCOMPARE(unchanged.baseBytes, input); QCOMPARE(unchanged.insertionByteOffset, -1);
        QVERIFY(unchanged.createdTracks.isEmpty());
        QCOMPARE(unchanged.baseLayout.geometryAfterNetdef, interleaved);
        current.tracks.append(created());
        const auto plan = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        rejected(plan);
        QVERIFY(plan.error.contains(interleaved ? QStringLiteral("交错") : QStringLiteral("尚未验证")));
        // 内嵌网表即使没有新增，也继续受旧 writer 的不可修改保护。
        current = *original;
        auto changedNet = std::make_shared<pt::Netlist>(*current.embeddedNetlist);
        changedNet->nets[0].name = QStringLiteral("篡改"); current.embeddedNetlist = changedNet;
        rejected(pt::LegacyTrackInsertionPlanner::prepare(*original, current));
    }

    void syntaxFactsPreserveBytesWithoutChoosingEncoding_data() {
        QTest::addColumn<QByteArray>("ending");
        QTest::newRow("no-final-newline") << QByteArray(" \tENDPCB \t");
        QTest::newRow("dos-eof") << QByteArray(" \tENDPCB \t\x1a \r\n\t");
        QTest::newRow("crlf-dos-eof") << QByteArray(" \tENDPCB \t\r\n\n\x1a\t");
    }
    void syntaxFactsPreserveBytesWithoutChoosingEncoding() {
        QFETCH(QByteArray, ending);
        const QByteArray prefix = "PCB FILE 4\r\n\n \tFT \n\t1  -2\t11 8 10 1 42\r\n" + component
            + "FS\r\n0 0 10 0 1 7\nENDPCB\nFS\n0 0 10 0 1 7\r\n" + QByteArray::fromHex("81") + "\n\n";
        const QByteArray input = prefix + ending;
        const auto original = pt::LegacyPcbReader::parse(input).document; QVERIFY(original);
        auto current = *original; current.tracks.append(created());
        const auto plan = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        QVERIFY2(plan.succeeded(), qPrintable(plan.error));
        QCOMPARE(plan.baseBytes, input);
        QCOMPARE(plan.insertionByteOffset, prefix.size());
        QCOMPARE(plan.baseBytes.mid(plan.insertionByteOffset), ending);
        QVERIFY(plan.baseLayout.newlines.mixed());
        QCOMPARE(plan.baseLayout.topLevelRecords.back().tag, QByteArray("ENDPCB"));
        QCOMPARE(plan.baseLayout.topLevelRecords.back().beginOffset, prefix.size());
        QCOMPARE(plan.baseLayout.topLevelRecords[1].tag, QByteArray("COMP"));
        QVERIFY(!plan.baseLayout.originalSoftwareInsertionVerified);
        QCOMPARE(original->sourceBytes, input);
        QCOMPARE(original->sha256, QString::fromLatin1(QCryptographicHash::hash(input, QCryptographicHash::Sha256).toHex()));
        current.tracks.removeLast();
        const auto noNew = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        QVERIFY(noNew.succeeded()); QCOMPARE(noNew.insertionByteOffset, -1); QCOMPARE(noNew.baseBytes, input);
        current.tracks[0].start += QPointF(10, 20); current.tracks[0].end += QPointF(10, 20);
        QByteArray moved = input; moved.replace("\t1  -2\t11 8", "\t11  18\t21 28");
        const auto noNewMoved = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        QVERIFY2(noNewMoved.succeeded(), qPrintable(noNewMoved.error));
        QCOMPARE(noNewMoved.baseBytes, moved); QCOMPARE(noNewMoved.insertionByteOffset, -1);
    }

    void malformedFrozenBytesNeverExposePartialPlan_data() {
        QTest::addColumn<QByteArray>("input");
        QTest::newRow("bad-field") << (header + oldTrack + "FV\n0 0 bad 0\nENDPCB\n");
        QTest::newRow("unclosed-component") << (header + oldTrack + "COMP\nU1\nDIP\ncomment\n");
        QTest::newRow("after-end") << (header + oldTrack + "ENDPCB\n" + oldTrack);
        QTest::newRow("after-eof") << (header + oldTrack + "ENDPCB\n\x1a" "BAD");
        QTest::newRow("missing-end") << (header + oldTrack);
    }
    void malformedFrozenBytesNeverExposePartialPlan() {
        QFETCH(QByteArray, input);
        pt::BoardDocument original;
        original.sourceBytes = input; original.byteSize = input.size();
        original.sha256 = QString::fromLatin1(QCryptographicHash::hash(input, QCryptographicHash::Sha256).toHex());
        auto current = original; current.tracks.append(created());
        rejected(pt::LegacyTrackInsertionPlanner::prepare(original, current));
    }

    void syntaxRecordLimitCountsComponentsInternalRecordsAndEndPcb() {
        // 199994 个过孔 + COMP/CT/ENDCOMP + 自由 FT + ENDPCB = 199999 条真实语法记录。
        const QByteArray capComponent = "COMP\nU1\nDIP\ncomment\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
            "CT\n0 0 10 0 1 1\nENDCOMP\n";
        const QByteArray input = header + capComponent + oldTrack + QByteArray("FV\n0 0 2 0\n").repeated(199994) + "ENDPCB\n";
        const auto original = pt::LegacyPcbReader::parse(input).document; QVERIFY(original);
        QCOMPARE(original->recordCounts.value(QStringLiteral("FV")), 199994);
        QCOMPARE(original->recordCounts.value(QStringLiteral("COMP")), 1);
        QCOMPARE(original->recordCounts.value(QStringLiteral("ENDCOMP")), 1);
        QCOMPARE(original->recordCounts.value(QStringLiteral("CT")), 1);
        auto current = *original; current.tracks.append(created());
        const auto atLimit = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        QVERIFY2(atLimit.succeeded(), qPrintable(atLimit.error));
        QCOMPARE(atLimit.baseBytes, input); QCOMPARE(atLimit.createdTracks.size(), 1);
        QCOMPARE(atLimit.insertionByteOffset, input.size() - 7);
        current.tracks.append(created(4));
        const auto overLimit = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        rejected(overLimit); QVERIFY(overLimit.error.contains(QStringLiteral("200000")));
        // 删除原 FT 后释放一条真实记录容量，两条新段恰好到上限，第三条仍拒绝。
        current.tracks.removeAt(1);
        const auto afterDelete = pt::LegacyTrackInsertionPlanner::prepare(*original, current);
        QVERIFY2(afterDelete.succeeded(), qPrintable(afterDelete.error));
        QByteArray deletedInput = input; deletedInput.replace(oldTrack, "");
        QCOMPARE(afterDelete.baseBytes, deletedInput);
        QCOMPARE(afterDelete.createdTracks.size(), 2);
        QCOMPARE(afterDelete.insertionByteOffset, deletedInput.size() - 7);
        current.tracks.append(created(5));
        rejected(pt::LegacyTrackInsertionPlanner::prepare(*original, current));
        QCOMPARE(original->sourceBytes, input);
        // reader 的真实边界与预检相符，ENDPCB 是上限中的一条记录。
        const QByteArray fullInput = input.left(input.size() - 7) + "FV\n0 0 2 0\nENDPCB\n";
        const auto full = pt::LegacyPcbReader::parse(fullInput); QVERIFY(full.succeeded());
        auto fullCurrent = *full.document; fullCurrent.tracks.append(created());
        rejected(pt::LegacyTrackInsertionPlanner::prepare(*full.document, fullCurrent));
        QVERIFY(!pt::LegacyPcbReader::parse(fullInput.left(fullInput.size() - 7) + "FV\n0 0 2 0\nENDPCB\n").succeeded());
    }
};

QTEST_APPLESS_MAIN(TrackInsertionPlanTests)
#include "TrackInsertionPlanTests.moc"
