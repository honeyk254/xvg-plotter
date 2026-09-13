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


def test_render_rescales_when_data_key_changes_despite_same_labels(app):
    """Regression: switching files kept the first file's axes (labels collide)."""
    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0.0, 250.0, 100)
    st_a = PlotState(entries=[Line(x, np.sin(x), label="RMSD (nm)")],
                     data_key=(("a", 0, (0,)),))
    panel.render(st_a)
    panel.fig.axes[0].set_xlim(2.0, 4.0)
    panel.fig.axes[0].set_ylim(0.0, 0.9)
    # same label, different file (data_key): axes must rescale to the new data
    st_b = PlotState(entries=[Line(x * 0.1, np.cos(x) * 2, label="RMSD (nm)")],
                     data_key=(("b", 0, (0,)),))
    panel.render(st_b)
    assert panel.fig.axes[0].get_xlim() != (2.0, 4.0)
    assert panel.fig.axes[0].get_ylim() != (0.0, 0.9)
    # same file again (same data_key): zoom is still preserved
    panel.fig.axes[0].set_xlim(1.0, 2.0)
    panel.render(st_b)
    assert panel.fig.axes[0].get_xlim() == (1.0, 2.0)


def test_style_tab_replaces_dock(app):
    from xvg_plotter.ui.main_window import MainWindow

    win = MainWindow()
    try:
        # the right-side Style dock is gone; a collapsible tab drives the panel
        assert [d.objectName() for d in win._docks] == ["files", "series"]
        assert not win.style.isVisibleTo(win)
        win._style_tab.setChecked(True)
        assert win.style.isVisibleTo(win)
        win._style_tab.setChecked(False)
        assert not win.style.isVisibleTo(win)
    finally:
        win.close()


def test_pin_survives_switching_files(app, tmp_path):
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    f1 = tmp_path / "one.xvg"
    f2 = tmp_path / "two.xvg"
    for p, v in ((f1, 1.0), (f2, 50.0)):
        p.write_text(f"@ title \"t\"\n@ yaxis label \"RMSD (nm)\"\n0 0\n1 {v}\n",
                     encoding="utf-8")
    win = MainWindow()
    try:
        fa = parse_file(f1)
        fb = parse_file(f2)
        win.files[fa.path] = fa
        win.files[fb.path] = fb

        win.active = fa.path
        win._entries = win._compose_state([fa]).entries
        win._toggle_pin("RMSD (nm)")  # pinned under its file-qualified label
        assert len(win.pins) == 1
        pin_label = next(iter(win.pins))
        assert pin_label.startswith("one")

        # switch to the other file: the pin must still be plotted
        win.active = fb.path
        st = win._compose_state([fb])
        labels = [e.label for e in st.entries]
        assert pin_label in labels
        assert len(labels) == 2  # pin + newly plotted file
        # a folder refresh re-parses the file and the pin follows the new data
        f1.write_text('@ title "t"\n@ yaxis label "RMSD (nm)"\n0 0\n1 9\n',
                      encoding="utf-8")
        win._on_file(parse_file(f1))
        st = win._compose_state([fb])
        pin_entry = next(e for e in st.entries if e.label == pin_label)
        assert pin_entry.y == pytest.approx([0.0, 9.0])
        # pins follow the current line style instead of freezing pin-time style
        win.style.spin_width.setValue(2.5)
        st = win._compose_state([fb])
        pin_entry = next(e for e in st.entries if e.label == pin_label)
        assert pin_entry.width == 2.5
        win.style.spin_width.setValue(1.5)
        # unpin and it disappears
        win._toggle_pin(pin_label)
        st2 = win._compose_state([fb])
        assert [e.label for e in st2.entries] == ["RMSD (nm)"]
    finally:
        win.close()


