import pytest
import numpy as np

from xvg_plotter.core.analysis import (
    auto_unit,
    average_replicas,
    convert_x,
    decimate_minmax,
    is_time_label,
    median_dt,
    moving_average,
    scale_label,
    series_summary,
    summary_stats,
)


def test_moving_average_exact():
    y = [0, 0, 0, 0, 9]
    assert moving_average(y, 3).tolist() == [0.0, 0.0, 0.0, 3.0, 6.0]


def test_moving_average_even_window_bumped_to_odd():
    y = [0, 0, 0, 0, 9]
    assert np.array_equal(moving_average(y, 2), moving_average(y, 3))


def test_moving_average_noop():
    y = np.array([1.0, 2.0])
    assert np.array_equal(moving_average(y, 1), y)


def test_average_equal_grids():
    x = np.array([0.0, 1.0, 2.0])
    xm, mean, std, warn = average_replicas([(x, [0, 0, 0]), (x, [2, 2, 2])])
    assert np.array_equal(xm, x)
    assert mean.tolist() == [1.0, 1.0, 1.0]
    assert np.allclose(std, np.sqrt(2.0))  # ddof=1
    assert warn is None


def test_average_grids_differ_full_coverage_is_quiet():
    # grids differ but every replica covers the whole range: interpolation
    # fabricates nothing, so no warning (C27 replaced the always-warn rule)
    x1 = np.array([0.0, 1.0, 2.0])
    x2 = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    xm, mean, std, warn = average_replicas([(x1, [0, 10, 20]), (x2, [0, 5, 10, 15, 20])])
    assert len(xm) == 3
    assert np.allclose(mean, [0, 10, 20])
    assert warn is None


def test_average_truncation_warns_over_5pct():
    x1 = np.linspace(0.0, 100.0, 101)
    x2 = np.linspace(0.0, 50.0, 51)  # covers only half of replica 1's range
    xm, mean, std, warn = average_replicas(
        [(x1, np.zeros(101)), (x2, np.zeros(51))])
    assert warn and "outside it" in warn and "Common time range" in warn
    assert xm.size == 101


def test_average_small_mismatch_stays_quiet():
    # ~3% of the aligned range lies outside replica 2 — under the 5% threshold
    x1 = np.linspace(0.0, 100.0, 101)
    x2 = np.linspace(0.0, 97.0, 98)
    _, _, _, warn = average_replicas([(x1, np.zeros(101)), (x2, np.zeros(98))])
    assert warn is None


def test_average_common_range_limits_span():
    x1 = np.array([0.0, 1.0, 2.0, 3.0])
    x2 = np.array([1.0, 2.0, 3.0])
    xm, mean, _, warn = average_replicas(
        [(x1, [0.0, 1.0, 2.0, 3.0]), (x2, [10.0, 20.0, 30.0])], common_range=True)
    assert xm.min() == 1.0 and xm.max() == 3.0
    assert np.allclose(mean, [5.5, 11.0, 16.5])
    assert warn is None  # nothing is extrapolated in the shared span


def test_average_common_range_no_overlap():
    xm, mean, std, warn = average_replicas(
        [(np.array([0.0, 1.0]), [0.0, 1.0]), (np.array([5.0, 6.0]), [5.0, 6.0])],
        common_range=True)
    assert xm.size == 0 and mean.size == 0
    assert warn and "no overlapping" in warn


def test_is_time_label():
    assert is_time_label("Time (ps)")
    assert is_time_label("t ps")
    assert is_time_label("time")
    assert is_time_label("t/ns")
    assert is_time_label(None)  # unlabeled: GROMACS default is time
    assert not is_time_label("Position")
    assert not is_time_label("Frame")
    assert not is_time_label("x (nm)")


def test_median_dt():
    assert median_dt([0.0, 1.0, 2.0, 3.0]) == 1.0
    assert median_dt([0.0, 0.5, 2.0]) == 1.0
    assert median_dt([3.0, 1.0, 2.0]) == 1.0  # order-independent
    assert median_dt([1.0]) == 0.0


def test_summary_stats_finite_only():
    assert summary_stats([1.0, np.nan, 3.0]) == (1.0, 3.0, 2.0)
    assert all(np.isnan(v) for v in summary_stats([np.inf]))


