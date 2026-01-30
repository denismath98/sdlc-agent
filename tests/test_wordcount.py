import os
import tempfile

import pytest

from src.wordcount import count_words, count_lines, count_chars, main


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


def test_cli_text_argument(capsys):
    main(["--text", "hello world"])
    captured = capsys.readouterr()
    assert captured.out.strip() == "words=2\nlines=1\nchars=11"


def test_cli_file_argument():
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write("a b\nc")
        tmp_path = tmp.name
    try:
        # Capture stdout
        from io import StringIO
        import sys

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            main(["--file", tmp_path])
            output = sys.stdout.getvalue().strip()
        finally:
            sys.stdout = old_stdout
        assert output == "words=3\nlines=2\nchars=6"
    finally:
        os.remove(tmp_path)
