"""Export dialog (SPEC §8)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from . import theme

FORMATS = ("png", "pdf", "svg", "eps", "tif")
RASTER_FORMATS = ("png", "tif")


class ExportDialog(QDialog):
    def __init__(self, default_name: str, default_dir: str, dpi: int = 300,
                 fmt: str = "png", transparent: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Export plot"))
        self.setMinimumWidth(380)
        self.ed_name = QLineEdit(default_name)
        self.ed_dir = QLineEdit(default_dir)
        self.btn_dir = QPushButton("…")
        self.btn_dir.setToolTip(self.tr("Browse for folder"))
        self.cmb_fmt = QComboBox()
        self.cmb_fmt.addItems(FORMATS)
        self.cmb_fmt.setCurrentText(fmt)
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(100, 600)
        self.spin_dpi.setValue(dpi)
        self.chk_transparent = QCheckBox(self.tr("transparent background"))
        self.chk_transparent.setChecked(transparent)
        self.spin_dpi.setEnabled(fmt in RASTER_FORMATS)

        form = QFormLayout()
        form.setContentsMargins(theme.SP_L, theme.SP_L, theme.SP_L, theme.SP_L)
        form.setSpacing(theme.SP_S + 1)
        form.addRow(self.tr("Filename"), self.ed_name)
        dirrow = QHBoxLayout()
        dirrow.setSpacing(theme.SP_S)
        dirrow.addWidget(self.ed_dir, 1)
        dirrow.addWidget(self.btn_dir)
        form.addRow(self.tr("Folder"), dirrow)
        form.addRow(self.tr("Format"), self.cmb_fmt)
        form.addRow(self.tr("DPI (raster: PNG/TIFF)"), self.spin_dpi)
        form.addRow("", self.chk_transparent)

        self.bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        bb_row = QHBoxLayout()
        bb_row.setContentsMargins(theme.SP_L, 0, theme.SP_L, theme.SP_L)
        bb_row.addWidget(self.bb)
        lay.addLayout(bb_row)

        self.btn_dir.clicked.connect(self._browse)
        self.cmb_fmt.currentTextChanged.connect(self._fmt_changed)
        self.ed_name.textChanged.connect(self._validate)
        self.ed_dir.textChanged.connect(self._validate)
        self._fmt_changed(self.cmb_fmt.currentText())  # initial EPS/TIFF state
        self._validate()

    def _fmt_changed(self, t: str) -> None:
        self.spin_dpi.setEnabled(t in RASTER_FORMATS)
        eps = t == "eps"  # EPS cannot carry a transparent background
        self.chk_transparent.setEnabled(not eps)
        self.chk_transparent.setToolTip(
            self.tr("EPS does not support a transparent background") if eps else "")

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, self.tr("Export to folder"),
                                             self.ed_dir.text())
        if d:
            self.ed_dir.setText(d)

    def _validate(self) -> None:
        ok = bool(self.ed_name.text().strip()) and Path(self.ed_dir.text().strip()).is_dir()
        self.bb.button(QDialogButtonBox.StandardButton.Ok).setEnabled(ok)

    def options(self) -> dict:
        d = Path(self.ed_dir.text().strip())
        name = self.ed_name.text().strip()
        fmt = self.cmb_fmt.currentText()
        if not name.lower().endswith("." + fmt):
            name += "." + fmt
        return {"path": d / name, "dpi": self.spin_dpi.value(),
                "transparent": self.chk_transparent.isChecked() and fmt != "eps",
                "fmt": fmt}