def test_two_panes_overlay_folders(app, tmp_path):
    from xvg_plotter.ui.main_window import MainWindow

    d1, d2 = tmp_path / "p1", tmp_path / "p2"
    d1.mkdir()
    d2.mkdir()
    f1 = d1 / "rmsd_a.xvg"
    f2 = d2 / "rmsd_b.xvg"
    f1.write_text("@ title \"A\"\n@ yaxis label \"RMSD (nm)\"\n0 0\n1 1\n",
                  encoding="utf-8")
    f2.write_text("@ title \"B\"\n@ yaxis label \"RMSD (nm)\"\n0 0\n1 2\n",
                  encoding="utf-8")
    win = MainWindow()
    try:
        win.load_folder(d1, 0)
        win.load_folder(d2, 1)
        _wait_for_scan(win)
        win.table.sync_check(f1.resolve(), True)
        win.table2.sync_check(f2.resolve(), True)
        win._on_overlay(win.files[f1.resolve()], True)
        ts = win._targets()
        assert [f.path for f in ts] == [f1.resolve(), f2.resolve()]
        st = win._compose_state(ts)
        labels = [e.label for e in st.entries]
        assert labels == ["rmsd_a: RMSD (nm)", "rmsd_b: RMSD (nm)"]
        # activating a file in pane 1 is still "solo": pane 2's checks clear
        win._on_activate(win.files[f2.resolve()])
        assert [f.path for f in win._targets()] == [f2.resolve()]
        assert not win.table.ordered_checked()
    finally:
        win.close()


