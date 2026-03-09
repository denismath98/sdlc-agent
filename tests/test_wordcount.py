import subprocess
import sys
import pathlib

import pytest

from src.wordcount import count_words, count_lines, count_chars


def test_empty_string():
    text = ""
    assert count_words(text) == 0
    assert count_lines(text) == 0
    assert count_chars(text) == 0


def test_spaces():
    text = "  hello   world  "
    assert count_words(text) == 2
    assert count_lines(text) == 1
    assert count_chars(text) == 17


def test_two_lines_with_trailing_newline():
    text = "line1\nline2\n"
    assert count_words(text) == 2
    assert count_lines(text) == 2
    assert count_chars(text) == 12


def test_one_line_with_newline():
    text = "one\n"
    assert count_words(text) == 1
    assert count_lines(text) == 1
    assert count_chars(text) == 4


def test_one_line_without_newline():
    text = "one"
    assert count_words(text) == 1
    assert count_lines(text) == 1
    assert count_chars(text) == 3


def test_multiple_newlines():
    text = "\n\n"
    assert count_words(text) == 0
    assert count_lines(text) == 2
    assert count_chars(text) == 2


@pytest.mark.parametrize(
    "cli_args,expected_output",
    [
        (["--text", ""], "words=0\nlines=0\nchars=0\n"),
        (["--text", "  hello   world  "], "words=2\nlines=1\nchars=17\n"),
        (["--text", "line1\nline2\n"], "words=2\nlines=2\nchars=12\n"),
    ],
)
def test_cli_with_text(cli_args, expected_output):
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount"] + cli_args,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == expected_output


def test_cli_with_file(tmp_path: pathlib.Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("one\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "src.wordcount", "--file", str(file_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == "words=1\nlines=1\nchars=4\n"
