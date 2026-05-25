<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./logo-dark.svg">
  <img src="./logo.svg" alt="Better Phrase" width="88">
</picture>

# Better Phrase

**Polish your English phrasing, baked into Claude Code.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**English** · [中文](README.md)

</div>

---

## What it looks like

When you write English:

> ✦ **Better Phrase** (1ms)
>
> ✏️ **English tip:**
> - "I very like" → "I really like" — *very* 不能直接修饰动词。
> - "open the light" → "turn on the light" — 开灯用 *turn on*。
>
> ✍️ Better Phrase: "I really like coding with Claude — turn on the lights, start typing, and it just works."

When you write Chinese:

> ✦ **Better Phrase** (1ms)
>
> 🌐 **English:**
> "I'd like to schedule a meeting with the client next Tuesday to go over the contract details."

When you write code, commands, or pure Chinese without translation need — **nothing**. Zero tokens, zero noise.

## Why not a skill

"Is this prompt English?" is a yes/no question. Asking the LLM to re-decide on every message looks equivalent, but the token cost and trigger reliability are not the same.

| | If it were a skill (LLM decides when to invoke) | Better Phrase (hook + code filter) |
|---|---|---|
| Trigger decision | LLM has to judge every prompt to decide if it should invoke | Python regex, **deterministic**, zero model cost |
| Token cost | Skill description stays in context, **loaded every message** | Instructions injected only when **English is detected** |
| Trigger reliability | Model may skip invocations or mistime them | 100% consistent — no reliance on model memory |
| Non-English prompts | Even when not invoked, the description still costs tokens | **Zero tokens** — hook exits immediately |

Skills shine for "should the AI use tool X?" — judgment calls. Language detection is a **yes/no question**; cheaper and more reliable in code.

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
3. You should see a `✦ Better Phrase (1ms)` tip block appear before the actual answer

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

The combination handles the common cases (~90%). Perfect paste awareness would need IDE integration.

## Privacy

- **100% local execution.** No external API calls, no telemetry, no analytics.
- Your prompts and corrections never leave your machine.
- If we ever add an error history, it'll live at `~/.better-phrase/`, owned by you.

## Contributing

This is an early-stage project — the feature set is deliberately tiny right now ("English polish + Chinese translation", nothing else) and there's plenty of room to grow. If you think the direction is worth continuing, jump in:

- **File a bug / pitch an idea** — open an [Issue](https://github.com/roseduan/better-phrase/issues). Chinglish patterns, new detection rules, UI tweaks, copy polish — all welcome.
- **Send a PR** — fork, hack, PR. Easy entry points:
  - Tweak language-detection heuristics in `better_phrase/detector.py`
  - Adjust tip / translation templates in `better_phrase/prompts.py`
  - Add more test cases to `tests/`
  - Improve the docs (README, SKILL.md, website)
- **Spread the word** — share with colleagues or friends if it's useful; feedback is gold this early.

The codebase is small (~100 lines of Python), so any PR makes a visible dent.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

---

<div align="center">

**Star ⭐ if Better Phrase helped you write better English in Claude Code.**

</div>
