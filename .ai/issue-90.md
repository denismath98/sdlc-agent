# Add CLI tool for word count

Что нужно сделать:
• добавить модуль src/wordcount.py с функциями:
• count_words(text: str) -> int
• count_lines(text: str) -> int
• count_chars(text: str) -> int
• добавить CLI python -m src.wordcount --file path --mode words|lines|chars
• добавить тесты (pytest) минимум на:
• empty string
• multiple spaces
• trailing newline
• обновить README коротким примером запуска

Generated: 2026-01-30 17:05:25.625717