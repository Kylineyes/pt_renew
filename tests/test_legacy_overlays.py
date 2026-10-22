"""覆盖布局工具的合成边界测试；不包含原软件字节或板图。"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "inspect_legacy_overlays.py"
SPEC = importlib.util.spec_from_file_location("inspect_legacy_overlays", MODULE_PATH)
inspector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspector)


def fixture():
    executable = bytearray(256)
    struct.pack_into("<14H", executable, 0, 0x5a4d, 256, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 28, 0)
    overlay = bytearray(b"TPOV" + b"\x00" * 40)
    # 两个描述符分别在段1和5；第一个代码块中的远调用引用第二个覆盖入口。
    for position, file_offset, previous in [(48, 4, 0), (112, 26, 1)]:
        executable[position:position + 4] = inspector.DESCRIPTOR_SIGNATURE
        struct.pack_into("<IHHHH", executable, position + 4, file_offset, 18, 4 if position == 48 else 0, 2, previous)
        executable[position + 32:position + 42] = b"\xcd\x3f\x00\x00\x00\xcd\x3f\xff\xff\x00"
    overlay[4:14] = b"\x9a\x20\x00\x05\x00\x9a\x00\x00\x08\x00"
    struct.pack_into("<HH", overlay, 22, 3, 8)
    return executable, overlay


class OverlayTests(unittest.TestCase):
    def assert_bad(self, executable, overlay):
        with self.assertRaises(inspector.LayoutError):
            inspector.inspect_overlays(executable, overlay)

    def test_maps_blocks_stubs_fixups_and_calls(self):
        executable, overlay = fixture()
        before = (bytes(executable), bytes(overlay))
        report = inspector.inspect_overlays(executable, overlay, "full")
        self.assertEqual(report["segment_count"], 2)
        self.assertEqual(report["stub_count"], 4)
        self.assertEqual(report["active_entry_count"], 2)
        self.assertEqual(report["fixup_count"], 2)
        self.assertEqual(report["code_bytes"], 36)
        self.assertEqual(report["resolved_overlay_call_candidates"], 1)
        self.assertEqual(report["resident_call_candidates"], 1)
        first = report["segments"][0]
        self.assertIsNone(first["stubs"][1]["target_file_offset"])
        self.assertEqual(first["direct_far_call_candidates"][0]["target_file_offset"], 26)
        self.assertEqual(report["executable_sha256"], hashlib.sha256(executable).hexdigest())
        self.assertEqual((bytes(executable), bytes(overlay)), before)

    def test_summary_omits_large_mappings(self):
        report = inspector.inspect_overlays(*fixture())
        self.assertNotIn("stubs", report["segments"][0])
        self.assertNotIn("fixups", report["segments"][0])
        self.assertNotIn("direct_far_call_candidates", report["segments"][0])
        self.assertEqual(report["segments"][0]["direct_far_call_candidate_count"], 2)

    def test_mz_headers_and_lengths_are_checked(self):
        executable, overlay = fixture()
        for invalid in [b"", b"MZ", b"NO" + executable[2:], executable[:-1], executable + b"X"]:
            with self.subTest(length=len(invalid)):
                self.assert_bad(invalid, overlay)
        struct.pack_into("<H", executable, 2, 512)
        self.assert_bad(executable, overlay)

    def test_mz_relocation_boundaries(self):
        executable, overlay = fixture()
        struct.pack_into("<H", executable, 6, 1)
        struct.pack_into("<HH", executable, 28, 0, 1)
        self.assertEqual(inspector.inspect_overlays(executable, overlay)["mz_relocation_count"], 1)
        struct.pack_into("<HH", executable, 28, 0xffff, 0xffff)
        self.assert_bad(executable, overlay)
        struct.pack_into("<H", executable, 24, 31)
        self.assert_bad(executable, overlay)

    def test_tpov_header_and_trailing_data(self):
        executable, overlay = fixture()
        self.assert_bad(executable, b"FAIL" + overlay[4:])
        self.assert_bad(executable, overlay + b"X")
        self.assert_bad(executable, overlay[:-1])

    def test_rejects_missing_or_truncated_descriptors(self):
        executable, overlay = fixture()
        executable[48:52] = b"xxxx"
        executable[112:116] = b"xxxx"
        self.assert_bad(executable, overlay)
        executable[240:244] = inspector.DESCRIPTOR_SIGNATURE
        self.assert_bad(executable, overlay)

    def test_rejects_unknown_reserved_values(self):
        executable, overlay = fixture()
        executable[64] = 1
        self.assert_bad(executable, overlay)

    def test_rejects_invalid_code_fixup_and_entry_counts(self):
        for field, value in [(56, 0), (58, 3), (60, 0), (60, 500)]:
            executable, overlay = fixture()
            struct.pack_into("<H", executable, field, value)
            with self.subTest(field=field, value=value):
                self.assert_bad(executable, overlay)

    def test_rejects_malformed_stub_and_target(self):
        for position, value in [(80, 0), (84, 1)]:
            executable, overlay = fixture()
            executable[position] = value
            self.assert_bad(executable, overlay)
        executable, overlay = fixture()
        struct.pack_into("<H", executable, 82, 18)
        self.assert_bad(executable, overlay)

    def test_rejects_noncontiguous_blocks_and_broken_chain(self):
        executable, overlay = fixture()
        struct.pack_into("<I", executable, 116, 25)
        self.assert_bad(executable, overlay)
        executable, overlay = fixture()
        struct.pack_into("<H", executable, 126, 9)
        self.assert_bad(executable, overlay)

    def test_rejects_overlapping_descriptor_tables(self):
        executable, overlay = fixture()
        executable[112:154] = b"\x00" * 42
        executable[80:122] = b"\xcd\x3f\x00\x00\x00" * 8 + b"\x00\x00"
        struct.pack_into("<H", executable, 60, 8)
        # 入口字节中人为放入新的描述符；不能把重叠结构报告为有效布局。
        executable[96:100] = inspector.DESCRIPTOR_SIGNATURE
        self.assert_bad(executable, overlay)

    def test_rejects_out_of_range_and_duplicate_fixups(self):
        for offsets in [(3, 17), (3, 3)]:
            executable, overlay = fixture()
            struct.pack_into("<HH", overlay, 22, *offsets)
            self.assert_bad(executable, overlay)

    def test_unknown_and_disabled_calls_remain_explicit(self):
        executable, overlay = fixture()
        struct.pack_into("<H", overlay, 5, 37)
        struct.pack_into("<H", overlay, 12, 0xffff)
        report = inspector.inspect_overlays(executable, overlay, "full")
        self.assertEqual(report["unresolved_call_candidates"], 2)
        self.assertEqual(report["segments"][0]["direct_far_call_candidates"][0]["destination"], "disabled_overlay_entry")
        struct.pack_into("<H", overlay, 5, 33)
        report = inspector.inspect_overlays(executable, overlay, "full")
        self.assertEqual(report["segments"][0]["direct_far_call_candidates"][0]["destination"], "unresolved")

    def test_unrelocated_bytes_do_not_become_call_candidates(self):
        executable, overlay = fixture()
        overlay[4] = 0
        report = inspector.inspect_overlays(executable, overlay)
        self.assertEqual(report["resolved_overlay_call_candidates"], 0)
        self.assertEqual(report["segments"][0]["direct_far_call_candidate_count"], 1)

    def test_size_and_detail_limits(self):
        executable, overlay = fixture()
        with self.assertRaises(inspector.LayoutError):
            inspector.inspect_overlays(executable, overlay, "invalid")
        self.assert_bad(executable, b"X" * (inspector.MAXIMUM_BYTES + 1))

    def test_cli_reads_files_and_returns_json_errors(self):
        executable, overlay = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            exe_path = Path(temporary) / "示例.EXE"
            ovr_path = Path(temporary) / "示例.OVR"
            exe_path.write_bytes(executable)
            ovr_path.write_bytes(overlay)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(inspector.main([str(exe_path), str(ovr_path)]), 0)
            self.assertEqual(json.loads(output.getvalue())["segment_count"], 2)
            self.assertEqual(exe_path.read_bytes(), executable)
            self.assertEqual(ovr_path.read_bytes(), overlay)
            ovr_path.unlink()
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(inspector.main([str(exe_path), str(ovr_path)]), 1)
            self.assertIn("error", json.loads(output.getvalue()))


if __name__ == "__main__":
    unittest.main()
