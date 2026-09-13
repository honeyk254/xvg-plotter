"""Plot canvas + toolbar + legend toggling (SPEC §6.3)."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("QtAgg")
import matplotlib as mpl
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .options import LEGEND_LOCS, LINE_STYLES, PALETTES  # noqa: F401  (re-exported)
from .theme import LIGHT, Tokens, current
from ..core import analysis

_FONT_BASE = ["DejaVu Sans", "Microsoft YaHei", "PingFang SC",
              "Noto Sans CJK SC", "Malgun Gothic", "Arial"]
DECIMATE_POINTS = 20000  # interactive cap; exports re-render with full=True (C23)


@dataclass
class Line:
    x: np.ndarray
    y: np.ndarray
    label: str = ""
    color: str = "C0"
    style: str = "-"
    width: float = 1.5
    alpha: float = 1.0
    dy: np.ndarray | None = None
    dx: np.ndarray | None = None
    smooth: np.ndarray | None = None  # dashed overlay, excluded from legend
    source: Path | None = None  # owning file, for pin labeling
    ds_idx: int = -1  # dataset/series position, for pin re-snapshot on refresh
    series_idx: int = -1


@dataclass
class Band:
    x: np.ndarray
    lo: np.ndarray
    hi: np.ndarray
    color: str = "#000000"


@dataclass
class PlotState:
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    logx: bool = False
    logy: bool = False
    grid: bool = True
    legend: str = "best"
    entries: list = field(default_factory=list)
    # identity of the plotted data (file/dataset/series), not just its labels;
    # lets render() tell "style change, keep zoom" from "file switched, rescale"
    data_key: tuple = ()


def _recolored_icon(name: str, color: str) -> QIcon | None:
    """Tint one of matplotlib's black toolbar glyphs with the theme text color."""
    img_dir = Path(matplotlib.get_data_path()) / "images"
    icon = QIcon()
    for suffix, dpr in (("", 1.0), ("_large", 2.0)):
        p = img_dir / f"{name}{suffix}.png"
        if not p.exists():
            continue
        img = QImage(str(p)).convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        if img.isNull():
            continue
        painter = QPainter(img)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(img.rect(), QColor(color))
        painter.end()
        pm = QPixmap.fromImage(img)
        pm.setDevicePixelRatio(dpr)
        icon.addPixmap(pm)
    return None if icon.isNull() else icon


class _Toolbar(NavigationToolbar2QT):
    save_requested = Signal()

    def save_figure(self, *args, **kwargs):  # route to the app's export dialog (SPEC §6.3)
        self.save_requested.emit()

    def _icon(self, name):
        ic = _recolored_icon(name.removesuffix(".png"), current().text)
        return ic if ic is not None else super()._icon(name)

    def retheme(self) -> None:
        for _text, _tip, image, callback in self.toolitems:
            if image is None or callback not in self._actions:
                continue
            self._actions[callback].setIcon(self._icon(image + ".png"))


