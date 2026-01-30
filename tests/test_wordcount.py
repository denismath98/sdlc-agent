import tempfile
from src.wordcount import count_words, count_lines, count_chars


def test_empty_string():
    text = ""
    assert count_words(text) == 0
    assert count_lines(text) == 0
    assert count_chars(text) == 0


def test_multiple_spaces():
    text = "Hello   world  test"
    assert count_words(text) == 3
    assert count_lines(text) == 1
    assert count_chars(text) == len(text)


def test_trailing_newline():
    text = "Hello world\n"
    assert count_words(text) == 2
    assert count_lines(text) == 1
    assert count_chars(text) == len(text)


def test_file_cli(tmp_path, capsys):
    # Create a temporary file for CLI testing
    file_content = "One two three\nFour five"
    file_path = tmp_path / "sample.txt"
    file_path.write_text(file_content, encoding="utf-8")

    # Import the CLI entry point
    from src import wordcount

    # Simulate CLI arguments for word count
    wordcount.main(["--file", str(file_path), "--mode", "words"])
    captured = capsys.readouterr()
    assert captured.out.strip() == "5"

    # Simulate CLI arguments for line count
    wordcount.main(["--file", str(file_path), "--mode", "lines"])
    captured = capsys.readouterr()
    assert captured.out.strip() == "2"

    # Simulate CLI arguments for char count
    wordcount.main(["--file", str(file_path), "--mode", "chars"])
    captured = capsys.readouterr()
    assert captured.out.strip() == str(len(file_content))
