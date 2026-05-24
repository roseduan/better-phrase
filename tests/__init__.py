"""Test package init.

Adds the repo root to sys.path so `from better_phrase.* import ...` works
without requiring `pip install -e .`.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_repo_str = str(_REPO_ROOT)
if _repo_str not in sys.path:
    sys.path.insert(0, _repo_str)
