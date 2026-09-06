"""Theme tokens + application stylesheet (SPEC §6.1).

Single source for every visual constant in the UI: color tokens (light/dark),
spacing constants, and the QSS that styles all widgets.  The mode is stored in
QSettings ("auto" | "light" | "dark"); "auto" follows the OS color scheme.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

from .. import settings

# Spacing / margin scale (px) shared by all widgets.
SP_S, SP_M, SP_L = 4, 8, 12

_ASSETS = Path(__file__).resolve().parents[1] / "assets"


def _asset(name: str) -> str:
    return (_ASSETS / name).as_posix()


@dataclass(frozen=True)
class Tokens:
    name: str
    window: str          # app background
    panel: str           # raised surface: inputs, table, group boxes, toolbar
    canvas: str          # matplotlib figure background
    alt: str             # table alternating rows
    hover: str           # button hover surface
    text: str
    dim: str             # secondary text
    accent: str
    accent_hover: str
    on_accent: str
    border: str
    border_strong: str
    danger: str          # warning rows
    selection: str
    on_selection: str
    grid: str            # matplotlib grid lines


LIGHT = Tokens(
    name="light",
    window="#f2f3f5", panel="#ffffff", canvas="#ffffff", alt="#f7f8fa",
    hover="#eceef1",
    text="#1f2126", dim="#69707a",
    accent="#2f6fed", accent_hover="#4c82f0", on_accent="#ffffff",
    border="#d9dce2", border_strong="#b6bcc7",
    danger="#c0392b",
    selection="#dbe6fd", on_selection="#12233f",
    grid="#d4d7dd",
)

DARK = Tokens(
    name="dark",
    window="#1b1c20", panel="#25262c", canvas="#202126", alt="#222329",
    hover="#2c2d34",
    text="#e8e9ec", dim="#9aa0ab",
    accent="#5b8cff", accent_hover="#729eff", on_accent="#0d1424",
    border="#34363e", border_strong="#4a4d57",
    danger="#e06c5b",
    selection="#2c3b5e", on_selection="#dbe6fd",
    grid="#3a3d46",
)

_active = LIGHT


def tokens_for(mode: str | None = None) -> Tokens:
    """Resolve the requested mode ('auto' follows the OS color scheme)."""
    mode = mode or settings.theme_mode()
    if mode == settings.THEME_LIGHT:
        return LIGHT
    if mode == settings.THEME_DARK:
        return DARK
    scheme = QGuiApplication.styleHints().colorScheme()
    return DARK if scheme == Qt.ColorScheme.Dark else LIGHT


def current() -> Tokens:
    """Tokens of the theme currently applied to the app."""
    return _active


def _palette(t: Tokens) -> QPalette:
    """Match the QSS: every palette-derived color (menu text, item text, glyphs)."""
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(t.window))
    p.setColor(QPalette.ColorRole.WindowText, QColor(t.text))
    p.setColor(QPalette.ColorRole.Base, QColor(t.panel))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(t.alt))
    p.setColor(QPalette.ColorRole.Text, QColor(t.text))
    p.setColor(QPalette.ColorRole.Button, QColor(t.panel))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(t.text))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(t.panel))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(t.text))
    p.setColor(QPalette.ColorRole.Highlight, QColor(t.selection))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(t.on_selection))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(t.dim))
    p.setColor(QPalette.ColorRole.Link, QColor(t.accent))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText,
                 QPalette.ColorRole.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, role, QColor(t.dim))
    return p


def apply(app: QApplication | None = None, tokens: Tokens | None = None) -> Tokens:
    """Apply a theme app-wide; returns the tokens used."""
    global _active
    tokens = tokens or tokens_for()
    _active = tokens
    app = app or QApplication.instance()
    app.setPalette(_palette(tokens))
    app.setStyleSheet(stylesheet(tokens))
    for w in QApplication.allWidgets():  # repaint children that cache their backing store
        w.update()
    return tokens


def stylesheet(t: Tokens) -> str:
    return f"""
QWidget {{ font-size: 10pt; }}

QMainWindow, QDialog {{ background: {t.window}; }}
QLabel {{ background: transparent; }}

QMenuBar {{
    background: {t.window}; color: {t.text};
    border-bottom: 1px solid {t.border};
}}
QMenuBar::item {{ padding: 4px 9px; border-radius: 4px; background: transparent; }}
QMenuBar::item:selected {{ background: {t.selection}; color: {t.on_selection}; }}

QMenu {{
    background: {t.panel}; color: {t.text};
    border: 1px solid {t.border}; border-radius: 6px; padding: 4px;
}}
QMenu::item {{ padding: 5px 24px 5px 10px; border-radius: 4px; background: transparent; }}
QMenu::item:selected {{ background: {t.selection}; color: {t.on_selection}; }}
QMenu::item:disabled {{ color: {t.dim}; }}
QMenu::separator {{ height: 1px; background: {t.border}; margin: 4px 8px; }}

