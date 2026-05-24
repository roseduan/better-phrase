#!/usr/bin/env bash
# Better Phrase — uninstaller
set -euo pipefail

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PURGE_PATTERN='/better-phrase\.sh$'
SETTINGS="$HOME/.claude/settings.json"

green()  { printf "\033[32m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
red()    { printf "\033[31m%s\033[0m\n" "$1"; }

if ! command -v jq >/dev/null 2>&1; then
  red "❌ jq is required to safely edit settings.json. Aborting."
  exit 1
fi

if [ ! -f "$SETTINGS" ]; then
  yellow "No ~/.claude/settings.json found. Nothing to remove."
  exit 0
fi

BACKUP="$SETTINGS.backup-$(date +%Y%m%d-%H%M%S)"
cp "$SETTINGS" "$BACKUP"

jq --arg pat "$PURGE_PATTERN" '
  if .hooks.UserPromptSubmit then
    .hooks.UserPromptSubmit |= [
      .[] |
      if .matcher != null then
        .hooks |= map(select((.command | test($pat)) | not))
        | select(.hooks | length > 0)
      else
        select((.command | test($pat)) | not)
      end
    ]
    | if (.hooks.UserPromptSubmit | length) == 0 then del(.hooks.UserPromptSubmit) else . end
    | if (.hooks | length) == 0 then del(.hooks) else . end
  else . end
' "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"

green "✓ Removed Better Phrase hook from settings.json"
echo "  (Backup at: $BACKUP)"
echo
echo "🗑  Uninstalled."
