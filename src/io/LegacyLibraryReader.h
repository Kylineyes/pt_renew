#pragma once
#include "domain/FootprintLibrary.h"

namespace pt {

// 仅支持已观测的 PCB 4 LIBRARY 布局，不执行目标代码或写回库。
class LegacyLibraryReader {
public:
    static LibraryReadResult readFile(const QString& path);
    static LibraryReadResult parse(const QByteArray& bytes,const QString& source={});
};

}
