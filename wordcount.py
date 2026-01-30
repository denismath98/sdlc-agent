"""Word count utilities."""


def count_words(text: str) -> int:
    """Return number of words in text."""
    # Words are separated by any whitespace.
    return len(text.split())


def count_lines(text: str) -> int:
    """Return number of lines in text, similar to wc -l."""
    if not text:
        return 0
    # wc counts lines as number of newline characters.
    # If text does not end with newline, wc still counts the last line.
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def count_characters(text: str) -> int:
    """Return number of characters including spaces and newlines, like wc -c."""
    # In Python, len gives number of Unicode code points, which matches wc behavior for ASCII.
    return len(text)


# Backward compatibility alias
count_chars = count_characters
