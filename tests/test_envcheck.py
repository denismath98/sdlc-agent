import subprocess
import sys
import os
import tempfile
from pathlib import Path

import pytest

from src.envcheck import parse_env, validate_env, check_env


def write_env(content: str) -> Path:
    fd, path = tempfile.mkstemp()
    os.close(fd)
    Path(path).write_text(content, encoding="utf-8")
    return Path(path)


def test_parse_env_basic():
    p = write_env("KEY=VALUE\n")
    env, errors = parse_env(str(p))
    assert env == {"KEY": "VALUE"}
    assert errors == []


def test_parse_env_ignores_empty_lines():
    p = write_env("\nKEY=VAL\n\n")
    env, errors = parse_env(str(p))
    assert env == {"KEY": "VAL"}
    assert errors == []


def test_parse_env_ignores_comments():
    p = write_env("# comment\nKEY=VAL\n  # another\n")
    env, errors = parse_env(str(p))
    assert env == {"KEY": "VAL"}
    assert errors == []


def test_parse_env_missing_equal():
    p = write_env("INVALID\n")
    env, errors = parse_env(str(p))
    assert env == {}
    assert errors == ["1 : missing '='"]


def test_parse_env_empty_key():
    p = write_env(" =value\n")
    env, errors = parse_env(str(p))
    assert env == {}
    assert errors == ["1 : empty key"]


def test_parse_env_duplicate_keys():
    p = write_env("A=1\nA=2\n")
    env, errors = parse_env(str(p))
    assert env == {"A": "2"}
    assert errors == []


def test_validate_env_port_zero():
    errors = validate_env({"PORT": "
