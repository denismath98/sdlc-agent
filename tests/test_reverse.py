from src.reverse import reverse_text


def test_reverse_basic():
    assert reverse_text("abc") == "cba"


def test_reverse_mixed_case():
    assert reverse_text("Hello") == "olleH"


def test_reverse_empty():
    assert reverse_text("") == ""


def test_reverse_with_space():
    assert reverse_text("ab cd") == "dc ba"


def test_reverse_unicode():
    assert reverse_text("🙂a") == "a🙂"
