#pragma once

#include "domain/BoardDocument.h"
#include <QDockWidget>

class QLineEdit;
class QTableView;
class QLabel;
class QPushButton;
class QSortFilterProxyModel;

namespace pt {
class ComponentTableModel;

class ComponentBrowser final : public QDockWidget {
    Q_OBJECT
public:
    explicit ComponentBrowser(QWidget* parent=nullptr);
    void setDocument(std::shared_ptr<const BoardDocument> document);
    void focusSearch();
signals:
    void componentActivated(qsizetype index);
private:
    void filterChanged();
    void activateCurrent();
    QLineEdit* m_search=nullptr;
    QTableView* m_table=nullptr;
    QLabel* m_count=nullptr;
    QPushButton* m_go=nullptr;
    ComponentTableModel* m_model=nullptr;
    QSortFilterProxyModel* m_proxy=nullptr;
};

}
