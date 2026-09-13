"""Main window: menus, docks, wiring, plot state composition (SPEC §6)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QCursor,
    QDesktopServices,
    QGuiApplication,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import fileassoc, settings, updates
from ..core import analysis
from ..core.models import XvgFile, series_label
from ..core.parser import parse_file
from ..export import copy_image, print_figure, save_figure, write_csv
from ..version import APP_VERSION
from . import theme
from .export_dialog import ExportDialog
from .file_table import FileTable, FolderScanner
from .folder_bar import FolderBar
from .help_dialogs import GlossaryDialog, KeyboardDialog
from .options import LINE_STYLES, PALETTES
from .plot_canvas import Band, Line, PlotPanel, PlotState
from .series_dock import SeriesDock
from .style_dock import StyleDock

DEFAULT_SIZE = (1150, 720)
MIN_SIZE = (900, 560)

_WINDOWS: list["MainWindow"] = []  # keep secondary windows alive (C22)


class _ColorCycle:
    """Sequential color allocator over a palette (or matplotlib's default cycle)."""

    def __init__(self, palette: list[str] | None):
        self._palette = palette
        self._i = 0

    def next(self) -> str:
        if self._palette:
            c = self._palette[self._i % len(self._palette)]
        else:
            c = f"C{self._i % 10}"
        self._i += 1
        return c


@dataclass
class PinnedCurve:
    """Snapshot of a plotted Line so a pin survives folder switches.

    `path`/`ds_idx`/`series_idx` let a folder refresh re-read the latest
    data; averaged/derived curves have path=None and keep their snapshot.
    """

    label: str
    path: Path | None
    ds_idx: int
    series_idx: int
    x: object
    y: object
    dy: object
    dx: object


class MainWindow(QMainWindow):
    def __init__(self, primary: bool = True):
        super().__init__()
        self._primary_window = primary  # C22: only the first window persists state
        self.setWindowTitle("XVG Plotter")
        self.files: dict[Path, XvgFile] = {}
        self.active: Path | None = None
        self.active_ds: dict[Path, int] = {}
        self.visible: dict[tuple[Path, int, int], bool] = {}
        self._scanners: list[FolderScanner | None] = [None, None]
        self._folders: list[Path | None] = [None, None]
        self._last_pane = 0
        self._colors: dict[tuple[Path, int, int], str] = {}  # C17 overrides
        self.pins: dict[str, PinnedCurve] = {}
        self._entries: list = []
        self._pending: list[Path] = []
        self._avg_warning: str | None = None

        self.folder_bar = FolderBar(settings.recent_items())
        self.table = FileTable()
        self.folder_bar2 = FolderBar(settings.recent_items())
        self.folder_bar2.combo.lineEdit().setPlaceholderText(
            "open a second folder to compare…")
        self.table2 = FileTable()
        self._bars = (self.folder_bar, self.folder_bar2)
        self._tables = (self.table, self.table2)
        self.series = SeriesDock()
        self.style = StyleDock()
        self.panel = PlotPanel()
        self.setAcceptDrops(True)  # C13

        split = QSplitter(Qt.Orientation.Vertical)
        for bar, table in zip(self._bars, self._tables):
            pane = QWidget()
            v = QVBoxLayout(pane)
            v.setContentsMargins(theme.SP_S, theme.SP_S, theme.SP_S, 0)
            v.setSpacing(theme.SP_S)
            v.addWidget(bar)
            v.addWidget(table)
            split.addWidget(pane)
        split.setSizes([420, 260])

        dock_files = QDockWidget("Files", self)
        dock_files.setObjectName("files")
        dock_files.setWidget(split)
        dock_series = QDockWidget("Series && analysis", self)
        dock_series.setObjectName("series")
        dock_series.setWidget(self.series)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_files)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_series)
        self.splitDockWidget(dock_files, dock_series, Qt.Orientation.Vertical)

        # Style lives in a collapsible tab above the plot, not a permanent dock
        self._style_tab = QToolButton()
        self._style_tab.setText("Style ▸")
        self._style_tab.setCheckable(True)
        self._style_tab.setToolTip("Show plot style options")
        self.style.setVisible(False)
        self._style_tab.toggled.connect(self._toggle_style_tab)
        central = QWidget()
        cv = QVBoxLayout(central)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        cv.addWidget(self._style_tab, 0, Qt.AlignmentFlag.AlignRight)
        cv.addWidget(self.style)
        cv.addWidget(self.panel, 1)
        self.setCentralWidget(central)
        self._docks = (dock_files, dock_series)
        self.resizeDocks([dock_files], [300], Qt.Orientation.Horizontal)
        self.resizeDocks([dock_files, dock_series], [350, 280], Qt.Orientation.Vertical)
        self.resize(*DEFAULT_SIZE)
        self.setMinimumSize(*MIN_SIZE)

        self._menus()

        for pane in range(2):
            bar, table = self._bars[pane], self._tables[pane]
            bar.folder_requested.connect(
                lambda path, pn=pane: self.load_folder(path, pn))
            bar.refresh_requested.connect(
                lambda _=False, pn=pane: self.load_folder(
                    self._bars[pn].current_folder(), pn))
            bar.filter_changed.connect(table.apply_filter)
            bar.pin_toggled.connect(lambda on, pn=pane: self._on_pin_toggled(on, pn))
            bar.recursive_toggled.connect(lambda on, pn=pane: self._on_recursive(on, pn))
            table.overlay_toggled.connect(self._on_overlay)
            table.file_activated.connect(self._on_activate)
        self.series.series_toggled.connect(self._on_series_toggled)
        self.series.dataset_changed.connect(self._on_dataset_changed)
        self.series.options_changed.connect(self.update_plot)
        self.series.series_color_changed.connect(self._on_series_color)
        self.style.style_changed.connect(self.update_plot)
        self.panel.save_requested.connect(self.export_dialog)
        self.panel.coords.connect(lambda s: self.statusBar().showMessage(s))
        self.panel.pin_requested.connect(self._on_pin_requested)

        self._info = QLabel("no folder loaded")
        self.statusBar().addWidget(self._info, 1)

        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self._on_system_scheme_changed)

        for key, restore in (("geometry", self.restoreGeometry),
                             ("window_state", self.restoreState)):
            val = None if primary else settings.get(key)
            if val is not None:
                try:
                    restore(val)
                except Exception:
                    pass

    # -- menus ---------------------------------------------------------------

    def _menus(self) -> None:
        mb = self.menuBar()
        m_file = mb.addMenu("&File")
        a = QAction("Open Folder…", self)
        a.setShortcut(QKeySequence("Ctrl+O"))
        a.triggered.connect(self.folder_bar.pick_folder)
        m_file.addAction(a)
        a = QAction("Open Folder in New Window…", self)  # C22: two-monitor setups
        a.setShortcut(QKeySequence("Ctrl+Shift+O"))
        a.triggered.connect(self._new_window)
        m_file.addAction(a)
        a = QAction("Refresh", self)
        a.setShortcut(QKeySequence("F5"))
        a.triggered.connect(lambda: self.load_folder(self.folder_bar.current_folder()))
        m_file.addAction(a)
        m_file.addSeparator()
        a = QAction("Export…", self)
        a.setShortcut(QKeySequence("Ctrl+E"))
        a.triggered.connect(self.export_dialog)
        m_file.addAction(a)
        a = QAction("Export all checked files…", self)  # C29: no more dialog loops
        a.setShortcut(QKeySequence("Ctrl+Shift+E"))
        a.triggered.connect(self._export_batch)
        m_file.addAction(a)
        a = QAction("Export data (CSV)…", self)  # C30
        a.setShortcut(QKeySequence("Ctrl+D"))
        a.triggered.connect(self._export_data)
        m_file.addAction(a)
        a = QAction("Print…", self)  # C33
        a.setShortcut(QKeySequence("Ctrl+P"))
        a.triggered.connect(self._print_plot)
        m_file.addAction(a)
        a = QAction("Copy Image", self)
        a.setShortcut(QKeySequence("Ctrl+Shift+C"))
        a.triggered.connect(self._copy_image)
        m_file.addAction(a)
        m_file.addSeparator()
        a = QAction("Export Settings…", self)
        a.triggered.connect(self._export_settings)
        m_file.addAction(a)
        a = QAction("Import Settings…", self)
        a.triggered.connect(self._import_settings)
        m_file.addAction(a)
        m_file.addSeparator()
        a = QAction("Quit", self)
        a.setShortcut(QKeySequence("Ctrl+Q"))
        a.triggered.connect(self.close)
        m_file.addAction(a)

        m_view = mb.addMenu("&View")
        m_theme = m_view.addMenu("&Theme")
        group = QActionGroup(self)
        for mode, label in ((settings.THEME_AUTO, "&Auto (system)"),
                            (settings.THEME_LIGHT, "&Light"),
                            (settings.THEME_DARK, "&Dark")):
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(settings.theme_mode() == mode)
            act.triggered.connect(lambda _=False, m=mode: self._set_theme_mode(m))
            group.addAction(act)
            m_theme.addAction(act)
        m_view.addSeparator()
        for d in self._docks:
            m_view.addAction(d.toggleViewAction())
        a = QAction("Clear all pins", self)
        a.triggered.connect(self._clear_pins)
        m_view.addAction(a)
        m_view.addSeparator()
        self._focus_action = QAction("Focus mode", self)  # C20: plot only
        self._focus_action.setCheckable(True)
        self._focus_action.setShortcut(QKeySequence("F11"))
        self._focus_action.toggled.connect(self._toggle_focus)
        m_view.addAction(self._focus_action)

        m_help = mb.addMenu("&Help")
        a = QAction("Keyboard shortcuts…", self)  # C19
        a.triggered.connect(lambda: KeyboardDialog(self).exec())
        m_help.addAction(a)
        a = QAction("Reading the analyses…", self)  # C37
        a.triggered.connect(lambda: GlossaryDialog(self).exec())
        m_help.addAction(a)
        a = QAction("Check for updates…", self)
        a.triggered.connect(self._check_updates)
        m_help.addAction(a)
        if sys.platform == "win32":  # C06: mirrors the installer's optional association
            m_help.addSeparator()
            a = QAction("Set as default .xvg viewer", self)
            a.triggered.connect(self._set_default_viewer)
            m_help.addAction(a)
        m_help.addSeparator()
        a = QAction("About", self)
        a.triggered.connect(self._about)
        m_help.addAction(a)

        # C19: hidden shortcuts — filter focus, panel toggles, refresh both panes
        for seq, slot in (("Ctrl+F", self._focus_filter),
                          ("Ctrl+1", lambda: self._docks[0].setVisible(
                              not self._docks[0].isVisible())),
                          ("Ctrl+2", lambda: self._docks[1].setVisible(
                              not self._docks[1].isVisible())),
                          ("Ctrl+3", lambda: self._style_tab.toggle()),
                          ("Ctrl+R", self._refresh_all)):
            a = QAction(self)
            a.setShortcut(QKeySequence(seq))
            a.triggered.connect(slot)
            self.addAction(a)

    def _about(self) -> None:
        import matplotlib
        import numpy
        import PySide6
        QMessageBox.about(
            self, "About XVG Plotter",
            f"<b>XVG Plotter</b> {APP_VERSION}<br><br>"
            f"Interactive viewer for GROMACS .xvg analysis files — RMSD, energy, "
            f"RDF and other .xvg output.<br>"
            f"Trajectories (.xtc), maps (.xpm) and .edr files are not supported.<br><br>"
            f"matplotlib {matplotlib.__version__} · numpy {numpy.__version__} · "
            f"PySide6 {PySide6.__version__}")

    # -- update check (C02) ----------------------------------------------------

    def _check_updates(self) -> None:
        from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

        self.statusBar().showMessage("checking for updates…", 3000)
        nam = QNetworkAccessManager(self)
        reply = nam.get(QNetworkRequest(QUrl(updates.RELEASES_URL)))
        reply.finished.connect(lambda: self._update_reply(reply))

    def _update_reply(self, reply) -> None:
        import json

        try:
            from PySide6.QtNetwork import QNetworkReply

            if reply.error() != QNetworkReply.NetworkError.NoError:
                QMessageBox.information(
                    self, "Check for updates",
                    f"Could not check for updates:\n{reply.errorString()}")
                return
            latest = updates.latest_from_json(json.loads(bytes(reply.readAll())))
            if latest and updates.is_newer(latest, APP_VERSION):
                box = QMessageBox(self)
                box.setWindowTitle("Check for updates")
                box.setIcon(QMessageBox.Icon.Information)
                box.setText(f"A new version is available: {latest} "
                            f"(you have {APP_VERSION}).")
                open_btn = box.addButton("Open downloads",
                                         QMessageBox.ButtonRole.AcceptRole)
                box.addButton(QMessageBox.StandardButton.Close)
                box.exec()
                if box.clickedButton() is open_btn:
                    QDesktopServices.openUrl(QUrl(updates.DOWNLOADS_URL))
            else:
                QMessageBox.information(
                    self, "Check for updates",
                    f"You are up to date (version {APP_VERSION}).")
        except Exception:
            QMessageBox.information(self, "Check for updates",
                                    "Could not check for updates (no connection?).")
        finally:
            reply.deleteLater()

    # -- theme ---------------------------------------------------------------

    def _set_theme_mode(self, mode: str) -> None:
        settings.set_theme_mode(mode)
        self.retheme()

    def retheme(self) -> None:
        tokens = theme.apply(QApplication.instance())
        self.panel.apply_theme(tokens)
        for t in self._tables:
            t.retheme()
        for b in self._bars:
            b.retheme()

    def _toggle_style_tab(self, on: bool) -> None:
        self._style_tab.setText("Style ▾" if on else "Style ▸")
        self.style.setVisible(on)

    def _on_system_scheme_changed(self, *_):
        if settings.theme_mode() == settings.THEME_AUTO:
            self.retheme()

    # -- folder / files --------------------------------------------------------

    def load_folder(self, path: str | Path, pane: int = 0) -> None:
        p = Path(str(path)).expanduser()
        if p.exists():
            p = p.resolve()
        if not p.is_dir():
            self.statusBar().showMessage(f"not a folder: {p}", 4000)
            return
        bar, table = self._bars[pane], self._tables[pane]
        sc = self._scanners[pane]
        if sc is not None and sc.isRunning():
            sc.stop()
            sc.wait(2000)
        self._last_pane = pane  # Ctrl+F focuses this pane's filter
        old = self._folders[pane]
        if old is not None and old != p:
            # drop the state belonging to this pane's previous folder only;
            # the other pane (and pins, which snapshot their data) survive
            self.files = {k: v for k, v in self.files.items() if k.parent != old}
            self.active_ds = {k: v for k, v in self.active_ds.items()
                              if k.parent != old}
            self.visible = {k: v for k, v in self.visible.items()
                            if k[0].parent != old}
            if self.active is not None and self.active.parent == old:
                self.active = None
                self.series.rebuild([], self.active_ds, self.visible, False)
        table.clear_all()
        bar.set_path(str(p), settings.recent_items())
        bar.set_pinned(str(p) in settings.pinned())
        settings.add_recent(str(p))
        settings.set_("last_folder" if pane == 0 else "last_folder2", str(p))
        self._folders[pane] = p
        self._info.setText("scanning…")
        sc = FolderScanner(p, recursive=bar.recursive())  # C08
        self._scanners[pane] = sc
        sc.file_parsed.connect(lambda f, pn=pane: self._on_file(f, pn))
        sc.done.connect(lambda pn=pane: self._on_scan_done(pn))
        sc.start()

    def open_path(self, target: str) -> None:
        """Entry point for argv and second-instance launches (SPEC §10.4)."""
        p = Path(str(target)).expanduser()
        if p.exists():
            p = p.resolve()
        if p.is_dir():
            self.load_folder(p)
        elif p.is_file() and p.suffix.lower() == ".xvg":
            self._pending = [p]
            self.load_folder(p.parent)

    # -- drag & drop (C13) -------------------------------------------------------

    def dragEnterEvent(self, ev) -> None:
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()

    def dragMoveEvent(self, ev) -> None:
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()

    def dropEvent(self, ev) -> None:
        paths = [Path(u.toLocalFile()) for u in ev.mimeData().urls()
                 if u.isLocalFile()]
        ev.acceptProposedAction()
        if paths:
            self._handle_dropped_paths(paths)

    def _handle_dropped_paths(self, paths: list[Path]) -> None:
        dirs = [p for p in paths if p.is_dir()]
        files = [p for p in paths if p.is_file() and p.suffix.lower() == ".xvg"]
        if dirs:
            for i, d in enumerate(dirs[:2]):  # one pane per dropped folder
                self.load_folder(d, i)
        elif files:
            self._pending = list(dict.fromkeys(files))  # dedupe, keep order
            self.load_folder(files[0].parent)

    def _on_file(self, f: XvgFile, pane: int = 0) -> None:
        self.files[f.path] = f
        self._tables[pane].add_file(f)
        self._resnap_pins(f)
        if f.path in self._pending:
            self._pending.remove(f.path)
            self._tables[pane].sync_check(f.path, True)
            if self.active is None:
                self.active = f.path
                self._refresh_series_dock()
                self.update_plot()

    def _on_scan_done(self, pane: int = 0) -> None:
        self._pending.clear()  # drop argv/drop pre-plot targets if never parsed
        table = self._tables[pane]
        table.finish_scan()
        table.apply_filter(self._bars[pane].filter_text())
        if self.active is not None:
            # keep the plotted summary (+ C26 stats) visible after the scan text
            self.update_plot()
            return
        self._info.setText(f"{table.rowCount()} file(s) · "
                           f"{len(table._warned)} with warnings")

    # -- selection -------------------------------------------------------------

    def _checked(self) -> list[XvgFile]:
        seen: set[Path] = set()
        out = []
        for t in self._tables:
            for f in t.ordered_checked():
                if f.path not in seen:  # same file open in both panes → plot once
                    seen.add(f.path)
                    out.append(f)
        return out

    def _targets(self) -> list[XvgFile]:
        ts = self._checked()
        if not ts and self.active is not None:
            t = self.files.get(self.active)
            ts = [t] if t else []
        return ts

    def _primary(self, ts: list[XvgFile]) -> XvgFile | None:
        """Active file drives title/labels/units when plotted, else first."""
        if ts and self.active is not None:
            for f in ts:
                if f.path == self.active:
                    return f
        return ts[0] if ts else None

    def _on_overlay(self, f: XvgFile, on: bool) -> None:
        cur = self._checked()
        if on and self.active is None:
            self.active = f.path
        elif not on and self.active == f.path:
            self.active = cur[0].path if cur else None
        self._refresh_series_dock()
        self.update_plot()

    def _on_activate(self, f: XvgFile) -> None:
        if not f.datasets and f.warnings:  # C09: hydrate a cloud placeholder on demand
            f = parse_file(f.path)
            self.files[f.path] = f
        for pn, t in enumerate(self._tables):
            if self._folders[pn] == f.path.parent:
                t.set_checked_only(f.path)
            else:
                t.uncheck_all()
        self.active = f.path
        self._refresh_series_dock()
        self.update_plot()

    def _on_series_toggled(self, f: XvgFile, i: int, on: bool) -> None:
        key = (f.path, self.active_ds.get(f.path, 0), i)
        self.visible[key] = on
        self.update_plot()

    def _on_dataset_changed(self, f: XvgFile, i: int) -> None:
        self.active_ds[f.path] = i
        self._refresh_series_dock()
        self.update_plot()

    # -- curve pins (right-click a legend entry) ---------------------------------

    def _on_pin_requested(self, label: str) -> None:
        m = QMenu(self)
        act = m.addAction("📌 Unpin curve" if label in self.pins else "📌 Pin curve")
        act.triggered.connect(lambda: self._toggle_pin(label))
        m.exec(QCursor.pos())

    def _toggle_pin(self, label: str) -> None:
        if label in self.pins:
            del self.pins[label]
            self.update_plot()
            return
        for e in self._entries:
            if not isinstance(e, Line) or e.label != label:
                continue
            pl = label
            if e.source is not None and not label.startswith(e.source.stem):
                pl = f"{e.source.stem}: {label}"
            data = (self._pin_data(e.source, e.ds_idx, e.series_idx)
                    if e.source is not None and e.ds_idx >= 0 else None)
            if data is not None:
                self.pins[pl] = PinnedCurve(
                    pl, e.source, e.ds_idx, e.series_idx, *data)
            else:  # averaged/derived curve: keep the plotted arrays as-is
                self.pins[pl] = PinnedCurve(pl, None, -1, -1, e.x, e.y, e.dy, e.dx)
            break
        self.update_plot()

    def _pin_data(self, path: Path, ds_idx: int, series_idx: int):
        """Unit-converted series data for a pin target, or None if gone."""
        f = self.files.get(path)
        if f is None or ds_idx >= len(f.datasets):
            return None
        ds = f.datasets[ds_idx]
        if series_idx >= len(ds.series):
            return None
        s = ds.series[series_idx]
        unit = self._unit(self._targets(), self.style.state().unit)
        return (analysis.convert_x(ds.x, unit), ds.columns[s.y_col],
                ds.columns[s.dy_col] if s.dy_col is not None else None,
                analysis.convert_x(ds.columns[s.dx_col], unit)
                if s.dx_col is not None else None)

    def _resnap_pins(self, f: XvgFile) -> None:
        """A folder refresh re-parses files; refresh this file's pins in place."""
        for pin in self.pins.values():
            if pin.path != f.path:
                continue
            data = self._pin_data(pin.path, pin.ds_idx, pin.series_idx)
            if data is not None:  # structure changed → keep the old snapshot
                pin.x, pin.y, pin.dy, pin.dx = data

    def _clear_pins(self) -> None:
        if self.pins:
            self.pins.clear()
            self.update_plot()

    def _refresh_series_dock(self) -> None:
        ts = self._targets()
        self.series.rebuild(ts, self.active_ds, self.visible, self._compatible(ts),
                            self._colors)

    def _compatible(self, files: list[XvgFile]) -> bool:
        if len(files) < 2:
            return False
        sigs = set()
        try:
            for f in files:
                ds = f.datasets[self.active_ds.get(f.path, 0)]
                sigs.add((len(ds.columns),
                          tuple((s.kind, s.y_col, s.dy_col, s.dx_col, s.legend)
                                for s in ds.series)))
        except (IndexError, KeyError):
            return False
        return len(sigs) == 1

    # -- plotting ----------------------------------------------------------------

    def _unit(self, ts: list[XvgFile], unit_mode: str) -> str:
        if unit_mode != "auto":
            return unit_mode
        # C25: 'auto' only rescales genuine time axes, never frame indices etc.
        src = self._primary(ts)
        if src and src.datasets and analysis.is_time_label(src.x_label):
            ds = src.datasets[self.active_ds.get(src.path, 0)]
            if ds.x.size:
                return analysis.auto_unit(ds.x)
        return "ps"

    def _compose_state(self, ts: list[XvgFile]) -> PlotState:
        st = PlotState()
        sst = self.style.state()
        ast = self.series.analysis_state()
        st.logx, st.logy, st.grid = sst.logx, sst.logy, sst.grid
        st.legend = sst.legend
        colors = _ColorCycle(PALETTES.get(sst.palette))
        style = LINE_STYLES[sst.line]
        width = sst.width
        avg_on = ast.average and self._compatible(ts)
        unit = self._unit(ts, sst.unit)
        src = self._primary(ts)
        time_like = analysis.is_time_label(src.x_label) if src else False

        if src:
            st.title = sst.title or src.title or src.path.stem
            # C25: a non-time X axis keeps its own label; no "(unit)" is appended
            st.xlabel = sst.xlabel or (analysis.scale_label(src.x_label, unit)
                                       if time_like
                                       else (src.x_label or ""))
            st.ylabel = sst.ylabel or (src.y_label or "")

        self._avg_warning = None
        if ts:
            if avg_on:
                n_series = min(
                    len(f.datasets[self.active_ds.get(f.path, 0)].series) for f in ts)
                for i in range(n_series):
                    legend = series_label(
                        ts[0].datasets[self.active_ds.get(ts[0].path, 0)].series[i],
                        ts[0].y_label, n_series)
                    curves = []
                    for f in ts:
                        ds = f.datasets[self.active_ds.get(f.path, 0)]
                        s = ds.series[i]
                        curves.append((analysis.convert_x(ds.x, unit),
                                       ds.columns[s.y_col]))
                    x, mean, std, warn = analysis.average_replicas(
                        curves, common_range=ast.common_range)
                    if warn and not self._avg_warning:
                        self._avg_warning = warn
                    c = colors.next()
                    line = Line(x, mean, label=legend or f"series {i + 1}",
                                color=c, style=style, width=width + 0.5)
                    if ast.smooth:
                        line.smooth = analysis.moving_average(mean, ast.window)
                    st.entries.append(line)
                    st.entries.append(Band(x, mean - std, mean + std, color=c))
                    if ast.members:
                        for _, my in curves:
                            st.entries.append(Line(x, my, color=c, width=0.7, alpha=0.3))
            else:
                multi = len(ts) > 1
                for f in ts:
                    if not f.datasets:
                        continue
                    ds_i = self.active_ds.get(f.path, 0)
                    ds = f.datasets[ds_i]
                    for i, s in enumerate(ds.series):
                        if not self.visible.get((f.path, ds_i, i), True):
                            continue
                        x = analysis.convert_x(ds.x, unit)
                        y = ds.columns[s.y_col]
                        # C17: per-series color override, else the palette cycle
                        c = self._colors.get((f.path, ds_i, i)) or colors.next()
                        base = series_label(s, f.y_label, len(ds.series))
                        line = Line(
                            x, y,
                            label=f"{f.path.stem}: {base}" if multi else base,
                            color=c, style=style, width=width,
                            dy=ds.columns[s.dy_col] if s.dy_col is not None else None,
                            # C25: x error bars follow the same unit conversion as X
                            dx=analysis.convert_x(ds.columns[s.dx_col], unit)
                            if s.dx_col is not None else None,
                            source=f.path, ds_idx=ds_i, series_idx=i)
                        if ast.smooth:
                            line.smooth = analysis.moving_average(y, ast.window)
                        st.entries.append(line)
        # pinned curves ride along on every render; skip ones already plotted.
        # they follow the current palette/line style like live curves do
        for pin in self.pins.values():
            if any(isinstance(e, Line) and e.label == pin.label for e in st.entries):
                continue
            st.entries.append(Line(pin.x, pin.y, label=pin.label, color=colors.next(),
                                   style=style, width=width, dy=pin.dy, dx=pin.dx))
        key = []
        for f in ts:
            ds_i = self.active_ds.get(f.path, 0)
            if ds_i >= len(f.datasets):
                continue
            ds = f.datasets[ds_i]
            key.append((f.path, ds_i,
                        tuple(i for i, s in enumerate(ds.series)
                              if self.visible.get((f.path, ds_i, i), True))))
        st.data_key = tuple(key)
        return st

    def update_plot(self, *_) -> None:
        ts = self._targets()
        sst = self.style.state()
        self.panel.set_font_family(None if sst.font == "Match UI" else sst.font)
        if sst.fig_w != float(settings.get("view/fig_w", 0.0) or 0.0):
            settings.set_("view/fig_w", sst.fig_w)
        if sst.fig_h != float(settings.get("view/fig_h", 0.0) or 0.0):
            settings.set_("view/fig_h", sst.fig_h)
        if sst.font != str(settings.get("view/font", "Match UI")):
            settings.set_("view/font", sst.font)
        st = self._compose_state(ts)
        self._entries = st.entries
        self.panel.render(st)
        self._update_time_hint(ts)
        if ts:
            parts = [f"{len(ts)} file(s) plotted"]
            summary = analysis.series_summary(
                [(e.label, e.y) for e in st.entries if getattr(e, "label", "")])
            if summary:
                parts.append(summary)
            if self._avg_warning:
                parts.append("⚠ " + self._avg_warning)
            if len(ts) > 1 and len({analysis.is_time_label(f.x_label)
                                    for f in ts}) > 1:
                parts.append("⚠ mixed X axes (time vs other) — check units")
            self._info.setText(" · ".join(parts))
        else:
            self._info.setText("no file selected")

    def _update_time_hint(self, ts: list[XvgFile]) -> None:
        """Physical span of the smoothing window on the active file (C28)."""
        txt = ""
        src = self._primary(ts)
        if src and src.datasets and analysis.is_time_label(src.x_label):
            ds = src.datasets[self.active_ds.get(src.path, 0)]
            unit = self._unit(ts, self.style.state().unit)
            dt = analysis.median_dt(ds.x) * analysis.UNITS[unit]
            if dt > 0:
                win = self.series.analysis_state().window
                txt = f"≈ {dt * win:.3g} {unit}"
        self.series.set_time_hint(txt)

    # -- export -----------------------------------------------------------------

    def _current_dir(self) -> str:
        t = self._targets()
        if t:
            return str(t[0].path.parent)
        d = self.folder_bar.current_folder()
        return d if Path(d).is_dir() else str(Path.home())

    def _fig_size(self) -> tuple | None:
        """C16: the requested (w, h) inches, or None for auto size."""
        sst = self.style.state()
        if sst.fig_w > 0 and sst.fig_h > 0:
            return (sst.fig_w, sst.fig_h)
        return None

    def export_dialog(self) -> None:
        t = self._targets()
        base = (t[0].title or t[0].path.stem) if t else "plot"
        safe = "".join(ch if ch not in '\\/:*?"<>|' else "_" for ch in base)
        dlg = ExportDialog(
            safe, self._current_dir(),
            dpi=int(settings.get("export/dpi") or 300),
            fmt=str(settings.get("export/fmt", "png")),
            transparent=str(settings.get("export/transparent", "false")).lower() == "true",
            parent=self)
        if dlg.exec():
            o = dlg.options()
            size = self._fig_size()
            st = self._compose_state(self._targets())
            try:
                with self.panel.full_render(st, size):  # C23 full data, C16 exact size
                    save_figure(self.panel.fig, o["path"], o["dpi"], o["transparent"],
                                tight=size is None)
            except (OSError, ValueError, RuntimeError) as e:
                QMessageBox.warning(self, "Export failed",
                                    f"Could not write {o['path']}:\n{e}")
                return
            settings.set_("export/dpi", o["dpi"])
            settings.set_("export/fmt", o["fmt"])
            settings.set_("export/transparent", o["transparent"])
            self.statusBar().showMessage(f"saved {o['path']}", 5000)

    def _ask_directory(self, title: str, default: str) -> str:
        return QFileDialog.getExistingDirectory(self, title, default)

    def _ask_save_path(self, title: str, default: str) -> str:
        path, _ = QFileDialog.getSaveFileName(self, title, default, "CSV (*.csv)")
        return path

    def _export_batch(self) -> None:
        """C29: render every checked file as its own plot, one folder, no loops
        through the export dialog."""
        ts = self._checked()
        if not ts:
            self.statusBar().showMessage("check files to export first", 4000)
            return
        d = self._ask_directory("Export all checked plots to", self._current_dir())
        if not d:
            return
        dpi = int(settings.get("export/dpi") or 300)
        fmt = str(settings.get("export/fmt", "png"))
        transparent = (str(settings.get("export/transparent", "false")).lower()
                       == "true") and fmt != "eps"
        prog = QProgressDialog(f"Exporting {len(ts)} plots…", "Cancel",
                               0, len(ts), self)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        size = self._fig_size()
        saved = 0
        try:
            for i, f in enumerate(ts):
                prog.setValue(i)
                QApplication.processEvents()
                if prog.wasCanceled():
                    break
                base = f.title or f.path.stem
                safe = "".join(ch if ch not in '\\/:*?"<>|' else "_" for ch in base)
                out = Path(d) / f"{safe}.{fmt}"
                n = 2
                while out.exists():
                    out = Path(d) / f"{safe}-{n}.{fmt}"
                    n += 1
                st = self._compose_state([f])
                try:
                    with self.panel.full_render(st, size):  # C23 + C16
                        save_figure(self.panel.fig, out, dpi, transparent,
                                    tight=size is None)
                    saved += 1
                except (OSError, ValueError, RuntimeError) as e:
                    QMessageBox.warning(self, "Export failed",
                                        f"Could not write {out}:\n{e}")
            prog.setValue(len(ts))
        finally:
            self.update_plot()  # back to the interactive (decimated) view
        self.statusBar().showMessage(f"exported {saved} plot(s) to {d}", 6000)

    def _csv_sections(self, ts: list[XvgFile]) -> list:
        """CSV blocks for the current view: averaged curves, or one block per
        file with every visible series (± / dx columns included) — C30."""
        sst = self.style.state()
        ast = self.series.analysis_state()
        unit = self._unit(ts, sst.unit)
        sections = []
        if ast.average and self._compatible(ts):
            n_series = min(len(f.datasets[self.active_ds.get(f.path, 0)].series)
                           for f in ts)
            for i in range(n_series):
                legend = series_label(
                    ts[0].datasets[self.active_ds.get(ts[0].path, 0)].series[i],
                    ts[0].y_label, n_series) or f"series {i + 1}"
                curves = []
                for f in ts:
                    ds = f.datasets[self.active_ds.get(f.path, 0)]
                    s = ds.series[i]
                    curves.append((analysis.convert_x(ds.x, unit),
                                   ds.columns[s.y_col]))
                x, mean, std, _ = analysis.average_replicas(
                    curves, common_range=ast.common_range)
                sections.append((
                    [f"# replica average: {legend}", f"# x unit: {unit}"],
                    ["x", legend, legend + " SD"],
                    [x, mean, std]))
            return sections
        multi = len(ts) > 1
        for f in ts:
            if not f.datasets:
                continue
            ds_i = self.active_ds.get(f.path, 0)
            ds = f.datasets[ds_i]
            headers = ["x"]
            cols = [analysis.convert_x(ds.x, unit)]
            for i, s in enumerate(ds.series):
                if not self.visible.get((f.path, ds_i, i), True):
                    continue
                base = series_label(s, f.y_label, len(ds.series))
                prefix = f"{f.path.stem}: {base}" if multi else base
                headers.append(prefix)
                cols.append(ds.columns[s.y_col])
                if s.dy_col is not None:
                    headers.append(prefix + " ±")
                    cols.append(ds.columns[s.dy_col])
                if s.dx_col is not None:
                    headers.append(prefix + " dx")
                    cols.append(analysis.convert_x(ds.columns[s.dx_col], unit))
            sections.append(([f"# file: {f.path.name}", f"# x unit: {unit}"],
                             headers, cols))
        return sections

    def _export_data(self) -> None:
        """C30: save the plotted (unit-converted, averaged) series as numbers."""
        ts = self._targets()
        if not ts:
            self.statusBar().showMessage("nothing plotted to export", 4000)
            return
        src = self._primary(ts)
        base = (src.title or src.path.stem) if src else "data"
        safe = "".join(ch if ch not in '\\/:*?"<>|' else "_" for ch in base)
        path = self._ask_save_path("Export data (CSV)",
                                   str(Path(self._current_dir()) / f"{safe}.csv"))
        if not path:
            return
        try:
            write_csv(Path(path), self._csv_sections(ts))
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "Export failed", f"Could not write {path}:\n{e}")
            return
        self.statusBar().showMessage(f"saved {path}", 5000)

    def _print_plot(self, printer=None) -> None:
        """C33: print the current plot at the printer's resolution."""
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter

        if printer is None:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dlg = QPrintDialog(printer, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
        st = self._compose_state(self._targets())
        try:
            with self.panel.full_render(st):
                print_figure(self.panel.fig, printer)
        except (OSError, ValueError, RuntimeError) as e:
            QMessageBox.warning(self, "Print", f"Could not print:\n{e}")
            return
        self.statusBar().showMessage("sent to printer", 4000)

    def _copy_image(self) -> None:
        try:
            st = self._compose_state(self._targets())
            with self.panel.full_render(st):
                copy_image(
                    self.panel.canvas,
                    dpi=int(settings.get("export/dpi") or 300),
                    transparent=str(settings.get("export/transparent", "false"))
                    .lower() == "true")
        except Exception as e:
            QMessageBox.warning(self, "Copy Image", f"Could not copy the plot: {e}")
            return
        self.statusBar().showMessage("plot image copied to clipboard", 4000)

    # -- windows / focus mode / shortcuts ----------------------------------------

    def _new_window(self) -> None:
        """C22 residual: a real second window for two-monitor setups."""
        d = self._ask_directory("Open folder in new window", self._current_dir())
        if not d:
            return
        w = MainWindow(primary=False)
        _WINDOWS.append(w)
        w.show()
        w.load_folder(d)

    def _toggle_focus(self, on: bool) -> None:
        """C20: hide every panel so only the plot remains."""
        if on:
            self._focus_state = ([not d.isHidden() for d in self._docks]
                                 + [self._style_tab.isChecked()])
            for d in self._docks:
                d.setVisible(False)
            self._style_tab.setChecked(False)
        else:
            for d, vis in zip(self._docks, self._focus_state[:len(self._docks)]):
                d.setVisible(vis)
            self._style_tab.setChecked(self._focus_state[len(self._docks)])

    def _focus_filter(self) -> None:
        bar = self._bars[self._last_pane]
        bar.edit_filter.setFocus()
        bar.edit_filter.selectAll()

    def _refresh_all(self) -> None:
        for pn, bar in enumerate(self._bars):
            cur = bar.current_folder()
            if cur and Path(cur).is_dir():
                self.load_folder(cur, pn)

    def _on_recursive(self, on: bool, pane: int = 0) -> None:
        settings.set_("scan/recursive", on)
        cur = self._bars[pane].current_folder()
        if cur and Path(cur).is_dir():
            self.load_folder(cur, pane)

    def _on_series_color(self, f: XvgFile, ds_i: int, i: int, color) -> None:
        """C17: per-series color override (None = back to the palette cycle)."""
        if color:
            self._colors[(f.path, ds_i, i)] = color
        else:
            self._colors.pop((f.path, ds_i, i), None)
        self.update_plot()

    # -- pinning / settings files / association ----------------------------------

    def _on_pin_toggled(self, on: bool, pane: int = 0) -> None:
        bar = self._bars[pane]
        cur = bar.current_folder()
        if not cur:
            return
        settings.toggle_pinned(cur)
        bar.set_pinned(cur in settings.pinned())
        bar.set_path(cur, settings.recent_items())

    def _export_settings(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export settings", "xvg-plotter-settings.ini",
            "Settings (*.ini)")
        if not path:
            return
        n = settings.export_settings(path)
        self.statusBar().showMessage(f"exported {n} settings", 5000)

    def _import_settings(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import settings", "",
                                              "Settings (*.ini)")
        if not path:
            return
        n = settings.import_settings(path)
        self.retheme()
        for b in self._bars:
            cur = b.current_folder()
            b.set_path(cur, settings.recent_items())
            b.set_pinned(cur in settings.pinned())
        QMessageBox.information(
            self, "Import settings",
            f"Imported {n} settings. Window layout applies after a restart.")

    def _set_default_viewer(self) -> None:
        if not getattr(sys, "frozen", False):
            QMessageBox.information(
                self, "Set as default .xvg viewer",
                "This is a development run from source; the file association is "
                "registered by the installed app.")
            return
        ret = QMessageBox.question(
            self, "Set as default .xvg viewer",
            "Register XVG Plotter as an app for .xvg files (current user)?")
        if ret != QMessageBox.StandardButton.Yes:
            return
        try:
            fileassoc.register_xvg_association(str(Path(sys.executable)))
        except OSError as e:
            QMessageBox.warning(self, "Set as default .xvg viewer",
                                f"Could not update the registry:\n{e}")
            return
        QMessageBox.information(
            self, "Set as default .xvg viewer",
            "XVG Plotter was registered for .xvg files. If Windows still asks, "
            "pick it in the Open-with dialog or under Settings ▸ Default apps.")

    # -- lifecycle -----------------------------------------------------------------

    def closeEvent(self, ev) -> None:
        if self._primary_window:  # C22: secondary windows never touch saved state
            settings.set_("geometry", self.saveGeometry())
            settings.set_("window_state", self.saveState())
        super().closeEvent(ev)
