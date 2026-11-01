#include "io/LegacyFreeTrackCodec.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbWriter.h"
#include "application/BoardEditSession.h"
#include <QDir>
#include <QFileInfo>
#include <QLocale>
#include <QTemporaryDir>
#include <QtTest/QTest>
#include <array>
#include <limits>
#include <type_traits>

namespace {
using Codec = pt::LegacyFreeTrackCodec;
Codec::Options six() { return {Codec::FieldLayout::SixFields, Codec::LineEnding::Lf, {}}; }
// 换行没有原始字符串入口，混合换行、孤立 CR 或记录注入不能作为选项传入。
static_assert(!std::is_convertible_v<QByteArray, Codec::LineEnding>);
}

class FreeTrackCodecTests final : public QObject {
    Q_OBJECT
private slots:
    void exactExplicitBytes_data() {
        QTest::addColumn<bool>("seven");
        QTest::addColumn<bool>("crlf");
        QTest::addColumn<int>("extra");
        QTest::addColumn<QByteArray>("expected");
        QTest::newRow("six-lf") << false << false << 0 << QByteArray("FT\n-1000000 1000000 1000000 -1000000 1000000 6\n");
        QTest::newRow("six-crlf") << false << true << 0 << QByteArray("FT\r\n-1000000 1000000 1000000 -1000000 1000000 6\r\n");
        QTest::newRow("seven-lf-min-int") << true << false << std::numeric_limits<int>::min()
            << QByteArray("FT\n-1000000 1000000 1000000 -1000000 1000000 6 -2147483648\n");
        QTest::newRow("seven-crlf-max-int") << true << true << std::numeric_limits<int>::max()
            << QByteArray("FT\r\n-1000000 1000000 1000000 -1000000 1000000 6 2147483647\r\n");
        QTest::newRow("seven-lf-zero") << true << false << 0
            << QByteArray("FT\n-1000000 1000000 1000000 -1000000 1000000 6 0\n");
        QTest::newRow("seven-crlf-negative") << true << true << -42
            << QByteArray("FT\r\n-1000000 1000000 1000000 -1000000 1000000 6 -42\r\n");
    }
    void exactExplicitBytes() {
        QFETCH(bool, seven); QFETCH(bool, crlf); QFETCH(int, extra); QFETCH(QByteArray, expected);
        auto options = six();
        options.fields = seven ? Codec::FieldLayout::SevenFields : Codec::FieldLayout::SixFields;
        options.lineEnding = crlf ? Codec::LineEnding::CrLf : Codec::LineEnding::Lf;
        if (seven) options.extra = extra;
        const auto result = Codec::encode({-1000000, 1000000}, {1000000, -1000000}, 1000000, 6, options);
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        QCOMPARE(result.bytes, expected);
        QVERIFY(result.error.isEmpty());
        const auto newline = crlf ? QByteArray("\r\n") : QByteArray("\n");
        QCOMPARE(result.bytes.count('\n'), 2);
        QCOMPARE(result.bytes.count('\r'), crlf ? 2 : 0);
        QVERIFY(result.bytes.endsWith(newline));
        for (const auto ch : result.bytes) QVERIFY(static_cast<unsigned char>(ch) < 128);
        const auto parsed = pt::LegacyPcbReader::parse("PCB FILE 4" + newline + result.bytes + "ENDPCB" + newline);
        QVERIFY2(parsed.succeeded(), qPrintable(parsed.error));
        QCOMPARE(parsed.document->tracks.size(), 1);
        const auto& track = parsed.document->tracks[0];
        QCOMPARE(track.start, QPointF(-1000000, 1000000));
        QCOMPARE(track.end, QPointF(1000000, -1000000));
        QCOMPARE(track.width, 1000000);
        QCOMPARE(track.layer, 6);
        QCOMPARE(track.extra, options.extra);
    }

