import pytest
from wordcount import count_words, count_lines, count_characters


def test_count_characters_includes_spaces_and_newlines():
    text = "Hello world\nThis is a test.\n"
    expected = len(text)
    assert count_characters(text) == expected


def test_count_characters_empty_string():
    assert count_characters("") == 0


def test_count_lines_behaviour():
    assert count_lines("a\nb\nc") == 3
    assert count_lines("a\nb\nc\n") == 3
    assert count_lines("") == 0


def test_count_words_basic():
    assert count_words("one two three") == 3
    assert count_words("  leading and trailing  ") == 3
