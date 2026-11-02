#include "application/BoardEditSession.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbWriter.h"
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QTemporaryDir>
#include <QtTest/QTest>
#include <limits>

namespace {
using Codec = pt::LegacyFreeTrackCodec;
using Writer = pt::LegacyPcbWriter;
const QByteArray header = "PCB FILE 4\n";
const QByteArray oldTrack = " FT \r\n\t+00100  100\t400 500  10\t1  +0042 \r\n";
const QByteArray secondTrack = "FT\n600 100 900 100 12 6\n";
const QByteArray component = "COMP\nENDPCB\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
    "CT\n0 0 100 0 10 1 9\nCP\n100 100 60 60 1 20 1 13\nENDPCB\nENDCOMP\n";
QByteArray net() { return "NETDEF\nGND\n[\nmetadata ENDPCB\n]\n(\nENDPCB-1\n)\n"; }
QByteArray fixture() {
    return header + "\r\n" + oldTrack + secondTrack + component
        + "FP\n100 100 60 80 1 20 1 13\nPin\nFV\n300 400 40 20\n"
          "FA\n100 100 50 5 10 7\nFF\n30 40 10 20 6\nFS\n100 200 60 17 10 7\nOpaque \x82\n"
          " \t\r\n ENDPCB \r\n\x1a \t\r\n";
}
Codec::Options six() { return {Codec::FieldLayout::SixFields, Codec::LineEnding::Lf, {}}; }
pt::Track created(quint64 sequence = 1) {
    return {{-100, 200}, {300, -400}, 15, 6, {}, {}, pt::TrackIdentity::created(sequence)};
}
pt::PrimitiveId track(qsizetype index) { return {pt::PrimitiveKind::Track, index}; }
void rejected(const pt::BoardWriteResult& result) {
    QVERIFY(!result.succeeded()); QVERIFY(!result.error.isEmpty());
    QVERIFY(result.bytes.isEmpty()); QVERIFY(result.sha256.isEmpty()); QVERIFY(result.filePath.isEmpty());
}
bool writeFile(const QString& path, const QByteArray& bytes) {
    QFile file(path); return file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size();
}
QByteArray readFile(const QString& path) {
    QFile file(path); if (!file.open(QIODevice::ReadOnly)) return {}; return file.readAll();
}
QByteArray paddedBoard(qsizetype size) {
    QByteArray bytes = header + oldTrack;
    const auto padding = size - bytes.size() - 7;
    const QByteArray line = QByteArray(65535, ' ') + '\n';
    bytes += line.repeated(padding / line.size());
    const auto remainder = padding % line.size();
    if (remainder) bytes += QByteArray(remainder - 1, ' ') + '\n';
    return bytes + "ENDPCB\n";
}
}

class TrackCreatedWritingTests final : public QObject {
    Q_OBJECT
private slots:
    void explicitEncodingRoundTrips_data() {
        QTest::addColumn<bool>("seven"); QTest::addColumn<bool>("crlf"); QTest::addColumn<int>("extra");
        QTest::newRow("six-lf") << false << false << 0;
        QTest::newRow("six-crlf") << false << true << 0;
        QTest::newRow("seven-lf-zero") << true << false << 0;
        QTest::newRow("seven-crlf-negative") << true << true << -42;
        QTest::newRow("seven-min") << true << false << std::numeric_limits<int>::min();
        QTest::newRow("seven-max") << true << true << std::numeric_limits<int>::max();
    }
    void explicitEncodingRoundTrips() {
        QFETCH(bool, seven); QFETCH(bool, crlf); QFETCH(int, extra);
        const QByteArray input = "PCB FILE 4\r\n\nENDPCB\x1a \r\n";
        const auto original = pt::LegacyPcbReader::parse(input).document; QVERIFY(original);
        auto current = *original; current.tracks.append(created(2));
        const Codec::Options options{seven ? Codec::FieldLayout::SevenFields : Codec::FieldLayout::SixFields,
            crlf ? Codec::LineEnding::CrLf : Codec::LineEnding::Lf, seven ? std::optional<int>(extra) : std::nullopt};
        const auto result = Writer::prepareWithCreated(*original, current, options);
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        const QByteArray newline = crlf ? "\r\n" : "\n";
        const QByteArray record = "FT" + newline + "-100 200 300 -400 15 6"
            + (seven ? QByteArray(" ") + QByteArray::number(extra) : QByteArray{}) + newline;
        QCOMPARE(result.bytes, QByteArray("PCB FILE 4\r\n\n") + record + "ENDPCB\x1a \r\n");
        QCOMPARE(result.sha256, QString::fromLatin1(QCryptographicHash::hash(result.bytes, QCryptographicHash::Sha256).toHex()));
        const auto reopened = pt::LegacyPcbReader::parseWithLayout(result.bytes); QVERIFY(reopened.succeeded());
        QCOMPARE(reopened.document->tracks.size(), 1);
        const auto& output = reopened.document->tracks[0];
        QCOMPARE(output.start, current.tracks[0].start); QCOMPARE(output.end, current.tracks[0].end);
        QCOMPARE(output.width, 15); QCOMPARE(output.layer, 6);
        QCOMPARE(output.extra, options.extra); QCOMPARE(output.source.line, 3);
        QCOMPARE(output.source.component, -1); QCOMPARE(output.source.byteOffset, -1);
        QCOMPARE(output.identity, pt::TrackIdentity::loaded(3));
        QCOMPARE(reopened.layout.topLevelRecords[0].beginOffset, qsizetype(13));
        QVERIFY(!reopened.layout.originalSoftwareInsertionVerified);
        QCOMPARE(current.tracks[0].identity, pt::TrackIdentity::created(2)); QVERIFY(!current.tracks[0].extra);
        QCOMPARE(current.sourceBytes, input); QCOMPARE(original->sourceBytes, input);
        rejected(Writer::prepare(*original, current));
    }

