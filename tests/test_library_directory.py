"""使用自主合成库验证目录分类、续记录边界及不恢复残留的约束。"""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from inspect_library_directory import HEADER, inspect_directory, main


def library(records=0):
    data = bytearray(6416 + records * 16)
    data[:16] = HEADER
    for slot in range(200):
        struct.pack_into("<HH", data, 16 + slot * 32 + 18, 0xffff, 0xffff)
    return data


def row(data, slot, name, count, start):
    offset = 16 + 32 * slot
    data[offset + 2] = len(name)
    data[offset + 3:offset + 3 + len(name)] = name
    struct.pack_into("<HH", data, offset + 18, count, start)


class DirectoryTests(unittest.TestCase):
    def test_marker_retained_and_empty_are_separate(self):
        data = library()
        row(data, 0, b"********", 0xffff, 0xffff)
        row(data, 1, b"OLD", 5, 0xffff)
        row(data, 2, b"", 0, 0xffff)
        report = inspect_directory(data)
        self.assertEqual(report["state_counts"], {"unallocated_count_ffff": 198,
                         "unallocated_retained_name": 1, "unallocated_empty_name": 1})
        self.assertNotIn("end_record", report["slots"][1])
        self.assertEqual(report["structural_errors"], [])

    def test_unsorted_directory_and_continuations_preserve_gap(self):
        data = library(6)
        row(data, 0, b"LATER", 1, 405)
        row(data, 1, b"FIRST", 1, 401)
        data[401 * 16 + 1] = 3
        data[402 * 16 + 1] = 4
        data[405 * 16 + 1] = 5
        report = inspect_directory(data)
        self.assertEqual(report["slots"][1]["end_record"], 403)
        self.assertEqual(report["unreferenced_record_ranges"], [
            {"first_record": 403, "end_record": 405}, {"first_record": 406, "end_record": 407}])
        self.assertEqual(report["structural_errors"], [])

    def test_duplicate_pointer_is_unknown_not_an_alias(self):
        data = library(1)
        data[401 * 16 + 1] = 5
        for slot in (0, 1):
            row(data, slot, b"A", 1, 401)
        report = inspect_directory(data)
        self.assertEqual(report["duplicate_pointers"], [{"first_record": 401, "slots0": [0, 1]}])
        self.assertIsNone(report["unreferenced_record_ranges"])
        self.assertTrue(report["structural_errors"])

    def test_broken_boundary_does_not_report_proven_unreferenced_data(self):
        for pointer in (400, 402, 60000):
            with self.subTest(pointer=pointer):
                data = library(1)
                row(data, 0, b"BAD", 1, pointer)
                report = inspect_directory(data)
                self.assertTrue(report["structural_errors"])
                self.assertIsNone(report["unreferenced_record_ranges"])
        data = library(1)
        row(data, 0, b"BAD", 1, 401)
        data[401 * 16 + 1] = 6
        self.assertTrue(inspect_directory(data)["structural_errors"])

    def test_unknown_reserved_bytes_are_reported_without_invented_meaning(self):
        data = library(1)
        row(data, 0, b"FLAG", 1, 401)
        data[401 * 16 + 1] = 5
        data[16] = 7
        data[16 + 30] = 8
        report = inspect_directory(data)
        self.assertEqual(report["nonzero_reserved_slots0"], [0])
        self.assertEqual(report["slots"][0]["nonzero_reserved_offsets"], [0, 30])

    def test_cli_is_readonly_and_rejects_other_header(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.lib"
            path.write_bytes(library())
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([str(path)]), 0)
            self.assertEqual(json.loads(output.getvalue())[0]["sha256"], before)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
            path.write_bytes(b"OTHER" + path.read_bytes()[5:])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(path)]), 1)


if __name__ == "__main__":
    unittest.main()
