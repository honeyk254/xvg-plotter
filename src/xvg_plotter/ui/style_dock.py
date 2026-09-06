"""Style dock: grid, log axes, legend, palette, line style, overrides, unit (SPEC §6.1)."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .options import LEGEND_LOCS, LINE_STYLES, PALETTES


@dataclass
class StyleState:
    logx: bool = False
    logy: bool = False
    grid: bool = True
    legend: str = "best"
    palette: str = "Default"
    line: str = "Solid"
    width: float = 1.5
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    unit: str = "auto"


class StyleDock(QWidget):
    style_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chk_grid = QCheckBox()
        self.chk_grid.setChecked(True)
        self.chk_logx = QCheckBox()
        self.chk_logy = QCheckBox()
        self.cmb_legend = QComboBox()
        self.cmb_legend.addItems(LEGEND_LOCS)
        self.cmb_palette = QComboBox()
        self.cmb_palette.addItems(list(PALETTES))
        self.cmb_line = QComboBox()
        self.cmb_line.addItems(list(LINE_STYLES))
        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(0.5, 6.0)
        self.spin_width.setSingleStep(0.5)
        self.spin_width.setValue(1.5)
        self.ed_title = QLineEdit()
        self.ed_title.setPlaceholderText("auto from file")
        self.ed_xlabel = QLineEdit()
        self.ed_xlabel.setPlaceholderText("auto from file")
        self.ed_ylabel = QLineEdit()
        self.ed_ylabel.setPlaceholderText("auto from file")
        self.cmb_unit = QComboBox()
        self.cmb_unit.addItems(["auto", "ps", "ns", "µs", "ms"])

        form = QFormLayout()
        form.setContentsMargins(theme.SP_M, theme.SP_M, theme.SP_M, theme.SP_M)
        form.setSpacing(theme.SP_S + 1)
        form.addRow("Grid", self.chk_grid)
        form.addRow("Log X", self.chk_logx)
        form.addRow("Log Y", self.chk_logy)
        form.addRow("Legend", self.cmb_legend)
        form.addRow("Colors", self.cmb_palette)
        form.addRow("Line", self.cmb_line)
        form.addRow("Width", self.spin_width)
        form.addRow("Title", self.ed_title)
        form.addRow("X label", self.ed_xlabel)
        form.addRow("Y label", self.ed_ylabel)
        form.addRow("X unit", self.cmb_unit)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(form)
        outer.addStretch(1)

        for w in (self.chk_grid, self.chk_logx, self.chk_logy):
            w.toggled.connect(self.style_changed)
        for c in (self.cmb_legend, self.cmb_palette, self.cmb_line, self.cmb_unit):
            c.currentTextChanged.connect(lambda *_: self.style_changed.emit())
        self.spin_width.valueChanged.connect(self.style_changed)
        for e in (self.ed_title, self.ed_xlabel, self.ed_ylabel):
            e.textChanged.connect(self.style_changed)

    def state(self) -> StyleState:
        return StyleState(
            logx=self.chk_logx.isChecked(),
            logy=self.chk_logy.isChecked(),
            grid=self.chk_grid.isChecked(),
            legend=self.cmb_legend.currentText(),
            palette=self.cmb_palette.currentText(),
            line=self.cmb_line.currentText(),
            width=self.spin_width.value(),
            title=self.ed_title.text().strip(),
            xlabel=self.ed_xlabel.text().strip(),
            ylabel=self.ed_ylabel.text().strip(),
            unit=self.cmb_unit.currentText(),
        )
