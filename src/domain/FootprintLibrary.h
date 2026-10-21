#pragma once

#include "domain/BoardDocument.h"
#include <QByteArray>

namespace pt {

struct LibraryEntry {
    QString name;
    int slot=0;
    quint16 primitiveCount=0;
    quint32 firstRecord=0, limitRecord=0, endRecord=0;
    std::shared_ptr<const BoardDocument> preview;
    QString error;
};

struct FootprintLibrary {
    QString filePath, sha256;
    QByteArray sourceBytes;
    QList<LibraryEntry> entries;
    int unallocatedSlots=0, retainedNameSlots=0;
    QStringList warnings;
};

struct LibraryReadResult {
    std::shared_ptr<const FootprintLibrary> library;
    QString error;
    bool succeeded() const { return library!=nullptr && error.isEmpty(); }
};

}
