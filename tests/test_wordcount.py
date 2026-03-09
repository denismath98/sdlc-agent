import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from src.wordcount import count_chars, count_lines, count_words


@pytest.mark.parametrize(
    "text,expected_words,expected_lines,expected_chars",
    [
        ("", 0, 0, 0),
        ("  hello   world  ", 2, 1, 17),
        ("line1\nline2\n", 2, 2, 12),
        ("one\n", 1, 1, 4),
        ("one", 1, 1, 3),
        ("\n\n", 0, 2, 2),
    ],
)
def test_counts(text, expected_words, expected_lines, expected_chars):
    assert count_words(text) == expected_words
    assert count_lines(text) == expected_lines
    assert count_chars(text) == expected_chars


def run_cli(args):
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount"] + args,
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def test_cli_text():
    result = run_cli(["--text", "hello world"])
    assert result.returncode == 0
    assert result.stdout.strip() == "words=2\nlines=1\nchars=11"


def test_cli_file():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write("first line\nsecond line")
        tmp_path = Path(tmp.name)
    try:
        result = run_cli(["--file", str(tmp_path)])
        assert result.returncode == 0
        # "first line\nsecond line" -> words=4, lines=2, chars=23
        assert result.stdout.strip() == "words=4\nlines=2\nchars=23"
    finally:
        tmp_path.unlink()
