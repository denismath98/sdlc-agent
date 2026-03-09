import subprocess
import sys
from pathlib import Path

import pytest

from src.wordcount import count_chars, count_lines, count_words


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
    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)
    assert (words, lines, chars) == expected


def run_cli(args):
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.mark.parametrize(
    "cli_args,expected_output",
    [
        (["--text", ""], "words=0\nlines=0\nchars=0"),
        (["--text", " hello world "], "words=2\nlines=1\nchars=17"),
        (["--file", "test_file.txt"], "words=2\nlines=2\nchars=12"),
    ],
)
def test_cli(tmp_path: Path, cli_args, expected_output):
    if "--file" in cli_args:
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("line1\nline2\n", encoding="utf-8")
        cli_args = [
            arg if arg != "test_file.txt" else str(file_path) for arg in cli_args
        ]

    output = run_cli(cli_args)
    assert output == expected_output