def test_series_dock_rebuild_preserves_scroll_and_syncs(app):
    from pathlib import Path

    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.series_dock import SeriesDock

    f = parse_file(Path(__file__).parent / "fixtures" / "energy.xvg")
    dock = SeriesDock()
    visible: dict = {}
    dock.rebuild([f], {}, visible, False)
    assert len(dock._groups) == 1
    checks = dock._groups[f.path].checks
    assert sum(len(cbs) for cbs in checks.values()) == len(f.datasets[0].series)
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
    while (any(s is not None and s.isRunning() for s in win._scanners)
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

    old = settings.get("export/dpi") or 300
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
    assert mod.VERSION == "1.3.0"  # single-sourced from version.py
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


# -- v1.2.0 remediation tests (REMEDIATION_PLAN.md Phase 2) -------------------


def test_c08_recursive_scan(app, tmp_path):
    from xvg_plotter.ui.main_window import MainWindow

    (tmp_path / "top.xvg").write_text("@ title \"top\"\n0 0\n1 1\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.xvg").write_text("@ title \"deep\"\n0 0\n1 2\n", encoding="utf-8")
    (sub / ".hidden").mkdir()
    (sub / ".hidden" / "hid.xvg").write_text("0 0\n1 1\n", encoding="utf-8")
    win = MainWindow()
    try:
        win._bars[0].chk_sub.setChecked(True)  # fires recursive_toggled → saved
        win.load_folder(tmp_path, 0)
        _wait_for_scan(win)
        names = [win._tables[0].item(r, 1).text()
                 for r in range(win._tables[0].rowCount())]
        assert "top.xvg" in names and "deep.xvg" in names
        assert not any(".hidden" in n for n in names)  # hidden dirs skipped
        win._bars[0].chk_sub.setChecked(False)  # rescan without subfolders
        _wait_for_scan(win)
        names = [win._tables[0].item(r, 1).text()
                 for r in range(win._tables[0].rowCount())]
        assert "top.xvg" in names and "deep.xvg" not in names
    finally:
        win.close()


def test_c09_cloud_placeholder_listed_without_reading(app, tmp_path, monkeypatch):
    import xvg_plotter.ui.file_table as ft

    f = tmp_path / "cloud.xvg"
    f.write_text("0 0\n1 1\n", encoding="utf-8")
    assert not ft.is_cloud_placeholder(f)  # a real local file is not a placeholder

    stub = ft.placeholder_file(f)
    assert "cloud-only" in stub.warnings[0] and not stub.datasets

    # scanner lists the placeholder without ever parsing the file
    calls = []
    monkeypatch.setattr(ft, "is_cloud_placeholder", lambda p: True)
    monkeypatch.setattr(ft, "parse_file",
                        lambda p: calls.append(p) or (_ for _ in ()).throw(
                            AssertionError("parse_file must not be called")))
    from xvg_plotter.ui.file_table import FolderScanner

    sc = FolderScanner(tmp_path)
    seen = []
    sc.file_parsed.connect(seen.append)
    sc.start()
    import time as _time
    deadline = _time.time() + 5
    while sc.isRunning() and _time.time() < deadline:
        QApplication.processEvents()
        _time.sleep(0.01)
    for _ in range(50):  # queued cross-thread signals can land a tick later
        QApplication.processEvents()
        if len(seen) == 1:
            break
        _time.sleep(0.01)
    assert len(seen) == 1 and "cloud-only" in seen[0].warnings[0]
    assert calls == []


def test_c16_figure_size_and_font_controls(app, tmp_path):
    from PySide6.QtGui import QImage

    from xvg_plotter import settings as s
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    out = tmp_path / "out"
    out.mkdir()
    f = tmp_path / "a.xvg"
    f.write_text('@ title "t"\n@ yaxis label "E (kJ)"\n0 0\n1 1\n', encoding="utf-8")
    fa = parse_file(f)
    # clean slate: the style dock reads these at construction
    old = (s.get("view/fig_w"), s.get("view/fig_h"), s.get("view/font"))
    s.set_("view/fig_w", 0.0)
    s.set_("view/fig_h", 0.0)
    s.set_("view/font", "Match UI")
    win = MainWindow()
    try:
        win.files[fa.path] = fa
        win._tables[0].add_file(fa)
        win.table.sync_check(fa.path, True)
        win.style.spin_figw.setValue(8.0)
        win.style.spin_figh.setValue(5.0)
        win.style.cmb_font.setCurrentText("Arial")
        assert win.panel._font_family == "Arial"
        win._ask_directory = lambda *a, **k: str(out)
        win._export_batch()
        # exact publication size: 8x5 in at 300 dpi, no tight cropping
        img = QImage(str(out / "t.png"))
        assert img.width() == 2400 and img.height() == 1500
        assert float(str(s.get("view/fig_w"))) == pytest.approx(8.0)
        assert str(s.get("view/font")) == "Arial"
    finally:
        s.set_("view/fig_w", old[0])
        s.set_("view/fig_h", old[1])
        s.set_("view/font", old[2])
        win.close()


def test_c17_series_color_override_and_reset(app, tmp_path):
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow
    from xvg_plotter.ui.options import PALETTES

    f = tmp_path / "a.xvg"
    f.write_text('@ title "t"\n@ yaxis label "E"\n0 0\n1 1\n', encoding="utf-8")
    win = MainWindow()
    try:
        fa = parse_file(f)
        win.files[fa.path] = fa
        win.active = fa.path
        win._refresh_series_dock()
        default = win._compose_state([fa]).entries[0].color
        win._on_series_color(fa, 0, 0, "#ff0000")
        st = win._compose_state([fa])
        assert st.entries[0].color == "#ff0000"
        win._refresh_series_dock()
        swatch = win.series._groups[fa.path].swatches[(0, 0)]
        assert "#ff0000" in swatch.styleSheet()
        win._on_series_color(fa, 0, 0, None)  # reset → back to the cycle
        assert win._compose_state([fa]).entries[0].color == default
    finally:
        win.close()

    okabe = next(iter(PALETTES))  # first palette = the default
    assert "colorblind" in okabe.lower()


def test_c17_outside_right_legend(app):
    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0.1, 10, 100)
    panel.render(PlotState(legend="outside right",
                           entries=[Line(x, np.sin(x), label="s")]))
    # an outside legend is a figure legend (constrained layout reserves its space)
    assert panel.fig.legends or panel.fig.axes[0].get_legend()


def test_c23_decimated_interactive_and_full_export(app):
    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0.1, 10, 50000)
    st = PlotState(entries=[Line(x, np.sin(20 * x) + 0.01 * np.sin(2000 * x),
                                 label="s")])
    panel.render(st)  # interactive: decimated
    plotted = len(panel.fig.axes[0].lines[0].get_xdata())
    assert plotted < 50000 and plotted >= 20000
    panel.render(st, full=True)  # exports: every point
    assert len(panel.fig.axes[0].lines[0].get_xdata()) == 50000


