import math
from pathlib import Path

from xvg_plotter.core.parser import parse_file

FIX = Path(__file__).parent / "fixtures"


def p(name):
    return FIX / name


def test_minimal():
    f = parse_file(p("minimal.xvg"))
    assert f.title == "RMSD"
    assert f.x_label == "Time (ps)"
    assert f.y_label == "RMSD (nm)"
    assert f.stats.rows_ok == 3
    d = f.datasets[0]
    assert len(d.series) == 1
    assert d.series[0].legend == "Protein"
    assert d.series[0].kind == "xy"
    assert d.x.tolist() == [0.0, 10.0, 20.0]
    assert d.columns[1].tolist() == [0.0, 0.12, 0.15]
    assert not f.warnings


def test_energy_multi_series():
    f = parse_file(p("energy.xvg"))
    d = f.datasets[0]
    assert f.stats.n_cols == 4
    assert [s.legend for s in d.series] == ["Potential", "Kinetic", "Total Energy"]
    assert all(s.kind == "xy" for s in d.series)
    assert [s.y_col for s in d.series] == [1, 2, 3]


def test_errorbar_xydy():
    f = parse_file(p("errorbar.xvg"))
    s = f.datasets[0].series[0]
    assert s.kind == "xydy"
    assert s.y_col == 1 and s.dy_col == 2
    assert f.datasets[0].columns[2].tolist() == [0.05, 0.06, 0.04, 0.05]


def test_xydxdy():
    f = parse_file(p("xydxdy.xvg"))
    s = f.datasets[0].series[0]
    assert s.kind == "xydxdy"
    assert s.dx_col == 1 and s.y_col == 2 and s.dy_col == 3
    assert f.datasets[0].columns[2].tolist() == [1.0, 2.0, 1.5]


def test_multidataset():
    f = parse_file(p("multidataset.xvg"))
    assert len(f.datasets) == 2
    assert f.datasets[0].series[0].legend == "A"
    assert f.datasets[1].series[0].legend == "B"  # directives reset per dataset
    assert len(f.datasets[0].x) == 2 and len(f.datasets[1].x) == 3


def test_malformed():
    f = parse_file(p("malformed.xvg"))
    assert f.stats.rows_ok == 2
    assert f.stats.rows_skipped == 2  # one bad-token row, one ragged row
    assert f.warnings
    assert f.datasets[0].columns[1].tolist() == [2.0, 8.0]


def test_headers_only():
    f = parse_file(p("headers_only.xvg"))
    assert f.datasets == []
    assert f.title == "Nothing"
    assert any("no data rows" in w for w in f.warnings)


def test_empty():
    f = parse_file(p("empty.xvg"))
    assert f.datasets == []
    assert f.warnings


def test_nan_inf_scientific():
    f = parse_file(p("nan.xvg"))
    y = f.datasets[0].columns[1]
    assert math.isnan(y[1])
    assert math.isinf(y[2]) and y[2] > 0
    assert math.isinf(y[3]) and y[3] < 0
    assert y[4] == 0.25
    assert y[5] == -100.0


def test_crlf():
    a, b = parse_file(p("minimal.xvg")), parse_file(p("crlf.xvg"))
    assert b.title == a.title and b.stats.rows_ok == a.stats.rows_ok
    assert b.datasets[0].columns[1].tolist() == a.datasets[0].columns[1].tolist()


def test_bom():
    f = parse_file(p("bom.xvg"))
    assert f.title == "RMSD"
    assert f.stats.rows_ok == 3
