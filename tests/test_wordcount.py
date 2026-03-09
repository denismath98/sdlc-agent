import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from src.wordcount import count_chars, count_lines, count_words


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", (0, 0, 0)),
        ("  hello   world  ", (2, 1, 17)),
        ("line1\nline2\n", (2, 2, 12)),
        ("one\n", (1, 1, 4)),
        ("one", (1, 1, 3)),
        ("\n\n", (0, 2, 2)),
    ],
)
def test_counts(text: str, expected: tuple[int, int, int]):
    words, lines, chars = expected
    assert count_words(text) == words
    assert count_lines(text) == lines
    assert count_chars(text) == chars


def run_cli(args: list[str]) -> str:
    """Run the module as a script and return its stdout."""
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_cli_text():
    output = run_cli(["--text", "alpha beta gamma"])
    assert output == "words=3\nlines=1\nchars=16"


def test_cli_file():
    content = "alpha beta\n\ngamma"
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        output = run_cli(["--file", str(tmp_path)])
        # Expected: 3 words, 3 lines, 17 characters
        assert output == "words=3\nlines=3\nchars=17"
    finally:
        tmp_path.unlink()
