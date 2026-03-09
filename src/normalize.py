import re
import argparse
from typing import List


def _normalize_line(line: str) -> str:
    """
    Replace sequences of spaces and tabs with a single space,
    then strip leading and trailing spaces.
    Empty lines are returned unchanged.
    """
    if line == "":
        return ""
    # Collapse spaces and tabs
    collapsed = re.sub(r"[ \t]+", " ", line)
    # Strip leading/trailing spaces
    return collapsed.strip()


def normalize_spaces(text: str) -> str:
    """
    Normalize spaces in the given text.

    - Replace sequences of spaces and tabs with a single space.
    - Remove leading and trailing spaces on each line.
    - Preserve newline characters.
    - Empty string remains empty.
    """
    if text == "":
        return ""
    lines: List[str] = text.split("\n")
    normalized = [_normalize_line(line) for line in lines]
    return "\n".join(normalized)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize spaces in a text.")
    parser.add_argument(
        "--text",
        required=True,
        help="The text to normalize.",
    )
    args = parser.parse_args()
    result = normalize_spaces(args.text)
    print(f"normalized={result}")
