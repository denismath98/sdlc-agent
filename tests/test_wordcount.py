import subprocess
import sys
from pathlib import Path

import pytest

from src.wordcount import count_words, count_lines, count_chars


@pytest.mark.parametrize(
    "text,exp_words,exp_lines,exp_chars",
    [
        ("", 0, 0, 0),
        (" hello world ", 2, 1, 13),
        ("line1\nline2\n", 2, 2, 12),
        ("one\n", 1, 1, 4),
        ("one", 1, 1, 3),
        ("\n\n", 0, 2, 2),
    ],
)
def test_counts(text, exp_words, exp_lines, exp_chars):
    assert count_words(text) == exp_words
    assert count_lines(text) == exp_lines
    assert count_chars(text) == exp_chars


def run_cli(args):
    """Run the CLI module and return its stdout as text."""
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_cli_text():
    out = run_cli(["--text", "hello world"])
    assert out == "words=2\nlines=1\nchars=11\n"


def test_cli_file(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("a b\nc", encoding="utf-8")
    out = run_cli(["--file", str(file_path)])
    # "a b\nc" -> words=3, lines=2, chars=5
    assert out == "words=3\nlines=2\nchars=5\n"
