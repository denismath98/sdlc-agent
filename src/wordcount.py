import argparse
import sys
from pathlib import Path


def count_words(text: str) -> int:
    """Return the number of words in *text*.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in *text*.

    An empty string yields 0. If the text does not end with a newline,
    the final segment is counted as a line.
    """
    if not text:
        return 0
    newline_count = text.count("\n")
    if text.endswith("\n"):
        return newline_count
    return newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters in *text*."""
    return len(text)


def _read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8")
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.wordcount")
    parser.add_argument("--text", type=str, help="Text to analyse")
    parser.add_argument("--file", type=str, help="Path to a UTF‑8 encoded file")
    parsed = parser.parse_args(argv)

    content = _read_input(parsed)

    words = count_words(content)
    lines = count_lines(content)
    chars = count_chars(content)

    sys.stdout.write(f"words={words}\\nlines={lines}\\nchars={chars}\\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
