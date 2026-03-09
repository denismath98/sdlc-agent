import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from src.inimerge import parse_ini, merge_ini, validate_config


def write_file(content: str) -> Path:
    fd, path = tempfile.mkstemp(text=True)
    with open(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return Path(path)


def test_parse_ini_basic():
    content = "key1=value1\nkey2 = value2\n"
    path = write_file(content)
    result = parse_ini(str(path))
    assert result == {"key1": "value1", "key2": "value2"}


def test_parse_ini_ignores_empty_lines():
    content = "\nkey=val\n\n"
    path = write_file(content)
    result = parse_ini(str(path))
    assert result == {"key": "val"}


def test_parse_ini_ignores_comments():
    content = "# comment line\nkey=val\n#another comment"
    path = write_file(content)
    result = parse_ini(str(path))
    assert result == {"key": "val"}


def test_parse_ini_last_key_wins():
    content = "key=first\nkey=second\n"
    path = write_file(content)
    result = parse_ini(str(path))
    assert result == {"key": "second"}


def test_parse_ini_ignores_invalid_lines():
    content = "invalid_line_without_equal\nkey=val"
    path = write_file(content)
    result = parse_ini(str(path))
    assert result == {"key": "val"}


def test_merge_ini_overrides():
    base = write_file("a=1\nb=2\n")
    override = write_file("b=3\nc=4\n")
    merged = merge_ini(str(base), str(override))
    assert merged == {"a": "1", "b": "3", "c": "4"}


def test_validate_config_port_range():
    errors = validate_config({"port": "0"})
    assert "port must be between 1 and 65535" in errors


def test_validate_config_port_integer():
    errors = validate_config({"port": "not_an_int"})
    assert "port must be an integer" in errors


def test_validate_config_debug_value():
    errors = validate_config({"debug": "yes"})
    assert "debug must be true or false" in errors


def test_validate_config_host_not_empty():
    errors = validate_config({"host": ""})
    assert "host must not be empty" in errors


def test_cli_valid_output():
    base = write_file("host=localhost\nport=8080\ndebug=false\n")
    override = write_file("debug=true\n")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.inimerge",
            "--base",
            str(base),
            "--override",
            str(override),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Expected merged config: debug=true, host=localhost, port=8080 (sorted)
    expected = "debug=true\nhost=localhost\nport=8080\n"
    assert result.stdout == expected


def test_cli_invalid_errors():
    base = write_file("port=0\n")
    override = write_file("")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.inimerge",
            "--base",
            str(base),
            "--override",
            str(override),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "port must be between 1 and 65535" in result.stderr.strip()
