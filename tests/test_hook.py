from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path


class HookTests(unittest.TestCase):
    def setUp(self):
        # Isolate config per-test in a temp dir so tests don't read/write the
        # user's real ~/.better-phrase/config.json.
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["BETTER_PHRASE_HOME"] = self._tmpdir.name

    def tearDown(self):
        self._tmpdir.cleanup()
        os.environ.pop("BETTER_PHRASE_HOME", None)

    def _run(self, payload: object) -> tuple[int, str]:
        # Import lazily so the env var above is honored.
        from better_phrase.hook import run

        stdin = io.StringIO(json.dumps(payload) if not isinstance(payload, str) else payload)
        stdout = io.StringIO()
        code = run(stdin=stdin, stdout=stdout)
        return code, stdout.getvalue()

    def _set_translate(self, enabled: bool):
        from better_phrase import config

        config.set_translate_enabled(enabled)

    def _suppress_hint(self):
        # Pretend the hint has already been shown the max number of times so we
        # can assert on prompt content without the hint footer noise.
        from better_phrase import config

        cfg = config.load()
        cfg["hint_shown_count"] = config.HINT_LIMIT
        config.save(cfg)

    # ── Inert inputs ────────────────────────────────────────────────────────

    def test_empty_prompt_silent(self):
        code, out = self._run({"prompt": ""})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_missing_prompt_key_silent(self):
        code, out = self._run({})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_invalid_json_silent(self):
        code, out = self._run("not json at all {")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_code_only_silent(self):
        self._suppress_hint()
        code, out = self._run({"prompt": "useState useEffect useMemo"})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    # ── English polish (always on) ──────────────────────────────────────────

    def test_english_prompt_emits_polish(self):
        self._suppress_hint()
        code, out = self._run({"prompt": "how are you today"})
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("English tip", parsed["hookSpecificOutput"]["additionalContext"])

    def test_english_polish_even_when_translate_off(self):
        self._set_translate(False)
        self._suppress_hint()
        code, out = self._run({"prompt": "how are you today"})
        self.assertEqual(code, 0)
        self.assertIn("English tip", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    # ── Chinese translation toggle ──────────────────────────────────────────

    def test_chinese_emits_translation_when_enabled(self):
        # Default: translate_enabled=True.
        self._suppress_hint()
        code, out = self._run({"prompt": "你好,这是中文输入,请帮我看下"})
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("English:", ctx)

    def test_chinese_silent_when_translate_off(self):
        self._set_translate(False)
        self._suppress_hint()
        code, out = self._run({"prompt": "你好,这是中文输入,请帮我看下"})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    # ── Mixed-input dominant-language routing ───────────────────────────────

    def test_mixed_chinese_dominant_translates(self):
        self._suppress_hint()
        code, out = self._run({"prompt": "Hi Mike, 关于明天的会议我想确认一下时间表能否再调整"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("English:", ctx)

    def test_mixed_english_dominant_polishes(self):
        self._suppress_hint()
        code, out = self._run({"prompt": "What time should we meet 我希望下午"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("English tip", ctx)

    # ── Hint footer behavior ────────────────────────────────────────────────

    def test_hint_footer_present_first_time(self):
        code, out = self._run({"prompt": "how are you today"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("better-phrase translate off", ctx)

    def test_hint_footer_disappears_after_limit(self):
        from better_phrase import config

        # Burn through HINT_LIMIT triggers.
        for _ in range(config.HINT_LIMIT):
            self._run({"prompt": "how are you today"})

        code, out = self._run({"prompt": "how are you today"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("better-phrase translate off", ctx)

    # ── Timing footer behavior ─────────────────────────────────────────────

    def test_timing_footer_present_by_default(self):
        self._suppress_hint()
        code, out = self._run({"prompt": "how are you today"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("⏱ Better Phrase", ctx)
        self.assertIn("ms hook", ctx)

    def test_timing_footer_substitutes_real_hook_ms(self):
        import re

        self._suppress_hint()
        code, out = self._run({"prompt": "how are you today"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        # Placeholder must have been substituted with an actual integer.
        self.assertNotIn("__HOOK_MS__", ctx)
        m = re.search(r"Better Phrase: (\d+)ms hook", ctx)
        self.assertIsNotNone(m, f"hook_ms not found in context tail: {ctx[-300:]}")
        # Sanity bound — hook runs in well under 1000ms even in slow CI.
        self.assertLess(int(m.group(1)), 1000)

    def test_timing_footer_omitted_when_disabled(self):
        from better_phrase import config

        config.set_show_timing(False)
        self._suppress_hint()
        code, out = self._run({"prompt": "how are you today"})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("⏱", ctx)
        self.assertNotIn("ms hook", ctx)


if __name__ == "__main__":
    unittest.main()
