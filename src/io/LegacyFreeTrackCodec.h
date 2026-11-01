#pragma once

#include <QByteArray>
#include <QPointF>
#include <QString>
#include <optional>

namespace pt {

// 仅合成调用方明确指定的 FT 字节，不代表原软件默认编码已核定。
class LegacyFreeTrackCodec final {
public:
    enum class FieldLayout { Unspecified, SixFields, SevenFields };
    enum class LineEnding { Unspecified, Lf, CrLf };
    struct Options {
        FieldLayout fields = FieldLayout::Unspecified;
        LineEnding lineEnding = LineEnding::Unspecified;
        // 七字段时必须显式提供；仅保留整数，不解释其电气语义。
        std::optional<int> extra;
    };
    struct Result {
        QByteArray bytes;
        QString error;
        bool succeeded() const { return error.isEmpty() && !bytes.isEmpty(); }
    };

    // 不取整、不捕捉网格，不接收已有 Track、来源身份或文件路径。
    static Result encode(QPointF start, QPointF end, int width, int layer, const Options& options);
};

}
