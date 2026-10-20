#pragma once

#include <QHash>
#include <QMainWindow>

class QAction;
class QDockWidget;
class QLabel;
class QMenu;
class QPlainTextEdit;

namespace pt {

class BoardCanvas;

class MainWindow final : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(QWidget* parent = nullptr);
    bool inspectFile(const QString& path);

signals:
    void commandInvoked(const QString& id);

private:
    void createMenus();
    void executeCommand(const QString& id);
    void showLegacyMenu(const QString& key);
    void clearFileInfo();
    void updateViewStatus();
    BoardCanvas* m_canvas = nullptr;
    QDockWidget* m_infoDock = nullptr;
    QPlainTextEdit* m_infoText = nullptr;
    QLabel* m_viewStatus = nullptr;
    QHash<QString, QAction*> m_actions;
    QHash<QString, QMenu*> m_menus;
};

}
