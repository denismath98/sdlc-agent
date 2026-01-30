import argparse
import sys
from pathlib import Path


def count_words(text: str) -> int:
    """Count the number of words in the given text."""
    # Split on any whitespace and filter out empty strings
    return len([w for w in text.split() if w])


def count_lines(text: str) -> int:
    """Count the number of lines in the given text."""
    # splitlines handles different newline conventions and does not keep linebreaks
    return len(text.splitlines())


def count_chars(text: str) -> int:
    """Count the number of characters in the given text."""
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
        sys.stderr.write(f"Error reading file {args.file}: {e}\n")
        sys.exit(1)

    if args.mode == "words":
        result = count_words(text)
    elif args.mode == "lines":
        result = count_lines(text)
    elif args.mode == "chars":
        result = count_chars(text)
    else:
        sys.stderr.write(f"Unsupported mode: {args.mode}\n")
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
