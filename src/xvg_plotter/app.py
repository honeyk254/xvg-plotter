"""Application bootstrap: QApplication, icon, single instance, argv routing (SPEC §11, §10)."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyleFactory

from . import settings
from .single_instance import SingleInstance

ASSETS = Path(__file__).parent / "assets"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    app = QApplication(["XVG Plotter"])
    app.setApplicationName("XVG Plotter")
    app.setOrganizationName("XVGPlotter")
    # Fusion renders our stylesheet identically on every platform
    app.setStyle(QStyleFactory.create("Fusion"))
    from .ui import theme
    theme.apply(app)
    icon = ASSETS / ("icon.ico" if sys.platform == "win32" else "icon.png")
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))

    inst = SingleInstance()
    if not inst.is_primary and inst.send(argv):
        return 0  # handed off to the running instance
    # either primary, or the port is owned by a foreign service: launch standalone

    from .ui.main_window import MainWindow  # after backend selection
    win = MainWindow()
    inst.message.connect(lambda paths: [win.open_path(p) for p in paths])
    win.show()

    if argv:
        win.open_path(argv[0])
    else:
        last = settings.get("last_folder")
        if last and Path(str(last)).is_dir():
            win.load_folder(str(last))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
