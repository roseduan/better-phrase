from __future__ import annotations

import unittest

from better_phrase.detector import (
    clean,
    extract_user_intent,
    route_intent,
    should_polish,
    should_translate_cn,
)


class CleanTests(unittest.TestCase):
    def test_strips_fenced_block_single_line(self):
        self.assertNotIn("secret", clean("hello ```secret``` world"))

    def test_strips_fenced_block_multiline(self):
        src = "hello\n```\nlots of english here for sure\n```\nbye"
        out = clean(src)
        self.assertNotIn("english", out)
        self.assertIn("hello", out)
        self.assertIn("bye", out)

    def test_strips_inline_code(self):
        self.assertNotIn("foo", clean("see `foo()` here"))

    def test_strips_slash_command_line(self):
        self.assertNotIn("/help", clean("/help me\nhello"))

    def test_strips_bang_command_line(self):
        self.assertNotIn("!ls", clean("!ls -la\nhello"))

    def test_keeps_inline_slash_mid_line(self):
        # Only lines *starting* with / are stripped; AC/DC stays.
        self.assertIn("AC/DC", clean("listening to AC/DC right now"))


class ShouldPolishTests(unittest.TestCase):
    def test_empty_returns_false(self):
        self.assertFalse(should_polish(""))
        self.assertFalse(should_polish(None))

    def test_pure_chinese_returns_false(self):
        self.assertFalse(should_polish("你好,这是中文测试,完全没有英文"))

    def test_too_few_english_words(self):
        self.assertFalse(should_polish("hi there"))

    def test_code_identifiers_without_function_word(self):
        # Three identifiers but no function word → looks like code, skip.
        self.assertFalse(should_polish("useState useEffect useMemo"))

    def test_plain_english_question(self):
        self.assertTrue(should_polish("how are you today"))

    def test_mixed_chinese_and_english(self):
        self.assertTrue(should_polish("帮我看下 how to use this feature"))

    def test_english_inside_fenced_block_does_not_trigger(self):
        # Long English inside a code fence should be stripped before counting.
        src = "```\nthe quick brown fox jumps over the lazy dog\n```\n你好"
        self.assertFalse(should_polish(src))

    def test_slash_command_only_does_not_trigger(self):
        # The whole "/help ..." line is stripped → nothing English remains.
        self.assertFalse(should_polish("/help me with the docs please"))


class CodeHeuristicTests(unittest.TestCase):
    """Coverage for the _looks_like_code_token fallback path — inputs that
    have no function word but should be classified correctly anyway."""

    def test_camelcase_identifiers_skip(self):
        self.assertFalse(should_polish("useState useEffect useMemo"))

    def test_pascalcase_identifiers_skip(self):
        self.assertFalse(should_polish("MyClass YourClass HisClass"))

    def test_all_caps_constants_skip(self):
        self.assertFalse(should_polish("HTTP_REQUEST MAX_CONN BUFFER_SIZE"))

    def test_identifiers_with_digits_skip(self):
        self.assertFalse(should_polish("react18 svelte5 nuxt3"))

    def test_imperative_without_function_word_does_polish(self):
        # The bug we just fixed — real English imperative with no
        # function word should still trigger polish.
        self.assertTrue(
            should_polish("write two MDs, one english, one chinese")
        )

    def test_lowercase_imperative_does_polish(self):
        self.assertTrue(should_polish("send help fast please"))

    def test_mixed_code_and_prose_does_polish(self):
        # "MDs" looks code-like, but other tokens are normal English →
        # not ALL code → polish.
        self.assertTrue(should_polish("write two MDs please"))

    def test_title_case_english_does_polish(self):
        # Leading capital alone is normal English, not code.
        self.assertTrue(should_polish("Write Two Files Please"))


class ShouldTranslateCnTests(unittest.TestCase):
    def test_empty_returns_false(self):
        self.assertFalse(should_translate_cn(""))
        self.assertFalse(should_translate_cn(None))

    def test_pure_english_returns_false(self):
        self.assertFalse(should_translate_cn("how are you today"))

    def test_short_chinese_returns_false(self):
        # < 5 CJK chars
        self.assertFalse(should_translate_cn("你好"))

    def test_long_chinese_returns_true(self):
        self.assertTrue(should_translate_cn("你好,这是中文输入,请帮我看下"))

    def test_chinese_inside_fenced_block_does_not_trigger(self):
        src = "```\n这里是大段的中文代码注释,应该被剥掉\n```\nhi"
        self.assertFalse(should_translate_cn(src))


