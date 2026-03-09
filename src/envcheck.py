import sys
import argparse
from typing import Tuple, Dict, List


def parse_env(path: str) -> Tuple[Dict[str, str], List[str]]:
    env: Dict[str, str] = {}
    errors: List[str] = []
    with open(path, encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.lstrip().startswith("#"):
                continue
            if "=" not in line:
                errors.append(f"{lineno} : missing '='")
                continue
            key_part, value_part = line.split("=", 1)
            key = key_part.strip()
            value = value_part.strip()
            if key == "":
                errors.append(f"{lineno} : empty key")
                continue
            env[key] = value
    return env, errors


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
        if data["HOST"].strip() == "":
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
    env, parse_errors = parse_env(path)
    validation_errors = validate_env(env)
    return env, parse_errors + validation_errors


def _run_cli() -> None:
    parser = argparse.ArgumentParser(description="Parse and validate .env files")
    parser.add_argument("--file", required=True, help="Path to .env file")
    args = parser.parse_args()
    env, errors = check_env(args.file)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)
    for key in sorted(env.keys()):
        print(f"{key}={env[key]}")
    sys.exit(0)


if __name__ == "__main__":
    _run_cli()
