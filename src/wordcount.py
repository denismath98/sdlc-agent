import argparse
import sys
from pathlib import Path


def count_words(text: str) -> int:
    """Return the number of words in the given text."""
    return len([w for w in text.split() if w])


def count_lines(text: str) -> int:
    """Return the number of lines in the given text."""
    if not text:
        return 0
    # splitlines handles different newline conventions
    return len(text.splitlines())


def count_chars(text: str) -> int:
    """Return the number of characters in the given text."""
    return len(text)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Word count utility")
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to the input text file",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["words", "lines", "chars"],
        help="Counting mode: words, lines, or chars",
    )
    return parser.parse_args(argv)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = _parse_args(argv)

    try:
        text = args.file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file {args.file}: {e}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "words":
        result = count_words(text)
    elif args.mode == "lines":
        result = count_lines(text)
    else:  # chars
        result = count_chars(text)

    print(result)


if __name__ == "__main__":
    main()
