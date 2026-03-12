import argparse
import sys
from typing import Tuple


def count_words(text: str) -> int:
    """Return the number of words in *text*.

    A word is defined as a consecutive sequence of non‑whitespace characters.
    """
    return len([w for w in text.split() if w])


def count_lines(text: str) -> int:
    """Return the number of lines in *text*.

    An empty string yields 0. If the text does not end with a newline, the final
    fragment is also counted as a line.
    """
    if not text:
        return 0
    newline_count = text.count("\n")
    return newline_count if text.endswith("\n") else newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters in *text*, including whitespace."""
    return len(text)


def _process(text: str) -> Tuple[int, int, int]:
    """Calculate word, line and character counts for *text*."""
    return count_words(text), count_lines(text), count_chars(text)


def _print_counts(words: int, lines: int, chars: int) -> None:
    """Print counts in the required format."""
    sys.stdout.write(f"words={words}\nlines={lines}\nchars={chars}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="WordCount Pro CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=str, help="Path to a UTF‑8 encoded text file")
    args = parser.parse_args()

    if args.text is not None:
        text = args.text
    else:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as exc:
            parser.error(str(exc))
            return

    words, lines, chars = _process(text)
    _print_counts(words, lines, chars)


if __name__ == "__main__":
    main()
