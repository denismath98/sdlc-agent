import argparse
import sys
from pathlib import Path
from typing import Optional


def count_words(text: str) -> int:
    """Return the number of words in the given text.

    A word is defined as a sequence of non‑whitespace characters.
    """
    return len(text.split())


def count_lines(text: str) -> int:
    """Return the number of lines in the given text.

    An empty string yields 0 lines. A trailing newline does not create an extra empty line.
    """
    return len(text.splitlines())


def count_chars(text: str) -> int:
    """Return the total number of characters in the given text, including whitespace."""
    return len(text)


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _process_input(text: Optional[str], file_path: Optional[Path]) -> str:
    if text is not None:
        return text
    if file_path is not None:
        return _read_file(file_path)
    raise ValueError("Either --text or --file must be provided.")


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description="WordCount Pro CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyse")
    group.add_argument("--file", type=Path, help="Path to a UTF‑8 encoded text file")
    args = parser.parse_args(argv)

    try:
        content = _process_input(args.text, args.file)
    except Exception as exc:
        parser.error(str(exc))

    words = count_words(content)
    lines = count_lines(content)
    chars = count_chars(content)

    sys.stdout.write(f"words={words}\nlines={lines}\nchars={chars}\n")


if __name__ == "__main__":
    main()
