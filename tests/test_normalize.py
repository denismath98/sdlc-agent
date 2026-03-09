import pytest
from src.normalize import normalize_spaces


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("", ""),
        ("  hello   world  ", "hello world"),
        ("a\t\tb", "a b"),
        ("a\n   b", "a\nb"),
        ("   ", ""),
    ],
)
def test_normalize_spaces(input_text, expected):
    assert normalize_spaces(input_text) == expected
