<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./logo-dark.svg">
  <img src="./logo.svg" alt="Better Phrase" width="88">
</picture>

# Better Phrase

**Polish your English phrasing, baked into Claude Code.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**English** · [中文](README.zh-CN.md)

</div>

---

## What it looks like

When you write English:

> ✏️ **English tip:**
> - "I very like" → "I really like" — *very* 不能直接修饰动词。
> - "open the light" → "turn on the light" — 开灯用 *turn on*。
>
> ✍️ **Better version:** "I really like coding with Claude — turn on the lights, start typing, and it just works."

When you write Chinese:

> 🌐 **English:**
> "I'd like to schedule a meeting with the client next Tuesday to go over the contract details."

When you write code, commands, or pure Chinese without translation need — **nothing**. Zero tokens, zero noise.

## What is this?

Better Phrase is a Claude Code add-on that:
- catches grammar and idiom issues in your **English** prompts,
- prepends an idiomatic English version when you write in **Chinese**,
- and stays completely silent for everything else.

Useful for anyone writing English daily — PR descriptions, client emails, technical docs, Slack messages.

## Why not just put rules in CLAUDE.md?

| | Rules in CLAUDE.md | Better Phrase |
|---|---|---|
| Token cost | **Every** prompt loads ~400 tokens of rules | Only when **actually triggered** |
| Trigger reliability | LLM judges (might forget or false-positive) | Deterministic, 100% consistent |
| Pure Chinese / code prompts | Still cost tokens | **Zero** cost, completely silent |

**Result: 5–10× less token spend over a working day, more reliable triggering.**

The core thesis: **boolean decisions belong in code, not in the LLM**. The LLM should generate corrections — not decide whether to generate them.

## Features

- ✏️ **English polish** — grammar, word choice, idiom fixes + native-style rewrite
- 🌐 **Chinese → English translation** — idiomatic English version of what you said (toggleable)
- 🎯 **Zero noise** — code, commands, and irrelevant inputs trigger nothing
- 🇨🇳 **Chinese explanations** — tips are explained in Chinese, focused on common 中式英语 patterns
- 🚀 **Imperceptible overhead** — far faster than Claude's own response latency
- 🔒 **100% local** — no API calls, no telemetry, no data leaves your machine

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and working
- **Python 3.9+** (pre-installed on macOS and most Linux distros)
- **git** — used by the installer to fetch the source
  - macOS: `brew install git` (usually pre-installed via Xcode CLI tools)
  - Linux: `sudo apt install git` (or your distro's equivalent)

## Installation

### Option A — one-liner (recommended)

```bash
curl -fsSL https://betterphrase.roseduan.cn/install.sh | bash
```

Auto-clones the repo to `~/.claude/skills/better-phrase/`, registers the `UserPromptSubmit` hook in `~/.claude/settings.json`, and backs up your existing settings. Re-running pulls the latest version. Override the clone path with `BETTER_PHRASE_HOME=/path bash ...`.

### Option B — clone + install (audit before running)

If you'd rather read the script before executing it:

```bash
git clone https://github.com/roseduan/better-phrase.git ~/.claude/skills/better-phrase
cd ~/.claude/skills/better-phrase
./install.sh
```

What the installer does (either option):

1. Checks `~/.claude/` exists and that `python3` / `git` are installed
2. Backs up your existing `~/.claude/settings.json` (timestamped backup)
3. Adds a `UserPromptSubmit` hook entry pointing at `better-phrase.sh`
4. Cleans up any previous Better Phrase entries from earlier installs

### Verify it works

1. Restart Claude Code (or open a new session) so it picks up the updated settings
2. Type any English sentence into Claude Code, e.g. `how are you today`
3. You should see an `✏️ English tip` block appear before the actual answer

If nothing appears, check that `~/.claude/settings.json` contains an entry under `hooks.UserPromptSubmit` pointing at `better-phrase.sh`.

### Uninstall

One-liner (mirrors the install entry point):

```bash
curl -fsSL https://betterphrase.roseduan.cn/uninstall.sh | bash
```

To also delete the cloned source directory:

```bash
curl -fsSL https://betterphrase.roseduan.cn/uninstall.sh | bash -s -- --purge
```

From a local clone:

```bash
./uninstall.sh            # remove hook only
./uninstall.sh --purge    # also delete the source directory (refused when run from inside it)
```

The uninstaller backs up `~/.claude/settings.json` (timestamped) before editing, removes the Better Phrase hook entry, and prints exactly what it changed. Without `--purge`, your installed folder stays put.

## Configuration

There's exactly **one** user-facing toggle: whether Chinese → English translation is on.

English polish is the product's core value — it's always on. To disable everything, run `./uninstall.sh`.

```bash
# From the repo root:
PYTHONPATH=. python3 -m better_phrase translate           # show current state
PYTHONPATH=. python3 -m better_phrase translate off       # disable
PYTHONPATH=. python3 -m better_phrase translate on        # re-enable
```

### Behavior matrix

| Input | `translate=on` (default) | `translate=off` |
|-------|--------------------------|-----------------|
| English | ✏️ English tip | ✏️ English tip |
| Chinese | 🌐 English version | (silent) |
| Mixed, Chinese-dominant | 🌐 English version | Polish if enough English, else silent |
| Mixed, English-dominant | ✏️ English tip | ✏️ English tip |
| Code / commands | (silent) | (silent) |

## Known limitations

Better Phrase sees the assembled prompt *after* it leaves your keyboard. **It cannot distinguish what you typed from what you pasted** — Claude Code doesn't pass paste metadata.

To compensate:

- **Tail-only heuristic.** When the trailing segment of your input is much shorter than the body (≤ 50 chars vs ≥ 100 chars body), Better Phrase analyzes only that trailing segment. This catches the common "pasted content + short typed question" pattern automatically.
- **Skip-anything mechanism.** Wrap any content in triple backticks to exclude it from detection entirely:

      ```
      <anything you pasted that you don't want analyzed>
      ```

      your actual question

  Fenced blocks are stripped before any language detection runs.

The combination handles the common cases (~90%). For perfect paste awareness we'd need IDE integration (planned for V1.0).

## Privacy

- **100% local execution.** No external API calls, no telemetry, no analytics.
- Your prompts and corrections never leave your machine.
- Any future error history will live at `~/.better-phrase/`, owned by you (planned for V0.3).

## Roadmap

- [x] **V0.1** — initial release
- [x] **V0.2** — Chinese → English translation toggle
- [ ] **V0.3** — local error history + `better-phrase stats` subcommand
- [ ] **V0.4** — spaced repetition (SRS) review of past mistakes
- [ ] **V0.5** — 中式英语 pattern library (specialized 中式英语 detection)
- [ ] **V1.0** — cross-tool support (Cursor / VS Code / Chrome extension sharing the same error history)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

---

<div align="center">

**Star ⭐ if Better Phrase helped you write better English in Claude Code.**

</div>
