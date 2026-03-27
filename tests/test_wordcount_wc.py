import unittest
from wordcount import count_lines, count_words, count_characters, wc


class TestWordCountWC(unittest.TestCase):
    def test_empty_string(self):
        text = ""
        self.assertEqual(count_lines(text), 0)
        self.assertEqual(count_words(text), 0)
        self.assertEqual(count_characters(text), 0)
        self.assertEqual(wc(text), (0, 0, 0))

    def test_single_line_no_newline(self):
        text = "Hello world"
        self.assertEqual(count_lines(text), 1)
        self.assertEqual(count_words(text), 2)
        self.assertEqual(count_characters(text), len(text))
        self.assertEqual(wc(text), (1, 2, len(text)))

    def test_multiple_lines_with_newlines(self):
        text = "First line\nSecond line\nThird line\n"
        # Lines: 4 because trailing newline creates an empty line
        self.assertEqual(count_lines(text), 4)
        self.assertEqual(count_words(text), 6)
        self.assertEqual(count_characters(text), len(text))
        self.assertEqual(wc(text), (4, 6, len(text)))

    def test_spaces_and_tabs(self):
        text = "  leading spaces\nword\twith\ttabs  "
        self.assertEqual(count_lines(text), 2)
        self.assertEqual(count_words(text), 4)
        self.assertEqual(count_characters(text), len(text))
        self.assertEqual(wc(text), (2, 4, len(text)))


if __name__ == "__main__":
    unittest.main()
