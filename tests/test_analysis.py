import numpy as np

from xvg_plotter.core.analysis import (
    auto_unit,
    average_replicas,
    convert_x,
    moving_average,
    scale_label,
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


def test_average_interp_warning():
    x1 = np.array([0.0, 1.0, 2.0])
    x2 = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    xm, mean, std, warn = average_replicas([(x1, [0, 10, 20]), (x2, [0, 5, 10, 15, 20])])
    assert len(xm) == 3
    assert np.allclose(mean, [0, 10, 20])
    assert warn and "interpolation" in warn


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
