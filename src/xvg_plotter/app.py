"""Application bootstrap: logging, QApplication, icon, single instance, argv routing (SPEC §11, §10)."""
from __future__ import annotations

import logging
import logging.handlers
import sys
import time
import traceback
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QStyleFactory

from . import settings
from .single_instance import SingleInstance
from .version import APP_VERSION

ASSETS = Path(__file__).parent / "assets"
START_T0: float | None = None  # set by packaging/entry.py for cold-start timing

log = logging.getLogger("xvg_plotter")

_QT_LEVELS = {
    QtMsgType.QtDebugMsg: logging.DEBUG,
    QtMsgType.QtInfoMsg: logging.INFO,
    QtMsgType.QtWarningMsg: logging.WARNING,
    QtMsgType.QtCriticalMsg: logging.ERROR,
    QtMsgType.QtFatalMsg: logging.CRITICAL,
}


def log_path() -> Path | None:
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation)
    return Path(base) / "xvg_plotter.log" if base else None


def setup_logging() -> Path | None:
    """Rotating file log + crash dialog for the --noconsole builds (C39)."""
    p = log_path()
    if p is None:
        return None
    root = logging.getLogger()
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root.handlers):
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            h = logging.handlers.RotatingFileHandler(
                p, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
            h.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s"))
            root.setLevel(logging.INFO)
            root.addHandler(h)
        except OSError:
            return None

    def hook(t, v, tb):
        log.critical("uncaught exception", exc_info=(t, v, tb))
        if QApplication.instance() is not None:
            try:
                box = QMessageBox(
                    QMessageBox.Icon.Critical, "XVG Plotter — unexpected error",
                    f"An unexpected error occurred:\n{v}\n\n"
                    f"A full trace was written to the log:\n{p}")
                box.setDetailedText("".join(traceback.format_exception(t, v, tb)))
                box.exec()
            except Exception:
                pass

    sys.excepthook = hook
    qInstallMessageHandler(_qt_message_handler)
    log.info("XVG Plotter %s starting (argv=%s)", APP_VERSION, sys.argv[1:])
    return p


def _qt_message_handler(mode, _ctx, message: str) -> None:
    logging.getLogger("qt").log(_QT_LEVELS.get(mode, logging.WARNING), message)


def main(argv=None) -> int:
    t0 = START_T0 if START_T0 is not None else time.perf_counter()
    argv = list(sys.argv[1:] if argv is None else argv)
    app = QApplication(["XVG Plotter"])
    app.setApplicationName("XVG Plotter")
    app.setOrganizationName("XVGPlotter")
    setup_logging()  # after the app name, so AppDataLocation resolves per-app
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
    log.info("startup: window shown in %.2fs (C03 guardrail: < 3 s warm)",
             time.perf_counter() - t0)

    if argv:
        win.open_path(argv[0])
    else:
        last = settings.get("last_folder")
        if last and Path(str(last)).is_dir():
            win.load_folder(str(last))
        last2 = settings.get("last_folder2")
        if last2 and Path(str(last2)).is_dir():
            win.load_folder(str(last2), 1)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
