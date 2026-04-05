from aqt import mw
from aqt.utils import tooltip

from .cloze_rewriter import fix_mathjax_in_clozes


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
