import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional

VALID_LEVELS = {"INFO", "WARN", "ERROR"}
LEVEL_ORDER = ["INFO", "WARN", "ERROR"]


def parse_log(path: str) -> Tuple[List[Tuple[str, str]], List[str]]:
    entries: List[Tuple[str, str]] = []
    errors: List[str] = []
    file_path = Path(path)

    with file_path.open(encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.lstrip().startswith("#"):
                continue

            if "|" not in line:
                errors.append(f"line {line_no}: missing separator")
                continue

            level_part, message_part = line.split("|", 1)
            level = level_part.strip()
            message = message_part.strip()

            if level not in VALID_LEVELS:
                errors.append(f"line {line_no}: invalid level")
                continue

            if not message:
                errors.append(f"line {line_no}: empty message")
                continue

            entries.append((level, message))

    return entries, errors


def summarize_log(entries: List[Tuple[str, str]]) -> Dict[str, int]:
    summary = {lvl: 0 for lvl in VALID_LEVELS}
    for level, _ in entries:
        summary[level] += 1
    total = sum(summary.values())
    summary["TOTAL"] = total
    # Ensure fixed order in output functions
    return summary


def filter_entries(
    entries: List[Tuple[str, str]], min_level: Optional[str]
) -> List[Tuple[str, str]]:
    if min_level is None:
        return entries
    if min_level not in VALID_LEVELS:
        return entries
    min_index = LEVEL_ORDER.index(min_level)
    return [(lvl, msg) for lvl, msg in entries if LEVEL_ORDER.index(lvl) >= min_index]


def build_output(entries: List[Tuple[str, str]]) -> str:
    summary = summarize_log(entries)
    lines = [
        f"INFO={summary.get('INFO', 0)}",
        f"WARN={summary.get('WARN', 0)}",
        f"ERROR={summary.get('ERROR', 0)}",
        f"TOTAL={summary.get('TOTAL', 0)}",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Log summarizer utility")
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the log file",
    )
    parser.add_argument(
        "--min-level",
        choices=["INFO", "WARN", "ERROR"],
        help="Minimum log level to include",
    )
    args = parser.parse_args()

    entries, errors = parse_log(args.file)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    filtered = filter_entries(entries, args.min_level)
    output = build_output(filtered)
    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
