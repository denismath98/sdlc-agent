import pytest
from wordcount.processor import count_words, count_lines, count_characters


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),
        ("hello", 1),
        ("hello world", 2),
        ("   multiple   spaces   ", 3),
        ("line1\nline2\nline3", 3),
    ],
)
def test_count_words(text, expected):
    assert count_words(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),
        ("single line", 1),
        ("first line\nsecond line", 2),
        ("line1\nline2\n", 2),
        ("\n\n", 3),  # three empty lines: two newlines create three lines
    ],
)
def test_count_lines(text, expected):
    assert count_lines(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),
        ("abc", 3),
        ("a b c", 5),  # includes spaces
        ("line1\nline2", 11),  # includes newline
        (" \n\t", 3),  # space, newline, tab counted
    ],
)
def test_count_characters(text, expected):
    assert count_characters(text) == expected


# New test covering character count with spaces and newlines
def test_character_count_including_spaces_and_newlines():
    sample = "Hello World\nThis is a test.\n"
    # Expected count: all characters including spaces and two newline characters
    expected = len(sample)
    assert count_characters(sample) == expected
