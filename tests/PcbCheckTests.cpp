#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QTemporaryDir>
#include <QtTest/QTest>

namespace {
QByteArray fixture() {
    return "PCB FILE 4\r\n FT \r\n+001 2 3 4 5 1\n"
        "FS\n0 0 10 0 1 7\nFT\n"
        "COMP\nENDPCB\nFT\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 0\n"
        "CT\n20 30 40 50 6 1 99\nENDCOMP\n"
        "FS\r\n0 0 10 0 1 7\nENDPCB\r\n"
        "FT\n-4 -3 -2 -1 7 6 -42\r\n ENDPCB \x1a \t\r\n";
}
bool writeFile(const QString& path, const QByteArray& bytes) {
    QFile file(path);
    return file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size();
}
QByteArray readFile(const QString& path) {
    QFile file(path);
    return file.open(QIODevice::ReadOnly) ? file.readAll() : QByteArray{};
}
struct Run {
    bool finished = false;
    int code = -1;
    QByteArray stdoutBytes, stderrBytes;
    QJsonObject report;
};
Run run(const QStringList& arguments) {
    auto executable = qEnvironmentVariable("PT_PCB_CHECK_EXECUTABLE");
    if (executable.isEmpty()) {
#ifdef Q_OS_WIN
        const auto name = QStringLiteral("pt-pcb-check.exe");
#else
        const auto name = QStringLiteral("pt-pcb-check");
#endif
        executable = QDir(QCoreApplication::applicationDirPath()).filePath(name);
    }
    QProcess process;
    process.start(executable, arguments);
    Run result;
    if (!process.waitForStarted(5000)) { result.stderrBytes = process.errorString().toUtf8(); return result; }
    result.finished = process.waitForFinished(30000) && process.exitStatus() == QProcess::NormalExit;
    if (!result.finished) { process.kill(); process.waitForFinished(5000); }
    result.code = process.exitCode();
    result.stdoutBytes = process.readAllStandardOutput();
    result.stderrBytes = process.readAllStandardError();
    QJsonParseError error;
    const auto document = QJsonDocument::fromJson(result.stdoutBytes, &error);
    if (error.error == QJsonParseError::NoError && document.isObject()) result.report = document.object();
    return result;
}
void checkSuccess(const Run& result) {
    QVERIFY2(result.finished, result.stderrBytes.constData());
    QCOMPARE(result.code, 0); QVERIFY(result.stderrBytes.isEmpty()); QVERIFY(!result.report.isEmpty());
    QVERIFY(result.report.value("succeeded").toBool());
    QVERIFY(!result.report.value("originalSoftwareCompatibilityVerified").toBool(true));
    QVERIFY(result.report.value("notice").toString().contains(QStringLiteral("不是默认编码策略")));
}
void checkFailure(const Run& result, int code) {
    QVERIFY2(result.finished, result.stderrBytes.constData()); QCOMPARE(result.code, code);
    QVERIFY(result.stderrBytes.isEmpty()); QVERIFY(!result.report.isEmpty());
    QVERIFY(!result.report.value("succeeded").toBool(true)); QVERIFY(!result.report.value("error").toString().isEmpty());
    QVERIFY(!result.report.contains("freeTracks")); QVERIFY(!result.report.contains("recordCounts"));
    QVERIFY(!result.report.contains("layout")); QVERIFY(!result.report.contains("sha256"));
    QVERIFY(!result.report.value("originalSoftwareCompatibilityVerified").toBool(true));
}
}

