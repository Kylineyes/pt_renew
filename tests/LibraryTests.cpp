#include "io/LegacyLibraryReader.h"
#include "ui/LibraryBrowser.h"
#include "ui/MainWindow.h"
#include "ui/BoardCanvas.h"
#include "geometry/BoardGeometry.h"
#include <QAction>
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QStandardPaths>
#include <QProcess>
#include <QMenu>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QtTest/QTest>

namespace {
// 合成测试文件仅按已分析布局生成，不包含原始库数据。
void putWord(QByteArray& bytes,qsizetype offset,int value) {
    const auto word=static_cast<quint16>(value);
    bytes[offset]=char(word&255); bytes[offset+1]=char(word>>8);
}
QByteArray record(int layer,int type) {
    QByteArray bytes(16,'\0'); bytes[0]=char(layer); bytes[1]=char(type); return bytes;
}
QByteArray stringRecord(int type,const QByteArray& text) {
    auto bytes=record(0,type); bytes[2]=char(text.size()); bytes.replace(3,text.size(),text); return bytes;
}
QByteArray track() {
    auto bytes=record(7,5); putWord(bytes,2,-100); putWord(bytes,6,100); putWord(bytes,10,12); return bytes;
}
QByteArray allPrimitives() {
    auto arc=record(7,1); putWord(arc,2,-20); putWord(arc,4,30); putWord(arc,6,50); arc[8]=5; arc[9]=10;
    auto fill=record(6,2); putWord(fill,2,-20); putWord(fill,4,-30); putWord(fill,6,10); putWord(fill,8,20);
    auto pad=record(13,3); putWord(pad,2,100); putWord(pad,4,200); putWord(pad,6,60); putWord(pad,8,80); putWord(pad,10,20); pad[12]=2; pad[13]=1;
    auto text=record(7,6); putWord(text,2,10); putWord(text,4,20); putWord(text,6,40); text[8]=4; text[9]=17;
    auto via=record(0,8); putWord(via,2,-50); putWord(via,4,-60); via[6]=30; via[7]=10; via[8]=1;
    return arc+fill+pad+stringRecord(4,"P1")+track()+text+stringRecord(7,"ABC")+via;
}
struct Entry { int slot; QByteArray name; int count; QByteArray body; };
QByteArray library(const QList<Entry>& entries) {
    QByteArray bytes(6416,'\0'); bytes.replace(0,16,QByteArray("\0\0\x0d" "PCB 4 LIBRARY",16));
    for (int slot=0;slot<200;++slot) { putWord(bytes,16+slot*32+18,65535); putWord(bytes,16+slot*32+20,65535); }
    for (const auto& entry : entries) {
        const int offset=16+entry.slot*32; bytes[offset+2]=char(entry.name.size()); bytes.replace(offset+3,entry.name.size(),entry.name);
        putWord(bytes,offset+18,entry.count); putWord(bytes,offset+20,int(bytes.size()/16)); bytes+=entry.body;
    }
    return bytes;
}
}