QToolBar {{
    background: {t.panel}; border: none;
    border-bottom: 1px solid {t.border};
    padding: 3px; spacing: 2px;
}}
QToolBar::separator {{ background: {t.border}; width: 1px; margin: 4px 3px; }}
QToolButton {{
    background: transparent; border: none; border-radius: 4px; padding: 3px;
}}
QToolButton:hover {{ background: {t.hover}; }}
QToolButton:pressed, QToolButton:checked {{ background: {t.selection}; color: {t.on_selection}; }}
QToolBar QLabel {{ background: transparent; color: {t.text}; padding-right: 6px; }}

QPushButton {{
    background: {t.panel}; color: {t.text};
    border: 1px solid {t.border_strong}; border-radius: 5px;
    padding: 5px 12px; min-height: 14px;
}}
QPushButton:hover {{ background: {t.hover}; }}
QPushButton:pressed {{ background: {t.border}; }}
QPushButton:disabled {{ color: {t.dim}; border-color: {t.border}; }}
QPushButton:default {{
    background: {t.accent}; color: {t.on_accent};
    border-color: {t.accent}; font-weight: 600;
}}
QPushButton:default:hover {{ background: {t.accent_hover}; }}
QPushButton:default:pressed {{ background: {t.accent}; }}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {t.panel}; color: {t.text};
    border: 1px solid {t.border_strong}; border-radius: 5px;
    padding: 4px 8px;
    selection-background-color: {t.selection}; selection-color: {t.on_selection};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {t.accent};
}}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
    color: {t.dim}; background: {t.window}; border-color: {t.border};
}}
QLineEdit[readOnly="true"] {{ color: {t.text}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox::down-arrow {{ image: url({_asset("arrow-down.svg")}); width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background: {t.panel}; color: {t.text};
    border: 1px solid {t.border}; border-radius: 4px;
    selection-background-color: {t.selection}; selection-color: {t.on_selection};
}}

QCheckBox {{ background: transparent; spacing: 6px; }}
QCheckBox:disabled {{ color: {t.dim}; }}
QCheckBox::indicator {{
    width: 15px; height: 15px;
    border: 1px solid {t.border_strong}; border-radius: 3px;
    background: {t.panel};
}}
QCheckBox::indicator:hover {{ border-color: {t.accent}; }}
QCheckBox::indicator:checked {{
    background: {t.accent}; border-color: {t.accent};
    image: url({_asset("check.svg")});
}}
QCheckBox::indicator:disabled {{ background: {t.window}; border-color: {t.border}; }}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: transparent; border: none; width: 16px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {t.hover}; border-radius: 3px;
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url({_asset("arrow-up.svg")}); width: 8px; height: 8px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url({_asset("arrow-down.svg")}); width: 8px; height: 8px;
}}

QGroupBox {{
    background: {t.panel};
    border: 1px solid {t.border}; border-radius: 7px;
    margin-top: 17px; padding: 9px 8px 9px 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 9px; top: 1px; padding: 0 3px;
    color: {t.dim}; font-size: 8pt; font-weight: 700; letter-spacing: 0.5px;
}}

QDockWidget::title {{
    background: {t.window}; color: {t.text}; padding: 6px 10px 5px;
    border-bottom: 1px solid {t.border};
    font-weight: 600;
}}

QTableWidget {{
    background: {t.panel}; alternate-background-color: {t.alt};
    gridline-color: {t.border};
    border: 1px solid {t.border}; border-radius: 7px;
    selection-background-color: {t.selection}; selection-color: {t.on_selection};
}}
QTableWidget::item {{ padding: 2px 4px; }}
QTableWidget::item:selected {{ background: {t.selection}; color: {t.on_selection}; }}
QHeaderView::section {{
    background: {t.window}; color: {t.dim};
    border: none; border-bottom: 1px solid {t.border};
    padding: 5px 6px; font-size: 9pt; font-weight: 600;
}}

QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background: {t.border_strong}; border-radius: 4px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {t.dim}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{
    background: {t.border_strong}; border-radius: 4px; min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{ background: {t.dim}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QSplitter::handle {{ background: {t.window}; }}

QStatusBar {{
    background: {t.window};
    border-top: 1px solid {t.border};
    color: {t.dim};
}}
QStatusBar QLabel {{ color: {t.dim}; }}

QToolTip {{
    background: {t.panel}; color: {t.text};
    border: 1px solid {t.border_strong}; border-radius: 4px;
    padding: 4px 8px;
}}
"""
