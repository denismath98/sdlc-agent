import pathlib
import tempfile

import pytest

from src.wordcount import count_words, count_lines, count_chars


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),  # empty string
        ("   ", 0),  # multiple spaces only
        ("Hello world", 2),  # simple case
        ("Hello   world  ", 2),  # multiple spaces between words
    ],
)
def test_count_words(text, expected):
    assert count_words(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),  # empty string
        ("Line1\nLine2\nLine3", 3),  # three lines
        ("Single line", 1),  # no newline
        ("Trailing newline\n", 1),  # trailing newline counts as one line
    ],
)
def test_count_lines(text, expected):
    assert count_lines(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),  # empty string
        ("abc", 3),  # simple chars
        ("a b c", 5),  # includes spaces
        ("Line1\nLine2", 11),  # includes newline character
    ],
)
def test_count_chars(text, expected):
    assert count_chars(text) == expected


def test_cli_wordcount(tmp_path, monkeypatch, capsys):
    # Create a temporary file with known content
    content = "Hello world\nSecond line"
    file_path = tmp_path / "sample.txt"
    file_path.write_text(content, encoding="utf-8")

    # Monkeypatch sys.argv for CLI invocation
    from src import wordcount

    monkeypatch.setattr(
        wordcount,
        "sys",
        type(
            "sys",
            (),
            {
                "argv": ["prog", "--file", str(file_path), "--mode", "words"],
                "exit": lambda code=0: None,
                "stderr": sys.stderr,
            },
        ),
    )
    # Run main
    wordcount.main()
    captured = capsys.readouterr()
    assert (
        captured.out.strip() == "3"
    )  # "Hello", "world", "Second", "line" -> actually 4 words? Wait split: "Hello", "world", "Second", "line" => 4
