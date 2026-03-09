import re
import argparse

__all__ = ["normalize_spaces"]


def normalize_spaces(text: str) -> str:
    """
    Replace sequences of spaces and tabs with a single space,
    trim leading and trailing spaces on each line, preserve line breaks,
    and keep empty lines unchanged.
    """
    lines = text.split("\n")
    normalized_lines = []
    for line in lines:
        if line == "":
            normalized_lines.append("")
            continue
        # Collapse spaces and tabs, then strip leading/trailing spaces
        collapsed = re.sub(r"[ \t]+", " ", line)
        normalized_lines.append(collapsed.strip())
    return "\n".join(normalized_lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize spaces in a given text.")
    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="The text to normalize.",
    )
    args = parser.parse_args()
    result = normalize_spaces(args.text)
    print(f"normalized={result}")
