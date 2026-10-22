"""文字静态解释器的独立合成测试；不包含原软件字节或字形。"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "inspect_legacy_text.py"
SPEC = importlib.util.spec_from_file_location("inspect_legacy_text", MODULE_PATH)
inspector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspector)


def fixture():
    # 自行构造非对称方向和小指令串，避免用恢复结果为自身作证。
    records = [b""] * 127
    records[64] = bytes([0x10, 2, 0x21, 1, 0x10, 2, 0x11])
    records[31] = bytes([2, 0x30])
    return tuple(records), (2, -1) + (0,) * 14, (1, 2) + (0,) * 14


def executable_fixture():
    records, directions_x, directions_y = fixture()
    data = bytearray(inspector.DIRECTION_Y_FILE_OFFSET + 32)
    for index, commands in enumerate(records):
        start = inspector.TABLE_FILE_OFFSET + index * 25
        data[start] = len(commands)
        data[start + 1:start + 1 + len(commands)] = commands
    struct.pack_into("<16h", data, inspector.DIRECTION_X_FILE_OFFSET, *directions_x)
    struct.pack_into("<16h", data, inspector.DIRECTION_Y_FILE_OFFSET, *directions_y)
    return bytes(data)


class LegacyTextTests(unittest.TestCase):
    def decode(self, text=b"A", height=12, orientation=0):
        return inspector.decode_text(*fixture(), text, height, orientation)

    def test_pen_moves_and_final_advance(self):
        report = self.decode()
        self.assertEqual(report["segments"], [[0, 0, 2, 1], [0, 5, 2, 6]])
        self.assertEqual(report["end"], [1, 8])
        self.assertEqual(report["segment_count"], 2)

    def test_pen_resets_per_character_and_position_carries(self):
        report = self.decode(b"AA")
        self.assertEqual(report["segments"][2:], [[1, 8, 3, 9], [1, 13, 3, 14]])
        self.assertEqual(report["end"], [2, 16])
        self.assertEqual(report["characters"][1]["start"], [1, 8])

    def test_space_moves_without_drawing(self):
        report = self.decode(b"A A")
        self.assertEqual(report["segment_count"], 4)
        self.assertEqual(report["characters"][1]["segment_count"], 0)
        self.assertEqual(report["end"], [8, 19])

    def test_height_quantizes_before_multiplication(self):
        self.assertEqual(self.decode(height=23)["segments"], self.decode(height=12)["segments"])
        self.assertEqual(self.decode(height=24)["end"], [2, 16])
        self.assertEqual(self.decode(height=11)["end"], [0, 0])

    def test_rotations_and_mirrors_follow_rotation(self):
        expected = {0: [1, 8], 1: [-8, 1], 2: [-1, -8], 3: [8, -1],
                    0x10: [-1, 8], 0x20: [1, -8], 0x11: [8, 1],
                    0x21: [-8, -1], 0x33: [-8, 1]}
        for flags, end in expected.items():
            with self.subTest(flags=flags):
                self.assertEqual(self.decode(orientation=flags)["end"], end)

    def test_high_bit_alias_and_zero_index_rejection(self):
        self.assertEqual(self.decode(b"\xc1"), self.decode(b"A"))
        for text in (b"\0", b"\x80", b"A\0"):
            with self.assertRaises(inspector.TextEvidenceError):
                self.decode(text)

    def test_empty_and_unpopulated_characters(self):
        self.assertEqual(self.decode(b"")["segments"], [])
        self.assertEqual(self.decode(b"B")["end"], [0, 0])

    def test_short_string_limit(self):
        self.assertEqual(len(self.decode(b"A" * 80)["characters"]), 80)
        with self.assertRaises(inspector.TextEvidenceError):
            self.decode(b"A" * 81)

    def test_invalid_dimensions_and_orientation(self):
        for height in (0, -1, 32768):
            with self.assertRaises(inspector.TextEvidenceError):
                self.decode(height=height)
        for flags in (-1, 4, 0x14, 0x40):
            with self.assertRaises(inspector.TextEvidenceError):
                self.decode(orientation=flags)
        with self.assertRaises(inspector.TextEvidenceError):
            inspector.decode_text((), (), (), b"A")

    def test_rejects_coordinate_and_product_overflow(self):
        for text, height in ((b"A" * 80, 32000), (b" " * 80, 32000)):
            with self.assertRaises(inspector.TextEvidenceError):
                self.decode(text, height)
        records, dx, dy = fixture()
        records = list(records)
        records[64] = bytes([0xf0])
        with self.assertRaises(inspector.TextEvidenceError):
            inspector.decode_text(tuple(records), dx, dy, b"A", 32000)

    def test_other_control_commands_do_not_move_or_draw(self):
        records, dx, dy = fixture()
        records = list(records)
        records[64] = bytes([0, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        report = inspector.decode_text(tuple(records), dx, dy, b"A")
        self.assertEqual(report["end"], [0, 0])
        self.assertEqual(report["segments"], [])

    def test_slot_boundaries_and_padding(self):
        table = bytearray(127 * 25)
        table[0] = 24
        table[1:25] = bytes([1] * 24)
        self.assertEqual(len(inspector.parse_records(table)[0]), 24)
        for invalid in (table[:-1], table + b"\0", bytes([25]) + table[1:]):
            with self.assertRaises(inspector.TextEvidenceError):
                inspector.parse_records(invalid)
        table[25 + 24] = 1
        with self.assertRaises(inspector.TextEvidenceError):
            inspector.parse_records(table)

    def test_exact_digest_gate_and_summary(self):
        data = executable_fixture()
        with self.assertRaises(inspector.TextEvidenceError):
            inspector.inspect_text(data)
        with patch.object(inspector, "KNOWN_EXECUTABLE_SHA256", hashlib.sha256(data).hexdigest()):
            report = inspector.inspect_text(data)
            self.assertFalse(report["runtime_verified"])
            self.assertEqual(report["nonempty_records"], 2)
            self.assertNotIn("decoded", report)
            self.assertEqual(inspector.inspect_text(data, b"A", 12)["decoded"], self.decode())
            with self.assertRaises(inspector.TextEvidenceError):
                inspector.inspect_text(data + b"\0")
        with self.assertRaises(inspector.TextEvidenceError):
            inspector.inspect_text(b"\0" * (inspector.MAXIMUM_BYTES + 1))

    def test_cli_success_error_and_input_unchanged(self):
        data = executable_fixture()
        digest = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "合成.EXE"
            path.write_bytes(data)
            with patch.object(inspector, "KNOWN_EXECUTABLE_SHA256", digest):
                for arguments, expected in (([str(path), "--text", "A", "--height", "12", "--orientation", "0x11"], 0),
                                            ([str(path), "--text", "汉字"], 1),
                                            ([str(path), "--text", "A", "--orientation", "4"], 1),
                                            ([str(path), "--orientation", "4"], 1),
                                            ([str(path), "--height", "0"], 1),
                                            ([str(path) + ".missing"], 1)):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(inspector.main(arguments), expected)
                    report = json.loads(output.getvalue())
                    if expected:
                        self.assertIn("error", report)
                    else:
                        self.assertEqual(report["decoded"]["end"], [8, 1])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
