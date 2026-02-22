import re

from aqt import mw
from aqt.gui_hooks import browser_menus_did_init, reviewer_will_show_context_menu
from aqt.qt import QAction
from aqt.utils import tooltip

CLOZE_START_RE = re.compile(r"\{\{c\d+::", re.IGNORECASE)


def _replacement_token() -> str:
    config = mw.addonManager.getConfig(__name__) or {}
    return config.get("replacement", "} }")


def _fix_internal_double_close(answer: str) -> tuple[str, int]:
    count = answer.count("}}")
    if count == 0:
        return answer, 0
    return answer.replace("}}", _replacement_token()), count


def fix_mathjax_in_clozes(text: str) -> tuple[str, int]:
    """
    Rewrites each cloze answer so internal `}}` sequences become `} }`.
    This avoids accidental cloze termination with MathJax brace-heavy content.
    Returns (rewritten_text, number_of_replacements).
    """
    result: list[str] = []
    cursor = 0
    replacements = 0

    while True:
        match = CLOZE_START_RE.search(text, cursor)
        if not match:
            result.append(text[cursor:])
            break

        result.append(text[cursor:match.start()])

        i = match.end()
        depth = 0
        in_hint = False
        answer_chars: list[str] = []
        hint_chars: list[str] = []
        closed = False

        while i < len(text):
            if not in_hint and depth == 0 and text.startswith("::", i):
                in_hint = True
                i += 2
                continue

            if depth == 0 and text.startswith("}}", i):
                i += 2
                closed = True
                break

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

        if not closed:
            # Malformed cloze: keep remainder unchanged.
            result.append(text[match.start():])
            break

        fixed_answer, replaced = _fix_internal_double_close("".join(answer_chars))
        replacements += replaced

        rebuilt = [match.group(0), fixed_answer]
        if in_hint:
            rebuilt.extend(["::", "".join(hint_chars)])
        rebuilt.append("}}")

        result.append("".join(rebuilt))
        cursor = i

    return "".join(result), replacements


def _fix_note(note) -> tuple[bool, int]:
    changed = False
    replacements = 0

    for field_name in note.keys():
        original = note[field_name]
        rewritten, count = fix_mathjax_in_clozes(original)
        if count > 0:
            note[field_name] = rewritten
            replacements += count
            changed = True

    if changed:
        mw.col.update_note(note)

    return changed, replacements


def on_browser_fix(browser) -> None:
    nids = browser.selectedNotes()
    if not nids:
        tooltip("No notes selected.")
        return

    mw.checkpoint("Fix MathJax in Cloze")
    mw.progress.start(label="Fixing MathJax in selected notes...")

    changed_notes = 0
    replacements = 0

    try:
        total = len(nids)
        for index, nid in enumerate(nids, start=1):
            mw.progress.update(value=index, max=total)
            note = mw.col.get_note(nid)
            changed, changed_count = _fix_note(note)
            if changed:
                changed_notes += 1
                replacements += changed_count
    finally:
        mw.progress.finish()

    mw.reset()

    if changed_notes == 0:
        tooltip("No cloze conflicts found.")
    else:
        tooltip(f"Updated {changed_notes} notes ({replacements} replacements).")


def on_reviewer_fix(reviewer) -> None:
    card = reviewer.card
    if not card:
        return

    note = card.note()

    mw.checkpoint("Fix MathJax in Cloze")
    changed, replacements = _fix_note(note)

    if not changed:
        tooltip("No cloze conflicts found in this note.")
        return

    mw.reset()
    try:
        reviewer._redraw_current_card()
    except Exception:
        pass

    tooltip(f"Updated note ({replacements} replacements).")


def setup_browser_menu(browser) -> None:
    action = QAction("Fix MathJax in Cloze (selected notes)", browser)
    action.triggered.connect(lambda _checked=False, b=browser: on_browser_fix(b))
    browser.form.menu_Notes.addSeparator()
    browser.form.menu_Notes.addAction(action)


def setup_reviewer_menu(reviewer, menu) -> None:
    action = menu.addAction("Fix MathJax in This Note")
    action.triggered.connect(lambda _checked=False, r=reviewer: on_reviewer_fix(r))


browser_menus_did_init.append(setup_browser_menu)
reviewer_will_show_context_menu.append(setup_reviewer_menu)
