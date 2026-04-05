from aqt import mw
from aqt.gui_hooks import (
    browser_menus_did_init,
    browser_will_show_context_menu,
    reviewer_will_show_context_menu,
)
from aqt.qt import QAction

from .config_dialog import show_config_dialog
from .note_ops import on_browser_fix, on_reviewer_fix


def setup_browser_menu(browser) -> None:
    action = QAction("Fix MathJax in Cloze (selected notes)", browser)
    action.triggered.connect(lambda _checked=False, b=browser: on_browser_fix(b))
    browser.form.menu_Notes.addSeparator()
    browser.form.menu_Notes.addAction(action)


def setup_browser_context_menu(browser, menu) -> None:
    menu.addSeparator()
    action = menu.addAction("Fix MathJax in Cloze (selected notes)")
    action.triggered.connect(lambda _checked=False, b=browser: on_browser_fix(b))


def setup_reviewer_menu(reviewer, menu) -> None:
    action = menu.addAction("Fix MathJax in This Note")
    action.triggered.connect(lambda _checked=False, r=reviewer: on_reviewer_fix(r))


def _register_config_action() -> None:
    addon_manager = getattr(mw, "addonManager", None)
    if addon_manager is None or not hasattr(addon_manager, "setConfigAction"):
        return
    addon_manager.setConfigAction(__name__, show_config_dialog)


def register_all() -> None:
    browser_menus_did_init.append(setup_browser_menu)
    browser_will_show_context_menu.append(setup_browser_context_menu)
    reviewer_will_show_context_menu.append(setup_reviewer_menu)
    _register_config_action()
