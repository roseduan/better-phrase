"""Detect what action to take for a given Claude Code prompt.

Cheap pre-filters that run before any LLM call — so the hook costs zero tokens
on Chinese-only, code-only, or trivial inputs. Pure stdlib, fully unit-tested.
"""

from __future__ import annotations

import re

_FENCED_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_COMMAND_LINE = re.compile(r"^\s*[/!]")
_WORD = re.compile(r"[a-zA-Z0-9]{2,}")  # widen to capture code tokens with digits
_LETTER_WORD = re.compile(r"[a-zA-Z]{2,}")  # narrow form used for counting words
_FUNCTION_WORD = re.compile(
    r"\b("
    r"the|a|an|is|are|was|were|i|you|we|they|this|that|these|those|"
    r"how|what|why|when|where|who|do|does|did|have|has|had|"
    r"can|could|will|would|should|may|might|"
    r"in|on|at|for|to|of|with|and|or|but|if|so|because|though|while"
    r")\b",
    re.IGNORECASE,
)
_CJK = re.compile(r"[一-鿿]")

# Sentence boundary used by the tail-only heuristic. Splits on:
#   - blank lines (paragraph break)
#   - line breaks
#   - Chinese sentence-ending punctuation, optionally followed by whitespace
#   - English sentence-ending punctuation followed by whitespace
_SEGMENT_SPLIT = re.compile(r"\n\n+|(?<=[。!?])\s*|\n+|(?<=[.!?])\s+")

MIN_ENGLISH_WORDS = 3
MIN_CJK_CHARS = 5

# Tail-only heuristic thresholds. Trigger when the trailing segment is much
# shorter than the rest of the input — the common "pasted long content +
# short typed question" case. The hook can't actually distinguish paste from
# typing (Claude Code doesn't expose paste metadata to UserPromptSubmit hooks),
# so this length-disparity proxy is the best we have at this layer.
TAIL_MAX_LEN = 50
TAIL_REST_MIN_LEN = 100


def clean(text: str) -> str:
    """Strip fenced blocks, slash/bang command lines, and inline backticks."""
    text = _FENCED_BLOCK.sub("", text)
    text = "\n".join(
        line for line in text.split("\n") if not _COMMAND_LINE.match(line)
    )
    text = _INLINE_CODE.sub("", text)
    return text


def _split_segments(text: str) -> list[str]:
    """Break text into sentence-ish segments. Drops empty pieces."""
    return [s.strip() for s in _SEGMENT_SPLIT.split(text) if s.strip()]


def extract_user_intent(text: str) -> str:
    """Return the slice of `text` that most likely reflects the user's intent.

    When the trailing segment is much shorter than the body — strongly
    suggesting "pasted bulk + short typed comment" — only the trailing
    segment is returned. Otherwise the full text passes through unchanged.
    """
    segments = _split_segments(text)
    if len(segments) < 2:
        return text
    last = segments[-1]
    rest_len = sum(len(s) for s in segments[:-1])
    if len(last) <= TAIL_MAX_LEN and rest_len >= TAIL_REST_MIN_LEN:
        return last
    return text


def _looks_like_code_token(word: str) -> bool:
    """Heuristic: does this token look like a code identifier rather than
    natural English?

    True for:
      - tokens containing a digit                  (react18, http2, v5)
      - long ALL_CAPS tokens                        (HTTP, MAX_CONN, BUFFER)
      - tokens with internal uppercase letters     (useState, MyClass, iPhone)

    A leading capital alone (e.g. "Write", "Hello") is normal English and
    is NOT treated as code.
    """
    if any(ch.isdigit() for ch in word):
        return True
    if word.isupper() and len(word) > 2:
        return True
    # Internal uppercase: camelCase / PascalCase. Skip index 0 so plain
    # Title-Case English words ("Write", "Hello") aren't flagged.
    if len(word) > 1 and any(ch.isupper() for ch in word[1:]):
        return True
    return False


def _has_english_signal(cleaned: str) -> bool:
    """Whether the cleaned text reads like English prose worth polishing."""
    words = _LETTER_WORD.findall(cleaned)
    if len(words) < MIN_ENGLISH_WORDS:
        return False
    if _FUNCTION_WORD.search(cleaned):
        return True
    all_tokens = _WORD.findall(cleaned)
    if all_tokens and all(_looks_like_code_token(w) for w in all_tokens):
        return False
    return True


def should_polish(prompt: str | None) -> bool:
    """True iff the prompt has enough English signal to trigger polish."""
    if not prompt:
        return False
    target = extract_user_intent(clean(prompt))
    return _has_english_signal(target)


def should_translate_cn(prompt: str | None) -> bool:
    """True iff the prompt has enough Chinese to be worth translating."""
    if not prompt:
        return False
    target = extract_user_intent(clean(prompt))
    return len(_CJK.findall(target)) >= MIN_CJK_CHARS


def route_intent(prompt: str | None, translate_enabled: bool) -> str | None:
    """Decide what action to take given the prompt and the user's translate setting.

    Returns one of: "polish", "translate", or None (skip).

    English polish is always available (the product's core value). Chinese
    translation is opt-in/opt-out via translate_enabled.

    Mixed-input rule: dominant language wins.
      - cjk_chars > en_words * 2 → Chinese-dominant → translate (if enabled)
      - otherwise English signal present → polish
      - otherwise some Chinese present → translate (if enabled)

    Tail-only mode: if the input ends with a much shorter trailing segment
    than the rest, analyze only that trailing segment. Catches the common
    "pasted content + short typed question" pattern without paste metadata.
    """
    if not prompt:
        return None

    cleaned = clean(prompt)
    target = extract_user_intent(cleaned)

    en_words = len(_LETTER_WORD.findall(target))
    cjk_chars = len(_CJK.findall(target))
    has_english = _has_english_signal(target)
    has_chinese = cjk_chars >= MIN_CJK_CHARS

    # Chinese-dominant input.
    if has_chinese and cjk_chars > en_words * 2:
        if translate_enabled:
            return "translate"
        # Translation off and not enough English to polish → silent.
        return "polish" if has_english else None

    # English signal — polish it.
    if has_english:
        return "polish"

    # Some Chinese present but not dominant; polish is not applicable here.
    if has_chinese and translate_enabled:
        return "translate"

    return None