def test_c29_batch_export(app, tmp_path, monkeypatch):
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    out = tmp_path / "out"
    out.mkdir()
    files = []
    for i in (1, 2):
        p = tmp_path / f"plot{i}.xvg"
        p.write_text(f"@ title \"p{i}\"\n0 0\n1 {i}\n", encoding="utf-8")
        files.append(parse_file(p))
    win = MainWindow()
    try:
        for fa in files:
            win.files[fa.path] = fa
            win._tables[0].add_file(fa)
            win.table.sync_check(fa.path, True)
        win._ask_directory = lambda *a, **k: str(out)
        monkeypatch.setattr("xvg_plotter.settings.get",
                            lambda k, d=None: "png" if k == "export/fmt" else d)
        win._export_batch()
        names = sorted(p.name for p in out.iterdir())
        assert names == ["p1.png", "p2.png"]  # named after the plot title
    finally:
        win.close()


def test_c30_csv_data_export(app, tmp_path):
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    out = tmp_path / "data.csv"
    f = tmp_path / "rg.xvg"
    f.write_text('@ title "Rg"\n@ yaxis label "Rg (nm)"\n'
                 '@ s0 type xydy\n0 1 0.1\n1000 2 0.2\n', encoding="utf-8")
    fa = parse_file(f)
    win = MainWindow()
    try:
        win.files[fa.path] = fa
        win.active = fa.path
        win._ask_save_path = lambda *a, **k: str(out)
        win._export_data()
        text = out.read_text(encoding="utf-8")
        assert "# file: rg.xvg" in text and "Rg (nm)" in text
        assert "Rg (nm) ±" in text  # error column included
        assert "# x unit: ns" in text  # auto unit conversion honored
        assert text.strip().splitlines()[-1] == "1,2,0.2"  # x = 1000 ps -> 1 ns
    finally:
        win.close()


def test_c33_print_to_pdf(app, tmp_path):
    from PySide6.QtPrintSupport import QPrinter

    from xvg_plotter.ui.main_window import MainWindow

    out = tmp_path / "plot.pdf"
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(out))
    win = MainWindow()
    try:
        win._print_plot(printer)  # empty plot: must not raise
    finally:
        win.close()
    assert out.exists() and out.stat().st_size > 0


def test_c19_shortcuts_and_help_dialogs(app):
    from xvg_plotter.ui.help_dialogs import GlossaryDialog, KeyboardDialog
    from xvg_plotter.ui.main_window import MainWindow

    win = MainWindow()
    try:
        seqs = {a.shortcut().toString() for a in win.actions() if not a.shortcut().isEmpty()}
        assert {"Ctrl+F", "Ctrl+1", "Ctrl+2", "Ctrl+3", "Ctrl+R"} <= seqs
        assert "Keyboard shortcuts…" in _help_texts(win)
        assert "Reading the analyses…" in _help_texts(win)
        kbd = KeyboardDialog(win)
        assert kbd._body.rowCount() >= 10
        gloss = GlossaryDialog(win)
        assert "RMSD" in gloss._body.toPlainText()
    finally:
        win.close()


def test_c20_focus_mode_hides_and_restores(app):
    from xvg_plotter.ui.main_window import MainWindow

    win = MainWindow()
    try:
        for d in win._docks:
            d.setVisible(True)
        win._style_tab.setChecked(True)
        win._focus_action.setChecked(True)
        assert all(d.isHidden() for d in win._docks)
        assert not win._style_tab.isChecked()
        win._focus_action.setChecked(False)
        assert not any(d.isHidden() for d in win._docks)
        assert win._style_tab.isChecked()  # restored to the pre-focus state
        win._style_tab.setChecked(False)
    finally:
        win.close()


def test_c22_open_folder_in_new_window(app, tmp_path):
    from xvg_plotter.ui import main_window as mw
    from xvg_plotter.ui.main_window import MainWindow

    d = tmp_path / "win2"
    d.mkdir()
    (d / "b.xvg").write_text("@ title \"b\"\n0 0\n1 1\n", encoding="utf-8")
    win = MainWindow()
    before = len(mw._WINDOWS)
    try:
        win._ask_directory = lambda *a, **k: str(d)
        win._new_window()
        assert len(mw._WINDOWS) == before + 1
        second = mw._WINDOWS[-1]
        assert second is not win and not second._primary_window
        _wait_for_scan(second)
        assert second._folders[0] == d.resolve()
        second.close()
        win.close()
    finally:
        mw._WINDOWS.clear()


