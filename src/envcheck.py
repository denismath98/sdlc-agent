import argparse
import sys
from typing import Dict, List, Tuple


def parse_env(path: str) -> Tuple[Dict[str, str], List[str]]:
    vars_dict: Dict[str, str] = {}
    errors: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for idx, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if "=" not in line:
                errors.append(f"line {idx}: missing '='")
                continue
            key_part, value_part = line.split("=", 1)
            key = key_part.strip()
            value = value_part.strip()
            if key == "":
                errors.append(f"line {idx}: empty key")
                continue
            vars_dict[key] = value
    return vars_dict, errors


def validate_env(data: Dict[str, str]) -> List[str]:
    errors: List[str] = []
    if "PORT" in data:
        port_str = data["PORT"]
        try:
            port = int(port_str)
        except ValueError:
            errors.append("PORT: must be an integer")
        else:
            if not (1 <= port <= 65535):
                errors.append("PORT: must be between 1 and 65535")
    if "DEBUG" in data:
        debug = data["DEBUG"].lower()
        if debug not in ("true", "false"):
            errors.append("DEBUG: must be true or false")
    if "HOST" in data:
        if data["HOST"] == "":
            errors.append("HOST: must not be empty")
    if "TIMEOUT" in data:
        timeout_str = data["TIMEOUT"]
        try:
            timeout = int(timeout_str)
        except ValueError:
            errors.append("TIMEOUT: must be an integer")
        else:
            if timeout < 0:
                errors.append("TIMEOUT: must be >= 0")
    return errors


def check_env(path: str) -> Tuple[Dict[str, str], List[str]]:
    vars_dict, parse_errors = parse_env(path)
    validation_errors = validate_env(vars_dict)
    all_errors = parse_errors + validation_errors
    return vars_dict, all_errors


def _print_errors(errors: List[str]) -> None:
    for err in errors:
        print(err, file=sys.stderr)


def _print_vars(vars_dict: Dict[str, str]) -> None:
    for key in sorted(vars_dict):
        print(f"{key}={vars_dict[key]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse and validate .env files")
    parser.add_argument("--file", required=True, help="Path to .env file")
    args = parser.parse_args()
    vars_dict, errors = check_env(args.file)
    if errors:
        _print_errors(errors)
        sys.exit(1)
    _print_vars(vars_dict)
    sys.exit(0)


if __name__ == "__main__":
    main()
