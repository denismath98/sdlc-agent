import re
from pathlib import Path


def extract_context_file_paths(issue_text: str) -> list[str]:
    """
    Извлекает пути файлов из текста issue.
    Ищет пути вида:
    - src/...py
    - tests/...py
    """
    if not issue_text:
        return []

    matches = re.findall(r"(?:src|tests)/[A-Za-z0-9_\-/]+\.py", issue_text)

    result: list[str] = []
    seen: set[str] = set()

    for path in matches:
        if path not in seen:
            seen.add(path)
            result.append(path)

    return result


def read_context_files(paths: list[str], max_chars_per_file: int = 4000) -> str:
    """
    Читает содержимое файлов и собирает единый контекстный блок.
    """
    blocks: list[str] = []

    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        content = content.strip()
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + "\n...[TRUNCATED]..."

        blocks.append(f"Файл: {raw_path}\n```python\n{content}\n```")

    return "\n\n".join(blocks)