    void rejectsMissingOrContradictoryOptions_data() {
        QTest::addColumn<int>("mode");
        for (int i = 0; i != 8; ++i) QTest::newRow(qPrintable(QString::number(i))) << i;
    }
    void rejectsMissingOrContradictoryOptions() {
        QFETCH(int, mode);
        const auto original = pt::LegacyPcbReader::parse(header + "ENDPCB").document; QVERIFY(original);
        auto current = *original; current.tracks.append(created()); auto options = six();
        if (mode == 0) options = {};
        if (mode == 1) options.fields = Codec::FieldLayout::Unspecified;
        if (mode == 2) options.lineEnding = Codec::LineEnding::Unspecified;
        if (mode == 3) options.fields = Codec::FieldLayout::SevenFields;
        if (mode == 4) options.extra = 0;
        if (mode == 5) options.fields = static_cast<Codec::FieldLayout>(99);
        if (mode == 6) options.lineEnding = static_cast<Codec::LineEnding>(99);
        if (mode == 7) { options.fields = Codec::FieldLayout::SevenFields; options.extra = 42; options.lineEnding = {}; }
        rejected(Writer::prepareWithCreated(*original, current, options));
    }

    void mixedEditsHistoryAndSnapshotsPreserveOldBytes() {
        const auto original = pt::LegacyPcbReader::parse(fixture(), QStringLiteral("冻结输入.pcb")).document; QVERIFY(original);
        pt::BoardEditSession session; session.reset(original);
        QVERIFY(session.addTrack({-10, 20}, {30, 40}, 15, 6, session.revision()));
        const auto addedSnapshot = session.document();
        QVERIFY(session.moveTrack(track(0), session.revision(), {100000, -9999}));
        QVERIFY(session.deleteTrack(track(1), session.revision()));
        QVERIFY(session.addTrack({5, 6}, {7, 8}, 1, 1, session.revision()));
        QVERIFY(session.moveTrack(track(2), session.revision(), {2, -3}));
        const auto snapshot = session.document(); const auto revision = session.revision();
        const auto result = Writer::prepareWithCreated(*original, *snapshot, six());
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        auto expected = fixture();
        expected.replace("\t+00100  100\t400 500", "\t100100  -9899\t100400 -9499");
        expected.replace(secondTrack, "");
        expected.replace(" ENDPCB \r\n\x1a", "FT\n-8 17 32 37 15 6\nFT\n5 6 7 8 1 1\n ENDPCB \r\n\x1a");
        QCOMPARE(result.bytes, expected);
        const auto reopened = pt::LegacyPcbReader::parse(result.bytes); QVERIFY(reopened.succeeded());
        QCOMPARE(reopened.document->tracks.size(), 4);
        // 删除 FT 后，元件内 CT 的行身份须跟随输出实际前移。
        QCOMPARE(reopened.document->tracks[1].identity, pt::TrackIdentity::loaded(original->tracks[2].source.line - 2));
        QCOMPARE(reopened.document->tracks[1].source.component, 0);
        QCOMPARE(reopened.document->tracks[0].extra, std::optional<int>(42));
        QCOMPARE(session.document(), snapshot); QCOMPARE(session.revision(), revision); QVERIFY(session.dirty());
        QVERIFY(session.undo()); QVERIFY(session.undo()); QVERIFY(session.undo()); QVERIFY(session.undo());
        QCOMPARE(session.document()->tracks.back().identity, addedSnapshot->tracks.back().identity);
        QCOMPARE(Writer::prepareWithCreated(*original, *session.document(), six()).bytes,
            Writer::prepareWithCreated(*original, *addedSnapshot, six()).bytes);
        QVERIFY(session.undo()); QCOMPARE(Writer::prepareWithCreated(*original, *session.document(), {}).bytes, fixture());
        for (int i = 0; i != 5; ++i) QVERIFY(session.redo());
        QCOMPARE(Writer::prepareWithCreated(*original, *session.document(), six()).bytes, result.bytes);
        QCOMPARE(Writer::prepareWithCreated(*original, *snapshot, six()).bytes, result.bytes);
        QCOMPARE(original->sourceBytes, fixture()); QCOMPARE(addedSnapshot->tracks[0].start, QPointF(100, 100));
    }

