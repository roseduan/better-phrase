from __future__ import annotations

import os
import sys
import time

# Capture invocation time as early as possible so the displayed hook overhead
# includes module imports + routing + JSON serialization. Process-level Python
# interpreter startup (~30ms) is still excluded — that cost predates the
# interpreter even reaching this file.
os.environ.setdefault("BP_HOOK_START_NS", str(time.perf_counter_ns()))

from .cli import main  # noqa: E402  (intentional: capture time first)

if __name__ == "__main__":
    sys.exit(main())
