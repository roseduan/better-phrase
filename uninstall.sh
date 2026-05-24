#!/usr/bin/env bash
# Better Phrase — uninstaller
set -euo pipefail

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SETTINGS="$HOME/.claude/settings.json"

green()  { printf "\033[32m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
red()    { printf "\033[31m%s\033[0m\n" "$1"; }

if ! command -v python3 >/dev/null 2>&1; then
  red "❌ python3 is required to safely edit settings.json. Aborting."
  exit 1
fi

if [ ! -f "$SETTINGS" ]; then
  yellow "No ~/.claude/settings.json found. Nothing to remove."
  exit 0
fi

BACKUP="$SETTINGS.backup-$(date +%Y%m%d-%H%M%S)"
cp "$SETTINGS" "$BACKUP"

python3 "$PROJECT_DIR/tools/settings_patch.py" uninstall "$SETTINGS"

green "✓ Removed Better Phrase hook from settings.json"
echo "  (Backup at: $BACKUP)"
echo
echo "🗑  Uninstalled."
