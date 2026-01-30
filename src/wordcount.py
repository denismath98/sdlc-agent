import argparse
import sys
from pathlib import Path
from typing import Callable


def count_words(text: str) -> int:
    """Return the number of words in the given text."""
    # Split on any whitespace and filter out empty strings
    return len([w for w in text.split() if w])


def count_lines(text: str) -> int:
    """Return the number of lines in the given text."""
    # splitlines handles different newline conventions and does not keep the linebreaks
    return len(text.splitlines())


def count_chars(text: str) -> int:
    """Return the number of characters in the given text."""
    return len(text)


def _get_counter(mode: str) -> Callable[[str], int]:
    if mode == "words":
        return count_words
    if mode == "lines":
        return count_lines
    if mode == "chars":
        return count_chars
    raise ValueError(f"Unsupported mode: {mode!r}. Choose from words|lines|chars.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Count words, lines, or characters in a text file."
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to the input text file.",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["words", "lines", "chars"],
        help="Counting mode: words, lines, or chars.",
    )
    args = parser.parse_args(argv)

    if not args.file.is_file():
        print(f"Error: file not found – {args.file}", file=sys.stderr)
        return 1

    try:
        text = args.file.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        return 1

    counter = _get_counter(args.mode)
    result = counter(text)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
