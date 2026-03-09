import argparse
from pathlib import Path
from typing import Optional


def count_words(text: str) -> int:
    """Return the number of words in the given text.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in the given text.

    An empty string has 0 lines.
    If the text does not end with a newline, the final fragment counts as a line.
    """
    if not text:
        return 0
    line_count = text.count("\n")
    if not text.endswith("\n"):
        line_count += 1
    return line_count


def count_chars(text: str) -> int:
    """Return the total number of characters in the given text,
    including whitespace and newline characters.
    """
    return len(text)


def _read_input(text: Optional[str], file_path: Optional[Path]) -> str:
    if text is not None:
        return text
    if file_path is not None:
        return file_path.read_text(encoding="utf-8")
    raise ValueError("Either text or file_path must be provided.")


def main() -> None:
    parser = argparse.ArgumentParser(description="WordCount Pro")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=Path, help="Path to a UTF‑8 encoded text file")
    args = parser.parse_args()

    content = _read_input(args.text, args.file)

    words = count_words(content)
    lines = count_lines(content)
    chars = count_chars(content)

    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")


if __name__ == "__main__":
    main()
