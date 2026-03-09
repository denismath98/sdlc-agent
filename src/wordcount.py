import argparse
import sys
from typing import Tuple


def count_words(text: str) -> int:
    """Return the number of words in the given text.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in the given text according to the rules."""
    if not text:
        return 0
    newline_count = text.count("\n")
    if text.endswith("\n"):
        return newline_count
    return newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters, including whitespace."""
    return len(text)


def _process(text: str) -> Tuple[int, int, int]:
    """Helper to compute words, lines and chars."""
    return count_words(text), count_lines(text), count_chars(text)


def _print_counts(words: int, lines: int, chars: int) -> None:
    """Print counts in the required format."""
    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="WordCount Pro")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=str, help="Path to a UTF‑8 encoded text file")
    args = parser.parse_args(argv)

    if args.text is not None:
        text = args.text
    else:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as exc:
            parser.error(f"Cannot read file: {exc}")

    words, lines, chars = _process(text)
    _print_counts(words, lines, chars)


if __name__ == "__main__":
    main()
