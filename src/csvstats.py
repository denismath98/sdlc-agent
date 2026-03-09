import argparse
import sys
from pathlib import Path
from typing import Dict, List


def analyze_csv_numbers(path: str) -> Dict[str, float]:
    numbers: List[float] = []
    file_path = Path(path)
    if not file_path.is_file():
        return {"count": 0, "sum": 0, "mean": 0, "min": 0, "max": 0}
    with file_path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                num = float(stripped)
                numbers.append(num)
            except ValueError:
                continue
    if not numbers:
        return {"count": 0, "sum": 0, "mean": 0, "min": 0, "max": 0}
    count = len(numbers)
    total = sum(numbers)
    mean = total / count
    minimum = min(numbers)
    maximum = max(numbers)
    return {
        "count": count,
        "sum": total,
        "mean": mean,
        "min": minimum,
        "max": maximum,
    }


def _format_value(value):
    if isinstance(value, int):
        return str(value)
    if value.is_integer():
        return str(int(value))
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a single‑column CSV of numbers."
    )
    parser.add_argument("--file", required=True, help="Path to the CSV file")
    args = parser.parse_args()
    result = analyze_csv_numbers(args.file)
    print(f"count={_format_value(result['count'])}")
    print(f"sum={_format_value(result['sum'])}")
    print(f"mean={_format_value(result['mean'])}")
    print(f"min={_format_value(result['min'])}")
    print(f"max={_format_value(result['max'])}")


if __name__ == "__main__":
    main()
