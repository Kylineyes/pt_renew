#include "ui/ComponentBrowser.h"
#include "application/ComponentTableModel.h"
#include <QHeaderView>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QSortFilterProxyModel>
#include <QTableView>
#include <QVBoxLayout>

namespace pt {
ComponentBrowser::ComponentBrowser(QWidget* parent) : QDockWidget(QStringLiteral("元件检索与定位（只读）"),parent) {
    setObjectName(QStringLiteral("componentDock"));
    auto* content=new QWidget(this);
    auto* layout=new QVBoxLayout(content);
    m_search=new QLineEdit(content);
    m_search->setObjectName(QStringLiteral("componentSearch"));
    m_search->setPlaceholderText(QStringLiteral("输入标号、封装或注释；Enter 定位"));
    m_search->setClearButtonEnabled(true);
    m_model=new ComponentTableModel(this);
    m_proxy=new QSortFilterProxyModel(this);
    m_proxy->setSourceModel(m_model);
    m_proxy->setFilterCaseSensitivity(Qt::CaseInsensitive);
    m_proxy->setSortCaseSensitivity(Qt::CaseInsensitive);
    m_proxy->setFilterKeyColumn(-1);
    m_table=new QTableView(content);
    m_table->setObjectName(QStringLiteral("componentTable"));
    m_table->setModel(m_proxy);
    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setSelectionMode(QAbstractItemView::SingleSelection);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->setSortingEnabled(true);
    m_table->sortByColumn(0,Qt::AscendingOrder);
    m_table->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    m_table->verticalHeader()->hide();
    m_count=new QLabel(content);
    m_count->setObjectName(QStringLiteral("componentCount"));
    m_go=new QPushButton(QStringLiteral("定位当前元件"),content);
    m_go->setObjectName(QStringLiteral("componentGo"));
    layout->addWidget(m_search); layout->addWidget(m_count); layout->addWidget(m_table); layout->addWidget(m_go);
    setWidget(content);
    connect(m_search,&QLineEdit::textChanged,this,[this] { m_proxy->setFilterFixedString(m_search->text()); filterChanged(); });
    connect(m_search,&QLineEdit::returnPressed,this,&ComponentBrowser::activateCurrent);
    connect(m_go,&QPushButton::clicked,this,&ComponentBrowser::activateCurrent);
    connect(m_table,&QTableView::activated,this,[this](const QModelIndex&) { activateCurrent(); });
    filterChanged();
}

void ComponentBrowser::setDocument(std::shared_ptr<const BoardDocument> document) {
    m_model->setDocument(std::move(document));
    m_search->clear();
    filterChanged();
}

void ComponentBrowser::filterChanged() {
    const int count=m_proxy->rowCount();
    m_count->setText(QStringLiteral("匹配 %1 / %2 个元件").arg(count).arg(m_model->rowCount()));
    m_go->setEnabled(count>0);
    if (count>0) m_table->setCurrentIndex(m_proxy->index(0,0));
    else { m_table->clearSelection(); m_table->setCurrentIndex({}); }
}

void ComponentBrowser::activateCurrent() {
    const auto current=m_table->currentIndex();
    if (!current.isValid()) return;
    const auto source=m_proxy->mapToSource(current);
    if (source.isValid()) emit componentActivated(source.row());
}

void ComponentBrowser::focusSearch() {
    show(); raise(); m_search->setFocus(Qt::ShortcutFocusReason); m_search->selectAll();
}
}
