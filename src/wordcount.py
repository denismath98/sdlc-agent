import argparse
import sys
from pathlib import Path
from typing import Optional


def count_words(text: str) -> int:
    """Return the number of words in *text*.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in *text* according to the specification."""
    if not text:
        return 0
    newline_count = text.count("\n")
    return newline_count if text.endswith("\n") else newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters in *text*."""
    return len(text)


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WordCount Pro")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=Path, help="Path to a UTF‑8 encoded text file")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = _parse_args(argv)

    if args.text is not None:
        text = args.text
    else:
        text = _read_file(args.file)

    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)

    output = f"words={words}\nlines={lines}\nchars={chars}"
    print(output)


if __name__ == "__main__":
    main()
