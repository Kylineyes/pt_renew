#include "io/LegacyPcbReader.h"
#include <QCryptographicHash>
#include <QFile>
#include <QTemporaryDir>
#include <QtTest/QTest>

namespace {
const QByteArray header = "PCB FILE 4\n";
const QByteArray track = "FT\n0 0 100 0 12 1\n";
const QByteArray component = "COMP\nENDPCB\nENDPCB\nENDPCB\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
                             "CT\n0 0 100 0 12 1 9\nCP\n0 0 60 60 1 20 1 13\nENDPCB\n"
                             "CS\n0 0 10 0 1 7\nENDPCB\nENDCOMP\n";
QByteArray net(const QByteArray& name = "GND") {
    return "NETDEF\n" + name + "\n[\ncontains ENDPCB and NETDEF\n]\n(\nENDPCB-1\nU1-ENDPCB\n)\n";
}
}

class PcbLayoutTests final : public QObject {
    Q_OBJECT
private slots:
    void endTagIsAParsedTopLevelBoundary() {
        const QByteArray prefix = header + "\n \t\n" + track + "\n";
        const QByteArray input = prefix + " \tENDPCB \t\n\n \t\n";
        const auto result = pt::LegacyPcbReader::parseWithLayout(input, QStringLiteral("合成板图"));
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        const auto& layout = result.layout;
        QCOMPARE(layout.endPcbOffset, prefix.size());
        QCOMPARE(layout.insertion.kind, pt::LegacyPcbInsertionKind::BeforeEndPcb);
        QCOMPARE(layout.insertion.byteOffset, prefix.size());
        QCOMPARE(layout.insertion.anchorLineEnding, QByteArray("\n"));
        QVERIFY(layout.insertion.isValid());
        QVERIFY(layout.insertion.unavailableReason.isEmpty());
        QCOMPARE(layout.dosEofOffset, -1);
        QCOMPARE(layout.textEndOffset, input.size());
        QCOMPARE(layout.sourceByteSize, input.size());
        QCOMPARE(layout.trailingNetdefsOffset, -1);
        QCOMPARE(layout.topLevelRecords.size(), 2);
        const auto& ft = layout.topLevelRecords[0];
        QCOMPARE(ft.tag, QByteArray("FT"));
        QCOMPARE(ft.line, 4);
        QCOMPARE(input.mid(ft.beginOffset, ft.endOffset - ft.beginOffset), track);
        const auto& end = layout.topLevelRecords[1];
        QCOMPARE(end.beginOffset, prefix.size());
        QCOMPARE(end.endOffset, prefix.size() + QByteArray(" \tENDPCB \t\n").size());
        QCOMPARE(end.line, 7);
        QVERIFY(!layout.originalSoftwareInsertionVerified);
        QVERIFY(!layout.unverifiedReasons.isEmpty());
        QCOMPARE(result.document->sourceBytes, input);
        QCOMPARE(result.document->filePath, QStringLiteral("合成板图"));
        QCOMPARE(result.document->tracks[0].source.line, 4);
        QCOMPARE(result.document->tracks[0].identity, pt::TrackIdentity::loaded(4));
    }

    void labelsAndComponentFieldsDoNotTerminateTheBoard() {
        const QByteArray freeText = "FS\n0 0 10 0 1 7\nENDPCB\n";
        const QByteArray pad = "FP\n0 0 60 60 1 20 1 13\nENDPCB\n";
        const QByteArray prefix = header + freeText + pad + component;
        const auto result = pt::LegacyPcbReader::parseWithLayout(prefix + "ENDPCB\n");
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        QCOMPARE(result.layout.endPcbOffset, prefix.size());
        QCOMPARE(result.layout.insertion.byteOffset, prefix.size());
        QCOMPARE(result.document->components[0].designator, QStringLiteral("ENDPCB"));
        QCOMPARE(result.document->pads[0].name, QStringLiteral("ENDPCB"));
        QCOMPARE(result.document->texts[0].value, QStringLiteral("ENDPCB"));
        QCOMPARE(result.layout.topLevelRecords.size(), 4);
        const auto& comp = result.layout.topLevelRecords[2];
        QCOMPARE(comp.tag, QByteArray("COMP"));
        QCOMPARE(comp.beginOffset, (header + freeText + pad).size());
        QCOMPARE(comp.endOffset, prefix.size());
        QCOMPARE(result.document->tracks[0].source.component, 0);
    }

