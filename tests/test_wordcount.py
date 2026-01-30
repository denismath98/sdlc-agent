import pytest
from src.wordcount import count_words, count_lines, count_chars


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),
        ("   ", 0),
        ("\n", 0),
    ],
)
def test_count_words_empty_cases(text, expected):
    assert count_words(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("hello world", 2),
        ("  hello   world  ", 2),
        ("one\ntwo three", 3),
    ],
)
def test_count_words_various(text, expected):
    assert count_words(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),
        ("single line", 1),
        ("line1\nline2", 2),
        ("line1\nline2\n", 2),
        ("line1\r\nline2\r\n", 2),
    ],
)
def test_count_lines(text, expected):
    assert count_lines(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),
        ("abc", 3),
        ("a b c", 5),
        ("line1\nline2\n", 12),  # includes two newline characters
    ],
)
def test_count_chars(text, expected):
    assert count_chars(text) == expected