    void multipleCreatedIdentitiesMapInSequenceOrder() {
        const auto original = pt::LegacyPcbReader::parse(header + "ENDPCB").document; QVERIFY(original);
        auto current = *original;
        auto first = created(2); auto second = created(5); auto last = created(std::numeric_limits<quint64>::max());
        second.start = {-1000000, 1000000}; second.end = {1000000, -1000000}; second.width = 1000000; second.layer = 1;
        current.tracks = {first, second, last};
        const auto result = Writer::prepareWithCreated(*original, current, six()); QVERIFY2(result.succeeded(), qPrintable(result.error));
        const auto reopened = pt::LegacyPcbReader::parse(result.bytes); QVERIFY(reopened.succeeded());
        for (qsizetype i = 0; i != 3; ++i) {
            QCOMPARE(reopened.document->tracks[i].identity, pt::TrackIdentity::loaded(2 + 2 * i));
            QCOMPARE(reopened.document->tracks[i].start, current.tracks[i].start);
            QCOMPARE(reopened.document->tracks[i].end, current.tracks[i].end);
            QCOMPARE(reopened.document->tracks[i].width, current.tracks[i].width);
            QCOMPARE(reopened.document->tracks[i].layer, current.tracks[i].layer);
        }
        // 相同几何也保留不同身份和创建顺序，不能按几何去重。
        QCOMPARE(reopened.document->tracks[0].start, reopened.document->tracks[2].start);
    }