    void trailingNetdefs_data() {
        QTest::addColumn<QByteArray>("geometry");
        QTest::addColumn<int>("count");
        QTest::newRow("empty-board-one-net") << QByteArray() << 1;
        QTest::newRow("free-track-two-nets") << track << 2;
        QTest::newRow("component-three-nets") << component << 3;
    }
    void trailingNetdefs() {
        QFETCH(QByteArray, geometry);
        QFETCH(int, count);
        const QByteArray prefix = header + geometry + "\n";
        QByteArray nets;
        for (int i = 0; i < count; ++i) nets += net("ENDPCB-NET" + QByteArray::number(i)) + "\n";
        const QByteArray input = prefix + nets + "ENDPCB";
        const auto result = pt::LegacyPcbReader::parseWithLayout(input);
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        const auto& layout = result.layout;
        QCOMPARE(layout.trailingNetdefsOffset, prefix.size());
        QCOMPARE(layout.endPcbOffset, (prefix + nets).size());
        QCOMPARE(layout.netdefCount, count);
        QCOMPARE(layout.insertion.kind, pt::LegacyPcbInsertionKind::BeforeTrailingNetdefs);
        QCOMPARE(layout.insertion.byteOffset, prefix.size());
        QCOMPARE(layout.insertion.anchorLineEnding, QByteArray("\n"));
        QVERIFY(!layout.geometryAfterNetdef);
        QVERIFY(!layout.originalSoftwareInsertionVerified);
        QVERIFY(layout.unverifiedReasons.join('\n').contains(QStringLiteral("NETDEF")));
        QCOMPARE(result.document->embeddedNetlist->nets.size(), count);
        QCOMPARE(result.document->sourceBytes, input);
        const auto& boundary = layout.topLevelRecords[geometry.isEmpty() ? 0 : 1];
        QCOMPARE(boundary.tag, QByteArray("NETDEF"));
        QCOMPARE(input.mid(boundary.beginOffset, boundary.endOffset - boundary.beginOffset), net("ENDPCB-NET0"));
    }

    void interleavedNetdefsRemainReadableWithoutCandidate_data() {
        QTest::addColumn<QByteArray>("body");
        QTest::newRow("net-before-track") << (net() + track);
        QTest::newRow("net-before-component") << (net() + component);
        QTest::newRow("multiple-net-runs") << (track + net() + track + net("VCC"));
        QTest::newRow("empty-component-after-net") << (net() + QByteArray("COMP\nU1\nDIP\nV\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\nENDCOMP\n"));
    }
    void interleavedNetdefsRemainReadableWithoutCandidate() {
        QFETCH(QByteArray, body);
        const QByteArray input = header + body + "ENDPCB\n";
        const auto result = pt::LegacyPcbReader::parseWithLayout(input);
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        QVERIFY(pt::LegacyPcbReader::parse(input).succeeded());
        QVERIFY(result.layout.geometryAfterNetdef);
        QCOMPARE(result.layout.trailingNetdefsOffset, -1);
        QCOMPARE(result.layout.insertion.kind, pt::LegacyPcbInsertionKind::None);
        QCOMPARE(result.layout.insertion.byteOffset, -1);
        QVERIFY(!result.layout.insertion.isValid());
        QVERIFY(result.layout.insertion.unavailableReason.contains(QStringLiteral("交错")));
        QCOMPARE(result.layout.endPcbOffset, (header + body).size());
    }

