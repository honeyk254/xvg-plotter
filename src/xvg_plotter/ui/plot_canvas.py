"""Plot canvas + toolbar + legend toggling (SPEC §6.3)."""
from __future__ import annotations

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
from .theme import Tokens, current


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
        self._targets: list = []
        self._last_state = PlotState()
        self._view: tuple[frozenset[str], tuple[float, float], tuple[float, float]] | None = None
        self.apply_theme(current())

    def apply_theme(self, t: Tokens) -> None:
        self._tokens = t
        mpl.rcParams.update({
            "font.size": 9,
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

    def render(self, st: PlotState) -> None:
        t = self._tokens
        labels_now = frozenset(e.label for e in st.entries if getattr(e, "label", ""))
        # carry the current (possibly user-zoomed) view across the redraw when
        # the plotted series set is unchanged (SPEC §6.3)
        same_series = self._view is not None and labels_now == self._view[0]
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
                ax.fill_between(e.x, e.lo, e.hi, color=e.color, alpha=0.25, lw=0)
                continue
            if e.dx is not None or e.dy is not None:
                ax.errorbar(e.x, e.y, yerr=e.dy, xerr=e.dx, fmt=e.style, color=e.color,
                            lw=e.width, alpha=e.alpha, elinewidth=0.9, capsize=2,
                            label=e.label or None)
            else:
                ax.plot(e.x, e.y, e.style, color=e.color, lw=e.width, alpha=e.alpha,
                        label=e.label or None)
            if e.smooth is not None:
                ax.plot(e.x, e.smooth, "--", color=e.color, lw=1.0, alpha=0.9)
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
        self._view = (labels_now, ax.get_xlim(), ax.get_ylim())
        self._last_state = st
        self.toolbar.push_current()  # re-seed nav history so Home works after a redraw
        self.canvas.draw_idle()

    def _on_motion(self, ev):
        if ev.inaxes is not None and ev.xdata is not None:
            self.coords.emit(f"x = {ev.xdata:.6g}   y = {ev.ydata:.6g}")

    def _on_pick(self, ev):
        lbl = ev.artist.get_label()
        if not lbl:
            return
        for t in self._targets:
            if t.get_label() == lbl:
                vis = not t.get_visible()
                t.set_visible(vis)
                ev.artist.set_alpha(1.0 if vis else 0.2)
        self.canvas.draw_idle()
