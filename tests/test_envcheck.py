import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from src.envcheck import parse_env, validate_env, check_env


def write_temp(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def test_parse_env_basic():
    path = write_temp("KEY=VALUE\n")
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "VALUE"}
    assert errors == []


def test_parse_env_ignores_empty_lines():
    path = write_temp("\nKEY=VAL\n\n")
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "VAL"}
    assert errors == []


def test_parse_env_ignores_comments():
    path = write_temp("# comment\nKEY=VAL\n   # another\n")
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "VAL"}
    assert errors == []


def test_parse_env_missing_equal():
    path = write_temp("INVALID_LINE\n")
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {}
    assert errors == ["line 1: missing '='"]


def test_parse_env_empty_key():
    path = write_temp("   =value\n")
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {}
    assert errors == ["line 1: empty key"]


def test_parse_env_last_key_wins():
    path = write_temp("KEY=first\nKEY=second\n")
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "second"}
    assert errors == []


def test_validate_env_port_zero():
    errors = validate_env({"PORT": "0"})
    assert "PORT: must be between 1 and 65535" in errors
    assert "PORT: must be an integer" not in errors


def test_validate_env_port_non_int():
    errors = validate_env({"PORT": "abc"})
    assert "PORT: must be an integer" in errors
    assert "PORT: must be between 1 and 65535" not in errors


def test_validate_env_debug_invalid():
    errors = validate_env({"DEBUG": "yes"})
    assert errors == ["DEBUG: must be true or false"]


def test_validate_env_host_empty():
    errors = validate_env({"HOST": ""})
    assert errors == ["HOST: must not be empty"]


def test_validate_env_timeout_negative():
    errors = validate_env({"TIMEOUT": "-1"})
    assert errors == ["TIMEOUT: must be >= 0"]


def test_cli_valid_output():
    content = "HOST=localhost\nPORT=8080\nDEBUG=true\n"
    path = write_temp(content)
    result = subprocess.run(
        [sys.executable, "-m", "src.envcheck", "--file", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    expected = "DEBUG=true\nHOST=localhost\nPORT=8080\n"
    assert result.stdout == expected
    assert result.stderr == ""


def test_cli_invalid_output():
    content = "HOST=\nPORT=0\nDEBUG=maybe\n"
    path = write_temp(content)
    result = subprocess.run(
        [sys.executable, "-m", "src.envcheck", "--file", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    # Errors should be in order: parsing none, then validation
    expected_errors = [
        "HOST: must not be empty",
        "PORT: must be between 1 and 65535",
        "DEBUG: must be true or false",
    ]
    assert result.stderr.strip().splitlines() == expected_errors
    assert result.stdout == ""


def test_cli_parsing_and_validation_order():
    content = "BADLINE\nHOST=\nPORT=abc\n"
    path = write_temp(content)
    result = subprocess.run(
        [sys.executable, "-m", "src.envcheck", "--file", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    # Parsing errors first, then validation (HOST empty, PORT int)
    expected = [
        "line 1: missing '='",
        "line 2: empty key",
        "HOST: must not be empty",
        "PORT: must be an integer",
    ]
    assert result.stderr.strip().splitlines() == expected
    assert result.stdout == ""


def test_check_env_combined():
    content = "KEY=val\nPORT=65536\n"
    path = write_temp(content)
    data, errors = check_env(str(path))
    assert data == {"KEY": "val", "PORT": "65536"}
    assert errors == ["PORT: must be between 1 and 65535"]