    void newlineFacts_data() {
        QTest::addColumn<QByteArray>("input");
        QTest::addColumn<int>("lf");
        QTest::addColumn<int>("crlf");
        QTest::addColumn<int>("bareCr");
        QTest::addColumn<bool>("terminated");
        QTest::addColumn<QByteArray>("anchorEnding");
        QTest::newRow("lf") << QByteArray("PCB FILE 4\nENDPCB\n") << 2 << 0 << 0 << true << QByteArray("\n");
        QTest::newRow("crlf") << QByteArray("PCB FILE 4\r\nENDPCB\r\n") << 0 << 2 << 0 << true << QByteArray("\r\n");
        QTest::newRow("mixed-trailing-whitespace") << QByteArray("PCB FILE 4\r\n\nENDPCB\n \r\n") << 2 << 2 << 0 << true << QByteArray("\n");
        QTest::newRow("unterminated-end") << QByteArray("PCB FILE 4\r\nENDPCB") << 0 << 1 << 0 << false << QByteArray();
        QTest::newRow("unterminated-trailing-whitespace") << QByteArray("PCB FILE 4\nENDPCB\r\n \t") << 1 << 1 << 0 << false << QByteArray("\r\n");
        QTest::newRow("bare-cr-is-not-line-separator") << QByteArray("PCB FILE 4\nENDPCB\r") << 1 << 0 << 1 << false << QByteArray();
        QTest::newRow("embedded-net-lines") << QByteArray("PCB FILE 4\r\nNETDEF\r\nGND\n(\r\nU1-1\n)\r\nENDPCB") << 2 << 4 << 0 << false << QByteArray("\r\n");
    }
    void newlineFacts() {
        QFETCH(QByteArray, input); QFETCH(int, lf); QFETCH(int, crlf); QFETCH(int, bareCr);
        QFETCH(bool, terminated); QFETCH(QByteArray, anchorEnding);
        const auto result = pt::LegacyPcbReader::parseWithLayout(input);
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        const auto& facts = result.layout.newlines;
        QCOMPARE(facts.lfCount, lf);
        QCOMPARE(facts.crlfCount, crlf);
        QCOMPARE(facts.bareCarriageReturnCount, bareCr);
        QCOMPARE(facts.textEndsWithNewline, terminated);
        QCOMPARE(facts.mixed(), lf > 0 && crlf > 0);
        QCOMPARE(facts.firstLineEnding, input.startsWith("PCB FILE 4\r\n") ? QByteArray("\r\n") : QByteArray("\n"));
        QCOMPARE(result.layout.insertion.anchorLineEnding, anchorEnding);
        QCOMPARE(result.document->sourceBytes, input);
    }

    void dosEofAndHighBytesPreserveFrozenOffsets_data() {
        QTest::addColumn<QByteArray>("ending");
        QTest::newRow("newline-before-eof") << QByteArray("\r\n\x1a\r\n \t");
        QTest::newRow("eof-attached-to-end-tag") << QByteArray("\x1a\n\t");
    }
    void dosEofAndHighBytesPreserveFrozenOffsets() {
        QFETCH(QByteArray, ending);
        const QByteArray prefix = QByteArray("PCB FILE 4\r\nFS\n0 0 10 0 1 7\r\n") + QByteArray::fromHex("82ff") + " ENDPCB\n";
        const QByteArray text = prefix + "\t ENDPCB \t";
        const QByteArray input = text + ending;
        const auto result = pt::LegacyPcbReader::parseWithLayout(input);
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        QCOMPARE(result.layout.endPcbOffset, prefix.size());
        QCOMPARE(result.layout.insertion.byteOffset, prefix.size());
        const auto eof = text.size() + (ending.startsWith("\r\n") ? 2 : 0);
        QCOMPARE(result.layout.dosEofOffset, eof);
        QCOMPARE(result.layout.textEndOffset, eof);
        QCOMPARE(result.layout.sourceByteSize, input.size());
        QCOMPARE(result.layout.newlines.crlfCount, ending.startsWith("\r\n") ? 3 : 2);
        QCOMPARE(result.layout.newlines.lfCount, 2);
        QCOMPARE(result.document->sourceBytes, input);
        QCOMPARE(result.document->byteSize, input.size());
        QCOMPARE(result.document->sha256, QString::fromLatin1(QCryptographicHash::hash(input, QCryptographicHash::Sha256).toHex()));
        QVERIFY(result.document->texts[0].value.startsWith(QString(2, QChar::ReplacementCharacter)));
    }

