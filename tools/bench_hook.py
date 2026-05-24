#!/usr/bin/env python3
"""Hook latency benchmark.

Measures the wall-clock time of a full hook invocation across a variety of
input types. Reports p50 / p95 / p99 / max so you can see both the typical
tax and the worst-case outlier.

Run from anywhere:
    python3 tools/bench_hook.py

Optionally:
    python3 tools/bench_hook.py --iterations 200
    python3 tools/bench_hook.py --json   # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent / "better-phrase.sh"


SCENARIOS: list[tuple[str, dict]] = [
    ("empty",          {"prompt": ""}),
    ("pure_chinese",   {"prompt": "你好,这是中文输入,请帮我看下时间安排"}),
    ("english_short",  {"prompt": "hi there"}),                                 # below threshold → skip
    ("english_full",   {"prompt": "how are you today and what should we work on"}),
    ("code_only",      {"prompt": "useState useEffect useMemo reactDOM"}),
    ("mixed_zh_heavy", {"prompt": "Hi Mike, 关于明天的会议我想确认一下时间表能否再调整"}),
    ("mixed_en_heavy", {"prompt": "What time should we meet 我希望下午"}),
    ("long_chinese",   {"prompt": "你好" * 500}),
    ("long_english",   {"prompt": "the quick brown fox jumps over the lazy dog " * 50}),
    ("invalid_json",   "not json {"),
]


def bench_one(payload, iterations: int, env: dict) -> dict:
    times_ms: list[float] = []
    nonzero_exits = 0
    for _ in range(iterations):
        body = payload if isinstance(payload, str) else json.dumps(payload)
        t0 = time.perf_counter()
        try:
            result = subprocess.run(
                [str(HOOK_PATH)],
                input=body,
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
        except subprocess.TimeoutExpired:
            nonzero_exits += 1
            continue
        t1 = time.perf_counter()
        times_ms.append((t1 - t0) * 1000.0)
        if result.returncode != 0:
            nonzero_exits += 1

    if not times_ms:
        return {"error": "no successful runs"}

    times_ms.sort()
    return {
        "n": len(times_ms),
        "min_ms":  round(min(times_ms), 1),
        "p50_ms":  round(statistics.median(times_ms), 1),
        "p95_ms":  round(times_ms[int(len(times_ms) * 0.95)], 1),
        "p99_ms":  round(times_ms[int(len(times_ms) * 0.99)], 1),
        "max_ms":  round(max(times_ms), 1),
        "mean_ms": round(statistics.mean(times_ms), 1),
        "stdev_ms": round(statistics.stdev(times_ms), 1) if len(times_ms) > 1 else 0.0,
        "nonzero_exits": nonzero_exits,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bench_hook")
    parser.add_argument("--iterations", "-n", type=int, default=100,
                        help="Iterations per scenario (default: 100)")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON instead of a table")
    parser.add_argument("--warmup", type=int, default=5,
                        help="Warmup iterations before timing (default: 5)")
    args = parser.parse_args(argv)

    if not HOOK_PATH.is_file():
        print(f"Hook not found: {HOOK_PATH}", file=sys.stderr)
        return 1

    # Isolate config so the bench doesn't disturb the user's real settings.
    tmphome = tempfile.mkdtemp(prefix="bp-bench-")
    env = dict(os.environ)
    env["BETTER_PHRASE_HOME"] = tmphome

    # Warmup so JIT / OS file cache / Python bytecode cache are hot.
    for _ in range(args.warmup):
        subprocess.run(
            [str(HOOK_PATH)],
            input=json.dumps({"prompt": "warmup"}),
            capture_output=True, text=True, timeout=10, env=env,
        )

    results: dict[str, dict] = {}
    for name, payload in SCENARIOS:
        results[name] = bench_one(payload, args.iterations, env)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    # Pretty table.
    cols = ["scenario", "n", "min", "p50", "p95", "p99", "max", "mean", "stdev", "errs"]
    widths = [22, 5, 7, 7, 7, 7, 7, 7, 7, 6]

    def row(values):
        print(" ".join(str(v).ljust(w) for v, w in zip(values, widths)))

    row(cols)
    row(["-" * (w - 1) for w in widths])
    for name, r in results.items():
        row([
            name,
            r.get("n", "—"),
            r.get("min_ms", "—"),
            r.get("p50_ms", "—"),
            r.get("p95_ms", "—"),
            r.get("p99_ms", "—"),
            r.get("max_ms", "—"),
            r.get("mean_ms", "—"),
            r.get("stdev_ms", "—"),
            r.get("nonzero_exits", "—"),
        ])

    print()
    print(f"Iterations per scenario: {args.iterations}  (after {args.warmup} warmups)")
    print(f"Hook: {HOOK_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
