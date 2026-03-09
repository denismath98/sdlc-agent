import argparse
import sys
from pathlib import Path

from .models import Task, validate_task_dict
from .storage import load_tasks, save_tasks, summarize_tasks


def _print_errors(errors: list[str]) -> None:
    for err in errors:
        print(err, file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(prog="tasktracker")
    parser.add_argument("--file", required=True, help="Path to tasks JSON file")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--report", action="store_true", help="Show summary")
    mode_group
