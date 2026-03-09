from dataclasses import dataclass

ALLOWED_STATUS = {"todo", "in_progress", "done"}
ALLOWED_PRIORITY = {"low", "medium", "high"}


@dataclass
class Task:
    id: int
    title: str
    status: str
    priority: str


def validate_task_dict(data: dict) -> list[str]:
    errors: list[str] = []

    # id validation
    if "id" not in data or not isinstance(data["id"], int):
        errors.append("id: must be integer")

    # title validation
    title = data.get("title")
    if not isinstance(title, str) or title.strip() == "":
        errors.append("title: must be non-empty")

    # status validation
    status = data.get("status")
    if status not in ALLOWED_STATUS:
        errors.append("status: must be one of todo,in_progress,done")

    # priority validation
    priority = data.get("priority")
    if priority not in ALLOWED_PRIORITY:
        errors.append("priority: must be one of low,medium,high")

    return errors
