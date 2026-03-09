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
    if text == "":
        return 0
    newline_count = text.count("\n")
    if text.endswith("\n"):
        return newline_count
    return newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters in *text* (including spaces and newlines)."""
    return len(text)


def _read_input(text_arg: Optional[str], file_arg: Optional[str]) -> str:
    if text_arg is not None:
        return text_arg
    if file_arg is not None:
        path = Path(file_arg)
        return path.read_text(encoding="utf-8")
    raise ValueError("Either --text or --file must be provided.")


def main() -> None:
    parser = argparse.ArgumentParser(description="WordCount Pro")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=str, help="Path to a UTF‑8 encoded file")
    args = parser.parse_args()

    try:
        content = _read_input(args.text, args.file)
    except Exception as exc:
        parser.error(str(exc))

    words = count_words(content)
    lines = count_lines(content)
    chars = count_chars(content)

    sys.stdout.write(f"words={words}\nlines={lines}\nchars={chars}\n")


if __name__ == "__main__":
    main()
