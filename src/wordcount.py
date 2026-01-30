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
    """Return the number of lines in *text*.

    An empty string has 0 lines. If the text does not end with a newline
    but is not empty, it is counted as a line.
    """
    if not text:
        return 0
    newline_count = text.count("\n")
    return newline_count if text.endswith("\n") else newline_count + 1


def count_chars(text: str) -> int:
    """Return the total number of characters in *text*."""
    return len(text)


def _read_input(text: Optional[str], file_path: Optional[Path]) -> str:
    if text is not None:
        return text
    if file_path is not None:
        return file_path.read_text(encoding="utf-8")
    raise ValueError("Either --text or --file must be provided.")


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description="WordCount Pro CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=Path, help="Path to a UTF‑8 encoded text file")
    args = parser.parse_args(argv)

    try:
        content = _read_input(args.text, args.file)
    except Exception as exc:  # pragma: no cover
        parser.error(str(exc))

    words = count_words(content)
    lines = count_lines(content)
    chars = count_chars(content)

    sys.stdout.write(f"words={words}\\n")
    sys.stdout.write(f"lines={lines}\\n")
    sys.stdout.write(f"chars={chars}\\n")


if __name__ == "__main__":
    main()
