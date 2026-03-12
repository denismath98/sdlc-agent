"""
src package initialization.
Exports word count utilities.
"""

from .wordcount import count_words, count_lines, count_chars

__all__ = ["count_words", "count_lines", "count_chars"]
