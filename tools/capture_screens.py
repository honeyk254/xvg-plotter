"""Capture themed screenshots of every major surface (docs + visual review).

Renders the real widgets on the offscreen Qt platform with a sandboxed
QSettings file, so the developer's app settings are never touched.  Writes
one PNG per surface per theme into --out (default ``build/screens``) and
refreshes the three README shots in ``docs/`` when --docs is passed.

    python tools/capture_screens.py [--out build/screens] [--docs]
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # headless render

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PySide6.QtCore import QSize, QSettings, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QDockWidget  # noqa: E402

THEMES = ("light", "dark")


def _sandbox_settings(tmp: Path) -> None:
    """Point xvg_plotter.settings at a throwaway ini before any widget runs."""
    from xvg_plotter import settings
    settings._s = QSettings(str(tmp / "capture-settings.ini"),
                            QSettings.Format.IniFormat)


def _populate(win) -> None:
    """Load fixture files, check them for overlay, open the style tab."""
    from xvg_plotter.core.parser import parse_file
    fixtures = ROOT / "tests" / "fixtures"
    for name in ("energy.xvg", "errorbar.xvg", "multidataset.xvg"):
        win._on_file(parse_file(fixtures / name))
    for f in list(win.files.values()):
        win._tables[0].sync_check(f.path, True)
    win.active = next(iter(win.files))
    win._refresh_series_dock()
    win.update_plot()
    for pane, table in enumerate(win._tables):  # real column widths + folder text
        win._bars[pane].set_path(str(fixtures), [str(fixtures)])
        table.finish_scan()
    win._style_tab.setChecked(True)
    # showcase features in the docs shots: least-squares fit + a text annotation
    win.series.chk_fit.setChecked(True)
    win._annotations.append((1.2, 125.0, "replica A"))
    win.update_plot()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "build" / "screens"))
    ap.add_argument("--docs", action="store_true",
                    help="also refresh docs/screenshot-{light,dark,grid}.png")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    app = QApplication(["XVG Plotter"])
    app.setApplicationName("XVG Plotter")
    app.setStyle("Fusion")
    _sandbox_settings(Path(tempfile.mkdtemp(prefix="xvg-capture-")))

    from xvg_plotter import settings
    from xvg_plotter.ui import theme
    from xvg_plotter.ui.export_dialog import ExportDialog
    from xvg_plotter.ui.first_run import FirstRunDialog
    from xvg_plotter.ui.help_dialogs import GlossaryDialog, KeyboardDialog
    from xvg_plotter.ui.main_window import MainWindow
    from xvg_plotter.version import APP_VERSION

    theme.apply(app, theme.LIGHT)
    win = MainWindow(primary=False)
    _populate(win)
    win.resize(QSize(1440, 920))
    files_dock = win.findChild(QDockWidget, "files")
    series_dock = win.findChild(QDockWidget, "series")
    win.resizeDocks([files_dock, series_dock], [340, 340], Qt.Orientation.Horizontal)
    win.resizeDocks([files_dock, series_dock], [420, 400], Qt.Orientation.Vertical)
    win.show()
    app.processEvents()

    for mode in THEMES:
        settings.set_theme_mode(mode)
        win.retheme()
        app.processEvents()

        def grab(widget, name, _pre=mode):
            app.processEvents()
            widget.grab().save(str(out / f"{_pre}-{name}.png"))

        grab(win, "main")

        win._grid_action.setChecked(True)
        grab(win, "grid")
        win._grid_action.setChecked(False)

        grab(win.series, "series")
        grab(win.style, "style")
        grab(win.findChild(QDockWidget, "files"), "files")

        dlg = ExportDialog("rmsd_1ns.png", str(ROOT / "tests" / "fixtures"),
                           parent=win)
        dlg.show()
        grab(dlg, "export")
        dlg.close()

        for cls, name in ((FirstRunDialog, "firstrun"),
                          (KeyboardDialog, "keyboard"),
                          (GlossaryDialog, "glossary")):
            d = cls(win)
            d.show()
            grab(d, name)
            d.close()

    win.close()
    written = sorted(p.name for p in out.glob("*.png"))
    print(f"XVG Plotter {APP_VERSION} — {len(written)} screenshots in {out}:")
    for n in written:
        print(" ", n)

    if args.docs:
        docs = ROOT / "docs"
        (out / "light-main.png").replace(docs / "screenshot-light.png")
        (out / "dark-main.png").replace(docs / "screenshot-dark.png")
        (out / "light-grid.png").replace(docs / "screenshot-grid.png")
        print("docs/ screenshots refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
