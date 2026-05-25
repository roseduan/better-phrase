#!/usr/bin/env bash
# Better Phrase — uninstaller
#
# Two modes (mirrors install.sh):
#   1. In-repo:   bash ./uninstall.sh          (run from cloned repo)
#   2. Bootstrap: curl ... | bash              (no local repo needed)
#
# Flags:
#   --purge        also delete the Better Phrase source directory
#                  (bootstrap mode only — refuses to self-delete an in-repo run)
#   -h, --help     show this help
#
# One-liner:
#   curl -fsSL https://raw.githubusercontent.com/roseduan/better-phrase/main/uninstall.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/roseduan/better-phrase/main/uninstall.sh | bash -s -- --purge
set -euo pipefail

DEFAULT_HOME="$HOME/.claude/skills/better-phrase"
SETTINGS_DIR="$HOME/.claude"
SETTINGS="$SETTINGS_DIR/settings.json"

PURGE=false
for arg in "$@"; do
  case "$arg" in
    --purge)
      PURGE=true
      ;;
    -h|--help)
      cat <<EOF
Better Phrase uninstaller.

Usage:
  bash ./uninstall.sh [--purge]
  curl -fsSL https://raw.githubusercontent.com/roseduan/better-phrase/main/uninstall.sh | bash
  curl -fsSL https://raw.githubusercontent.com/roseduan/better-phrase/main/uninstall.sh | bash -s -- --purge

Options:
  --purge       Also delete the Better Phrase source directory.
  -h, --help    Show this help and exit.
EOF
      exit 0
      ;;
    *)
      printf "Unknown flag: %s (try --help)\n" "$arg" >&2
      exit 2
      ;;
  esac
done

green()  { printf "\033[32m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
red()    { printf "\033[31m%s\033[0m\n" "$1"; }
dim()    { printf "\033[2m%s\033[0m\n" "$1"; }
bold()   { printf "\033[1m%s\033[0m\n" "$1"; }
cyan()   { printf "\033[36m%s\033[0m\n" "$1"; }
rule()   { printf "\033[2m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n"; }

echo
rule
bold   "  📚 Better Phrase — uninstall"
cyan   "     https://github.com/roseduan/better-phrase"
rule
echo

if ! command -v python3 >/dev/null 2>&1; then
  red "❌ python3 is required to safely edit settings.json. Aborting."
  exit 1
fi

# ─── Mode detection: in-repo vs bootstrap ────────────────────────────────────
# In-repo if the script's directory contains better-phrase.sh.
# When piped via `curl | bash`, BASH_SOURCE[0] is empty → bootstrap.
SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi

if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/better-phrase.sh" ]; then
  IN_REPO=true
  PROJECT_DIR="$SCRIPT_DIR"
  dim "  → running from local checkout: $PROJECT_DIR"
else
  IN_REPO=false
  PROJECT_DIR=""
  # Try to recover the install location from the existing hook path in settings.json.
  if [ -f "$SETTINGS" ]; then
    set +e
    PROJECT_DIR="$(python3 -c '
import json, os, re, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except Exception:
    sys.exit(0)
entries = (data.get("hooks") or {}).get("UserPromptSubmit") or []
rx = re.compile(r"/better-phrase\.sh$")
for entry in entries:
    hooks = entry.get("hooks", []) if entry.get("matcher") is not None else [entry]
    for h in hooks:
        cmd = h.get("command", "")
        if rx.search(cmd):
            print(os.path.dirname(cmd))
            sys.exit(0)
' "$SETTINGS" 2>/dev/null)"
    set -e
  fi
  if [ -z "$PROJECT_DIR" ]; then
    PROJECT_DIR="${BETTER_PHRASE_HOME:-$DEFAULT_HOME}"
  fi
  yellow "→ Bootstrap mode (source dir: $PROJECT_DIR)"
fi

# ─── Remove hook from settings.json ──────────────────────────────────────────
if [ ! -f "$SETTINGS" ]; then
  yellow "No ~/.claude/settings.json found. Nothing to remove from settings."
else
  BACKUP="$SETTINGS.backup-$(date +%Y%m%d-%H%M%S)"
  cp "$SETTINGS" "$BACKUP"

  # Prefer the in-tree tool when available; otherwise run an inline equivalent
  # so `curl | bash` works without any local files.
  if [ -f "$PROJECT_DIR/tools/settings_patch.py" ]; then
    python3 "$PROJECT_DIR/tools/settings_patch.py" uninstall "$SETTINGS"
  else
    python3 -c '
import json, os, re, sys
from pathlib import Path

path = Path(sys.argv[1])
PURGE = re.compile(r"/better-phrase\.sh$")

with path.open() as f:
    data = json.load(f)

hooks = data.get("hooks") or {}
entries = hooks.get("UserPromptSubmit") or []
kept_outer = []
for entry in entries:
    if entry.get("matcher") is not None:
        kept = [h for h in entry.get("hooks", []) if not PURGE.search(h.get("command", ""))]
        if kept:
            entry["hooks"] = kept
            kept_outer.append(entry)
    else:
        if not PURGE.search(entry.get("command", "")):
            kept_outer.append(entry)
if kept_outer:
    hooks["UserPromptSubmit"] = kept_outer
else:
    hooks.pop("UserPromptSubmit", None)
if not hooks:
    data.pop("hooks", None)

tmp = path.with_suffix(path.suffix + ".tmp")
with tmp.open("w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
os.replace(tmp, path)
' "$SETTINGS"
  fi

  green "✓ Removed Better Phrase hook from settings.json"
  dim   "  ⚙️  Settings:  $SETTINGS"
  dim   "  🗄  Backup:    $BACKUP"
fi

# ─── Source dir removal (opt-in) ─────────────────────────────────────────────
echo
if [ "$PURGE" = "true" ]; then
  if [ "$IN_REPO" = "true" ]; then
    yellow "→ Skipping source removal — you're running from inside it."
    dim    "    Delete it manually after this script exits:"
    dim    "      rm -rf $PROJECT_DIR"
  elif [ -d "$PROJECT_DIR" ]; then
    # Safety: only purge if it actually looks like a Better Phrase checkout.
    if [ -f "$PROJECT_DIR/better-phrase.sh" ] && [ -d "$PROJECT_DIR/better_phrase" ]; then
      rm -rf "$PROJECT_DIR"
      green "✓ Removed source directory"
      dim   "  📁 $PROJECT_DIR"
    else
      yellow "→ $PROJECT_DIR doesn't look like a Better Phrase checkout — left untouched."
    fi
  else
    dim "→ No source directory at $PROJECT_DIR — nothing to purge."
  fi
else
  if [ -d "$PROJECT_DIR" ]; then
    dim "  📁 Source kept at: $PROJECT_DIR"
    dim "     Re-run with --purge to delete it, or remove manually:"
    dim "       rm -rf $PROJECT_DIR"
  fi
fi

echo
rule
bold  "  🗑  Better Phrase uninstalled."
echo  "  Restart Claude Code to pick up the change."
rule
echo
