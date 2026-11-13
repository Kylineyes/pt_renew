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

// 原软件新增 FT 编码与保存闭环核定前，产品入口统一关闭。
bool trackPlacementUserEntryAvailable();
const QList<MenuSpec>& commandCatalog();

}
