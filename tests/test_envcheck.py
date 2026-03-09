import subprocess
import sys
from pathlib import Path

import pytest

from src.envcheck import parse_env, validate_env, check_env


def write_env(tmp_path: Path, content: str) -> Path:
    file_path = tmp_path / ".env"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_parse_env_basic():
    content = "KEY=VALUE\nANOTHER=123"
    path = write_env(Path("."), content)  # use current dir for simplicity
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "VALUE", "ANOTHER": "123"}
    assert errors == []


def test_parse_env_ignores_empty_lines():
    content = "KEY=VAL\n\n   \nANOTHER=2"
    path = write_env(Path("."), content)
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "VAL", "ANOTHER": "2"}
    assert errors == []


def test_parse_env_ignores_comments():
    content = "# comment line\nKEY=VAL\n   # another comment\nANOTHER=2"
    path = write_env(Path("."), content)
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "VAL", "ANOTHER": "2"}
    assert errors == []


def test_parse_env_missing_equal():
    content = "KEYVAL\nKEY=VAL"
    path = write_env(Path("."), content)
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "VAL"}
    assert errors == ["line 1: missing '='"]


def test_parse_env_empty_key():
    content = " =value\nKEY=VAL"
    path = write_env(Path("."), content)
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "VAL"}
    assert errors == ["line 1: empty key"]


def test_parse_env_duplicate_keys():
    content = "KEY=first\nKEY=second\nKEY=third"
    path = write_env(Path("."), content)
    vars_dict, errors = parse_env(str(path))
    assert vars_dict == {"KEY": "third"}
    assert errors == []


def test_validate_env_port_range():
    data = {"PORT": "0"}
    errors = validate_env(data)
    assert "PORT: must be between 1 and 65535" in errors


def test_validate_env_port_not_integer():
    data = {"PORT": "abc"}
    errors = validate_env(data)
    assert "PORT: must be an integer" in errors


def test_validate_env_debug_invalid():
    data = {"DEBUG": "yes"}
    errors = validate_env(data)
    assert "DEBUG: must be true or false" in errors


def test_validate_env_host_empty():
    data = {"HOST": ""}
    errors = validate_env(data)
    assert "HOST: must not be empty" in errors


def test_validate_env_timeout_negative():
    data = {"TIMEOUT": "-1"}
    errors = validate_env(data)
    assert "TIMEOUT: must
