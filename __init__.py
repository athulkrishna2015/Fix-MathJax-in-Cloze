import re
from dataclasses import dataclass
from pathlib import Path

from aqt import mw
from aqt.gui_hooks import browser_menus_did_init, reviewer_will_show_context_menu
from aqt.qt import QAction
from aqt.utils import tooltip

CLOZE_START_RE = re.compile(r"\{\{c\d+::", re.IGNORECASE)
DEFAULT_REPLACEMENT = "} }"
SUPPORT_QR_WIDTH = 360


@dataclass(frozen=True)
class ParsedCloze:
    opening: str
    answer: str
    hint: str | None
    end: int


@dataclass(frozen=True)
class SupportOption:
    name: str
    value: str
    image_name: str
    copy_label: str


@dataclass(frozen=True)
class RewriteTokens:
    replacement: str
    boundary_replacement: str


SUPPORT_OPTIONS = (
    SupportOption("UPI", "athulkrishnasv2015-2@okhdfcbank", "UPI.jpg", "UPI ID"),
    SupportOption("BTC", "bc1qrrek3m7sr33qujjrktj949wav6mehdsk057cfx", "BTC.jpg", "BTC address"),
    SupportOption(
        "ETH",
        "0xce6899e4903EcB08bE5Be65E44549fadC3F45D27",
        "ETH.jpg",
        "ETH address",
    ),
)


def _addon_config() -> dict:
    config = mw.addonManager.getConfig(__name__) or {}
    if isinstance(config, dict):
        return config
    return {}


def _is_valid_replacement(value) -> bool:
    return isinstance(value, str) and bool(value) and "}}" not in value


def _replacement_token() -> str:
    replacement = _addon_config().get("replacement", DEFAULT_REPLACEMENT)
    if _is_valid_replacement(replacement):
        return replacement
    return DEFAULT_REPLACEMENT


def _rewrite_tokens() -> RewriteTokens:
    replacement = _replacement_token()
    boundary_replacement = replacement if replacement.endswith("}") else DEFAULT_REPLACEMENT
    return RewriteTokens(
        replacement=replacement,
        boundary_replacement=boundary_replacement,
    )


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
    return ClozeRewriter(_rewrite_tokens()).fix_text(text)


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


def _copy_support_value(text: str, label: str) -> None:
    from aqt.qt import QApplication

    clipboard = QApplication.clipboard()
    if clipboard is None:
        return
    clipboard.setText(text)
    tooltip(f"Copied {label}.")


def _support_qr_path(image_name: str) -> Path:
    return Path(__file__).resolve().parent / "Support" / image_name


def _build_support_card(option: SupportOption):
    from aqt.qt import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QPixmap,
        Qt,
        QVBoxLayout,
    )

    card = QFrame()
    card.setFrameShape(QFrame.Shape.StyledPanel)

    layout = QVBoxLayout(card)
    title = QLabel(option.name)
    title.setStyleSheet("font-weight: 600; font-size: 15px;")
    layout.addWidget(title)

    value_label = QLabel(option.value)
    value_label.setWordWrap(True)
    value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    layout.addWidget(value_label)

    qr_label = QLabel()
    qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    qr_label.setMinimumWidth(SUPPORT_QR_WIDTH)
    pixmap = QPixmap(str(_support_qr_path(option.image_name)))
    if pixmap.isNull():
        qr_label.setText("QR code not available.")
    else:
        qr_label.setPixmap(
            pixmap.scaledToWidth(
                SUPPORT_QR_WIDTH,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    layout.addWidget(qr_label)

    button_row = QHBoxLayout()
    button_row.addStretch()
    copy_button = QPushButton(f"Copy {option.copy_label}")
    copy_button.clicked.connect(
        lambda _checked=False, value=option.value, label=option.copy_label: _copy_support_value(
            value, label
        )
    )
    button_row.addWidget(copy_button)
    layout.addLayout(button_row)
    return card


def _build_support_tab():
    from aqt.qt import QLabel, QScrollArea, QVBoxLayout, QWidget

    tab = QWidget()
    layout = QVBoxLayout(tab)

    intro = QLabel("Support the add-on using any of the QR codes or copy buttons below.")
    intro.setWordWrap(True)
    layout.addWidget(intro)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    scroll_container = QWidget()
    scroll_layout = QVBoxLayout(scroll_container)

    for option in SUPPORT_OPTIONS:
        scroll_layout.addWidget(_build_support_card(option))

    scroll_layout.addStretch()
    scroll_area.setWidget(scroll_container)
    layout.addWidget(scroll_area)
    return tab


def show_config_dialog() -> None:
    from aqt.qt import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    dialog = QDialog(mw)
    dialog.setWindowTitle("Fix MathJax in Cloze")
    dialog.resize(620, 760)

    layout = QVBoxLayout(dialog)
    tabs = QTabWidget()
    layout.addWidget(tabs)

    settings_tab = QWidget()
    settings_layout = QVBoxLayout(settings_tab)
    settings_form = QFormLayout()
    replacement_input = QLineEdit(_addon_config().get("replacement", _replacement_token()))
    settings_form.addRow("Replacement token", replacement_input)
    settings_layout.addLayout(settings_form)

    help_text = QLabel(
        "Used when rewriting unsafe `}}` inside cloze text. "
        "The value must be non-empty and cannot contain `}}`."
    )
    help_text.setWordWrap(True)
    settings_layout.addWidget(help_text)
    settings_layout.addStretch()

    tabs.addTab(settings_tab, "Settings")
    tabs.addTab(_build_support_tab(), "Support")

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    layout.addWidget(buttons)

    def on_accept() -> None:
        replacement = replacement_input.text()
        if not _is_valid_replacement(replacement):
            QMessageBox.warning(
                dialog,
                "Invalid replacement",
                "Replacement must be a non-empty string and cannot contain `}}`.",
            )
            return

        config = _addon_config()
        config["replacement"] = replacement
        mw.addonManager.writeConfig(__name__, config)
        dialog.accept()
        tooltip("Configuration saved.")

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)
    dialog.exec()


def setup_browser_menu(browser) -> None:
    action = QAction("Fix MathJax in Cloze (selected notes)", browser)
    action.triggered.connect(lambda _checked=False, b=browser: on_browser_fix(b))
    browser.form.menu_Notes.addSeparator()
    browser.form.menu_Notes.addAction(action)


def setup_reviewer_menu(reviewer, menu) -> None:
    action = menu.addAction("Fix MathJax in This Note")
    action.triggered.connect(lambda _checked=False, r=reviewer: on_reviewer_fix(r))


def _register_config_action() -> None:
    addon_manager = getattr(mw, "addonManager", None)
    if addon_manager is None or not hasattr(addon_manager, "setConfigAction"):
        return
    addon_manager.setConfigAction(__name__, show_config_dialog)


browser_menus_did_init.append(setup_browser_menu)
reviewer_will_show_context_menu.append(setup_reviewer_menu)
_register_config_action()