    void rejectsForgedCreatedAndUnsupportedEdits_data() {
        QTest::addColumn<QString>("mode");
        for (const auto* mode : {"zero-id", "duplicate", "decreasing", "loaded-after-created", "unassigned", "unknown-kind",
                "source-line", "source-offset", "component", "created-extra", "fraction", "nan", "infinite", "limit",
                "zero-length", "width", "layer", "loaded-id", "loaded-source", "loaded-shape", "loaded-width", "loaded-extra",
                "loaded-layer", "loaded-reorder", "component-move", "component-delete", "pad", "via", "arc", "fill", "text",
                "component-value", "bytes", "hash", "path", "size", "counts", "library"})
            QTest::newRow(mode) << QString::fromLatin1(mode);
    }
    void rejectsForgedCreatedAndUnsupportedEdits() {
        QFETCH(QString, mode);
        const auto original = pt::LegacyPcbReader::parse(fixture()).document; QVERIFY(original);
        auto current = *original; current.tracks.append(created()); auto& added = current.tracks.last();
        if (mode == "zero-id") added.identity = pt::TrackIdentity::created(0);
        if (mode == "duplicate") current.tracks.append(created());
        if (mode == "decreasing") { added.identity = pt::TrackIdentity::created(2); current.tracks.append(created()); }
        if (mode == "loaded-after-created") current.tracks.swapItemsAt(0, 3);
        if (mode == "unassigned") added.identity = {};
        if (mode == "unknown-kind") added.identity.kind = static_cast<pt::TrackIdentity::Kind>(99);
        if (mode == "source-line") added.source.line = original->tracks[0].source.line;
        if (mode == "source-offset") added.source.byteOffset = 0;
        if (mode == "component") added.source.component = 0;
        if (mode == "created-extra") added.extra = 42;
        if (mode == "fraction") added.start.setX(0.5);
        if (mode == "nan") added.start.setX(std::numeric_limits<qreal>::quiet_NaN());
        if (mode == "infinite") added.end.setY(std::numeric_limits<qreal>::infinity());
        if (mode == "limit") added.end.setX(1000001);
        if (mode == "zero-length") added.end = added.start;
        if (mode == "width") added.width = 0;
        if (mode == "layer") added.layer = 2;
        if (mode == "loaded-id") current.tracks[0].identity = pt::TrackIdentity::created(99);
        if (mode == "loaded-source") ++current.tracks[0].source.byteOffset;
        if (mode == "loaded-shape") current.tracks[0].end += QPointF(1, 0);
        if (mode == "loaded-width") ++current.tracks[0].width;
        if (mode == "loaded-extra") current.tracks[0].extra = 7;
        if (mode == "loaded-layer") current.tracks[0].layer = 6;
        if (mode == "loaded-reorder") current.tracks.swapItemsAt(0, 1);
        if (mode == "component-move") { current.tracks[2].start += QPointF(1, 0); current.tracks[2].end += QPointF(1, 0); }
        if (mode == "component-delete") current.tracks.removeAt(2);
        if (mode == "pad") ++current.pads[0].width;
        if (mode == "via") ++current.vias[0].diameter;
        if (mode == "arc") ++current.arcs[0].quadrants;
        if (mode == "fill") current.fills[0].rectangle.translate(1, 0);
        if (mode == "text") current.texts[0].value = QStringLiteral("改写");
        if (mode == "component-value") current.components[0].comment = QStringLiteral("改写");
        if (mode == "bytes") current.sourceBytes += ' ';
        if (mode == "hash") current.sha256 = QStringLiteral("伪造");
        if (mode == "path") current.filePath = QStringLiteral("其他.pcb");
        if (mode == "size") ++current.byteSize;
        if (mode == "counts") ++current.recordCounts[QStringLiteral("FT")];
        if (mode == "library") current.sourceContext = QStringLiteral("库预览");
        rejected(Writer::prepareWithCreated(*original, current, six()));
    }

    void netdefRefusedWithCreatedAndPreservedWithoutCreated_data() {
        QTest::addColumn<QByteArray>("input");
        QTest::newRow("trailing") << (header + oldTrack + net() + "ENDPCB\n");
        QTest::newRow("interleaved") << (header + net() + oldTrack + "ENDPCB\n");
    }
    void netdefRefusedWithCreatedAndPreservedWithoutCreated() {
        QFETCH(QByteArray, input);
        const auto original = pt::LegacyPcbReader::parse(input).document; QVERIFY(original);
        auto current = *original; current.tracks.append(created());
        const auto refused = Writer::prepareWithCreated(*original, current, six()); rejected(refused);
        QVERIFY(refused.error.contains(QStringLiteral("NETDEF")));
        current.tracks.removeLast(); current.tracks[0].start += QPointF(1, 0); current.tracks[0].end += QPointF(1, 0);
        const auto explicitResult = Writer::prepareWithCreated(*original, current, {});
        const auto legacyResult = Writer::prepare(*original, current);
        QVERIFY2(explicitResult.succeeded(), qPrintable(explicitResult.error)); QCOMPARE(explicitResult.bytes, legacyResult.bytes);
        QVERIFY(explicitResult.bytes.contains(net()));
        auto changedNet = std::make_shared<pt::Netlist>(*current.embeddedNetlist);
        changedNet->nets[0].metadata = QByteArray("篡改"); current.embeddedNetlist = changedNet;
        rejected(Writer::prepareWithCreated(*original, current, six()));
    }

