import subprocess
import sys
from pathlib import Path

import pytest

from src.wordcount import count_chars, count_lines, count_words


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
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()


@pytest.mark.parametrize(
    "text,exp_output",
    [
        ("", ["words=0", "lines=0", "chars=0"]),
        (" hello world ", ["words=2", "lines=1", "chars=13"]),
        ("line1\nline2\n", ["words=2", "lines=2", "chars=12"]),
        ("one\n", ["words=1", "lines=1", "chars=4"]),
        ("one", ["words=1", "lines=1", "chars=3"]),
        ("\n\n", ["words=0", "lines=2", "chars=2"]),
    ],
)
def test_cli_text_argument(text, exp_output):
    output = run_cli(["--text", text])
    assert output == exp_output


def test_cli_file_argument(tmp_path: Path):
    content = "hello world\nsecond line"
    file_path = tmp_path / "sample.txt"
    file_path.write_text(content, encoding="utf-8")
    output = run_cli(["--file", str(file_path)])
    expected = [
        f"words={len(content.split())}",
        f"lines={content.count(chr(10)) + (0 if content.endswith(chr(10)) else 1)}",
        f"chars={len(content)}",
    ]
    assert output == expected
