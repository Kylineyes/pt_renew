#include "ui/MainWindow.h"
#include "experiment/AsyncExperiment.h"

#include "application/CommandCatalog.h"
#include "io/LegacyPcbReader.h"
#include "ui/BoardRenderer.h"
#include <QListWidget>
#include <QIcon>
#include <QPixmap>
#include "ui/BoardCanvas.h"
#include "ui/ComponentBrowser.h"
#include "ui/LibraryBrowser.h"
#include "ui/NetlistBrowser.h"
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
#include <QApplication>
#include <QCloseEvent>
#include <QDialog>
#include <QDialogButtonBox>
#include <QFormLayout>
#include <QLineEdit>
#include <QPushButton>
#include <QSessionManager>

namespace pt {

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent) {
    setObjectName(QStringLiteral("mainWindow"));
    setWindowTitle(QStringLiteral("PT Renew · 内存编辑 · 不支持保存"));
    resize(1440, 850);
    m_canvas = new BoardCanvas(this);
    setCentralWidget(m_canvas);
    m_infoDock = new QDockWidget(QStringLiteral("原输入与工作副本"), this);
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
    m_componentBrowser=new ComponentBrowser(this);
    addDockWidget(Qt::LeftDockWidgetArea,m_componentBrowser);
    tabifyDockWidget(layerDock,m_componentBrowser);
    layerDock->raise();
    m_netlistBrowser=new NetlistBrowser(this);
    addDockWidget(Qt::LeftDockWidgetArea,m_netlistBrowser);
    tabifyDockWidget(m_componentBrowser,m_netlistBrowser);layerDock->raise();
    connect(m_netlistBrowser,&NetlistBrowser::padsHighlighted,m_canvas,&BoardCanvas::setNetPads);
    connect(m_netlistBrowser,&NetlistBrowser::padActivated,this,[this](qsizetype index) {
        if (m_canvas->focusPad(index)) m_canvas->setFocus(Qt::ShortcutFocusReason);
    });
    connect(m_netlistBrowser,&NetlistBrowser::primitiveActivated,this,[this](PrimitiveId id) {
        if (m_canvas->focusPrimitive(id)) {
            m_selectionDock->show();m_selectionDock->raise();
            m_canvas->setFocus(Qt::ShortcutFocusReason);
            statusBar()->showMessage(QStringLiteral("已定位未覆盖图元；仅改变视图与选择，隐藏图层保持关闭。"),8000);
        }
    });
    m_measureDock=new QDockWidget(QStringLiteral("两点测量（只读）"),this);
    m_measureDock->setObjectName(QStringLiteral("measureDock"));
    m_measureText=new QPlainTextEdit(m_measureDock);
    m_measureText->setObjectName(QStringLiteral("measureText"));
    m_measureText->setReadOnly(true);
    m_measureDock->setWidget(m_measureText);
    addDockWidget(Qt::RightDockWidgetArea,m_measureDock);
    tabifyDockWidget(m_selectionDock,m_measureDock);
    m_selectionDock->raise();
    m_viewStatus = new QLabel(this);
    m_viewStatus->setObjectName(QStringLiteral("viewStatus"));
    statusBar()->addPermanentWidget(m_viewStatus);
    m_libraryBrowser=new LibraryBrowser(this);
    createMenus();
    clearFileInfo();
    updateViewStatus();
    updateSelectionInfo();
    updateMeasurementInfo();
    connect(m_componentBrowser,&ComponentBrowser::componentActivated,this,[this](qsizetype index) {
        if (m_canvas->focusComponent(index)) {
            m_canvas->setFocus(Qt::ShortcutFocusReason);
            statusBar()->showMessage(QStringLiteral("已定位元件，仅改变视图，不移动元件。"),8000);
        }
    });
    connect(m_canvas,&BoardCanvas::measurementChanged,this,&MainWindow::updateMeasurementInfo);
    connect(m_canvas, &BoardCanvas::selectionChanged, this, &MainWindow::updateSelectionInfo);
    connect(m_canvas, &BoardCanvas::legacyMenuRequested, this, &MainWindow::showLegacyMenu);
    connect(m_canvas, &BoardCanvas::viewChanged, this, &MainWindow::updateViewStatus);
    connect(qApp, &QGuiApplication::commitDataRequest, this, [this](QSessionManager& manager) {
        if (!m_editSession.dirty()) return;
        ++m_loadGeneration;
        if (!manager.allowsInteraction() || !confirmDiscard()) manager.cancel();
    });
    connect(qApp, &QApplication::focusChanged, this, [this] { updateEditingActions(); });
    m_canvas->setFocus();
}

