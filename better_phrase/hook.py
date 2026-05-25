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
from .prompts import (
    HINT_FOOTER,
    POLISH_INSTRUCTIONS,
    TIMING_PLACEHOLDER,
    TRANSLATION_INSTRUCTIONS,
)


def run(stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    start = time.perf_counter()

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

    elapsed_ms = max(1, int((time.perf_counter() - start) * 1000))
    template = template.replace(TIMING_PLACEHOLDER, str(elapsed_ms))

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
