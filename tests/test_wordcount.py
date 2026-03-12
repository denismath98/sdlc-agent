import pathlib

import pytest

from src.wordcount import count_words, count_lines, count_chars, main


@pytest.mark.parametrize(
    "text,exp_words,exp_lines,exp_chars",
    [
        ("",
