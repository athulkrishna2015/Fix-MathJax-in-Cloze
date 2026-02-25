import importlib.util
import sys
import types
import unittest
from pathlib import Path


def load_addon_module(config: dict | None = None):
    aqt = types.ModuleType("aqt")
    qt = types.ModuleType("aqt.qt")
    utils = types.ModuleType("aqt.utils")
    gui_hooks = types.ModuleType("aqt.gui_hooks")

    class DummyAction:
        def __init__(self, *args, **kwargs):
            pass

    class DummyAddonManager:
        def __init__(self, cfg):
            self._cfg = cfg

        def getConfig(self, _name):
            return self._cfg

    qt.QAction = DummyAction
    utils.tooltip = lambda *_args, **_kwargs: None
    gui_hooks.browser_menus_did_init = []
    gui_hooks.reviewer_will_show_context_menu = []
    aqt.mw = types.SimpleNamespace(addonManager=DummyAddonManager(config or {}))

    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = qt
    sys.modules["aqt.utils"] = utils
    sys.modules["aqt.gui_hooks"] = gui_hooks

    module_path = Path(__file__).resolve().parents[1] / "__init__.py"
    spec = importlib.util.spec_from_file_location("addon_module_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
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


if __name__ == "__main__":
    unittest.main()
