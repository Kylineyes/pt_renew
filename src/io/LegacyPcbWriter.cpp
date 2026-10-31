#include "io/LegacyPcbWriter.h"
#include "io/LegacyPcbReader.h"
#include <QCryptographicHash>
#include <QDir>
#include <QFileInfo>
#include <QTemporaryFile>
#include <algorithm>
#include <cmath>

namespace pt {
namespace {
bool sameSource(const PrimitiveSource& a, const PrimitiveSource& b, bool lines) {
    return a.component == b.component && (!lines || (a.line == b.line && a.byteOffset == b.byteOffset));
}
bool same(const Track& a, const Track& b, bool lines) {
    return a.start == b.start && a.end == b.end && a.width == b.width && a.layer == b.layer
        && a.extra == b.extra && sameSource(a.source, b.source, lines);
}
bool same(const Pad& a, const Pad& b, bool lines) {
    return a.center == b.center && a.width == b.width && a.height == b.height && a.shape == b.shape
        && a.drill == b.drill && a.planeFlags == b.planeFlags && a.layer == b.layer && a.name == b.name
        && sameSource(a.source, b.source, lines);
}
bool same(const Via& a, const Via& b, bool lines) {
    return a.center == b.center && a.diameter == b.diameter && a.drill == b.drill && sameSource(a.source, b.source, lines);
}
bool same(const Arc& a, const Arc& b, bool lines) {
    return a.center == b.center && a.radius == b.radius && a.quadrants == b.quadrants && a.width == b.width
        && a.layer == b.layer && sameSource(a.source, b.source, lines);
}
bool same(const Fill& a, const Fill& b, bool lines) {
    return a.rectangle == b.rectangle && a.layer == b.layer && sameSource(a.source, b.source, lines);
}
bool same(const BoardText& a, const BoardText& b, bool lines) {
    return a.position == b.position && a.height == b.height && a.direction == b.direction && a.stroke == b.stroke
        && a.layer == b.layer && a.mirrored == b.mirrored && a.value == b.value && sameSource(a.source, b.source, lines);
}
bool same(const Component& a, const Component& b, bool) {
    return a.designator == b.designator && a.footprint == b.footprint && a.comment == b.comment
        && a.origin == b.origin && a.placement == b.placement;
}
template<class T> bool sameList(const QList<T>& a, const QList<T>& b, bool lines) {
    if (a.size() != b.size()) return false;
    for (qsizetype i = 0; i < a.size(); ++i) if (!same(a[i], b[i], lines)) return false;
    return true;
}
bool sameOtherGeometry(const BoardDocument& a, const BoardDocument& b, bool lines) {
    return sameList(a.pads, b.pads, lines) && sameList(a.vias, b.vias, lines) && sameList(a.arcs, b.arcs, lines)
        && sameList(a.fills, b.fills, lines) && sameList(a.texts, b.texts, lines) && sameList(a.components, b.components, lines);
}
bool sameNetlist(const std::shared_ptr<const Netlist>& a, const std::shared_ptr<const Netlist>& b, bool lines) {
    if (!a || !b) return a == b;
    if (a->embedded != b->embedded || a->components.size() != b->components.size() || a->nets.size() != b->nets.size()) return false;
    for (qsizetype i = 0; i < a->components.size(); ++i) {
        const auto& x = a->components[i]; const auto& y = b->components[i];
        if (x.designator != y.designator || x.footprint != y.footprint || x.comment != y.comment
            || x.additionalFields != y.additionalFields || (lines && x.sourceLine != y.sourceLine)) return false;
    }
    for (qsizetype i = 0; i < a->nets.size(); ++i) {
        const auto& x = a->nets[i]; const auto& y = b->nets[i];
        if (x.name != y.name || x.metadata != y.metadata || x.nodes.size() != y.nodes.size()
            || (lines && x.sourceLine != y.sourceLine)) return false;
        for (qsizetype j = 0; j < x.nodes.size(); ++j)
            if (x.nodes[j].token != y.nodes[j].token || (lines && x.nodes[j].sourceLine != y.nodes[j].sourceLine)) return false;
    }
    return true;
}
struct Line { qsizetype begin, end; };
QList<Line> lineSpans(const QByteArray& bytes) {
    QList<Line> result;
    for (qsizetype begin = 0; begin < bytes.size();) {
        const auto newline = bytes.indexOf('\n', begin);
        const auto end = newline < 0 ? bytes.size() : newline + 1;
        result.append({begin, end}); begin = end;
    }
    return result;
}
struct Replacement { qsizetype begin, end; QByteArray bytes; };
bool coordinate(qreal value) { return std::isfinite(value) && std::trunc(value) == value && std::abs(value) <= 1000000; }
QString normalizedDestination(const QString& path) {
    const QFileInfo info(path);
    const auto parent = info.dir().canonicalPath();
    return QDir::cleanPath((parent.isEmpty() ? info.absolutePath() : parent) + '/' + info.fileName());
}
bool samePath(const QString& a, const QString& b) {
#ifdef Q_OS_WIN
    return a.compare(b, Qt::CaseInsensitive) == 0;
#else
    return a == b;
#endif
}
}

BoardWriteResult LegacyPcbWriter::prepare(const BoardDocument& original, const BoardDocument& current) {
    auto fail = [](const QString& error) { return BoardWriteResult{{}, {}, {}, error}; };
    if (!original.sourceContext.isEmpty() || !current.sourceContext.isEmpty()) return fail(QStringLiteral("库预览不能另存为 PCB。"));
    const auto& raw = original.sourceBytes;
    const auto digest = QString::fromLatin1(QCryptographicHash::hash(raw, QCryptographicHash::Sha256).toHex());
    if (raw.isEmpty() || raw.size() != original.byteSize || digest != original.sha256)
        return fail(QStringLiteral("缺少完整原始板图字节或原始摘要不符，不能写出。"));
    const auto baseline = LegacyPcbReader::parse(raw, original.filePath);
    if (!baseline.succeeded() || !sameList(baseline.document->tracks, original.tracks, true)
        || !sameOtherGeometry(*baseline.document, original, true) || !sameNetlist(baseline.document->embeddedNetlist, original.embeddedNetlist, true)
        || baseline.document->recordCounts != original.recordCounts)
        return fail(QStringLiteral("原始文档与冻结字节不一致，不能写出。"));
    if (current.sourceBytes != raw || current.sha256 != original.sha256 || current.byteSize != original.byteSize
        || current.filePath != original.filePath || current.recordCounts != original.recordCounts
        || !sameOtherGeometry(original, current, true) || !sameNetlist(original.embeddedNetlist, current.embeddedNetlist, true))
        return fail(QStringLiteral("当前另存为仅支持自由走线移动或删除，检测到其他文档修改。"));
    // 按原来源行建立对应关系，不把删除后的数组下标误当记录身份。
    const auto spans = lineSpans(raw);
    QMap<qsizetype, qsizetype> indices;
    for (qsizetype i = 0; i < original.tracks.size(); ++i) {
        const auto line = original.tracks[i].source.line;
        if (line <= 0 || line >= spans.size() || indices.contains(line)) return fail(QStringLiteral("原走线来源记录不唯一或越界。"));
        indices.insert(line, i);
    }
    QMap<qsizetype, Track> surviving;
    qsizetype previous = -1;
    for (const auto& track : current.tracks) {
        const auto found = indices.constFind(track.source.line);
        if (found == indices.cend() || found.value() <= previous) return fail(QStringLiteral("不支持新增、重复或重排走线。"));
        previous = found.value(); surviving.insert(track.source.line, track);
    }
    QList<Replacement> replacements;
    for (const auto& before : original.tracks) {
        const auto line = before.source.line;
        const auto tag = spans[line - 1], values = spans[line];
        const auto after = surviving.constFind(line);
        if (after == surviving.cend()) {
            if (before.source.component >= 0) return fail(QStringLiteral("不支持删除元件内部走线。"));
            replacements.append({tag.begin, values.end, {}}); continue;
        }
        if (same(before, after.value(), true)) continue;
        if (before.source.component >= 0 || before.width != after->width || before.layer != after->layer
            || before.extra != after->extra || !sameSource(before.source, after->source, true))
            return fail(QStringLiteral("不支持修改元件内部走线或走线宽度、图层和附加字段。"));
        const auto delta = after->start - before.start;
        if (after->end - before.end != delta) return fail(QStringLiteral("当前仅支持走线整体平移，不支持改变走线形状。"));
        const qreal coordinates[] = {after->start.x(), after->start.y(), after->end.x(), after->end.y()};
        for (auto value : coordinates) if (!coordinate(value)) return fail(QStringLiteral("走线坐标必须是 ±1000000 mil 内的整数。"));
        // 仅替换前四个数值词；保留分隔符、换行及未解释的第七字段原字节。
        qsizetype cursor = values.begin;
        for (auto value : coordinates) {
            while (cursor < values.end && (raw[cursor] == ' ' || raw[cursor] == '\t' || raw[cursor] == '\r' || raw[cursor] == '\v' || raw[cursor] == '\f')) ++cursor;
            const auto begin = cursor;
            while (cursor < values.end && raw[cursor] != ' ' && raw[cursor] != '\t' && raw[cursor] != '\r' && raw[cursor] != '\n' && raw[cursor] != '\v' && raw[cursor] != '\f') ++cursor;
            if (cursor == begin) return fail(QStringLiteral("原走线数值记录不完整。"));
            replacements.append({begin, cursor, QByteArray::number(qint64(value))});
        }
    }
    QByteArray output;
    qsizetype cursor = 0;
    // 记录可能分布在元件前后，使用原字节偏移排序后一次顺序写出。
    std::sort(replacements.begin(), replacements.end(), [](const auto& a, const auto& b) { return a.begin < b.begin; });
    for (const auto& replacement : replacements) {
        if (replacement.begin < cursor) return fail(QStringLiteral("走线替换范围重叠，已停止写出。"));
        output.append(raw.constData() + cursor, replacement.begin - cursor); output.append(replacement.bytes); cursor = replacement.end;
    }
    output.append(raw.constData() + cursor, raw.size() - cursor);
    const auto reopened = LegacyPcbReader::parse(output, original.filePath);
    if (!reopened.succeeded() || !sameList(reopened.document->tracks, current.tracks, false)
        || !sameOtherGeometry(*reopened.document, current, false) || !sameNetlist(reopened.document->embeddedNetlist, current.embeddedNetlist, false))
        return fail(QStringLiteral("写出内容重新解析后与当前工作副本不一致，未创建目标文件。"));
    return {output, {}, QString::fromLatin1(QCryptographicHash::hash(output, QCryptographicHash::Sha256).toHex()), {}};
}

BoardWriteResult LegacyPcbWriter::saveAs(const QString& path, const BoardDocument& original, const BoardDocument& current) {
    auto result = prepare(original, current);
    if (!result.succeeded()) return result;
    auto fail = [&](const QString& error) { result.error = error; return result; };
    if (path.trimmed().isEmpty()) return fail(QStringLiteral("另存为路径不能为空。"));
    const QFileInfo target(path);
    // Windows的冒号可指定已有文件的备用数据流，不能把它当作“全新文件”。
    const auto name = target.fileName();
    const auto device = name.section(QLatin1Char('.'), 0, 0).toUpper();
    if (name.contains(QLatin1Char(':')) || device == QStringLiteral("CON") || device == QStringLiteral("PRN")
        || device == QStringLiteral("AUX") || device == QStringLiteral("NUL")
        || (device.size() == 4 && (device.startsWith(QStringLiteral("COM")) || device.startsWith(QStringLiteral("LPT")))
            && device[3] >= QLatin1Char('1') && device[3] <= QLatin1Char('9')))
        return fail(QStringLiteral("目标必须是普通 PCB 文件名，不能使用设备名或备用数据流。"));
    const auto destination = normalizedDestination(path);
    if (!original.filePath.isEmpty() && samePath(destination, normalizedDestination(original.filePath)))
        return fail(QStringLiteral("原输入始终只读，请选择不同的新 PCB 文件名。"));
    if (target.exists() || target.isSymLink()) return fail(QStringLiteral("目标已存在；当前只允许另存为全新文件，不覆盖已有文件。"));
    if (target.suffix().compare(QStringLiteral("pcb"), Qt::CaseInsensitive) != 0)
        return fail(QStringLiteral("另存为目标必须使用 .pcb 扩展名。"));
    QTemporaryFile staging(target.absolutePath() + QStringLiteral("/.pt-renew-XXXXXX.tmp"));
    if (!staging.open()) return fail(QStringLiteral("无法在目标目录创建临时文件：%1").arg(staging.errorString()));
    if (staging.write(result.bytes) != result.bytes.size() || !staging.flush())
        return fail(QStringLiteral("临时文件写入失败：%1").arg(staging.errorString()));
    // QTemporaryFile的同目录原子改名不采用复制回退，并拒绝覆盖已出现的目标。
    staging.close();
    if (!staging.rename(target.absoluteFilePath())) return fail(QStringLiteral("无法发布新文件（目标可能已存在）：%1").arg(staging.errorString()));
    staging.setAutoRemove(false);
    result.filePath = target.absoluteFilePath();
    return result;
}
}
