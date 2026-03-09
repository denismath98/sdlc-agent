import argparse
import sys

from .models import validate_task_dict, Task
from .storage import load_tasks, save_tasks, summarize_tasks

def main() -> None:
    parser = argparse.ArgumentParser(prog="tasktracker")
    parser.add_argument("--file", required=True, help="Path to tasks JSON file")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--report", action="store_true", help="Print summary")
    mode_group.add_argument("--add", action="store_true", help="Add a new task")

    parser.add_argument("--id", type=int, help="Task ID")
    parser.add_argument("--title", help="Task title")
    parser.add_argument("--status", help="Task status")
    parser.add_argument("--priority", help="Task