    void malformedOrForgedOriginalRejected_data() {
        QTest::addColumn<QByteArray>("input");
        QTest::newRow("unsupported") << (header + "FX\n0 0\nENDPCB\n");
        QTest::newRow("missing-end") << (header + oldTrack);
        QTest::newRow("after-eof") << (header + "ENDPCB\n\x1a" "BAD");
        QTest::newRow("malformed") << (header + "FT\n0 0 1 1 X 1\nENDPCB\n");
    }
    void malformedOrForgedOriginalRejected() {
        QFETCH(QByteArray, input);
        pt::BoardDocument original; original.sourceBytes = input; original.byteSize = input.size();
        original.sha256 = QString::fromLatin1(QCryptographicHash::hash(input, QCryptographicHash::Sha256).toHex());
        auto current = original; current.tracks.append(created()); rejected(Writer::prepareWithCreated(original, current, six()));
    }
    void frozenSnapshotMustMatchOriginalBytes() {
        const auto original = pt::LegacyPcbReader::parse(fixture()).document; QVERIFY(original);
        for (int mode = 0; mode != 5; ++mode) {
            auto forged = *original;
            if (mode == 0) forged.tracks[0].identity = pt::TrackIdentity::created(1);
            if (mode == 1) ++forged.tracks[0].source.line;
            if (mode == 2) ++forged.tracks[0].width;
            if (mode == 3) forged.sourceBytes.clear();
            if (mode == 4) forged.sha256 = QStringLiteral("伪造");
            auto current = forged; current.tracks.append(created());
            rejected(Writer::prepareWithCreated(forged, current, six()));
        }
    }

    void actualSyntaxCapacityAndDeletionRelease() {
        // 过孔 199994 + COMP/CT/ENDCOMP + 自由 FT + ENDPCB = 199999，隐式文字不另计。
        const QByteArray capComponent = "COMP\nU1\nDIP\ncomment\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
            "CT\n0 0 10 0 1 1\nENDCOMP\n";
        const auto original = pt::LegacyPcbReader::parse(header + capComponent + oldTrack
            + QByteArray("FV\n0 0 2 0\n").repeated(199994) + "ENDPCB\n").document; QVERIFY(original);
        auto current = *original; current.tracks.append(created());
        const auto full = Writer::prepareWithCreated(*original, current, six()); QVERIFY2(full.succeeded(), qPrintable(full.error));
        const auto parsed = pt::LegacyPcbReader::parse(full.bytes); QVERIFY(parsed.succeeded());
        qsizetype total = 1; for (const auto count : parsed.document->recordCounts) total += count; QCOMPARE(total, 200000);
        current.tracks.append(created(3));
        const auto refused = Writer::prepareWithCreated(*original, current, six()); rejected(refused);
        QVERIFY(refused.error.contains(QStringLiteral("200000")));
        current.tracks.removeAt(1);
        const auto released = Writer::prepareWithCreated(*original, current, six()); QVERIFY2(released.succeeded(), qPrintable(released.error));
        QVERIFY(pt::LegacyPcbReader::parse(released.bytes).succeeded());
        current.tracks.append(created(5)); rejected(Writer::prepareWithCreated(*original, current, six()));
    }

    void totalByteLimitIncludesEncodingAndMovementExpansion() {
        constexpr qsizetype limit = 64 * 1024 * 1024;
        const auto newTrack = created();
        const auto encoded = Codec::encode(newTrack.start, newTrack.end, newTrack.width, newTrack.layer, six());
        const auto original = pt::LegacyPcbReader::parse(paddedBoard(limit - encoded.bytes.size())).document; QVERIFY(original);
        auto current = *original; current.tracks.append(newTrack);
        const auto exact = Writer::prepareWithCreated(*original, current, six()); QVERIFY2(exact.succeeded(), qPrintable(exact.error));
        QCOMPARE(exact.bytes.size(), limit); QVERIFY(pt::LegacyPcbReader::parse(exact.bytes).succeeded());
        current.tracks.append(created(2));
        const auto over = Writer::prepareWithCreated(*original, current, six()); rejected(over);
        QVERIFY(over.error.contains(QStringLiteral("64 MiB")));
        // 移动增加十进制位数，不能只检查原件大小或新建字节数。
        current.tracks.removeLast(); current.tracks[0].start += QPointF(999000, 999000); current.tracks[0].end += QPointF(999000, 999000);
        const auto enlarged = Writer::prepareWithCreated(*original, current, six()); rejected(enlarged);
        QVERIFY(enlarged.error.contains(QStringLiteral("64 MiB")));
        current.tracks.removeFirst(); current.tracks.append(created(2));
        const auto afterDelete = Writer::prepareWithCreated(*original, current, six()); QVERIFY2(afterDelete.succeeded(), qPrintable(afterDelete.error));
        QVERIFY(afterDelete.bytes.size() < limit);
        // 默认入口也须在 append 前拒绝仅位移造成的整体超限。
        const auto maxOriginal = pt::LegacyPcbReader::parse(paddedBoard(limit)).document; QVERIFY(maxOriginal);
        auto moved = *maxOriginal; moved.tracks[0].start += QPointF(999000, 999000); moved.tracks[0].end += QPointF(999000, 999000);
        const auto defaultRefused = Writer::prepare(*maxOriginal, moved); rejected(defaultRefused);
        QVERIFY(defaultRefused.error.contains(QStringLiteral("64 MiB")));
    }

