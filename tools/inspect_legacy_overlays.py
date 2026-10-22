#!/usr/bin/env python3
"""只读核对本项目已验证的 DOS MZ / TPOV 覆盖布局，不执行或修补目标程序。"""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

MAXIMUM_BYTES = 16 * 1024 * 1024
DESCRIPTOR_SIGNATURE = b"\xcd\x3f\x00\x00"


class LayoutError(ValueError):
    """输入不属于当前已验证布局，或结构不完整。"""


def inspect_overlays(executable: bytes, overlay: bytes, detail: str = "summary") -> dict:
    if detail not in ("summary", "full"):
        raise LayoutError("报告详细程度必须为 summary 或 full。")
    if len(executable) > MAXIMUM_BYTES or len(overlay) > MAXIMUM_BYTES:
        raise LayoutError("输入超过 16 MiB 分析上限。")
    if len(executable) < 28 or executable[:2] != b"MZ":
        raise LayoutError("主程序缺少完整 MZ 文件头。")
    header = struct.unpack_from("<14H", executable)
    last_page, pages, relocation_count, paragraphs = header[1:5]
    if not pages or last_page > 511:
        raise LayoutError("MZ 页数字段无效。")
    declared_size = (pages - 1) * 512 + (last_page or 512)
    image_start = paragraphs * 16
    if declared_size != len(executable) or not 28 <= image_start < declared_size:
        raise LayoutError("仅支持无附加尾部数据、头部与映像范围完整的 MZ。")
    relocation_start = header[12]
    if relocation_count and (relocation_start < 28 or relocation_start + relocation_count * 4 > image_start):
        raise LayoutError("MZ 重定位表超出文件头。")
    for index in range(relocation_count):
        offset, segment = struct.unpack_from("<HH", executable, relocation_start + index * 4)
        if image_start + segment * 16 + offset + 2 > declared_size:
            raise LayoutError("MZ 重定位目标超出映像。")
    if overlay[:4] != b"TPOV":
        raise LayoutError("覆盖文件缺少 TPOV 标识。")

    segments = []
    stub_table_end = image_start
    for position in range(image_start, declared_size - 3, 16):
        # 入口目标为零时也会以 CD 3F 00 00 开头；已验证入口表内的字节不能再当描述符。
        if position < stub_table_end:
            continue
        if executable[position:position + 4] != DESCRIPTOR_SIGNATURE:
            continue
        if position + 32 > declared_size:
            raise LayoutError("覆盖描述符被截断。")
        file_offset, code_size, fixup_bytes, count, previous = struct.unpack_from("<IHHHH", executable, position + 4)
        if any(executable[position + 16:position + 32]):
            raise LayoutError("覆盖描述符含未解释的非零保留字段。")
        if not code_size or fixup_bytes % 2 or not count:
            raise LayoutError("覆盖代码长度、重定位字节数或入口数无效。")
        if file_offset < 4 or file_offset + code_size + fixup_bytes > len(overlay):
            raise LayoutError("覆盖代码或重定位表越界。")
        end = position + 32 + count * 5
        if end > declared_size:
            raise LayoutError("覆盖入口表超出 MZ 映像。")
        stubs = []
        for index in range(count):
            stub_position = position + 32 + index * 5
            if executable[stub_position:stub_position + 2] != b"\xcd\x3f" or executable[stub_position + 4] != 0:
                raise LayoutError("覆盖入口不是已验证的五字节 INT 3F 布局。")
            target = struct.unpack_from("<H", executable, stub_position + 2)[0]
            disabled = target == 0xffff
            if not disabled and target >= code_size:
                raise LayoutError("覆盖入口目标超出所属代码块。")
            stubs.append({"slot": index, "stub_file_offset": stub_position,
                          "stub_segment_offset": 32 + index * 5,
                          "disabled": disabled, "target_offset": None if disabled else target,
                          "target_file_offset": None if disabled else file_offset + target})
        fixups = list(struct.unpack_from("<" + "H" * (fixup_bytes // 2), overlay, file_offset + code_size))
        if any(offset + 2 > code_size for offset in fixups):
            raise LayoutError("覆盖重定位目标超出所属代码块。")
        if len(set(fixups)) != len(fixups):
            raise LayoutError("覆盖重定位表含重复位置。")
        stub_table_end = end
        segments.append({"descriptor_file_offset": position, "stub_segment": (position - image_start) // 16,
                         "previous_stub_segment": previous, "overlay_file_offset": file_offset,
                         "code_bytes": code_size, "fixup_bytes": fixup_bytes, "stub_count": count,
                         "active_entry_count": sum(not stub["disabled"] for stub in stubs),
                         "fixup_count": len(fixups), "stubs": stubs, "fixups": fixups})
    if not segments:
        raise LayoutError("未找到已验证的覆盖描述符。")
    expected = 4
    previous = 0
    descriptor_end = image_start
    for segment in segments:
        if segment["descriptor_file_offset"] < descriptor_end:
            raise LayoutError("覆盖描述符或入口表互相重叠。")
        descriptor_end = segment["descriptor_file_offset"] + 32 + segment["stub_count"] * 5
        if segment["previous_stub_segment"] != previous:
            raise LayoutError("覆盖描述符前驱链不连续。")
        previous = segment["stub_segment"]
        if segment["overlay_file_offset"] != expected:
            raise LayoutError("覆盖块存在空洞、重叠或顺序差异。")
        expected += segment["code_bytes"] + segment["fixup_bytes"]
    if expected != len(overlay):
        raise LayoutError("覆盖文件含未解释的尾部数据。")

    by_segment = {segment["stub_segment"]: segment for segment in segments}
    resolved_calls = 0
    resident_calls = 0
    unresolved_calls = 0
    for segment in segments:
        calls = []
        start = segment["overlay_file_offset"]
        for offset in segment["fixups"]:
            # 仅将具有段重定位记录的 9A 立即数形式列为候选；未证明该位置可达。
            if offset < 3 or overlay[start + offset - 3] != 0x9a:
                continue
            target_offset, target_segment = struct.unpack_from("<HH", overlay, start + offset - 2)
            call = {"instruction_file_offset": start + offset - 3,
                    "target_segment": target_segment, "target_offset": target_offset}
            destination = by_segment.get(target_segment)
            if destination:
                slot, remainder = divmod(target_offset - 32, 5)
                if target_offset >= 32 and remainder == 0 and slot < destination["stub_count"]:
                    stub = destination["stubs"][slot]
                    call.update({"destination": "disabled_overlay_entry" if stub["disabled"] else "overlay_entry",
                                 "descriptor_file_offset": destination["descriptor_file_offset"],
                                 "target_file_offset": stub["target_file_offset"]})
                    if not stub["disabled"]:
                        resolved_calls += 1
                    else:
                        unresolved_calls += 1
                else:
                    call["destination"] = "unresolved"
                    unresolved_calls += 1
            else:
                target_file = image_start + target_segment * 16 + target_offset
                if image_start <= target_file < declared_size:
                    call.update({"destination": "resident_candidate", "target_file_offset": target_file})
                    resident_calls += 1
                else:
                    call["destination"] = "unresolved"
                    unresolved_calls += 1
            calls.append(call)
        segment["direct_far_call_candidate_count"] = len(calls)
        if detail == "full":
            segment["direct_far_call_candidates"] = calls
        else:
            segment.pop("stubs")
            segment.pop("fixups")
    return {"schema_version": 1, "layout": "mz_tpov_observed", "detail": detail,
            "executable_sha256": hashlib.sha256(executable).hexdigest(),
            "overlay_sha256": hashlib.sha256(overlay).hexdigest(),
            "executable_bytes": len(executable), "overlay_bytes": len(overlay),
            "mz_image_file_offset": image_start, "mz_relocation_count": relocation_count,
            "segment_count": len(segments), "stub_count": sum(s["stub_count"] for s in segments),
            "active_entry_count": sum(s["active_entry_count"] for s in segments),
            "code_bytes": sum(s["code_bytes"] for s in segments),
            "fixup_count": sum(s["fixup_count"] for s in segments),
            "resolved_overlay_call_candidates": resolved_calls,
            "resident_call_candidates": resident_calls, "unresolved_call_candidates": unresolved_calls,
            "segments": segments,
            "limitations": ["仅支持本项目已验证的 MZ/TPOV 描述符、前驱链和连续覆盖布局。",
                            "入口槽位数量不是函数总数；FFFF 槽位保留为禁用入口。",
                            "9A 与段重定位的匹配仅是直接远调用候选，未证明指令边界、可达性或运行行为。",
                            "未执行目标、未应用重定位、未恢复字形、未输出或重新分发原软件代码。"]}


def read_bounded(path: Path) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(MAXIMUM_BYTES + 1)
    if len(data) > MAXIMUM_BYTES:
        raise LayoutError("输入超过 16 MiB 分析上限。")
    return data


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path, help="只读 DOS MZ 主程序路径")
    parser.add_argument("overlay", type=Path, help="只读 TPOV 覆盖模块路径")
    parser.add_argument("--detail", choices=("summary", "full"), default="summary", help="默认输出摘要；full 包含入口和重定位映射")
    args = parser.parse_args(argv)
    try:
        result = inspect_overlays(read_bounded(args.executable), read_bounded(args.overlay), args.detail)
    except (OSError, LayoutError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
