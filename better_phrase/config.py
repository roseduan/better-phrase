"""Config management for Better Phrase.

Config lives at ~/.better-phrase/config.json (overridable via BETTER_PHRASE_HOME).
Created lazily on first write — running the hook with no config simply uses defaults.

Design choice: only ONE user-facing setting — whether Chinese-to-English translation
is on. English polish is the product's core value, always on. To turn the whole
thing off, run ./uninstall.sh.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_TRANSLATE_ENABLED = True
HINT_LIMIT = 3  # Show "how to disable" footer this many times, then stop.


def _config_dir() -> Path:
    return Path(os.environ.get("BETTER_PHRASE_HOME", str(Path.home() / ".better-phrase")))


def _config_path() -> Path:
    return _config_dir() / "config.json"


def _defaults() -> dict[str, Any]:
    return {
        "translate_enabled": DEFAULT_TRANSLATE_ENABLED,
        "hint_shown_count": 0,
    }


def load() -> dict[str, Any]:
    """Read config; return defaults on any failure (missing file, bad JSON, etc.)."""
    path = _config_path()
    if not path.exists():
        return _defaults()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _defaults()
    if not isinstance(data, dict):
        return _defaults()
    return {**_defaults(), **data}


def save(cfg: dict[str, Any]) -> None:
    """Atomically write config."""
    _config_dir().mkdir(parents=True, exist_ok=True)
    path = _config_path()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    tmp.replace(path)


def get_translate_enabled() -> bool:
    return bool(load().get("translate_enabled", DEFAULT_TRANSLATE_ENABLED))


def set_translate_enabled(enabled: bool) -> None:
    cfg = load()
    cfg["translate_enabled"] = bool(enabled)
    save(cfg)


def should_show_hint() -> bool:
    return load().get("hint_shown_count", 0) < HINT_LIMIT


def increment_hint_count() -> None:
    cfg = load()
    cfg["hint_shown_count"] = cfg.get("hint_shown_count", 0) + 1
    save(cfg)
