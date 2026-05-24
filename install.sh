#!/usr/bin/env bash
# Better Phrase — installer
#
# Two modes:
#   1. In-repo:   bash ./install.sh    (run from cloned repo, uses script's dir)
#   2. Bootstrap: curl ... | bash      (clones repo to BETTER_PHRASE_HOME first)
#
# Override clone location with: BETTER_PHRASE_HOME=/path bash install.sh
set -euo pipefail

REPO_URL="https://github.com/roseduan/better-phrase.git"
DEFAULT_HOME="$HOME/.claude/skills/better-phrase"
PURGE_PATTERN='/better-phrase\.sh$'
SETTINGS_DIR="$HOME/.claude"
SETTINGS="$SETTINGS_DIR/settings.json"

green()  { printf "\033[32m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
red()    { printf "\033[31m%s\033[0m\n" "$1"; }
dim()    { printf "\033[2m%s\033[0m\n" "$1"; }

echo
echo "📚 Better Phrase — installer"
echo

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
  PROJECT_DIR="${BETTER_PHRASE_HOME:-$DEFAULT_HOME}"
  yellow "→ Bootstrap mode (will sync repo to $PROJECT_DIR)"
fi

# ─── Preflight ────────────────────────────────────────────────────────────────
if [ ! -d "$SETTINGS_DIR" ]; then
  red "❌ ~/.claude directory not found."
  echo "   Install Claude Code first: https://docs.claude.com/en/docs/claude-code"
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  red "❌ jq is required (used by this installer to edit settings.json)."
  echo "   macOS:  brew install jq"
  echo "   Linux:  sudo apt install jq   (or your distro's equivalent)"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  red "❌ python3 is required (the hook is implemented in Python, stdlib only)."
  echo "   macOS:  brew install python"
  echo "   Linux:  sudo apt install python3"
  exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))')"
PY_OK="$(python3 -c 'import sys; print(int(sys.version_info >= (3, 9)))')"
if [ "$PY_OK" != "1" ]; then
  red "❌ python3 ${PY_VERSION} is too old. Need ≥ 3.9."
  exit 1
fi
dim "  → python3 ${PY_VERSION}"

# ─── Bootstrap: clone or update ──────────────────────────────────────────────
# In bootstrap mode we own the checkout — always ensure it's current.
# In-repo mode leaves the user's working tree untouched.
if [ "$IN_REPO" = "false" ]; then
  if ! command -v git >/dev/null 2>&1; then
    red "❌ git is required for bootstrap install."
    echo "   macOS:  brew install git   (or use Xcode CLI tools)"
    echo "   Linux:  sudo apt install git"
    exit 1
  fi

  if [ -d "$PROJECT_DIR/.git" ]; then
    yellow "→ Updating existing checkout at $PROJECT_DIR"
    git -C "$PROJECT_DIR" pull --ff-only --quiet
    green "✓ Pulled latest from main"
  elif [ -e "$PROJECT_DIR" ]; then
    red "❌ $PROJECT_DIR exists but is not a git checkout."
    echo "   Remove it manually, or set BETTER_PHRASE_HOME to a different path."
    exit 1
  else
    yellow "→ Cloning $REPO_URL"
    mkdir -p "$(dirname "$PROJECT_DIR")"
    git clone --depth 1 --quiet "$REPO_URL" "$PROJECT_DIR"
    green "✓ Cloned to $PROJECT_DIR"
  fi
fi

HOOK_SCRIPT="$PROJECT_DIR/better-phrase.sh"

if [ ! -f "$HOOK_SCRIPT" ]; then
  red "❌ hook script not found at: $HOOK_SCRIPT"
  exit 1
fi

chmod +x "$HOOK_SCRIPT"
green "✓ Hook script is executable"
dim   "  → $HOOK_SCRIPT"

# ─── Update / create settings.json ───────────────────────────────────────────
mkdir -p "$SETTINGS_DIR"

if [ -f "$SETTINGS" ]; then
  BACKUP="$SETTINGS.backup-$(date +%Y%m%d-%H%M%S)"
  cp "$SETTINGS" "$BACKUP"
  green "✓ Backed up existing settings.json"
  dim   "  → $BACKUP"

  # Purge any prior Better Phrase entry, then append the new canonical entry.
  jq --arg cmd "$HOOK_SCRIPT" --arg pat "$PURGE_PATTERN" '
    .hooks //= {}
    | .hooks.UserPromptSubmit //= []
    | .hooks.UserPromptSubmit |= [
        .[] |
        if .matcher != null then
          .hooks |= map(select((.command | test($pat)) | not))
          | select(.hooks | length > 0)
        else
          select((.command | test($pat)) | not)
        end
      ]
    | .hooks.UserPromptSubmit += [{
        matcher: "",
        hooks: [{ type: "command", command: $cmd, timeout: 10 }]
      }]
  ' "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
else
  jq -n --arg cmd "$HOOK_SCRIPT" '{
    hooks: {
      UserPromptSubmit: [
        {
          matcher: "",
          hooks: [
            { type: "command", command: $cmd, timeout: 10 }
          ]
        }
      ]
    }
  }' > "$SETTINGS"
  green "✓ Created ~/.claude/settings.json"
fi

green "✓ Registered UserPromptSubmit hook"

echo
green "🎉 Installation complete."
echo
echo "Features:"
echo "  • English polish         — always on; catches issues when you write English"
echo "  • Chinese translation    — on by default; shows English version when you write Chinese"
echo
echo "Toggle Chinese translation any time:"
dim "  cd $PROJECT_DIR"
dim "  PYTHONPATH=. python3 -m better_phrase translate off    # disable"
dim "  PYTHONPATH=. python3 -m better_phrase translate on     # re-enable"
dim "  PYTHONPATH=. python3 -m better_phrase translate        # show status"
echo
echo "Next steps:"
echo "  1. Restart Claude Code (or open a new session)"
echo "  2. Type any English sentence — you'll see the polish tip block appear"
echo
dim "To uninstall:  bash $PROJECT_DIR/uninstall.sh"
echo