def test_series_summary_format_and_cap():
    s = series_summary([("RMSD", [1.0, 2.0, 3.0])])
    assert s == "RMSD: 1–3 (mean 2)"
    named = [(f"s{i}", [0.0]) for i in range(6)]
    s = series_summary(named, max_series=4)
    assert s.endswith("+2 more") and s.count(";") == 4
    assert series_summary([]) == ""


def test_decimate_small_series_passthrough():
    x = np.arange(50.0)
    sel = decimate_minmax(x, np.sin(x), max_points=100)
    assert sel.tolist() == list(range(50))  # nothing to decimate


def test_decimate_preserves_bucket_extremes():
    n = 1000
    x = np.arange(float(n))
    y = np.zeros(n)
    y[123] = -5.0  # a sharp dip inside bucket 1
    y[456] = 9.0   # a sharp spike inside bucket 3
    sel = decimate_minmax(x, y, max_points=10)
    assert len(sel) <= 2 * 100 + (n % 100) + 2
    assert 123 in sel and 456 in sel  # spikes survive
    assert y[sel].min() == -5.0 and y[sel].max() == 9.0


def test_decimate_nan_buckets_never_collapse():
    x = np.arange(float(500))
    y = np.full(500, np.nan)
    sel = decimate_minmax(x, y, max_points=10)
    assert sel.size > 0  # all-NaN buckets still keep their first point


def test_convert_and_label():
    assert convert_x([1000.0, 2000.0], "ns").tolist() == [1.0, 2.0]
    assert convert_x([1.0, 2.0], "ps").tolist() == [1.0, 2.0]
    assert scale_label("Time (ps)", "ns") == "Time (ns)"
    assert scale_label("t ps", "µs") == "t µs"
    assert scale_label(None, "ns") == "Time (ns)"
    assert scale_label("Position", "ns") == "Position (ns)"


def test_auto_unit():
    assert auto_unit(np.linspace(0, 5000, 10)) == "ns"
    assert auto_unit(np.linspace(0, 800, 10)) == "ps"
    assert auto_unit(np.linspace(0, 5e6, 10)) == "µs"
    assert auto_unit(np.linspace(0, 9e9, 10)) == "ms"
    assert auto_unit([0.0]) == "ps"


# -- v1.3.0 derived quantities (C24) --------------------------------------------

def test_normalize_modes():
    from xvg_plotter.core.analysis import normalize
    y = [4.0, 2.0, 8.0]
    assert normalize(y, "first").tolist() == [1.0, 0.5, 2.0]
    assert normalize(y, "max").tolist() == [0.5, 0.25, 1.0]
    assert normalize(y, "off").tolist() == y
    # zero reference (first value 0) leaves the data untouched
    assert normalize([0.0, 1.0], "first").tolist() == [0.0, 1.0]
    # all-NaN input is returned as-is
    assert all(np.isnan(v) for v in normalize([np.nan], "max"))


def test_norm_reference():
    from xvg_plotter.core.analysis import norm_reference
    assert norm_reference([4.0, 2.0, 8.0], "first") == 4.0
    assert norm_reference([4.0, 2.0, 8.0], "max") == 8.0
    assert norm_reference([np.nan, np.inf], "max") == 0.0


def test_subtract_baseline():
    from xvg_plotter.core.analysis import subtract_baseline
    assert subtract_baseline([4.0, 2.0, 8.0]).tolist() == [0.0, -2.0, 4.0]
    out = subtract_baseline([np.nan, 3.0])
    assert np.isnan(out[0]) and out[1] == 0.0


def test_fit_line_recovers_synthetic_slope():
    from xvg_plotter.core.analysis import fit_line
    x = np.linspace(0.0, 10.0, 11)
    xf, a, b = fit_line(x, 2.0 * x + 1.0)
    assert a == pytest.approx(2.0) and b == pytest.approx(1.0)
    assert xf[0] == pytest.approx(0.0) and xf[-1] == pytest.approx(10.0)


def test_fit_line_range_limited_and_degenerate():
    from xvg_plotter.core.analysis import fit_line
    x = np.linspace(0.0, 10.0, 101)
    y = np.where(x <= 5.0, 2.0 * x, 0.0)  # slope 2 only on the first half
    xf, a, b = fit_line(x, y, (0.0, 5.0))
    assert a == pytest.approx(2.0) and b == pytest.approx(0.0)
    assert xf.max() == pytest.approx(5.0)
    assert fit_line(x[:1], y[:1]) is None  # < 2 points: no fit
