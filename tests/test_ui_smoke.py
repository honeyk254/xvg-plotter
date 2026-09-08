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


# -- v1.0.1 remediation tests (REMEDIATION_PLAN.md Phase 0/1) -----------------


def _wait_for_scan(win, timeout_ms: int = 10000) -> None:
    import time

    waited = 0.0
    while (win._scanner is not None and win._scanner.isRunning()
           and waited < timeout_ms / 1000):
        time.sleep(0.05)
        waited += 0.05
    QApplication.processEvents()


def _help_texts(win) -> list[str]:
    help_menu = next(a.menu() for a in win.menuBar().actions()
                     if a.text() == "&Help")
    return [act.text() for act in help_menu.actions() if act.text()]


def test_c02_update_action_exists(app):
    from xvg_plotter.ui.main_window import MainWindow

    win = MainWindow()
    texts = _help_texts(win)
    assert "Check for updates…" in texts
    win.close()


def test_c06_association_action_on_windows(app):
    import sys as _sys

    from xvg_plotter.ui.main_window import MainWindow

    win = MainWindow()
    texts = _help_texts(win)
    if _sys.platform == "win32":
        assert "Set as default .xvg viewer" in texts
    else:
        assert "Set as default .xvg viewer" not in texts
    win.close()


def test_c10_directives_surfaced_in_tooltip(app, tmp_path):
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.file_table import FileTable

    f = tmp_path / "styled.xvg"
    f.write_text('@ title "t"\n@ with g0\n@ s0 color 2\n0 1\n1 2\n',
                 encoding="utf-8")
    table = FileTable()
    table.add_file(parse_file(f))
    tip = table.item(0, 1).toolTip()
    assert "grace directive(s) ignored" in tip


def test_c13_dropped_files_checked_and_plotted(app, tmp_path):
    from xvg_plotter.ui.main_window import MainWindow

    f1 = tmp_path / "a.xvg"
    f2 = tmp_path / "b.xvg"
    for i, p in enumerate((f1, f2)):
        p.write_text(f"x y\n0 {i}\n1 {i + 1}\n", encoding="utf-8")
    win = MainWindow()
    try:
        win._handle_dropped_paths([f1, f2])
        _wait_for_scan(win)
        checked = [f.path for f in win.table.ordered_checked()]
        assert f1.resolve() in checked and f2.resolve() in checked
        assert win.active == f1.resolve()
        # C26: the status bar carries the live min/max/mean summary
        assert "file(s) plotted" in win._info.text()
        assert "mean" in win._info.text()
    finally:
        win.close()


def test_c14_recents_pruned_and_pinned(app, tmp_path):
    from xvg_plotter import settings

    old_rec, old_pin = settings.recents(), settings.pinned()
    settings.set_("recents", [])
    settings.set_("pinned", [])
    try:
        d1, d2 = tmp_path / "a", tmp_path / "b"
        d1.mkdir()
        d2.mkdir()
        settings.add_recent(str(d2))
        settings.add_recent(str(d1))
        assert settings.recents()[0] == str(d1)
        settings.set_("recents", [str(tmp_path / "gone")] + settings.recents())
        items = settings.recent_items()
        assert str(tmp_path / "gone") not in items
        assert str(d1) in items
        assert settings.toggle_pinned(str(d2)) is True
        assert settings.recent_items()[0] == str(d2)
        assert settings.toggle_pinned(str(d2)) is False
    finally:
        settings.set_("recents", old_rec)
        settings.set_("pinned", old_pin)


