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

    An empty string has 0 lines. If the text does not end with a newline
    but is non‑empty, it is counted as an additional line.
    """
    if not text:
        return 0
    line_count = text.count("\n")
    if not text.endswith("\n"):
        line_count += 1
    return line_count


def count_chars(text: str) -> int:
    """Return the total number of characters in *text*."""
    return len(text)


def _process_input(text: Optional[str] = None, file_path: Optional[Path] = None) -> str:
    if text is not None:
        return text
    if file_path is not None:
        return file_path.read_text(encoding="utf-8")
    raise ValueError("Either --text or --file must be provided.")


def main() -> None:
    parser = argparse.ArgumentParser(description="WordCount Pro CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=Path, help="Path to a UTF‑8 encoded file")
    args = parser.parse_args()

    input_text = _process_input(text=args.text, file_path=args.file)

    words = count_words(input_text)
    lines = count_lines(input_text)
    chars = count_chars(input_text)

    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")


if __name__ == "__main__":
    main()
