import argparse
import pathlib
import re
import sys


def count_words(text: str) -> int:
    """Return the number of words in *text*."""
    return len(re.findall(r"\S+", text))


def count_lines(text: str) -> int:
    """Return the number of lines in *text*."""
    if text == "":
        return 0
    lines = text.count("\n")
    if not text.endswith("\n"):
        lines += 1
    return lines


def count_chars(text: str) -> int:
    """Return the number of characters in *text*."""
    return len(text)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WordCount Pro")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Input text")
    group.add_argument(
        "--file", type=pathlib.Path, help="Path to a UTF‑8 encoded text file"
    )
    return parser.parse_args(argv)


def main() -> None:
    args = _parse_args()
    if args.text is not None:
        text = args.text
    else:
        text = args.file.read_text(encoding="utf-8")
    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)
    print(f"words={words}")
    print(f"lines={lines}")
    print(f"chars={chars}")


if __name__ == "__main__":
    main()
