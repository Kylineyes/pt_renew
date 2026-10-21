#include "application/CommandCatalog.h"
#include "io/LegacyPcbInspector.h"
#include "ui/BoardCanvas.h"
#include "ui/MainWindow.h"

#include <QAction>
#include <QApplication>
#include <QCryptographicHash>
#include <QFile>
#include <QLineEdit>
#include <QMenu>
#include <QMenuBar>
#include <QPlainTextEdit>
#include <QSet>
#include <QSignalSpy>
#include <QTemporaryDir>
#include <QtTest/QTest>

class ShellTests final : public QObject {
    Q_OBJECT
private:
    static void expose(pt::MainWindow& window) {
        window.show();
        window.activateWindow();
        QVERIFY(QTest::qWaitForWindowExposed(&window));
        QVERIFY(QTest::qWaitForWindowActive(&window));
    }

private slots:
    void catalogHasSeventeenUniqueEntries() {
        const auto& menus = pt::commandCatalog();
        QCOMPARE(menus.size(), 17);
        QSet<QString> menuKeys;
        QSet<QString> commandIds;
        QSet<QString> shortcuts;
        for (const auto& menu : menus) {
            QVERIFY(!menuKeys.contains(menu.key));
            QVERIFY(menu.title.contains(QStringLiteral("&") + menu.key));
            menuKeys.insert(menu.key);
            QVERIFY(!menu.commands.isEmpty());
            for (const auto& command : menu.commands) {
                QVERIFY(!commandIds.contains(command.id));
                commandIds.insert(command.id);
                for (const auto& key : command.shortcuts) {
                    QVERIFY(!shortcuts.contains(key));
                    shortcuts.insert(key);
                }
            }
        }
    }

    void inspectionDoesNotChangeInput() {
        QTemporaryDir temporary;
        QVERIFY(temporary.isValid());
        const QString path = temporary.filePath(QStringLiteral("样例.PCB"));
        const QByteArray original("PCB FILE 4\r\nFT\r\n10 20 30 40 12 1\r\nFV\r\n10 20 24 12\r\nENDPCB\r\n");
        QFile file(path);
        QVERIFY(file.open(QIODevice::WriteOnly));
        QCOMPARE(file.write(original), original.size());
        file.close();
        const auto result = pt::LegacyPcbInspector::inspect(path);
        QVERIFY2(result.succeeded(), qPrintable(result.error));
        QCOMPARE(result.info.byteSize, original.size());
        QCOMPARE(result.info.markerCounts.value(QStringLiteral("FT")), 1);
        QCOMPARE(result.info.markerCounts.value(QStringLiteral("FV")), 1);
        QCOMPARE(result.info.sha256, QString::fromLatin1(QCryptographicHash::hash(original, QCryptographicHash::Sha256).toHex()));
        QVERIFY(file.open(QIODevice::ReadOnly));
        QCOMPARE(file.readAll(), original);
    }

    void invalidFileBoundariesAreRejected_data() {
        QTest::addColumn<QByteArray>("bytes");
        QTest::newRow("unsupported-header") << QByteArray("PCB FILE 5\nENDPCB\n");
        QTest::newRow("truncated") << QByteArray("PCB FILE 4\nFT\n1 2 3\n");
        QTest::newRow("trailing-record") << QByteArray("PCB FILE 4\nENDPCB\nFT\n");
        QTest::newRow("empty") << QByteArray();
        QTest::newRow("binary") << (QByteArray("PCB FILE 4\n") + QByteArray(1, '\0') + QByteArray("\nENDPCB\n"));
    }

    void invalidFileBoundariesAreRejected() {
        QFETCH(QByteArray, bytes);
        QTemporaryDir temporary;
        QFile file(temporary.filePath(QStringLiteral("invalid.pcb")));
        QVERIFY(file.open(QIODevice::WriteOnly));
        QCOMPARE(file.write(bytes), bytes.size());
        file.close();
        const auto result = pt::LegacyPcbInspector::inspect(file.fileName());
        QVERIFY(!result.succeeded());
        QVERIFY(!result.error.isEmpty());
    }

    void nonexistentFileIsRejected() {
        QTemporaryDir temporary;
        QVERIFY(!pt::LegacyPcbInspector::inspect(temporary.filePath(QStringLiteral("missing.pcb"))).succeeded());
    }

    void oversizedFilesAreRejectedBeforeReading() {
        QTemporaryDir temporary;
        QFile file(temporary.filePath(QStringLiteral("oversized.pcb")));
        QVERIFY(file.open(QIODevice::WriteOnly));
        QVERIFY(file.resize(64 * 1024 * 1024 + 1));
        file.close();
        const auto result = pt::LegacyPcbInspector::inspect(file.fileName());
        QVERIFY(!result.succeeded());
        QVERIFY(result.error.contains(QStringLiteral("64 MiB")));
    }

    void unimplementedEditingCannotExecute() {
        pt::MainWindow window;
        for (const auto& menu : pt::commandCatalog()) {
            for (const auto& spec : menu.commands) {
                auto* action = window.findChild<QAction*>(spec.id);
                QVERIFY(action);
                if (!spec.implemented) {
                    QVERIFY(!action->isEnabled());
                    QVERIFY(action->text().contains(QStringLiteral("未实现")));
                }
            }
        }
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.close"))->isEnabled());
    }

