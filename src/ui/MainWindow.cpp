#include "ui/MainWindow.h"

#include "application/CommandCatalog.h"
#include "io/LegacyPcbReader.h"
#include "ui/BoardRenderer.h"
#include <QListWidget>
#include <QIcon>
#include <QPixmap>
#include "ui/BoardCanvas.h"
#include <QFutureWatcher>
#include <QtConcurrent/QtConcurrentRun>
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
    setWindowTitle(QStringLiteral("PT Renew · AUTOTRAX 重建 · 只读预览"));
    resize(1440, 850);
    m_canvas = new BoardCanvas(this);
    setCentralWidget(m_canvas);
    m_infoDock = new QDockWidget(QStringLiteral("板图信息（只读）"), this);
    m_infoDock->setObjectName(QStringLiteral("fileInfoDock"));
    m_infoText = new QPlainTextEdit(m_infoDock);
    m_infoText->setObjectName(QStringLiteral("fileInfoText"));
    m_infoText->setReadOnly(true);
    m_infoText->setMinimumWidth(280);
    m_infoDock->setWidget(m_infoText);
    addDockWidget(Qt::RightDockWidgetArea, m_infoDock);
    m_selectionDock=new QDockWidget(QStringLiteral("图元属性（只读）"),this);
    m_selectionDock->setObjectName(QStringLiteral("selectionDock"));
    m_selectionText=new QPlainTextEdit(m_selectionDock);
    m_selectionText->setObjectName(QStringLiteral("selectionText"));
    m_selectionText->setReadOnly(true);
    m_selectionDock->setWidget(m_selectionText);
    addDockWidget(Qt::RightDockWidgetArea,m_selectionDock);
    splitDockWidget(m_infoDock,m_selectionDock,Qt::Vertical);
    auto* layerDock = new QDockWidget(QStringLiteral("图层显隐"), this);
    layerDock->setObjectName(QStringLiteral("layerDock"));
    auto* layers = new QListWidget(layerDock);
    layers->setObjectName(QStringLiteral("layerList"));
    for (int layer = 1; layer <= 13; ++layer) {
        auto* item = new QListWidgetItem(QStringLiteral("%1 · %2").arg(layer).arg(layerName(layer)), layers);
        item->setData(Qt::UserRole, layer);
        item->setCheckState(Qt::Checked);
        QPixmap swatch(16,16); swatch.fill(layerColor(layer)); item->setIcon(QIcon(swatch));
    }
    connect(layers, &QListWidget::itemChanged, this, [this](QListWidgetItem* item) {
        m_canvas->setLayerVisible(item->data(Qt::UserRole).toInt(), item->checkState() == Qt::Checked);
    });
    layerDock->setWidget(layers);
    addDockWidget(Qt::LeftDockWidgetArea, layerDock);
    m_viewStatus = new QLabel(this);
    m_viewStatus->setObjectName(QStringLiteral("viewStatus"));
    statusBar()->addPermanentWidget(m_viewStatus);
    createMenus();
    clearFileInfo();
    updateViewStatus();
    updateSelectionInfo();
    connect(m_canvas, &BoardCanvas::selectionChanged, this, &MainWindow::updateSelectionInfo);
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
                if (command.id.startsWith(QStringLiteral("selection."))) {
                    action->setShortcutContext(Qt::WidgetShortcut);
                    m_canvas->addAction(action);
                }
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
    if (id == QStringLiteral("file.open")) {
        const QString file = QFileDialog::getOpenFileName(this, QStringLiteral("打开旧 PCB（只读预览）"), {},
            QStringLiteral("AUTOTRAX 板图 (*.pcb *.PCB *.abk *.ABK);;所有文件 (*)"));
        if (!file.isEmpty()) requestOpenFile(file);
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
    } else if (id == QStringLiteral("selection.clear")) {
        m_canvas->clearSelection();
    } else if (id == QStringLiteral("selection.next")) {
        m_canvas->selectNextOverlap();
    } else if (id == QStringLiteral("info.selection")) {
        m_selectionDock->show(); m_selectionDock->raise();
    } else if (id == QStringLiteral("setup.layers")) {
        auto* dock = findChild<QDockWidget*>(QStringLiteral("layerDock"));
        dock->show(); dock->raise();
    } else if (id == QStringLiteral("app.about")) {
        QMessageBox::information(this, QStringLiteral("关于当前阶段"),
            QStringLiteral("C++ + Qt 6 的 AUTOTRAX 重建工程。\n\n"
                           "当前支持基本图元、元件与图层的只读预览、选择和属性查看。\n"
                           "文字与部分轮廓为近似显示；不支持编辑、保存、DRC、布线和生产输出。"));
    }
    statusBar()->showMessage(QStringLiteral("命令：%1").arg(id), 4000);
}

