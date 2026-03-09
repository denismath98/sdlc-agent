import argparse
from typing import Any


def reverse_text(text: str) -> str:
    """Return the given text reversed.

    The function does not modify character case and fully supports Unicode.
    """
    return text[::-1]


def _main() -> None:
    parser = argparse.ArgumentParser(description="Reverse a given text.")
    parser.add_argument("--text", required=True, help="Text to reverse")
    args = parser.parse_args()
    result = reverse_text(args.text)
    print(f"reversed={result}")


if __name__ == "__main__":
    _main()

__all__ = ["reverse_text"]