def test_c25_unit_guard_and_dx_scaling(app, tmp_path):
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    time_f = tmp_path / "t.xvg"
    time_f.write_text('@ title "t"\n@ xaxis label "Time (ps)"\n'
                      '@ s0 type xydx\n0 1 0.5\n1000 2 1.0\n', encoding="utf-8")
    frame_f = tmp_path / "f.xvg"
    frame_f.write_text('@ title "f"\n@ xaxis label "Frame"\n'
                       '@ s0 type xydx\n0 1 0.5\n1000 2 1.0\n', encoding="utf-8")
    win = MainWindow()
    try:
        ft = parse_file(time_f)
        win.files[ft.path] = ft
        win.active = ft.path
        st = win._compose_state([ft])
        assert win._unit([ft], "auto") == "ns"  # 1000 ps -> ns
        assert st.xlabel == "Time (ns)"
        # xydx rows are "x dx y": dx = [1.0, 2.0] ps -> [0.001, 0.002] ns
        assert st.entries[0].dx == pytest.approx([0.001, 0.002])

        ff = parse_file(frame_f)
        win.files[ff.path] = ff
        win.active = ff.path
        st2 = win._compose_state([ff])
        assert win._unit([ff], "auto") == "ps"  # guard: not a time axis
        assert st2.xlabel == "Frame"  # no "(unit)" appended
        assert st2.entries[0].dx == pytest.approx([1.0, 2.0])  # unchanged (ps factor)

        # an explicit unit choice is still honored on a non-time axis
        win.style.cmb_unit.setCurrentText("ns")
        st3 = win._compose_state([ff])
        assert st3.entries[0].x == pytest.approx([0.0, 1.0])
        assert st3.entries[0].dx == pytest.approx([0.001, 0.002])
        win.style.cmb_unit.setCurrentText("auto")
    finally:
        win.close()


def test_c27_common_range_option(app):
    from xvg_plotter.ui.series_dock import SeriesDock

    dock = SeriesDock()
    assert dock.analysis_state().common_range is False
    dock.chk_average.setChecked(True)
    assert dock.chk_common.isEnabled()
    dock.chk_common.setChecked(True)
    assert dock.analysis_state().common_range is True
    dock.chk_average.setChecked(False)
    assert not dock.chk_common.isEnabled()


def test_c28_time_hint_label(app):
    from xvg_plotter.ui.series_dock import SeriesDock

    dock = SeriesDock()
    dock.set_time_hint("≈ 2.1 ns")
    assert dock.lbl_time.text() == "≈ 2.1 ns"
    dock.set_time_hint("")
    assert dock.lbl_time.text() == ""


def test_c31_clipboard_at_export_dpi(app):
    import numpy as np

    from xvg_plotter.export import copy_image
    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0.1, 10, 100)
    panel.render(PlotState(entries=[Line(x, np.sin(x), label="s")]))
    img = copy_image(panel.canvas, dpi=300)
    # widget grab would be ~600 px wide at 100% scaling; a 300-dpi render is much wider
    assert img.width() > 1200


def test_c32_tiff_format_and_eps_transparent_rule(app, tmp_path):
    import numpy as np

    from xvg_plotter.export import save_figure
    from xvg_plotter.ui.export_dialog import FORMATS, ExportDialog
    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    assert "tif" in FORMATS
    panel = PlotPanel()
    x = np.linspace(0.1, 10, 50)
    panel.render(PlotState(entries=[Line(x, np.sin(x), label="s")]))
    out = tmp_path / "o.tif"
    save_figure(panel.fig, out, dpi=120)
    assert out.exists() and out.stat().st_size > 0

    dlg_tif = ExportDialog("o", str(tmp_path), fmt="tif")
    assert dlg_tif.spin_dpi.isEnabled()
    dlg_eps = ExportDialog("o", str(tmp_path), fmt="eps", transparent=True)
    assert not dlg_eps.spin_dpi.isEnabled()
    assert not dlg_eps.chk_transparent.isEnabled()
    assert dlg_eps.options()["transparent"] is False  # forced off for EPS


def test_c34_accessible_summary(app):
    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0.1, 10, 100)
    panel.render(PlotState(title="RMSD", entries=[Line(x, np.sin(x), label="s")]))
    assert panel.canvas.accessibleName() == "RMSD"
    assert "mean" in panel.canvas.accessibleDescription()
    panel.render(PlotState())
    assert "empty plot" in panel.canvas.accessibleDescription()


