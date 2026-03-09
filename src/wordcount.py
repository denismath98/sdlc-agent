import argparse
import sys
from pathlib import Path


def count_words(text: str) -> int:
    """Return the number of words in the given text.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in the given text.

    Empty string → 0.
    If the text does not end with a newline, the last line is counted as well.
    """
    if not text:
        return 0
    newline_count = text.count("\n")
    return newline_count if text.endswith("\n") else newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters, including whitespace and newlines."""
    return len(text)


def _process_text(text: str) -> tuple[int, int, int]:
    """Helper that returns (words, lines, chars) for the given text."""
    return count_words(text), count_lines(text), count_chars(text)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Count words, lines, and characters in a text."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--text",
        type=str,
        help="Text string to be analysed.",
    )
    group.add_argument(
        "--file",
        type=Path,
        help="Path to a UTF‑8 encoded file to be analysed.",
    )
    args = parser.parse_args(argv)

    if args.text is not None:
        text = args.text
    else:
        try:
            text = args.file.read_text(encoding="utf-8")
        except Exception as exc:
            parser.error(f"Unable to read file: {exc}")

    words, lines, chars = _process_text(text)
    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")


if __name__ == "__main__":
    main()
