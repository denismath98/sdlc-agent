import argparse
import sys
import re
from pathlib import Path
from typing import Tuple


def count_words(text: str) -> int:
    """Return the number of words in *text*.

    A word is defined as a consecutive sequence of non‑whitespace characters.
    """
    return len(re.findall(r"\S+", text))


def count_lines(text: str) -> int:
    """Return the number of lines in *text* according to the specification."""
    if not text:
        return 0
    newline_count = text.count("\n")
    return newline_count if text.endswith("\n") else newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters in *text* (including whitespace)."""
    return len(text)


def _process_text(text: str) -> Tuple[int, int, int]:
    """Calculate words, lines and characters for *text*."""
    return count_words(text), count_lines(text), count_chars(text)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m src.wordcount",
        description="Count words, lines and characters in a string or file.",
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
        help="Path to a UTF‑8 encoded text file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.text is not None:
        text = args.text
    else:
        try:
            text = args.file.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"Error reading file: {exc}", file=sys.stderr)
            return 1

    words, lines, chars = _process_text(text)
    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
