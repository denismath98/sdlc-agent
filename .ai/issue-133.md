# Add log summarizer utility with filtering, validation and CLI

Добавить модуль src/logsummary.py.

Нужно реализовать утилиту для анализа текстового лог-файла.

Каждая строка лога имеет формат:

LEVEL|message

Примеры:
INFO|service started
ERROR|database unavailable
WARN|retrying request

Допустимые LEVEL:
- INFO
- WARN
- ERROR

Требуется реализовать функции:

1. parse_log(path: str) -> tuple[list[tuple[str, str]], list[str]]
   Возвращает:
   - список валидных записей в виде (level, message)
   - список ошибок парсинга

   Правила:
   - пустые строки игнорируются
   - строки, начинающиеся с #, считаются комментариями и игнорируются
   - если в строке нет символа | → ошибка:
     line <N>: missing separator
   - если level не один из INFO/WARN/ERROR → ошибка:
     line <N>: invalid level
   - если message после trim пустой → ошибка:
     line <N>: empty message
   - пробелы вокруг level и message нужно обрезать
   - ошибки должны сохраняться в порядке появления строк

2. summarize_log(entries: list[tuple[str, str]]) -> dict[str, int]
   Возвращает словарь:
   {
     "INFO": <count>,
     "WARN": <count>,
     "ERROR": <count>,
     "TOTAL": <count>
   }

3. filter_entries(entries: list[tuple[str, str]], min_level: str | None) -> list[tuple[str, str]]
   Если min_level:
   - INFO → вернуть все записи
   - WARN → вернуть WARN и ERROR
   - ERROR → вернуть только ERROR
   Если min_level is None → вернуть все записи

4. build_output(entries: list[tuple[str, str]]) -> str
   Формат вывода строго такой:

   INFO=<n>
   WARN=<n>
   ERROR=<n>
   TOTAL=<n>

CLI:
python -m src.logsummary --file app.log [--min-level INFO|WARN|ERROR]

Поведение CLI:
- сначала парсит файл
- если есть ошибки парсинга:
  - печатает ошибки в stderr
  - exit code 1
  - stdout должен быть пустым
- если ошибок нет:
  - применяет filter_entries
  - печатает build_output(...) в stdout
  - exit code 0

Тесты: tests/test_logsummary.py
Нужно минимум 14 тестов, включая:

1. parse_log читает валидные INFO/WARN/ERROR строки
2. parse_log игнорирует пустые строки
3. parse_log игнорирует комментарии
4. parse_log сообщает line N: missing separator
5. parse_log сообщает line N: invalid level
6. parse_log сообщает line N: empty message
7. parse_log обрезает пробелы вокруг level и message
8. summarize_log считает корректные количества
9. filter_entries(INFO) возвращает все записи
10. filter_entries(WARN) возвращает WARN и ERROR
11. filter_entries(ERROR) возвращает только ERROR
12. CLI при валидном файле печатает корректную summary
13. CLI с --min-level WARN печатает summary только по WARN и ERROR
14. CLI при ошибках печатает stderr и завершает процесс с кодом 1
15. При нескольких ошибках парсинга порядок ошибок должен совпадать с порядком строк

Дополнительные требования:
- использовать только стандартную библиотеку Python
- код должен проходить black
- __init__.py добавлять только если действительно нужно
- не добавлять лишние зависимости

Generated: 2026-03-09 19:27:11.025340