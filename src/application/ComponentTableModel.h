#pragma once

#include "domain/BoardDocument.h"
#include <QAbstractTableModel>

namespace pt {

// 元件表按需提供数据，不为每行建立控件；行号对应不可变文档内的元件索引。
class ComponentTableModel final : public QAbstractTableModel {
public:
    explicit ComponentTableModel(QObject* parent=nullptr) : QAbstractTableModel(parent) {}
    void setDocument(std::shared_ptr<const BoardDocument> document);
    int rowCount(const QModelIndex& parent={}) const override;
    int columnCount(const QModelIndex& parent={}) const override;
    QVariant data(const QModelIndex& index, int role=Qt::DisplayRole) const override;
    QVariant headerData(int section, Qt::Orientation orientation, int role=Qt::DisplayRole) const override;
private:
    std::shared_ptr<const BoardDocument> m_document;
};

}