    void canonicalAsciiIgnoresLocaleAndNegativeZero() {
        const auto previousLocale = QLocale();
        QLocale::setDefault(QLocale(QLocale::Arabic, QLocale::Egypt));
        const auto result = Codec::encode({-0.0, 0}, {1, -1}, 1, 1, six());
        QLocale::setDefault(previousLocale);
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        QCOMPARE(result.bytes, QByteArray("FT\n0 0 1 -1 1 1\n"));
    }

    void invalidOptions_data() {
        QTest::addColumn<int>("fields");
        QTest::addColumn<int>("ending");
        QTest::addColumn<bool>("hasExtra");
        QTest::addColumn<QString>("reason");
        const auto row = [](const char* name, int fields, int ending, bool extra, const QString& reason) {
            QTest::newRow(name) << fields << ending << extra << reason;
        };
        row("all-unspecified", 0, 0, false, QStringLiteral("显式选择 FT"));
        row("fields-unspecified", 0, 1, false, QStringLiteral("显式选择 FT"));
        row("ending-unspecified", 1, 0, false, QStringLiteral("显式选择 LF"));
        row("seven-missing-extra", 2, 1, false, QStringLiteral("显式提供附加整数"));
        row("six-conflicting-extra", 1, 1, true, QStringLiteral("不能提供附加整数"));
        row("negative-field-enum", -1, 1, false, QStringLiteral("布局枚举无效"));
        row("unknown-field-enum", 3, 1, false, QStringLiteral("布局枚举无效"));
        row("max-field-enum", std::numeric_limits<int>::max(), 1, false, QStringLiteral("布局枚举无效"));
        row("negative-ending-enum", 1, -1, false, QStringLiteral("换行枚举无效"));
        row("unknown-ending-enum", 1, 3, false, QStringLiteral("换行枚举无效"));
        row("raw-cr-not-an-enum", 1, '\r', false, QStringLiteral("换行枚举无效"));
        row("raw-lf-not-an-enum", 1, '\n', false, QStringLiteral("换行枚举无效"));
        row("max-ending-enum", 1, std::numeric_limits<int>::max(), false, QStringLiteral("换行枚举无效"));
    }
    void invalidOptions() {
        QFETCH(int, fields); QFETCH(int, ending); QFETCH(bool, hasExtra); QFETCH(QString, reason);
        Codec::Options options;
        options.fields = static_cast<Codec::FieldLayout>(fields);
        options.lineEnding = static_cast<Codec::LineEnding>(ending);
        if (hasExtra) options.extra = 0;
        const auto result = Codec::encode({0, 0}, {100, 0}, 12, 1, options);
        QVERIFY(!result.succeeded());
        QVERIFY(result.bytes.isEmpty());
        QVERIFY2(result.error.contains(reason), qPrintable(result.error));
    }

