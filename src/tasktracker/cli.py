import argparse
import sys
from pathlib import Path

from .models import Task, validate_task_dict
from .storage import load_tasks, save_tasks, summarize_tasks


def _print_errors(errors):
    for err in errors:
        print(err, file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(prog="tasktracker")
    parser.add_argument("--file", required=True, help="Path to tasks JSON file")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--report", action="store_true", help="Print summary of tasks"
    )
    mode_group.add_argument(
        "--add", action="store_true", help="Add a new task to the file"
    )

    parser.add_argument("--id", type=int, help="Task ID")
    parser.add_argument("--title", help="Task title")
    parser.add_argument("--status", help="Task status")
    parser.add_argument("--priority", help="Task priority")

    args = parser.parse_args()

    file_path = args.file

    if args.report:
        tasks, errors = load_tasks(file_path)
        if errors:
            _print_errors(errors)
            sys.exit(1)
        summary = summarize_tasks(tasks)
        print(f"todo={summary['todo']}")
        print(f"in_progress={summary['in_progress']}")
        print(f"done={summary['done']}")
        print(f"total={summary['total']}")
        sys.exit(0)

    # --add mode
    # Ensure required fields are present
    missing = []
    for field in ("id", "title", "status", "priority"):
        if getattr(args, field) is None:
            missing.append(f"--{field}")
    if missing:
        parser.error(f"the following arguments are required: {', '.join(missing)}")

    tasks, load_errors = load_tasks(file_path)
    if load_errors:
        _print_errors(load_errors)
        sys.exit(1)

    new_task_dict = {
        "id": args.id,
        "title": args.title,
        "status": args.status,
        "priority": args.priority,
    }

    validation_errors = validate_task_dict(new_task_dict)
    if validation_errors:
        _print_errors(validation_errors)
        sys.exit(1)

    if any(t.id == args.id for t in tasks):
        print("id: already exists", file=sys.stderr)
        sys.exit(1)

    tasks.append(Task(**new_task_dict))
    save_tasks(file_path, tasks)
    sys.exit(0)


if
