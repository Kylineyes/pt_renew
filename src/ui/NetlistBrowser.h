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
    void runCopperAnalysis();
    bool copperAnalysisRunning() const { return m_analyzing; }
    const NetlistMapping& mapping() const { return m_mapping; }
    const Netlist* netlist() const { return m_active.get(); }
signals:
    void padsHighlighted(const QList<qsizetype>& pads);
    void padActivated(qsizetype index);
    void primitiveActivated(pt::PrimitiveId id);
    void netlistLoaded(bool success);
    void copperAnalysisFinished();
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
    QWidget* m_coverageBox=nullptr;
    QLabel* m_coverageStatus=nullptr;
    QListWidget* m_coverageIssues=nullptr;
    QPlainTextEdit* m_details=nullptr;
    QLabel* m_status=nullptr;
    QPushButton* m_open=nullptr;
    QPushButton* m_clear=nullptr;
    QPushButton* m_copper=nullptr;
    QString m_copperReport;
    quint64 m_copperGeneration=0;
    bool m_analyzing=false;
    bool m_loading=false;
    quint64 m_generation=0;
    QString m_error;
};
}
