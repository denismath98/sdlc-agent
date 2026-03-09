import pytest
from src.reverse import reverse_text


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("abc", "cba"),
        ("Hello", "olleH"),
        ("", ""),
        ("ab cd", "dc ba"),
        ("🙂a", "a🙂"),
    ],
)
def test_reverse_text(input_text, expected):
    assert reverse_text(input_text) == expected
