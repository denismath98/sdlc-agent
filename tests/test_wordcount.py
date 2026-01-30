import pathlib

import pytest

from src.wordcount import count_chars, count_lines, count_words


@pytest.mark.parametrize(
    "text,expected_words,expected_lines,expected_chars",
    [
        ("", 0, 0, 0),
        ("  hello   world  ", 2, 1, 17),
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


def test_cli_text_argument(tmp_path, monkeypatch, capsys):
    from src import wordcount

    test_text = "hello world"
    monkeypatch.setattr("sys.argv", ["prog", "--text", test_text])
    wordcount.main()
    captured = capsys.readouterr().out.strip().splitlines()
    assert captured == ["words=2", "lines=1", "chars=11"]


def test_cli_file_argument(tmp_path, monkeypatch, capsys):
    from src import wordcount

    file_content = "a b\nc"
    file_path = tmp_path / "sample.txt"
    file_path.write_text(file_content, encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["prog", "--file", str(file_path)])
    wordcount.main()
    captured = capsys.readouterr().out.strip().splitlines()
    assert captured == ["words=3", "lines=2", "chars=6"]