class RouteIntentTests(unittest.TestCase):
    def test_chinese_dominant_translate_on(self):
        prompt = "你好,这是中文输入,请帮我看下时间安排"
        self.assertEqual(route_intent(prompt, translate_enabled=True), "translate")

    def test_chinese_dominant_translate_off_falls_through_silent(self):
        prompt = "你好,这是中文输入,请帮我看下时间安排"
        self.assertIsNone(route_intent(prompt, translate_enabled=False))

    def test_english_only_always_polishes(self):
        prompt = "how are you doing today"
        self.assertEqual(route_intent(prompt, translate_enabled=True), "polish")
        self.assertEqual(route_intent(prompt, translate_enabled=False), "polish")

    def test_mixed_chinese_dominant_translates(self):
        prompt = "Hi Mike, 关于明天的会议我想确认一下时间表能否再调整两天"
        self.assertEqual(route_intent(prompt, translate_enabled=True), "translate")

    def test_mixed_english_dominant_polishes(self):
        prompt = "What time should we meet tomorrow 我希望下午"
        self.assertEqual(route_intent(prompt, translate_enabled=True), "polish")

    def test_empty_or_none(self):
        self.assertIsNone(route_intent("", translate_enabled=True))
        self.assertIsNone(route_intent(None, translate_enabled=True))

    def test_code_only_no_action(self):
        self.assertIsNone(route_intent("useState useEffect useMemo", translate_enabled=True))


class TailOnlyHeuristicTests(unittest.TestCase):
    """Coverage for extract_user_intent + downstream effects.

    The hook can't tell pasted from typed content (Claude Code doesn't pass
    paste metadata). The tail-only heuristic uses length disparity as a
    proxy: when the trailing segment is much shorter than the rest, treat
    only that trailing segment as the user's intent.
    """

    LONG_PASTE_ZH = (
        "一个初级程序员，部署一个 spring boot，和一个 go web 服务，"
        "遇到奇奇怪怪的问题的概率，go 要少 80%。特别是在 k8s 环境下。"
        "k8s 已经是事实上的微服务的基础设施的背景下，我觉得是 k8s "
        "带动了 go 语言的流行。"
    )

    def test_single_segment_unchanged(self):
        text = "how are you today"
        self.assertEqual(extract_user_intent(text), text)

    def test_two_balanced_segments_unchanged(self):
        # Neither side dominates → full text preserved.
        text = "First sentence here. Second one too."
        self.assertEqual(extract_user_intent(text), text)

    def test_long_body_short_tail_returns_tail(self):
        text = self.LONG_PASTE_ZH + " 这不是我复制的内容"
        self.assertEqual(extract_user_intent(text), "这不是我复制的内容")

    def test_short_input_with_short_tail_unchanged(self):
        # Body too short to trigger tail-only.
        text = "hi there. small thing."
        self.assertEqual(extract_user_intent(text), text)

    def test_paste_plus_short_zh_routes_to_typed_only(self):
        # Long pasted Chinese article + short typed Chinese tail.
        # Without tail-only this would translate the whole article;
        # with tail-only we only see the trailing 9 chars (still ≥ 5,
        # so it still triggers translate but on the right slice).
        text = self.LONG_PASTE_ZH + " 这不是我复制的内容"
        self.assertEqual(
            route_intent(text, translate_enabled=True), "translate"
        )

    def test_paste_plus_short_en_question_routes_to_polish(self):
        # Long pasted Chinese body + short typed English question →
        # tail-only sees just the English, routes to polish.
        text = self.LONG_PASTE_ZH + " what does this mean please"
        self.assertEqual(
            route_intent(text, translate_enabled=True), "polish"
        )

    def test_paste_plus_trivial_tail_stays_silent(self):
        # Tail "ok" is too short to carry any signal. The user's intent is
        # an acknowledgment, not a translation request — staying silent is
        # exactly what we want (we don't translate the pasted body).
        text = self.LONG_PASTE_ZH + " ok"
        self.assertIsNone(route_intent(text, translate_enabled=True))

    def test_paragraph_break_separator_works(self):
        # Blank-line-separated paragraphs also split into segments.
        text = "paragraph one is here with some content " * 5 + "\n\nhelp"
        self.assertEqual(extract_user_intent(text), "help")


if __name__ == "__main__":
    unittest.main()