MainWindow::~MainWindow() {
    // QWidget 析构会改变全局焦点；成员销毁前先解除依赖编辑会话和菜单的回调。
    disconnect(qApp, nullptr, this, nullptr);
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
                if (command.checkable) action->setChecked(command.id==QStringLiteral("view.grid"));
                QList<QKeySequence> keys;
                for (const auto& shortcut : command.shortcuts) {
                    keys.append(QKeySequence(shortcut, QKeySequence::PortableText));
                }
                action->setShortcuts(keys);
                action->setShortcutContext(Qt::WindowShortcut);
                if (command.id.startsWith(QStringLiteral("selection.")) || command.id==QStringLiteral("measure.toggle") || command.id==QStringLiteral("measure.snap") || command.id==QStringLiteral("jump.origin") || command.id==QStringLiteral("delete.track") || command.id==QStringLiteral("edit.undo") || command.id==QStringLiteral("edit.redo")) {
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
        const QString file = QFileDialog::getOpenFileName(this, QStringLiteral("打开旧 PCB 的内存工作副本（不支持保存）"), {},
            QStringLiteral("AUTOTRAX 板图 (*.pcb *.PCB *.abk *.ABK);;所有文件 (*)"));
        if (!file.isEmpty()) requestOpenFile(file);
    } else if (id == QStringLiteral("file.close")) {
        // 先撤销待载入结果，避免读取完成在放弃确认框内再弹出换图确认。
        ++m_loadGeneration;
        if (confirmDiscard()) clearFileInfo();
    } else if (id == QStringLiteral("move.track")) {
        moveTrackDialog();
    } else if (id == QStringLiteral("delete.track")) {
        deleteSelectedTrack();
    } else if (id == QStringLiteral("edit.undo")) {
        if (m_editSession.undo()) publishWorkingDocument();
    } else if (id == QStringLiteral("edit.redo")) {
        if (m_editSession.redo()) publishWorkingDocument();
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
    } else if (id==QStringLiteral("netlist.load")) {
        m_netlistBrowser->show();m_netlistBrowser->raise();m_netlistBrowser->chooseFile();
    } else if (id==QStringLiteral("netlist.browse")) {
        m_netlistBrowser->focusSearch();
    } else if (id==QStringLiteral("netlist.copper")) {
        m_netlistBrowser->show();m_netlistBrowser->raise();m_netlistBrowser->runCopperAnalysis();
    } else if (id==QStringLiteral("netlist.clear")) {
        m_netlistBrowser->clearExternal();
    } else if (id==QStringLiteral("highlight.reset")) {
        m_netlistBrowser->clearHighlight();
    } else if (id==QStringLiteral("library.file")) {
        m_libraryBrowser->chooseFile();
    } else if (id==QStringLiteral("library.browse")) {
        m_libraryBrowser->showBrowser();
    } else if (id == QStringLiteral("jump.component") || id==QStringLiteral("info.components")) {
        m_componentBrowser->focusSearch();
    } else if (id == QStringLiteral("jump.origin")) {
        m_canvas->centerOn({0,0}); m_canvas->setFocus(Qt::ShortcutFocusReason);
    } else if (id == QStringLiteral("measure.toggle")) {
        m_canvas->setMeasurementMode(m_actions.value(id)->isChecked());
        m_canvas->setFocus(Qt::ShortcutFocusReason);
    } else if (id == QStringLiteral("measure.snap")) {
        m_canvas->setMeasurementSnapEnabled(m_actions.value(id)->isChecked());
    } else if (id == QStringLiteral("measure.clear")) {
        m_canvas->clearMeasurement();
    } else if (id == QStringLiteral("measure.info")) {
        m_measureDock->show(); m_measureDock->raise();
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
                           "当前支持自由走线的内存移动、删除及撤销重做；原输入只读。\n"
                           "库/网表只读，铜层分析受限，不是完整 DRC。\n"
                           "文字与部分轮廓为近似显示；不支持保存、另存为、DRC、布线和生产输出。"));
    }
    statusBar()->showMessage(QStringLiteral("命令：%1").arg(id), 4000);
}