    void allLegacyMenuKeysWork() {
        pt::MainWindow window;
        expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        QVERIFY(canvas);
        for (const auto& spec : pt::commandCatalog()) {
            canvas->setFocus();
            QTest::keyClick(canvas, static_cast<Qt::Key>(spec.key.front().unicode()));
            auto* menu = window.findChild<QMenu*>(QStringLiteral("menu.") + spec.key);
            QVERIFY(menu);
            QTRY_VERIFY(menu->isVisible());
            QTest::keyClick(menu, Qt::Key_Escape);
            QTRY_VERIFY(!menu->isVisible());
        }
    }

    void altMenuAccessWorks() {
        pt::MainWindow window;
        expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        canvas->setFocus();
        QTest::keyClick(canvas, Qt::Key_F, Qt::AltModifier);
        auto* menu = window.findChild<QMenu*>(QStringLiteral("menu.F"));
        QTRY_VERIFY(menu->isVisible());
        QTest::keyClick(menu, Qt::Key_Escape);
    }

    void textFieldsKeepTheirLetters() {
        pt::MainWindow window;
        expose(window);
        QLineEdit edit(&window);
        edit.setGeometry(50, 160, 240, 36);
        edit.show();
        edit.raise();
        edit.setFocus();
        QTest::keyClicks(&edit, "file");
        QCOMPARE(edit.text(), QStringLiteral("file"));
        QVERIFY(QApplication::activePopupWidget() == nullptr);
    }

    void menuAndShortcutUseTheSameCommand() {
        pt::MainWindow window;
        expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        auto* action = window.findChild<QAction*>(QStringLiteral("view.grid"));
        auto* menu = window.findChild<QMenu*>(QStringLiteral("menu.G"));
        QSignalSpy spy(&window, &pt::MainWindow::commandInvoked);
        canvas->setFocus();
        QTest::keyClick(canvas, Qt::Key_G);
        QTRY_VERIFY(menu->isVisible());
        QTest::mouseClick(menu, Qt::LeftButton, Qt::NoModifier, menu->actionGeometry(action).center());
        QTRY_COMPARE(spy.size(), 1);
        QCOMPARE(spy.at(0).at(0).toString(), QStringLiteral("view.grid"));
        QVERIFY(!canvas->gridVisible());
        QVERIFY(!action->isChecked());
        canvas->setFocus();
        QTest::keyClick(canvas, Qt::Key_G, Qt::ControlModifier);
        QTRY_COMPARE(spy.size(), 2);
        QCOMPARE(spy.at(1).at(0).toString(), QStringLiteral("view.grid"));
        QVERIFY(canvas->gridVisible());
        QVERIFY(action->isChecked());
    }

    void legacyZoomKeysWork() {
        pt::MainWindow window;
        expose(window);
        auto* canvas = window.findChild<pt::BoardCanvas*>();
        canvas->setFocus();
        QCOMPARE(canvas->zoom(), 1.0);
        QTest::keyClick(canvas, Qt::Key_F6);
        QTRY_VERIFY(canvas->zoom() > 1.0);
        QTest::keyClick(canvas, Qt::Key_F5);
        QTRY_VERIFY(qAbs(canvas->zoom() - 1.0) < 0.0001);
        for (int i = 0; i < 100; ++i) canvas->zoomOut();
        QCOMPARE(canvas->zoom(), 0.125);
        for (int i = 0; i < 100; ++i) canvas->zoomIn();
        QCOMPARE(canvas->zoom(), 16.0);
    }

    void readOnlyBoardKeepsEditingDisabled() {
        QTemporaryDir temporary;
        const QString path = temporary.filePath(QStringLiteral("sample.pcb"));
        QFile file(path);
        QVERIFY(file.open(QIODevice::WriteOnly));
        file.write("PCB FILE 4\nENDPCB\n");
        file.close();
        pt::MainWindow window;
        QVERIFY(window.inspectFile(path));
        auto* text = window.findChild<QPlainTextEdit*>(QStringLiteral("fileInfoText"));
        QVERIFY(text->toPlainText().contains(QStringLiteral("只读预览")));
        QVERIFY(window.findChild<QAction*>(QStringLiteral("file.close"))->isEnabled());
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.save"))->isEnabled());
        window.findChild<QAction*>(QStringLiteral("file.close"))->trigger();
        QVERIFY(text->toPlainText().contains(QStringLiteral("尚未打开文件")));
        QVERIFY(window.inspectFile(path));
        QVERIFY(!window.inspectFile(temporary.filePath(QStringLiteral("missing.pcb"))));
        QVERIFY(!window.windowTitle().contains(QStringLiteral("sample.pcb")));
        QVERIFY(!window.findChild<QAction*>(QStringLiteral("file.close"))->isEnabled());
        QVERIFY(text->toPlainText().contains(QStringLiteral("探测失败")));
    }
};

QTEST_MAIN(ShellTests)
#include "ShellTests.moc"
