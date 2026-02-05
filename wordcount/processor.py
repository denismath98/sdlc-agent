def count_words(text: str) -> int:
    """
    Count the number of words in the given text.
    Words are separated by any whitespace.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """
    Count the number of lines in the given text.
    A line is terminated by a newline character.
    The last line without a trailing newline is also counted.
    """
    if not text:
        return 0
    # Number of newline characters plus one for the final line if it doesn't end with a newline
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def count_characters(text: str) -> int:
    """
    Count the number of characters in the given text, including spaces and newline characters.
    This mirrors the behavior of the Unix `wc -c` utility (character count).
    """
    return len(text)


__all__ = ["count_words", "count_lines", "count_characters"]
