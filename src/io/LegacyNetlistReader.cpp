#include "io/LegacyNetlistReader.h"
#include "experiment/AsyncExperiment.h"
#include "io/DosText.h"
#include <QCryptographicHash>
#include <QFile>
#include <QFileInfo>

namespace pt {
namespace {
constexpr qsizetype maximumBytes=8*1024*1024, maximumLines=300000, maximumNodes=200000;
struct NetError { QString message; };
class Cursor {
public:
    Cursor(const QByteArray& bytes,qsizetype offset=0,qsizetype line=0): bytes(bytes),offset(offset),number(line),initialLine(line) {}
    QByteArray next() {
        if (offset>=bytes.size()) fail(QStringLiteral("记录意外结束。"));
        const auto newline=bytes.indexOf('\n',offset); const auto end=newline<0?bytes.size():newline;
        if (++number-initialLine>maximumLines || end-offset>65536) fail(QStringLiteral("行数或单行长度超出安全限制。"));
        auto text=bytes.mid(offset,end-offset); offset=newline<0?bytes.size():newline+1;
        if (text.endsWith('\r')) text.chop(1);
        for (unsigned char ch : text) if (ch>=127 || (ch<32 && ch!='\t')) fail(QStringLiteral("网表标识只支持已确认的 ASCII 文本，禁止控制字符或未知代码页。"));
        return text;
    }
    QString text() { return QString::fromLatin1(next()); }
    [[noreturn]] void fail(const QString& message) const { throw NetError{QStringLiteral("第 %1 行：%2").arg(number).arg(message)}; }
    const QByteArray& bytes;
    qsizetype offset,number,initialLine;
};
bool delimiter(const QByteArray& line) { return line=="[" || line=="]" || line=="(" || line==")" || line=="{" || line=="}" || line=="NETDEF" || line=="ENDPCB"; }
QString identifier(Cursor& cursor,const QByteArray& line) {
    const auto clean=line.trimmed();
    if (clean.isEmpty() || delimiter(clean) || clean.size()>255) cursor.fail(QStringLiteral("名称为空、超长或与结构分隔符冲突。"));
    return QString::fromLatin1(clean);
}
NetNode node(Cursor& cursor,const QByteArray& line) {
    const auto token=identifier(cursor,line);
    bool separator=false;
    for (qsizetype i=1;i+1<token.size();++i) if (token[i]==QLatin1Char('-')) separator=true;
    // 不按首个/最后一个连字符切分，允许负号引脚等标识；后续按板图全标识精确匹配。
    if (!separator || token.contains(' ') || token.contains('\t')) cursor.fail(QStringLiteral("节点必须为无空白的元件-引脚标识。"));
    return {token,cursor.number};
}
}

NetlistReadResult LegacyNetlistReader::parse(const QByteArray& original,const QString& source) {
    try {
        if (original.size()>maximumBytes) throw NetError{QStringLiteral("网表超过 8 MiB 限制。")};
        const qsizetype end=dosTextEnd(original);
        if (end<0) throw NetError{QStringLiteral("DOS EOF 后存在非空白数据或重复 EOF，禁止截断读取。")};
        const QByteArray bytes=original.left(end);
        auto result=std::make_shared<Netlist>(); result->sourceBytes=original; result->filePath=source;
        result->sha256=QString::fromLatin1(QCryptographicHash::hash(original,QCryptographicHash::Sha256).toHex());
        Cursor cursor(bytes); qsizetype nodes=0;
        while (cursor.offset<bytes.size()) {
            const auto tag=cursor.next().trimmed(); if (tag.isEmpty()) continue;
            const auto start=cursor.number;
            if (tag=="[") {
                NetlistComponent component; component.sourceLine=start;
                component.designator=identifier(cursor,cursor.next());
                const auto footprint=cursor.next(); if (delimiter(footprint.trimmed())) cursor.fail(QStringLiteral("元件缺少封装字段。"));
                component.footprint=QString::fromLatin1(footprint);
                const auto comment=cursor.next(); if (delimiter(comment.trimmed())) cursor.fail(QStringLiteral("元件缺少注释字段。"));
                component.comment=QString::fromLatin1(comment);
                bool ended=false;
                while (cursor.offset<bytes.size()) {
                    const auto line=cursor.next(); if (line.trimmed()=="]") { ended=true;break; }
                    if (delimiter(line.trimmed()) || component.additionalFields.size()>=64) cursor.fail(QStringLiteral("元件块嵌套、终止错误或附加字段过多。"));
                    component.additionalFields.append(QString::fromLatin1(line));
                }
                if (!ended) cursor.fail(QStringLiteral("元件块缺少 ]。"));
                if (result->components.size()>=20000) cursor.fail(QStringLiteral("元件声明超过 20000。"));
                result->components.append(component);
            } else if (tag=="(") {
                Net net; net.sourceLine=start; net.name=identifier(cursor,cursor.next()); bool ended=false;
                while (cursor.offset<bytes.size()) {
                    const auto line=cursor.next().trimmed(); if (line==")") { ended=true;break; }
                    if (line.isEmpty()) continue;
                    net.nodes.append(node(cursor,line));
                    if (++nodes>maximumNodes) cursor.fail(QStringLiteral("网络节点超过 200000。"));
                }
                if (!ended) cursor.fail(QStringLiteral("网络块缺少 )。"));
                if (net.nodes.isEmpty()) result->warnings.append(QStringLiteral("网络 %1 没有节点。").arg(net.name));
                if (result->nets.size()>=20000) cursor.fail(QStringLiteral("网络数量超过 20000。"));
                result->nets.append(net);
            } else cursor.fail(QStringLiteral("不支持的网表顶层记录：%1").arg(QString::fromLatin1(tag.left(80))));
        }
        if (result->components.isEmpty() && result->nets.isEmpty()) throw NetError{QStringLiteral("网表没有任何元件声明或网络。")};
        return {result,{}};
    } catch (const NetError& error) { return {{},error.message}; }
}

EmbeddedNetResult LegacyNetlistReader::readEmbedded(const QByteArray& bytes,qsizetype offset,qsizetype line) {
    EmbeddedNetResult result;
    try {
        if (offset<0 || offset>=bytes.size() || line<0 || line>bytes.size()) throw NetError{QStringLiteral("NETDEF 起始位置无效。")};
        Cursor cursor(bytes,offset,line); result.net.sourceLine=line+1;
        result.net.name=identifier(cursor,cursor.next());
        bool inNodes=false,ended=false; int metadataBlock=0; qsizetype metadataStart=0;
        while (cursor.offset<bytes.size()) {
            const auto rawStart=cursor.offset;
            const auto raw=cursor.next(); const auto tag=raw.trimmed();
            if (cursor.offset-offset>maximumBytes) cursor.fail(QStringLiteral("NETDEF 单节超过 8 MiB。"));
            if (metadataBlock) {
                if (tag==(metadataBlock==1?"]":"}")) {
                    result.net.metadata+=bytes.mid(metadataStart,cursor.offset-metadataStart);metadataBlock=0;continue;
                }
                if (delimiter(tag)) cursor.fail(QStringLiteral("NETDEF 元数据块嵌套或截断，当前不支持该变体。"));
                continue;
            }
            if (tag.isEmpty()) continue;
            if (tag=="[" || tag=="{") {
                metadataBlock=tag=="["?1:2;metadataStart=rawStart;continue;
            }
            if (tag=="(") { if (inNodes) cursor.fail(QStringLiteral("NETDEF 节点列表不允许嵌套。")); inNodes=true;continue; }
            if (tag==")") { if (!inNodes) cursor.fail(QStringLiteral("NETDEF 缺少节点列表起始符。")); ended=true;break; }
            if (!inNodes) cursor.fail(QStringLiteral("NETDEF 节点列表前存在未知记录。"));
            result.net.nodes.append(node(cursor,tag));
            if (result.net.nodes.size()>maximumNodes) cursor.fail(QStringLiteral("NETDEF 节点超过 200000。"));
        }
        if (!ended || metadataBlock) cursor.fail(QStringLiteral("NETDEF 节点列表或元数据未结束。"));
        result.nextOffset=cursor.offset; result.nextLine=cursor.number;
    } catch (const NetError& error) { result.error=error.message; }
    return result;
}

NetlistReadResult LegacyNetlistReader::readFile(const QString& path) {
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) return {{},QStringLiteral("无法读取网表：%1").arg(file.errorString())};
    if (file.size()>maximumBytes) return {{},QStringLiteral("网表超过 8 MiB 限制。")};
    experiment::checkpoint(QStringLiteral("net-file-open-before-read"));
    const auto bytes=file.read(maximumBytes+1);
    if (file.error()!=QFileDevice::NoError) return {{},QStringLiteral("读取网表失败：%1").arg(file.errorString())};
    return parse(bytes,QFileInfo(file).absoluteFilePath());
}
}
