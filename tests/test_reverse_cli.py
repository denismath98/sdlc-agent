import subprocess
import sys
from pathlib import Path


def test_cli_reverse():
    result = subprocess.run(
        [sys.executable, "-m", "src.reverse", "--text", "abc"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "reversed=cba"
