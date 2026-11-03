#include "io/LegacyPcbReader.h"
#include <QCoreApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <iostream>

namespace {
const QString notice = QStringLiteral("仅证明本项目严格解析成功，不代表原 AUTOTRAX 兼容；FT 字段和换行观测不是默认编码策略。");
const QString usage = QStringLiteral("用法：pt-pcb-check [--track-limit 0..1000] [--] <PCB 路径>；默认最多输出 100 条自由 FT 明细；--help 只显示说明，不读取文件。");

int output(QJsonObject report, int code) {
    report.insert(QStringLiteral("originalSoftwareCompatibilityVerified"), false);
    report.insert(QStringLiteral("notice"), notice);
    const auto bytes = QJsonDocument(report).toJson(QJsonDocument::Indented);
    std::cout.write(bytes.constData(), bytes.size());
    std::cout.flush();
    return std::cout.good() ? code : 3;
}
int failure(const QString& message, const QString& path, int code) {
    return output({{"succeeded", false}, {"path", path}, {"error", message}}, code);
}

// 只在严格解析确认的单条 FT 区间内观察两行，绝不以正文标签搜索记录。
bool observeTrack(const QByteArray& bytes, const pt::LegacyPcbRecordBoundary& record,
    const pt::Track& track, QJsonObject& observation) {
    if (record.beginOffset < 0 || record.endOffset > bytes.size() || record.beginOffset >= record.endOffset
        || record.line != track.source.line || track.source.component != -1
        || track.identity != pt::TrackIdentity::loaded(record.line)) return false;
    const auto tagEnd = bytes.indexOf('\n', record.beginOffset);
    if (tagEnd < record.beginOffset || tagEnd >= record.endOffset) return false;
    const auto valuesBegin = tagEnd + 1;
    const auto valuesLf = bytes.indexOf('\n', valuesBegin);
    const auto valuesEnd = valuesLf < 0 ? record.endOffset : valuesLf + 1;
    if (valuesBegin >= record.endOffset || valuesEnd != record.endOffset) return false;
    const auto tag = bytes.mid(record.beginOffset, valuesBegin - record.beginOffset);
    const auto values = bytes.mid(valuesBegin, valuesEnd - valuesBegin);
    if (tag.trimmed() != "FT") return false;
    const auto fields = values.simplified().split(' ').size();
    if (fields != (track.extra.has_value() ? 7 : 6)) return false;
    const auto ending = [](const QByteArray& line) {
        if (line.endsWith("\r\n")) return QStringLiteral("\r\n");
        if (line.endsWith('\n')) return QStringLiteral("\n");
        if (line.endsWith('\r')) return QStringLiteral("\r");
        return QString{};
    };
    observation = {{"fieldCount", qint64(fields)}, {"tagLineEnding", ending(tag)},
        {"valuesLineEnding", ending(values)}, {"beginOffset", qint64(record.beginOffset)},
        {"endOffset", qint64(record.endOffset)}};
    return true;
}
QString insertionKind(pt::LegacyPcbInsertionKind kind) {
    switch (kind) {
    case pt::LegacyPcbInsertionKind::BeforeEndPcb: return QStringLiteral("BeforeEndPcb");
    case pt::LegacyPcbInsertionKind::BeforeTrailingNetdefs: return QStringLiteral("BeforeTrailingNetdefs");
    case pt::LegacyPcbInsertionKind::None: return QStringLiteral("None");
    }
    return QStringLiteral("None");
}
}