def test_c37_first_run_and_glossary(app):
    from xvg_plotter.ui.first_run import FirstRunDialog
    from xvg_plotter.ui.help_dialogs import GlossaryDialog

    intro = FirstRunDialog()
    assert "Welcome" in intro.windowTitle()
    gloss = GlossaryDialog()
    plain = gloss._body.toPlainText()
    for term in ("RMSD", "Rg (gyrate)", "replica", "pin"):
        assert term in plain


# -- v1.3.0 remediation tests (REMEDIATION_PLAN.md Phase 2 leftover / 3 / 4) ----


def test_c24_derived_quantities_compose(app, tmp_path):
    import numpy as np

    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    f = tmp_path / "lin.xvg"
    f.write_text("0 2\n1 4\n2 6\n3 8\n", encoding="utf-8")  # y = 2x + 2
    fa = parse_file(f)
    win = MainWindow()
    try:
        win.files[fa.path] = fa
        win.active = fa.path
        st = win._compose_state([fa])
        assert st.entries[0].y == pytest.approx([2, 4, 6, 8])
        # baseline subtraction shifts to zero
        win.series.chk_baseline.setChecked(True)
        st = win._compose_state([fa])
        assert st.entries[0].y == pytest.approx([0, 2, 4, 6])
        # baseline+max normalize: divide by the max of the shifted curve
        win.series.cmb_norm.setCurrentIndex(2)  # max
        st = win._compose_state([fa])
        assert st.entries[0].y == pytest.approx([0.0, 1 / 3, 2 / 3, 1.0])
        # normalize by first value without baseline (a shifted curve's first
        # value is 0, so normalize-by-first alone is intentionally a no-op)
        win.series.chk_baseline.setChecked(False)
        win.series.cmb_norm.setCurrentIndex(1)  # first value
        st = win._compose_state([fa])
        assert st.entries[0].y == pytest.approx([1.0, 2.0, 3.0, 4.0])
        # off again, then the least-squares fit overlay
        win.series.cmb_norm.setCurrentIndex(0)
        win.series.chk_fit.setChecked(True)
        st = win._compose_state([fa])
        assert len(st.entries) == 2
        fit = st.entries[1]
        assert fit.style == "--"
        assert fit.label.startswith("fit: y = 2·x + 2")
        assert fit.y == pytest.approx(2 * fit.x + 2)
        # the fit is limited to the visible X range
        win.update_plot()
        win.panel.fig.axes[0].set_xlim(1.0, 2.0)
        st = win._compose_state([fa])
        fit = st.entries[1]
        assert fit.x.min() >= 1.0 and fit.x.max() <= 2.0
    finally:
        win.close()


def test_c15_annotation_dialog_wiring(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QInputDialog

    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    f = tmp_path / "a.xvg"
    f.write_text('@ title "t"\n0 0\n1 1\n', encoding="utf-8")
    fa = parse_file(f)
    win = MainWindow()
    try:
        win.files[fa.path] = fa
        win.active = fa.path
        monkeypatch.setattr(QInputDialog, "getText",
                            staticmethod(lambda *a, **k: ("plateau", True)))
        win.panel.annotation_requested.emit(0.5, 0.25)
        assert win._annotations == [(0.5, 0.25, "plateau")]
        assert win._ann_clear_action.isEnabled()
        win.update_plot()
        texts = [t.get_text() for t in win.panel.fig.axes[0].texts]
        assert "plateau" in texts
        # the compose pipeline carries annotations into exports/prints
        st = win._compose_state([fa])
        assert st.annotations == [(0.5, 0.25, "plateau")]
        win._clear_annotations()
        assert win._compose_state([fa]).annotations == []
        assert not win._ann_clear_action.isEnabled()
    finally:
        win.close()


def test_c15_canvas_annotation_render_and_drag_sync(app):
    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0, 10, 50)
    st = PlotState(entries=[Line(x, x, label="s")],
                   annotations=[(2.0, 3.0, "note")])
    panel.render(st)
    assert len(panel._ann_artists) == 1
    artist = panel._ann_artists[0]
    assert artist.get_text() == "note"
    assert artist.get_position() == (2.0, 3.0)
    # a click in annotate mode emits the placement signal
    seen = []
    panel.annotation_requested.connect(lambda px, py: seen.append((px, py)))
    panel.annotate_mode = True
    ax = panel.fig.axes[0]

    class _Ev:
        button = 1
        inaxes = ax
        xdata = 1.5
        ydata = 2.5

    panel._on_button(_Ev())
    assert seen == [(1.5, 2.5)]
    # dragging the label and releasing syncs the new position into the state
    artist.set_position((4.0, 5.0))
    panel._on_release(None)
    assert panel._last_state.annotations == [(4.0, 5.0, "note")]
    # a plain re-render keeps the (moved) annotation
    panel.render(panel._last_state)
    assert panel._ann_artists[0].get_position() == (4.0, 5.0)