class PcbCheckTests final : public QObject {
    Q_OBJECT
private slots:
    void mixedLayoutUnicodeAndReadonly() {
        QTemporaryDir dir; QVERIFY(dir.isValid());
        const auto path = dir.filePath(QStringLiteral("板图 样例-é.PCB"));
        const auto input = fixture(); QVERIFY(writeFile(path, input));
        const auto result = run({path}); checkSuccess(result);
        const auto report = result.report;
        QCOMPARE(report.value("path").toString(), QFileInfo(path).absoluteFilePath());
        QCOMPARE(report.value("byteSize").toInteger(), input.size());
        QCOMPARE(report.value("sha256").toString(), QString::fromLatin1(QCryptographicHash::hash(input, QCryptographicHash::Sha256).toHex()));
        QCOMPARE(report.value("freeTrackCount").toInt(), 2); QCOMPARE(report.value("primitiveCount").toInt(), 5);
        QCOMPARE(report.value("syntaxRecordCount").toInt(), 8);
        QCOMPARE(report.value("recordCounts").toObject().value("CT").toInt(), 1);
        QCOMPARE(report.value("recordCounts").toObject().value("FT").toInt(), 2);
        const auto tracks = report.value("freeTracks").toArray(); QCOMPARE(tracks.size(), 2);
        const auto first = tracks[0].toObject(), second = tracks[1].toObject();
        QCOMPARE(first.value("start").toArray(), (QJsonArray{1, 2}));
        QCOMPARE(first.value("end").toArray(), (QJsonArray{3, 4}));
        QCOMPARE(first.value("width").toInt(), 5); QCOMPARE(first.value("layer").toInt(), 1);
        QVERIFY(!first.contains("extra")); QCOMPARE(second.value("extra").toInt(), -42);
        QCOMPARE(second.value("start").toArray(), (QJsonArray{-4, -3}));
        QCOMPARE(first.value("sourceLine").toInt(), 2); QCOMPARE(second.value("sourceLine").toInt(), 20);
        QCOMPARE(second.value("identity").toObject().value("kind").toString(), QStringLiteral("Loaded"));
        QCOMPARE(second.value("identity").toObject().value("value").toInt(), 20);
        QCOMPARE(second.value("sourceComponent").toInt(), -1); QCOMPARE(second.value("sourceByteOffset").toInt(), -1);
        const auto firstRecord = first.value("sourceRecord").toObject(), secondRecord = second.value("sourceRecord").toObject();
        QCOMPARE(firstRecord.value("fieldCount").toInt(), 6); QCOMPARE(secondRecord.value("fieldCount").toInt(), 7);
        QCOMPARE(firstRecord.value("tagLineEnding").toString(), QStringLiteral("\r\n"));
        QCOMPARE(firstRecord.value("valuesLineEnding").toString(), QStringLiteral("\n"));
        QCOMPARE(secondRecord.value("tagLineEnding").toString(), QStringLiteral("\n"));
        QCOMPARE(secondRecord.value("valuesLineEnding").toString(), QStringLiteral("\r\n"));
        QCOMPARE(firstRecord.value("beginOffset").toInteger(), qint64(QByteArray("PCB FILE 4\r\n").size()));
        const auto layout = report.value("layout").toObject(), newlines = layout.value("newlines").toObject();
        QCOMPARE(newlines.value("lfCount").toInt(), 16); QCOMPARE(newlines.value("crlfCount").toInt(), 5);
        QVERIFY(newlines.value("mixed").toBool()); QVERIFY(!newlines.value("textEndsWithNewline").toBool(true));
        QCOMPARE(layout.value("dosEofOffset").toInteger(), input.size() - 5);
        QCOMPARE(layout.value("textEndOffset").toInteger(), input.size() - 5);
        const auto insertion = layout.value("insertion").toObject();
        QCOMPARE(insertion.value("kind").toString(), QStringLiteral("BeforeEndPcb"));
        QCOMPARE(insertion.value("byteOffset"), layout.value("endPcbOffset"));
        QCOMPARE(insertion.value("anchorLineEnding").toString(), QString{});
        QVERIFY(!layout.value("originalSoftwareInsertionVerified").toBool(true));
        QCOMPARE(readFile(path), input);
        QCOMPARE(QDir(dir.path()).entryList(QDir::Files), QStringList{QFileInfo(path).fileName()});
    }
    void limitsBoundDetailsWithoutLosingCounts_data() {
        QTest::addColumn<QStringList>("options"); QTest::addColumn<int>("expected");
        QTest::newRow("default") << QStringList{} << 100;
        QTest::newRow("zero") << QStringList{"--track-limit", "0"} << 0;
        QTest::newRow("one") << QStringList{"--track-limit", "1"} << 1;
        QTest::newRow("maximum") << QStringList{"--track-limit", "1000"} << 1000;
    }
    void limitsBoundDetailsWithoutLosingCounts() {
        QFETCH(QStringList, options); QFETCH(int, expected);
        QTemporaryDir dir; const auto path = dir.filePath("many.pcb");
        const QByteArray input = "PCB FILE 4\n" + QByteArray("FT\n0 0 1 1 1 1 0\n").repeated(1002) + "ENDPCB\n";
        QVERIFY(writeFile(path, input)); options.append(path);
        const auto result = run(options); checkSuccess(result);
        QCOMPARE(result.report.value("freeTrackCount").toInt(), 1002);
        QCOMPARE(result.report.value("syntaxRecordCount").toInt(), 1003);
        QCOMPARE(result.report.value("freeTracks").toArray().size(), expected);
        QCOMPARE(result.report.value("freeTracksOmitted").toInt(), 1002 - expected);
        if (expected) QCOMPARE(result.report.value("freeTracks").toArray()[0].toObject().value("extra").toInt(-1), 0);
        QVERIFY(result.stdoutBytes.size() < 1000000); QCOMPARE(readFile(path), input);
    }
    void helpAndArgumentErrors() {
        const auto help = run({"--help"}); QVERIFY(help.finished); QCOMPARE(help.code, 0);
        QVERIFY(help.report.value("usage").toString().contains(QStringLiteral("不读取文件")));
        QVERIFY(!help.report.contains("sha256")); QVERIFY(help.stderrBytes.isEmpty());
        for (const QStringList& arguments : QList<QStringList>{{}, {"--unknown"}, {"a.pcb", "b.pcb"},
                {"--track-limit"}, {"--track-limit", "-1", "a.pcb"}, {"--track-limit", "1001", "a.pcb"},
                {"--track-limit", "1.5", "a.pcb"}, {"--track-limit", "999999999999999999", "a.pcb"},
                {"--track-limit", "1", "--track-limit", "2", "a.pcb"}, {"--help", "absent.pcb"}})
            checkFailure(run(arguments), 2);
        QTemporaryDir dir; const auto path = dir.filePath("--file.pcb");
        QVERIFY(writeFile(path, "PCB FILE 4\nENDPCB")); checkSuccess(run({"--", path}));
        checkFailure(run({dir.filePath("absent.pcb")}), 1);
    }
    void strictFailuresNeverExportPartialGeometry_data() {
        QTest::addColumn<QByteArray>("suffix");
        QTest::newRow("unknown-tag") << QByteArray("FX\n1 2\nENDPCB\n");
        QTest::newRow("bad-eof") << QByteArray("ENDPCB\n\x1a" "BAD");
        QTest::newRow("missing-end") << QByteArray{};
        QTest::newRow("data-after-end") << QByteArray("ENDPCB\nFT\n0 0 1 1 1 1\n");
        QTest::newRow("bad-field") << QByteArray("FT\n0 0 1 1 bad 1\nENDPCB\n");
    }
    void strictFailuresNeverExportPartialGeometry() {
        QFETCH(QByteArray, suffix);
        QTemporaryDir dir; const auto path = dir.filePath("invalid.pcb");
        const QByteArray input = "PCB FILE 4\nFT\n0 0 1 1 1 1\n" + suffix;
        QVERIFY(writeFile(path, input));
        checkFailure(run({path}), 1); checkFailure(run({"--track-limit", "0", path}), 1);
        QCOMPARE(readFile(path), input);
    }
    void netdefLayoutIsReportedWithoutClaimingInsertionCompatibility() {
        QTemporaryDir dir; const auto path = dir.filePath("net.pcb");
        const QByteArray net = "NETDEF\nGND\n[\n]\n(\nU1-1\n)\n";
        QVERIFY(writeFile(path, "PCB FILE 4\n" + net + "ENDPCB\n"));
        auto result = run({path}); checkSuccess(result);
        auto layout = result.report.value("layout").toObject();
        QCOMPARE(layout.value("netdefCount").toInt(), 1);
        QCOMPARE(layout.value("insertion").toObject().value("kind").toString(), QStringLiteral("BeforeTrailingNetdefs"));
        QVERIFY(writeFile(path, "PCB FILE 4\n" + net + "FT\n0 0 1 1 1 1\nENDPCB\n"));
        result = run({path}); checkSuccess(result); layout = result.report.value("layout").toObject();
        QVERIFY(layout.value("geometryAfterNetdef").toBool());
        QVERIFY(!layout.value("insertion").toObject().value("valid").toBool(true));
        QCOMPARE(result.report.value("freeTrackCount").toInt(), 1);
    }
    void readerSizeLimitIsPreserved() {
        QTemporaryDir dir; const auto path = dir.filePath("too-large.pcb");
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); QVERIFY(file.resize(64 * 1024 * 1024 + 1)); file.close();
        const auto result = run({path}); checkFailure(result, 1);
        QVERIFY(result.report.value("error").toString().contains(QStringLiteral("64 MiB")));
        QCOMPARE(QFileInfo(path).size(), qint64(64 * 1024 * 1024 + 1));
    }
};

QTEST_GUILESS_MAIN(PcbCheckTests)
#include "PcbCheckTests.moc"