    void invalidGeometry_data() {
        QTest::addColumn<QPointF>("start");
        QTest::addColumn<QPointF>("end");
        QTest::addColumn<int>("width");
        QTest::addColumn<int>("layer");
        QTest::addColumn<QString>("reason");
        const std::array<qreal, 9> invalidCoordinates = {
            -1000001, 1000001, -0.25, 0.25, std::numeric_limits<qreal>::quiet_NaN(),
            std::numeric_limits<qreal>::infinity(), -std::numeric_limits<qreal>::infinity(),
            std::numeric_limits<qreal>::max(), std::numeric_limits<qreal>::denorm_min()
        };
        for (int axis = 0; axis < 4; ++axis) {
            for (size_t value = 0; value < invalidCoordinates.size(); ++value) {
                std::array<qreal, 4> points = {0, 0, 100, 50};
                points[axis] = invalidCoordinates[value];
                const auto name = QByteArray("coordinate-") + QByteArray::number(axis) + '-' + QByteArray::number(value);
                QTest::newRow(name.constData()) << QPointF(points[0], points[1]) << QPointF(points[2], points[3])
                    << 12 << 1 << QStringLiteral("有限整数");
            }
        }
        for (const auto width : {std::numeric_limits<int>::min(), -1, 0, 1000001, std::numeric_limits<int>::max()}) {
            const auto name = QByteArray("width-") + QByteArray::number(width);
            QTest::newRow(name.constData()) << QPointF(0, 0) << QPointF(100, 0) << width << 1 << QStringLiteral("宽度");
        }
        for (const auto layer : {-1, 0, 2, 7, 13, std::numeric_limits<int>::max()}) {
            const auto name = QByteArray("layer-") + QByteArray::number(layer);
            QTest::newRow(name.constData()) << QPointF(0, 0) << QPointF(100, 0) << 12 << layer << QStringLiteral("顶层 1 或底层 6");
        }
        QTest::newRow("zero-length") << QPointF(-10, 20) << QPointF(-10, 20) << 12 << 1 << QStringLiteral("不能相同");
    }
    void invalidGeometry() {
        QFETCH(QPointF, start); QFETCH(QPointF, end); QFETCH(int, width); QFETCH(int, layer); QFETCH(QString, reason);
        const auto result = Codec::encode(start, end, width, layer, six());
        QVERIFY(!result.succeeded());
        QVERIFY(result.bytes.isEmpty());
        QVERIFY2(result.error.contains(reason), qPrintable(result.error));
    }

    void defaultOptionsStayUnspecified() {
        const Codec::Options options;
        QCOMPARE(options.fields, Codec::FieldLayout::Unspecified);
        QCOMPARE(options.lineEnding, Codec::LineEnding::Unspecified);
        QVERIFY(!options.extra.has_value());
        const auto result = Codec::encode({0, 0}, {1, 0}, 1, 1, options);
        QVERIFY(!result.succeeded());
        QVERIFY(result.bytes.isEmpty());
    }

    void explicitEncodingDoesNotUnlockWriter() {
        const QByteArray originalBytes = "PCB FILE 4\nFT\n0 0 100 0 12 1 42\nENDPCB\n";
        const auto original = pt::LegacyPcbReader::parse(originalBytes);
        QVERIFY(original.succeeded());
        pt::BoardEditSession session;
        session.reset(original.document);
        QString error;
        QVERIFY2(session.addTrack({10, 20}, {30, 40}, 8, 6, session.revision(), &error), qPrintable(error));
        QVERIFY(!session.document()->tracks.back().extra.has_value());
        const auto revision = session.revision();
        const auto working = session.document();
        const auto encoded = Codec::encode({10, 20}, {30, 40}, 8, 6,
            {Codec::FieldLayout::SevenFields, Codec::LineEnding::CrLf, -9});
        QVERIFY2(encoded.succeeded(), qPrintable(encoded.error));
        QCOMPARE(encoded.bytes, QByteArray("FT\r\n10 20 30 40 8 6 -9\r\n"));
        QCOMPARE(session.document(), working);
        QCOMPARE(session.revision(), revision);
        QCOMPARE(session.document()->sourceBytes, originalBytes);
        QCOMPARE(original.document->tracks[0].extra, std::optional<int>(42));
        const auto prepared = pt::LegacyPcbWriter::prepare(*original.document, *session.document());
        QVERIFY(!prepared.succeeded());
        QVERIFY(prepared.bytes.isEmpty());
        QVERIFY(prepared.error.contains(QStringLiteral("新增")));
        QTemporaryDir dir;
        QVERIFY(dir.isValid());
        const auto path = dir.filePath(QStringLiteral("新增仍拒绝.pcb"));
        const auto saved = pt::LegacyPcbWriter::saveAs(path, *original.document, *session.document());
        QVERIFY(!saved.succeeded());
        QVERIFY(!QFileInfo::exists(path));
        QVERIFY(QDir(dir.path()).entryList(QDir::Files | QDir::Hidden).isEmpty());
        QVERIFY(session.dirty());
    }
};

QTEST_GUILESS_MAIN(FreeTrackCodecTests)
#include "FreeTrackCodecTests.moc"
