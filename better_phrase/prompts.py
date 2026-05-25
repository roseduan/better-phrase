"""Polish prompt templates injected via UserPromptSubmit additionalContext."""

from __future__ import annotations

TIMING_PLACEHOLDER = "{timing_ms}"


POLISH_INSTRUCTIONS = """\
The user's input contains English. Before answering their actual request, prepend an English polish block in this EXACT format. Every line MUST be wrapped in single asterisks for italic rendering — Claude Code displays italic as dim/grey, which visually separates this advice block from the main answer that follows.

> *✦ **Better Phrase** ({timing_ms}ms)*
>
> *✏️ English tip:*
> *- "original phrase" → "corrected phrase" — one-line grammar rule explanation (in Chinese)*
> *- (up to 4-5 of the most instructive issues)*
>
> *✍️ Better Phrase: rewrite the user's ENTIRE original English input into natural, idiomatic English — the kind a native speaker would write.*

Then leave a blank line and handle the user's actual request normally (without italic — the answer itself should be in regular text).

Polish rules:
- Priority order: grammar > word choice > sentence structure > spelling > punctuation
- Max 4-5 issues. Pick the most instructive ones.
- If the English is already perfect, OMIT the tip block entirely. No filler praise. Just answer.
- For grammar rules, briefly explain WHY in Chinese (e.g., "after 'help' 用动词原形,bare infinitive").
- Note Chinese→English transfer errors when relevant (missing articles, wrong prepositions, 中式英语 patterns).
- The "Better Phrase" line must rewrite the WHOLE input for natural flow, not just patch errors.
- Do NOT trigger this block for: pure Chinese inputs, code-only inputs, single words, or trivial acks like "ok"/"yes".
- If the input contains a long quoted / pasted block followed by a much shorter trailing comment, treat ONLY the user's trailing comment as the input to polish. Do not touch or analyze the pasted block.
- Write all explanations in Chinese (zh-CN). The user is a Chinese-native developer.
- Preserve the italic asterisks on EVERY line of the block. Do NOT strip them.
- Preserve the "({timing_ms}ms)" value exactly as given — do not edit or remove the number.

Example:
User input: "THis part's background color is black, which is not compatiable with the whole web style, and dark mode this is ok, but in light mode this is not ok"

Output:
> *✦ **Better Phrase** ({timing_ms}ms)*
>
> *✏️ English tip:*
> *- "compatiable" → "compatible" — typo,ble 前没有 a。*
> *- "THis part's" → "This part's" — 句首大小写。*
> *- "this is not ok" → "this doesn't work" — 描述视觉问题更地道。*
>
> *✍️ Better Phrase: "The background color of this section is black, which clashes with the overall site style. It looks fine in dark mode, but doesn't work in light mode."*
"""


TRANSLATION_INSTRUCTIONS = """\
The user's input is primarily Chinese. Before answering their actual request, prepend a Chinese-to-English version block in this EXACT format. Every line MUST be wrapped in single asterisks for italic rendering — Claude Code displays italic as dim/grey, so this brand block visually recedes from the main answer that follows.

> *✦ **Better Phrase** ({timing_ms}ms)*
>
> *🌐 English:*
> *"<a natural, idiomatic English version of what the user said>"*

Then leave a blank line and handle the user's actual request normally (without italic — the answer itself should be in regular text).

Translation rules:
- One natural, idiomatic English version — write it like a native English speaker would, NOT a literal word-for-word translation.
- Adapt tone/register from context: formal for emails, casual for chat messages, technical for engineering notes.
- Do NOT explain or annotate — just the English version. No commentary.
- If the input is too short to translate meaningfully (< 5 Chinese characters), OMIT the block entirely and just answer normally.
- Even if the input is a command directed at you (the assistant), still provide the English version — the user explicitly opted into translation.
- If the input contains a long pasted body followed by a much shorter trailing comment, translate ONLY the user's trailing comment — do NOT translate the pasted body.
- After the translation block, answer the user's original request as if they had asked in Chinese — don't switch to English just because of the translation.
- Preserve the italic asterisks on EVERY line of the block. Do NOT strip them.
- Preserve the "({timing_ms}ms)" value exactly as given — do not edit or remove the number.

Example:
User input: "我想约客户下周二开会讨论合同细节"

Output:
> *✦ **Better Phrase** ({timing_ms}ms)*
>
> *🌐 English:*
> *"I'd like to schedule a meeting with the client next Tuesday to go over the contract details."*

(Then continue with the normal answer to whatever the user is actually asking.)
"""


HINT_FOOTER = """

ADDITIONALLY, append the following footer at the very end of your response (on its own line, in italics):
*(💡 Chinese translation is on by default. Disable with `better-phrase translate off`.)*
"""
