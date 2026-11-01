#include "io/LegacyTrackInsertionPlanner.h"
#include "io/LegacyPcbReader.h"
#include "io/LegacyPcbWriter.h"
#include <cmath>

namespace pt {
namespace {
// 与严格读取器的语法记录上限一致；字段行和 COMP 隐式文字不另计记录。
constexpr qsizetype maximumRecords = 200000;

bool coordinate(qreal value) {
    return std::isfinite(value) && std::trunc(value) == value && std::abs(value) <= 1000000;
}
}

LegacyTrackInsertionPlan LegacyTrackInsertionPlanner::prepare(const BoardDocument& original, const BoardDocument& current) {
    const auto fail = [](const QString& error) {
        LegacyTrackInsertionPlan result;
        result.error = error;
        result.baseLayout.insertion.unavailableReason = QStringLiteral("预检失败，不提供局部插入计划：%1").arg(error);
        return result;
    };

    auto loadedOnly = current;
    loadedOnly.tracks.clear();
    QList<Track> created;
    quint64 previousSequence = 0;
    for (const auto& track : current.tracks) {
        if (track.identity.kind == TrackIdentity::Kind::Loaded) {
            if (!created.isEmpty()) return fail(QStringLiteral("载入走线必须全部位于新建走线之前。"));
            loadedOnly.tracks.append(track);
            continue;
        }
        if (track.identity.kind != TrackIdentity::Kind::Created)
            return fail(QStringLiteral("走线身份未分配或类型无效，不能准备插入计划。"));
        if (!track.identity.valid() || track.identity.value <= previousSequence)
            return fail(QStringLiteral("新建走线身份必须非零、唯一且按创建序号严格递增；允许序号缺号。"));
        if (track.source.line != 0 || track.source.byteOffset != -1 || track.source.component != -1)
            return fail(QStringLiteral("新建走线不能带原来源行、字节偏移或元件归属。"));
        if (track.extra.has_value())
            return fail(QStringLiteral("新建走线不能带未知附加字段；新增 FT 编码策略尚未核定。"));
        const qreal coordinates[] = {track.start.x(), track.start.y(), track.end.x(), track.end.y()};
        for (const auto value : coordinates) {
            if (!coordinate(value)) return fail(QStringLiteral("新建走线坐标必须是 ±1000000 mil 内的有限整数。"));
        }
        if (track.width < 1 || track.width > 1000000)
            return fail(QStringLiteral("新建走线宽度必须在 1 至 1000000 mil 范围。"));
        if (track.layer != 1 && track.layer != 6)
            return fail(QStringLiteral("新建走线仅支持铜层 1 或 6。"));
        if (track.start == track.end) return fail(QStringLiteral("新建走线长度必须非零。"));
        previousSequence = track.identity.value;
        created.append(track);
    }

    // 复用冻结原件、摘要、载入身份、原记录次序与受限修改校验，禁止重新读取源路径。
    const auto base = LegacyPcbWriter::prepare(original, loadedOnly);
    if (!base.succeeded()) return fail(base.error);

    // 位移可改变数字长度，删除可缩短文件；必须在编辑后的字节上重新获取语法布局。
    const auto parsed = LegacyPcbReader::parseWithLayout(base.bytes, original.filePath);
    if (!parsed.succeeded()) return fail(parsed.error);
    // 只使用编辑后字节的严格解析计数，删除旧段释放实际记录容量。
    // recordCounts 包含元件内部及 ENDCOMP，唯独不含 ENDPCB，因此另加一条。
    qsizetype baseRecords = 1;
    for (const auto count : parsed.document->recordCounts) baseRecords += count;
    if (created.size() > maximumRecords - baseRecords)
        return fail(QStringLiteral("编辑后原有语法记录数加新建走线超过 200000 的安全限制（含 COMP、ENDCOMP、元件内部记录及 ENDPCB）。"));
    qsizetype insertionOffset = -1;
    if (!created.isEmpty()) {
        const auto& layout = parsed.layout;
        if (layout.geometryAfterNetdef)
            return fail(QStringLiteral("NETDEF 与几何或 COMP 交错，拒绝新增走线插入计划。"));
        if (layout.netdefCount != 0 || layout.insertion.kind == LegacyPcbInsertionKind::BeforeTrailingNetdefs)
            return fail(QStringLiteral("尾部 NETDEF 前新增走线的原软件排序尚未验证，本版暂不支持。"));
        if (layout.insertion.kind != LegacyPcbInsertionKind::BeforeEndPcb || !layout.insertion.isValid())
            return fail(QStringLiteral("严格解析未提供无 NETDEF 的 ENDPCB 前插入位置。"));
        insertionOffset = layout.insertion.byteOffset;
    }
    return {base.bytes, parsed.layout, created, insertionOffset, {}};
}

}
