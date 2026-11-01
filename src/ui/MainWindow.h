#pragma once

#include "application/BoardEditSession.h"
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
    ~MainWindow() override;
    bool inspectFile(const QString& path);
    void requestOpenFile(const QString& path);
    void openLibrary(const QString& path);
    void openNetlist(const QString& path);
    const BoardEditSession& editSession() const { return m_editSession; }
    bool moveSelectedTrack(QPointF delta, QString* error = nullptr);
    bool deleteSelectedTrack();
    bool saveAsFile(const QString& path, QString* error = nullptr);

protected:
    void closeEvent(QCloseEvent* event) override;

signals:
    void commandInvoked(const QString& id);
    void boardLoadFinished(bool succeeded);

private:
    bool applyReadResult(const BoardReadResult& result, const QString& path);
    void createMenus();
    bool confirmDiscard();
    bool selectedTrackEditable() const;
    void moveTrackDialog();
    void saveAsDialog();
    void publishWorkingDocument();
    void updateEditingActions();
    void updateFileInfo();
    void executeCommand(const QString& id);
    void showLegacyMenu(const QString& key);
    void clearFileInfo();
    void updateViewStatus();
    void updateSelectionInfo();
    void updateMeasurementInfo();
    BoardEditSession m_editSession;
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
    QString m_savedPath, m_savedSha256;
    qint64 m_savedBytes = 0;
};

}
