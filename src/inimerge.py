import argparse
import sys
from pathlib import Path
from typing import Dict, List


def parse_ini(path: str) -> Dict[str, str]:
    """Parse a simple INI‑like file into a dictionary.

    Lines starting with ``#`` or empty lines are ignored.
    Only the last occurrence of a key is kept.
    """
    result: Dict[str, str] = {}
    file_path = Path(path)
    if not file_path.is_file():
        return result
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        result[key] = value.strip()
    return result


def merge_ini(base_path: str, override_path: str) -> Dict[str, str]:
    """Merge two INI files, giving precedence to ``override_path``."""
    base = parse_ini(base_path)
    override = parse_ini(override_path)
    merged = base.copy()
    merged.update(override)
    return merged


def validate_config(data: Dict[str, str]) -> List[str]:
    """Validate configuration dictionary.

    Returns a list of error messages; empty list means the config is valid.
    """
    errors: List[str] = []

    if "port" in data:
        port_str = data["port"].strip()
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                errors.append("port must be between 1 and 65535")
        except ValueError:
            errors.append("port must be an integer")

    if "debug" in data:
        debug_val = data["debug"].strip().lower()
        if debug_val not in {"true", "false"}:
            errors.append("debug must be true or false")

    if "host" in data:
        host_val = data["host"].strip()
        if not host_val:
            errors.append("host must not be empty")

    return errors


def _print_config(config: Dict[str, str]) -> None:
    for key in sorted(config):
        print(f"{key}={config[key]}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Merge and validate INI files.")
    parser.add_argument("--base", required=True, help="Path to base INI file")
    parser.add_argument("--override", required=True, help="Path to overriding INI file")
    args = parser.parse_args(argv)

    merged = merge_ini(args.base, args.override)
    errors = validate_config(merged)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    _print_config(merged)


if __name__ == "__main__":
    main()
