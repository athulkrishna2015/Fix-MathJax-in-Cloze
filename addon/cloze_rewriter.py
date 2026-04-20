import re
from .config import CLOZE_START_RE, ParsedCloze, RewriteTokens, rewrite_tokens


MATHJAX_RE = re.compile(r"(?s)(\\\(.*?\\\)|\\\[.*?\\\]|<anki-mathjax[^>]*>.*?</anki-mathjax>)")

def remove_nbsp_from_mathjax(text: str) -> tuple[str, int]:
    replacements = 0

    def repl(match: re.Match) -> str:
        nonlocal replacements
        original = match.group(0)
        fixed = original.replace("&nbsp;", " ").replace("\xa0", " ").replace("&amp;nbsp;", " ")
        if fixed != original:
            replacements += original.count("&nbsp;") + original.count("\xa0") + original.count("&amp;nbsp;")
        return fixed

    new_text = MATHJAX_RE.sub(repl, text)
    return new_text, replacements

class ClozeRewriter:

    def __init__(self, tokens: RewriteTokens) -> None:
        self._replacement = tokens.replacement
        self._boundary_replacement = tokens.boundary_replacement

    def fix_text(self, text: str) -> tuple[str, int]:
        result: list[str] = []
        cursor = 0
        replacements = 0

        while True:
            match = CLOZE_START_RE.search(text, cursor)
            if not match:
                result.append(text[cursor:])
                break

            result.append(text[cursor:match.start()])
            parsed = self._parse_cloze_at(text, match.start())

            if not parsed:
                # Malformed cloze start: keep it unchanged and continue searching.
                result.append(text[match.start():match.end()])
                cursor = match.end()
                continue

            rewritten_cloze, cloze_replacements = self._rewrite_parsed_cloze(parsed)
            result.append(rewritten_cloze)
            replacements += cloze_replacements
            cursor = parsed.end

        return "".join(result), replacements

    def _parse_cloze_at(self, text: str, start: int) -> ParsedCloze | None:
        match = CLOZE_START_RE.match(text, start)
        if not match:
            return None

        i = match.end()
        depth = 0
        in_hint = False
        answer_chars: list[str] = []
        hint_chars: list[str] = []

        while i < len(text):
            if not in_hint and depth == 0 and text.startswith("::", i):
                in_hint = True
                i += 2
                continue

            if depth == 0 and text.startswith("}}", i):
                return ParsedCloze(
                    opening=match.group(0),
                    answer="".join(answer_chars),
                    hint="".join(hint_chars) if in_hint else None,
                    end=i + 2,
                )

            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}" and depth > 0:
                depth -= 1

            if in_hint:
                hint_chars.append(ch)
            else:
                answer_chars.append(ch)
            i += 1

        return None

    def _protected_double_close_starts(self, text: str) -> set[int]:
        protected: set[int] = set()
        cursor = 0

        while True:
            match = CLOZE_START_RE.search(text, cursor)
            if not match:
                return protected

            parsed = self._parse_cloze_at(text, match.start())
            if not parsed:
                cursor = match.end()
                continue

            answer_start = match.end()
            protected.add(parsed.end - 2)

            for nested_start in self._protected_double_close_starts(parsed.answer):
                protected.add(answer_start + nested_start)

            if parsed.hint is not None:
                hint_start = answer_start + len(parsed.answer) + 2
                for nested_start in self._protected_double_close_starts(parsed.hint):
                    protected.add(hint_start + nested_start)

            cursor = parsed.end

    def _rewrite_segment(self, segment: str) -> tuple[str, int]:
        if "}}" not in segment:
            return segment, 0

        protected = self._protected_double_close_starts(segment)
        rewritten: list[str] = []
        replacements = 0
        i = 0

        while i < len(segment):
            if segment.startswith("}}", i) and i not in protected:
                rewritten.append(self._replacement)
                replacements += 1
                i += 2
                continue

            rewritten.append(segment[i])
            i += 1

        return "".join(rewritten), replacements

    def _rewrite_trailing_close_before_terminator(self, segment: str) -> tuple[str, str, int]:
        """
        Rewrites a trailing `}` right before cloze closure.
        This handles content like `...}}}` where the first two braces may be parsed
        as cloze end; we replace that boundary `}}` with the configured token.
        Returns (rewritten_segment, cloze_terminator_to_append, replacements_count).
        """
        if not segment.endswith("}"):
            return segment, "}}", 0
        return segment[:-1] + self._boundary_replacement, "}", 1

    def _rewrite_parsed_cloze(self, parsed: ParsedCloze) -> tuple[str, int]:
        fixed_answer, replacements = self._rewrite_segment(parsed.answer)
        fixed_hint = parsed.hint

        if fixed_hint is not None:
            fixed_hint, hint_replacements = self._rewrite_segment(fixed_hint)
            replacements += hint_replacements
            fixed_hint, cloze_terminator, boundary_replacements = (
                self._rewrite_trailing_close_before_terminator(fixed_hint)
            )
        else:
            fixed_answer, cloze_terminator, boundary_replacements = (
                self._rewrite_trailing_close_before_terminator(fixed_answer)
            )

        replacements += boundary_replacements

        rebuilt = [parsed.opening, fixed_answer]
        if fixed_hint is not None:
            rebuilt.extend(["::", fixed_hint])
        rebuilt.append(cloze_terminator)
        return "".join(rebuilt), replacements


def fix_mathjax_in_clozes(text: str) -> tuple[str, int]:
    """
    Rewrites each cloze answer so unsafe internal `}}` sequences become `} }`.
    Nested cloze terminators are preserved, and any adjacent outer `}` is
    rewritten instead.
    Returns (rewritten_text, number_of_replacements).
    """
    return ClozeRewriter(rewrite_tokens()).fix_text(text)
