"""Pytest bootstrap.

Running `pytest` directly does NOT put the project root on Python's module
search path (unlike `python -m pytest`, which does). This file makes the root
importable so tests can do `from src.config... import ...` either way.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