int main(int argc, char** argv) {
    QCoreApplication application(argc, argv);
    const auto arguments = application.arguments().mid(1);
    if (arguments == QStringList{QStringLiteral("--help")})
        return output({{"usage", usage}}, 0);
    QString path;
    int trackLimit = 100;
    bool hasLimit = false, positionalOnly = false;
    for (qsizetype i = 0; i < arguments.size(); ++i) {
        const auto& argument = arguments[i];
        if (!positionalOnly && argument == QStringLiteral("--")) { positionalOnly = true; continue; }
        if (!positionalOnly && argument == QStringLiteral("--track-limit")) {
            if (hasLimit || ++i >= arguments.size()) return failure(QStringLiteral("--track-limit 必须且只能指定一次 0..1000 整数。") + usage, path, 2);
            const auto& value = arguments[i];
            bool digits = !value.isEmpty();
            for (const auto ch : value) digits = digits && ch >= QLatin1Char('0') && ch <= QLatin1Char('9');
            bool ok = false;
            trackLimit = value.toInt(&ok);
            if (!digits || !ok || trackLimit < 0 || trackLimit > 1000)
                return failure(QStringLiteral("--track-limit 必须是 0..1000 的十进制整数。") + usage, path, 2);
            hasLimit = true;
        } else if ((!positionalOnly && argument.startsWith(QLatin1Char('-'))) || !path.isEmpty() || argument.isEmpty()) {
            return failure(QStringLiteral("参数无效或 PCB 路径不唯一。") + usage, path, 2);
        } else path = argument;
    }
    if (path.isEmpty()) return failure(QStringLiteral("缺少 PCB 路径。") + usage, path, 2);

    // 唯一一次文件读取；布局解析严格复用冻结的同一份完整输入字节。
    const auto loaded = pt::LegacyPcbReader::readFile(path);
    if (!loaded.succeeded()) return failure(loaded.error, path, 1);
    const auto& board = *loaded.document;
    const auto parsed = pt::LegacyPcbReader::parseWithLayout(board.sourceBytes, board.filePath);
    if (!parsed.succeeded()) return failure(parsed.error, board.filePath, 1);
    const auto& layout = parsed.layout;
    QJsonArray tracks;
    qsizetype trackIndex = 0, freeTrackCount = 0;
    for (const auto& record : layout.topLevelRecords) {
        if (record.tag != "FT") continue;
        while (trackIndex < board.tracks.size() && board.tracks[trackIndex].source.component >= 0) ++trackIndex;
        if (trackIndex >= board.tracks.size()) return failure(QStringLiteral("严格布局 FT 与载入模型无法对应，拒绝输出部分报告。"), board.filePath, 1);
        const auto& track = board.tracks[trackIndex++];
        QJsonObject observation;
        if (!observeTrack(board.sourceBytes, record, track, observation))
            return failure(QStringLiteral("无法确认 FT 原记录的两行边界或六／七字段布局，拒绝猜测。"), board.filePath, 1);
        if (freeTrackCount++ >= trackLimit) continue;
        QJsonObject detail{{"start", QJsonArray{qint64(track.start.x()), qint64(track.start.y())}},
            {"end", QJsonArray{qint64(track.end.x()), qint64(track.end.y())}},
            {"width", track.width}, {"layer", track.layer},
            {"identity", QJsonObject{{"kind", "Loaded"}, {"value", qint64(track.identity.value)}}},
            {"sourceLine", qint64(track.source.line)}, {"sourceByteOffset", track.source.byteOffset},
            {"sourceComponent", qint64(track.source.component)}, {"sourceRecord", observation}};
        if (track.extra) detail.insert(QStringLiteral("extra"), *track.extra);
        tracks.append(detail);
    }
    while (trackIndex < board.tracks.size() && board.tracks[trackIndex].source.component >= 0) ++trackIndex;
    if (trackIndex != board.tracks.size() || freeTrackCount != board.recordCounts.value(QStringLiteral("FT")))
        return failure(QStringLiteral("严格布局与自由 FT 总数不一致，拒绝输出部分报告。"), board.filePath, 1);

    QJsonObject counts;
    qint64 recordCount = 1; // ENDPCB 不在 reader 的 recordCounts 中。
    for (auto it = board.recordCounts.cbegin(); it != board.recordCounts.cend(); ++it) {
        counts.insert(it.key(), qint64(it.value()));
        recordCount += it.value();
    }
    const auto& newlines = layout.newlines;
    const auto& insertion = layout.insertion;
    return output({{"succeeded", true}, {"path", board.filePath}, {"sha256", board.sha256},
        {"byteSize", board.byteSize}, {"recordCounts", counts}, {"syntaxRecordCount", recordCount},
        {"primitiveCount", qint64(board.primitiveCount())}, {"freeTrackCount", qint64(freeTrackCount)},
        {"trackLimit", trackLimit}, {"freeTracksOmitted", qint64(freeTrackCount - tracks.size())}, {"freeTracks", tracks},
        {"layout", QJsonObject{{"sourceByteSize", qint64(layout.sourceByteSize)},
            {"textEndOffset", qint64(layout.textEndOffset)}, {"dosEofOffset", qint64(layout.dosEofOffset)},
            {"endPcbOffset", qint64(layout.endPcbOffset)}, {"trailingNetdefsOffset", qint64(layout.trailingNetdefsOffset)},
            {"netdefCount", qint64(layout.netdefCount)}, {"geometryAfterNetdef", layout.geometryAfterNetdef},
            {"topLevelRecordCount", qint64(layout.topLevelRecords.size())},
            {"originalSoftwareInsertionVerified", false},
            {"unverifiedReasons", QJsonArray::fromStringList(layout.unverifiedReasons)},
            {"newlines", QJsonObject{{"lfCount", qint64(newlines.lfCount)}, {"crlfCount", qint64(newlines.crlfCount)},
                {"bareCarriageReturnCount", qint64(newlines.bareCarriageReturnCount)}, {"mixed", newlines.mixed()},
                {"textEndsWithNewline", newlines.textEndsWithNewline},
                {"firstLineEnding", QString::fromLatin1(newlines.firstLineEnding)}}},
            {"insertion", QJsonObject{{"kind", insertionKind(insertion.kind)}, {"valid", insertion.isValid()},
                {"byteOffset", qint64(insertion.byteOffset)}, {"anchorLineEnding", QString::fromLatin1(insertion.anchorLineEnding)},
                {"unavailableReason", insertion.unavailableReason}}}}}}, 0);
}