void MainWindow::openNetlist(const QString& path) {
    m_netlistBrowser->show();m_netlistBrowser->raise();m_netlistBrowser->requestFile(path);
}

void MainWindow::openLibrary(const QString& path) {
    m_libraryBrowser->showBrowser(); m_libraryBrowser->requestLibrary(path);
}

void MainWindow::requestOpenFile(const QString& path) {
    // 保留当前工作副本直至读取成功；失败、取消或迟到的结果不能丢弃修改。
    if (m_loading) return;
    const quint64 generation = ++m_loadGeneration;
    m_loading = true;
    m_actions.value(QStringLiteral("file.open"))->setEnabled(false);
    m_actions.value(QStringLiteral("file.close"))->setEnabled(true);
    statusBar()->showMessage(QStringLiteral("正在后台读取板图，当前工作副本仍保留；关闭板图可放弃本次载入。"));
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
        statusBar()->showMessage(QStringLiteral("读取失败：%1；当前工作副本和历史已保留。").arg(result.error), 15000);
        if (!m_editSession.document()) m_infoText->setPlainText(QStringLiteral("探测失败：%1\n未载入板图。").arg(result.error));
        m_actions.value(QStringLiteral("file.close"))->setEnabled(m_editSession.document()!=nullptr);
        return false;
    }
    if (!confirmDiscard()) return false;
    m_editSession.reset(result.document);
    m_canvas->setDocument(m_editSession.document());
    m_componentBrowser->setDocument(m_editSession.document());
    m_netlistBrowser->setBoard(m_editSession.document());
    m_actions.value(QStringLiteral("jump.component"))->setEnabled(!result.document->components.isEmpty());
    m_actions.value(QStringLiteral("info.components"))->setEnabled(true);
    m_actions.value(QStringLiteral("jump.origin"))->setEnabled(true);
    m_actions.value(QStringLiteral("file.close"))->setEnabled(true);
    updateFileInfo(); updateEditingActions();
    m_infoDock->show(); m_infoDock->raise();
    statusBar()->showMessage(QStringLiteral("已只读载入 %1；可编辑自由走线工作副本，不支持保存。").arg(QFileInfo(path).fileName()), 10000);
    return true;
}

void MainWindow::clearFileInfo() {
    ++m_loadGeneration;
    m_editSession.reset();
    m_canvas->setDocument(nullptr);
    m_componentBrowser->setDocument(nullptr);
    m_netlistBrowser->setBoard(nullptr);
    for (const auto& id : {"jump.component","info.components","jump.origin"}) m_actions.value(QString::fromLatin1(id))->setEnabled(false);
    m_infoText->setPlainText(QStringLiteral("尚未打开文件。\n\n"
        "Ctrl+O：只读载入原件并建立工作副本。\n"
        "画布内按 F，再按 L：同一命令的旧式入口。\n\n"
        "第十一阶段支持自由走线内存移动、删除及撤销重做；保存和另存为尚未实现。"));
    m_actions.value(QStringLiteral("file.close"))->setEnabled(false);
    setWindowTitle(QStringLiteral("PT Renew · 内存编辑 · 不支持保存"));
    updateEditingActions(); updateViewStatus();
}

bool MainWindow::confirmDiscard() {
    if (!m_editSession.dirty()) return true;
    QMessageBox box(QMessageBox::Warning, QStringLiteral("放弃工作副本更改？"),
        QStringLiteral("工作副本已修改，更改仅在内存中。保存和另存为尚未实现。\n放弃后无法恢复这些更改。"), QMessageBox::NoButton, this);
    box.setObjectName(QStringLiteral("discardChangesDialog"));
    auto* discard = box.addButton(QStringLiteral("放弃更改"), QMessageBox::DestructiveRole);
    auto* cancel = box.addButton(QStringLiteral("取消"), QMessageBox::RejectRole);
    box.setDefaultButton(cancel); box.setEscapeButton(cancel);
    box.exec();
    return box.clickedButton() == discard;
}

