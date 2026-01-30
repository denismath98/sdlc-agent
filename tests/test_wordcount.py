import pytest
from src.wordcount import count_words, count_lines, count_chars


@pytest.mark.parametrize(
    "text, expected_words, expected_lines, expected_chars",
    [
        ("", 0, 0, 0),  # empty string
        ("  hello   world  ", 2, 1, 19),  # multiple spaces
        ("line1\nline2\n", 2, 2, 12),  # trailing newline
    ],
)
def test_counts(text, expected_words, expected_lines, expected_chars):
    assert count_words(text) == expected_words
    assert count_lines(text) == expected_lines
    assert count_chars(text) == expected_chars
