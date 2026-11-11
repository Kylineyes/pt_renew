#!/usr/bin/env python3
"""只读盘点已观测 PCB 4 LIBRARY 目录；不恢复失效槽，不证明原软件兼容。"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

RECORD_BYTES = 16
SLOT_COUNT = 200
DATA_RECORD = 401
MAXIMUM_BYTES = 8 * 1024 * 1024
HEADER = b"\0\0\x0dPCB 4 LIBRARY"


def inspect_directory(data: bytes) -> dict:
    """分类依目录指针；空洞仅是完整结构遍历后的未引用区间。"""
    if not DATA_RECORD * RECORD_BYTES <= len(data) <= MAXIMUM_BYTES or len(data) % RECORD_BYTES:
        raise ValueError("库长度须为 16 的倍数，至少 6416 字节且不超过 8 MiB。")
    if data[:RECORD_BYTES] != HEADER:
        raise ValueError("仅支持已观测的 PCB 4 LIBRARY 头；不猜测其他版本。")
    rows = []
    by_start = defaultdict(list)
    errors = []
    for slot in range(SLOT_COUNT):
        offset = RECORD_BYTES + slot * 32
        raw = data[offset:offset + 32]
        count, start = struct.unpack_from("<HH", raw, 18)
        length = raw[2]
        # 保留可见字节的无损表示；不猜代码页或把字符串尾部当名称。
        name_bytes = raw[3:3 + min(length, 15)]
        if start != 0xffff:
            state = "pointer_present"
        elif count == 0xffff:
            state = "unallocated_count_ffff"
        elif 0 < length <= 15:
            state = "unallocated_retained_name"
        elif length == 0:
            state = "unallocated_empty_name"
        else:
            state = "unallocated_invalid_name_length"
        row = {"slot0": slot, "byte_offset": offset, "state": state,
               "name_length": length, "name_bytes_hex": name_bytes.hex(),
               "primitive_count": count, "first_record": start,
               "nonzero_reserved_offsets": [i for i in (*range(2), *range(22, 32)) if raw[i]]}
        if start != 0xffff:
            by_start[start].append(slot)
            if not 1 <= length <= 15 or any(ch < 32 or ch == 127 for ch in name_bytes):
                errors.append({"slot0": slot, "reason": "有指针条目的名称长度或控制字符无效。"})
            if start < DATA_RECORD or start > len(data) // RECORD_BYTES or (count and start == len(data) // RECORD_BYTES):
                errors.append({"slot0": slot, "reason": "目录指针超出数据区。"})
        rows.append(row)
    duplicates = [{"first_record": start, "slots0": slots}
                  for start, slots in sorted(by_start.items()) if len(slots) > 1]
    if duplicates:
        errors.append({"reason": "存在重复指针，不能据此认定为合法别名。"})
    # 这里只核定记录边界及字符串续记录，不检查图元几何、图层或电气字段。
    ranges = []
    for index, start in enumerate(sorted(by_start)):
        limit = sorted(by_start)[index + 1] if index + 1 < len(by_start) else len(data) // RECORD_BYTES
        for slot in by_start[start]:
            row = rows[slot]
            current = start
            try:
                if start < DATA_RECORD or start > limit:
                    raise ValueError("指针或上界无效。")
                for _ in range(row["primitive_count"]):
                    if current >= limit:
                        raise ValueError("声明图元数越过下一指针或文件尾。")
                    kind = data[current * RECORD_BYTES + 1]
                    current += 1
                    if kind in (3, 6):
                        if current >= limit:
                            raise ValueError("缺少字符串续记录。")
                        following = data[current * RECORD_BYTES:(current + 1) * RECORD_BYTES]
                        if following[0] or following[1] != (4 if kind == 3 else 7) or following[2] > 13:
                            raise ValueError("字符串续记录类型或长度无效。")
                        current += 1
                    elif kind not in (1, 2, 5, 8):
                        raise ValueError("遇到未支持的记录类型，停止结构盘点。")
                row["end_record"] = current
                ranges.append((start, current))
            except (IndexError, ValueError) as error:
                errors.append({"slot0": slot, "reason": str(error)})
    gaps = None
    if not errors:
        gaps = []
        end = DATA_RECORD
        for start, stop in sorted(ranges):
            if start > end:
                gaps.append({"first_record": end, "end_record": start})
            end = max(end, stop)
        if end < len(data) // RECORD_BYTES:
            gaps.append({"first_record": end, "end_record": len(data) // RECORD_BYTES})
    return {"schema_version": 1, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "state_counts": dict(Counter(row["state"] for row in rows)),
            "nonzero_reserved_slots0": [r["slot0"] for r in rows if r["nonzero_reserved_offsets"]],
            "duplicate_pointers": duplicates, "structural_errors": errors,
            "unreferenced_record_ranges": gaps, "slots": rows,
            "limitations": ["目录类别是静态字节状态，不追认删除历史或恢复失效条目。",
                            "未引用区间没有名称归属，不是可恢复封装列表。",
                            "记录遍历不验证几何、电气、全部标志或原软件行为；不是预览能力门。"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("libraries", type=Path, nargs="+", help="只读原库路径")
    parser.add_argument("--slots", action="store_true", help="包含目录槽元数据；不输出图元原字节")
    args = parser.parse_args(argv)
    reports = []
    failed = False
    for path in args.libraries:
        try:
            with path.open("rb") as stream:
                data = stream.read(MAXIMUM_BYTES + 1)
            report = inspect_directory(data)
            report["path"] = str(path)
            failed |= bool(report["structural_errors"])
            if not args.slots:
                report.pop("slots")
            reports.append(report)
        except (OSError, ValueError) as error:
            failed = True
            reports.append({"path": str(path), "error": str(error)})
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return int(failed)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
