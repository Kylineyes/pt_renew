#pragma once

#include <QList>
#include <QString>
#include <QStringList>

namespace pt {

struct CommandSpec {
    QString id;
    QString text;
    QStringList shortcuts;
    bool implemented = false;
    bool checkable = false;
};

struct MenuSpec {
    QString key;
    QString title;
    QList<CommandSpec> commands;
};

const QList<MenuSpec>& commandCatalog();

}
