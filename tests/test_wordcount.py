import subprocess
import sys
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


def test_cli_with_text():
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount", "--text", "  hello   world  "],
        capture_output=True,
        text=True,
        check=True,
    )
    expected = "words=2\nlines=1\nchars=17"
    assert result.stdout.strip() == expected


def test_cli_with_file(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("line1\nline2\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount", "--file", str(file_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    expected = "words=2\nlines=2\nchars=12"
    assert result.stdout.strip() == expected
