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
def test_counts_direct(text, expected):
    words = count_words(text)
    lines = count_lines(text)
    chars = count_chars(text)
    assert (words, lines, chars) == expected


@pytest.mark.parametrize(
    "arg,expected_output",
    [
        (
            "--text",
            "words=2\nlines=1\nchars=17\n",
        ),
        (
            "--file",
            "words=2\nlines=2\nchars=12\n",
        ),
    ],
)
def test_cli(tmp_path: Path, arg, expected_output):
    if arg == "--text":
        cmd = [
            sys.executable,
            "-m",
            "src.wordcount",
            "--text",
            "  hello   world  ",
        ]
    else:
        file_path = tmp_path / "sample.txt"
        file_path.write_text("line1\nline2\n", encoding="utf-8")
        cmd = [
            sys.executable,
            "-m",
            "src.wordcount",
            "--file",
            str(file_path),
        ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    assert result.stdout == expected_output
