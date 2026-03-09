import argparse
import re
import sys
from pathlib import Path


def count_words(text: str) -> int:
    """Return the number of words in the given text.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(re.findall(r"\S+", text))


def count_lines(text: str) -> int:
    """Return the number of lines in the given text.

    An empty string has 0 lines. If the text does not end with a newline,
    the final line is still counted.
    """
    if text == "":
        return 0
    newline_count = text.count("\n")
    if text.endswith("\n"):
        return newline_count
    return newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters, including whitespace."""
    return len(text)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WordCount Pro CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=Path, help="Path to a UTF‑8 encoded text file")
    return parser.parse_args(argv)


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    try:
        return args.file.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    args = _parse_args()
    text = _read_input(args)

    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)

    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")


if __name__ == "__main__":
    main()
