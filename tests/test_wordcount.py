import subprocess
import sys
from pathlib import Path

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
        check=False,
    )
    return result


@pytest.mark.parametrize(
    "cli_args,expected_output",
    [
        (["--text", ""], "words=0\nlines=0\nchars=0\n"),
        (["--text", "  hello   world  "], "words=2\nlines=1\nchars=17\n"),
        (["--text", "line1\nline2\n"], "words=2\nlines=2\nchars=12\n"),
        (["--text", "one\n"], "words=1\nlines=1\nchars=4\n"),
        (["--text", "one"], "words=1\nlines=1\nchars=3\n"),
        (["--text", "\n\n"], "words=0\nlines=2\nchars=2\n"),
    ],
)
def test_cli_text(cli_args, expected_output):
    result = run_cli(cli_args)
    assert result.returncode == 0
    assert result.stdout == expected_output


def test_cli_file(tmp_path: Path):
    file_content = "alpha beta\n\ngamma"
    file_path = tmp_path / "sample.txt"
    file_path.write_text(file_content, encoding="utf-8")

    result = run_cli(["--file", str(file_path)])
    assert result.returncode == 0
    # Expected counts:
    # words: 4 (alpha, beta, gamma)
    # lines: 3 (line1 ends with \n, empty line, line3 without trailing \n)
    # chars: len(file_content)
    expected = f"words=4\nlines=3\nchars={len(file_content)}\n"
    assert result.stdout == expected
