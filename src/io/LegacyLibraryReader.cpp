#include "io/LegacyLibraryReader.h"
#include <QCryptographicHash>
#include <QFile>
#include <QFileInfo>
#include <QtEndian>
#include <algorithm>

namespace pt {
namespace {
constexpr qsizetype recordSize=16, directorySlots=200, firstDataRecord=401;
constexpr qsizetype maximumBytes=8*1024*1024, maximumTotalPrimitives=200000, maximumEntryPrimitives=20000;
struct LibraryError { QString message; };
[[noreturn]] void fail(const QString& message) { throw LibraryError{message}; }
quint8 byte(const QByteArray& bytes,qsizetype offset) { return static_cast<quint8>(bytes[offset]); }
quint16 word(const QByteArray& bytes,qsizetype offset) {
    return qFromLittleEndian<quint16>(reinterpret_cast<const uchar*>(bytes.constData()+offset));
}
qint16 signedWord(const QByteArray& bytes,qsizetype offset) {
    return qFromLittleEndian<qint16>(reinterpret_cast<const uchar*>(bytes.constData()+offset));
}
bool zero(const QByteArray& bytes,qsizetype offset,qsizetype count) {
    for (qsizetype i=0;i<count;++i) if (byte(bytes,offset+i)!=0) return false;
    return true;
}
QString shortString(const QByteArray& record,qsizetype maximum,bool& nonAscii) {
    const int count=byte(record,2);
    if (count>maximum) fail(QStringLiteral("Pascal 字符串长度超出记录容量。"));
    QString value;
    for (int i=0;i<count;++i) {
        const auto ch=byte(record,3+i);
        if (ch<32 || ch==127) fail(QStringLiteral("名称或文字包含不支持的控制字符。"));
        if (ch>=128) { value.append(QChar::ReplacementCharacter); nonAscii=true; }
        else value.append(QChar(ch));
    }
    return value;
}

std::shared_ptr<const BoardDocument> decode(const FootprintLibrary& library,LibraryEntry& entry) {
    if (entry.primitiveCount>maximumEntryPrimitives) fail(QStringLiteral("单个封装超过 20000 图元的限制。"));
    const auto& bytes=library.sourceBytes;
    auto board=std::make_shared<BoardDocument>();
    board->filePath=library.filePath; board->sha256=library.sha256; board->byteSize=bytes.size();
    board->sourceContext=QStringLiteral("LIB 封装 %1（独立预览，未放置到板图）").arg(entry.name);
    quint32 current=entry.firstRecord;
    bool nonAscii=false,hasVia=false,approximatePad=false;
    auto next=[&]() {
        if (current>=entry.limitRecord) fail(QStringLiteral("封装越过文件边界或下一个目录条目的起始记录。"));
        const auto record=bytes.mid(qsizetype(current)*recordSize,recordSize);
        if (record.size()!=recordSize) fail(QStringLiteral("图元记录被截断。"));
        ++current; return record;
    };
    auto layer=[](int number) { if (number<1 || number>13) fail(QStringLiteral("图层必须为 1 至 13。")); };
    auto positive=[](int number) { if (number<=0) fail(QStringLiteral("图元尺寸必须为正数。")); };
    auto requireZero=[](const QByteArray& record,int start) {
        if (!zero(record,start,recordSize-start)) fail(QStringLiteral("记录存在未知的非零保留字段，禁止不完整预览。"));
    };
    auto followingString=[&](int type) {
        const auto record=next();
        if (byte(record,0)!=0 || byte(record,1)!=type) fail(QStringLiteral("缺少正确类型的字符串续记录。"));
        return shortString(record,13,nonAscii);
    };
    for (int i=0;i<entry.primitiveCount;++i) {
        const PrimitiveSource source{0,-1,qint64(current)*recordSize};
        const auto record=next();
        const int number=byte(record,0),type=byte(record,1);
        if (type!=8) layer(number);
        const QPointF position(signedWord(record,2),signedWord(record,4));
        switch (type) {
        case 1: {
            const int radius=word(record,6),mask=byte(record,8),width=byte(record,9);
            positive(radius); positive(width); requireZero(record,10);
            if (mask<1 || mask>15) fail(QStringLiteral("圆弧象限掩码必须为 1 至 15。"));
            board->arcs.append({position,radius,mask,width,number,source}); break;
        }
        case 2: {
            const QPointF end(signedWord(record,6),signedWord(record,8));
            requireZero(record,10);
            if (position.x()==end.x() || position.y()==end.y()) fail(QStringLiteral("填充矩形宽高不能为零。"));
            board->fills.append({QRectF(position,end).normalized(),number,source}); break;
        }
        case 3: {
            const int width=word(record,6),height=word(record,8),drill=word(record,10);
            const int shape=byte(record,12),plane=byte(record,13);
            positive(width); positive(height); requireZero(record,14);
            if (shape<1 || shape>4) fail(QStringLiteral("尚不支持此焊盘形状。"));
            if (drill>qMin(width,height)) fail(QStringLiteral("焊盘孔径大于外形尺寸。"));
            board->pads.append({position,width,height,shape,drill,plane,number,followingString(4),source});
            approximatePad=approximatePad || shape>=3; break;
        }
        case 5: {
            const QPointF end(signedWord(record,6),signedWord(record,8));
            const int width=word(record,10); positive(width); requireZero(record,12);
            board->tracks.append({position,end,width,number,{},source}); break;
        }
        case 6: {
            const int height=word(record,6),width=byte(record,8),direction=byte(record,9);
            positive(height); positive(width); requireZero(record,10);
            if (!((direction>=0 && direction<=3) || (direction>=16 && direction<=19))) fail(QStringLiteral("未知文字方向编码。"));
            board->texts.append({position,height,direction&3,width,number,(direction&16)!=0,followingString(7),source}); break;
        }
        case 8: {
            const int diameter=byte(record,6),drill=byte(record,7);
            positive(diameter); requireZero(record,9);
            if (number!=0 || byte(record,8)!=1) fail(QStringLiteral("不支持的类型 8 过孔标志变体。"));
            if (drill>diameter) fail(QStringLiteral("过孔孔径大于外径。"));
            board->vias.append({position,diameter,drill,source}); hasVia=true; break;
        }
        default: fail(QStringLiteral("尚未支持二进制图元类型 %1，停止该封装预览。").arg(type));
        }
        ++board->recordCounts[QStringLiteral("LIB 类型 %1").arg(type)];
    }
    entry.endRecord=current;
    board->warnings.append(QStringLiteral("仅为当前已观测 LIB 布局的只读预览，不是已放置元件，不可用于生产输出。"));
    if (!board->texts.isEmpty()) board->warnings.append(QStringLiteral("文字使用系统等宽字体近似显示，旧 DOS 笔画字体尚未恢复。"));
    if (approximatePad) board->warnings.append(QStringLiteral("八角/圆角焊盘轮廓为预览近似值。"));
    if (hasVia) board->warnings.append(QStringLiteral("类型 8 按过孔显示；原始附加标志保留在库快照中，尚未作电气解释。"));
    if (nonAscii) board->warnings.append(QStringLiteral("旧代码页未确认，非 ASCII 字节显示为替代字符。"));
    return board;
}
}

LibraryReadResult LegacyLibraryReader::parse(const QByteArray& bytes,const QString& source) {
    try {
        if (bytes.size()<firstDataRecord*recordSize || bytes.size()>maximumBytes || bytes.size()%recordSize!=0)
            fail(QStringLiteral("LIB 长度必须为 16 的倍数，至少 6416 字节且不超过 8 MiB。"));
        const QByteArray header("\0\0\x0d" "PCB 4 LIBRARY",16);
        if (bytes.left(recordSize)!=header) fail(QStringLiteral("仅支持已观测的 PCB 4 LIBRARY 二进制头。"));
        auto library=std::make_shared<FootprintLibrary>();
        library->sourceBytes=bytes; library->filePath=source;
        library->sha256=QString::fromLatin1(QCryptographicHash::hash(bytes,QCryptographicHash::Sha256).toHex());
        qsizetype total=0; bool nonAscii=false;
        for (int slot=0;slot<directorySlots;++slot) {
            const auto row=bytes.mid(recordSize+slot*32,32);
            const auto count=word(row,18),start=word(row,20);
            if (start==65535) {
                ++library->unallocatedSlots;
                if (count!=65535 && byte(row,2)>0) ++library->retainedNameSlots;
                continue;
            }
            const auto name=shortString(row,15,nonAscii);
            if (name.isEmpty()) fail(QStringLiteral("有指针目录条目缺少名称。"));
            if (start<firstDataRecord || qsizetype(start)>bytes.size()/recordSize || (count>0 && qsizetype(start)==bytes.size()/recordSize))
                fail(QStringLiteral("目录槽 %1 的数据指针超出库数据区。").arg(slot+1));
            total+=count;
            if (total>maximumTotalPrimitives) fail(QStringLiteral("目录累计声明超过 200000 个图元。"));
            LibraryEntry entry; entry.name=name; entry.slot=slot; entry.primitiveCount=count; entry.firstRecord=start;
            if (!zero(row,0,2) || !zero(row,22,10)) entry.error=QStringLiteral("目录存在未知标志字段，禁止该条目预览。");
            library->entries.append(entry);
        }
        QList<qsizetype> order;
        for (qsizetype i=0;i<library->entries.size();++i) order.append(i);
        std::sort(order.begin(),order.end(),[&](qsizetype a,qsizetype b) { return library->entries[a].firstRecord<library->entries[b].firstRecord; });
        for (qsizetype i=0;i<order.size();++i) {
            auto& entry=library->entries[order[i]];
            entry.limitRecord=i+1<order.size()?library->entries[order[i+1]].firstRecord:quint32(bytes.size()/recordSize);
            if (i+1<order.size() && entry.firstRecord==entry.limitRecord) fail(QStringLiteral("目录包含重复数据指针，尚不支持别名或重叠条目。"));
            if (!entry.error.isEmpty()) continue;
            try { entry.preview=decode(*library,entry); }
            catch (const LibraryError& error) {
                entry.error=QStringLiteral("封装 %1（起始记录 %2）：%3").arg(entry.name).arg(entry.firstRecord).arg(error.message);
            }
        }
        if (nonAscii) library->warnings.append(QStringLiteral("目录名称包含非 ASCII 字节，旧代码页未确认。"));
        library->warnings.append(QStringLiteral("指针为 FFFF 的目录槽只计为未分配；残留名称不等于可用封装。"));
        return {library,{}};
    } catch (const LibraryError& error) { return {{},error.message}; }
}

LibraryReadResult LegacyLibraryReader::readFile(const QString& path) {
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) return {{},QStringLiteral("无法只读打开库：%1").arg(file.errorString())};
    if (file.size()>maximumBytes) return {{},QStringLiteral("LIB 文件超过 8 MiB 限制。")};
    const auto bytes=file.read(maximumBytes+1);
    if (file.error()!=QFileDevice::NoError) return {{},QStringLiteral("读取库失败：%1").arg(file.errorString())};
    return parse(bytes,QFileInfo(file).absoluteFilePath());
}
}
