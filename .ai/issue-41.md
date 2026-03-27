# Issue 41

## Title
Add add() utility function with tests

## Body
Please implement a tiny utility.

1) Create src/utils.py with:
def add(a: int, b: int) -> int:
    return a + b

2) Create tests/test_utils.py with pytest test:
from src.utils import add

def test_add():
    assert add(2, 3) == 5

Notes:
- Ensure src is importable (add src/__init__.py if needed)
- CI must pass

## Generated
2026-01-30T10:34:16.836808Z
