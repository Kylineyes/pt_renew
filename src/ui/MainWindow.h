#pragma once

#include "domain/BoardDocument.h"
#include <QHash>
#include <QMainWindow>

class QAction;
class QDockWidget;
class QLabel;
class QMenu;
class QPlainTextEdit;

namespace pt {

class BoardCanvas;
class ComponentBrowser;
class LibraryBrowser;
class NetlistBrowser;

class MainWindow final : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(QWidget* parent = nullptr);
    bool inspectFile(const QString& path);
    void requestOpenFile(const QString& path);
    void openLibrary(const QString& path);
    void openNetlist(const QString& path);

signals:
    void commandInvoked(const QString& id);
    void boardLoadFinished(bool succeeded);

private:
    bool applyReadResult(const BoardReadResult& result, const QString& path);
    void createMenus();
    void executeCommand(const QString& id);
    void showLegacyMenu(const QString& key);
    void clearFileInfo();
    void updateViewStatus();
    void updateSelectionInfo();
    void updateMeasurementInfo();
    BoardCanvas* m_canvas = nullptr;
    QDockWidget* m_infoDock = nullptr;
    QPlainTextEdit* m_infoText = nullptr;
    QDockWidget* m_selectionDock = nullptr;
    QPlainTextEdit* m_selectionText = nullptr;
    ComponentBrowser* m_componentBrowser=nullptr;
    LibraryBrowser* m_libraryBrowser=nullptr;
    NetlistBrowser* m_netlistBrowser=nullptr;
    QDockWidget* m_measureDock=nullptr;
    QPlainTextEdit* m_measureText=nullptr;
    QLabel* m_viewStatus = nullptr;
    QHash<QString, QAction*> m_actions;
    QHash<QString, QMenu*> m_menus;
    quint64 m_loadGeneration = 0;
    bool m_loading = false;
};

}