void MainWindow::requestOpenFile(const QString& path) {
    // 同时最多一个解析任务；窗口销毁或关闭文件后，迟到结果不再覆盖界面。
    if (m_loading) return;
    clearFileInfo();
    const quint64 generation = ++m_loadGeneration;
    m_loading = true;
    m_actions.value(QStringLiteral("file.open"))->setEnabled(false);
    m_actions.value(QStringLiteral("file.close"))->setEnabled(true);
    m_infoText->setPlainText(QStringLiteral("正在后台读取板图，请稍候……\n可用 Ctrl+W 放弃本次载入。"));
    auto* watcher = new QFutureWatcher<BoardReadResult>(this);
    connect(watcher, &QFutureWatcher<BoardReadResult>::finished, this, [this, watcher, generation, path] {
        const auto result = watcher->result();
        watcher->deleteLater();
        m_loading = false;
        m_actions.value(QStringLiteral("file.open"))->setEnabled(true);
        if (generation == m_loadGeneration) {
            const bool success = applyReadResult(result, path);
            emit boardLoadFinished(success);
        }
    });
    watcher->setFuture(QtConcurrent::run([path] { return LegacyPcbReader::readFile(path); }));
}

bool MainWindow::inspectFile(const QString& path) {
    ++m_loadGeneration;
    return applyReadResult(LegacyPcbReader::readFile(path), path);
}

bool MainWindow::applyReadResult(const BoardReadResult& result, const QString& path) {
    if (!result.succeeded()) {
        clearFileInfo();
        statusBar()->showMessage(result.error, 15000);
        m_infoDock->show();
        m_infoText->setPlainText(QStringLiteral("探测失败：%1\n\n本次没有载入或修改任何板图。").arg(result.error));
        return false;
    }
    const auto& board = *result.document;
    m_canvas->setDocument(result.document);
    QString text = QStringLiteral("只读预览，不支持编辑或保存。\n\n"
                                  "文件：%1\n格式：PCB FILE 4\n大小：%2 字节\n\nSHA-256：\n%3\n\n"
                                  "元件：%4\n走线：%5\n焊盘：%6\n过孔：%7\n圆弧：%8\n填充：%9\n文字（含可见元件标签）：%10\n\n"
                                  "单位：mil（1 mil = 0.0254 mm）\n\n记录数：\n")
                       .arg(board.filePath).arg(board.byteSize).arg(board.sha256)
                       .arg(board.components.size()).arg(board.tracks.size()).arg(board.pads.size())
                       .arg(board.vias.size()).arg(board.arcs.size()).arg(board.fills.size()).arg(board.texts.size());
    for (auto it = board.recordCounts.cbegin(); it != board.recordCounts.cend(); ++it) {
        text += QStringLiteral("%1：%2\n").arg(it.key()).arg(it.value());
    }
    text += QStringLiteral("\n显示限制：\n仅供只读检查，不可用于生产输出。\n");
    for (const auto& warning : board.warnings) text += warning + QLatin1Char('\n');
    m_infoText->setPlainText(text);
    m_infoDock->show();
    m_infoDock->raise();
    m_actions.value(QStringLiteral("file.close"))->setEnabled(true);
    setWindowTitle(QStringLiteral("%1 · 只读板图 · PT Renew").arg(QFileInfo(path).fileName()));
    statusBar()->showMessage(QStringLiteral("已载入只读板图；请留意显示近似与未支持格式说明。"), 10000);
    return true;
}

void MainWindow::clearFileInfo() {
    ++m_loadGeneration;
    m_canvas->setDocument(nullptr);
    m_infoText->setPlainText(QStringLiteral("尚未打开文件。\n\n"
        "Ctrl+O：打开 PCB 只读预览。\n"
        "画布内按 F，再按 L：同一命令的旧式入口。\n\n"
        "第三阶段支持只读预览与图元选择，不支持编辑或保存。"));
    m_actions.value(QStringLiteral("file.close"))->setEnabled(false);
    setWindowTitle(QStringLiteral("PT Renew · AUTOTRAX 重建 · 只读预览"));
}

void MainWindow::updateSelectionInfo() {
    const auto id=m_canvas->selection();
    m_actions.value(QStringLiteral("selection.clear"))->setEnabled(id.has_value());
    m_actions.value(QStringLiteral("selection.next"))->setEnabled(m_canvas->overlapCount()>1);
    if (!id || !m_canvas->document()) {
        m_selectionText->setPlainText(QStringLiteral("尚未选择图元。\n\n单击画布中的图元查看尺寸和来源。\n"
            "同位置再次单击或 Ctrl+Tab 切换本次点击的重叠候选。\n"
            "画布内 Esc 或单击空白处清除选择。\n\n"
            "钻孔内点击归属焊盘/过孔对象；文字按近似包围框选择。\n全部属性只读。"));
    } else {
        QString info=primitiveDescription(*m_canvas->document(),*id);
        info.prepend(QStringLiteral("本次命中：%1 / %2\n图层：%3\n\n")
            .arg(m_canvas->overlapPosition()>=0?m_canvas->overlapPosition()+1:1)
            .arg(qMax<qsizetype>(1,m_canvas->overlapCount()))
            .arg(layerName(primitiveLayer(*m_canvas->document(),*id))));
        m_selectionText->setPlainText(info);
        m_selectionDock->show();
    }
}

void MainWindow::updateViewStatus() {
    m_viewStatus->setText(QStringLiteral("缩放 %1%　网格%2　只读预览")
        .arg(qRound(m_canvas->zoom() * 100)).arg(m_canvas->gridVisible() ? QStringLiteral("开") : QStringLiteral("关")));
}

}
