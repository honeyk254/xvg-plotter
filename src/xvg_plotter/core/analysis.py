"""Analysis extras: averaging, smoothing, time-unit conversion (SPEC §7)."""
from __future__ import annotations

import re

import numpy as np

UNITS = {"ps": 1.0, "ns": 1e-3, "µs": 1e-6, "ms": 1e-9}

# C25: only treat X as time when the label says so (unlabeled axes count as
# time — GROMACS' default output is time in ps).
_TIME_RE = re.compile(r"time|\bps\b|\bns\b|µs|μs|\bms\b|\bfs\b", re.IGNORECASE)


def is_time_label(label: str | None) -> bool:
    """True when the X axis label identifies a time axis (C25)."""
    return label is None or bool(_TIME_RE.search(label))


def median_dt(x) -> float:
    """Median positive spacing of X — the physical dt behind a point window (C28)."""
    x = np.sort(np.asarray(x, dtype=float))
    if x.size < 2:
        return 0.0
    d = np.diff(x)
    d = d[d > 0]
    return float(np.median(d)) if d.size else 0.0


def decimate_minmax(x, y, max_points: int = 20000) -> np.ndarray:
    """Index subset keeping every bucket's min and max — interactive-view
    decimation for huge series (C23). Returns all indices unchanged when the
    series is already small enough; buckets with only NaNs contribute their
    first point so gaps never collapse."""
    x = np.asarray(x)
    y = np.asarray(y, dtype=float)
    n = x.size
    if n <= max_points:
        return np.arange(n)
    bucket = int(np.ceil(n / max_points))
    m = (n // bucket) * bucket
    if m == 0:
        return np.arange(n)
    yb = y[:m].reshape(-1, bucket)
    lo = np.where(np.isnan(yb), np.inf, yb).argmin(axis=1)
    hi = np.where(np.isnan(yb), -np.inf, yb).argmax(axis=1)
    base = np.arange(0, m, bucket)
    return np.unique(np.concatenate([base + lo, base + hi, np.arange(m, n)]))


def moving_average(y, window: int) -> np.ndarray:
    """Centered moving average, edge-padded; even windows rounded up to odd."""
    window = max(int(window), 1)
    if window % 2 == 0:
        window += 1
    y = np.asarray(y, dtype=float)
    if window <= 1 or y.size == 0:
        return y
    pad = window // 2
    yp = np.pad(y, pad, mode="edge")
    return np.convolve(yp, np.full(window, 1.0 / window), mode="valid")


def average_replicas(curves, common_range: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray, str | None]:
    """curves: list of (x, y). Aligns all onto the first X grid and returns
    (x, mean, std, warning). Assumes X ascending (GROMACS output always is).

    With common_range=True the average covers only the span every replica
    shares, so shorter runs never truncate longer ones (C27). A warning is
    emitted when >5 % of the aligned points fall outside a replica's own
    range (SPEC §7.1 threshold) — interpolation beyond a replica's data
    silently fabricates it.
    """
    x0 = np.asarray(curves[0][0], dtype=float)
    if common_range and len(curves) > 1 and x0.size:
        lo = max(float(np.min(np.asarray(c[0], dtype=float))) for c in curves)
        hi = min(float(np.max(np.asarray(c[0], dtype=float))) for c in curves)
        if lo > hi:
            return (np.array([]), np.array([]), np.array([]),
                    "replicas share no overlapping time range; nothing to average")
        x0 = x0[(x0 >= lo) & (x0 <= hi)]
    ys: list[np.ndarray] = []
    short: tuple[int, float, float, float] | None = None
    for i, curve in enumerate(curves):
        x = np.asarray(curve[0], dtype=float)
        y = np.asarray(curve[1], dtype=float)
        if x0.size and x.size and (len(x) != len(x0) or not np.array_equal(x, x0)):
            inside = (x0 >= x.min()) & (x0 <= x.max())
            frac = 1.0 - float(inside.mean())
            if frac > 0.05 and short is None:
                short = (i, frac * 100.0, float(x.min()), float(x.max()))
            y = np.interp(x0, x, y)
        ys.append(y)
    stack = np.stack(ys)
    mean = np.nanmean(stack, axis=0)
    std = np.nanstd(stack, axis=0, ddof=1) if len(curves) > 1 else np.zeros_like(mean)
    warn = None
    if short is not None:
        i, pct, xmin, xmax = short
        warn = (f"replica {i + 1} covers {xmin:g}–{xmax:g}: {pct:.0f}% of the aligned "
                f"range lies outside it — shorter replicas truncate the mean; "
                f"enable 'Common time range' to average only the shared span")
    return x0, mean, std, warn


def auto_unit(x) -> str:
    """Largest unit such that the scaled axis max is >= 1 (SPEC §7.3)."""
    m = float(np.nanmax(np.abs(x))) if np.asarray(x).size else 0.0
    for u in ("ms", "µs", "ns"):
        if m * UNITS[u] >= 1.0:
            return u
    return "ps"


def scale_label(label: str | None, unit: str) -> str:
    if label is None:
        return f"Time ({unit})"
    if "(ps)" in label:
        return label.replace("(ps)", f"({unit})")
    if re.search(r"\bps\b", label):
        return re.sub(r"\bps\b", unit, label, count=1)
    return f"{label} ({unit})"


def convert_x(x, unit: str) -> np.ndarray:
    return np.asarray(x, dtype=float) * UNITS[unit]


def summary_stats(y) -> tuple[float, float, float]:
    """(min, max, mean) over finite values (C26)."""
    v = np.asarray(y, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan"), float("nan"), float("nan")
    return float(np.min(v)), float(np.max(v)), float(np.mean(v))


def series_summary(named, max_series: int = 4) -> str:
    """Compact min/max/mean line for the status bar / accessibility text (C26, C34).

    named: iterable of (label, y)."""
    items = list(named)
    parts: list[str] = []
    for label, y in items[:max_series]:
        lo, hi, mu = summary_stats(y)
        parts.append(f"{label}: {lo:.4g}–{hi:.4g} (mean {mu:.4g})")
    if len(items) > max_series:
        parts.append(f"… +{len(items) - max_series} more")
    return "; ".join(parts)
