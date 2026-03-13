import os
from typing import Dict


def parse_files_from_llm(text: str) -> Dict[str, str]:
    files: Dict[str, str] = {}
    current_path = None
    buffer = []

    for line in text.splitlines():
        if line.startswith("FILE: "):
            if current_path:
                files[current_path] = "\n".join(buffer).rstrip() + "\n"
            current_path = line.replace("FILE: ", "").strip()
            buffer = []
        else:
            buffer.append(line)

    if current_path:
        files[current_path] = "\n".join(buffer).rstrip() + "\n"

    return files


def write_files(files: Dict[str, str]) -> None:
    for path, content in files.items():
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
