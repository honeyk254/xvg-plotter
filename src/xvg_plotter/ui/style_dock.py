"""Style dock: grid, log axes, legend, palette, line style, overrides, unit (SPEC §6.1)."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from .. import settings
from . import theme
from .options import LEGEND_LOCS, LINE_STYLES, PALETTES

FONTS = ["Match UI", "DejaVu Sans", "Arial", "Helvetica", "Times New Roman",
         "Microsoft YaHei", "SimSun", "Noto Sans CJK SC"]


@dataclass
class StyleState:
    logx: bool = False
    logy: bool = False
    grid: bool = True
    legend: str = "best"
    palette: str = "Okabe–Ito (colorblind-safe)"
    line: str = "Solid"
    width: float = 1.5
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    unit: str = "auto"
    fig_w: float = 0.0  # 0 = auto size (C16)
    fig_h: float = 0.0
    font: str = "Match UI"


class StyleDock(QWidget):
    style_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chk_grid = QCheckBox()
        self.chk_grid.setChecked(True)
        self.chk_grid.setToolTip("Draw a light grid on the plot")
        self.chk_logx = QCheckBox()
        self.chk_logx.setToolTip("Logarithmic X axis")
        self.chk_logy = QCheckBox()
        self.chk_logy.setToolTip("Logarithmic Y axis")
        self.cmb_legend = QComboBox()
        self.cmb_legend.addItems(LEGEND_LOCS)
        self.cmb_legend.setToolTip("Legend position — 'outside right' keeps it off the data (C17)")
        self.cmb_palette = QComboBox()
        self.cmb_palette.addItems(list(PALETTES))
        self.cmb_palette.setToolTip("Color cycle for overlaid series; Okabe–Ito is colorblind-safe (C17)")
        self.cmb_line = QComboBox()
        self.cmb_line.addItems(list(LINE_STYLES))
        self.cmb_line.setToolTip("Line / marker style for every plotted series")
        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(0.5, 6.0)
        self.spin_width.setSingleStep(0.5)
        self.spin_width.setValue(1.5)
        self.spin_width.setToolTip("Line width")
        self.ed_title = QLineEdit()
        self.ed_title.setPlaceholderText("auto from file")
        self.ed_xlabel = QLineEdit()
        self.ed_xlabel.setPlaceholderText("auto from file")
        self.ed_ylabel = QLineEdit()
        self.ed_ylabel.setPlaceholderText("auto from file")
        self.cmb_unit = QComboBox()
        self.cmb_unit.addItems(["auto", "ps", "ns", "µs", "ms"])
        self.cmb_unit.setToolTip("Rescale the time axis (auto picks the largest unit; "
                                 "only applied to genuine time axes)")
        # C16: fixed figure geometry + font family for publication figures
        self.spin_figw = QDoubleSpinBox()
        self.spin_figw.setRange(0.0, 30.0)
        self.spin_figw.setSingleStep(0.5)
        self.spin_figw.setDecimals(1)
        self.spin_figw.setSpecialValueText("auto")
        self.spin_figw.setValue(float(settings.get("view/fig_w", 0.0) or 0.0))
        self.spin_figw.setToolTip("Figure width in inches (auto = fill the window)")
        self.spin_figh = QDoubleSpinBox()
        self.spin_figh.setRange(0.0, 30.0)
        self.spin_figh.setSingleStep(0.5)
        self.spin_figh.setDecimals(1)
        self.spin_figh.setSpecialValueText("auto")
        self.spin_figh.setValue(float(settings.get("view/fig_h", 0.0) or 0.0))
        self.spin_figh.setToolTip("Figure height in inches (auto = fill the window)")
        self.cmb_font = QComboBox()
        self.cmb_font.addItems(FONTS)
        self.cmb_font.setCurrentText(str(settings.get("view/font", "Match UI")))
        self.cmb_font.setToolTip("Font family for titles, labels and ticks")

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
        sizrow = QHBoxLayout()
        sizrow.addWidget(self.spin_figw)
        sizrow.addWidget(self.spin_figh)
        form.addRow("Fig size (in)", sizrow)
        form.addRow("Font", self.cmb_font)
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
        for c in (self.cmb_legend, self.cmb_palette, self.cmb_line, self.cmb_unit,
                  self.cmb_font):
            c.currentTextChanged.connect(lambda *_: self.style_changed.emit())
        for s in (self.spin_width, self.spin_figw, self.spin_figh):
            s.valueChanged.connect(self.style_changed)
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
            fig_w=self.spin_figw.value(),
            fig_h=self.spin_figh.value(),
            font=self.cmb_font.currentText(),
        )
