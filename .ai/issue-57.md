# Issue 57

## Title
Add add() utility function with tests

## Body
Please implement a tiny utility.

Create src/utils.py with:
def add(a: int, b: int) -> int:
return a + b

Create tests/test_utils.py with pytest test:
from src.utils import add

def test_add():
assert add(2, 3) == 5

Notes:

Ensure src is importable (add src/init.py if needed)
CI must pass

## Generated
2026-01-30T13:05:40.706705Z
