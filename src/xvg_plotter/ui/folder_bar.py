"""Folder bar: Open Folder, path/recents combo, refresh, filter (SPEC §6.1)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from .. import settings
from . import theme
from .icons import icon


class FolderBar(QWidget):
    folder_requested = Signal(str)
    refresh_requested = Signal()
    filter_changed = Signal(str)
    pin_toggled = Signal(bool)
    recursive_toggled = Signal(bool)

    def __init__(self, recents: list[str], parent=None):
        super().__init__(parent)
        self.btn_open = QPushButton(icon("folder"), self.tr("Open Folder…"))
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo.setMinimumContentsLength(14)
        self.combo.addItems(recents)
        self.combo.setToolTip(self.tr(
            "Current folder; the list holds pinned and recent folders"))
        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(icon("refresh"))
        self.btn_refresh.setToolTip(self.tr("Rescan folder (F5)"))
        self.btn_pin = QPushButton()
        self.btn_pin.setIcon(icon("pin"))
        self.btn_pin.setCheckable(True)
        self.btn_pin.setToolTip(self.tr("Pin this folder to the top of the list"))
        self.chk_sub = QCheckBox(self.tr("subfolders"))
        self.chk_sub.setChecked(bool(settings.get("scan/recursive", False)))
        self.chk_sub.setToolTip(self.tr(
            "Include .xvg files in subfolders when scanning"))
        self.edit_filter = QLineEdit()
        self.edit_filter.setPlaceholderText(self.tr("filter…"))
        self.edit_filter.setClearButtonEnabled(True)
        self.edit_filter.addAction(icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        self.edit_filter.setMinimumWidth(112)
        self.edit_filter.setMaximumWidth(200)
        self.edit_filter.setToolTip(self.tr(
            "Filter the list by file name or title (Ctrl+F; Esc clears)"))
        self.edit_filter.installEventFilter(self)  # Esc clears (C19)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(theme.SP_S, theme.SP_S, theme.SP_S, theme.SP_S)
        lay.setSpacing(theme.SP_S)
        lay.addWidget(self.btn_open)
        lay.addWidget(self.combo, 1)
        lay.addWidget(self.btn_refresh)
        lay.addWidget(self.btn_pin)
        lay.addWidget(self.chk_sub)
        lay.addWidget(self.edit_filter)

        self.btn_open.clicked.connect(self.pick_folder)
        self.combo.activated.connect(self._emit_current)
        self.combo.lineEdit().returnPressed.connect(self._emit_current)
        self.btn_refresh.clicked.connect(self.refresh_requested)
        self.btn_pin.toggled.connect(self.pin_toggled)
        self.chk_sub.toggled.connect(self.recursive_toggled)
        self.edit_filter.textChanged.connect(self.filter_changed)

    def eventFilter(self, obj, ev) -> bool:
        if obj is self.edit_filter and ev.type() == QEvent.Type.KeyPress \
                and ev.key() == Qt.Key.Key_Escape:
            if self.edit_filter.text():
                self.edit_filter.clear()
            else:
                self.edit_filter.clearFocus()
            return True
        return super().eventFilter(obj, ev)

    def retheme(self) -> None:
        self.btn_open.setIcon(icon("folder"))
        self.btn_refresh.setIcon(icon("refresh"))
        self.btn_pin.setIcon(icon("pin"))
        while self.edit_filter.actions():
            self.edit_filter.removeAction(self.edit_filter.actions()[0])
        self.edit_filter.addAction(icon("search"), QLineEdit.ActionPosition.LeadingPosition)

    def set_path(self, path: str, recents: list[str]) -> None:
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(recents)
        self.combo.setCurrentText(path)
        self.combo.blockSignals(False)

    def set_pinned(self, on: bool) -> None:
        self.btn_pin.blockSignals(True)
        self.btn_pin.setChecked(on)
        self.btn_pin.blockSignals(False)
        self.btn_pin.setToolTip(self.tr("Unpin this folder") if on else
                                self.tr("Pin this folder to the top of the list"))

    def recursive(self) -> bool:
        return self.chk_sub.isChecked()

    def current_folder(self) -> str:
        return self.combo.currentText().strip()

    def filter_text(self) -> str:
        return self.edit_filter.text()

    def pick_folder(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, self.tr("Open analysis folder"),
            self.combo.currentText() or str(Path.home()))
        if d:
            self.folder_requested.emit(d)

    def _emit_current(self, *_):
        t = self.current_folder()
        if t:
            # MainWindow validates and reports invalid paths via the status bar
            self.folder_requested.emit(t)
