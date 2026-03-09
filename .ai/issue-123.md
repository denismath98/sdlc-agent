# Add CSV statistics utility with CLI

Добавить модуль src/csvstats.py.

Функциональность:

Функция:
analyze_csv_numbers(path: str) -> dict

CSV-файл содержит одну колонку чисел (целых или float).

Функция должна вернуть:

{
  "count": <количество значений>,
  "sum": <сумма>,
  "mean": <среднее>,
  "min": <минимум>,
  "max": <максимум>
}

Требования:

- игнорировать пустые строки
- игнорировать строки, содержащие нечисловые значения
- поддерживать float
- если валидных чисел нет → вернуть count=0 и остальные значения = 0

CLI:

python -m src.csvstats --file data.csv

Вывод строго:

count=<n>
sum=<value>
mean=<value>
min=<value>
max=<value>

Пример:

CSV:
1
2
3

Вывод:

count=3
sum=6
mean=2
min=1
max=3

---

Тесты (tests/test_csvstats.py) минимум 7:

1️⃣ простой файл

1
2
3

→ count=3 sum=6 mean=2 min=1 max=3

---

2️⃣ float

1.5
2.5

→ mean=2.0

---

3️⃣ пустые строки

1

2

→ count=2

---

4️⃣ невалидные строки

1
abc
2

→ abc игнорируется

---

5️⃣ файл без валидных чисел

abc
xyz

→ count=0
→ sum=0
→ mean=0
→ min=0
→ max=0

---

6️⃣ один элемент

5

→ mean=5

---

7️⃣ CLI тест

pytest должен запускать CLI и проверять вывод.

---

Код должен:

- проходить pytest
- проходить black
- использовать только стандартную библиотеку Python

Generated: 2026-03-09 18:49:01.772205