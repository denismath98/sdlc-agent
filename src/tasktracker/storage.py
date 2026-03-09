import json
from pathlib import Path
from typing import List, Tuple

from .models import Task, validate_task_dict


def load_tasks(path: str) -> Tuple[List[Task], List[str]]:
    file_path = Path(path)
    if not file_path.exists():
        return [], []

    try:
        raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [], ["file: invalid json"]

    if not isinstance(raw_data, list):
        return [], ["file: root must be a list"]

    tasks: List[Task] = []
    errors: List[str] = []

    for idx, item in enumerate(raw_data):
        if not isinstance(item, dict):
            errors.append(f"item {idx}: invalid format")
            continue

        item_errors = validate_task_dict(item)
        if item_errors:
            errors.append(f"item {idx}: {'; '.join(item_errors)}")
        else:
            tasks.append(Task(**item))

    return tasks, errors


def save_tasks(path: str, tasks: List[Task]) -> None:
    data = [
        {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
        }
        for task in tasks
    ]
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def summarize_tasks(tasks: List[Task]) -> dict[str, int]:
    summary = {"todo": 0, "in_progress": 0, "done": 0}
    for task in tasks:
        if task.status in summary:
            summary[task.status] += 1
    summary["total"] = sum(summary.values())
    return summary