class LibraryTests final : public QObject {
    Q_OBJECT
private slots:
    void decodesAllTypesAndSourceOffsets() {
        const auto bytes=library({{0,"OWN_TEST",6,allPrimitives()}});
        const auto result=pt::LegacyLibraryReader::parse(bytes,QStringLiteral("fixture.lib"));
        QVERIFY2(result.succeeded(),qPrintable(result.error));
        QCOMPARE(result.library->entries.size(),1); QCOMPARE(result.library->unallocatedSlots,199);
        const auto& entry=result.library->entries[0]; QVERIFY2(entry.preview!=nullptr,qPrintable(entry.error));
        const auto& b=*entry.preview;
        QCOMPARE(b.primitiveCount(),6); QCOMPARE(b.arcs[0].center,QPointF(-20,30)); QCOMPARE(b.arcs[0].quadrants,5); QCOMPARE(b.arcs[0].width,10);
        QCOMPARE(b.fills[0].rectangle,QRectF(-20,-30,30,50));
        QCOMPARE(b.pads[0].center,QPointF(100,200)); QCOMPARE(b.pads[0].drill,20); QCOMPARE(b.pads[0].name,QStringLiteral("P1"));
        QCOMPARE(b.texts[0].height,40); QCOMPARE(b.texts[0].stroke,4); QCOMPARE(b.texts[0].direction,1); QVERIFY(b.texts[0].mirrored);
        QCOMPARE(b.vias[0].diameter,30); QCOMPARE(b.vias[0].drill,10);
        QCOMPARE(b.arcs[0].source.byteOffset,6416); QCOMPARE(b.arcs[0].source.line,0);
        QCOMPARE(entry.endRecord,409);
        QVERIFY(pt::primitiveDescription(b,{pt::PrimitiveKind::Pad,0}).contains(QStringLiteral("源文件字节偏移")));
        QVERIFY(pt::primitiveDescription(b,{pt::PrimitiveKind::Pad,0}).contains(QStringLiteral("独立预览，未放置")));
        QCOMPARE(result.library->sourceBytes,bytes);
    }
    void directoryOrderIsNotPhysicalOrder() {
        const auto result=pt::LegacyLibraryReader::parse(library({{5,"FIRST",1,track()},{0,"SECOND",1,track()}}));
        QVERIFY(result.succeeded());
        QCOMPARE(result.library->entries[0].name,QStringLiteral("SECOND"));
        QCOMPARE(result.library->entries[0].firstRecord,402);
        QVERIFY(result.library->entries[0].preview); QVERIFY(result.library->entries[1].preview);
    }
    void unallocatedNamesAreNotUsableEntries() {
        auto bytes=library({{0,"OWN_TEST",1,track()}});
        bytes[16+32+2]=4; bytes.replace(16+32+3,4,"OLDX"); putWord(bytes,16+32+18,5);
        const auto result=pt::LegacyLibraryReader::parse(bytes);
        QVERIFY(result.succeeded()); QCOMPARE(result.library->entries.size(),1); QCOMPARE(result.library->retainedNameSlots,1);
    }
    void rejectsBrokenCatalog_data() {
        QTest::addColumn<int>("variant");
        QTest::newRow("signature")<<0; QTest::newRow("short")<<1; QTest::newRow("misaligned")<<2;
        QTest::newRow("pointer-into-directory")<<3; QTest::newRow("pointer-beyond-eof")<<4;
        QTest::newRow("oversized-name")<<5; QTest::newRow("duplicate-pointer")<<6;
    }
    void rejectsBrokenCatalog() {
        QFETCH(int,variant);
        auto bytes=library({{0,"ONE",1,track()},{1,"TWO",1,track()}});
        switch (variant) {
        case 0: bytes[3]='X'; break; case 1: bytes.resize(100); break; case 2: bytes.append('x'); break;
        case 3: putWord(bytes,36,10); break; case 4: putWord(bytes,36,60000); break;
        case 5: bytes[18]=16; break; case 6: putWord(bytes,16+32+20,401); break;
        }
        const auto result=pt::LegacyLibraryReader::parse(bytes); QVERIFY(!result.succeeded()); QVERIFY(!result.error.isEmpty());
    }
    void badEntryDoesNotReturnPartialGeometry_data() {
        QTest::addColumn<int>("variant");
        QTest::newRow("unknown-type")<<0; QTest::newRow("missing-name")<<1;
        QTest::newRow("reserved-bits")<<2; QTest::newRow("record-count-too-large")<<3;
        QTest::newRow("bad-pad-shape")<<4; QTest::newRow("bad-via-diameter")<<5;
    }
    void badEntryDoesNotReturnPartialGeometry() {
        QFETCH(int,variant);
        auto body=allPrimitives();
        if (variant==0) body[1]=99;
        if (variant==1) body[3*16+1]=5;
        if (variant==2) body[15]=1;
        if (variant==4) body[2*16+12]=5;
        if (variant==5) body[7*16+7]=31;
        const auto result=pt::LegacyLibraryReader::parse(library({{0,"BAD",variant==3?7:6,body},{1,"GOOD",1,track()}}));
        QVERIFY(result.succeeded()); QVERIFY(!result.library->entries[0].preview); QVERIFY(!result.library->entries[0].error.isEmpty());
        QVERIFY(result.library->entries[1].preview);
    }
    void directoryFlagsAndStringOverflowAreVisibleErrors() {
        auto bytes=library({{0,"OWN_TEST",6,allPrimitives()}}); bytes[38]=1;
        auto result=pt::LegacyLibraryReader::parse(bytes); QVERIFY(result.succeeded()); QVERIFY(!result.library->entries[0].preview);
        bytes=library({{0,"OWN_TEST",6,allPrimitives()}}); bytes[6416+3*16+2]=14;
        result=pt::LegacyLibraryReader::parse(bytes); QVERIFY(result.succeeded()); QVERIFY(!result.library->entries[0].preview);
    }
    void enforcesResourceLimits() {
        const auto large=pt::LegacyLibraryReader::parse(QByteArray(8*1024*1024+16,'\0')); QVERIFY(!large.succeeded());
        const auto aggregate=pt::LegacyLibraryReader::parse(library({{0,"A",65534,track()},{1,"B",65534,track()},{2,"C",65534,track()},{3,"D",65534,track()}}));
        QVERIFY(!aggregate.succeeded()); QVERIFY(aggregate.error.contains(QStringLiteral("200000")));
        const auto single=pt::LegacyLibraryReader::parse(library({{0,"A",20001,track()}}));
        QVERIFY(single.succeeded()); QVERIFY(!single.library->entries[0].preview); QVERIFY(single.library->entries[0].error.contains(QStringLiteral("20000")));
    }
    void diagnosticToolDistinguishesPartialAndInvalidLibraries() {
        QTemporaryDir directory; const auto path=directory.filePath(QStringLiteral("fixture.lib"));
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); file.write(library({{0,"BAD",1,record(1,99)},{1,"GOOD",1,track()}})); file.close();
        const auto executable=QStandardPaths::findExecutable(QStringLiteral("pt-library-check"),{QCoreApplication::applicationDirPath()}); QVERIFY(!executable.isEmpty());
        QProcess process; process.start(executable,{path});
        QVERIFY(process.waitForFinished(10000)); QCOMPARE(process.exitCode(),2);
        const auto output=QJsonDocument::fromJson(process.readAllStandardOutput()); QVERIFY(output.isArray()); QVERIFY(!output.array().isEmpty());
        const auto report=output.array().first().toObject();
        QCOMPARE(report.value(QStringLiteral("previewable")).toInt(),1); QCOMPARE(report.value(QStringLiteral("problems")).toArray().size(),1);
        QVERIFY(file.open(QIODevice::WriteOnly)); file.write("invalid"); file.close();
        process.start(executable,{path});
        QVERIFY(process.waitForFinished(10000)); QCOMPARE(process.exitCode(),1);
        const auto invalidOutput=QJsonDocument::fromJson(process.readAllStandardOutput()); QVERIFY(invalidOutput.isArray()); QVERIFY(!invalidOutput.array().isEmpty());
        QVERIFY(invalidOutput.array().first().toObject().contains(QStringLiteral("error")));
    }

    void browserFiltersAndClearsStalePreview() {
        QTemporaryDir directory; const auto path=directory.filePath(QStringLiteral("fixture.lib"));
        const auto bytes=library({{0,"AXIAL_TEST",6,allPrimitives()},{1,"BROKEN",1,record(1,99)}});
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); file.write(bytes); file.close();
        pt::LibraryBrowser browser; browser.showBrowser(); QVERIFY(QTest::qWaitForWindowExposed(&browser));
        QVERIFY(browser.loadLibrary(path));
        auto* canvas=browser.findChild<pt::BoardCanvas*>(); QVERIFY(canvas->document());
        auto* search=browser.findChild<QLineEdit*>(QStringLiteral("librarySearch"));
        search->setText(QStringLiteral("broken")); QVERIFY(!canvas->document());
        QVERIFY(browser.findChild<QPlainTextEdit*>(QStringLiteral("libraryDetails"))->toPlainText().contains(QStringLiteral("禁止预览")));
        search->setText(QStringLiteral("[")); QVERIFY(!canvas->document());
        search->setText(QStringLiteral("axial")); QVERIFY(canvas->document());
        QVERIFY(browser.findChild<QPlainTextEdit*>(QStringLiteral("libraryDetails"))->isReadOnly());
        QVERIFY(file.open(QIODevice::ReadOnly)); QCOMPARE(file.readAll(),bytes); file.close();
        QVERIFY(!browser.loadLibrary(directory.filePath(QStringLiteral("missing.lib")))); QVERIFY(!canvas->document()); QVERIFY(!browser.library());
    }
    void asynchronousCancelCannotRestoreOldLibrary() {
        QTemporaryDir directory; const auto path=directory.filePath(QStringLiteral("fixture.lib"));
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); file.write(library({{0,"OWN_TEST",1,track()}})); file.close();
        pt::LibraryBrowser browser;
        QSignalSpy loaded(&browser,&pt::LibraryBrowser::libraryLoaded);
        browser.requestLibrary(path); browser.clearLibrary();
        QTRY_VERIFY(browser.findChild<QPushButton*>(QStringLiteral("libraryOpen"))->isEnabled());
        QVERIFY(!browser.library()); QCOMPARE(loaded.size(),0);
        browser.requestLibrary(path); QTRY_COMPARE(loaded.size(),1); QVERIFY(loaded.last()[0].toBool()); QVERIFY(browser.library());
    }
    void dialogKeyboardStaysLocalAndEscapeClearsSelection() {
        QTemporaryDir directory;
        QFile pcb(directory.filePath(QStringLiteral("board.pcb"))); QVERIFY(pcb.open(QIODevice::WriteOnly));
        pcb.write("PCB FILE 4\nCOMP\nU1\nDIP\nV\n0 0 10 0 1 7\n0 0 10 0 1 7\n0 0 2 2 2\nCP\n0 0 60 60 1 20 1 13\n1\nENDCOMP\nENDPCB\n"); pcb.close();
        QFile lib(directory.filePath(QStringLiteral("fixture.lib"))); QVERIFY(lib.open(QIODevice::WriteOnly)); lib.write(library({{0,"OWN_TEST",6,allPrimitives()}})); lib.close();
        pt::MainWindow window; window.show(); QVERIFY(QTest::qWaitForWindowExposed(&window)); QVERIFY(window.inspectFile(pcb.fileName()));
        auto* browser=window.findChild<pt::LibraryBrowser*>(); QVERIFY(browser->loadLibrary(lib.fileName())); browser->showBrowser();
        QVERIFY(QTest::qWaitForWindowExposed(browser)); QVERIFY(QTest::qWaitForWindowActive(browser));
        auto* preview=browser->findChild<pt::BoardCanvas*>();
        QTest::mouseClick(preview,Qt::LeftButton,Qt::NoModifier,preview->boardToScreen({100,200}).toPoint());
        QVERIFY(preview->selection());
        QVERIFY(browser->findChild<QPlainTextEdit*>(QStringLiteral("libraryDetails"))->toPlainText().contains(QStringLiteral("源文件字节偏移")));
        QTest::keyClick(preview,Qt::Key_F,Qt::ControlModifier);
        auto* search=browser->findChild<QLineEdit*>(QStringLiteral("librarySearch")); QTRY_VERIFY(search->hasFocus());
        QTest::keyClicks(search,"own"); QVERIFY(preview->selection());
        preview->setFocus(); QTest::keyClick(preview,Qt::Key_Escape);
        QVERIFY(!preview->selection()); QVERIFY(browser->isVisible());
        QTest::keyClick(preview,Qt::Key_Escape); QTRY_VERIFY(!browser->isVisible());
    }

    void browsingLibraryCannotReplaceMainBoard() {
        QTemporaryDir directory;
        QFile pcb(directory.filePath(QStringLiteral("board.pcb"))); QVERIFY(pcb.open(QIODevice::WriteOnly)); pcb.write("PCB FILE 4\nENDPCB\n"); pcb.close();
        QFile lib(directory.filePath(QStringLiteral("fixture.lib"))); QVERIFY(lib.open(QIODevice::WriteOnly)); lib.write(library({{0,"OWN_TEST",1,track()}})); lib.close();
        pt::MainWindow window; window.show(); QVERIFY(QTest::qWaitForWindowExposed(&window)); QVERIFY(window.inspectFile(pcb.fileName()));
        auto* board=window.findChild<pt::BoardCanvas*>(); const auto* original=board->document();
        window.activateWindow(); QVERIFY(QTest::qWaitForWindowActive(&window));
        QSignalSpy commands(&window,&pt::MainWindow::commandInvoked);
        board->setFocus(); QTest::keyClick(board,Qt::Key_L);
        auto* menu=window.findChild<QMenu*>(QStringLiteral("menu.L")); QTRY_VERIFY(menu->isVisible());
        QTest::keyClick(menu,Qt::Key_B);
        auto* browser=window.findChild<pt::LibraryBrowser*>(); QTRY_VERIFY(browser->isVisible());
        QVERIFY(!commands.isEmpty()); QCOMPARE(commands.last().at(0).toString(),QStringLiteral("library.browse"));
        browser->hide(); window.activateWindow(); QVERIFY(QTest::qWaitForWindowActive(&window));
        board->setFocus(); QTest::keyClick(board,Qt::Key_L,Qt::ControlModifier); QTRY_VERIFY(browser->isVisible());
        QCOMPARE(commands.last().at(0).toString(),QStringLiteral("library.browse"));
        QVERIFY(browser->loadLibrary(lib.fileName()));
        QCOMPARE(board->document(),original); QCOMPARE(board->document()->primitiveCount(),0);
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("place.component"))->isEnabled());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.save"))->isEnabled());
        window.findChild<QAction*>(QStringLiteral("file.close"))->trigger(); QVERIFY(browser->library());
        browser->clearLibrary(); QVERIFY(!board->document());
    }
};
QTEST_MAIN(LibraryTests)
#include "LibraryTests.moc"