class PlotPanel(QWidget):
    coords = Signal(str)
    save_requested = Signal()
    pin_requested = Signal(str)  # right-click on a legend entry (label)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(constrained_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = _Toolbar(self.canvas, self)
        self.toolbar.save_requested.connect(self.save_requested)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.toolbar)
        lay.addWidget(self.canvas)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self.canvas.mpl_connect("pick_event", self._on_pick)
        self.canvas.mpl_connect("button_press_event", self._on_button)
        self._targets: list = []
        self._last_state = PlotState()
        self._font_family: str | None = None  # C16: explicit user font, if any
        self._view: tuple | None = None  # (labels, data_key, xlim, ylim)
        self.apply_theme(current())

    def apply_theme(self, t: Tokens) -> None:
        # the plot stays publication-light in every UI theme (academia style);
        # only the chrome (toolbar, docks) follows the dark/light setting
        t = LIGHT
        self._tokens = t
        chain = ([self._font_family] + _FONT_BASE) if self._font_family else _FONT_BASE
        mpl.rcParams.update({
            "font.size": 9,
            # C36: platform CJK fonts after DejaVu keep µ Å ± ε and Chinese/
            # Japanese/Korean titles from rendering as boxes; unicode_minus
            # avoids U+2212, which several of those fonts lack.
            "font.family": "sans-serif",
            "font.sans-serif": chain,
            "axes.unicode_minus": False,
            "text.color": t.text,
            "axes.titlecolor": t.text,
            "axes.labelcolor": t.text,
            "axes.edgecolor": t.border_strong,
            "xtick.color": t.border_strong,
            "ytick.color": t.border_strong,
            "xtick.labelcolor": t.dim,
            "ytick.labelcolor": t.dim,
            "figure.facecolor": t.canvas,
            "axes.facecolor": t.canvas,
            "savefig.facecolor": t.canvas,
            "savefig.edgecolor": t.border,
            "grid.color": t.grid,
        })
        self.fig.set_facecolor(t.canvas)
        self.toolbar.retheme()
        self.render(self._last_state)

    def set_font_family(self, family: str | None) -> None:
        """Explicit font family for plots, or None to follow the C36 chain (C16)."""
        if family != self._font_family:
            self._font_family = family
            self.apply_theme(current())

    @contextmanager
    def full_render(self, st: PlotState, size: tuple | None = None):
        """Re-render without decimation for an export/print, then restore (C23).

        size=(w, h) also applies a fixed figure size in inches for the export
        (C16) and restores the previous one afterwards."""
        old_size = self.fig.get_size_inches()
        if size is not None:
            self.fig.set_size_inches(size[0], size[1], forward=False)
        self.render(st, full=True)
        try:
            yield
        finally:
            if size is not None:
                self.fig.set_size_inches(float(old_size[0]), float(old_size[1]),
                                         forward=False)
            self.render(st, full=False)

    def render(self, st: PlotState, full: bool = False) -> None:
        t = self._tokens
        labels_now = frozenset(e.label for e in st.entries if getattr(e, "label", ""))
        # carry the current (possibly user-zoomed) view across the redraw when
        # neither the labels nor the underlying data changed (SPEC §6.3) —
        # switching files keeps its labels ("RMSD (nm)") but changes data_key
        same_series = (self._view is not None and labels_now == self._view[0]
                       and st.data_key == self._view[1])
        prev_ax = self.fig.axes[0] if self.fig.axes else None
        prev_xlim = prev_ax.get_xlim() if same_series and prev_ax else None
        prev_ylim = prev_ax.get_ylim() if same_series and prev_ax else None

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if st.logx:
            ax.set_xscale("log")
        if st.logy:
            ax.set_yscale("log")
        if st.grid:
            ax.grid(True, color=t.grid, lw=0.6, alpha=0.6)
        for e in st.entries:
            if isinstance(e, Band):
                sel = None
                if not full and len(e.x) > DECIMATE_POINTS:
                    sel = np.unique(np.concatenate([
                        analysis.decimate_minmax(e.x, np.asarray(e.hi, dtype=float)),
                        analysis.decimate_minmax(e.x, -np.asarray(e.lo, dtype=float))]))
                bx = e.x if sel is None else np.asarray(e.x)[sel]
                blo = e.lo if sel is None else np.asarray(e.lo)[sel]
                bhi = e.hi if sel is None else np.asarray(e.hi)[sel]
                ax.fill_between(bx, blo, bhi, color=e.color, alpha=0.25, lw=0)
                continue
            sel = None
            if not full and len(e.x) > DECIMATE_POINTS:
                # C23: min/max buckets keep spikes visible without million-point draws
                sel = analysis.decimate_minmax(e.x, e.y)
            x = e.x if sel is None else np.asarray(e.x)[sel]
            y = e.y if sel is None else np.asarray(e.y)[sel]
            dy = None if e.dy is None else (e.dy if sel is None else np.asarray(e.dy)[sel])
            dx = None if e.dx is None else (e.dx if sel is None else np.asarray(e.dx)[sel])
            if dx is not None or dy is not None:
                ax.errorbar(x, y, yerr=dy, xerr=dx, fmt=e.style, color=e.color,
                            lw=e.width, alpha=e.alpha, elinewidth=0.9, capsize=2,
                            label=e.label or None)
            else:
                ax.plot(x, y, e.style, color=e.color, lw=e.width, alpha=e.alpha,
                        label=e.label or None)
            if e.smooth is not None:
                sm = e.smooth if sel is None else np.asarray(e.smooth)[sel]
                ax.plot(x, sm, "--", color=e.color, lw=1.0, alpha=0.9)
        if st.title:
            ax.set_title(st.title)
        if st.xlabel:
            ax.set_xlabel(st.xlabel)
        if st.ylabel:
            ax.set_ylabel(st.ylabel)
        self._targets = []
        if st.legend != "off":
            labels = [h.get_label() for h in ax.get_legend_handles_labels()[0]]
            if labels:
                if st.legend == "outside right":  # C17: figure legend reserves space
                    handles = ax.get_legend_handles_labels()[0]
                    leg = self.fig.legend(handles=handles, loc="outside right upper",
                                          fontsize=9, framealpha=0.92,
                                          facecolor=t.panel, edgecolor=t.border,
                                          borderpad=0.6, labelspacing=0.35)
                else:
                    leg = ax.legend(loc=st.legend, fontsize=9, framealpha=0.92,
                                    facecolor=t.panel, edgecolor=t.border,
                                    borderpad=0.6, labelspacing=0.35)
                for proxy, text in zip(leg.get_lines(), leg.get_texts()):
                    proxy.set_label(text.get_text())  # pick handler matches on label
                    proxy.set_picker(True)
                    proxy.set_pickradius(6)
                self._targets = [h for h in ax.get_children()
                                 if h.get_label() in set(labels)]
        if prev_xlim is not None:
            ax.set_xlim(prev_xlim)
            ax.set_ylim(prev_ylim)
        if not st.entries:  # C12: say what the app reads while nothing is plotted
            ax.text(0.5, 0.5,
                    "Open a folder and click a GROMACS .xvg file to plot.\n"
                    "Reads .xvg analysis files (RMSD, energy, RDF …).\n"
                    "Trajectories (.xtc), maps (.xpm) and .edr files are not supported.",
                    transform=ax.transAxes, ha="center", va="center",
                    color=t.dim, fontsize=10)
        self._view = (labels_now, st.data_key, ax.get_xlim(), ax.get_ylim())
        self._last_state = st
        # C34: a textual summary of what is plotted, for screen readers
        labeled = [(e.label, e.y) for e in st.entries if getattr(e, "label", "")]
        self.canvas.setAccessibleName(st.title or "plot")
        self.canvas.setAccessibleDescription(
            analysis.series_summary(labeled) or "empty plot — no file selected")
        self.toolbar.push_current()  # re-seed nav history so Home works after a redraw
        self.canvas.draw_idle()

    def _on_motion(self, ev):
        if ev.inaxes is not None and ev.xdata is not None:
            self.coords.emit(f"x = {ev.xdata:.6g}   y = {ev.ydata:.6g}")

    def _on_button(self, ev):
        if ev.button != 3 or not self.fig.axes:
            return
        legs = ([a.get_legend() for a in self.fig.axes]
                + list(self.fig.legends))  # covers outside-right (figure) legends
        for leg in legs:
            if leg is None:
                continue
            for ln in leg.get_lines():
                if ln.contains(ev)[0]:
                    self.pin_requested.emit(ln.get_label())
                    return

    def _on_pick(self, ev):
        if ev.mouseevent.button != 1:  # left-click toggles visibility; right = pin
            return
        lbl = ev.artist.get_label()
        if not lbl:
            return
        for t in self._targets:
            if t.get_label() == lbl:
                vis = not t.get_visible()
                t.set_visible(vis)
                ev.artist.set_alpha(1.0 if vis else 0.2)
        self.canvas.draw_idle()