void MainWindow::closeEvent(QCloseEvent* event) {
    ++m_loadGeneration;
    if (confirmDiscard()) event->accept();
    else event->ignore();
}

bool MainWindow::selectedTrackEditable() const {
    const auto id = m_canvas->selection();
    return !m_libraryBrowser->isActiveWindow() && id && m_canvas->document()==m_editSession.document().get()
        && m_editSession.editable(*id, m_editSession.revision())
        && m_canvas->layerVisible(primitiveLayer(*m_canvas->document(), *id));
}

void MainWindow::updateEditingActions() {
    const bool editable = selectedTrackEditable();
    m_actions.value(QStringLiteral("move.track"))->setEnabled(editable);
    m_actions.value(QStringLiteral("delete.track"))->setEnabled(editable);
    const bool boardContext = !m_libraryBrowser->isActiveWindow();
    m_actions.value(QStringLiteral("edit.undo"))->setEnabled(boardContext && m_editSession.canUndo());
    m_actions.value(QStringLiteral("edit.redo"))->setEnabled(boardContext && m_editSession.canRedo());
}

bool MainWindow::moveSelectedTrack(QPointF delta, QString* error) {
    if (!selectedTrackEditable()) return false;
    if (!m_editSession.moveTrack(*m_canvas->selection(), m_editSession.revision(), delta, error)) return false;
    publishWorkingDocument(); return true;
}

bool MainWindow::deleteSelectedTrack() {
    if (!selectedTrackEditable()) return false;
    if (!m_editSession.deleteTrack(*m_canvas->selection(), m_editSession.revision())) return false;
    publishWorkingDocument(); return true;
}

void MainWindow::publishWorkingDocument() {
    m_canvas->setDocument(m_editSession.document(), true);
    m_componentBrowser->setDocument(m_editSession.document());
    m_netlistBrowser->setBoard(m_editSession.document(), true);
    updateFileInfo(); updateEditingActions(); updateViewStatus();
    experiment::documentPublished({
        {QStringLiteral("revision"), QString::number(m_editSession.document()->workingRevision)},
        {QStringLiteral("tracks"), QString::number(m_editSession.document()->tracks.size())},
        {QStringLiteral("dirty"), m_editSession.dirty()},
        {QStringLiteral("net_sha256"), m_netlistBrowser->netlist() ? m_netlistBrowser->netlist()->sha256 : QString()}});
    statusBar()->showMessage(QStringLiteral("工作副本已更新；选择、测量与铜层结论已清除，外部网表已重新映射。不支持保存。"), 10000);
}

void MainWindow::moveTrackDialog() {
    if (!selectedTrackEditable()) return;
    const auto revision = m_editSession.revision();
    QDialog dialog(this); dialog.setObjectName(QStringLiteral("moveTrackDialog"));
    dialog.setWindowTitle(QStringLiteral("移动所选自由走线（仅内存）"));
    auto* layout = new QFormLayout(&dialog);
    auto* dx = new QLineEdit(QStringLiteral("0"), &dialog); dx->setObjectName(QStringLiteral("moveDeltaX"));
    auto* dy = new QLineEdit(QStringLiteral("0"), &dialog); dy->setObjectName(QStringLiteral("moveDeltaY"));
    layout->addRow(QStringLiteral("ΔX（整数 mil，向右为正）："), dx);
    layout->addRow(QStringLiteral("ΔY（整数 mil，向上为正）："), dy);
    auto* error = new QLabel(QStringLiteral("位移范围 ±2000000；端点范围 ±1000000 mil。不支持保存。"), &dialog);
    error->setWordWrap(true); error->setObjectName(QStringLiteral("moveError")); layout->addRow(error);
    auto* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dialog);
    buttons->button(QDialogButtonBox::Ok)->setText(QStringLiteral("移动"));
    buttons->button(QDialogButtonBox::Cancel)->setText(QStringLiteral("取消")); layout->addRow(buttons);
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    connect(buttons, &QDialogButtonBox::accepted, &dialog, [&] {
        bool xOk = false, yOk = false;
        const auto x = dx->text().toLongLong(&xOk), y = dy->text().toLongLong(&yOk);
        if (!xOk || !yOk || x < -2000000 || x > 2000000 || y < -2000000 || y > 2000000) {
            error->setText(QStringLiteral("请输入 ±2000000 范围内的整数 mil，不接受小数或非有限值。")); return;
        }
        if (revision != m_editSession.revision() || !selectedTrackEditable()) { dialog.reject(); return; }
        if (x == 0 && y == 0) { dialog.accept(); return; }
        QString message;
        if (moveSelectedTrack(QPointF(qreal(x), qreal(y)), &message)) dialog.accept();
        else error->setText(message);
    });
    dialog.exec();
    m_canvas->setFocus(Qt::ShortcutFocusReason);
}

