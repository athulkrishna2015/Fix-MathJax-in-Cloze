from aqt import mw
from aqt.utils import tooltip

from .config import addon_config, is_valid_replacement, replacement_token
from .support_ui import build_support_tab


def show_config_dialog() -> None:
    from aqt.qt import (
        QCheckBox,
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
    replacement_input = QLineEdit(addon_config().get("replacement", replacement_token()))
    settings_form.addRow("Replacement token", replacement_input)
    
    nbsp_checkbox = QCheckBox("Remove non-breaking spaces (&nbsp;) inside MathJax")
    nbsp_checkbox.setChecked(addon_config().get("remove_nbsp_in_mathjax", True))
    settings_form.addRow(nbsp_checkbox)
    
    settings_layout.addLayout(settings_form)

    help_text = QLabel(
        "Replacement token is used when rewriting unsafe `}}` inside cloze text. "
        "The value must be non-empty and cannot contain `}}`.\n\n"
        "Removing non-breaking spaces (&nbsp;) solves rendering issues inside MathJax "
        "created by typing multiple spaces or after pasting code."
    )
    help_text.setWordWrap(True)
    settings_layout.addWidget(help_text)
    settings_layout.addStretch()

    tabs.addTab(settings_tab, "Settings")
    tabs.addTab(build_support_tab(), "Support")

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    layout.addWidget(buttons)

    def on_accept() -> None:
        replacement = replacement_input.text()
        if not is_valid_replacement(replacement):
            QMessageBox.warning(
                dialog,
                "Invalid replacement",
                "Replacement must be a non-empty string and cannot contain `}}`.",
            )
            return

        config = addon_config()
        config["replacement"] = replacement
        config["remove_nbsp_in_mathjax"] = nbsp_checkbox.isChecked()
        mw.addonManager.writeConfig(__name__, config)
        dialog.accept()
        tooltip("Configuration saved.")

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)
    dialog.exec()
