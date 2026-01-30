import pathlib

import pytest

from src.wordcount import count_chars, count_lines, count_words


@pytest.mark.parametrize(
    "text,expected_words,expected_lines,expected_chars",
    [
        ("", 0, 0, 0),
        (" hello world ", 2, 1, 17),
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


def test_cli_text_argument(tmp_path: pathlib.Path, capsys):
    from src import wordcount

    test_text = "hello world"
    # Simulate command line call
    wordcount.main(["--text", test_text])
    captured = capsys.readouterr()
    expected = "words=2\nlines=1\nchars=11\n"
    assert captured.out == expected


def test_cli_file_argument(tmp_path: pathlib.Path, capsys):
    from src import wordcount

    file_content = "line1\nline2"
    file_path = tmp_path / "sample.txt"
    file_path.write_text(file_content, encoding="utf-8")
    wordcount.main(["--file", str(file_path)])
    captured = capsys.readouterr()
    expected = "words=2\nlines=2\nchars=11\n"
    assert captured.out == expected
