#!/usr/bin/env python3
"""只读检查已核对版本的原文字形表；可输出静态推导的笔画，尚未完成原程序行为对照。"""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

MAXIMUM_BYTES = 16 * 1024 * 1024
KNOWN_EXECUTABLE_SHA256 = "abc56e2e8467e608c68a0ddf0b0705e8270c5c60f83f193fa991f10293ece968"
TABLE_FILE_OFFSET = 0x2563F
DIRECTION_X_FILE_OFFSET = 0x32FBC
DIRECTION_Y_FILE_OFFSET = 0x32FDC
RECORD_BYTES = 25
CHARACTER_COUNT = 127


class TextEvidenceError(ValueError):
    """输入或请求超出已核对的静态证据范围。"""


def parse_records(table: bytes) -> tuple:
    if len(table) != RECORD_BYTES * CHARACTER_COUNT:
        raise TextEvidenceError("字形表长度不等于 127 个固定槽位。")
    records = []
    for offset in range(0, len(table), RECORD_BYTES):
        record = table[offset:offset + RECORD_BYTES]
        count = record[0]
        if count >= RECORD_BYTES:
            raise TextEvidenceError("指令数量超出 25 字节字符槽位。")
        if any(record[count + 1:]):
            raise TextEvidenceError("字符槽位出现未解释的非零填充。")
        records.append(record[1:count + 1])
    return tuple(records)


def checked_word(value: int) -> int:
    # 原指令使用 16 位运算；研究工具拒绝溢出，不把宽整数结果误当成原行为。
    if not -32768 <= value <= 32767:
        raise TextEvidenceError("笔画运算超出有符号 16 位范围，尚不支持溢出行为对照。")
    return value


def decode_text(records: tuple, directions_x: tuple, directions_y: tuple,
                text: bytes, height: int = 120, orientation: int = 0) -> dict:
    """按已核对指令静态解释；不模拟线宽、裁剪、VGA 像素或 DRC。"""
    if len(records) != CHARACTER_COUNT or len(directions_x) != 16 or len(directions_y) != 16:
        raise TextEvidenceError("字符或方向表尺寸无效。")
    if not 1 <= height <= 32767:
        raise TextEvidenceError("文字高度必须为 1 到 32767 的整数。")
    if orientation < 0 or (orientation & ~0x33) or (orientation & 0xf) > 3:
        raise TextEvidenceError("仅解释四向旋转及 0x10、0x20 镜像位。")
    if len(text) > 80:
        raise TextEvidenceError("仅解释最多 80 字节的原程序短字符串。")
    if any((character & 0x7f) == 0 for character in text):
        raise TextEvidenceError("字符低 7 位为零会索引表前内存，拒绝推导。")
    scale = height // 12
    x = y = 0
    segments = []
    characters = []
    for character in text:
        code = character & 0x7f
        commands = records[code - 1]
        if len(commands) >= RECORD_BYTES:
            raise TextEvidenceError("字符指令超出已验证槽位。")
        pen_down = True
        start = [x, y]
        first_segment = len(segments)
        for command in commands:
            if command < 12:
                if command == 1:
                    pen_down = True
                elif command == 2:
                    pen_down = False
                continue
            direction, distance = command & 0xf, command >> 4
            dx = checked_word(checked_word(directions_x[direction] * scale) * distance)
            dy = checked_word(checked_word(directions_y[direction] * scale) * distance)
            rotation = orientation & 0xf
            if rotation == 1:
                dx, dy = checked_word(-dy), dx
            elif rotation == 2:
                dx, dy = checked_word(-dx), checked_word(-dy)
            elif rotation == 3:
                dx, dy = dy, checked_word(-dx)
            if orientation & 0x10:
                dx = checked_word(-dx)
            if orientation & 0x20:
                dy = checked_word(-dy)
            next_x, next_y = checked_word(x + dx), checked_word(y + dy)
            if pen_down:
                segments.append([x, y, next_x, next_y])
            x, y = next_x, next_y
        characters.append({"code_7bit": code, "start": start, "end": [x, y],
                           "segment_count": len(segments) - first_segment})
    return {"height": height, "integer_scale": scale, "orientation": orientation,
            "origin": [0, 0], "end": [x, y], "characters": characters,
            "segment_count": len(segments), "segments": segments}


def inspect_text(executable: bytes, text=None,
                 height: int = 120, orientation: int = 0) -> dict:
    if len(executable) > MAXIMUM_BYTES:
        raise TextEvidenceError("输入超过 16 MiB 分析上限。")
    digest = hashlib.sha256(executable).hexdigest()
    if digest != KNOWN_EXECUTABLE_SHA256:
        raise TextEvidenceError("EXE 摘要不属于已核对版本，拒绝套用固定表偏移。")
    table = executable[TABLE_FILE_OFFSET:TABLE_FILE_OFFSET + RECORD_BYTES * CHARACTER_COUNT]
    records = parse_records(table)
    if len(executable) < DIRECTION_Y_FILE_OFFSET + 32:
        raise TextEvidenceError("方向表超出 EXE 范围。")
    directions_x = struct.unpack_from("<16h", executable, DIRECTION_X_FILE_OFFSET)
    directions_y = struct.unpack_from("<16h", executable, DIRECTION_Y_FILE_OFFSET)
    decoded = decode_text(records, directions_x, directions_y,
                          text if text is not None else b"", height, orientation)
    report = {"schema_version": 1, "evidence": "static_instruction_derivation",
              "runtime_verified": False, "executable_sha256": digest,
              "table_file_offset": TABLE_FILE_OFFSET, "table_bytes": len(table),
              "table_sha256": hashlib.sha256(table).hexdigest(),
              "record_bytes": RECORD_BYTES, "character_count": len(records),
              "nonempty_records": sum(bool(record) for record in records),
              "maximum_commands": max(map(len, records)),
              "direction_x_file_offset": DIRECTION_X_FILE_OFFSET,
              "direction_y_file_offset": DIRECTION_Y_FILE_OFFSET,
              "limitations": ["仅适用摘要匹配的本地 PT.EXE；不含内置字体或原程序代码。",
                              "笔画来自静态指令推导，尚未完成原程序单字符独立行为对照。",
                              "不模拟 16 位溢出、裁剪、线宽、像素、低缩放替代显示或完整 DRC。",
                              "未将字形接入 Qt 渲染或铜层分析；铜层文字覆盖继续保持未知。"]}
    if text is not None:
        report["decoded"] = decoded
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path, help="只读的已核对版本 PT.EXE")
    parser.add_argument("--text", help="可选：按 Latin-1 字节解释，输出静态推导笔画供本地核对")
    parser.add_argument("--height", type=int, default=120, help="原坐标单位文字高度，默认 120")
    parser.add_argument("--orientation", type=lambda value: int(value, 0), default=0,
                        help="旋转与镜像位，支持十进制或 0x 前缀")
    args = parser.parse_args(argv)
    try:
        text = args.text.encode("latin-1") if args.text is not None else None
        with args.executable.open("rb") as stream:
            executable = stream.read(MAXIMUM_BYTES + 1)
        report = inspect_text(executable, text, args.height, args.orientation)
    except (OSError, TextEvidenceError, UnicodeError) as error:
        message = "文字必须能编码为 Latin-1 字节。" if isinstance(error, UnicodeError) else str(error)
        print(json.dumps({"error": message}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