    void publishesFrozenSnapshotAndNeverOverwrites() {
        QTemporaryDir dir; QVERIFY(dir.isValid()); const auto input = dir.filePath(QStringLiteral("原件.pcb"));
        QVERIFY(writeFile(input, fixture())); const auto original = pt::LegacyPcbReader::readFile(input).document; QVERIFY(original);
        pt::BoardEditSession session; session.reset(original);
        QVERIFY(session.addTrack({1, 2}, {3, 4}, 5, 6, session.revision()));
        const auto snapshot = session.document(); const auto revision = session.revision();
        // 原路径已被外部更改也只能使用冻结字节；不得重新读取并改写原件。
        QVERIFY(writeFile(input, "外部文件"));
        const auto destination = dir.filePath(QStringLiteral("显式输出.PCB"));
        const auto result = Writer::saveAsWithCreated(destination, *original, *snapshot, six());
        QVERIFY2(result.succeeded(), qPrintable(result.error)); QCOMPARE(readFile(destination), result.bytes);
        QCOMPARE(result.filePath, destination); QCOMPARE(readFile(input), QByteArray("外部文件"));
        QVERIFY(pt::LegacyPcbReader::readFile(destination).succeeded());
        QCOMPARE(session.document(), snapshot); QCOMPARE(session.revision(), revision); QVERIFY(session.dirty()); QVERIFY(session.canUndo());
        const auto existing = dir.filePath("existing.pcb"); QVERIFY(writeFile(existing, "保留"));
        for (const auto& path : {input, dir.path() + QStringLiteral("/./原件.pcb"), destination, existing,
                dir.filePath("missing/output.pcb"), dir.filePath("wrong.txt"), dir.filePath("NUL.pcb"),
                dir.filePath("COM1.pcb"), dir.filePath("input.pcb:stream.pcb"), QString{}}) {
            const auto refused = Writer::saveAsWithCreated(path, *original, *snapshot, six()); QVERIFY(!refused.succeeded()); QVERIFY(!refused.error.isEmpty());
            QVERIFY(refused.filePath.isEmpty());
        }
        QCOMPARE(readFile(destination), result.bytes); QCOMPARE(readFile(existing), QByteArray("保留"));
        QCOMPARE(readFile(input), QByteArray("外部文件"));
        const auto defaultTarget = dir.filePath("default.pcb");
        rejected(Writer::saveAs(defaultTarget, *original, *snapshot)); QVERIFY(!QFile::exists(defaultTarget));
        const auto invalidTarget = dir.filePath("invalid.pcb");
        rejected(Writer::saveAsWithCreated(invalidTarget, *original, *snapshot, {})); QVERIFY(!QFile::exists(invalidTarget));
        QVERIFY(QDir(dir.path()).entryList({".pt-renew-*"}, QDir::Files | QDir::Hidden).isEmpty());
        QVERIFY(QFile::remove(input));
        QVERIFY(!Writer::saveAsWithCreated(input, *original, *snapshot, six()).succeeded()); QVERIFY(!QFile::exists(input));
        QVERIFY(Writer::saveAsWithCreated(dir.filePath("frozen.pcb"), *original, *snapshot, six()).succeeded());
    }

    void failedAtomicPublishLeavesNoTemporary() {
        QTemporaryDir dir; QVERIFY(dir.isValid()); const auto input = dir.filePath("input.pcb"); QVERIFY(writeFile(input, fixture()));
        const auto original = pt::LegacyPcbReader::readFile(input).document; QVERIFY(original);
        auto current = *original; current.tracks.append(created());
        const auto impossible = dir.filePath(QString(300, QLatin1Char('x')) + QStringLiteral(".pcb"));
        const auto result = Writer::saveAsWithCreated(impossible, *original, current, six());
        QVERIFY(!result.succeeded()); QVERIFY2(result.error.contains(QStringLiteral("无法发布新文件")), qPrintable(result.error));
        QCOMPARE(readFile(input), fixture());
        QCOMPARE(QDir(dir.path()).entryList(QDir::Files | QDir::Hidden | QDir::NoDotAndDotDot), QStringList{"input.pcb"});
    }
};

QTEST_APPLESS_MAIN(TrackCreatedWritingTests)
#include "TrackCreatedWritingTests.moc"
