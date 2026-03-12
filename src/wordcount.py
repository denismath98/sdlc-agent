import argparse
import sys
from pathlib import Path


def count_words(text: str) -> int:
    """Return the number of words in the given text.

    A word is defined as a sequence of non‑whitespace characters.
    """
    if not text:
        return 0
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in the given text.

    An empty string has 0 lines. If the text does not end with a newline,
    the last line is still counted.
    """
    if text == "":
        return 0
    newline_count = text.count("\n")
    return newline_count if text.endswith("\n") else newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters, including whitespace and newlines."""
    return len(text)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Word, line and character counter")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--text",
        type=str,
        help="Text string to analyse",
    )
    group.add_argument(
        "--file",
        type=Path,
        help="Path to a UTF‑8 encoded text file",
    )
    return parser.parse_args(argv)


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    # args.file is guaranteed to be set because of mutual exclusivity
    return args.file.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    text = _read_input(args)

    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)

    output = f"words={words}\nlines={lines}\nchars={chars}"
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
