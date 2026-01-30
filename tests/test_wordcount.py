import pathlib

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
    words, lines, chars = expected
    assert count_words(text) == words
    assert count_lines(text) == lines
    assert count_chars(text) == chars


def test_cli_text_argument(tmp_path, capsys):
    from src import wordcount

    test_text = "hello world"
    wordcount.main(["--text", test_text])
    captured = capsys.readouterr()
    assert captured.out == "words=2\\nlines=1\\nchars=11\\n"


def test_cli_file_argument(tmp_path, capsys):
    from src import wordcount

    file_path = tmp_path / "sample.txt"
    file_path.write_text("a b\\nc", encoding="utf-8")
    wordcount.main(["--file", str(file_path)])
    captured = capsys.readouterr()
    # "a b\\nc" -> words=3, lines=2, chars=5
    assert captured.out == "words=3\\nlines=2\\nchars=5\\n")
