import pathlib
import subprocess
import sys

import pytest

from src.wordcount import count_words, count_lines, count_chars


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", (0, 0, 0)),
        (" hello world ", (2, 1, 17)),
        ("line1\nline2\n", (2, 2, 12)),
        ("one\n", (1, 1, 4)),
        ("one", (1, 1, 3)),
        ("\n\n", (0, 2, 2)),
    ],
)
def test_counts(text, expected):
    words, lines, chars = expected
    assert count_words(text) == words
    assert count_lines(text) == lines
    assert count_chars(text) == chars


def run_cli(args):
    """Run the module as a script and capture its output."""
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()


def test_cli_text():
    output = run_cli(["--text", " hello world "])
    assert output == ["words=2", "lines=1", "chars=17"]


def test_cli_file(tmp_path: pathlib.Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("one\n", encoding="utf-8")
    output = run_cli(["--file", str(file_path)])
    assert output == ["words=1", "lines=1", "chars=4"]
