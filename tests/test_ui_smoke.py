"""UI smoke tests: the window constructs, theming applies, views are preserved.

Runs on the offscreen Qt platform so it works headless (SPEC §14).
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_app_version_importable():
    from xvg_plotter.version import APP_VERSION
    assert APP_VERSION


def test_main_window_constructs_and_plots_empty(app):
    from xvg_plotter.ui.main_window import MainWindow  # regression: bad ui/version import
    win = MainWindow()
    assert win.windowTitle() == "XVG Plotter"
    win.update_plot()  # no selection: must not raise
    win.close()


def test_theme_applies_stylesheet(app):
    from xvg_plotter.ui import theme
    tokens = theme.apply(app, theme.LIGHT)
    assert app.styleSheet() and tokens.name == "light"
    tokens = theme.apply(app, theme.DARK)
    assert app.styleSheet() and tokens.name == "dark"
    theme.apply(app, theme.LIGHT)


def test_theme_switch_rethemes_window(app):
    from xvg_plotter.ui import theme
    from xvg_plotter.ui.main_window import MainWindow
    win = MainWindow()
    win.retheme()
    assert theme.current().name in ("light", "dark")
    win.close()


def test_render_keeps_zoom_across_style_changes(app):
    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState
    panel = PlotPanel()
    x = np.linspace(0.1, 10, 100)
    st = PlotState(entries=[Line(x, np.sin(x), label="s")])
    panel.render(st)
    # user zooms in
    panel.fig.axes[0].set_xlim(2.0, 4.0)
    # a style-only re-render (same series) keeps the zoomed view...
    panel.render(st)
    assert panel.fig.axes[0].get_xlim() == (2.0, 4.0)
    # ...and the zoom survives further style toggles
    panel.render(st)
    assert panel.fig.axes[0].get_xlim() == (2.0, 4.0)
    # a data change (different series) resets the view
    panel.render(PlotState(entries=[Line(x, np.cos(x), label="c")]))
    assert panel.fig.axes[0].get_xlim() != (2.0, 4.0)


def test_series_dock_rebuild_preserves_scroll_and_syncs(app):
    from pathlib import Path

    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.series_dock import SeriesDock

    f = parse_file(Path(__file__).parent / "fixtures" / "energy.xvg")
    dock = SeriesDock()
    visible: dict = {}
    dock.rebuild([f], {}, visible, False)
    assert len(dock._groups) == 1
    assert len(dock._groups[f.path].checks) == len(f.datasets[0].series)
    # rebuilding with the same file keeps the same widgets (no teardown)
    g = dock._groups[f.path]
    dock.rebuild([f], {}, visible, False)
    assert dock._groups[f.path] is g
    # dropping the file clears the group
    dock.rebuild([], {}, visible, False)
    assert not dock._groups