void MainWindow::updateFileInfo() {
    if (!m_editSession.original()) return;
    const auto& original = *m_editSession.original();
    const auto& current = *m_editSession.document();
    QString text = QStringLiteral("当前工作副本：%1\n工作修订：%2\n当前图元：%3；走线：%4\n"
        "仅所选自由走线可移动/删除；保存和另存为尚未实现。\n\n"
        "原输入（始终只读，以下不是工作副本的文件摘要）：\n文件：%5\n格式：PCB FILE 4\n原输入大小：%6 字节\n"
        "原输入 SHA-256：\n%7\n\n原输入记录数：\n")
        .arg(m_editSession.dirty()?QStringLiteral("已修改（仅内存）"):QStringLiteral("未修改"))
        .arg(m_editSession.revision()).arg(current.primitiveCount()).arg(current.tracks.size())
        .arg(original.filePath).arg(original.byteSize).arg(original.sha256);
    for (auto it = original.recordCounts.cbegin(); it != original.recordCounts.cend(); ++it)
        text += QStringLiteral("%1：%2\n").arg(it.key()).arg(it.value());
    text += QStringLiteral("\n单位：mil（1 mil = 0.0254 mm）\n文字与部分轮廓近似，不可用于生产输出。\n");
    for (const auto& warning : original.warnings) text += warning + QLatin1Char('\n');
    m_infoText->setPlainText(text);
    setWindowTitle(QStringLiteral("%1%2 · 工作副本 · 不支持保存 · PT Renew")
        .arg(QFileInfo(original.filePath).fileName(), m_editSession.dirty()?QStringLiteral(" * 已修改"):QString()));
}

void MainWindow::updateSelectionInfo() {
    updateEditingActions();
    const auto id=m_canvas->selection();
    m_actions.value(QStringLiteral("selection.clear"))->setEnabled(id.has_value() || m_canvas->focusedComponent().has_value());
    m_actions.value(QStringLiteral("selection.next"))->setEnabled(m_canvas->overlapCount()>1);
    if (m_canvas->focusedComponent() && m_canvas->document()) {
        m_selectionText->setPlainText(componentDescription(*m_canvas->document(),*m_canvas->focusedComponent()));
        m_selectionDock->show(); m_selectionDock->raise();
        return;
    }
    if (!id || !m_canvas->document()) {
        m_selectionText->setPlainText(QStringLiteral("尚未选择图元。\n\n单击画布中的图元查看尺寸和来源。\n"
            "同位置再次单击或 Ctrl+Tab 切换本次点击的重叠候选。\n"
            "画布内 Esc 或单击空白处清除选择。\n\n"
            "钻孔内点击归属焊盘/过孔对象；文字按近似包围框选择。\n属性面板只读；可用菜单移动或删除所选自由走线，不支持保存。"));
    } else {
        QString info=primitiveDescription(*m_canvas->document(),*id);
        info.prepend(QStringLiteral("本次命中：%1 / %2\n图层：%3\n\n")
            .arg(m_canvas->overlapPosition()>=0?m_canvas->overlapPosition()+1:1)
            .arg(qMax<qsizetype>(1,m_canvas->overlapCount()))
            .arg(layerName(primitiveLayer(*m_canvas->document(),*id))));
        m_selectionText->setPlainText(info);
        m_selectionDock->show(); m_selectionDock->raise();
    }
}

