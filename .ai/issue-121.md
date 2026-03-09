# Add reverse string utility

Создать модуль src/reverse.py

Функция:
reverse_text(text: str) -> str

Требования:

вернуть строку в обратном порядке
не менять регистр
поддерживать unicode
CLI:
python -m src.reverse --text "abc"

Вывод:
reversed=cba

Тесты:

"abc" -> "cba"
"Hello" -> "olleH"
"" -> ""
"ab cd" -> "dc ba"
"🙂a" -> "a🙂"
Код должен проходить black и pytest.

Generated: 2026-03-09 18:45:37.720439