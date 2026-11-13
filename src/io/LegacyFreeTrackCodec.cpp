#include "io/LegacyFreeTrackCodec.h"
#include <cmath>

namespace pt {

LegacyFreeTrackCodec::Result LegacyFreeTrackCodec::encode(
    QPointF start, QPointF end, int width, int layer, const Options& options) {
    const auto fail = [](const QString& error) { return Result{{}, error}; };
    switch (options.fields) {
    case FieldLayout::SixFields:
        if (options.extra) return fail(QStringLiteral("六字段 FT 不能提供附加整数。"));
        break;
    case FieldLayout::SevenFields:
        if (!options.extra) return fail(QStringLiteral("七字段 FT 必须显式提供附加整数。"));
        break;
    case FieldLayout::Unspecified:
        return fail(QStringLiteral("必须显式选择 FT 六字段或七字段布局。"));
    default:
        return fail(QStringLiteral("FT 字段布局枚举无效。"));
    }
    QByteArray newline;
    switch (options.lineEnding) {
    case LineEnding::Lf: newline = "\n"; break;
    case LineEnding::CrLf: newline = "\r\n"; break;
    case LineEnding::Unspecified:
        return fail(QStringLiteral("必须显式选择 LF 或 CRLF 换行。"));
    default:
        return fail(QStringLiteral("FT 换行枚举无效，仅支持 LF 或 CRLF。"));
    }
    for (const auto coordinate : {start.x(), start.y(), end.x(), end.y()}) {
        if (!std::isfinite(coordinate) || coordinate < -1000000 || coordinate > 1000000
            || std::trunc(coordinate) != coordinate) {
            return fail(QStringLiteral("走线端点须为 ±1000000 mil 内的有限整数，不允许隐式取整。"));
        }
    }
    if (start == end) return fail(QStringLiteral("走线起点和终点不能相同。"));
    if (width < 1 || width > 1000000) return fail(QStringLiteral("走线宽度须为 1 至 1000000 mil 的整数。"));
    if (layer != 1 && layer != 6) return fail(QStringLiteral("自由走线仅支持顶层 1 或底层 6。"));

    // 校验后转换整数，ASCII 十进制不受区域设置影响；无原始文本入口可注入新行。
    QByteArray bytes = "FT" + newline;
    for (const auto coordinate : {start.x(), start.y(), end.x(), end.y()}) {
        bytes += QByteArray::number(static_cast<int>(coordinate));
        bytes += ' ';
    }
    bytes += QByteArray::number(width) + ' ' + QByteArray::number(layer);
    if (options.extra) bytes += ' ' + QByteArray::number(*options.extra);
    bytes += newline;
    return {bytes, {}};
}

}
