import argparse
import sys
from typing import Optional


def count_words(text: str) -> int:
    """Return the number of words in *text*.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in *text*.

    An empty string has 0 lines. If the text does not end with a newline
    but is non‑empty, it is counted as an additional line.
    """
    if not text:
        return 0
    lines = text.count("\n")
    if not text.endswith("\n"):
        lines += 1
    return lines


def count_chars(text: str) -> int:
    """Return the total number of characters in *text* (including whitespace)."""
    return len(text)


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WordCount Pro CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=str, help="Path to a UTF‑8 encoded file")
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> None:
    args = _parse_args(argv)
    if args.text is not None:
        text = args.text
    else:
        text = _read_file(args.file)

    print(f"words={count_words(text)}")
    print(f"lines={count_lines(text)}")
    print(f"chars={count_chars(text)}")


if __name__ == "__main__":
    main(sys.argv[1:])