void MainWindow::updateMeasurementInfo() {
    const auto result=m_canvas->measurement();
    const auto start=m_canvas->measurementStart();
    const bool active=m_canvas->measurementMode();
    m_actions.value(QStringLiteral("measure.toggle"))->setEnabled(m_canvas->document()!=nullptr);
    m_actions.value(QStringLiteral("measure.toggle"))->setChecked(active);
    m_actions.value(QStringLiteral("measure.snap"))->setEnabled(m_canvas->document()!=nullptr);
    m_actions.value(QStringLiteral("measure.snap"))->setChecked(m_canvas->measurementSnapEnabled());
    m_actions.value(QStringLiteral("measure.clear"))->setEnabled(result.has_value() || start.has_value());
    QString text=active?QStringLiteral("测量模式：依次单击两点，画布内 Esc 退出。\n"):QStringLiteral("测量模式已关闭。\n");
    auto unit=[](qreal value) { return QStringLiteral("%1 mil（%2 mm）").arg(QString::number(value,'f',2),QString::number(value*0.0254,'f',4)); };
    if (start) text+=QStringLiteral("\n第一点：X=%1，Y=%2 mil\n等待第二点。\n").arg(start->x(),0,'f',2).arg(start->y(),0,'f',2);
    if (result) {
        text+=QStringLiteral("\n起点：X=%1，Y=%2 mil\n终点：X=%3，Y=%4 mil\n\nΔX：%5\nΔY：%6\n距离：%7\n方向角：%8°\n")
            .arg(result->start.x(),0,'f',2).arg(result->start.y(),0,'f',2)
            .arg(result->end.x(),0,'f',2).arg(result->end.y(),0,'f',2)
            .arg(unit(result->deltaX()),unit(result->deltaY()),unit(result->distance()))
            .arg(result->angleDegrees(),0,'f',2);
        auto origin = [this](const std::optional<PrimitiveId>& anchor) {
            if (!anchor || !m_canvas->document()) return QStringLiteral("屏幕自由取点");
            const auto source = primitiveSource(*m_canvas->document(), *anchor);
            return QStringLiteral("模型几何捕捉（源文件行 %1）").arg(source.line);
        };
        text += QStringLiteral("起点来源：%1\n终点来源：%2\n").arg(origin(result->startAnchor), origin(result->endAnchor));
    } else if (!start) text+=active?QStringLiteral("\n尚无测量结果，请在画布依次单击两点。\n"):QStringLiteral("\n尚无测量结果。请在画布内按 Ctrl+M，或从信息菜单进入两点测量。\n");
    text += m_canvas->measurementSnapEnabled()
        ? QStringLiteral("\n端点捕捉已开启：靠近可见图元的端点或中心时显示黄色方框。\n超出捕捉范围时仍为自由取点，不捕捉网格或文字。\n")
        : QStringLiteral("\n当前为屏幕自由取点。可在信息菜单开启端点捕捉，或在画布内按 Ctrl+Shift+M。\n");
    text+=QStringLiteral("结果按当前模型坐标计算；自由取点受屏幕精度影响。\n不是 DRC 或制造尺寸验收；不写入板图。\n"
                        "完成一组后可继续取两点，清除命令删除结果；退出模式保留已完成结果。");
    m_measureText->setPlainText(text);
    if (active) { m_measureDock->show(); m_measureDock->raise(); }
    updateViewStatus();
}

void MainWindow::updateViewStatus() {
    m_viewStatus->setText(QStringLiteral("缩放 %1%　网格%2　%3　工作副本%4 · 不支持保存")
        .arg(qRound(m_canvas->zoom() * 100)).arg(m_canvas->gridVisible() ? QStringLiteral("开") : QStringLiteral("关"))
        .arg(m_canvas->measurementMode()?QStringLiteral("测量取点中"):QStringLiteral("选择模式"))
        .arg(m_editSession.dirty()?QStringLiteral("已修改"):QStringLiteral("未修改")));
}

}
