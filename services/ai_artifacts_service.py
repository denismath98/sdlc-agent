import os
from datetime import datetime

AI_DIR = ".ai"


def ensure_ai_dir() -> None:
    os.makedirs(AI_DIR, exist_ok=True)


def write_issue_artifact(issue_number: int, title: str, body: str) -> str:
    ensure_ai_dir()
    path = f"{AI_DIR}/issue-{issue_number}.md"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{body}\n\nGenerated: {datetime.utcnow()}")

    return path
