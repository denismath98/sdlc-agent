import subprocess
import sys
from pathlib import Path

import pytest

from src.wordcount import count_words, count_lines, count_chars


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
        check=True,
    )
    return result.stdout.strip()


def test_cli_with_text():
    output = run_cli(["--text", "hello world"])
    assert output == "words=2\nlines=1\nchars=11"


def test_cli_with_file(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("a b\nc", encoding="utf-8")
    output = run_cli(["--file", str(file_path)])
    # "a b\nc" -> words=3, lines=2, chars=5
    assert output == "words=3\nlines=2\nchars=5"