    void failuresNeverExposePartialBoundaries_data() {
        QTest::addColumn<QByteArray>("input");
        QTest::newRow("empty") << QByteArray();
        QTest::newRow("wrong-header") << QByteArray("PCB FILE 5\nENDPCB\n");
        QTest::newRow("missing-end") << (header + track);
        QTest::newRow("label-only-end") << (header + QByteArray("FS\n0 0 10 0 1 7\nENDPCB\n"));
        QTest::newRow("nested-component") << (header + component.left(component.size() - 8) + "COMP\nENDPCB\n");
        QTest::newRow("end-in-component") << (header + component.left(component.size() - 8) + "ENDPCB\n");
        QTest::newRow("unmatched-component-end") << (header + "ENDCOMP\nENDPCB\n");
        QTest::newRow("net-in-component") << (header + component.left(component.size() - 8) + net() + "ENDCOMP\nENDPCB\n");
        QTest::newRow("unclosed-net") << (header + "NETDEF\nGND\n(\nU1-1\nENDPCB\n");
        QTest::newRow("unknown-record") << (header + "XY\nENDPCB\n");
        QTest::newRow("bad-fields") << (header + "FT\n0 0 ENDPCB 0 12 1\nENDPCB\n");
        QTest::newRow("data-after-end") << (header + "ENDPCB\n" + track);
        QTest::newRow("duplicate-end") << (header + "ENDPCB\nENDPCB\n");
        QTest::newRow("data-after-eof") << (header + "ENDPCB\n\x1a" + track);
        QTest::newRow("duplicate-eof") << (header + "ENDPCB\n\x1a\x1a");
        QTest::newRow("early-eof") << (header + "\x1a");
        QTest::newRow("zero-byte") << (header + QByteArray(1, '\0') + "ENDPCB\n");
        QTest::newRow("long-line") << (header + QByteArray(65537, ' ') + "\nENDPCB\n");
        QTest::newRow("too-large") << QByteArray(64 * 1024 * 1024 + 1, ' ');
    }
    void failuresNeverExposePartialBoundaries() {
        QFETCH(QByteArray, input);
        const auto result = pt::LegacyPcbReader::parseWithLayout(input);
        const auto legacy = pt::LegacyPcbReader::parse(input);
        QVERIFY(!result.succeeded());
        QVERIFY(!result.document);
        QVERIFY(!result.error.isEmpty());
        QCOMPARE(legacy.error, result.error);
        QVERIFY(!legacy.succeeded());
        QCOMPARE(result.layout.endPcbOffset, -1);
        QCOMPARE(result.layout.trailingNetdefsOffset, -1);
        QCOMPARE(result.layout.dosEofOffset, -1);
        QVERIFY(result.layout.topLevelRecords.isEmpty());
        QVERIFY(!result.layout.insertion.isValid());
        QVERIFY(!result.layout.insertion.unavailableReason.isEmpty());
    }

    void legacyReadFileAndParseShareTheSameDocumentFacts() {
        const QByteArray input = header + component + track + net() + "ENDPCB\n\x1a\n";
        QTemporaryDir dir;
        QVERIFY(dir.isValid());
        const auto path = dir.filePath(QStringLiteral("合成板图.pcb"));
        QFile file(path);
        QVERIFY(file.open(QIODevice::WriteOnly));
        QCOMPARE(file.write(input), input.size());
        file.close();
        const auto layout = pt::LegacyPcbReader::parseWithLayout(input, path);
        const auto parsed = pt::LegacyPcbReader::parse(input, path);
        const auto loaded = pt::LegacyPcbReader::readFile(path);
        QVERIFY(layout.succeeded()); QVERIFY(parsed.succeeded()); QVERIFY(loaded.succeeded());
        for (const auto& board : {parsed.document, loaded.document}) {
            QCOMPARE(board->sourceBytes, layout.document->sourceBytes);
            QCOMPARE(board->sha256, layout.document->sha256);
            QCOMPARE(board->recordCounts, layout.document->recordCounts);
            QCOMPARE(board->warnings, layout.document->warnings);
            QCOMPARE(board->filePath, path);
            QCOMPARE(board->tracks[0].identity, layout.document->tracks[0].identity);
            QCOMPARE(board->tracks[1].extra, layout.document->tracks[1].extra);
            QCOMPARE(board->embeddedNetlist->sourceBytes, input);
        }
        QVERIFY(!pt::LegacyPcbReader::readFile(dir.filePath(QStringLiteral("不存在.pcb"))).succeeded());
    }
};

QTEST_GUILESS_MAIN(PcbLayoutTests)
#include "PcbLayoutTests.moc"
