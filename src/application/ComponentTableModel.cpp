#include "application/ComponentTableModel.h"

namespace pt {

void ComponentTableModel::setDocument(std::shared_ptr<const BoardDocument> document) {
    beginResetModel();
    m_document=std::move(document);
    endResetModel();
}

int ComponentTableModel::rowCount(const QModelIndex& parent) const {
    return !parent.isValid() && m_document ? int(m_document->components.size()) : 0;
}

int ComponentTableModel::columnCount(const QModelIndex& parent) const { return parent.isValid()?0:3; }

QVariant ComponentTableModel::data(const QModelIndex& index, int role) const {
    if (!m_document || !index.isValid() || index.row()<0 || index.row()>=rowCount() || index.column()<0 || index.column()>=3) return {};
    if (role==Qt::UserRole) return index.row();
    if (role!=Qt::DisplayRole && role!=Qt::ToolTipRole) return {};
    const auto& c=m_document->components[index.row()];
    switch (index.column()) {
    case 0: return c.designator;
    case 1: return c.footprint;
    case 2: return c.comment;
    }
    return {};
}

QVariant ComponentTableModel::headerData(int section, Qt::Orientation orientation, int role) const {
    if (role!=Qt::DisplayRole) return {};
    if (orientation==Qt::Vertical) return section>=0 && section<rowCount()?QVariant(section+1):QVariant();
    switch (section) {
    case 0: return QStringLiteral("标号");
    case 1: return QStringLiteral("封装");
    case 2: return QStringLiteral("注释");
    }
    return {};
}

}
