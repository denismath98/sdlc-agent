import pathlib
import subprocess
import sys

import pytest

from src.wordcount import count_words, count_lines, count_chars


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
def test_counts(text, expected):
    w, l, c = expected
    assert count_words(text) == w
    assert count_lines(text) == l
    assert count_chars(text) == c


def test_cli_text_argument():
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount", "--text", "a b c"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "words=3\nlines=1\nchars=5"


def test_cli_file_argument(tmp_path: pathlib.Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("x y\nz", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount", "--file", str(file_path)],
        capture
