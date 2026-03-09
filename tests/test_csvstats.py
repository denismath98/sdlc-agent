import subprocess
import sys
import tempfile

import pytest

from src.csvstats import analyze_csv_numbers


def write_temp(content: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return tmp.name


def test_simple_file():
    path = write_temp("1\n2\n3\n")
    result = analyze_csv_numbers(path)
    assert result["count"] == 3
    assert result["sum"] == 6
    assert result["mean"] == 2
    assert result["min"] == 1
    assert result["max"] == 3


def test_float_values():
    path = write_temp("1.5\n2.5\n")
    result = analyze_csv_numbers(path)
    assert result["count"] == 2
    assert result["sum"] == 4.0
    assert result["mean"] == 2.0
    assert result["min"] == 1.5
    assert result["max"] == 2.5


def test_empty_lines():
    path = write_temp("1\n\n2\n\n")
    result = analyze_csv_numbers(path)
    assert result["count"] == 2
    assert result["sum"] == 3
    assert result["mean"] == 1.5
    assert result["min"] == 1
    assert result["max"] == 2


def test_invalid_lines():
    path = write_temp("1\nabc\n2\n")
    result = analyze_csv_numbers(path)
    assert result["count"] == 2
    assert result["sum"] == 3
    assert result["mean"] == 1.5
    assert result["min"] == 1
    assert result["max"] == 2


def test_no_valid_numbers():
    path = write_temp("abc\nxyz\n")
    result = analyze_csv_numbers(path)
    assert result["count"] == 0
    assert result["sum"] == 0
    assert result["mean"] == 0
    assert result["min"] == 0
    assert result["max"] == 0


def test_single_element():
    path = write_temp("5\n")
    result = analyze_csv_numbers(path)
    assert result["count"] == 1
    assert result["sum"] == 5
    assert result["mean"] == 5
    assert result["min"] == 5
    assert result["max"] == 5


def test_cli_output():
    path = write_temp("1\n2\n3\n")
    completed = subprocess.run(
        [sys.executable, "-m", "src.csvstats", "--file", path],
        capture_output=True,
        text=True,
        check=True,
    )
    output_lines = completed.stdout.strip().splitlines()
    expected = [
        "count=3",
        "sum=6",
        "mean=2",
        "min=1",
        "max=3",
    ]
    assert output_lines == expected
