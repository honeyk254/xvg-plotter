"""Main window: menus, docks, wiring, plot state composition (SPEC §6)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .. import settings
from ..core import analysis
from ..core.models import XvgFile, series_label
from ..export import copy_image, save_figure
from ..version import APP_VERSION
from . import theme
from .export_dialog import ExportDialog
from .file_table import FileTable, FolderScanner
from .folder_bar import FolderBar
from .options import LINE_STYLES, PALETTES
from .plot_canvas import Band, Line, PlotPanel, PlotState
from .series_dock import SeriesDock
from .style_dock import StyleDock

DEFAULT_SIZE = (1150, 720)
MIN_SIZE = (900, 560)


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XVG Plotter")
        self.files: dict[Path, XvgFile] = {}
        self.active: Path | None = None
        self.active_ds: dict[Path, int] = {}
        self.visible: dict[tuple[Path, int, int], bool] = {}
        self._scanner: FolderScanner | None = None
        self._pending: Path | None = None
        self._avg_warning: str | None = None

        self.folder_bar = FolderBar(settings.recents())
        self.table = FileTable()
        self.series = SeriesDock()
        self.style = StyleDock()
        self.panel = PlotPanel()

        files_widget = QWidget()
        v = QVBoxLayout(files_widget)
        v.setContentsMargins(theme.SP_S, theme.SP_S, theme.SP_S, 0)
        v.setSpacing(theme.SP_S)
        v.addWidget(self.folder_bar)
        v.addWidget(self.table)

        dock_files = QDockWidget("Files", self)
        dock_files.setObjectName("files")
        dock_files.setWidget(files_widget)
        dock_series = QDockWidget("Series && analysis", self)
        dock_series.setObjectName("series")
        dock_series.setWidget(self.series)
        dock_style = QDockWidget("Style", self)
        dock_style.setObjectName("style")
        dock_style.setWidget(self.style)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_files)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_series)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_style)
        self.splitDockWidget(dock_files, dock_series, Qt.Orientation.Vertical)
        self.setCentralWidget(self.panel)
        self._docks = (dock_files, dock_series, dock_style)
        self.resizeDocks([dock_files, dock_style], [300, 220], Qt.Orientation.Horizontal)
        self.resizeDocks([dock_files, dock_series], [350, 280], Qt.Orientation.Vertical)
        self.resize(*DEFAULT_SIZE)
        self.setMinimumSize(*MIN_SIZE)

        self._menus()

        self.folder_bar.folder_requested.connect(self.load_folder)
        self.folder_bar.refresh_requested.connect(
            lambda: self.load_folder(self.folder_bar.current_folder()))
        self.folder_bar.filter_changed.connect(self.table.apply_filter)
        self.table.overlay_toggled.connect(self._on_overlay)
        self.table.file_activated.connect(self._on_activate)
        self.series.series_toggled.connect(self._on_series_toggled)
        self.series.dataset_changed.connect(self._on_dataset_changed)
        self.series.options_changed.connect(self.update_plot)
        self.style.style_changed.connect(self.update_plot)
        self.panel.save_requested.connect(self.export_dialog)
        self.panel.coords.connect(lambda s: self.statusBar().showMessage(s))

        self._info = QLabel("no folder loaded")
        self.statusBar().addWidget(self._info, 1)

        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self._on_system_scheme_changed)

        for key, restore in (("geometry", self.restoreGeometry),
                             ("window_state", self.restoreState)):
            val = settings.get(key)
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
        a = QAction("Refresh", self)
        a.setShortcut(QKeySequence("F5"))
        a.triggered.connect(lambda: self.load_folder(self.folder_bar.current_folder()))
        m_file.addAction(a)
        m_file.addSeparator()
        a = QAction("Export…", self)
        a.setShortcut(QKeySequence("Ctrl+E"))
        a.triggered.connect(self.export_dialog)
        m_file.addAction(a)
        a = QAction("Copy Image", self)
        a.setShortcut(QKeySequence("Ctrl+Shift+C"))
        a.triggered.connect(self._copy_image)
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

        m_help = mb.addMenu("&Help")
        a = QAction("About", self)
        a.triggered.connect(self._about)
        m_help.addAction(a)

    def _about(self) -> None:
        import matplotlib
        import numpy
        import PySide6
        QMessageBox.about(
            self, "About XVG Plotter",
            f"<b>XVG Plotter</b> {APP_VERSION}<br><br>"
            f"Interactive viewer for GROMACS .xvg analysis files.<br>"
            f"matplotlib {matplotlib.__version__} · numpy {numpy.__version__} · "
            f"PySide6 {PySide6.__version__}")

    # -- theme ---------------------------------------------------------------

    def _set_theme_mode(self, mode: str) -> None:
        settings.set_theme_mode(mode)
        self.retheme()

    def retheme(self) -> None:
        tokens = theme.apply(QApplication.instance())
        self.panel.apply_theme(tokens)
        self.table.retheme()
        self.folder_bar.retheme()

    def _on_system_scheme_changed(self, *_):
        if settings.theme_mode() == settings.THEME_AUTO:
            self.retheme()

    # -- folder / files --------------------------------------------------------

    def load_folder(self, path: str | Path) -> None:
        p = Path(str(path)).expanduser()
        if p.exists():
            p = p.resolve()
        if not p.is_dir():
            self.statusBar().showMessage(f"not a folder: {p}", 4000)
            return
        if self._scanner is not None and self._scanner.isRunning():
            self._scanner.stop()
            self._scanner.wait(2000)
        self.files.clear()
        self.active = None
        self.active_ds.clear()
        self.visible.clear()
        self.table.clear_all()
        self.series.rebuild([], self.active_ds, self.visible, False)
        self.folder_bar.set_path(str(p), settings.recents())
        settings.add_recent(str(p))
        settings.set_("last_folder", str(p))
        self._info.setText("scanning…")
        self._scanner = FolderScanner(p)
        self._scanner.file_parsed.connect(self._on_file)
        self._scanner.done.connect(self._on_scan_done)
        self._scanner.start()

    def open_path(self, target: str) -> None:
        """Entry point for argv and second-instance launches (SPEC §10.4)."""
        p = Path(str(target)).expanduser()
        if p.exists():
            p = p.resolve()
        if p.is_dir():
            self.load_folder(p)
        elif p.is_file() and p.suffix.lower() == ".xvg":
            self._pending = p
            self.load_folder(p.parent)

    def _on_file(self, f: XvgFile) -> None:
        self.files[f.path] = f
        self.table.add_file(f)
        if self._pending == f.path:
            self._pending = None
            self.table.sync_check(f.path, True)
            self.active = f.path
            self._refresh_series_dock()
            self.update_plot()

    def _on_scan_done(self) -> None:
        self._pending = None  # drop argv pre-plot target if its file never appeared
        self.table.finish_scan()
        self.table.apply_filter(self.folder_bar.filter_text())
        n = len(self.files)
        w = sum(1 for f in self.files.values() if f.warnings)
        self._info.setText(f"{n} file(s) · {w} with warnings")

    # -- selection -------------------------------------------------------------

    def _targets(self) -> list[XvgFile]:
        ts = self.table.ordered_checked()
        if not ts and self.active is not None:
            t = self.files.get(self.active)
            ts = [t] if t else []
        return ts

    def _on_overlay(self, f: XvgFile, on: bool) -> None:
        cur = self.table.ordered_checked()
        if on and self.active is None:
            self.active = f.path
        elif not on and self.active == f.path:
            self.active = cur[0].path if cur else None
        self._refresh_series_dock()
        self.update_plot()

    def _on_activate(self, f: XvgFile) -> None:
        self.table.set_checked_only(f.path)
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

    def _refresh_series_dock(self) -> None:
        ts = self._targets()
        self.series.rebuild(ts, self.active_ds, self.visible, self._compatible(ts))

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
        if ts and ts[0].datasets:
            ds = ts[0].datasets[self.active_ds.get(ts[0].path, 0)]
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

        if ts:
            st.title = sst.title or ts[0].title or ts[0].path.stem
            st.xlabel = sst.xlabel or analysis.scale_label(ts[0].x_label, unit)
            st.ylabel = sst.ylabel or (ts[0].y_label or "")

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
                    x, mean, std, warn = analysis.average_replicas(curves)
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
                        c = colors.next()
                        base = series_label(s, f.y_label, len(ds.series))
                        line = Line(
                            x, y,
                            label=f"{f.path.stem}: {base}" if multi else base,
                            color=c, style=style, width=width,
                            dy=ds.columns[s.dy_col] if s.dy_col is not None else None,
                            dx=ds.columns[s.dx_col] if s.dx_col is not None else None)
                        if ast.smooth:
                            line.smooth = analysis.moving_average(y, ast.window)
                        st.entries.append(line)
        return st

    def update_plot(self, *_) -> None:
        ts = self._targets()
        self.panel.render(self._compose_state(ts))
        if ts:
            parts = [f"{len(ts)} file(s) plotted"]
            if self._avg_warning:
                parts.append("⚠ " + self._avg_warning)
            self._info.setText(" · ".join(parts))
        else:
            self._info.setText("no file selected")

    # -- export -----------------------------------------------------------------

    def _current_dir(self) -> str:
        t = self._targets()
        if t:
            return str(t[0].path.parent)
        d = self.folder_bar.current_folder()
        return d if Path(d).is_dir() else str(Path.home())

    def export_dialog(self) -> None:
        t = self._targets()
        base = (t[0].title or t[0].path.stem) if t else "plot"
        safe = "".join(ch if ch not in '\\/:*?"<>|' else "_" for ch in base)
        dlg = ExportDialog(
            safe, self._current_dir(),
            dpi=int(settings.get("export/dpi", 300)),
            fmt=str(settings.get("export/fmt", "png")),
            transparent=str(settings.get("export/transparent", "false")).lower() == "true",
            parent=self)
        if dlg.exec():
            o = dlg.options()
            try:
                save_figure(self.panel.fig, o["path"], o["dpi"], o["transparent"])
            except (OSError, ValueError, RuntimeError) as e:
                QMessageBox.warning(self, "Export failed",
                                    f"Could not write {o['path']}:\n{e}")
                return
            settings.set_("export/dpi", o["dpi"])
            settings.set_("export/fmt", o["fmt"])
            settings.set_("export/transparent", o["transparent"])
            self.statusBar().showMessage(f"saved {o['path']}", 5000)

    def _copy_image(self) -> None:
        try:
            copy_image(self.panel.canvas)
        except Exception as e:
            QMessageBox.warning(self, "Copy Image", f"Could not copy the plot: {e}")
            return
        self.statusBar().showMessage("plot image copied to clipboard", 4000)

    # -- lifecycle -----------------------------------------------------------------

    def closeEvent(self, ev) -> None:
        settings.set_("geometry", self.saveGeometry())
        settings.set_("window_state", self.saveState())
        super().closeEvent(ev)
