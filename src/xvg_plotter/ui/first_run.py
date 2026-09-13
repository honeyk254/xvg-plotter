"""One-screen first-run introduction (C37). Shown once, remembered via settings."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
)

_INTRO = (
    "<h3>Welcome to XVG Plotter</h3>"
    "<p>The fast way from GROMACS <code>.xvg</code> files to publication figures:</p>"
    "<ul>"
    "<li><b>Open a folder</b> — every analysis file is listed with title, series and "
    "points; tick <b>subfolders</b> for nested trees.</li>"
    "<li><b>Click a file</b> to plot it; <b>tick several</b> to overlay them. The two "
    "file panes can hold <b>two different folders</b> for comparisons.</li>"
    "<li><b>Right-click a legend entry</b> to <b>pin</b> a curve — it survives file "
    "and folder switches.</li>"
    "<li><b>Average replicas</b> in the Series panel, rescale time in the Style "
    "options, then <b>Export</b> (PNG/TIFF/PDF/SVG/EPS), <b>print</b>, or <b>copy</b> "
    "straight into slides.</li>"
    "</ul>"
    "<p>Help ▸ <i>Reading the analyses</i> explains the jargon; Help ▸ <i>Keyboard "
    "shortcuts</i> lists every shortcut. Drag files or folders onto the window "
    "anytime.</p>"
)


class FirstRunDialog(QDialog):
    """Shown once on first launch; the caller records 'ui/onboarded'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Welcome to XVG Plotter"))
        self.resize(560, 380)
        lay = QVBoxLayout(self)
        head = QLabel(self)
        head.setTextFormat(Qt.TextFormat.RichText)
        head.setText(f"<b>{self.tr('Double-click an .xvg, get a proper plot.')}</b>")
        body = QTextBrowser(self)
        body.setOpenExternalLinks(False)
        body.setHtml(self.tr(_INTRO))
        lay.addWidget(head)
        lay.addWidget(body, 1)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("Got it"))
        bb.accepted.connect(self.accept)
        lay.addWidget(bb)