def test_c12_empty_state_names_supported_formats(app):
    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0.1, 10, 10)
    panel.render(PlotState(entries=[Line(x, np.sin(x), label="s")]))
    assert not panel.fig.axes[0].texts  # hint only when nothing is plotted
    panel.render(PlotState())
    texts = " ".join(t.get_text() for t in panel.fig.axes[0].texts)
    assert "not supported" in texts and ".xvg" in texts


def _cjk_font_available() -> bool:
    from matplotlib.font_manager import FontProperties, findfont

    for fam in ("Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC",
                "Malgun Gothic", "SimHei", "WenQuanYi Zen Hei"):
        try:
            path = findfont(FontProperties(family=fam), fallback_to_default=False)
            if path and "last resort" not in path.lower():
                return True
        except Exception:
            continue
    return False


@pytest.mark.skipif(not _cjk_font_available(), reason="no CJK font on this system")
def test_c36_cjk_titles_render_without_missing_glyphs(app):
    import warnings as _warnings

    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0.1, 10, 20)
    st = PlotState(title="均方根位移 µ ± Å", xlabel="时间 (ns)", ylabel="Å",
                   entries=[Line(x, np.sin(x), label="ε")])
    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        panel.render(st)
    missing = [w for w in caught if "missing from font" in str(w.message)]
    assert not missing


def test_c39_logging_setup(app):
    import logging
    import sys as _sys

    from xvg_plotter import app as appmod

    # match the real app's identity so AppDataLocation resolves like production
    app.setApplicationName("XVG Plotter")
    app.setOrganizationName("XVGPlotter")
    p = appmod.setup_logging()
    assert p is not None and p.name == "xvg_plotter.log"
    assert _sys.excepthook is not _sys.__excepthook__  # crash dialog installed
    logging.getLogger("xvg_plotter.test").info("smoke log line")
    assert p.exists()


def test_c40_settings_export_import_roundtrip(app, tmp_path):
    from xvg_plotter import settings

    old = settings.get("export/dpi")
    settings.set_("export/dpi", 311)
    try:
        ini = tmp_path / "s.ini"
        n = settings.export_settings(str(ini))
        assert n > 0 and ini.exists()
        settings.set_("export/dpi", 42)
        settings.import_settings(str(ini))
        assert int(str(settings.get("export/dpi"))) == 311
    finally:
        settings.set_("export/dpi", old)


def test_c03_and_c05_packaging_guards():
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "xvg_build", root / "packaging" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.VERSION == "1.0.1"  # single-sourced from version.py
    iss = (root / "packaging" / "windows" / "setup.iss").read_text(encoding="utf-8")
    assert "#ifdef ONEDIR" in iss and "#ifdef MACHINE" in iss
    assert "/DONEDIR" in (root / "packaging" / "build.py").read_text(encoding="utf-8")


def test_c07_checksums(tmp_path):
    import hashlib
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "xvg_build", root / "packaging" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    f = tmp_path / "artifact.exe"
    f.write_bytes(b"payload")
    mod._checksums([f, tmp_path / "missing.exe"], tmp_path)
    lines = (tmp_path / "SHA256SUMS.txt").read_text(encoding="utf-8").strip().splitlines()
    expected = hashlib.sha256(b"payload").hexdigest()
    assert lines == [f"{expected}  artifact.exe"]

    empty = tmp_path / "none.txt"
    mod._checksums([tmp_path / "missing.exe"], empty.parent)
    assert not (tmp_path / "SHA256SUMS.txt").exists() or \
        "none.txt" not in (tmp_path / "SHA256SUMS.txt").read_text(encoding="utf-8")


def test_plot_stays_light_in_dark_mode(app):
    from xvg_plotter.ui import theme
    from xvg_plotter.ui.plot_canvas import PlotPanel
    panel = PlotPanel()
    panel.apply_theme(theme.DARK)
    r, g, b, _ = panel.fig.get_facecolor()
    assert (r, g, b) == (1.0, 1.0, 1.0)  # canvas stays publication-white
