#!/usr/bin/env python3
"""Patch ~/.claude/settings.json to add or remove the Better Phrase hook.

Used by install.sh / uninstall.sh in place of jq. Pure stdlib.

Usage:
  python3 tools/settings_patch.py install   <settings_path> <hook_command>
  python3 tools/settings_patch.py uninstall <settings_path>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

PURGE_PATTERN = r"/better-phrase\.sh$"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _purge(entries: list, pattern: str) -> list:
    """Remove any Better Phrase hook entries. Mirrors the jq purge logic:
    handles both nested-form ({matcher, hooks: [...]}) and flat-form entries.
    """
    rx = re.compile(pattern)
    out = []
    for entry in entries:
        if entry.get("matcher") is not None:
            kept = [
                h for h in entry.get("hooks", [])
                if not rx.search(h.get("command", ""))
            ]
            if kept:
                entry["hooks"] = kept
                out.append(entry)
        else:
            if not rx.search(entry.get("command", "")):
                out.append(entry)
    return out


def install(settings_path: Path, hook_command: str, pattern: str = PURGE_PATTERN) -> None:
    data = _load(settings_path)
    hooks = data.setdefault("hooks", {})
    entries = hooks.setdefault("UserPromptSubmit", [])
    entries = _purge(entries, pattern)
    entries.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": hook_command, "timeout": 10}],
    })
    hooks["UserPromptSubmit"] = entries
    _save(settings_path, data)


def uninstall(settings_path: Path, pattern: str = PURGE_PATTERN) -> None:
    if not settings_path.exists():
        return
    data = _load(settings_path)
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return
    entries = hooks.get("UserPromptSubmit")
    if not isinstance(entries, list):
        return
    entries = _purge(entries, pattern)
    if entries:
        hooks["UserPromptSubmit"] = entries
    else:
        hooks.pop("UserPromptSubmit", None)
    if not hooks:
        data.pop("hooks", None)
    _save(settings_path, data)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="settings_patch")
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install")
    p_install.add_argument("settings")
    p_install.add_argument("hook_command")

    p_uninstall = sub.add_parser("uninstall")
    p_uninstall.add_argument("settings")

    args = parser.parse_args(argv)
    path = Path(args.settings)

    if args.command == "install":
        install(path, args.hook_command)
    elif args.command == "uninstall":
        uninstall(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
