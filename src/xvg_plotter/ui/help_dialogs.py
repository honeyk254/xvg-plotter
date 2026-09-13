"""Help dialogs: keyboard reference and analysis glossary (C19 / C37)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
)

# (shortcut, action) — keep in sync with the actions in main_window._menus()
KEYBOARD_ROWS = [
    ("Ctrl+O", "Open folder (pane 1)"),
    ("Ctrl+Shift+O", "Open the current folder in a new window"),
    ("F5 / Ctrl+R", "Refresh scan (Ctrl+R refreshes both panes)"),
    ("Ctrl+F", "Jump to the folder filter (Esc clears it)"),
    ("Ctrl+1 / Ctrl+2", "Show or hide the Files / Series panels"),
    ("Ctrl+3", "Show or hide the Style options"),
    ("F11", "Focus mode — hide everything except the plot"),
    ("Ctrl+G", "Grid view — one subplot per checked file (small multiples)"),
    ("Ctrl+E", "Export the current plot…"),
    ("Ctrl+Shift+E", "Export every checked file as its own plot…"),
    ("Ctrl+D", "Export the plotted data as CSV…"),
    ("Ctrl+P", "Print the current plot…"),
    ("Ctrl+Shift+C", "Copy the plot image to the clipboard"),
    ("Ctrl+Q", "Quit"),
]

# (term, plain-language explanation) — the jargon a first-year student meets first
GLOSSARY = [
    ("RMSD", "Root-mean-square deviation: how far the protein structure has moved "
             "from a reference, in nanometres. A flattening curve means the "
             "simulation is stable."),
    ("Rg (gyrate)", "Radius of gyration: how compact the molecule is, in nanometres. "
                    "Written by gmx gyrate."),
    ("RDF", "Radial distribution function: how likely two atoms are to be a certain "
            "distance apart. Often has error bars (a ± column)."),
    ("energy.xvg", "gmx energy output — several series in one file (Potential, "
                   "Kinetic, Total, …). Toggle series in the Series panel."),
    ("xydy / xydx", "Grace column types: 'xydy' means the third column is the ± "
                    "error of Y; 'xydx' the same for X. The app draws error bars "
                    "automatically."),
    ("replica", "An independent repeat of the same simulation. Select ≥ 2 matching "
                "files and tick 'Average replicas' for a mean ± SD band."),
    ("ps / ns", "Picosecond / nanosecond time units. Use the X unit selector to "
                "rescale the axis (only real time axes are converted)."),
    ("moving average", "A smoothed overlay that averages a sliding window of points; "
                       "the label shows the window in physical time."),
    ("pin", "Right-click a legend entry to pin a curve — it stays plotted while you "
            "switch files or folders, so you can compare anything with anything."),
    ("normalize / baseline / fit", "Analysis-panel helpers. 'Normalize' divides "
                                   "each curve by its first value or maximum; 'Subtract "
                                   "baseline' shifts curves to start at zero; 'Fit line' "
                                   "draws a dashed least-squares y = a·x + b over the "
                                   "visible range. Display-only — your files are "
                                   "never changed."),
    ("annotation", "Click ✎ Text on the plot toolbar, then click the canvas to place a "
                   "text label at that data point. Drag labels to move them; they are "
                   "kept in exports and prints. View ▸ Clear annotations removes all."),
    ("grid view", "View ▸ Grid view of checked files (Ctrl+G) draws each checked file "
                  "in its own small subplot — up to 24 — instead of overlaying them."),
    ("dataset", "A '&' in an .xvg file starts a new dataset. Multi-dataset files list "
                "every dataset's series in the Series panel; tick any of them, also "
                "across files, to overlay."),
]

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
    "shortcuts</i> lists every shortcut.</p>"
)


class _InfoDialog(QDialog):
    def __init__(self, title: str, parent=None, width: int = 520, height: int = 420):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(width, height)
        lay = QVBoxLayout(self)
        self._body = None  # set by subclasses before adding buttons
        self._lay = lay

    def _finish(self) -> None:
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject)
        bb.clicked.connect(lambda *_: self.accept())
        self._lay.addWidget(self._body, 1)
        self._lay.addWidget(bb)


class KeyboardDialog(_InfoDialog):
    """Every shortcut, one row each (C19)."""

    def __init__(self, parent=None):
        super().__init__(self.tr("Keyboard shortcuts"), parent)
        table = QTableWidget(len(KEYBOARD_ROWS), 2, self)
        table.setHorizontalHeaderLabels([self.tr("Shortcut"), self.tr("Action")])
        for r, (seq, action) in enumerate(KEYBOARD_ROWS):
            seq_item = QTableWidgetItem(seq)
            seq_item.setFont(self.font())
            table.setItem(r, 0, seq_item)
            table.setItem(r, 1, QTableWidgetItem(self.tr(action)))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setCornerButtonEnabled(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnToContents(0)
        table.setFocus()
        self._body = table
        self._finish()


class GlossaryDialog(_InfoDialog):
    """Plain-language explanation of the jargon in the file names (C37)."""

    def __init__(self, parent=None):
        super().__init__(self.tr("Reading the analyses"), parent)
        body = QTextBrowser(self)
        body.setOpenExternalLinks(False)
        parts = [f"<dt><b>{self.tr(term)}</b></dt><dd>{self.tr(text)}</dd>"
                 for term, text in GLOSSARY]
        body.setHtml(f"<h3>{self.tr('The jargon, in plain language')}</h3><dl>"
                     + "".join(parts) + "</dl>")
        self._body = body
        self._finish()
