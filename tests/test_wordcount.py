import pathlib
import tempfile

import pytest

from src.wordcount import count_words, count_lines, count_chars


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),  # empty string
        ("   ", 0),  # multiple spaces only
        ("Hello   world", 2),  # multiple spaces between words
        ("Hello\nWorld", 2),  # newline separates words
    ],
)
def test_count_words(text, expected):
    assert count_words(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),  # empty string
        ("   ", 1),  # spaces count as a single line
        ("line1\nline2\nline3", 3),  # multiple lines
        ("single line\n", 1),  # trailing newline does not add extra line
    ],
)
def test_count_lines(text, expected):
    assert count_lines(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),  # empty string
        ("abc", 3),  # simple case
        ("a b c", 5),  # includes spaces
        ("line1\nline2", 11),  # includes newline character
    ],
)
def test_count_chars(text, expected):
    assert count_chars(text) == expected


def test_cli_integration():
    # Create a temporary file with known content
    content = "Hello world\nThis is a test."
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = pathlib.Path(tmpdir) / "sample.txt"
        file_path.write_text(content, encoding="utf-8")

        # Run the CLI in each mode and capture output
        import subprocess
        import sys

        for mode, expected in [
            ("words", "6"),
            ("lines", "2"),
            ("chars", str(len(content))),
        ]:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.wordcount",
                    "--file",
                    str(file_path),
                    "--mode",
                    mode,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip() == expected
