from dataclasses import dataclass
from pathlib import Path

from aqt.utils import tooltip
from aqt.webview import AnkiWebView

SUPPORT_QR_WIDTH = 360


@dataclass(frozen=True)
class SupportOption:
    name: str
    value: str
    image_name: str
    copy_label: str


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


def build_support_tab():
    from aqt.qt import QLabel, QScrollArea, QVBoxLayout, QWidget

    tab = QWidget()
    layout = QVBoxLayout(tab)

    intro = QLabel("Support the add-on using any of the QR codes or copy buttons below.")
    intro.setWordWrap(True)
    layout.addWidget(intro)

    support_webview = AnkiWebView(tab)
    support_webview.setFixedHeight(40)
    kofi_html = """
<html>
<head>
<style>
  body { background-color: transparent; margin: 0; padding: 0; overflow: hidden; }
</style>
<script type='text/javascript' src='https://storage.ko-fi.com/cdn/widget/Widget_2.js'></script>
<script type='text/javascript'>
  kofiwidget2.init('Support me on Ko-fi', '#72a4f2', 'D1D01W6NQT');
  kofiwidget2.draw();
</script>
</head>
<body></body>
</html>
"""
    support_webview.setHtml(kofi_html)
    layout.addWidget(support_webview)

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
