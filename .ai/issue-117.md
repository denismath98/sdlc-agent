# Add text normalizer utility with CLI

Добавить модуль src/normalize.py с функцией:

normalize_spaces(text: str) -> str
- заменить последовательности пробелов и табов одним пробелом
- убрать пробелы в начале и в конце строки
- переносы строк сохранять как есть
- пустая строка остается пустой

Добавить CLI:
python -m src.normalize --text "..."

Вывод:
normalized=<result>

Тесты tests/test_normalize.py минимум 5:
- "" -> ""
- "  hello   world  " -> "hello world"
- "a\t\tb" -> "a b"
- "a\n   b" -> "a\n b"
- "   " -> ""

Код должен проходить black и pytest.

Generated: 2026-03-09 17:42:01.412252