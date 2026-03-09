# Add task tracker package with storage, reporting and CLI

Нужно добавить небольшой task tracker.

Структура:

src/tasktracker/models.py
src/tasktracker/storage.py
src/tasktracker/cli.py
Если действительно нужно для импорта/запуска, добавить src/tasktracker/init.py.

Модель задачи

В models.py реализовать dataclass Task:

id: int
title: str
status: str
priority: str
Ограничения:

status может быть только: todo, in_progress, done
priority может быть только: low, medium, high
Также реализовать функцию:

validate_task_dict(data: dict) -> list[str]

Она принимает словарь и возвращает список ошибок.

Ошибки строго:

id: must be integer
title: must be non-empty
status: must be one of todo,in_progress,done
priority: must be one of low,medium,high
Если ошибок нет, вернуть [].

Хранилище

В storage.py реализовать функции:

load_tasks(path: str) -> tuple[list[Task], list[str]]
Файл хранится в JSON и содержит список объектов.

Требования:

если файл не существует, вернуть ([], [])
если JSON невалидный, вернуть ([], ["file: invalid json"])
если корневой элемент не список, вернуть ([], ["file: root must be a list"])
каждую запись валидировать через validate_task_dict
ошибки для невалидных записей строго:
item :
где N — индекс элемента в списке, начиная с 0
невалидные записи не включать в итоговый список Task
валидные записи загружать
save_tasks(path: str, tasks: list[Task]) -> None
сохраняет список задач в JSON
JSON должен быть pretty-printed with indent=2
порядок полей в объекте:
id, title, status, priority
summarize_tasks(tasks: list[Task]) -> dict[str, int]
Возвращает:
{
"todo": ,
"in_progress": ,
"done": ,
"total":
}

CLI

В cli.py реализовать запуск:

python -m src.tasktracker.cli --file tasks.json --report
python -m src.tasktracker.cli --file tasks.json --add --id 1 --title "Task" --status todo --priority high

Поддерживаемые режимы:

--report
загружает задачи
если есть ошибки загрузки:
печатает ошибки в stderr
exit code 1
stdout пустой
если ошибок нет:
печатает summary в stdout строго в формате:
todo=
in_progress=
done=
total=

exit code 0
--add
добавляет одну задачу в файл
обязательные аргументы:
--id
--title
--status
--priority
сначала загружает существующие задачи
если есть ошибки загрузки:
печатает ошибки в stderr
exit code 1
если новая задача невалидна:
печатает ошибки в stderr
exit code 1
если уже существует задача с таким id:
печатает строго:
id: already exists
в stderr
exit code 1
иначе:
добавляет задачу
сохраняет файл
ничего не печатает
exit code 0
Дополнительно:

режимы --report и --add взаимоисключающие
использовать только стандартную библиотеку Python
Тесты

Добавить tests/test_tasktracker_models.py
Добавить tests/test_tasktracker_storage.py
Добавить tests/test_tasktracker_cli.py

Нужно минимум 16 тестов, включая:

Models:

validate_task_dict принимает валидную задачу
validate_task_dict ловит невалидный id
validate_task_dict ловит пустой title
validate_task_dict ловит невалидный status
validate_task_dict ловит невалидный priority
Storage:
6. load_tasks возвращает [] если файла нет
7. load_tasks сообщает file: invalid json
8. load_tasks сообщает file: root must be a list
9. load_tasks пропускает невалидные записи и возвращает ошибки item N: ...
10. save_tasks сохраняет JSON с indent=2
11. summarize_tasks считает корректно

CLI:
12. --report печатает summary для валидного файла
13. --report при ошибках загрузки печатает stderr и exit code 1
14. --add добавляет валидную задачу
15. --add отклоняет duplicate id с ошибкой id: already exists
16. --add отклоняет невалидную задачу с сообщениями validate_task_dict
17. --report и --add не должны работать одновременно

Дополнительные требования:

black должен проходить
pytest должен проходить
не добавлять лишние зависимости
не менять существующие workflow-файлы без необходимости

Generated: 2026-03-09 20:36:58.853768