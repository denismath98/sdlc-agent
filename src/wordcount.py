import argparse
import re
import sys
from pathlib import Path


def count_words(text: str) -> int:
    """Return the number of words in the given text.

    A word is defined as a consecutive sequence of non‑whitespace characters.
    """
    return len(re.findall(r"\S+", text))


def count_lines(text: str) -> int:
    """Return the number of lines in the given text.

    An empty string has 0 lines. If the text does not end with a newline,
    the final segment is still counted as a line.
    """
    if not text:
        return 0
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return len(lines)


def count_chars(text: str) -> int:
    """Return the total number of characters, including whitespace and newlines."""
    return len(text)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Word, line and character counter.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse.")
    group.add_argument(
        "--file", type=Path, help="Path to a UTF‑8 encoded text file to analyse."
    )
    return parser.parse_args(argv)


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    # args.file is guaranteed to be set because of mutually exclusive group
    return args.file.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    text = _read_input(args)

    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)

    output = f"words={words}\nlines={lines}\nchars={chars}"
    print(output)


if __name__ == "__main__":
    main()
