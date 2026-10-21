#include "io/LegacyPcbReader.h"
#include "io/LegacyNetlistReader.h"
#include "io/DosText.h"
#include <QCryptographicHash>
#include <QFile>
#include <QFileInfo>
#include <array>

namespace pt {
namespace {
constexpr qint64 maximumBytes = 64 * 1024 * 1024;
constexpr int maximumCoordinate = 1000000;
constexpr qsizetype maximumRecords = 200000;

struct ParseError { QString message; };

class Reader {
public:
    explicit Reader(const QByteArray& bytes) : m_bytes(bytes) {}
    std::shared_ptr<BoardDocument> run() {
        if (line().trimmed() != "PCB FILE 4") fail(QStringLiteral("仅支持 PCB FILE 4 文件头。"));
        bool ended = false;
        bool inComponent = false;
        while (m_offset < m_bytes.size()) {
            const auto tag = line().trimmed();
            if (tag.isEmpty()) continue;
            const qsizetype recordLine = m_line;
            const PrimitiveSource source{recordLine, inComponent ? m_board->components.size()-1 : -1};
            if (++m_records > maximumRecords) fail(QStringLiteral("记录数超过 200000 的安全限制。"));
            if (tag == "ENDPCB") {
                if (inComponent) fail(QStringLiteral("元件尚未以 ENDCOMP 结束。"));
                ended = true;
                while (m_offset < m_bytes.size()) {
                    if (!line().trimmed().isEmpty()) fail(QStringLiteral("ENDPCB 后仍有数据。"));
                }
                break;
            }
            if (tag=="NETDEF") {
                if (inComponent) fail(QStringLiteral("NETDEF 不能出现在元件内部。"));
                const auto sectionStart=m_offset;
                const auto result=LegacyNetlistReader::readEmbedded(m_bytes,m_offset,m_line);
                if (!result.error.isEmpty()) throw ParseError{result.error};
                m_offset=result.nextOffset; m_line=result.nextLine;
                if (!m_netlist) { m_netlist=std::make_shared<Netlist>(); m_netlist->embedded=true; }
                m_netNodes+=result.net.nodes.size();m_netBytes+=result.nextOffset-sectionStart;
                if (m_netNodes>200000 || m_netlist->nets.size()>=20000 || m_netBytes>8*1024*1024) fail(QStringLiteral("NETDEF 网络或节点超过安全限制。"));
                if (!result.net.metadata.isEmpty()) m_board->warnings.append(QStringLiteral("NETDEF %1 的附加元数据已保留，尚未解释。").arg(result.net.name));
                m_netlist->nets.append(result.net);
                ++m_board->recordCounts[QStringLiteral("NETDEF")];
                continue;
            }
            if (tag == "COMP") {
                if (inComponent) fail(QStringLiteral("不允许嵌套 COMP。"));
                ++m_board->recordCounts[QStringLiteral("COMP")];
                Component c;
                c.designator = textLine(); c.footprint = textLine(); c.comment = textLine();
                auto comment = textFields(); comment.value = c.comment;
                comment.source = {m_line, m_board->components.size()};
                auto designator = textFields(); designator.value = c.designator;
                designator.source = {m_line, m_board->components.size()};
                const auto v = numbers(5);
                coordinate(v[0]); coordinate(v[1]);
                if ((v[2] != 1 && v[2] != 2) || (v[3] != 1 && v[3] != 2)) fail(QStringLiteral("不支持的元件文字显隐状态。"));
                c.origin = {qreal(v[0]), qreal(v[1])}; c.placement = v[4];
                // 元件图元和标签在板图文件中已是绝对坐标，不再次叠加元件原点。
                if (v[2] == 1 && !designator.value.isEmpty()) m_board->texts.append(designator);
                if (v[3] == 1 && !comment.value.isEmpty()) m_board->texts.append(comment);
                m_board->components.append(c);
                inComponent = true;
                continue;
            }
            if (tag == "ENDCOMP") {
                if (!inComponent) fail(QStringLiteral("ENDCOMP 没有对应的 COMP。"));
                ++m_board->recordCounts[QStringLiteral("ENDCOMP")];
                inComponent = false;
                continue;
            }
            if (tag.size() != 2 || (tag[0] != 'F' && tag[0] != 'C') || !QByteArray("TPVAFS").contains(tag[1])) {
                fail(QStringLiteral("尚不支持记录 %1；为避免丢失数据，已停止载入。").arg(QString::fromLatin1(tag.left(80))));
            }
            if ((tag[0] == 'C') != inComponent) fail(QStringLiteral("自由图元与元件图元的所属范围不正确。"));
            ++m_board->recordCounts[QString::fromLatin1(tag)];
            switch (tag[1]) {
            case 'T': {
                const auto v = numbers(6, true);
                for (int i = 0; i < 4; ++i) coordinate(v[i]);
                positive(v[4]); layer(v[5]);
                Track track{{qreal(v[0]), qreal(v[1])}, {qreal(v[2]), qreal(v[3])}, v[4], v[5], {}};
                if (m_fieldCount == 7) { track.extra = v[6]; m_extraTrackField = true; }
                track.source = source;
                m_board->tracks.append(track);
                break;
            }
            case 'P': {
                const auto v = numbers(8);
                coordinate(v[0]); coordinate(v[1]); positive(v[2]); positive(v[3]); layer(v[7]);
                if (v[4] < 1 || v[4] > 4) fail(QStringLiteral("尚不支持此焊盘形状。"));
                if (v[5] < 0 || v[5] > qMin(v[2], v[3])) fail(QStringLiteral("焊盘孔径超出焊盘尺寸。"));
                if (v[6] < 0 || v[6] > 255) fail(QStringLiteral("焊盘平面标志超出范围。"));
                m_board->pads.append({{qreal(v[0]), qreal(v[1])}, v[2], v[3], v[4], v[5], v[6], v[7], textLine(), source});
                break;
            }
            case 'V': {
                const auto v = numbers(4);
                coordinate(v[0]); coordinate(v[1]); positive(v[2]);
                if (v[3] < 0 || v[3] > v[2]) fail(QStringLiteral("过孔孔径超出外径。"));
                m_board->vias.append({{qreal(v[0]), qreal(v[1])}, v[2], v[3], source});
                break;
            }
            case 'A': {
                const auto v = numbers(6);
                coordinate(v[0]); coordinate(v[1]); positive(v[2]); positive(v[4]); layer(v[5]);
                if (v[3] < 1 || v[3] > 15) fail(QStringLiteral("圆弧象限掩码必须为 1 至 15。"));
                m_board->arcs.append({{qreal(v[0]), qreal(v[1])}, v[2], v[3], v[4], v[5], source});
                break;
            }
            case 'F': {
                const auto v = numbers(5);
                for (int i = 0; i < 4; ++i) coordinate(v[i]);
                layer(v[4]);
                if (v[0] == v[2] || v[1] == v[3]) fail(QStringLiteral("填充矩形的宽高必须非零。"));
                m_board->fills.append({QRectF(QPointF(v[0], v[1]), QPointF(v[2], v[3])).normalized(), v[4], source});
                break;
            }
            case 'S': {
                auto t = textFields(); t.source = source; t.value = textLine(); m_board->texts.append(t);
                break;
            }
            }
        }
        if (!ended) fail(QStringLiteral("缺少 ENDPCB 文件结束标记。"));
        if (m_extraTrackField) m_board->warnings.append(QStringLiteral("部分走线有第七附加字段，已保留原值但未解释其电气属性；仅显示已验证的几何字段。"));
        if (!m_board->texts.isEmpty()) {
            m_board->warnings.append(QStringLiteral("文字使用系统等宽字体近似显示，未恢复原 DOS 笔画字体和精确文字边界。"));
        }
        for (const auto& pad : m_board->pads) {
            if (pad.shape >= 3) {
                m_board->warnings.append(QStringLiteral("八角和圆角矩形焊盘的倒角尺寸尚未与原程序逐像素核对，当前为预览近似。"));
                break;
            }
        }
        if (m_nonAscii) m_board->warnings.append(QStringLiteral("发现非 ASCII 字节，旧代码页尚未确认，相关字符暂以替代符显示。"));
        m_board->embeddedNetlist=m_netlist;
        return m_board;
    }
private:
    [[noreturn]] void fail(const QString& message) const {
        throw ParseError{QStringLiteral("第 %1 行：%2").arg(m_line).arg(message)};
    }
    QByteArray line() {
        if (m_offset >= m_bytes.size()) fail(QStringLiteral("记录意外结束。"));
        const qsizetype end = m_bytes.indexOf('\n', m_offset);
        const qsizetype stop = end < 0 ? m_bytes.size() : end;
        ++m_line;
        if (stop - m_offset > 65536) fail(QStringLiteral("单行超过 64 KiB。"));
        auto result = m_bytes.mid(m_offset, stop - m_offset);
        m_offset = end < 0 ? m_bytes.size() : end + 1;
        if (result.endsWith('\r')) result.chop(1);
        return result;
    }
    QString textLine() {
        const auto bytes = line();
        QString text;
        for (unsigned char ch : bytes) {
            if (ch >= 128) { text.append(QChar::ReplacementCharacter); m_nonAscii = true; }
            else if (ch < 32 && ch != '\t') fail(QStringLiteral("文字包含不支持的控制字符。"));
            else text.append(QChar(ch));
        }
        return text;
    }
    std::array<int, 8> numbers(qsizetype count, bool allowTrackExtension = false) {
        auto raw = line().simplified();
        const auto tokens = raw.split(' ');
        m_fieldCount = tokens.size();
        if (tokens.size() != count && !(allowTrackExtension && tokens.size() == 7)) fail(QStringLiteral("数值字段数量应为 %1，实际为 %2。").arg(count).arg(tokens.size()));
        std::array<int, 8> values{};
        for (qsizetype i = 0; i < tokens.size(); ++i) {
            bool ok = false;
            values[i] = tokens[i].toInt(&ok);
            if (!ok) fail(QStringLiteral("字段不是有效的十进制整数。"));
        }
        return values;
    }
    void coordinate(int value) const {
        if (value < -maximumCoordinate || value > maximumCoordinate) fail(QStringLiteral("坐标超出支持范围（±1000000 mil）。"));
    }
    void positive(int value) const {
        if (value <= 0 || value > maximumCoordinate) fail(QStringLiteral("尺寸必须在 1 至 1000000 mil 范围。"));
    }
    void layer(int value) const {
        if (value < 1 || value > 13) fail(QStringLiteral("图层编号必须为 1 至 13。"));
    }
    BoardText textFields() {
        const auto v = numbers(6);
        coordinate(v[0]); coordinate(v[1]); positive(v[2]); positive(v[4]); layer(v[5]);
        if (!((v[3] >= 0 && v[3] <= 3) || (v[3] >= 16 && v[3] <= 19))) fail(QStringLiteral("不支持的文字方向编码。"));
        return {{qreal(v[0]), qreal(v[1])}, v[2], v[3] & 3, v[4], v[5], (v[3] & 16) != 0, {}};
    }
    const QByteArray& m_bytes;
    qsizetype m_offset = 0, m_line = 0, m_records = 0, m_fieldCount = 0;
    bool m_nonAscii = false, m_extraTrackField = false;
    std::shared_ptr<BoardDocument> m_board = std::make_shared<BoardDocument>();
    std::shared_ptr<Netlist> m_netlist;
    qsizetype m_netNodes=0,m_netBytes=0;
};
}

BoardReadResult LegacyPcbReader::parse(const QByteArray& bytes, const QString& source) {
    if (bytes.size() > maximumBytes) return {{}, QStringLiteral("文件超过 64 MiB 安全限制。")};
    if (bytes.contains('\0')) return {{}, QStringLiteral("PCB 文本中不允许二进制零字节。")};
    const auto end=dosTextEnd(bytes);
    if (end<0) return {{},QStringLiteral("DOS EOF 后存在非空白数据，禁止截断板图。")};
    const auto textBytes=bytes.left(end);
    try {
        auto board = Reader(textBytes).run();
        board->filePath = source; board->byteSize = bytes.size();
        board->sha256 = QString::fromLatin1(QCryptographicHash::hash(bytes, QCryptographicHash::Sha256).toHex());
        if (board->embeddedNetlist) {
            auto netlist=std::make_shared<Netlist>(*board->embeddedNetlist);
            netlist->filePath=source; netlist->sha256=board->sha256; netlist->sourceBytes=bytes;
            netlist->warnings.append(QStringLiteral("NETDEF 来自公开结构描述和合成测试，本地原始 PCB 尚无可用实例对照；元数据未作电气解释。"));
            board->embeddedNetlist=netlist;
        }
        return {board, {}};
    } catch (const ParseError& error) {
        return {{}, error.message};
    }
}

BoardReadResult LegacyPcbReader::readFile(const QString& path) {
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) return {{}, QStringLiteral("无法读取板图：%1").arg(file.errorString())};
    if (file.size() > maximumBytes) return {{}, QStringLiteral("文件超过 64 MiB 安全限制。")};
    const auto bytes = file.read(maximumBytes + 1);
    if (file.error() != QFileDevice::NoError) return {{}, QStringLiteral("读取板图失败：%1").arg(file.errorString())};
    return parse(bytes, QFileInfo(file).absoluteFilePath());
}
}
