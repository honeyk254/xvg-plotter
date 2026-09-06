"""File table with metadata + async folder scanner (SPEC §6.1, §6.2, §10.2)."""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
)

from ..core.models import XvgFile
from ..core.parser import parse_file
from .theme import current

COLS = ["", "Name", "Title", "Series", "Points", "Size", "Modified"]


def _human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _reveal(p: Path) -> None:
    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", str(p)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(p)])
    else:
        subprocess.Popen(["xdg-open", str(p.parent)])


class FolderScanner(QThread):
    """Parses every *.xvg in a folder on a worker thread (SPEC §13)."""

    file_parsed = Signal(object)
    done = Signal()

    def __init__(self, folder: Path, parent=None):
        super().__init__(parent)
        self._folder = Path(folder)
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            entries = sorted(self._folder.iterdir())
        except OSError:
            entries = []
        for p in entries:
            if self._stop:
                return
            if p.is_file() and p.suffix.lower() == ".xvg":
                self.file_parsed.emit(parse_file(p))
        self.done.emit()


class FileTable(QTableWidget):
    overlay_toggled = Signal(object, bool)
    file_activated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(0, len(COLS), parent)
        self.setHorizontalHeaderLabels(COLS)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(False)
        self.setAlternatingRowColors(True)
        self.itemChanged.connect(self._on_item_changed)
        self.cellClicked.connect(self._on_click)
        self.cellDoubleClicked.connect(self._on_double_click)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self._updating = False
        self._warned: set[Path] = set()

    def retheme(self) -> None:
        color = QBrush(QColor(current().danger))
        for r in range(self.rowCount()):
            f = self.item(r, 1).data(Qt.ItemDataRole.UserRole)
            if f and f.path in self._warned:
                self.item(r, 1).setForeground(color)

    def clear_all(self) -> None:
        self.setSortingEnabled(False)
        self.setRowCount(0)
        self._warned.clear()

    def finish_scan(self) -> None:
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)

    def add_file(self, f: XvgFile) -> None:
        self._updating = True
        r = self.rowCount()
        self.insertRow(r)
        chk = QTableWidgetItem()
        chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                     | Qt.ItemFlag.ItemIsSelectable)
        chk.setCheckState(Qt.CheckState.Unchecked)
        self.setItem(r, 0, chk)

        name = QTableWidgetItem(f.path.name)
        name.setData(Qt.ItemDataRole.UserRole, f)
        tips = list(f.warnings)
        if f.stats.directives_ignored:  # C10: never silently drop grace styling
            tips.append(f"{f.stats.directives_ignored} grace directive(s) ignored — "
                        f"in-file styling not applied")
        if tips:
            self._warned.add(f.path)
            name.setText("⚠ " + f.path.name)
            name.setToolTip("\n".join(tips))
            name.setForeground(QBrush(QColor(current().danger)))

        try:
            size = _human(f.path.stat().st_size)
            mod = dt.datetime.fromtimestamp(f.path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            size, mod = "—", "—"
        ds = f.datasets[0] if f.datasets else None
        items = [
            name,
            QTableWidgetItem(f.title or "—"),
            QTableWidgetItem(str(sum(len(d.series) for d in f.datasets))),
            QTableWidgetItem(str(f.stats.rows_ok) if f.datasets else "—"),
            QTableWidgetItem(size),
            QTableWidgetItem(mod),
        ]
        for c, it in enumerate(items, start=1):
            self.setItem(r, c, it)
        self._updating = False

    # -- selection ----------------------------------------------------------

    def ordered_checked(self) -> list[XvgFile]:
        out = []
        for r in range(self.rowCount()):
            if self.item(r, 0).checkState() == Qt.CheckState.Checked:
                f = self.item(r, 1).data(Qt.ItemDataRole.UserRole)
                if f:
                    out.append(f)
        return out

    def sync_check(self, path: Path, on: bool) -> None:
        r = self._row_of(path)
        if r is not None:
            self._updating = True
            self.item(r, 0).setCheckState(
                Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)
            self._updating = False

    def set_checked_only(self, path: Path) -> None:
        for r in range(self.rowCount()):
            f = self.item(r, 1).data(Qt.ItemDataRole.UserRole)
            self.sync_check(f.path, f.path == path)

    def _row_of(self, path: Path) -> int | None:
        for r in range(self.rowCount()):
            f = self.item(r, 1).data(Qt.ItemDataRole.UserRole)
            if f and f.path == path:
                return r
        return None

    def apply_filter(self, text: str) -> None:
        t = text.strip().lower()
        for r in range(self.rowCount()):
            name = self.item(r, 1).text().lower()
            title = self.item(r, 2).text().lower()
            self.setRowHidden(r, bool(t) and t not in name and t not in title)

    # -- events ---------------------------------------------------------------

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating or item.column() != 0:
            return
        f = self.item(item.row(), 1).data(Qt.ItemDataRole.UserRole)
        if f:
            self.overlay_toggled.emit(
                f, item.checkState() == Qt.CheckState.Checked)

    def _on_click(self, row: int, col: int) -> None:
        # click a row body to plot it (PRD U3); column 0 is the overlay checkbox
        if col == 0 or self._updating:
            return
        f = self.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if f:
            self.file_activated.emit(f)

    def _on_double_click(self, row: int, _col: int) -> None:
        f = self.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if f:
            self.file_activated.emit(f)

    def _menu(self, pos) -> None:
        r = self.rowAt(pos.y())
        if r < 0:
            return
        f = self.item(r, 1).data(Qt.ItemDataRole.UserRole)
        m = QMenu(self)
        a_show = m.addAction("Show in folder")
        a_copy = m.addAction("Copy path")
        act = m.exec(self.viewport().mapToGlobal(pos))
        if act == a_show:
            try:
                _reveal(f.path)
            except OSError as e:
                QMessageBox.warning(self, "Show in folder", str(e))
        elif act == a_copy:
            QGuiApplication.clipboard().setText(str(f.path))
