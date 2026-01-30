"""Word count utilities and CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


def count_words(text: str) -> int:
    """Return the number of words in *text*.

    A word is a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in *text*.

    An empty string has 0 lines. If the text does not end with a newline,
    the final line is still counted.
    """
    if not text:
        return 0
    newline_count = text.count("\n")
    return newline_count if text.endswith("\n") else newline_count + 1


def count_chars(text: str) -> int:
    """Return the number of characters in *text*."""
    return len(text)


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Count words, lines and characters.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse.")
    group.add_argument("--file", type=Path, help="Path to a UTF‑8 encoded text file.")
    return parser.parse_args(argv)


def main() -> None:
    args = _parse_args()
    if args.text is not None:
        text = args.text
    else:
        try:
            text = args.file.read_text(encoding="utf-8")
        except Exception as exc:
            sys.exit(f"Error reading file: {exc}")

    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)

    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")


if __name__ == "__main__":
    main()
