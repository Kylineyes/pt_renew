#include "ui/MainWindow.h"

#include "application/CommandCatalog.h"
#include "io/LegacyPcbInspector.h"
#include "ui/BoardCanvas.h"
#include <QAction>
#include <QDockWidget>
#include <QFileDialog>
#include <QFileInfo>
#include <QLabel>
#include <QMenu>
#include <QMenuBar>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QStatusBar>

namespace pt {

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent) {
    setObjectName(QStringLiteral("mainWindow"));
    setWindowTitle(QStringLiteral("PT Renew · AUTOTRAX 重建 · 第一阶段"));
    resize(1440, 850);
    m_canvas = new BoardCanvas(this);
    setCentralWidget(m_canvas);
    m_infoDock = new QDockWidget(QStringLiteral("文件信息（只读探测）"), this);
    m_infoDock->setObjectName(QStringLiteral("fileInfoDock"));
    m_infoText = new QPlainTextEdit(m_infoDock);
    m_infoText->setObjectName(QStringLiteral("fileInfoText"));
    m_infoText->setReadOnly(true);
    m_infoText->setMinimumWidth(280);
    m_infoDock->setWidget(m_infoText);
    addDockWidget(Qt::RightDockWidgetArea, m_infoDock);
    m_viewStatus = new QLabel(this);
    m_viewStatus->setObjectName(QStringLiteral("viewStatus"));
    statusBar()->addPermanentWidget(m_viewStatus);
    createMenus();
    clearFileInfo();
    updateViewStatus();
    connect(m_canvas, &BoardCanvas::legacyMenuRequested, this, &MainWindow::showLegacyMenu);
    connect(m_canvas, &BoardCanvas::viewChanged, this, &MainWindow::updateViewStatus);
    m_canvas->setFocus();
}

void MainWindow::createMenus() {
    menuBar()->setNativeMenuBar(false);
    for (const auto& spec : commandCatalog()) {
        auto* menu = menuBar()->addMenu(spec.title);
        menu->setObjectName(QStringLiteral("menu.") + spec.key);
        menu->setToolTipsVisible(true);
        m_menus.insert(spec.key, menu);
        for (const auto& command : spec.commands) {
            QAction* action = m_actions.value(command.id, nullptr);
            if (!action) {
                action = new QAction(command.text, this);
                action->setObjectName(command.id);
                action->setEnabled(command.implemented);
                action->setCheckable(command.checkable);
                if (command.checkable) action->setChecked(true);
                QList<QKeySequence> keys;
                for (const auto& shortcut : command.shortcuts) {
                    keys.append(QKeySequence(shortcut, QKeySequence::PortableText));
                }
                action->setShortcuts(keys);
                action->setShortcutContext(Qt::WindowShortcut);
                if (!command.implemented) {
                    action->setText(command.text + QStringLiteral("（未实现）"));
                    action->setToolTip(QStringLiteral("已保留命令入口，当前阶段尚未实现此业务。"));
                }
                connect(action, &QAction::triggered, this, [this, id = command.id] { executeCommand(id); });
                m_actions.insert(command.id, action);
            }
            menu->addAction(action);
        }
    }
}

void MainWindow::showLegacyMenu(const QString& key) {
    auto* menu = m_menus.value(key, nullptr);
    if (!menu) return;
    const QRect geometry = menuBar()->actionGeometry(menu->menuAction());
    menu->popup(menuBar()->mapToGlobal(geometry.bottomLeft()));
}

void MainWindow::executeCommand(const QString& id) {
    emit commandInvoked(id);
    if (id == QStringLiteral("file.inspect")) {
        const QString file = QFileDialog::getOpenFileName(this, QStringLiteral("查看旧 PCB 文件信息"), {},
            QStringLiteral("AUTOTRAX 板图 (*.pcb *.PCB *.abk *.ABK);;所有文件 (*)"));
        if (!file.isEmpty()) inspectFile(file);
    } else if (id == QStringLiteral("file.close")) {
        clearFileInfo();
    } else if (id == QStringLiteral("app.exit")) {
        close();
    } else if (id == QStringLiteral("view.grid")) {
        m_canvas->setGridVisible(m_actions.value(id)->isChecked());
    } else if (id == QStringLiteral("view.zoom_in")) {
        m_canvas->zoomIn();
    } else if (id == QStringLiteral("view.zoom_out")) {
        m_canvas->zoomOut();
    } else if (id == QStringLiteral("view.reset")) {
        m_canvas->resetView();
    } else if (id == QStringLiteral("view.center")) {
        m_canvas->centerView();
    } else if (id == QStringLiteral("view.redraw")) {
        m_canvas->update();
    } else if (id == QStringLiteral("info.file")) {
        m_infoDock->show();
        m_infoDock->raise();
    } else if (id == QStringLiteral("app.about")) {
        QMessageBox::information(this, QStringLiteral("关于当前阶段"),
            QStringLiteral("C++ + Qt 6 的 AUTOTRAX 重建工程。\n\n"
                           "当前仅实现菜单/快捷键、空白视图与只读文件信息探测。\n"
                           "尚未解析图元，不支持编辑、保存、DRC、布线和生产输出。"));
    }
    statusBar()->showMessage(QStringLiteral("命令：%1").arg(id), 4000);
}

bool MainWindow::inspectFile(const QString& path) {
    const auto result = LegacyPcbInspector::inspect(path);
    if (!result.succeeded()) {
        clearFileInfo();
        statusBar()->showMessage(result.error, 15000);
        m_infoDock->show();
        m_infoText->setPlainText(QStringLiteral("探测失败：%1\n\n本次没有载入或修改任何板图。").arg(result.error));
        return false;
    }
    const auto& info = result.info;
    QString text = QStringLiteral("仅查看文件信息，尚未解析或显示图元。\n\n"
                                  "文件：%1\n格式：PCB FILE 4\n大小：%2 字节\n\nSHA-256：\n%3\n\n"
                                  "标记行计数（不是语义解析结果）：\n")
                       .arg(info.filePath).arg(info.byteSize).arg(info.sha256);
    for (auto it = info.markerCounts.cbegin(); it != info.markerCounts.cend(); ++it) {
        text += QStringLiteral("%1：%2\n").arg(it.key()).arg(it.value());
    }
    text += QStringLiteral("\n源文件仅以只读方式打开。\n当前不支持保存、编辑或生产输出。");
    m_infoText->setPlainText(text);
    m_infoDock->show();
    m_infoDock->raise();
    m_actions.value(QStringLiteral("file.close"))->setEnabled(true);
    setWindowTitle(QStringLiteral("%1 · 文件信息 · PT Renew").arg(QFileInfo(path).fileName()));
    statusBar()->showMessage(QStringLiteral("已读取文件信息，尚未载入板图图元。"), 10000);
    return true;
}

void MainWindow::clearFileInfo() {
    m_infoText->setPlainText(QStringLiteral("尚未打开文件。\n\n"
        "Ctrl+O：查看 PCB 文件信息。\n"
        "画布内按 F，再按 L：同一命令的旧式入口。\n\n"
        "第一阶段不支持图元显示、编辑或保存。"));
    m_actions.value(QStringLiteral("file.close"))->setEnabled(false);
    setWindowTitle(QStringLiteral("PT Renew · AUTOTRAX 重建 · 第一阶段"));
}

void MainWindow::updateViewStatus() {
    m_viewStatus->setText(QStringLiteral("缩放 %1%　网格%2　只读探测阶段")
        .arg(qRound(m_canvas->zoom() * 100)).arg(m_canvas->gridVisible() ? QStringLiteral("开") : QStringLiteral("关")));
}

}
