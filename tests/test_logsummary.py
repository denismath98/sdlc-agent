import subprocess
import sys
from pathlib import Path

import pytest

from src.logsummary import (
    parse_log,
    summarize_log,
    filter_entries,
    build_output,
)


@pytest.fixture
def create_log_file(tmp_path):
    def _create(content: str) -> Path:
        file_path = tmp_path / "test.log"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return _create


def test_parse_log_valid_entries(create_log_file):
    path = create_log_file("INFO|service started\nWARN|retrying\nERROR|failed")
    entries, errors = parse_log(str(path))
    assert entries == [
        ("INFO", "service started"),
        ("WARN", "retrying"),
        ("ERROR", "failed"),
    ]
    assert errors == []


def test_parse_log_ignores_empty_lines(create_log_file):
    path = create_log_file("\nINFO|msg\n\nWARN|msg2\n")
    entries, errors = parse_log(str(path))
    assert len(entries) == 2
    assert not errors


def test_parse_log_ignores_comments(create_log_file):
    path = create_log_file("# this is a comment\nINFO|msg\n#another comment")
    entries, errors = parse_log(str(path))
    assert entries == [("INFO", "msg")]
    assert not errors


def test_parse_log_missing_separator(create_log_file):
    path = create_log_file("INFO service started")
    entries, errors = parse_log(str(path))
    assert entries == []
    assert errors == ["line 1: missing separator"]


def test_parse_log_invalid_level(create_log_file):
    path = create_log_file("DEBUG|something")
    entries, errors = parse_log(str(path))
    assert entries == []
    assert errors == ["line 1: invalid level"]


def test_parse_log_empty_message(create_log_file):
    path = create_log_file("INFO|   ")
    entries, errors = parse_log(str(path))
    assert entries == []
    assert errors == ["line 1: empty message"]


def test_parse_log_trims_spaces(create_log_file):
    path = create_log_file("  INFO  |  hello world  ")
    entries, errors = parse_log(str(path))
    assert entries == [("INFO", "hello world")]
    assert not errors
