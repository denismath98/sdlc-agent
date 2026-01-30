import argparse
from pathlib import Path
from typing import Optional


def count_words(text: str) -> int:
    """Return the number of words in *text*.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in *text*.

    An empty string has 0 lines. If the text does not end with a newline,
    the final segment counts as a line.
    """
    if not text:
        return 0
    newline_count = text.count("\n")
    return newline_count if text.endswith("\n") else newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters in *text*."""
    return len(text)


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8")
    return ""


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description="WordCount Pro")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=str, help="Path to a UTF‑8 encoded file")
    args = parser.parse_args(argv)

    text = _read_input(args)

    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)

    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")


if __name__ == "__main__":
    main()
