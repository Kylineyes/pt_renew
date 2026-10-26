#include "experiment/AsyncExperiment.h"
#include "ui/MainWindow.h"
#include "ui/BoardCanvas.h"
#include "ui/NetlistBrowser.h"
#include <QApplication>
#include <QDir>
#include <QCryptographicHash>
#include <QStandardPaths>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QLabel>
#include <QPlainTextEdit>
#include <QProcess>
#include <QPushButton>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QThreadPool>
#include <QTimer>
#include <QtCore/qt_windows.h>
#include <QtTest/QTest>

namespace {
bool writeFile(const QString& path, const QByteArray& bytes) {
    QFile file(path);
    return file.open(QIODevice::WriteOnly) && file.write(bytes)==bytes.size();
}
QList<QJsonObject> readEvents(const QString& directory) {
    QFile file(directory+QStringLiteral("/events.jsonl"));
    QList<QJsonObject> result;
    if (!file.open(QIODevice::ReadOnly)) return result;
    for (const auto& line:file.readAll().split('\n')) if (!line.isEmpty())
        result.append(QJsonDocument::fromJson(line).object());
    return result;
}
int eventIndex(const QList<QJsonObject>& events, const QString& name, const QString& id={}) {
    for (qsizetype i=0;i<events.size();++i)
        if (events[i].value(QStringLiteral("event")).toString()==name &&
            (id.isEmpty() || events[i].value(QStringLiteral("request_id")).toString()==id)) return int(i);
    return -1;
}
QJsonObject manifest(const QString& directory) {
    const auto names=QDir(directory).entryList({QStringLiteral("request-*.json")},QDir::Files);
    if (names.size()!=1) return {};
    QFile file(QDir(directory).filePath(names.first()));
    if (!file.open(QIODevice::ReadOnly)) return {};
    return QJsonDocument::fromJson(file.readAll()).object();
}
bool signalGate(const QString& directory, const QString& key) {
    const auto name=manifest(directory).value(key).toString();
    const auto handle=OpenEventW(EVENT_MODIFY_STATE,FALSE,reinterpret_cast<LPCWSTR>(name.utf16()));
    if (!handle) return false;
    const bool result=SetEvent(handle);
    CloseHandle(handle);
    return result;
}
const QByteArray board="PCB FILE 4\nFT\n100 100 400 500 10 1\n"
    "COMP\nU1\nDIP\nValue\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 2\n"
    "CP\n100 100 60 60 1 20 1 13\n1\nCP\n400 500 60 60 1 20 1 13\n2\nENDCOMP\nENDPCB\n";
QByteArray net(const char* name) { return QByteArray("(\n")+name+"\nU1-1\nU1-2\n)\n"; }
}

