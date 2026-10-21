#pragma once
#include <QByteArray>

namespace pt {
// 仅允许一个尾部 DOS EOF，其后只能有文本空白；绝不按中途 EOF 截断数据。
inline qsizetype dosTextEnd(const QByteArray& bytes) {
    const auto eof=bytes.indexOf('\x1a');
    if (eof<0) return bytes.size();
    for (qsizetype i=eof+1;i<bytes.size();++i) {
        const char ch=bytes[i];
        if (ch!=' ' && ch!='\t' && ch!='\r' && ch!='\n') return -1;
    }
    return eof;
}
}
