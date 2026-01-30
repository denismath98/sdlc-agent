import re
from typing import Tuple


def count_lines(text: str) -> int:
    """
    Count the number of lines in the given text.
    Empty string counts as 0 lines.
    """
    if not text:
        return 0
    # Split on newline characters; keep trailing empty line if text ends with newline
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def count_words(text: str) -> int:
    """
    Count the number of words in the given text.
    Words are sequences of non-whitespace characters.
    """
    if not text:
        return 0
    # Use regex to find word-like sequences
    return len(re.findall(r"\S+", text))


def _count_characters_raw(text: str) -> int:
    """
    Internal helper that returns the raw number of characters,
    including spaces and newline characters.
    Mirrors the behavior of the Unix `wc -m` option.
    """
    return len(text)


def count_characters(text: str) -> int:
    """
    Public API: count characters including spaces and newlines.
    This function preserves the original public name, extending its behavior
    to match the Unix `wc` utility.
    """
    return _count_characters_raw(text)


def wc(text: str) -> Tuple[int, int, int]:
    """
    Return a tuple (lines, words, characters) analogous to the output of `wc`.
    """
    return (count_lines(text), count_words(text), count_characters(text))
