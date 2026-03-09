import argparse


def reverse_text(text: str) -> str:
    """Return the given string reversed, preserving case and Unicode characters."""
    return text[::-1]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reverse a given text string.")
    parser.add_argument(
        "--text",
        required=True,
        type=str,
        help="The text to reverse.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    print(f"reversed={reverse_text(args.text)}")
