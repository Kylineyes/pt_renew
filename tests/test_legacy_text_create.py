"""文字对象创建复制边界模型的独立合成测试；不包含原软件字节。"""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "inspect_legacy_text_create.py"
SPEC = importlib.util.spec_from_file_location("inspect_legacy_text_create", MODULE_PATH)
creator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(creator)


class TextCreateBoundaryTests(unittest.TestCase):
    def test_empty_string_creates_no_object(self):
        self.assertIsNone(creator.expected_stored_text(b''))

    def test_single_character(self):
        self.assertEqual(creator.expected_stored_text(b'A'), b'A')

    def test_single_space_is_trimmed_to_none(self):
        self.assertIsNone(creator.expected_stored_text(b' '))

    def test_length_31_kept(self):
        text = b'A' * 30 + b'Z'
        self.assertEqual(creator.expected_stored_text(text), text)

    def test_length_32_kept(self):
        text = b'A' * 31 + b'Z'
        self.assertEqual(creator.expected_stored_text(text), text)

    def test_length_33_truncated_to_32(self):
        text = b'A' * 32 + b'Z'
        self.assertEqual(creator.expected_stored_text(text), b'A' * 32)

    def test_length_79_truncated_to_32(self):
        self.assertEqual(creator.expected_stored_text(b'A' * 78 + b'Z'), b'A' * 32)

    def test_length_80_truncated_to_32(self):
        self.assertEqual(creator.expected_stored_text(b'A' * 79 + b'Z'), b'A' * 32)

    def test_length_81_first_truncated_at_80(self):
        # 第 81 字符在进入本地缓冲前已丢弃：A*80+Z 与 A*80 结果相同
        self.assertEqual(creator.expected_stored_text(b'A' * 80 + b'Z'),
                         creator.expected_stored_text(b'A' * 80))

    def test_trailing_spaces_beyond_80_removed_before_32_cut(self):
        # A*80 + 空格*5：80 截断后全为 A，去尾空格无字符可删，再截 32
        self.assertEqual(creator.expected_stored_text(b'A' * 80 + b' ' * 5), b'A' * 32)

    def test_length_32_with_trailing_space_shrinks_to_31(self):
        self.assertEqual(creator.expected_stored_text(b'A' * 31 + b' '), b'A' * 31)

    def test_length_33_with_trailing_space_keeps_32(self):
        # 先 80 截断（不变）、去尾空格（32 个 A）、再截 32：长度仍 32
        self.assertEqual(creator.expected_stored_text(b'A' * 32 + b' '), b'A' * 32)

    def test_all_spaces_of_any_length_create_no_object(self):
        self.assertIsNone(creator.expected_stored_text(b' ' * 255))

    def test_rejects_overlong_input(self):
        with self.assertRaises(ValueError):
            creator.expected_stored_text(b'A' * 256)

    def test_rejects_non_bytes(self):
        with self.assertRaises(TypeError):
            creator.expected_stored_text('A')


if __name__ == '__main__':
    unittest.main()