def test_c18_grid_view_toggle_and_cap(app, tmp_path):
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    def make(i):
        p = tmp_path / f"rep{i}.xvg"
        p.write_text(f'@ title "rep{i}"\n0 0\n1 {i}\n', encoding="utf-8")
        fa = parse_file(p)
        win.files[fa.path] = fa
        win._tables[0].add_file(fa)
        win.table.sync_check(fa.path, True)
        return fa

    win = MainWindow()
    try:
        for i in range(1, 7):
            make(i)
        win._grid_action.setChecked(True)  # toggles grid mode + replots
        assert win._grid_mode
        st = win._compose_state(win._targets())
        assert len(st.grid_states) == 6
        win.update_plot()
        assert len(win.panel.fig.axes) == 6
        assert win.panel.fig.axes[0].get_title() == "rep1"
        # single-series cells don't get legends; each cell plots its own data
        assert len(win.panel.fig.axes[0].lines) == 1
        # back to the overlay view
        win._grid_action.setChecked(False)
        st = win._compose_state(win._targets())
        assert not st.grid_states and len(st.entries) == 6
        # the 24-panel cap: extra files are counted, not drawn
        for i in range(30):
            make(100 + i)
        win._grid_action.setChecked(True)
        st = win._compose_state(win._targets())
        assert len(st.grid_states) == 24
        assert win._grid_overflow == 12
        assert "cap" in win._info.text()
    finally:
        win.close()


def test_c18_grid_render_path_panel(app):
    import numpy as np

    from xvg_plotter.ui.plot_canvas import Line, PlotPanel, PlotState

    panel = PlotPanel()
    x = np.linspace(0, 1, 20)
    subs = []
    for i in (1, 2):
        cell1 = PlotState(entries=[Line(x, x * i, label=f"s{i}")])
        cell2 = PlotState(entries=[Line(x, x * i, label=f"s{i}"),
                                   Line(x, x * i + 1, label=f"t{i}")])
        subs.append((f"c{i}", cell1))
        subs.append((f"c{i}b", cell2))
    panel.render(PlotState(title="grid", grid_states=subs))
    assert len(panel.fig.axes) == 4
    assert panel.fig.axes[1].get_legend() is not None  # 2 series → cell legend
    assert panel.fig.axes[0].get_legend() is None
    panel.render(PlotState())  # back to the single view
    assert len(panel.fig.axes) == 1


