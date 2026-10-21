#pragma once
#include "application/NetlistMapping.h"
#include <QDockWidget>
class QListWidget;
class QComboBox;
class QLineEdit;
class QLabel;
class QPushButton;
class QPlainTextEdit;
namespace pt {
class NetlistBrowser final : public QDockWidget {
    Q_OBJECT
public:
    explicit NetlistBrowser(QWidget* parent=nullptr);
    void setBoard(std::shared_ptr<const BoardDocument> board);
    void chooseFile();
    void requestFile(const QString& path);
    bool loadFile(const QString& path);
    void clearExternal();
    void focusSearch();
    void clearHighlight();
    const NetlistMapping& mapping() const { return m_mapping; }
    const Netlist* netlist() const { return m_active.get(); }
signals:
    void padsHighlighted(const QList<qsizetype>& pads);
    void padActivated(qsizetype index);
    void netlistLoaded(bool success);
private:
    void rebuild();
    void filter();
    void showCurrent();
    bool apply(const NetlistReadResult& result);
    std::shared_ptr<const BoardDocument> m_board;
    std::shared_ptr<const Netlist> m_external,m_active;
    NetlistMapping m_mapping;
    QLineEdit* m_search=nullptr;
    QComboBox* m_source=nullptr;
    bool m_useExternal=true;
    QListWidget* m_nets=nullptr;
    QListWidget* m_nodes=nullptr;
    QPlainTextEdit* m_details=nullptr;
    QLabel* m_status=nullptr;
    QPushButton* m_open=nullptr;
    QPushButton* m_clear=nullptr;
    bool m_loading=false;
    quint64 m_generation=0;
    QString m_error;
};
}
