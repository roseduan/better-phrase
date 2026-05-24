"""UserPromptSubmit hook handler.

Reads the Claude Code hook payload from stdin and decides whether to inject:
  - English polish instructions (always available)
  - Chinese-to-English translation instructions (if user enabled it)
  - nothing at all (Chinese-only with translation off, code-only, etc.)

Stays silent (exit 0, no stdout) when no action is needed so the hook costs
zero tokens for those cases.
"""

from __future__ import annotations

import json
import sys
import time
from typing import TextIO

from . import config
from .detector import route_intent
from .prompts import HINT_FOOTER, POLISH_INSTRUCTIONS, TIMING_FOOTER, TRANSLATION_INSTRUCTIONS


def run(stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    # Prefer the start time captured at __main__ entry (includes imports);
    # fall back to a local clock when run() is invoked programmatically (tests).
    import os

    start_ns_env = os.environ.get("BP_HOOK_START_NS")
    if start_ns_env and start_ns_env.isdigit():
        hook_start_ns = int(start_ns_env)
    else:
        hook_start_ns = time.perf_counter_ns()

    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    try:
        payload = json.load(stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = payload.get("prompt") if isinstance(payload, dict) else None
    translate_enabled = config.get_translate_enabled()

    action = route_intent(prompt, translate_enabled)
    if action is None:
        return 0

    template = POLISH_INSTRUCTIONS if action == "polish" else TRANSLATION_INSTRUCTIONS

    if config.should_show_hint():
        template = template + HINT_FOOTER
        try:
            config.increment_hint_count()
        except OSError:
            # Counter persistence is best-effort; never fail the hook over it.
            pass

    if config.get_show_timing():
        hook_ms = max(1, round((time.perf_counter_ns() - hook_start_ns) / 1_000_000))
        template = template + TIMING_FOOTER.replace("__HOOK_MS__", str(hook_ms))

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": template,
            }
        },
        stdout,
    )
    return 0