def test_c11_all_datasets_listed_and_overlayable(app, tmp_path):
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    fa_file = tmp_path / "multidataset.xvg"
    fa_file.write_text('@ title "Multi"\n@ s0 legend "A"\n0 1\n1 2\n&\n'
                       '@ s0 legend "B"\n0 5\n1 6\n2 7\n', encoding="utf-8")
    fa = parse_file(fa_file)
    win = MainWindow()
    try:
        win.files[fa.path] = fa
        win.active = fa.path
        win._refresh_series_dock()
        g = win.series._groups[fa.path]
        assert set(g.checks) == {0, 1}  # both datasets listed (C11)
        assert len(g.checks[0]) == 1 and len(g.checks[1]) == 1
        assert g.combo is not None
        # every dataset's series defaults to visible, labels qualify per dataset
        st = win._compose_state([fa])
        assert [e.label for e in st.entries] == ["multidataset·ds1: A",
                                                 "multidataset·ds2: B"]
        # the toggle signal is dataset-aware: hiding ds2 leaves ds1, whose
        # label un-qualifies once the file contributes a single dataset
        win._on_series_toggled(fa, 1, 0, False)
        st = win._compose_state([fa])
        assert [e.label for e in st.entries] == ["A"]
        # unchecking through the dock checkbox reaches the window
        g.checks[0][0].setChecked(False)
        assert win._compose_state([fa]).entries == []
        # cross-file overlay: dataset 2 of file A with dataset 1 of file B
        fb_file = fa.path.parent / "other.xvg"
        fb_file.write_text('@ title "O"\n@ s0 legend "C"\n0 1\n1 2\n',
                           encoding="utf-8")
        fb = parse_file(fb_file)
        win.files[fb.path] = fb
        win._on_series_toggled(fa, 1, 0, True)
        g.checks[0][0].setChecked(True)
        st = win._compose_state([fa, fb])
        labels = [e.label for e in st.entries]
        assert labels == ["multidataset·ds1: A", "multidataset·ds2: B",
                          "other: C"]  # stem-qualified in multi-file overlays
    finally:
        win.close()


def test_c21_session_roundtrip(app, tmp_path):
    from xvg_plotter import settings
    from xvg_plotter.core.parser import parse_file
    from xvg_plotter.ui.main_window import MainWindow

    f1 = tmp_path / "one.xvg"
    f2 = tmp_path / "two.xvg"
    f1.write_text('@ title "one"\n0 0\n1 1\n', encoding="utf-8")
    f2.write_text('@ title "two"\n0 0\n1 5\n', encoding="utf-8")
    old_session = settings.get("session")
    try:
        win1 = MainWindow()
        fa, fb = parse_file(f1), parse_file(f2)
        for fx in (fa, fb):
            win1.files[fx.path] = fx
            win1._tables[0].add_file(fx)
        win1.table.sync_check(fa.path, True)
        win1.table.sync_check(fb.path, True)
        win1.active = fb.path
        win1._refresh_series_dock()
        win1._on_series_color(fa, 0, 0, "#123456")
        win1.style.chk_logy.setChecked(True)
        win1.series.chk_fit.setChecked(True)
        win1.update_plot()
        win1.panel.fig.axes[0].set_xlim(0.25, 0.75)
        win1._save_session()

        win2 = MainWindow()
        win2.restore_session()
        assert win2.style.chk_logy.isChecked()
        assert win2.series.chk_fit.isChecked()
        # files arrive as the scanner would deliver them
        win2._on_file(parse_file(f1))
        win2._on_file(parse_file(f2))
        assert win2.active == fb.path  # the saved active file, not the first
        assert [f.path for f in win2._checked()] == [fa.path, fb.path]
        assert win2._colors.get((fa.path, 0, 0)) == "#123456"
        assert win2._compose_state(win2._targets()).logy
        win2._on_scan_done(0)  # final render + saved zoom
        assert win2.panel.fig.axes[0].get_xlim() == pytest.approx((0.25, 0.75))
        win1.close()
        win2.close()
    finally:
        if old_session is not None:
            settings.set_("session", old_session)
        else:
            settings.set_("session", "")


def test_c35_zh_cn_translation_roundtrip(app):
    from xvg_plotter.i18n import DictTranslator, zh_CN
    from xvg_plotter.ui.main_window import MainWindow

    tr = DictTranslator(zh_CN.STRINGS, app)
    assert app.installTranslator(tr)
    try:
        win = MainWindow()
        menu_texts = [a.text() for a in win.menuBar().actions()]
        assert any("文件" in t for t in menu_texts)
        dock_titles = [d.windowTitle() for d in win._docks]
        assert dock_titles == ["文件", "曲线与分析"]
        assert win.series.chk_average.text() == "副本平均（均值 ± 标准差）"
        assert win.series.cmb_norm.itemText(1) == "按首值"
        win.series.cmb_norm.setCurrentIndex(1)
        assert win.series.analysis_state().norm == "first value"  # untranslated mode
        win.close()
    finally:
        app.removeTranslator(tr)
    # after removal the very next window is English again
    win = MainWindow()
    assert "&File" in [a.text() for a in win.menuBar().actions()]
    win.close()
