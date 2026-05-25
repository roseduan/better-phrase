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
SETTINGS_DIR="$HOME/.claude"
SETTINGS="$SETTINGS_DIR/settings.json"

green()  { printf "\033[32m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
red()    { printf "\033[31m%s\033[0m\n" "$1"; }
dim()    { printf "\033[2m%s\033[0m\n" "$1"; }
bold()   { printf "\033[1m%s\033[0m\n" "$1"; }
cyan()   { printf "\033[36m%s\033[0m\n" "$1"; }
rule()   { printf "\033[2m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n"; }

echo
rule
bold   "  📚 Better Phrase"
echo   "     Polish your English phrasing, baked into Claude Code."
cyan   "     https://github.com/roseduan/better-phrase"
rule
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
  python3 "$PROJECT_DIR/tools/settings_patch.py" install "$SETTINGS" "$HOOK_SCRIPT"
else
  python3 "$PROJECT_DIR/tools/settings_patch.py" install "$SETTINGS" "$HOOK_SCRIPT"
  green "✓ Created ~/.claude/settings.json"
fi

green "✓ Registered UserPromptSubmit hook"

# Read installed version for the summary footer.
VERSION="$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_DIR'); from better_phrase import __version__; print(__version__)" 2>/dev/null || echo "")"

echo
rule
if [ -n "$VERSION" ]; then
  bold "  🎉 Better Phrase v${VERSION} installed."
else
  bold "  🎉 Better Phrase installed."
fi
echo
echo "  📁 Source:    $PROJECT_DIR"
echo "  ⚙️  Settings:  $SETTINGS"
echo
echo "  Active features:"
echo "    ✏️  English polish        — always on"
echo "    🌐 Chinese translation   — on by default"
echo
echo "  Toggles (from source dir):"
dim  "    PYTHONPATH=. python3 -m better_phrase translate off    # disable Chinese translation"
dim  "    PYTHONPATH=. python3 -m better_phrase timing off       # hide timing footer"
echo
echo "  Next: restart Claude Code, then try typing English or Chinese."
echo
dim  "  Uninstall:  bash $PROJECT_DIR/uninstall.sh"
dim  "  Docs:       https://github.com/roseduan/better-phrase"
rule
echo
