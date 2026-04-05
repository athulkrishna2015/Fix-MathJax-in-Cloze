import importlib
import sys
import types
import unittest
from pathlib import Path


def load_addon_module(config: dict | None = None):
    aqt = types.ModuleType("aqt")
    qt = types.ModuleType("aqt.qt")
    utils = types.ModuleType("aqt.utils")
    gui_hooks = types.ModuleType("aqt.gui_hooks")
    webview = types.ModuleType("aqt.webview")

    class DummyAction:
        def __init__(self, *args, **kwargs):
            pass

    class DummyAddonManager:
        def __init__(self, cfg):
            self._cfg = cfg

        def getConfig(self, _name):
            return self._cfg

        def setConfigAction(self, _name, _callback):
            return None

        def writeConfig(self, _name, cfg):
            self._cfg = cfg

    class DummyWebView:
        def __init__(self, *args, **kwargs):
            pass

        def setFixedHeight(self, *args):
            pass

        def setHtml(self, *args):
            pass

    qt.QAction = DummyAction
    utils.tooltip = lambda *_args, **_kwargs: None
    gui_hooks.browser_menus_did_init = []
    gui_hooks.browser_will_show_context_menu = []
    gui_hooks.reviewer_will_show_context_menu = []
    webview.AnkiWebView = DummyWebView
    aqt.mw = types.SimpleNamespace(addonManager=DummyAddonManager(config or {}))

    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = qt
    sys.modules["aqt.utils"] = utils
    sys.modules["aqt.gui_hooks"] = gui_hooks
    sys.modules["aqt.webview"] = webview

    # Remove any previously cached addon submodules so reimport picks up fresh mocks.
    for key in list(sys.modules.keys()):
        if key == "addon" or key.startswith("addon."):
            del sys.modules[key]

    # Add the addon's parent directory to sys.path so 'addon' is importable as a package.
    addon_parent = str(Path(__file__).resolve().parents[1])
    if addon_parent not in sys.path:
        sys.path.insert(0, addon_parent)

    module = importlib.import_module("addon")
    return module


class FixMathJaxInClozeTests(unittest.TestCase):
    def test_rewrites_trailing_boundary_case(self):
        mod = load_addon_module()
        text = r"{{c1::\mathbf{0}}}"
        rewritten, count = mod.fix_mathjax_in_clozes(text)
        self.assertEqual(rewritten, r"{{c1::\mathbf{0} }}")
        self.assertEqual(count, 1)

    def test_boundary_rewrite_stays_valid_with_non_brace_custom_replacement(self):
        mod = load_addon_module({"replacement": "<X>"})
        text = r"{{c1::\mathbf{0}}}"
        rewritten, count = mod.fix_mathjax_in_clozes(text)
        self.assertEqual(rewritten, r"{{c1::\mathbf{0} }}")
        self.assertEqual(count, 1)

    def test_rewrites_internal_double_close_in_hint(self):
        mod = load_addon_module()
        text = r"{{c1::ans::[$]\frac{foo}{\frac{bar}{baz}}[/$]}}"
        rewritten, count = mod.fix_mathjax_in_clozes(text)
        self.assertEqual(
            rewritten,
            r"{{c1::ans::[$]\frac{foo}{\frac{bar}{baz} }[/$]}}",
        )
        self.assertEqual(count, 1)

    def test_malformed_cloze_does_not_block_later_clozes(self):
        mod = load_addon_module()
        text = r"{{c1::{broken text {{c2::[$]\frac{foo}{\frac{bar}{baz}}[/$]}}"
        rewritten, count = mod.fix_mathjax_in_clozes(text)
        self.assertEqual(
            rewritten,
            r"{{c1::{broken text {{c2::[$]\frac{foo}{\frac{bar}{baz} }[/$]}}",
        )
        self.assertEqual(count, 1)

    def test_preserves_nested_cloze_terminator_and_rewrites_outer_brace_boundary(self):
        mod = load_addon_module()
        text = (
            r"Formula: {{c3::\(\sin i_{{{c1::c}}} = \frac{n_2}{n_1}\), "
            r"\(n_1>n_2\)}}"
        )
        rewritten, count = mod.fix_mathjax_in_clozes(text)
        self.assertEqual(
            rewritten,
            r"Formula: {{c3::\(\sin i_{{{c1::c}} } = \frac{n_2}{n_1}\), "
            r"\(n_1>n_2\)}}",
        )
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