class AsyncExperimentTests final:public QObject {
    Q_OBJECT
    QTemporaryDir m_root;
    QString m_directory;
    bool configure(const QString& kind, int skip=0, int watchdog=60000, qint64 owner=QCoreApplication::applicationPid()) {
        m_directory=m_root.filePath(QString::fromLatin1(QTest::currentTestFunction())+QLatin1Char('-')+
            QString::fromLatin1(QTest::currentDataTag()));
        QString error;
        const bool result=pt::experiment::configure({m_directory,kind,owner,skip,watchdog},&error);
        if (!result) qWarning().noquote()<<error;
        return result;
    }
private slots:
    void cleanup() {
        signalGate(m_directory,QStringLiteral("cancel_event"));
        QThreadPool::globalInstance()->waitForDone();
        pt::experiment::shutdown();
        const auto evidence=qEnvironmentVariable("PT_ASYNC_TEST_EVIDENCE");
        if (!evidence.isEmpty() && !m_directory.isEmpty()) {
            const auto output=QDir(evidence).filePath(QFileInfo(m_directory).fileName());
            QVERIFY(QDir().mkpath(output));
            for (const auto& name:QDir(m_directory).entryList(QDir::Files))
                QVERIFY(QFile::copy(QDir(m_directory).filePath(name),QDir(output).filePath(name)));
            const auto inputs=QDir(output).filePath(QStringLiteral("inputs"));
            QVERIFY(QDir().mkpath(inputs)); QJsonObject hashes;
            for (const auto& name:QDir(m_root.path()).entryList({QStringLiteral("*.pcb"),QStringLiteral("*.net")},QDir::Files)) {
                const auto path=m_root.filePath(name); QFile file(path); QVERIFY(file.open(QIODevice::ReadOnly));
                const auto bytes=file.readAll();
                hashes.insert(name,QJsonObject{{QStringLiteral("bytes"),bytes.size()},
                    {QStringLiteral("sha256"),QString::fromLatin1(QCryptographicHash::hash(bytes,QCryptographicHash::Sha256).toHex())}});
                QVERIFY(QFile::copy(path,QDir(inputs).filePath(name)));
            }
            QVERIFY(writeFile(QDir(inputs).filePath(QStringLiteral("manifest.json")),QJsonDocument(hashes).toJson()));
        }
        m_directory.clear();
    }
    void controlledResult_data() {
        QTest::addColumn<QString>("kind"); QTest::addColumn<bool>("edit");
        QTest::newRow("net-control")<<QStringLiteral("net")<<false;
        QTest::newRow("net-edit")<<QStringLiteral("net")<<true;
        QTest::newRow("copper-control")<<QStringLiteral("copper")<<false;
        QTest::newRow("copper-edit")<<QStringLiteral("copper")<<true;
    }
    void controlledResult() {
        QFETCH(QString,kind); QFETCH(bool,edit);
        QVERIFY(configure(kind));
        const auto pcb=m_root.filePath(QStringLiteral("board.pcb"));
        const auto a=m_root.filePath(QStringLiteral("a.net")), b=m_root.filePath(QStringLiteral("b.net"));
        QVERIFY(writeFile(pcb,board)); QVERIFY(writeFile(a,net("NET_A"))); QVERIFY(writeFile(b,net("NET_B")));
        pt::MainWindow window; QVERIFY(window.inspectFile(pcb));
        auto* canvas=window.findChild<pt::BoardCanvas*>();
        auto* browser=window.findChild<pt::NetlistBrowser*>(); QVERIFY(browser->loadFile(a));
        auto* details=browser->findChild<QPlainTextEdit*>(QStringLiteral("netlistDetails"));
        auto* open=browser->findChild<QPushButton*>(QStringLiteral("netlistOpen"));
        const auto previous=browser->netlist(); const auto shaA=previous->sha256;
        QSignalSpy loaded(browser,&pt::NetlistBrowser::netlistLoaded);
        QSignalSpy analyzed(browser,&pt::NetlistBrowser::copperAnalysisFinished);
        int ticks=0; QTimer heartbeat; heartbeat.setInterval(1);
        connect(&heartbeat,&QTimer::timeout,this,[&]{++ticks;}); heartbeat.start();
        if (kind==QStringLiteral("net")) browser->requestFile(b); else browser->runCopperAnalysis();
        QTRY_VERIFY_WITH_TIMEOUT(eventIndex(readEvents(m_directory),QStringLiteral("gate-ready"))>=0,5000);
        const auto requestId=manifest(m_directory).value(QStringLiteral("request_id")).toString();
        QVERIFY(!requestId.isEmpty());
        QTRY_VERIFY(ticks>=2);
        QCOMPARE(eventIndex(readEvents(m_directory),QStringLiteral("worker-returned"),requestId),-1);
        if (edit) {
            QVERIFY(canvas->focusPrimitive({pt::PrimitiveKind::Track,0}));
            QVERIFY(window.deleteSelectedTrack());
            QCOMPARE(canvas->document()->tracks.size(),0); QVERIFY(window.editSession().dirty());
            QCOMPARE(browser->netlist(),previous); QCOMPARE(browser->netlist()->sha256,shaA);
            QVERIFY(!details->toPlainText().contains(QStringLiteral("当前工作文档修订")));
            QCOMPARE(eventIndex(readEvents(m_directory),QStringLiteral("worker-returned"),requestId),-1);
        }
        // 通过实际Python控制器打开同一命名事件，覆盖跨进程身份验证和释放路径。
        const auto python=QStandardPaths::findExecutable(QStringLiteral("python")); QVERIFY(!python.isEmpty());
        const auto script=QFINDTESTDATA("../tools/async_barrier_control.py"); QVERIFY(!script.isEmpty());
        if (kind==QStringLiteral("net") && !edit) {
            const auto wrong=m_root.filePath(QStringLiteral("wrong-identity")); QVERIFY(QDir().mkpath(wrong));
            auto data=manifest(m_directory); data.insert(QStringLiteral("creation_filetime"),QStringLiteral("0"));
            QVERIFY(writeFile(QDir(wrong).filePath(QStringLiteral("request-%1.json").arg(requestId)),QJsonDocument(data).toJson()));
            QProcess rejected; rejected.start(python,{script,QStringLiteral("release"),QStringLiteral("--directory"),wrong,QStringLiteral("--request"),requestId});
            QVERIFY(rejected.waitForFinished(5000)); QVERIFY(rejected.exitCode()!=0);
            QCOMPARE(eventIndex(readEvents(m_directory),QStringLiteral("worker-returned"),requestId),-1);
        }
        QProcess controller; controller.start(python,{script,QStringLiteral("release"),QStringLiteral("--directory"),m_directory,QStringLiteral("--request"),requestId});
        QVERIFY(controller.waitForFinished(5000)); QCOMPARE(controller.exitCode(),0);
        const auto callback=edit?QStringLiteral("callback-discarded"):QStringLiteral("callback-accepted");
        QTRY_VERIFY_WITH_TIMEOUT(eventIndex(readEvents(m_directory),callback,requestId)>=0,5000);
        if (kind==QStringLiteral("net")) {
            QVERIFY(open->isEnabled()); QCOMPARE(loaded.size(),edit?0:1);
            if (edit) {
                QCOMPARE(browser->netlist(),previous); QCOMPARE(browser->netlist()->sha256,shaA);
                QVERIFY(browser->findChild<QLabel*>(QStringLiteral("netlistStatus"))->text().contains(QStringLiteral("结果已放弃")));
            } else {
                QVERIFY(browser->netlist()->sha256!=shaA);
                QVERIFY(details->toPlainText().contains(QStringLiteral("NET_B")));
            }
        } else {
            QVERIFY(!browser->copperAnalysisRunning()); QCOMPARE(analyzed.size(),edit?0:1);
            QCOMPARE(details->toPlainText().contains(QStringLiteral("当前工作文档修订")),!edit);
            if (!edit) QVERIFY(details->toPlainText().contains(QStringLiteral("支持模型内已连接")));
        }
        const auto events=readEvents(m_directory);
        const auto ready=eventIndex(events,QStringLiteral("gate-ready"),requestId);
        const auto release=eventIndex(events,QStringLiteral("gate-released"),requestId);
        const auto returned=eventIndex(events,QStringLiteral("worker-returned"),requestId);
        const auto completed=eventIndex(events,callback,requestId);
        QVERIFY(ready>=0 && ready<release && release<returned && returned<completed);
        if (edit) {
            const auto published=eventIndex(events,QStringLiteral("document-published"));
            QVERIFY(ready<published && published<release);
            QVERIFY(events[published].value(QStringLiteral("dirty")).toBool());
            const auto expectedRevision=QString::number(window.editSession().document()->workingRevision);
            QCOMPARE(events[published].value(QStringLiteral("revision")).toString(),expectedRevision);
        }
        const auto entered=eventIndex(events,QStringLiteral("worker-entered"),requestId);
        QVERIFY(entered>=0 && entered<ready);
        QVERIFY(events[entered].value(QStringLiteral("thread_id"))!=events[completed].value(QStringLiteral("thread_id")));
        qint64 last=-1; quint64 sequence=0;
        for (const auto& event:events) {
            const auto clock=event.value(QStringLiteral("monotonic_ns")).toString().toLongLong();
            QVERIFY(clock>=last); last=clock;
            QCOMPARE(event.value(QStringLiteral("sequence")).toString().toULongLong(),++sequence);
        }
        QCOMPARE(eventIndex(events,QStringLiteral("aborted")),-1);
        QFile input(pcb); QVERIFY(input.open(QIODevice::ReadOnly)); QCOMPARE(input.readAll(),board);
        if (edit) {
            QVERIFY(window.editSession().canUndo());
            // 在竞争时间线结束后直接调用历史模型，不发送桌面键盘输入。
        }
    }
    void skipAndSingleUse() {
        QVERIFY(configure(QStringLiteral("net"),1));
        const auto path=m_root.filePath(QStringLiteral("skip.net")); QVERIFY(writeFile(path,net("SKIP")));
        pt::NetlistBrowser browser; QSignalSpy loaded(&browser,&pt::NetlistBrowser::netlistLoaded);
        browser.requestFile(path); QTRY_COMPARE(loaded.size(),1);
        QCOMPARE(eventIndex(readEvents(m_directory),QStringLiteral("gate-ready")),-1);
        browser.requestFile(path);
        QTRY_VERIFY(eventIndex(readEvents(m_directory),QStringLiteral("gate-ready"))>=0);
        QVERIFY(signalGate(m_directory,QStringLiteral("release_event"))); QTRY_COMPARE(loaded.size(),2);
        browser.requestFile(path); QTRY_COMPARE(loaded.size(),3);
        int gates=0;
        for (const auto& event:readEvents(m_directory)) if (event.value(QStringLiteral("event"))==QStringLiteral("gate-ready")) ++gates;
        QCOMPARE(gates,1);
    }
    void abort_data() {
        QTest::addColumn<QString>("reason");
        QTest::newRow("watchdog")<<QStringLiteral("watchdog");
        QTest::newRow("cancel")<<QStringLiteral("cancel");
        QTest::newRow("owner-exit")<<QStringLiteral("owner-exit");
    }
    void abort() {
        QFETCH(QString,reason);
        QProcess owner;
        qint64 ownerPid=QCoreApplication::applicationPid();
        if (reason==QStringLiteral("owner-exit")) {
            owner.start(QCoreApplication::applicationFilePath(),{QStringLiteral("--async-owner-child")});
            QVERIFY(owner.waitForStarted()); ownerPid=qint64(owner.processId());
        }
        QVERIFY(configure(QStringLiteral("net"),0,reason==QStringLiteral("watchdog")?500:60000,ownerPid));
        const auto path=m_root.filePath(QStringLiteral("abort.net")); QVERIFY(writeFile(path,net("ABORT")));
        pt::NetlistBrowser browser; QSignalSpy loaded(&browser,&pt::NetlistBrowser::netlistLoaded);
        browser.requestFile(path);
        QTRY_VERIFY(eventIndex(readEvents(m_directory),QStringLiteral("gate-ready"))>=0);
        if (reason==QStringLiteral("cancel")) QVERIFY(signalGate(m_directory,QStringLiteral("cancel_event")));
        if (reason==QStringLiteral("owner-exit")) { owner.kill(); QVERIFY(owner.waitForFinished()); }
        QTRY_COMPARE_WITH_TIMEOUT(loaded.size(),1,5000);
        const auto events=readEvents(m_directory);
        const auto aborted=eventIndex(events,QStringLiteral("aborted")); QVERIFY(aborted>=0);
        const auto accepted=eventIndex(events,QStringLiteral("callback-accepted")); QVERIFY(accepted>aborted);
        QVERIFY(events[accepted].value(QStringLiteral("experiment_aborted")).toBool());
        QCOMPARE(eventIndex(events,QStringLiteral("gate-released")),-1);
        // 中止只使实验无效，原产品成功读取和原淘汰条件仍按原路径执行。
        QVERIFY(browser.netlist());
    }
    void refusesGuiThreadGate() {
        QVERIFY(configure(QStringLiteral("net")));
        const auto request=pt::experiment::begin(QStringLiteral("net"),{});
        {
            pt::experiment::Scope scope(request);
            pt::experiment::checkpoint(QStringLiteral("direct-main-thread-check"));
            pt::experiment::returned({});
        }
        pt::experiment::callback(request,true,{});
        const auto events=readEvents(m_directory);
        QVERIFY(eventIndex(events,QStringLiteral("aborted"))>=0);
        QCOMPARE(eventIndex(events,QStringLiteral("gate-ready")),-1);
    }
    void refusesEvidenceReuseAndInvalidConfig() {
        QVERIFY(configure(QStringLiteral("net")));
        QString error;
        QVERIFY(!pt::experiment::configure({m_directory,QStringLiteral("net"),QCoreApplication::applicationPid()},&error));
        pt::experiment::shutdown();
        QVERIFY(!pt::experiment::configure({m_directory,QStringLiteral("net"),QCoreApplication::applicationPid()},&error));
        QVERIFY(!pt::experiment::configure({m_root.filePath(QStringLiteral("invalid")),QStringLiteral("bad"),0},&error));
    }
};

int main(int argc,char** argv) {
    if (argc==2 && QByteArray(argv[1])=="--async-owner-child") { Sleep(30000); return 0; }
    QApplication app(argc,argv);
    AsyncExperimentTests tests;
    return QTest::qExec(&tests,argc,argv);
}
#include "AsyncExperimentTests.moc"
