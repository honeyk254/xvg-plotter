"""Series dock: per-file series toggles + averaging/smoothing options (SPEC §6.1, §7)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QScrollArea,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..core.models import XvgFile, series_label
from . import theme


@dataclass
class AnalysisState:
    average: bool = False
    members: bool = False
    common_range: bool = False
    smooth: bool = False
    window: int = 21


@dataclass
class _Group:
    file: XvgFile
    box: QGroupBox
    combo: QComboBox | None
    checks: list[QCheckBox] = field(default_factory=list)
    swatches: dict[int, QToolButton] = field(default_factory=dict)


class SeriesDock(QWidget):
    series_toggled = Signal(object, int, bool)   # (file, series index, visible)
    dataset_changed = Signal(object, int)
    options_changed = Signal()
    series_color_changed = Signal(object, int, int, object)  # (file, ds, series, color|None)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._groups: dict[Path, _Group] = {}
        self._updating = False

        self._inner = QWidget()
        self._vbox = QVBoxLayout(self._inner)
        self._vbox.setContentsMargins(theme.SP_S, theme.SP_S, theme.SP_S, theme.SP_S)
        self._vbox.setSpacing(theme.SP_S + 1)
        self._vbox.addStretch(1)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self._inner)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.chk_average = QCheckBox("Average replicas (mean ± SD)")
        self.chk_average.setToolTip("Overlay the mean of matching replicas with a "
                                    "shaded ± SD band (C27)")
        self.chk_members = QCheckBox("Show member curves")
        self.chk_members.setToolTip("Draw each replica faintly under the mean")
        self.chk_common = QCheckBox("Common time range")
        self.chk_common.setToolTip(
            "Average only the time span every replica shares — shorter runs no "
            "longer truncate longer ones")
        self.chk_smooth = QCheckBox("Smooth overlay")
        self.chk_smooth.setToolTip("Dashed moving-average overlay on every plotted series")
        self.spin_window = QSpinBox()
        self.spin_window.setRange(3, 2001)
        self.spin_window.setSingleStep(2)
        self.spin_window.setValue(21)
        self.spin_window.setToolTip("Moving-average window (points)")
        self.lbl_time = QLabel("")
        self.chk_smooth.toggled.connect(self.spin_window.setEnabled)
        self.chk_average.toggled.connect(self.chk_members.setEnabled)
        self.chk_average.toggled.connect(self.chk_common.setEnabled)
        self.chk_members.setEnabled(False)
        self.chk_common.setEnabled(False)
        self.spin_window.setEnabled(False)

        a = QVBoxLayout()
        a.addWidget(self.chk_average)
        a.addWidget(self.chk_members)
        a.addWidget(self.chk_common)
        row = QHBoxLayout()
        row.addWidget(self.chk_smooth)
        row.addWidget(QLabel("window"))
        row.addWidget(self.spin_window)
        row.addWidget(self.lbl_time)

        opts = QGroupBox("Analysis")
        ov = QVBoxLayout(opts)
        ov.setContentsMargins(theme.SP_M, theme.SP_M, theme.SP_M, theme.SP_M)
        ov.addLayout(a)
        ov.addLayout(row)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(theme.SP_S)
        outer.addWidget(self.scroll, 1)
        outer.addWidget(opts)
        for w in (self.chk_average, self.chk_members, self.chk_common,
                  self.chk_smooth):
            w.toggled.connect(self.options_changed)
        self.spin_window.valueChanged.connect(self.options_changed)

    # -- state ---------------------------------------------------------------

    def analysis_state(self) -> AnalysisState:
        return AnalysisState(
            average=self.chk_average.isChecked(),
            members=self.chk_members.isChecked(),
            common_range=self.chk_common.isChecked(),
            smooth=self.chk_smooth.isChecked(),
            window=self.spin_window.value(),
        )

    def set_time_hint(self, text: str) -> None:
        """Physical span of the smoothing window for the active file (C28)."""
        self.lbl_time.setText(text)

    # -- series groups ---------------------------------------------------------

    def rebuild(self, files: list[XvgFile], active_ds: dict, visible: dict,
                avg_allowed: bool, colors: dict | None = None) -> None:
        """Sync the per-file groups in place: keeps scroll position on selection changes."""
        self._updating = True
        keep = {f.path for f in files}
        for p in [p for p in self._groups if p not in keep]:
            self._remove_group(self._groups.pop(p))
        for f in files:
            g = self._groups.get(f.path)
            if g is not None and g.file is f:
                self._sync_group(g, f, active_ds, visible, colors or {})
            else:
                if g is not None:
                    self._remove_group(self._groups.pop(f.path))
                g = self._make_group(f, active_ds, visible, colors or {})
                self._groups[f.path] = g
            # (re-)insert before the trailing stretch to keep the requested order
            self._vbox.removeWidget(g.box)
            self._vbox.insertWidget(self._vbox.count() - 1, g.box)
        self._updating = False
        self.chk_average.setEnabled(avg_allowed)
        self.chk_average.setToolTip("" if avg_allowed
                                    else "select ≥ 2 files with matching column structure")

    def _remove_group(self, g: _Group) -> None:
        self._vbox.removeWidget(g.box)
        g.box.deleteLater()

    def _sync_group(self, g: _Group, f: XvgFile, active_ds: dict, visible: dict,
                    colors: dict) -> None:
        ds_i = self._dataset_index(f, active_ds)
        if g.combo is not None:
            g.combo.blockSignals(True)
            g.combo.setCurrentIndex(ds_i)
            g.combo.blockSignals(False)
        ds = f.datasets[ds_i]
        for i, cb in enumerate(g.checks):
            cb.blockSignals(True)
            cb.setChecked(visible.get((f.path, ds_i, i), True))
            cb.blockSignals(False)
        for i, sw in g.swatches.items():  # keep swatches in sync with overrides
            self._paint_swatch(sw, colors.get((f.path, ds_i, i)))

    def _make_group(self, f: XvgFile, active_ds: dict, visible: dict,
                    colors: dict) -> _Group:
        box = QGroupBox(f.path.name)
        v = QVBoxLayout(box)
        v.setContentsMargins(theme.SP_S, 2, theme.SP_S, 2)
        v.setSpacing(theme.SP_S - 1)
        combo = None
        if not f.datasets:
            v.addWidget(QLabel("no data rows"))
            return _Group(file=f, box=box, combo=combo)
        ds_i = self._dataset_index(f, active_ds)
        ds = f.datasets[ds_i]
        if len(f.datasets) > 1:
            combo = QComboBox()
            combo.addItems([f"dataset {i + 1} ({len(d.x)} pts)"
                            for i, d in enumerate(f.datasets)])
            combo.setCurrentIndex(ds_i)
            combo.currentIndexChanged.connect(lambda i, f=f: self._emit_dataset(f, i))
            v.addWidget(combo)
        checks = []
        swatches: dict[int, QToolButton] = {}
        for i, s in enumerate(ds.series):
            row = QHBoxLayout()
            label = series_label(s, f.y_label, len(ds.series))
            if s.dy_col is not None:
                label += f"  (± col {s.dy_col})"
            if s.dx_col is not None:
                label += f"  (dx col {s.dx_col})"
            cb = QCheckBox(label)
            cb.setChecked(visible.get((f.path, ds_i, i), True))
            cb.toggled.connect(lambda on, f=f, i=i: self._emit_toggled(f, i, on))
            row.addWidget(cb, 1)
            sw = QToolButton()
            sw.setFixedSize(18, 18)
            sw.setToolTip("Click to set this curve's color; right-click to reset "
                          "to the palette cycle (C17)")
            self._paint_swatch(sw, colors.get((f.path, ds_i, i)))
            sw.clicked.connect(lambda _=False, f=f, i=i, sw=sw:
                               self._pick_color(f, ds_i, i, sw))
            sw.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            sw.customContextMenuRequested.connect(
                lambda _pos, f=f, i=i, sw=sw: self._reset_color(f, ds_i, i, sw))
            row.addWidget(sw)
            v.addLayout(row)
            checks.append(cb)
            swatches[i] = sw
        return _Group(file=f, box=box, combo=combo, checks=checks, swatches=swatches)

    @staticmethod
    def _paint_swatch(btn: QToolButton, color: str | None) -> None:
        btn.setStyleSheet(f"background: {color};"
                          if color else "background: rgba(127,127,127,64);")

    def _pick_color(self, f: XvgFile, ds_i: int, i: int, sw: QToolButton) -> None:
        c = QColorDialog.getColor(parent=self, title=f"Curve color — {f.path.name}")
        if not c.isValid():
            return
        self._paint_swatch(sw, c.name())
        self.series_color_changed.emit(f, ds_i, i, c.name())

    def _reset_color(self, f: XvgFile, ds_i: int, i: int, sw: QToolButton) -> None:
        m = QMenu(self)
        act = m.addAction("Reset to palette cycle")
        if m.exec(QCursor.pos()) != act:
            return
        self._paint_swatch(sw, None)
        self.series_color_changed.emit(f, ds_i, i, None)

    @staticmethod
    def _dataset_index(f: XvgFile, active_ds: dict) -> int:
        return min(active_ds.get(f.path, 0), len(f.datasets) - 1)

    def _emit_toggled(self, f: XvgFile, i: int, on: bool) -> None:
        if not self._updating:
            self.series_toggled.emit(f, i, on)

    def _emit_dataset(self, f: XvgFile, i: int) -> None:
        if not self._updating:
            self.dataset_changed.emit(f, i)
