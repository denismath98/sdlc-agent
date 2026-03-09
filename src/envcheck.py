import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def parse_env(path: str) -> Tuple[Dict[str, str], List[str]]:
    env_path = Path(path)
    variables: Dict[str, str] = {}
    errors: List[str] = []
    if not env_path.is_file():
        errors.append(f"File not found: {path}")
        return variables, errors

    with env_path.open(encoding="utf-8") as f:
        for idx, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in line:
                errors.append(f"line {idx}: missing '='")
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                errors.append(f"line {idx}: empty key")
                continue
            variables[key] = value
    return variables, errors


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
        debug_val = data["DEBUG"].lower()
        if debug_val not in {"true", "false"}:
            errors.append("DEBUG: must be true or false")

    if "HOST" in data:
        host_val = data["HOST"]
        if host_val == "":
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
    validation_errors = validate_env(vars_dict) if not parse_errors else []
    all_errors = parse_errors + validation_errors
    return vars_dict, all_errors


def _run_cli() -> None:
    parser = argparse.ArgumentParser(description="Parse and validate .env files")
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the .env file",
    )
    args = parser.parse_args()
    data, errors = check_env(args.file)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    for key in sorted(data):
        print(f"{key}={data[key]}")
    sys.exit(0)


if __name__ == "__main__":
    _run_cli()
